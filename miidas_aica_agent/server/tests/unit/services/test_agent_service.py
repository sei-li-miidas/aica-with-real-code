from unittest.mock import Mock

import pytest

pytestmark = pytest.mark.pre_extraction_parity

from domain.entities.agent import Agent
from repositories.agent_repo import AgentRepository
from repositories.prompt_repo import PromptRepository
from services.agent_service import AgentService
from utils.log_utils import clear_session_id, set_session_id


@pytest.fixture(autouse=True)
def session_scope():
    """全テストでセッションIDをセットアップする"""
    set_session_id("test-session-id")
    yield
    clear_session_id()


@pytest.fixture
def mock_agent_repo():
    """AgentRepositoryのモックを作成"""
    return Mock(spec=AgentRepository)


@pytest.fixture
def mock_prompt_repo():
    """PromptRepositoryのモックを作成"""
    return Mock(spec=PromptRepository)


@pytest.fixture
def service(mock_agent_repo, mock_prompt_repo):
    """AgentServiceインスタンスを作成"""
    return AgentService(
        agent_repository=mock_agent_repo,
        prompt_repository=mock_prompt_repo,
    )


def _create_mock_agent(agent_id, name, description=""):
    """Agentモックを作成するヘルパー"""
    agent = Mock(spec=Agent)
    agent.id = agent_id
    agent.name = name
    agent.description = description
    return agent


@pytest.fixture
def sample_agents():
    """テスト用のAgentエンティティリストを作成"""
    return [
        _create_mock_agent(1, "CareerAdvisor", "Career advisor"),
        _create_mock_agent(2, "PositionGuide", "Position guide"),
        _create_mock_agent(3, "PositionChangeAnalyze", "Position change analyze"),
    ]


class TestInit:
    """__init__メソッドのテスト"""

    def test_initializes_with_repositories(self, mock_agent_repo, mock_prompt_repo):
        """両方のリポジトリが正しく保存されること"""
        service = AgentService(
            agent_repository=mock_agent_repo,
            prompt_repository=mock_prompt_repo,
        )

        assert service._agent_repository == mock_agent_repo
        assert service._prompt_repository == mock_prompt_repo


