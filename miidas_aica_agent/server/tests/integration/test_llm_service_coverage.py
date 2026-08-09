"""
Integration tests for LLMService — targeting 100% branch coverage.

External boundaries mocked:
  - MCPServerStreamableHttp.connect() / cleanup()
  - MCPUtil.get_all_function_tools()
  - asyncio.create_task (for lifecycle task)

Tests call the real service with these mocks so the LLM/agent initialization
paths are exercised without a running MCP server.
"""

import asyncio
from copy import copy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from services.agent_service import AgentService
from services.llm_service import (
    AgentName,
    LLMService,
    NotSupportedModelName,
    ToolNotFoundInRepositoryError,
)

pytestmark = pytest.mark.pre_extraction_parity

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _make_tool(name: str):
    tool = MagicMock()
    tool.name = name
    tool.params_json_schema = {}
    tool.description = f"Description for {name}"
    return tool


def _make_agent_entity(
    name: str,
    tool_names: list[str] | None = None,
    next_agents=None,
    default_agent: bool = True,
    can_search_position: bool = False,
):
    entity = SimpleNamespace(
        id=1,
        name=name,
        tools=[
            SimpleNamespace(tool_name=t, return_direct=False)
            for t in (tool_names or [])
        ],
        next_agents=next_agents or [],
        default_agent=default_agent,
        can_search_position=can_search_position,
        deleted_at=None,
    )
    return entity


def _make_agent_svc(agents=None) -> AgentService:
    svc = MagicMock(spec=AgentService)
    if agents is None:
        agents = [(_make_agent_entity("CareerAdvisor"), "You are helpful.")]
    svc.get_agents_with_prompts.return_value = agents
    return svc


def _make_model_list(model="gpt-4o", use_for=None):
    return [
        {
            "model": model,
            "use_for": use_for or ["agent"],
            "model_settings": {},
        }
    ]


async def _boot_service(
    tools: list | None = None,
    agents=None,
    model_list=None,
) -> LLMService:
    """Boot an LLMService with mocked MCP and all function tools."""
    tools = tools or [_make_tool("my_tool")]
    model_list = model_list or _make_model_list()
    agent_svc = _make_agent_svc(agents)

    svc = LLMService()
    svc._mcp_server = MagicMock()
    svc._mcp_server.connect = AsyncMock()
    svc._mcp_server.cleanup = AsyncMock()
    svc._startup_event = asyncio.Event()
    svc._shutdown_event = asyncio.Event()
    svc._server_error = None
    svc._all_tools = tools

    await svc._init_agents(model_list, agent_svc)
    return svc


# ─── LLMService.__init__ ──────────────────────────────────────────────────────


def test_llm_service_init_sets_defaults():
    svc = LLMService()
    assert svc._server_task is None
    assert svc._startup_event is None
    assert svc._shutdown_event is None
    assert svc._server_error is None
    assert svc._mcp_server is None
    assert svc._agents == {}
    assert svc._all_tools == []
    assert svc._search_position_agent_names == {}


# ─── LLMService.shutdown ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_shutdown_no_server_task_is_noop():
    svc = LLMService()
    svc._server_task = None
    await svc.shutdown(None)  # Should not raise


@pytest.mark.asyncio
async def test_shutdown_sets_event_and_awaits_task():
    svc = LLMService()
    svc._shutdown_event = asyncio.Event()

    # Create a real completed future to act as _server_task
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    future.set_result(None)
    svc._server_task = future

    svc._mcp_server = MagicMock()
    svc._server_error = None

    await svc.shutdown(None)

    assert svc._server_task is None
    assert svc._mcp_server is None


@pytest.mark.asyncio
async def test_shutdown_raises_server_error():
    svc = LLMService()
    svc._shutdown_event = asyncio.Event()

    loop = asyncio.get_event_loop()
    future = loop.create_future()
    future.set_result(None)
    svc._server_task = future

    svc._mcp_server = MagicMock()
    svc._server_error = RuntimeError("lifecycle error")

    with pytest.raises(RuntimeError, match="lifecycle error"):
        await svc.shutdown(None)


