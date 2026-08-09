import pytest
from unittest.mock import AsyncMock, MagicMock
from domain.entities.workflow_definition import (
    DisplayType,
    SelectionType,
    WorkflowDefinition,
)
from services.llm_service import AgentName
from services.workflow_handlers.position_change_analyze import PositionChangeAnalyzeHandler
from utils.const import JOB_MATCH_DIAGNOSIS_WORKFLOW_ID, POSITION_CHANGE_ANALYZE_WORKFLOW_ID


@pytest.fixture
def workflow_definition():
    return WorkflowDefinition.model_validate({
        "id": POSITION_CHANGE_ANALYZE_WORKFLOW_ID,
        "name": "転職理由診断",
        "displayType": DisplayType.MODAL,
        "steps": [
            {
                "id": 1,
                "question": "転職を考えたきっかけを教えてください。",
                "questionPrompt": "P1",
                "selectionType": SelectionType.MULTIPLE,
                "options": [
                    {"label": "給与や昇給の見込みが低い", "value": 1, "allowFreeText": False},
                    {"label": "その他", "value": 6, "allowFreeText": True},
                ],
            },
            {
                "id": 2,
                "question": "やりがいを感じる瞬間を教えてください。",
                "questionPrompt": "P2",
                "selectionType": SelectionType.MULTIPLE,
                "options": [
                    {"label": "人に感謝された時", "value": 1, "allowFreeText": False},
                    {"label": "その他", "value": 6, "allowFreeText": True},
                ],
            },
            {
                "id": 3,
                "question": "今後のキャリアで重視することを教えてください。",
                "questionPrompt": "P3",
                "selectionType": SelectionType.MULTIPLE,
                "options": [
                    {"label": "年収を上げたい", "value": 1, "allowFreeText": False},
                    {"label": "その他", "value": 6, "allowFreeText": True},
                ],
            },
            {
                "id": 4,
                "question": "現在の環境は何点ですか？",
                "questionPrompt": "P4",
                "selectionType": SelectionType.SINGLE,
                "options": [
                    {"label": "80点以上", "value": 1, "allowFreeText": False},
                    {"label": "30点未満", "value": 4, "allowFreeText": False},
                ],
            },
            {
                "id": 5,
                "question": "次はどのように進めますか？",
                "questionPrompt": "P5",
                "selectionType": SelectionType.SINGLE,
                "options": [
                    {"label": "求人を探す", "value": 1, "allowFreeText": False},
                    {"label": "向いている仕事を見つける", "value": 2, "allowFreeText": False},
                    {"label": "会員登録して転職活動を始める", "value": 3, "allowFreeText": False},
                    {"label": "その他", "value": 4, "allowFreeText": True},
                ],
            },
        ],
    })


@pytest.fixture
def mock_summary_svc():
    svc = MagicMock()
    svc.generate_summary = AsyncMock(
        return_value={
            "summary": "転職軸まとめ",
            "explanation": "AIの視点まとめ",
            "keywords": ["フルリモート", "フレックス"],
        }
    )
    return svc


@pytest.fixture
def handler(workflow_definition, mock_summary_svc):
    return PositionChangeAnalyzeHandler(
        POSITION_CHANGE_ANALYZE_WORKFLOW_ID, mock_summary_svc, workflow_definition
    )


class TestGetValidatedAnswersForSummary:
    def test_step1_to_4_extracted(self, handler):
        raw_answers = {
            "1": [{"label": "給与や昇給の見込みが低い", "value": 1}],
            "2": [{"label": "人に感謝された時", "value": 1}],
            "3": [{"label": "年収を上げたい", "value": 1}],
            "4": [{"label": "80点以上", "value": 1}],
        }
        result = handler.get_validated_answers_for_summary(raw_answers)
        assert set(result.keys()) == {"1", "2", "3", "4"}

    def test_step5_not_included(self, handler):
        raw_answers = {
            "1": [{"label": "給与や昇給の見込みが低い", "value": 1}],
            "2": [{"label": "人に感謝された時", "value": 1}],
            "3": [{"label": "年収を上げたい", "value": 1}],
            "4": [{"label": "80点以上", "value": 1}],
            "5": [{"label": "求人を探す", "value": 1}],
        }
        result = handler.get_validated_answers_for_summary(raw_answers)
        assert "5" not in result

    def test_missing_step_raises_value_error(self, handler):
        raw_answers = {
            "1": [{"label": "給与や昇給の見込みが低い", "value": 1}],
            "2": [{"label": "人に感謝された時", "value": 1}],
            "3": [{"label": "年収を上げたい", "value": 1}],
            # step4 が欠落
        }
        with pytest.raises(ValueError, match="ステップ 4"):
            handler.get_validated_answers_for_summary(raw_answers)

    @pytest.mark.parametrize("invalid_value", [None, "not-a-list", 123, {"value": 1}])
    def test_non_list_step_value_raises_value_error(self, handler, invalid_value):
        raw_answers = {
            "1": [{"label": "給与や昇給の見込みが低い", "value": 1}],
            "2": [{"label": "人に感謝された時", "value": 1}],
            "3": [{"label": "年収を上げたい", "value": 1}],
            "4": invalid_value,
        }
        with pytest.raises(ValueError, match="リスト形式ではありません"):
            handler.get_validated_answers_for_summary(raw_answers)