class TestGetAgentsWithPrompts:
    """get_agents_with_promptsメソッドのテスト"""

    def test_returns_agents_with_prompts_successfully(
        self, service, mock_agent_repo, mock_prompt_repo, sample_agents
    ):
        """エージェントとプロンプトのタプルリストが正しく返されること"""
        # AgentRepository.get_agents()のモック
        mock_agent_repo.get_agents.return_value = sample_agents

        # PromptRepository.get_prompt()のモック
        prompt_map = {
            (1, "CareerAdvisor"): "Prompt for CareerAdvisor",
            (2, "PositionGuide"): "Prompt for PositionGuide",
            (3, "PositionChangeAnalyze"): "Prompt for PositionChangeAnalyze",
        }

        def get_prompt_side_effect(agent_id, agent_name):
            return prompt_map[(agent_id, agent_name)]

        mock_prompt_repo.get_prompt.side_effect = get_prompt_side_effect

        # テスト実行
        result = service.get_agents_with_prompts()

        # 検証
        assert len(result) == 3
        assert result[0] == (sample_agents[0], "Prompt for CareerAdvisor")
        assert result[1] == (sample_agents[1], "Prompt for PositionGuide")
        assert result[2] == (sample_agents[2], "Prompt for PositionChangeAnalyze")

        # メソッド呼び出しの検証
        mock_agent_repo.get_agents.assert_called_once()
        mock_prompt_repo.validate_all_prompts.assert_called_once_with(sample_agents)
        assert mock_prompt_repo.get_prompt.call_count == 3

    def test_validates_prompts_before_loading(
        self, service, mock_agent_repo, mock_prompt_repo, sample_agents
    ):
        """プロンプト読み込み前にvalidate_all_prompts()が呼ばれること"""
        mock_agent_repo.get_agents.return_value = sample_agents
        mock_prompt_repo.get_prompt.return_value = "Test prompt"

        # validate_all_promptsの呼び出しを記録
        call_order = []

        def validate_side_effect(agents):
            call_order.append("validate")

        def get_prompt_side_effect(agent_id, agent_name):
            call_order.append("get_prompt")
            return "Test prompt"

        mock_prompt_repo.validate_all_prompts.side_effect = validate_side_effect
        mock_prompt_repo.get_prompt.side_effect = get_prompt_side_effect

        service.get_agents_with_prompts()

        # validate_all_promptsがget_promptより先に呼ばれることを確認
        assert call_order[0] == "validate"
        assert call_order[1] == "get_prompt"

    def test_raises_file_not_found_error_when_validation_fails(
        self, service, mock_agent_repo, mock_prompt_repo, sample_agents
    ):
        """validate_all_prompts()が失敗した場合、エラーが伝播すること"""
        mock_agent_repo.get_agents.return_value = sample_agents
        mock_prompt_repo.validate_all_prompts.side_effect = FileNotFoundError(
            "Missing prompt files"
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            service.get_agents_with_prompts()

        assert "Missing prompt files" in str(exc_info.value)

        # get_prompt()が呼ばれないことを確認
        mock_prompt_repo.get_prompt.assert_not_called()

    def test_raises_file_not_found_error_when_prompt_loading_fails(
        self, service, mock_agent_repo, mock_prompt_repo, sample_agents
    ):
        """get_prompt()が失敗した場合、エラーが伝播すること"""
        mock_agent_repo.get_agents.return_value = sample_agents

        # 2番目のエージェントのプロンプト読み込みで失敗
        def get_prompt_side_effect(agent_id, agent_name):
            if agent_id == 2:
                raise FileNotFoundError(f"Prompt not found for agent {agent_id}")
            return f"Prompt for agent {agent_id}"

        mock_prompt_repo.get_prompt.side_effect = get_prompt_side_effect

        with pytest.raises(FileNotFoundError) as exc_info:
            service.get_agents_with_prompts()

        assert "Prompt not found for agent 2" in str(exc_info.value)

    def test_handles_empty_agent_list(self, service, mock_agent_repo, mock_prompt_repo):
        """エージェントリストが空の場合、空のリストが返されること"""
        mock_agent_repo.get_agents.return_value = []

        result = service.get_agents_with_prompts()

        assert result == []
        mock_agent_repo.get_agents.assert_called_once()
        mock_prompt_repo.validate_all_prompts.assert_called_once_with([])
        mock_prompt_repo.get_prompt.assert_not_called()

    def test_maintains_agent_order(self, service, mock_agent_repo, mock_prompt_repo):
        """返されるリストの順序が保持されること"""
        # 特定の順序でエージェントを作成
        agents = [
            _create_mock_agent(5, "Fifth"),
            _create_mock_agent(1, "First"),
            _create_mock_agent(3, "Third"),
        ]

        mock_agent_repo.get_agents.return_value = agents
        mock_prompt_repo.get_prompt.return_value = "Test prompt"

        result = service.get_agents_with_prompts()

        # 元の順序が保持されていることを確認
        assert result[0][0] == agents[0]
        assert result[1][0] == agents[1]
        assert result[2][0] == agents[2]

    @pytest.mark.parametrize("agent_count", [1, 3, 5])
    def test_with_different_agent_counts(
        self, service, mock_agent_repo, mock_prompt_repo, agent_count
    ):
        """異なる数のエージェントで正しく動作すること"""
        agents = [_create_mock_agent(i, f"Agent{i}") for i in range(1, agent_count + 1)]

        mock_agent_repo.get_agents.return_value = agents
        mock_prompt_repo.get_prompt.return_value = "Test prompt"

        result = service.get_agents_with_prompts()

        assert len(result) == agent_count
        assert mock_prompt_repo.get_prompt.call_count == agent_count

        # 全てのエージェントが結果に含まれることを確認
        result_agents = [item[0] for item in result]
        assert result_agents == agents

    def test_calls_get_prompt_with_correct_arguments(
        self, service, mock_agent_repo, mock_prompt_repo, sample_agents
    ):
        """get_prompt()が正しい引数で呼ばれること"""
        mock_agent_repo.get_agents.return_value = sample_agents
        mock_prompt_repo.get_prompt.return_value = "Test prompt"

        service.get_agents_with_prompts()

        # 各エージェントに対して正しい引数で呼ばれることを確認
        expected_calls = [
            (1, "CareerAdvisor"),
            (2, "PositionGuide"),
            (3, "PositionChangeAnalyze"),
        ]

        actual_calls = [call[0] for call in mock_prompt_repo.get_prompt.call_args_list]
        assert actual_calls == expected_calls