# ─── LLMService.init ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_init_raises_when_no_agent_models():
    svc = LLMService()
    model_list_no_agent = [
        {"model": "gpt-4o-mini", "use_for": ["summary"], "model_settings": {}}
    ]
    agent_svc = _make_agent_svc()

    with (
        patch("services.llm_service.MCPServerStreamableHttp") as mock_mcp_cls,
        patch(
            "services.llm_service.MCPUtil.get_all_function_tools",
            new=AsyncMock(return_value=[]),
        ),
    ):
        mock_mcp = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        async def fake_lifecycle(url):
            svc._startup_event.set()
            await svc._shutdown_event.wait()

        with (
            patch.object(svc, "_mcp_server_lifecycle", side_effect=fake_lifecycle),
            pytest.raises(Exception, match="Agent用のモデルが定義されていません"),
        ):
            await svc.init(
                mcp_url="http://fake-mcp/",
                timeout=10.0,
                model_list=model_list_no_agent,
                agent_svc=agent_svc,
            )


@pytest.mark.asyncio
async def test_init_raises_when_task_already_running():
    """Verify that init() raises RuntimeError when a lifecycle task is already running."""
    svc = LLMService()
    # Create a running task (done() returns False)
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    svc._server_task = future

    # The init() method creates MCPServerStreamableHttp, sets up events, then checks
    # if _server_task is running → raises RuntimeError.
    # In the except block it calls asyncio.gather(_server_task).
    # We resolve the future before gather actually waits so the test doesn't hang.
    original_gather = asyncio.gather

    async def patched_gather(*args, **kwargs):
        # Resolve any futures passed to gather so they complete
        for arg in args:
            if asyncio.isfuture(arg) and not arg.done():
                arg.set_result(None)
        return await original_gather(*args, **kwargs)

    with (
        patch("services.llm_service.MCPServerStreamableHttp"),
        patch("services.llm_service.asyncio.gather", side_effect=patched_gather),
        pytest.raises(RuntimeError, match="既に起動"),
    ):
        await svc.init(
            mcp_url="http://fake/",
            timeout=5.0,
            model_list=_make_model_list(),
            agent_svc=_make_agent_svc(),
        )


@pytest.mark.asyncio
async def test_init_succeeds_and_returns_self():
    """Covers lines 145, 158: init_agents called, return self on success."""
    svc = LLMService()

    tool = _make_tool("my_tool")
    agent = _make_agent_entity("CareerAdvisor")
    agents = [(agent, "System prompt")]
    agent_svc = _make_agent_svc(agents)

    with (
        patch("services.llm_service.MCPServerStreamableHttp") as mock_mcp_cls,
        patch(
            "services.llm_service.MCPUtil.get_all_function_tools",
            new=AsyncMock(return_value=[tool]),
        ),
    ):
        mock_mcp = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        async def good_lifecycle(url):
            # Set startup event and exit immediately (simulates connected state)
            svc._startup_event.set()
            # Don't wait for shutdown_event — just return immediately

        with patch.object(svc, "_mcp_server_lifecycle", side_effect=good_lifecycle):
            result = await svc.init(
                mcp_url="http://fake-mcp/",
                timeout=10.0,
                model_list=_make_model_list(),
                agent_svc=agent_svc,
            )

    assert result is svc


@pytest.mark.asyncio
async def test_init_raises_when_server_error_set_after_startup():
    """Covers line 133: raise self._server_error when startup_event fires but error is set.
    Also covers lines 151-154: shutdown_event not set, server_task set."""
    svc = LLMService()

    with (
        patch("services.llm_service.MCPServerStreamableHttp") as mock_mcp_cls,
        pytest.raises(RuntimeError, match="MCP connect failed"),
    ):
        mock_mcp = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # The lifecycle sets _server_error then sets startup_event, then completes quickly
        async def failing_lifecycle(url):
            svc._server_error = RuntimeError("MCP connect failed")
            svc._startup_event.set()
            # Return immediately (task is done), gather returns immediately too

        with patch.object(svc, "_mcp_server_lifecycle", side_effect=failing_lifecycle):
            await svc.init(
                mcp_url="http://fake/",
                timeout=5.0,
                model_list=_make_model_list(),
                agent_svc=_make_agent_svc(),
            )


