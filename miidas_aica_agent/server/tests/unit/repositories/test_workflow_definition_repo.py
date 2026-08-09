import pytest
import json
from repositories.workflow_definition_repo import WorkflowDefinitionRepository
from domain.entities.workflow_definition import DisplayType, SelectionType


@pytest.fixture
def workflow_dir(tmp_path):
    """テスト用のワークフロー定義ディレクトリを作成する"""
    d = tmp_path / "workflows"
    d.mkdir()

    # 有効なワークフロー定義
    valid_wf = {
        "id": "valid_wf",
        "name": "Valid Workflow",
        "displayType": "modal",
        "steps": [
            {
                "id": 1,
                "question": "Q1",
                "questionPrompt": "P1",
                "selectionType": "single",
                "options": [{"label": "O1", "value": 1, "allowFreeText": False}]
            }
        ]
    }
    (d / "valid_wf.json").write_text(json.dumps(valid_wf), encoding="utf-8")

    # 空のステップを持つ無効なワークフロー
    invalid_wf = {
        "id": "invalid_wf",
        "name": "Invalid Workflow",
        "displayType": "inline",
        "steps": []
    }
    (d / "invalid_wf.json").write_text(json.dumps(invalid_wf), encoding="utf-8")

    return d


def test_workflow_definition_repo_init_validation(workflow_dir):
    """初期化時のバリデーションテスト"""
    # 正常な初期化（invalid_wfが含まれるので例外が発生するはず）
    with pytest.raises(ValueError, match="バリデーションに失敗しました"):
        WorkflowDefinitionRepository(str(workflow_dir))

    # 無効なファイルを削除して初期化
    (workflow_dir / "invalid_wf.json").unlink()
    repo = WorkflowDefinitionRepository(str(workflow_dir))
    assert "valid_wf" in repo._definitions


def test_workflow_definition_repo_get_definition(workflow_dir):
    """get_definitionのテスト"""
    (workflow_dir / "invalid_wf.json").unlink()
    repo = WorkflowDefinitionRepository(str(workflow_dir))

    # キャッシュから取得
    definition = repo.get_definition("valid_wf")
    assert definition.id == "valid_wf"
    assert definition.display_type == DisplayType.MODAL

    # 不正なID形式（パストラバーサル）
    with pytest.raises(ValueError, match="不正なワークフローIDです"):
        repo.get_definition("../etc/passwd")

    # 存在しないファイル
    with pytest.raises(FileNotFoundError):
        repo.get_definition("non_existent")


def test_workflow_definition_repo_traversal_prevention(workflow_dir):
    """ディレクトリトラバーサル防止のテスト"""
    (workflow_dir / "invalid_wf.json").unlink()
    repo = WorkflowDefinitionRepository(str(workflow_dir))

    # resolve()後にディレクトリ外を指すような指定
    with pytest.raises(ValueError, match="不正なワークフローIDです"):
        repo.get_definition("..")
