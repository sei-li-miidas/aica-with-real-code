import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

pytestmark = pytest.mark.pre_extraction_parity
from agents import Agent
from agents.mcp import MCPServerStreamableHttp
from domain.entities.agent import Agent as AgentEntity
from domain.entities.agent_tool import AgentTool
from services.agent_service import AgentService
from services.llm_service import (
    LLMService,
    NotSupportedModelName,
    ToolNotFoundInRepositoryError,
)
from utils.enum import ToolName
from utils.log_utils import clear_session_id, set_session_id


@pytest.fixture(autouse=True)
def session_scope():
    """全テストでセッションIDをセットアップする"""
    set_session_id("test-session-id")
    yield
    clear_session_id()


@pytest.fixture
def mock_mcp_server():
    """MCPServerStreamableHttpのモックを作成"""
    mock = AsyncMock(spec=MCPServerStreamableHttp)
    mock.connect = AsyncMock()
    mock.cleanup = AsyncMock()
    return mock


@pytest.fixture
def mock_agent_service():
    """AgentServiceのモックを作成"""
    return Mock(spec=AgentService)


@pytest.fixture
def mock_job_type_to_tool_repo():
    """JobTypeToPositionSearchToolRepositoryのモックを作成"""
    mock = Mock()
    mock.get_all_tools.return_value = {}
    return mock


@pytest.fixture
def sample_model_list():
    """テスト用のモデルリストを作成"""
    return [
        {
            "model": "gpt-4o",
            "use_for": ["agent"],
            "model_settings": {"temperature": 0.7, "max_tokens": 1000},
        },
        {
            "model": "gpt-4o-mini",
            "use_for": ["summary"],
            "model_settings": {"temperature": 0.3},
        },
    ]


@pytest.fixture
def sample_agents_with_prompts():
    """エージェントとプロンプトのペアを作成"""
    agent1 = _create_mock_agent_entity(1, "CareerAdvisor", [], [])
    agent2 = _create_mock_agent_entity(2, "PositionGuide", [], [])
    return [
        (agent1, "Prompt for CareerAdvisor"),
        (agent2, "Prompt for PositionGuide"),
    ]


def _create_mock_agent_entity(
    agent_id, name, tools=None, next_agents=None, default_agent=False
):
    """AgentEntityモックを作成するヘルパー"""
    agent = Mock(spec=AgentEntity)
    agent.id = agent_id
    agent.name = name
    agent.tools = tools if tools is not None else []
    agent.next_agents = next_agents if next_agents is not None else []
    agent.default_agent = default_agent
    return agent


def _create_mock_agent_tool(tool_name, return_direct=False):
    """AgentToolモックを作成するヘルパー"""
    agent_tool = Mock(spec=AgentTool)
    agent_tool.tool_name = tool_name
    agent_tool.return_direct = return_direct
    return agent_tool


def _create_mock_agent(name):
    """Agentモック（openai-agents）を作成するヘルパー"""
    agent = Mock(spec=Agent)
    agent.name = name
    agent.clone = Mock(return_value=agent)
    agent.handoffs = []
    agent.tool_use_behavior = None
    return agent


@pytest.fixture
def service():
    """LLMServiceインスタンスを作成（未初期化）"""
    return LLMService()


class TestInit:
    """__init__メソッドのテスト"""

    def test_initializes_successfully(self):
        """正しく初期化されること"""
        service = LLMService()

        assert service._server_task is None
        assert service._startup_event is None
        assert service._shutdown_event is None
        assert service._server_error is None
        assert service._mcp_server is None
        assert service._agents == {}