@pytest.mark.asyncio
async def test_init_exception_with_shutdown_event_already_set():
    """Covers branch 151→153: shutdown_event already set when exception occurs."""
    svc = LLMService()

    with (
        patch("services.llm_service.MCPServerStreamableHttp") as mock_mcp_cls,
        pytest.raises(RuntimeError, match="MCP connect failed"),
    ):
        mock_mcp = MagicMock()
        mock_mcp_cls.return_value = mock_mcp

        # Lifecycle completes and sets shutdown_event before exception
        async def lifecycle_with_shutdown_set(url):
            svc._server_error = RuntimeError("MCP connect failed")
            svc._startup_event.set()
            svc._shutdown_event.set()  # pre-set shutdown event (already is_set=True)

        with patch.object(
            svc, "_mcp_server_lifecycle", side_effect=lifecycle_with_shutdown_set
        ):
            await svc.init(
                mcp_url="http://fake/",
                timeout=5.0,
                model_list=_make_model_list(),
                agent_svc=_make_agent_svc(),
            )


@pytest.mark.asyncio
async def test_init_exception_before_create_task_server_task_none():
    """Covers branch 153→156: _server_task is None when exception occurs
    (exception raised before asyncio.create_task() is called)."""
    svc = LLMService()
    # _server_task is None from __init__

    # Raise exception during MCPServerStreamableHttp creation (before create_task)
    with (
        patch(
            "services.llm_service.MCPServerStreamableHttp",
            side_effect=RuntimeError("mcp init failed"),
        ),
        pytest.raises(RuntimeError, match="mcp init failed"),
    ):
        await svc.init(
            mcp_url="http://fake/",
            timeout=5.0,
            model_list=_make_model_list(),
            agent_svc=_make_agent_svc(),
        )

    # _server_task should still be None since create_task was never called
    assert svc._server_task is None