class TestGenerateLlmSummary:
    @pytest.mark.asyncio
    async def test_calls_summary_svc_with_text(self, handler, mock_summary_svc):
        structured_answers = {
            "1": [{"label": "給与や昇給の見込みが低い", "value": 1, "allowFreeText": False}],
            "2": [{"label": "人に感謝された時", "value": 1, "allowFreeText": False}],
            "3": [{"label": "年収を上げたい", "value": 1, "allowFreeText": False}],
            "4": [{"label": "80点以上", "value": 1, "allowFreeText": False}],
        }
        result = await handler.generate_llm_summary(structured_answers)

        mock_summary_svc.generate_summary.assert_called_once()
        called_text = mock_summary_svc.generate_summary.call_args[0][0]
        assert "給与や昇給の見込みが低い" in called_text
        assert result == {
            "summary": "転職軸まとめ",
            "explanation": "AIの視点まとめ",
            "keywords": ["フルリモート", "フレックス"],
        }

    @pytest.mark.asyncio
    async def test_multiple_selection_answers_preserve_priority_order(self, handler, mock_summary_svc):
        structured_answers = {
            "1": [
                {"label": "給与や昇給の見込みが低い", "value": 1, "allowFreeText": False},
                {"label": "その他", "value": 6, "allowFreeText": True, "text": "補足"},
            ],
            "2": [{"label": "人に感謝された時", "value": 1, "allowFreeText": False}],
            "3": [{"label": "年収を上げたい", "value": 1, "allowFreeText": False}],
            "4": [{"label": "80点以上", "value": 1, "allowFreeText": False}],
        }
        await handler.generate_llm_summary(structured_answers)

        called_text = mock_summary_svc.generate_summary.call_args[0][0]
        assert "1. 給与や昇給の見込みが低い" in called_text
        assert "2. その他\n補足" in called_text


class TestBuildHistoryToSave:
    def _structured_answers(self):
        return {
            "1": [{"label": "給与や昇給の見込みが低い", "value": 1, "allowFreeText": False}],
            "2": [{"label": "人に感謝された時", "value": 1, "allowFreeText": False}],
            "3": [{"label": "年収を上げたい", "value": 1, "allowFreeText": False}],
            "4": [{"label": "80点以上", "value": 1, "allowFreeText": False}],
            "5": [{"label": "求人を探す", "value": 1, "allowFreeText": False}],
        }

    def test_multiple_selection_steps_formatted_as_numbered_list(self, handler):
        answers = {
            "1": [
                {"label": "給与や昇給の見込みが低い", "value": 1, "allowFreeText": False},
                {"label": "その他", "value": 6, "allowFreeText": True, "text": "補足"},
            ],
        }
        history = handler.build_history_to_save(answers)
        user_answer = next(e["content"] for e in history if e["role"] == "user")
        assert user_answer == "1. 給与や昇給の見込みが低い\n\n2. その他\n補足"

    def test_single_selection_step_not_numbered(self, handler):
        answers = {"4": [{"label": "80点以上", "value": 1, "allowFreeText": False}]}
        history = handler.build_history_to_save(answers)
        user_answer = next(e["content"] for e in history if e["role"] == "user")
        assert user_answer == "80点以上"
        assert "1." not in user_answer

    def test_no_extra_returns_plain_step5_prompt(self, handler):
        history = handler.build_history_to_save(self._structured_answers())
        step5_entry = next(e for e in history if e["content"] == "P5")
        assert "【あなたの転職軸】" not in step5_entry["content"]

    def test_extra_with_summary_appended_to_step5_prompt(self, handler):
        history = handler.build_history_to_save(
            self._structured_answers(), extra={"summary": "テストサマリー"}
        )
        step5_entry = next(e for e in history if "P5" in e["content"])
        assert "【あなたの転職軸】" in step5_entry["content"]
        assert "テストサマリー" in step5_entry["content"]
        assert "【解説】" not in step5_entry["content"]
        assert "【求人を探すポイント】" not in step5_entry["content"]

    def test_extra_with_all_fields_appended_to_step5_prompt(self, handler):
        history = handler.build_history_to_save(
            self._structured_answers(),
            extra={
                "summary": "テストサマリー",
                "explanation": "テスト解説",
                "keyword_suggestion": "テストキーワード",
            },
        )
        step5_entry = next(e for e in history if "P5" in e["content"])
        assert "【あなたの転職軸】\nテストサマリー" in step5_entry["content"]
        assert "【解説】\nテスト解説" in step5_entry["content"]
        assert "【求人を探すポイント】\nテストキーワード" in step5_entry["content"]

    def test_extra_with_only_explanation_appended_to_step5_prompt(self, handler):
        history = handler.build_history_to_save(
            self._structured_answers(), extra={"explanation": "テスト解説"}
        )
        step5_entry = next(e for e in history if "P5" in e["content"])
        assert "【解説】\nテスト解説" in step5_entry["content"]
        assert "【あなたの転職軸】" not in step5_entry["content"]
        assert "【求人を探すポイント】" not in step5_entry["content"]

    def test_extra_without_summary_key_is_ignored(self, handler):
        history = handler.build_history_to_save(
            self._structured_answers(), extra={"other_key": "value"}
        )
        step5_entry = next(e for e in history if e["content"] == "P5")
        assert "【あなたの転職軸】" not in step5_entry["content"]

    def test_other_steps_not_modified(self, handler):
        history = handler.build_history_to_save(
            self._structured_answers(), extra={"summary": "サマリー"}
        )
        for entry in history:
            if entry["content"] in ("P1", "P2", "P3", "P4"):
                assert "【あなたの転職軸】" not in entry["content"]