class TestInitAsync:
    """init（非同期初期化）メソッドのテスト"""

    def test_raises_type_error_when_timeout_not_provided(
        self, service, mock_agent_service, sample_model_list
    ):
        """timeout未指定の場合にTypeErrorが発生すること"""
        with pytest.raises(TypeError):
            service.init(
                mcp_url="http://test.com",
                model_list=sample_model_list,
                agent_svc=mock_agent_service,
            )

    @pytest.mark.asyncio
    async def test_initializes_mcp_server_successfully(
        self,
        service,
        mock_agent_service,
        sample_model_list,
        sample_agents_with_prompts,
    ):
        """MCPサーバーが正しく初期化されること"""
        mock_agent_service.get_agents_with_prompts.return_value = (
            sample_agents_with_prompts
        )

        with (
            patch("services.llm_service.MCPServerStreamableHttp") as mock_mcp_class,
            patch(
                "services.llm_service.MCPUtil.get_all_function_tools"
            ) as mock_get_tools,
            patch.object(service, "_mcp_server_lifecycle") as mock_lifecycle,
        ):
            mock_mcp_instance = AsyncMock(spec=MCPServerStreamableHttp)
            mock_mcp_class.return_value = mock_mcp_instance
            mock_get_tools.return_value = []

            # ライフサイクルタスクがすぐに完了するようにモック
            async def lifecycle_mock(*args):
                service._startup_event.set()

            mock_lifecycle.side_effect = lifecycle_mock

            result = await service.init(
                mcp_url="http://test.com",
                timeout=30,
                model_list=sample_model_list,
                agent_svc=mock_agent_service,
            )

            assert result == service
            assert service._mcp_server == mock_mcp_instance
            assert service._startup_event is not None
            assert service._shutdown_event is not None
            mock_mcp_class.assert_called_once()
            mcp_kwargs = mock_mcp_class.call_args.kwargs
            assert mcp_kwargs["params"]["url"] == "http://test.com"
            assert mcp_kwargs["client_session_timeout_seconds"] == 30
            assert mcp_kwargs["max_retry_attempts"] == 5

    @pytest.mark.asyncio
    async def test_initializes_agents_from_agent_service(
        self,
        service,
        mock_agent_service,
        sample_model_list,
        sample_agents_with_prompts,
    ):
        """AgentService.get_agents_with_prompts()が呼ばれること"""
        mock_agent_service.get_agents_with_prompts.return_value = (
            sample_agents_with_prompts
        )

        with (
            patch("services.llm_service.MCPServerStreamableHttp") as mock_mcp_class,
            patch(
                "services.llm_service.MCPUtil.get_all_function_tools"
            ) as mock_get_tools,
            patch.object(service, "_mcp_server_lifecycle") as mock_lifecycle,
        ):
            mock_mcp_class.return_value = AsyncMock(spec=MCPServerStreamableHttp)
            mock_get_tools.return_value = []

            async def lifecycle_mock(*args):
                service._startup_event.set()

            mock_lifecycle.side_effect = lifecycle_mock

            await service.init(
                mcp_url="http://test.com",
                timeout=30,
                model_list=sample_model_list,
                agent_svc=mock_agent_service,
            )

            mock_agent_service.get_agents_with_prompts.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_exception_when_no_agent_models_defined(
        self,
        service,
        mock_agent_service,
        sample_agents_with_prompts,
    ):
        """\"agent\"用のモデルがない場合にExceptionが発生すること"""
        mock_agent_service.get_agents_with_prompts.return_value = (
            sample_agents_with_prompts
        )

        # summaryモデルのみのリスト
        model_list_no_agent = [
            {
                "model": "gpt-4o-mini",
                "use_for": ["summary"],
                "model_settings": {"temperature": 0.3},
            }
        ]

        with (
            patch("services.llm_service.MCPServerStreamableHttp") as mock_mcp_class,
            patch(
                "services.llm_service.MCPUtil.get_all_function_tools"
            ) as mock_get_tools,
            patch.object(service, "_mcp_server_lifecycle") as mock_lifecycle,
        ):
            mock_mcp_class.return_value = AsyncMock(spec=MCPServerStreamableHttp)
            mock_get_tools.return_value = []

            async def lifecycle_mock(*args):
                service._startup_event.set()

            mock_lifecycle.side_effect = lifecycle_mock

            with pytest.raises(Exception) as exc_info:
                await service.init(
                    mcp_url="http://test.com",
                    timeout=30,
                    model_list=model_list_no_agent,
                    agent_svc=mock_agent_service,
                )

            assert "Agent用のモデルが定義されていません" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cleans_up_on_initialization_failure(
        self,
        service,
        mock_agent_service,
        sample_agents_with_prompts,
    ):
        """初期化失敗時にシャットダウンが呼ばれること"""
        mock_agent_service.get_agents_with_prompts.side_effect = Exception(
            "Initialization error"
        )

        with (
            patch("services.llm_service.MCPServerStreamableHttp") as mock_mcp_class,
            patch.object(service, "_mcp_server_lifecycle") as mock_lifecycle,
        ):
            mock_mcp_class.return_value = AsyncMock(spec=MCPServerStreamableHttp)

            async def lifecycle_mock(*args):
                service._startup_event.set()

            mock_lifecycle.side_effect = lifecycle_mock

            with pytest.raises(Exception) as exc_info:
                await service.init(
                    mcp_url="http://test.com",
                    timeout=30,
                    model_list=[
                        {
                            "model": "gpt-4o",
                            "use_for": ["agent"],
                            "model_settings": {},
                        }
                    ],
                    agent_svc=mock_agent_service,
                )

            assert "Initialization error" in str(exc_info.value)
            # shutdown_eventがセットされることを確認
            assert service._shutdown_event.is_set()