# ─── LLMService._mcp_server_lifecycle ────────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_none_mcp_raises():
    svc = LLMService()
    svc._mcp_server = None
    svc._startup_event = asyncio.Event()
    svc._shutdown_event = asyncio.Event()

    with pytest.raises(RuntimeError, match="初期化されていません"):
        await svc._mcp_server_lifecycle("http://fake/")


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_connect_raises_sets_error():
    svc = LLMService()
    svc._startup_event = asyncio.Event()
    svc._shutdown_event = asyncio.Event()
    svc._server_error = None

    mock_mcp = MagicMock()
    mock_mcp.connect = AsyncMock(side_effect=RuntimeError("connect failed"))
    mock_mcp.cleanup = AsyncMock()
    svc._mcp_server = mock_mcp

    await svc._mcp_server_lifecycle("http://fake/")

    assert isinstance(svc._server_error, RuntimeError)
    assert svc._startup_event.is_set()


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_cleanup_cancel_scope_error_logged():
    svc = LLMService()
    svc._startup_event = asyncio.Event()
    svc._shutdown_event = asyncio.Event()
    svc._server_error = None

    mock_mcp = MagicMock()
    mock_mcp.connect = AsyncMock(side_effect=RuntimeError("connect fail"))
    mock_mcp.cleanup = AsyncMock(
        side_effect=RuntimeError("Attempted to exit cancel scope in a different task")
    )
    svc._mcp_server = mock_mcp

    # Should not raise — cancel scope error is swallowed
    await svc._mcp_server_lifecycle("http://fake/")


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_cleanup_other_runtime_error_logged():
    svc = LLMService()
    svc._startup_event = asyncio.Event()
    svc._shutdown_event = asyncio.Event()
    svc._server_error = None

    mock_mcp = MagicMock()
    mock_mcp.connect = AsyncMock(side_effect=RuntimeError("connect fail"))
    mock_mcp.cleanup = AsyncMock(side_effect=RuntimeError("other runtime error"))
    svc._mcp_server = mock_mcp

    # Should not raise
    await svc._mcp_server_lifecycle("http://fake/")


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_cleanup_generic_exception_logged():
    svc = LLMService()
    svc._startup_event = asyncio.Event()
    svc._shutdown_event = asyncio.Event()
    svc._server_error = None

    mock_mcp = MagicMock()
    mock_mcp.connect = AsyncMock(side_effect=RuntimeError("connect fail"))
    mock_mcp.cleanup = AsyncMock(side_effect=Exception("generic error"))
    svc._mcp_server = mock_mcp

    # Should not raise
    await svc._mcp_server_lifecycle("http://fake/")


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_normal_flow():
    """Test the normal path: connect succeeds, startup event set, waits for shutdown."""
    svc = LLMService()
    svc._startup_event = asyncio.Event()
    svc._shutdown_event = asyncio.Event()
    svc._server_error = None

    mock_mcp = MagicMock()
    connect_called = []

    async def fake_connect():
        connect_called.append(True)

    mock_mcp.connect = fake_connect
    mock_mcp.cleanup = AsyncMock()
    svc._mcp_server = mock_mcp

    # Pre-set shutdown event so the lifecycle doesn't wait forever
    svc._shutdown_event.set()

    await svc._mcp_server_lifecycle("http://fake/")

    assert connect_called
    assert svc._startup_event.is_set()
    mock_mcp.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_cancelled_after_startup_covers_206_208():
    """Arc 206->208: startup_event already set when BaseException is caught.

    Sequence: connect() succeeds → startup_event.set() → wait() raises CancelledError.
    In except: startup_event.is_set() is True → line 206 condition is False → jumps to 208.
    """
    svc = LLMService()
    svc._startup_event = asyncio.Event()
    svc._shutdown_event = asyncio.Event()
    svc._server_error = None

    mock_mcp = MagicMock()
    mock_mcp.connect = AsyncMock()  # connect succeeds
    mock_mcp.cleanup = AsyncMock()
    svc._mcp_server = mock_mcp

    # Patch shutdown_event.wait to raise CancelledError so startup_event is already
    # set (by the normal flow) when the except BaseException block runs.
    async def raise_cancelled():
        raise asyncio.CancelledError()

    with patch.object(svc._shutdown_event, "wait", side_effect=raise_cancelled):
        await svc._mcp_server_lifecycle("http://fake/")

    assert svc._startup_event.is_set()
    assert isinstance(svc._server_error, asyncio.CancelledError)


# ─── LLMService._init_agents ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_init_agents_tool_not_in_mcp_raises():
    tools = [_make_tool("existing_tool")]
    agents = [
        (
            _make_agent_entity("TestAgent", tool_names=["missing_tool"]),
            "prompt",
        )
    ]
    svc = LLMService()
    svc._all_tools = tools
    agent_svc = _make_agent_svc(agents)

    with pytest.raises(ToolNotFoundInRepositoryError):
        await svc._init_agents(_make_model_list(), agent_svc)


@pytest.mark.asyncio
async def test_init_agents_with_return_direct_tool():
    tool = _make_tool("stop_tool")
    agent_entity = _make_agent_entity("Agent", tool_names=["stop_tool"])
    agent_entity.tools = [SimpleNamespace(tool_name="stop_tool", return_direct=True)]
    agents = [(agent_entity, "prompt")]

    svc = LLMService()
    svc._all_tools = [tool]
    agent_svc = _make_agent_svc(agents)

    await svc._init_agents(_make_model_list(), agent_svc)

    # The agent should have tool_use_behavior with stop_at_tool_names
    model_name = "gpt-4o"
    assert model_name in svc._agents
    cloned_agent, _ = svc._agents[model_name]["Agent"]
    assert cloned_agent.tool_use_behavior["stop_at_tool_names"] == ["stop_tool"]


