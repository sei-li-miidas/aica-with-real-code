import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.llm_service import LLMService, NotSupportedModelName

pytestmark = pytest.mark.pre_extraction_parity


@pytest.fixture
def service():
    return LLMService()


@pytest.mark.asyncio
async def test_init_raises_when_lifecycle_already_running(service):
    service._server_task = Mock()
    service._server_task.done.return_value = False

    gather_mock = AsyncMock(return_value=[])
    with (
        patch("services.llm_service.asyncio.gather", gather_mock),
        patch("services.llm_service.MCPServerStreamableHttp"),
    ):
        with pytest.raises(RuntimeError, match="既に起動しています"):
            await service.init(
                "http://mcp",
                10,
                [{"model": "m", "use_for": ["agent"], "model_settings": {}}],
                Mock(),
            )


@pytest.mark.asyncio
async def test_init_raises_server_error_after_startup_wait(service):
    async def _lifecycle(*_args):
        service._server_error = RuntimeError("boom")
        service._startup_event.set()

    with (
        patch("services.llm_service.MCPServerStreamableHttp"),
        patch.object(service, "_mcp_server_lifecycle", side_effect=_lifecycle),
        patch("services.llm_service.asyncio.gather", AsyncMock(return_value=[])),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            await service.init(
                "http://mcp",
                10,
                [{"model": "m", "use_for": ["agent"], "model_settings": {}}],
                Mock(),
            )


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_raises_when_server_not_initialized(service):
    service._mcp_server = None
    with pytest.raises(RuntimeError, match="初期化されていません"):
        await service._mcp_server_lifecycle("http://mcp")


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_logs_cleanup_runtime_error_other_message(service):
    mcp = AsyncMock()
    mcp.connect.side_effect = RuntimeError("connect error")
    mcp.cleanup.side_effect = RuntimeError("some other runtime")
    service._mcp_server = mcp
    service._startup_event = asyncio.Event()
    service._shutdown_event = asyncio.Event()

    await service._mcp_server_lifecycle("http://mcp")


@pytest.mark.asyncio
async def test_mcp_server_lifecycle_logs_cleanup_generic_exception_and_sets_startup_in_finally(
    service,
):
    startup = Mock()
    startup.is_set.side_effect = [True, False]
    startup.set = Mock()

    shutdown = Mock()
    shutdown.is_set.return_value = False
    shutdown.set = Mock()
    shutdown.wait = AsyncMock(side_effect=RuntimeError("wait failed"))

    mcp = AsyncMock()
    mcp.connect = AsyncMock()
    mcp.cleanup.side_effect = Exception("cleanup failed")

    service._mcp_server = mcp
    service._startup_event = startup
    service._shutdown_event = shutdown

    await service._mcp_server_lifecycle("http://mcp")

    assert startup.set.call_count >= 1
    shutdown.set.assert_called()


@pytest.mark.asyncio
async def test_init_agents_applies_reasoning_and_stop_at_tool_behavior(service):
    agent_tool = SimpleNamespace(tool_name="tool-a", return_direct=True)
    agent_entity = SimpleNamespace(
        name="AgentA",
        tools=[agent_tool],
        next_agents=[],
        default_agent=True,
        can_search_position=False,
    )
    agent_svc = Mock()
    agent_svc.get_agents_with_prompts.return_value = [(agent_entity, "prompt")]

    service._all_tools = [SimpleNamespace(name="tool-a")]

    with (
        patch("services.llm_service.Agent") as agent_ctor,
        patch(
            "services.llm_service.Reasoning.model_validate",
            return_value="reasoning-obj",
        ) as model_validate,
        patch("services.llm_service.ModelSettings", return_value=SimpleNamespace()),
    ):
        created_agent = Mock()
        created_agent.handoffs = []
        created_agent.tool_use_behavior = None
        agent_ctor.return_value = created_agent

        await service._init_agents(
            [
                {
                    "model": "gpt-x",
                    "use_for": ["agent"],
                    "model_settings": {"reasoning": {"effort": "medium"}},
                }
            ],
            agent_svc,
        )

    model_validate.assert_called_once()
    assert created_agent.tool_use_behavior == {"stop_at_tool_names": ["tool-a"]}


def test_clone_agents_returns_clones_when_position_tool_build_fails(service):
    base_agent = Mock()
    base_agent.clone.return_value = Mock()
    service._agents = {"gpt": {"A": (base_agent, False)}}
    service._search_position_agent_names = {"gpt": {"A"}}

    with patch.object(service, "_build_position_search_tool", return_value=None):
        cloned = service.clone_agents(
            "gpt", jobtype_names=["SE"], tool_name="search_job_postings"
        )

    assert "A" in cloned


def test_clone_agents_skips_missing_target_agents(service):
    base_agent = Mock()
    cloned_agent = Mock()
    cloned_agent.tools = []
    cloned_agent.tool_use_behavior = None
    base_agent.clone.return_value = cloned_agent
    service._agents = {"gpt": {"A": (base_agent, False)}}
    service._search_position_agent_names = {"gpt": {"A", "Missing"}}

    configured_tool = SimpleNamespace(name="search_job_postings")
    with patch.object(
        service, "_build_position_search_tool", return_value=configured_tool
    ):
        cloned = service.clone_agents(
            "gpt", jobtype_names=["SE"], tool_name="search_job_postings"
        )

    assert "A" in cloned


def test_update_agent_by_tool_name_paths(service):
    service._agents = {"gpt": {"A": (Mock(), False)}}
    service._search_position_agent_names = {"gpt": {"A"}}

    with pytest.raises(NotSupportedModelName):
        service.update_agent_by_tool_name("unknown", None)

    service._search_position_agent_names = {"gpt": set()}
    assert service.update_agent_by_tool_name("gpt", None) == (None, None)

    service._search_position_agent_names = {"gpt": {"A"}}
    with patch.object(
        service, "_update_position_search_agents", return_value={"A": Mock()}
    ) as upd:
        updated, tool_name = service.update_agent_by_tool_name("gpt", None)
    assert updated is not None and tool_name is None
    upd.assert_called_once()

    with patch.object(service, "_build_position_search_tool", return_value=None):
        assert service.update_agent_by_tool_name("gpt", "search_job_postings") == (
            None,
            None,
        )

    with (
        patch.object(
            service,
            "_build_position_search_tool",
            return_value=SimpleNamespace(name="search_job_postings"),
        ),
        patch.object(
            service, "_update_position_search_agents", return_value={"A": Mock()}
        ),
    ):
        updated, tool_name = service.update_agent_by_tool_name(
            "gpt", "search_job_postings"
        )
    assert updated is not None and tool_name == "search_job_postings"


def test_update_position_search_agents_and_iter_target_agents_paths(service):
    agent_a = Mock()
    model_agents = {"A": (agent_a, False)}
    service._agents = {"gpt": model_agents}

    # _iter_target_position_agents with target_agents provided and missing member
    items = list(
        service._iter_target_position_agents("gpt", {"A", "B"}, {"A": agent_a})
    )
    assert items == [("A", agent_a)]

    # _iter_target_position_agents fallback to self._agents and skip missing
    items = list(service._iter_target_position_agents("gpt", {"A", "B"}, None))
    assert items == [("A", agent_a)]

    with patch.object(service, "_set_position_search_tool") as setter:
        result = service._update_position_search_agents("gpt", {"A", "B"}, None, None)
    assert result == {"A": agent_a}
    setter.assert_called_once_with(agent_a, None)


def test_build_position_search_tool_residual_paths(service):
    assert service._build_position_search_tool("not-supported", None) is None

    service._all_tools = [SimpleNamespace(name="other")]
    assert service._build_position_search_tool("search_job_postings", None) is None

    tool = SimpleNamespace(
        name="search_job_postings",
        description="desc",
        params_json_schema={
            "properties": {
                "Keyword": {"type": "string"},
                "JobtypeNames": {"type": "array"},
            }
        },
    )
    service._all_tools = [tool]

    built = service._build_position_search_tool("search_job_postings", ["SE", "PM"])
    assert built is not None
    assert "JobtypeNames" in built.params_json_schema["properties"]
    assert "required" in built.params_json_schema


def test_build_position_search_tool_appends_jobtypenames_to_required_when_list_exists(
    service,
):
    tool = SimpleNamespace(
        name="search_job_postings",
        description="desc",
        params_json_schema={
            "properties": {
                "Keyword": {"type": "string"},
                "JobtypeNames": {"type": "array"},
            },
            "required": ["Keyword"],
        },
    )
    service._all_tools = [tool]

    built = service._build_position_search_tool("search_job_postings", ["SE"])
    assert built is not None
    assert "JobtypeNames" in built.params_json_schema["required"]


def test_normalize_helpers_and_find_tool(service):
    assert service._normalize_job_type_names(" SE ") == ["SE"]
    assert service._normalize_job_type_names(["SE", "", "SE", " PM "]) == ["SE", "PM"]

    t1 = SimpleNamespace(name="a")
    t2 = SimpleNamespace(name="b")
    service._all_tools = [t1, t2]
    assert service._find_tool_by_name("b") is t2

    class WithModelDump:
        def model_dump(self):
            return {"x": 1}

    class WithToDict:
        def to_dict(self):
            return {"y": 2}

    class Unknown:
        pass

    assert service._normalize_tool_use_behavior(WithModelDump()) == {"x": 1}
    assert service._normalize_tool_use_behavior(WithToDict()) == {"y": 2}
    assert service._normalize_tool_use_behavior(Unknown()) == {}