class TestShutdown:
    """shutdownメソッドのテスト"""

    @pytest.mark.asyncio
    async def test_shuts_down_successfully(self, service):
        """_shutdown_eventがセットされること"""
        service._shutdown_event = asyncio.Event()
        service._server_error = None

        async def mock_task():
            pass

        service._server_task = asyncio.create_task(mock_task())

        await service.shutdown(None)

        assert service._shutdown_event.is_set()
        assert service._server_task is None
        assert service._mcp_server is None

    @pytest.mark.asyncio
    async def test_handles_no_server_task(self, service):
        """_server_taskがNoneの場合にエラーなく終了すること"""
        service._server_task = None

        # 例外が発生しないことを確認
        await service.shutdown(None)

    @pytest.mark.asyncio
    async def test_raises_error_if_server_error_occurred(self, service):
        """_server_errorがある場合に例外が発生すること"""
        service._shutdown_event = asyncio.Event()
        service._server_error = Exception("Server error occurred")

        async def mock_task():
            pass

        service._server_task = asyncio.create_task(mock_task())

        with pytest.raises(Exception) as exc_info:
            await service.shutdown(None)

        assert "Server error occurred" in str(exc_info.value)


class TestMcpServerLifecycle:
    """_mcp_server_lifecycleメソッドのテスト"""

    @pytest.mark.asyncio
    async def test_connects_to_mcp_server(self, service):
        """connect()が呼ばれること"""
        mock_mcp_server = AsyncMock(spec=MCPServerStreamableHttp)
        service._mcp_server = mock_mcp_server
        service._startup_event = asyncio.Event()
        service._shutdown_event = asyncio.Event()

        with patch(
            "services.llm_service.MCPUtil.get_all_function_tools"
        ) as mock_get_tools:
            mock_get_tools.return_value = []

            # ライフサイクルタスクを起動
            task = asyncio.create_task(service._mcp_server_lifecycle("http://test.com"))

            # startup_eventを待つ
            await service._startup_event.wait()

            # shutdownをトリガー
            service._shutdown_event.set()
            await task

            mock_mcp_server.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleans_up_mcp_server_on_shutdown(self, service):
        """cleanup()が呼ばれること"""
        mock_mcp_server = AsyncMock(spec=MCPServerStreamableHttp)
        service._mcp_server = mock_mcp_server
        service._startup_event = asyncio.Event()
        service._shutdown_event = asyncio.Event()

        with patch(
            "services.llm_service.MCPUtil.get_all_function_tools"
        ) as mock_get_tools:
            mock_get_tools.return_value = []

            task = asyncio.create_task(service._mcp_server_lifecycle("http://test.com"))

            await service._startup_event.wait()
            service._shutdown_event.set()
            await task

            mock_mcp_server.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_connection_error(self, service):
        """接続エラー時に_server_errorが設定されること"""
        mock_mcp_server = AsyncMock(spec=MCPServerStreamableHttp)
        mock_mcp_server.connect.side_effect = Exception("Connection failed")
        service._mcp_server = mock_mcp_server
        service._startup_event = asyncio.Event()
        service._shutdown_event = asyncio.Event()

        task = asyncio.create_task(service._mcp_server_lifecycle("http://test.com"))

        await service._startup_event.wait()

        # エラーが記録されることを確認
        assert service._server_error is not None
        assert "Connection failed" in str(service._server_error)

        # クリーンアップ
        if not service._shutdown_event.is_set():
            service._shutdown_event.set()
        await task

    @pytest.mark.asyncio
    async def test_handles_cancel_scope_runtime_error_gracefully(self, service, caplog):
        """特定のRuntime Errorが警告として処理されること"""
        mock_mcp_server = AsyncMock(spec=MCPServerStreamableHttp)
        mock_mcp_server.cleanup.side_effect = RuntimeError(
            "Attempted to exit cancel scope in a different task"
        )
        service._mcp_server = mock_mcp_server
        service._startup_event = asyncio.Event()
        service._shutdown_event = asyncio.Event()

        with patch(
            "services.llm_service.MCPUtil.get_all_function_tools"
        ) as mock_get_tools:
            mock_get_tools.return_value = []

            task = asyncio.create_task(service._mcp_server_lifecycle("http://test.com"))

            await service._startup_event.wait()
            service._shutdown_event.set()
            await task

            # 警告ログを確認
            assert any(
                "CancelScopeの制約によりMCPサーバーのクリーンアップでRuntimeErrorを無視します"
                in record.message
                for record in caplog.records
            )