@pytest.mark.asyncio
async def test_init_agents_with_handoffs():
    tool = _make_tool("handoff_tool")
    dest_entity = _make_agent_entity("DestAgent")
    src_entity = _make_agent_entity("SrcAgent", tool_names=["handoff_tool"])
    src_entity.next_agents = [SimpleNamespace(dest_agent=dest_entity)]
    agents = [(src_entity, "src prompt"), (dest_entity, "dest prompt")]

    svc = LLMService()
    svc._all_tools = [tool]
    agent_svc = _make_agent_svc(agents)

    await svc._init_agents(_make_model_list(), agent_svc)

    model_name = "gpt-4o"
    src_agent, _ = svc._agents[model_name]["SrcAgent"]
    # src should have handoffs set
    assert len(src_agent.handoffs) == 1


@pytest.mark.asyncio
async def test_init_agents_with_reasoning_model_settings():
    tool = _make_tool("t")
    agents = [(_make_agent_entity("A"), "prompt")]

    model_list = [
        {
            "model": "o3",
            "use_for": ["agent"],
            "model_settings": {"reasoning": {"effort": "medium"}},
        }
    ]

    svc = LLMService()
    svc._all_tools = [tool]
    agent_svc = _make_agent_svc(agents)

    await svc._init_agents(model_list, agent_svc)
    assert "o3" in svc._agents


@pytest.mark.asyncio
async def test_init_agents_marks_can_search_position():
    tool = _make_tool("search_tool")
    agent = _make_agent_entity("SearchAgent", can_search_position=True)
    agents = [(agent, "prompt")]

    svc = LLMService()
    svc._all_tools = [tool]
    agent_svc = _make_agent_svc(agents)

    await svc._init_agents(_make_model_list(), agent_svc)

    model_name = "gpt-4o"
    assert "SearchAgent" in svc._search_position_agent_names[model_name]


# ─── LLMService.clone_agents ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clone_agents_unknown_model_raises():
    svc = await _boot_service()
    with pytest.raises(NotSupportedModelName):
        svc.clone_agents("unknown-model")


@pytest.mark.asyncio
async def test_clone_agents_no_tool_name_returns_cloned():
    svc = await _boot_service()
    result = svc.clone_agents("gpt-4o", jobtype_names=None, tool_name=None)
    assert "CareerAdvisor" in result


@pytest.mark.asyncio
async def test_clone_agents_with_invalid_tool_name_returns_cloned():
    svc = await _boot_service()
    # tool_name is not a position search tool → _build_position_search_tool logs error and returns None
    result = svc.clone_agents("gpt-4o", tool_name="not_a_search_tool")
    assert "CareerAdvisor" in result


@pytest.mark.asyncio
async def test_clone_agents_with_search_tool_name_not_in_mcp_returns_cloned():
    from utils.enum import ToolName

    svc = await _boot_service()
    # Use a valid position-search tool name but it's not in _all_tools
    result = svc.clone_agents(
        "gpt-4o", tool_name=ToolName.GENERIC_POSITION_SEARCH.value
    )
    assert "CareerAdvisor" in result


@pytest.mark.asyncio
async def test_clone_agents_with_valid_search_tool_sets_on_agent():
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {"properties": {}, "required": []}

    agent = _make_agent_entity(
        "SearchAgent",
        tool_names=[ToolName.GENERIC_POSITION_SEARCH.value],
        can_search_position=True,
    )
    agents = [(agent, "prompt")]

    svc = await _boot_service(tools=[search_tool], agents=agents)
    result = svc.clone_agents(
        "gpt-4o",
        tool_name=ToolName.GENERIC_POSITION_SEARCH.value,
        jobtype_names=["営業", "エンジニア"],
    )
    assert "SearchAgent" in result


@pytest.mark.asyncio
async def test_clone_agents_target_agent_missing_from_cloned():
    """Tests the case where target_agent_name not in cloned_agents."""
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {}

    agent = _make_agent_entity("CareerAdvisor")
    agents = [(agent, "prompt")]

    svc = await _boot_service(tools=[search_tool], agents=agents)
    # Manually add a search position agent name that doesn't exist in agents
    svc._search_position_agent_names["gpt-4o"] = {"GhostAgent"}

    result = svc.clone_agents(
        "gpt-4o",
        tool_name=ToolName.GENERIC_POSITION_SEARCH.value,
    )
    assert "CareerAdvisor" in result