class TestPerformPostProcessing:
    @pytest.mark.asyncio
    async def test_value1_career_advisor_no_workflow(self, handler):
        """value=1（求人を探す）でCareerAdvisorが返ること"""
        structured_answers = {"5": [{"label": "求人を探す", "value": 1, "allowFreeText": False}]}
        result = await handler.perform_post_processing(structured_answers)

        assert result.next_agent_name == AgentName.CAREER_ADVISOR
        assert result.next_workflow_id is None
        assert "求人" in result.message

    @pytest.mark.asyncio
    async def test_value2_career_advisor_with_job_match_workflow(self, handler):
        """value=2（向いている仕事）でCareerAdvisor + job_match_diagnosisが返ること"""
        structured_answers = {"5": [{"label": "向いている仕事を見つける", "value": 2, "allowFreeText": False}]}
        result = await handler.perform_post_processing(structured_answers)

        assert result.next_agent_name == AgentName.CAREER_ADVISOR
        assert result.next_workflow_id == JOB_MATCH_DIAGNOSIS_WORKFLOW_ID

    @pytest.mark.asyncio
    async def test_value3_career_advisor_form_registration(self, handler):
        """value=3（会員登録）でCareerAdvisorが返ること"""
        structured_answers = {"5": [{"label": "会員登録して転職活動を始める", "value": 3, "allowFreeText": False}]}
        result = await handler.perform_post_processing(structured_answers)

        assert result.next_agent_name == AgentName.CAREER_ADVISOR
        assert result.next_workflow_id is None
        assert "form_registration" in result.message

    @pytest.mark.asyncio
    async def test_value4_position_change_analyze_continues(self, handler):
        """value=4（その他）でPositionChangeAnalyzeが返ること"""
        structured_answers = {"5": [{"label": "その他", "value": 4, "allowFreeText": True, "text": "相談したい"}]}
        result = await handler.perform_post_processing(structured_answers)

        assert result.next_agent_name == AgentName.POSITION_CHANGE_ANALYZE
        assert result.next_workflow_id is None
        assert "相談したい" in result.message

    @pytest.mark.asyncio
    async def test_value4_without_free_text(self, handler):
        """value=4（その他）で自由入力なしでもPositionChangeAnalyzeが返ること"""
        structured_answers = {"5": [{"label": "その他", "value": 4, "allowFreeText": True}]}
        result = await handler.perform_post_processing(structured_answers)

        assert result.next_agent_name == AgentName.POSITION_CHANGE_ANALYZE

    @pytest.mark.asyncio
    async def test_unknown_value_raises_error(self, handler):
        """定義外のvalue でValueErrorが発生すること"""
        structured_answers = {"5": [{"label": "不明", "value": 99}]}
        with pytest.raises(ValueError, match="不明な選択値"):
            await handler.perform_post_processing(structured_answers)
