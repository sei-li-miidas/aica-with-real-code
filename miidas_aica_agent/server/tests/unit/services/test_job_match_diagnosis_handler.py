import pytest
from unittest.mock import AsyncMock
from services.workflow_handlers.job_match_diagnosis import JobMatchDiagnosisHandler

pytestmark = pytest.mark.pre_extraction_parity
from domain.entities.workflow_definition import WorkflowDefinition


@pytest.fixture
def mock_api_repo():
    return AsyncMock()


@pytest.fixture
def workflow_definition():
    # ステップ1と2で共通の選択肢リスト
    common_options = [
        {"label": "L1", "value": 1, "allowFreeText": False, "jobNature": "Nature1"},
        {"label": "L2", "value": 2, "allowFreeText": False, "jobNature": "Nature2"},
        {"label": "L3", "value": 3, "allowFreeText": False, "jobNature": "Nature3"},
        {"label": "L4", "value": 4, "allowFreeText": False, "jobNature": "Nature4"},
        {"label": "L5", "value": 5, "allowFreeText": False, "jobNature": "Nature5"},
        {"label": "L6", "value": 6, "allowFreeText": False, "jobNature": "Nature6"},
    ]

    data = {
        "id": "job_match_diagnosis",
        "name": "適職診断",
        "displayType": "modal",
        "steps": [
            {
                "id": 1,
                "question": "Q1",
                "questionPrompt": "P1",
                "selectionType": "multiple",
                "options": [{"id": "cat1", "name": "C1", "items": common_options}],
            },
            {
                "id": 2,
                "question": "Q2",
                "questionPrompt": "P2",
                "selectionType": "multiple",
                "options": [{"id": "cat1", "name": "C1", "items": common_options}],
            },
            {
                "id": 3,
                "question": "Q3",
                "questionPrompt": "P3",
                "selectionType": "multiple",
                "options": [],
            },
        ],
    }
    return WorkflowDefinition.model_validate(data)


def test_validation_step1_too_few(workflow_definition, mock_api_repo):
    """ステップ1の回答が少なすぎる場合のエラーテスト"""
    handler = JobMatchDiagnosisHandler(
        "job_match_diagnosis", mock_api_repo, workflow_definition
    )
    raw_answers = {"1": [{"label": "L1", "value": 1}, {"label": "L2", "value": 2}]}

    with pytest.raises(ValueError, match="3〜5つ選択してください"):
        handler.get_validated_structured_answers(raw_answers)


def test_validation_step3_missing(workflow_definition, mock_api_repo):
    """最終提出時にステップ3の回答がない場合のエラーテスト"""
    handler = JobMatchDiagnosisHandler(
        "job_match_diagnosis", mock_api_repo, workflow_definition
    )
    raw_answers = {
        "1": [
            {"label": "L1", "value": 1},
            {"label": "L2", "value": 2},
            {"label": "L3", "value": 3},
        ],
        "2": [{"label": "L4", "value": 4}],
        # "3" が欠落
    }

    with pytest.raises(ValueError, match="ステップ3は1つ以上選択してください"):
        handler.get_validated_structured_answers(raw_answers)


def test_get_validated_answers_for_search_success(workflow_definition, mock_api_repo):
    """職種検索用のバリデーション（ステップ1, 2のみ）のテスト"""
    handler = JobMatchDiagnosisHandler(
        "job_match_diagnosis", mock_api_repo, workflow_definition
    )
    raw_answers = {
        "1": [
            {"label": "L1", "value": 1},
            {"label": "L2", "value": 2},
            {"label": "L3", "value": 3},
        ],
        "2": [{"label": "L4", "value": 4}],
    }

    # 検索用バリデーションはステップ3がなくてもパスする
    structured = handler.get_validated_answers_for_search(raw_answers)
    assert len(structured["1"]) == 3
    assert len(structured["2"]) == 1


def test_get_job_nature_prefs(workflow_definition, mock_api_repo):
    """jobNatureが正しく抽出されるかのテスト"""
    handler = JobMatchDiagnosisHandler(
        "job_match_diagnosis", mock_api_repo, workflow_definition
    )
    structured_answers = {
        "1": [{"label": "L1", "value": 1, "jobNature": "Nature1"}],
        "2": [{"label": "L2", "value": 2, "jobNature": "Nature2"}],
    }
    prefs = handler.get_job_nature_prefs(structured_answers)
    assert len(prefs) == 2
    assert prefs[0] == {"JobNature": "Nature1", "Preference": "やりたい"}
    assert prefs[1] == {"JobNature": "Nature2", "Preference": "避けたい"}


@pytest.mark.asyncio
async def test_search_occupations(workflow_definition, mock_api_repo):
    """職種検索APIの呼び出しテスト"""
    handler = JobMatchDiagnosisHandler(
        "job_match_diagnosis", mock_api_repo, workflow_definition
    )
    # aica_api_repo.post をモックし、(status_code, body) のペアを返すようにする
    mock_api_repo.post.return_value = (
        200,
        [{"Name": "エンジニア", "ID": 1, "Description": "..."}],
    )

    results = await handler.search_job_match_diagnosis_occupations(
        [{"JobNature": "Nature1", "Preference": "やりたい"}]
    )
    assert len(results) == 1
    assert results[0]["職種名"] == "エンジニア"
    mock_api_repo.post.assert_called_once()


@pytest.mark.asyncio
async def test_perform_post_processing_returns_selected_jobtypes(
    workflow_definition, mock_api_repo
):
    """perform_post_processing がステップ3の職種ラベルを selected_jobtypes に返すテスト"""
    handler = JobMatchDiagnosisHandler(
        "job_match_diagnosis", mock_api_repo, workflow_definition
    )
    structured_answers = {
        "1": [
            {"label": "L1", "value": 1, "jobNature": "Nature1"},
            {"label": "L2", "value": 2, "jobNature": "Nature2"},
            {"label": "L3", "value": 3, "jobNature": "Nature3"},
        ],
        "2": [],
        "3": [
            {"label": "システムエンジニア", "value": 10},
            {"label": "Webエンジニア", "value": 11},
        ],
    }

    result = await handler.perform_post_processing(structured_answers)

    assert result.selected_jobtypes == ["システムエンジニア", "Webエンジニア"]
    assert result.message  # メッセージが空でないこと


@pytest.mark.asyncio
async def test_perform_post_processing_no_step3_returns_none(
    workflow_definition, mock_api_repo
):
    """ステップ3の回答がない場合、selected_jobtypes が None になるテスト"""
    handler = JobMatchDiagnosisHandler(
        "job_match_diagnosis", mock_api_repo, workflow_definition
    )
    structured_answers = {
        "1": [
            {"label": "L1", "value": 1, "jobNature": "Nature1"},
            {"label": "L2", "value": 2, "jobNature": "Nature2"},
            {"label": "L3", "value": 3, "jobNature": "Nature3"},
        ],
        "2": [],
        "3": [],
    }

    result = await handler.perform_post_processing(structured_answers)

    assert result.selected_jobtypes is None