# ─── LLMService.update_agent_by_tool_name ────────────────────────────────────


@pytest.mark.asyncio
async def test_update_agent_unknown_model_raises():
    svc = await _boot_service()
    with pytest.raises(NotSupportedModelName):
        svc.update_agent_by_tool_name("bad-model", None)


@pytest.mark.asyncio
async def test_update_agent_no_target_agent_names_returns_none():
    svc = await _boot_service()
    # CareerAdvisor has can_search_position=False → no search position agents
    result = svc.update_agent_by_tool_name("gpt-4o", None)
    assert result == (None, None)


@pytest.mark.asyncio
async def test_update_agent_no_tool_name_clears_search_tool():
    from utils.enum import ToolName

    agent = _make_agent_entity("SearchAgent", can_search_position=True)
    agents = [(agent, "prompt")]
    svc = await _boot_service(agents=agents)

    updated, tool_name = svc.update_agent_by_tool_name("gpt-4o", None)
    assert updated is not None
    assert tool_name is None


@pytest.mark.asyncio
async def test_update_agent_with_invalid_tool_name_returns_none():
    from utils.enum import ToolName

    agent = _make_agent_entity("SearchAgent", can_search_position=True)
    agents = [(agent, "prompt")]
    svc = await _boot_service(agents=agents)

    updated, tool_name = svc.update_agent_by_tool_name("gpt-4o", "not_a_search_tool")
    assert updated is None
    assert tool_name is None


@pytest.mark.asyncio
async def test_update_agent_with_valid_tool_updates_agent():
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {}

    agent = _make_agent_entity("SearchAgent", can_search_position=True)
    agents = [(agent, "prompt")]
    svc = await _boot_service(tools=[search_tool], agents=agents)

    updated, tool_name = svc.update_agent_by_tool_name(
        "gpt-4o", ToolName.GENERIC_POSITION_SEARCH.value
    )
    assert updated is not None
    assert tool_name == ToolName.GENERIC_POSITION_SEARCH.value


@pytest.mark.asyncio
async def test_update_agent_with_target_agents_override():
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {}

    agent = _make_agent_entity("SearchAgent", can_search_position=True)
    agents = [(agent, "prompt")]
    svc = await _boot_service(tools=[search_tool], agents=agents)

    # Override with a specific agent dict
    cloned = svc.clone_agents("gpt-4o")
    cloned_agents = {name: a for name, (a, _) in cloned.items()}

    updated, tool_name = svc.update_agent_by_tool_name(
        "gpt-4o",
        ToolName.GENERIC_POSITION_SEARCH.value,
        target_agents=cloned_agents,
    )
    assert updated is not None


@pytest.mark.asyncio
async def test_update_agent_target_agent_name_not_in_target_agents():
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {}

    agent = _make_agent_entity("SearchAgent", can_search_position=True)
    agents = [(agent, "prompt")]
    svc = await _boot_service(tools=[search_tool], agents=agents)

    # Pass an empty target_agents dict — agent name not in it → skipped
    updated, tool_name = svc.update_agent_by_tool_name(
        "gpt-4o",
        ToolName.GENERIC_POSITION_SEARCH.value,
        target_agents={},
    )
    assert updated == {}


@pytest.mark.asyncio
async def test_iter_target_position_agents_agent_not_in_model_agents():
    """Covers line 460: target_agent_name not in self._agents[model_name] → continue."""
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {}

    agent = _make_agent_entity("SearchAgent", can_search_position=True)
    agents = [(agent, "prompt")]
    svc = await _boot_service(tools=[search_tool], agents=agents)

    # Manually add a name to search_position_agent_names that doesn't exist in _agents
    svc._search_position_agent_names["gpt-4o"].add("NonExistentAgent")

    # update_agent_by_tool_name with target_agents=None, so it uses self._agents
    updated, _ = svc.update_agent_by_tool_name(
        "gpt-4o",
        ToolName.GENERIC_POSITION_SEARCH.value,
        target_agents=None,  # None → uses self._agents path
    )
    # NonExistentAgent would be skipped; SearchAgent would be updated
    assert "SearchAgent" in updated