class TestInitAgents:
    """_init_agentsメソッドのテスト"""

    @pytest.mark.asyncio
    async def test_creates_agents_from_model_list(
        self, service, mock_agent_service, sample_agents_with_prompts
    ):
        """model_listの各モデルに対してエージェントが作成されること"""
        mock_mcp_server = AsyncMock(spec=MCPServerStreamableHttp)
        service._mcp_server = mock_mcp_server

        model_list = [
            {
                "model": "gpt-4o",
                "use_for": ["agent"],
                "model_settings": {"temperature": 0.7},
            }
        ]

        mock_agent_service.get_agents_with_prompts.return_value = (
            sample_agents_with_prompts
        )

        with (
            patch("services.llm_service.Agent") as mock_agent_class,
        ):
            service._all_tools = []
            mock_agent_class.return_value = _create_mock_agent("TestAgent")

            await service._init_agents(model_list, mock_agent_service)

            # エージェントが作成されたことを確認
            assert "gpt-4o" in service._agents
            assert len(service._agents["gpt-4o"]) == 2  # CareerAdvisor と PositionGuide

    @pytest.mark.asyncio
    async def test_sets_up_agent_tools_correctly(self, service, mock_agent_service):
        """エージェントのツールが正しく設定されること"""
        tool1 = _create_mock_agent_tool("tool1")
        tool2 = _create_mock_agent_tool("tool2")

        agent1 = _create_mock_agent_entity(1, "Agent1", [tool1, tool2], [])
        agents_with_prompts = [(agent1, "Prompt for Agent1")]

        mock_agent_service.get_agents_with_prompts.return_value = agents_with_prompts

        mock_mcp_server = AsyncMock(spec=MCPServerStreamableHttp)
        service._mcp_server = mock_mcp_server

        model_list = [
            {
                "model": "gpt-4o",
                "use_for": ["agent"],
                "model_settings": {"temperature": 0.7},
            }
        ]

        # MCPツールモック
        mcp_tool1 = Mock()
        mcp_tool1.name = "tool1"
        mcp_tool2 = Mock()
        mcp_tool2.name = "tool2"

        with (
            patch("services.llm_service.Agent") as mock_agent_class,
        ):
            service._all_tools = [mcp_tool1, mcp_tool2]

            created_agents = []

            def agent_init(*args, **kwargs):
                agent = _create_mock_agent(kwargs.get("name", "TestAgent"))
                created_agents.append((args, kwargs))
                return agent

            mock_agent_class.side_effect = agent_init

            await service._init_agents(model_list, mock_agent_service)

            # ツールが正しく渡されたことを確認
            assert len(created_agents) == 1
            tools_passed = created_agents[0][1]["tools"]
            assert len(tools_passed) == 2
            assert mcp_tool1 in tools_passed
            assert mcp_tool2 in tools_passed

    @pytest.mark.asyncio
    async def test_raises_error_for_non_existent_tools(
        self, service, mock_agent_service
    ):
        """存在しないツールでエラーが発生すること"""
        tool1 = _create_mock_agent_tool("tool1")
        tool_nonexistent = _create_mock_agent_tool("nonexistent_tool")

        agent1 = _create_mock_agent_entity(1, "Agent1", [tool1, tool_nonexistent], [])
        agents_with_prompts = [(agent1, "Prompt for Agent1")]

        mock_agent_service.get_agents_with_prompts.return_value = agents_with_prompts

        mock_mcp_server = AsyncMock(spec=MCPServerStreamableHttp)
        service._mcp_server = mock_mcp_server

        model_list = [
            {
                "model": "gpt-4o",
                "use_for": ["agent"],
                "model_settings": {"temperature": 0.7},
            }
        ]

        # tool1のみ存在
        mcp_tool1 = Mock()
        mcp_tool1.name = "tool1"

        service._all_tools = [mcp_tool1]

        with pytest.raises(ToolNotFoundInRepositoryError) as exc_info:
            await service._init_agents(model_list, mock_agent_service)

        assert "nonexistent_tool" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sets_up_handoffs_correctly(self, service, mock_agent_service):
        """ハンドオフが正しく設定されること"""
        # エージェント設定
        agent1 = _create_mock_agent_entity(1, "Agent1", [], [])
        agent2 = _create_mock_agent_entity(2, "Agent2", [], [])

        # Agent1からAgent2へのハンドオフ
        next_agent_mock = Mock()
        next_agent_mock.dest_agent = agent2
        agent1.next_agents = [next_agent_mock]

        agents_with_prompts = [
            (agent1, "Prompt for Agent1"),
            (agent2, "Prompt for Agent2"),
        ]

        mock_agent_service.get_agents_with_prompts.return_value = agents_with_prompts

        mock_mcp_server = AsyncMock(spec=MCPServerStreamableHttp)
        service._mcp_server = mock_mcp_server

        model_list = [
            {
                "model": "gpt-4o",
                "use_for": ["agent"],
                "model_settings": {"temperature": 0.7},
            }
        ]

        with (
            patch("services.llm_service.Agent") as mock_agent_class,
        ):
            service._all_tools = []

            created_agents = {}

            def agent_init(*args, **kwargs):
                name = kwargs.get("name", "TestAgent")
                agent = _create_mock_agent(name)
                created_agents[name] = agent
                return agent

            mock_agent_class.side_effect = agent_init

            await service._init_agents(model_list, mock_agent_service)

            # Agent1のハンドオフにAgent2が含まれていることを確認
            agent1_instance = created_agents["Agent1"]
            assert len(agent1_instance.handoffs) == 1
            assert agent1_instance.handoffs[0] == created_agents["Agent2"]


