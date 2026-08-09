import pytest
from pydantic import ValidationError
from domain.entities.workflow_definition import WorkflowDefinition, SelectionType, DisplayType


def test_workflow_definition_valid():
    """正常なワークフロー定義のパーステスト"""
    data = {
        "id": "test_workflow",
        "name": "テストワークフロー",
        "displayType": "modal",
        "steps": [
            {
                "id": 1,
                "question": "質問1",
                "questionPrompt": "プロンプト1",
                "selectionType": "single",
                "options": [
                    {"label": "選択肢1", "value": 1, "allowFreeText": False}
                ]
            }
        ]
    }
    definition = WorkflowDefinition.model_validate(data)
    assert definition.id == "test_workflow"
    assert definition.display_type == DisplayType.MODAL
    assert definition.steps[0].id == 1
    assert definition.steps[0].selection_type == SelectionType.SINGLE
    assert definition.steps[0].options[0].label == "選択肢1"


def test_workflow_definition_with_categories():
    """階層構造（カテゴリ）を持つワークフロー定義のパーステスト"""
    data = {
        "id": "category_workflow",
        "name": "カテゴリワークフロー",
        "displayType": "inline",
        "steps": [
            {
                "id": 1,
                "question": "質問",
                "questionPrompt": "プロンプト",
                "selectionType": "multiple",
                "options": [
                    {
                        "id": "cat1",
                        "name": "カテゴリ1",
                        "items": [
                            {"label": "子選択肢1", "value": 1, "allowFreeText": True}
                        ]
                    }
                ]
            }
        ]
    }
    definition = WorkflowDefinition.model_validate(data)
    assert len(definition.steps[0].options) == 1
    assert definition.steps[0].options[0].name == "カテゴリ1"
    assert definition.steps[0].options[0].items[0].label == "子選択肢1"
    assert definition.steps[0].options[0].items[0].allow_free_text is True


def test_workflow_definition_invalid_enum():
    """不正なLiteral値（displayType）によるバリデーションエラーテスト"""
    data = {
        "id": "invalid",
        "name": "名前",
        "displayType": "invalid_type",  # modalかinlineである必要がある
        "steps": []
    }
    with pytest.raises(ValidationError):
        WorkflowDefinition.model_validate(data)


def test_workflow_definition_missing_required():
    """必須項目欠落によるバリデーションエラーテスト"""
    data = {
        "id": "invalid",
        # name が欠落
        "displayType": "modal",
        "steps": []
    }
    with pytest.raises(ValidationError):
        WorkflowDefinition.model_validate(data)


def test_workflow_definition_empty_steps():
    """ステップが空の場合のバリデーションエラーテスト (min_length=1)"""
    data = {
        "id": "empty_steps",
        "name": "空ステップ",
        "displayType": "modal",
        "steps": []
    }
    with pytest.raises(ValidationError, match="List should have at least 1 item"):
        WorkflowDefinition.model_validate(data)