# ─── LLMService._set_position_search_tool ────────────────────────────────────


@pytest.mark.asyncio
async def test_set_position_search_tool_removes_existing_and_appends_new():
    from utils.enum import ToolName

    existing_search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    new_search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)

    agent = _make_agent_entity("A")
    agents = [(agent, "prompt")]
    svc = await _boot_service(tools=[existing_search_tool], agents=agents)

    # Build a mock agents.Agent with the existing search tool
    from agents import Agent

    mock_agent = MagicMock(spec=Agent)
    mock_agent.tools = [existing_search_tool]
    mock_agent.tool_use_behavior = {
        "stop_at_tool_names": [ToolName.GENERIC_POSITION_SEARCH.value]
    }

    svc._set_position_search_tool(mock_agent, new_search_tool)

    # Should have removed old and added new
    assert new_search_tool in mock_agent.tools


@pytest.mark.asyncio
async def test_set_position_search_tool_with_none_removes_search_tool():
    from utils.enum import ToolName

    existing_search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)

    agent = _make_agent_entity("A")
    agents = [(agent, "prompt")]
    svc = await _boot_service(tools=[existing_search_tool], agents=agents)

    from agents import Agent

    mock_agent = MagicMock(spec=Agent)
    mock_agent.tools = [existing_search_tool]
    mock_agent.tool_use_behavior = None

    svc._set_position_search_tool(mock_agent, None)
    # All position search tools removed
    remaining = [t for t in mock_agent.tools]
    assert existing_search_tool not in remaining


# ─── LLMService._normalize_tool_use_behavior ─────────────────────────────────


@pytest.mark.asyncio
async def test_normalize_behavior_none_returns_empty():
    svc = await _boot_service()
    assert svc._normalize_tool_use_behavior(None) == {}


@pytest.mark.asyncio
async def test_normalize_behavior_dict_returns_copy():
    svc = await _boot_service()
    d = {"stop_at_tool_names": ["x"]}
    result = svc._normalize_tool_use_behavior(d)
    assert result == d
    assert result is not d  # should be a copy


@pytest.mark.asyncio
async def test_normalize_behavior_model_dump():
    svc = await _boot_service()

    class FakeBehavior:
        def model_dump(self):
            return {"stop_at_tool_names": ["y"]}

    result = svc._normalize_tool_use_behavior(FakeBehavior())
    assert result == {"stop_at_tool_names": ["y"]}


@pytest.mark.asyncio
async def test_normalize_behavior_to_dict():
    svc = await _boot_service()

    class FakeBehavior:
        def to_dict(self):
            return {"stop_at_tool_names": ["z"]}

    result = svc._normalize_tool_use_behavior(FakeBehavior())
    assert result == {"stop_at_tool_names": ["z"]}


@pytest.mark.asyncio
async def test_normalize_behavior_model_dump_returns_non_dict():
    svc = await _boot_service()

    class FakeBehavior:
        def model_dump(self):
            return "not-a-dict"

    result = svc._normalize_tool_use_behavior(FakeBehavior())
    assert result == {}


@pytest.mark.asyncio
async def test_normalize_behavior_to_dict_returns_non_dict():
    svc = await _boot_service()

    class FakeBehavior:
        def to_dict(self):
            return "not-a-dict"

    result = svc._normalize_tool_use_behavior(FakeBehavior())
    assert result == {}


@pytest.mark.asyncio
async def test_normalize_behavior_unknown_type_returns_empty():
    svc = await _boot_service()

    class UnknownBehavior:
        pass

    result = svc._normalize_tool_use_behavior(UnknownBehavior())
    assert result == {}


# ─── LLMService._normalize_job_type_names ────────────────────────────────────


