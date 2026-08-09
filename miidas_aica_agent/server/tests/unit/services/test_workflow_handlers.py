import pytest

from services.workflow_handlers.base import WorkflowHandler
from domain.entities.workflow_definition import (
    SelectionType,
    DisplayType,
    WorkflowDefinition,
)

pytestmark = pytest.mark.pre_extraction_parity


class DummyWorkflowHandler(WorkflowHandler):
    """テスト用の具象ハンドラクラス"""

    async def perform_post_processing(self, structured_answers: dict) -> str:
        return "dummy message"


@pytest.fixture
def workflow_definition():
    """テスト用のワークフロー定義オブジェクトを作成する"""
    data = {
        "id": "test_wf",
        "name": "Test Workflow",
        "displayType": DisplayType.MODAL,
        "steps": [
            {
                "id": 1,
                "question": "Q1",
                "questionPrompt": "P1",
                "selectionType": SelectionType.SINGLE,
                "options": [
                    {"label": "Opt1", "value": 1, "allowFreeText": False},
                    {"label": "Opt2", "value": 2, "allowFreeText": True},
                ],
            },
            {
                "id": 2,
                "question": "Q2",
                "questionPrompt": "P2",
                "selectionType": SelectionType.MULTIPLE,
                "options": [
                    {
                        "id": "cat1",
                        "name": "Cat1",
                        "items": [
                            {"label": "Sub1", "value": 10, "allowFreeText": False}
                        ],
                    }
                ],
            },
        ],
    }
    return WorkflowDefinition.model_validate(data)


def test_handler_init_and_load(workflow_definition):
    """ハンドラの初期化テスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)
    assert handler.workflow_id == "test_wf"
    assert handler._definition.name == "Test Workflow"


def test_handler_get_step(workflow_definition):
    """ステップ取得のテスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)

    # 存在するステップ
    step = handler._get_step(1)
    assert step.id == 1
    assert step.question == "Q1"

    # 存在しないステップ
    with pytest.raises(ValueError, match="存在しません"):
        handler._get_step(999)


def test_handler_get_question_methods(workflow_definition):
    """質問およびプロンプト取得メソッドのテスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)
    assert handler.get_question(1) == "Q1"
    assert handler.get_question_prompt(2) == "P2"


def test_get_structured_answers(workflow_definition):
    """回答構造化のテスト（正常系）"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)

    raw_answers = {
        "1": [{"label": "Opt1", "value": 1}],  # 正解
        "2": [
            {"label": "Sub1", "value": 10},
            {"label": "Invalid", "value": 999},
        ],  # 一部正解（定義外の値は無視される）
    }

    structured = handler.get_validated_structured_answers(raw_answers)

    # ステップ1の確認
    assert "1" in structured
    assert len(structured["1"]) == 1
    assert structured["1"][0]["value"] == 1

    # ステップ2の確認（有効なものだけ抽出されているか）
    assert "2" in structured
    assert len(structured["2"]) == 1
    assert structured["2"][0]["value"] == 10


def test_get_structured_answers_invalid_step(workflow_definition):
    """定義にないステップIDが含まれる場合の異常系テスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)

    raw_answers = {"999": [{"label": "NoStep", "value": 1}]}

    with pytest.raises(
        ValueError, match="ステップID `999` がワークフロー `test_wf` に存在しません"
    ):
        handler.get_validated_structured_answers(raw_answers)


def test_get_structured_answers_invalid_format(workflow_definition):
    """回答がリスト形式ではない場合の異常系テスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)

    raw_answers = {"1": "not a list"}

    with pytest.raises(ValueError, match="ステップ1の回答がリスト形式ではありません"):
        handler.get_validated_structured_answers(raw_answers)


def test_get_structured_answers_with_free_text(workflow_definition):
    """回答構造化（自由入力textあり）のテスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)

    raw_answers = {"1": [{"label": "Opt2", "value": 2, "text": "自由入力内容"}]}

    structured = handler.get_validated_structured_answers(raw_answers)

    assert structured["1"][0]["value"] == 2
    assert structured["1"][0]["text"] == "自由入力内容"


def test_get_conversation_pair_from_options(workflow_definition):
    """チャット履歴用ペア生成のテスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)

    valid_options = [
        {"label": "Opt1", "value": 1},
        {"label": "Opt2", "value": 2, "text": "補足"},
    ]

    q, a = handler.get_conversation_pair_from_options(1, valid_options)
    assert q == "P1"
    assert (
        a
        == """Opt1

Opt2
補足"""
    )


def test_summarize_answers(workflow_definition):
    """回答要約テキスト生成のテスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)

    structured_answers = {
        "1": [
            {"label": "Opt1", "value": 1},
            {"label": "Opt2", "value": 2, "text": "補足"},
        ],
        "2": [{"label": "Sub1", "value": 10}],
    }

    summary = handler.summarize_answers(structured_answers)

    # 各ステップの質問と回答が含まれているか確認
    assert "- Q1: Opt1、Opt2（補足）" in summary
    assert "- Q2: Sub1" in summary
    assert "\n" in summary


def test_get_structured_answers_single_selection_violation(workflow_definition):
    """単一選択ステップで複数回答があった場合の異常系テスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)

    raw_answers = {"1": [{"label": "Opt1", "value": 1}, {"label": "Opt2", "value": 2}]}

    with pytest.raises(ValueError, match="単一選択ですが、複数の回答が送信されました"):
        handler.get_validated_structured_answers(raw_answers)


def test_get_structured_answers_with_disallowed_free_text(workflow_definition):
    """自由入力が許可されていないオプションでtextが含まれる場合のテスト"""
    handler = DummyWorkflowHandler("test_wf", workflow_definition)

    raw_answers = {"1": [{"label": "Opt1", "value": 1, "text": "勝手な入力"}]}

    structured = handler.get_validated_structured_answers(raw_answers)

    # Opt1はallowFreeText: Falseなのでtextは除外されるはず
    assert structured["1"][0]["value"] == 1
    assert "text" not in structured["1"][0]