class TestCloneAgents:
    """clone_agentsメソッドのテスト"""

    def test_clones_agents_successfully(self, service):
        """エージェントのクローンが正しく作成されること"""
        agent1 = _create_mock_agent("Agent1")
        agent2 = _create_mock_agent("Agent2")

        service._agents = {
            "gpt-4o": {
                "Agent1": (agent1, False),
                "Agent2": (agent2, True),
            }
        }

        cloned_agents = service.clone_agents("gpt-4o")

        assert len(cloned_agents) == 2
        assert "Agent1" in cloned_agents
        assert "Agent2" in cloned_agents
        assert cloned_agents["Agent1"][1] is False  # default_agent flag
        assert cloned_agents["Agent2"][1] is True  # default_agent flag

        # clone()が呼ばれたことを確認
        agent1.clone.assert_called_once()
        agent2.clone.assert_called_once()

    def test_raises_not_supported_model_name_for_invalid_model(self, service):
        """存在しないモデル名でエラーが発生すること"""
        service._agents = {"gpt-4o": {}}

        with pytest.raises(NotSupportedModelName) as exc_info:
            service.clone_agents("invalid-model")

        assert "Unsupported model name: invalid-model" in str(exc_info.value)

    def test_preserves_default_agent_flag(self, service):
        """default_agentフラグが正しく保持されること"""
        agent1 = _create_mock_agent("CareerAdvisor")
        agent2 = _create_mock_agent("PositionGuide")

        service._agents = {
            "gpt-4o": {
                "CareerAdvisor": (agent1, True),  # default_agent=True
                "PositionGuide": (agent2, False),  # default_agent=False
            }
        }

        cloned_agents = service.clone_agents("gpt-4o")

        assert cloned_agents["CareerAdvisor"][1] is True
        assert cloned_agents["PositionGuide"][1] is False

    def test_replaces_existing_position_search_tools_when_configured_tool_is_set(
        self, service
    ):
        """職種別ツールを設定する際、既存のポジション検索ツールが共存しないこと"""
        position_agent = _create_mock_agent("PositionSearch")
        generic_tool = Mock()
        generic_tool.name = ToolName.GENERIC_POSITION_SEARCH.value
        unrelated_tool = Mock()
        unrelated_tool.name = "save_user_preference"
        position_agent.tools = [generic_tool, unrelated_tool]

        service._agents = {
            "gpt-4o": {
                "PositionSearch": (position_agent, False),
            }
        }
        service._search_position_agent_names = {"gpt-4o": {"PositionSearch"}}

        configured_tool = Mock()
        configured_tool.name = ToolName.IT_POSITION_SEARCH.value
        with patch.object(
            service,
            "_build_position_search_tool",
            return_value=configured_tool,
        ):
            cloned_agents = service.clone_agents(
                "gpt-4o",
                jobtype_names=["SE"],
                tool_name=ToolName.IT_POSITION_SEARCH.value,
            )

        cloned_tool_names = [
            tool.name for tool in cloned_agents["PositionSearch"][0].tools
        ]
        assert ToolName.GENERIC_POSITION_SEARCH.value not in cloned_tool_names
        assert ToolName.IT_POSITION_SEARCH.value in cloned_tool_names
        assert "save_user_preference" in cloned_tool_names

    def test_replaces_stop_at_tool_names_with_single_position_search_tool(
        self, service
    ):
        """clone_agentsでstop_at_tool_names内の既存検索ツール名も置換されること"""
        position_agent = _create_mock_agent("PositionSearch")
        generic_tool = Mock()
        generic_tool.name = ToolName.GENERIC_POSITION_SEARCH.value
        unrelated_tool = Mock()
        unrelated_tool.name = "save_user_preference"
        position_agent.tools = [generic_tool, unrelated_tool]
        position_agent.tool_use_behavior = {
            "stop_at_tool_names": [
                ToolName.GENERIC_POSITION_SEARCH.value,
                "save_user_preference",
            ]
        }

        service._agents = {
            "gpt-4o": {
                "PositionSearch": (position_agent, False),
            }
        }
        service._search_position_agent_names = {"gpt-4o": {"PositionSearch"}}

        configured_tool = Mock()
        configured_tool.name = ToolName.IT_POSITION_SEARCH.value
        with patch.object(
            service,
            "_build_position_search_tool",
            return_value=configured_tool,
        ):
            cloned_agents = service.clone_agents(
                "gpt-4o",
                jobtype_names=["SE"],
                tool_name=ToolName.IT_POSITION_SEARCH.value,
            )

        behavior = cloned_agents["PositionSearch"][0].tool_use_behavior
        stop_at_tool_names = behavior.get("stop_at_tool_names", [])
        assert ToolName.GENERIC_POSITION_SEARCH.value not in stop_at_tool_names
        assert ToolName.IT_POSITION_SEARCH.value in stop_at_tool_names
        assert "save_user_preference" in stop_at_tool_names
