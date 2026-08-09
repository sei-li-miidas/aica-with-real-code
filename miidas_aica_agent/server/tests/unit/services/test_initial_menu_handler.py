import pytest
from domain.entities.workflow_definition import (
    DisplayType,
    SelectionType,
    WorkflowDefinition,
)
from services.workflow_handlers.initial_menu import InitialMenuHandler
from services.llm_service import AgentName
from utils.const import INITIAL_MENU_WORKFLOW_ID, JOB_MATCH_DIAGNOSIS_WORKFLOW_ID, POSITION_CHANGE_ANALYZE_WORKFLOW_ID


@pytest.fixture
def initial_menu_definition():
    """initial_menu ワークフロー定義のフィクスチャ"""
    return WorkflowDefinition.model_validate({
        "id": INITIAL_MENU_WORKFLOW_ID,
        "name": "初期メニュー",
        "displayType": DisplayType.INLINE,
        "steps": [
            {
                "id": 1,
                "question": "ご希望の条件を選択してください",
                "questionPrompt": "本日はどのようなご相談を希望されますか？",
                "selectionType": SelectionType.SINGLE,
                "options": [
                    {"label": "求人検索", "value": 1, "allowFreeText": False},
                    {"label": "仕事の性質に基づく適職診断", "value": 2, "allowFreeText": False},
                    {"label": "転職理由診断", "value": 3, "allowFreeText": False},
                ],
            }
        ],
    })


@pytest.fixture
def handler(initial_menu_definition):
    return InitialMenuHandler(INITIAL_MENU_WORKFLOW_ID, initial_menu_definition)


class TestInitialMenuHandler:

    @pytest.mark.asyncio
    async def test_value1_sets_career_advisor_agent(self, handler):
        """value=1（求人検索）で CareerAdvisor が設定されること"""
        structured_answers = {"1": [{"value": 1, "label": "求人検索"}]}
        result = await handler.perform_post_processing(structured_answers)

        assert result.next_agent_name == AgentName.CAREER_ADVISOR
        assert result.next_workflow_id is None
        assert result.message != ""

    @pytest.mark.asyncio
    async def test_value2_sets_career_advisor_and_job_match_workflow(self, handler):
        """value=2（適職診断）で CareerAdvisor + job_match_diagnosis ワークフローが設定されること"""
        structured_answers = {"1": [{"value": 2, "label": "仕事の性質に基づく適職診断"}]}
        result = await handler.perform_post_processing(structured_answers)

        assert result.next_agent_name == AgentName.CAREER_ADVISOR
        assert result.next_workflow_id == JOB_MATCH_DIAGNOSIS_WORKFLOW_ID

    @pytest.mark.asyncio
    async def test_value3_sets_position_change_analyze_workflow(self, handler):
        """value=3（転職理由診断）で PositionChangeAnalyze + position_change_analyze ワークフローが設定されること"""
        structured_answers = {"1": [{"value": 3, "label": "転職理由診断"}]}
        result = await handler.perform_post_processing(structured_answers)

        assert result.next_agent_name == AgentName.POSITION_CHANGE_ANALYZE
        assert result.next_workflow_id == POSITION_CHANGE_ANALYZE_WORKFLOW_ID
        assert result.message == ""

    @pytest.mark.asyncio
    async def test_unknown_value_raises_value_error(self, handler):
        """定義外の value で ValueError が発生すること"""
        structured_answers = {"1": [{"value": 99, "label": "未知の選択肢"}]}
        with pytest.raises(ValueError, match="不明な選択値"):
            await handler.perform_post_processing(structured_answers)

    @pytest.mark.asyncio
    async def test_empty_step_answers_raises_value_error(self, handler):
        """step1 の回答が空の場合に ValueError が発生すること"""
        structured_answers = {"1": []}
        with pytest.raises(ValueError, match="不明な選択値"):
            await handler.perform_post_processing(structured_answers)

    @pytest.mark.asyncio
    async def test_missing_step1_raises_value_error(self, handler):
        """step1 の回答がない場合に ValueError が発生すること"""
        structured_answers = {}
        with pytest.raises(ValueError, match="不明な選択値"):
            await handler.perform_post_processing(structured_answers)

    @pytest.mark.asyncio
    async def test_value1_message_is_nonempty_and_mentions_job_search(self, handler):
        """value=1 のメッセージが求人検索の文脈を含むこと"""
        structured_answers = {"1": [{"value": 1, "label": "求人検索"}]}
        result = await handler.perform_post_processing(structured_answers)

        assert "求人" in result.message

    @pytest.mark.asyncio
    async def test_value3_message_is_empty(self, handler):
        """value=3 のメッセージが空文字であること（ワークフローが担うため）"""
        structured_answers = {"1": [{"value": 3, "label": "転職理由診断"}]}
        result = await handler.perform_post_processing(structured_answers)

        assert result.message == ""

    @pytest.mark.asyncio
    async def test_missing_value_key_in_option_raises_value_error(self, handler):
        """value キーが存在しない選択肢（get が None を返すケース）で ValueError が発生すること"""
        structured_answers = {"1": [{"label": "求人検索"}]}
        with pytest.raises(ValueError, match="不明な選択値"):
            await handler.perform_post_processing(structured_answers)