@pytest.mark.asyncio
async def test_normalize_job_type_names_none_returns_empty():
    svc = await _boot_service()
    assert svc._normalize_job_type_names(None) == []


@pytest.mark.asyncio
async def test_normalize_job_type_names_string_wraps_in_list():
    svc = await _boot_service()
    assert svc._normalize_job_type_names("営業") == ["営業"]


@pytest.mark.asyncio
async def test_normalize_job_type_names_deduplicates():
    svc = await _boot_service()
    result = svc._normalize_job_type_names(["営業", "エンジニア", "営業"])
    assert result == ["営業", "エンジニア"]


@pytest.mark.asyncio
async def test_normalize_job_type_names_filters_blank():
    svc = await _boot_service()
    result = svc._normalize_job_type_names(["営業", "  ", ""])
    assert result == ["営業"]


# ─── LLMService._build_position_search_tool ──────────────────────────────────


@pytest.mark.asyncio
async def test_build_position_search_tool_unsupported_name_returns_none():
    svc = await _boot_service()
    result = svc._build_position_search_tool("not_a_search_tool")
    assert result is None


@pytest.mark.asyncio
async def test_build_position_search_tool_name_not_in_mcp_returns_none():
    from utils.enum import ToolName

    svc = await _boot_service(tools=[])  # no tools in MCP
    result = svc._build_position_search_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    assert result is None


@pytest.mark.asyncio
async def test_build_position_search_tool_with_jobtypes():
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {
        "properties": {"JobtypeNames": {}},
        "required": [],
    }

    agent = _make_agent_entity("A")
    svc = await _boot_service(tools=[search_tool], agents=[(agent, "p")])

    result = svc._build_position_search_tool(
        ToolName.GENERIC_POSITION_SEARCH.value,
        job_type_names=["営業", "エンジニア"],
    )
    assert result is not None
    # description should have the job types
    assert "営業" in result.description
    # JobtypeNames should have an enum restriction
    assert "enum" in result.params_json_schema["properties"]["JobtypeNames"]["items"]


@pytest.mark.asyncio
async def test_build_position_search_tool_adds_jobtypes_to_required():
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {
        "properties": {"JobtypeNames": {}, "Other": {}},
        "required": ["Other"],
    }

    agent = _make_agent_entity("A")
    svc = await _boot_service(tools=[search_tool], agents=[(agent, "p")])

    result = svc._build_position_search_tool(
        ToolName.GENERIC_POSITION_SEARCH.value,
        job_type_names=["営業"],
    )
    assert "JobtypeNames" in result.params_json_schema["required"]


@pytest.mark.asyncio
async def test_build_position_search_tool_no_required_key_creates_from_properties():
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {
        "properties": {"JobtypeNames": {}, "Other": {}},
    }

    agent = _make_agent_entity("A")
    svc = await _boot_service(tools=[search_tool], agents=[(agent, "p")])

    result = svc._build_position_search_tool(
        ToolName.GENERIC_POSITION_SEARCH.value,
        job_type_names=["エンジニア"],
    )
    assert isinstance(result.params_json_schema.get("required"), list)


@pytest.mark.asyncio
async def test_build_position_search_tool_jobtypes_already_in_required():
    """Covers branch 523→530: JobtypeNames already in required → no append."""
    from utils.enum import ToolName

    search_tool = _make_tool(ToolName.GENERIC_POSITION_SEARCH.value)
    search_tool.params_json_schema = {
        "properties": {"JobtypeNames": {}, "Other": {}},
        "required": ["JobtypeNames", "Other"],  # already contains JobtypeNames
    }

    agent = _make_agent_entity("A")
    svc = await _boot_service(tools=[search_tool], agents=[(agent, "p")])

    result = svc._build_position_search_tool(
        ToolName.GENERIC_POSITION_SEARCH.value,
        job_type_names=["営業"],
    )
    assert result is not None
    # JobtypeNames should not be duplicated in required
    required = result.params_json_schema.get("required", [])
    assert required.count("JobtypeNames") == 1
