from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from services.workflow_service import WorkflowService

pytestmark = pytest.mark.pre_extraction_parity


@pytest.fixture
def service():
    return WorkflowService(
        aica_api_repository=Mock(),
        workflow_repository=Mock(),
        workflow_definition_repository=Mock(),
        position_change_analyze_summary_svc=Mock(),
    )


def test_exists_definition_returns_false_on_value_error(service):
    service._workflow_definition_repository.get_definition.side_effect = ValueError("x")
    assert service.exists_definition("wf") is False


def test_exists_definition_returns_false_on_file_not_found(service):
    service._workflow_definition_repository.get_definition.side_effect = (
        FileNotFoundError("x")
    )
    assert service.exists_definition("wf") is False


def test_exists_definition_returns_true_when_definition_exists(service):
    service._workflow_definition_repository.get_definition.return_value = object()
    assert service.exists_definition("wf") is True


def test_get_handler_returns_job_match_handler_for_specific_workflow(service):
    fake_definition = object()
    service.get_definition = Mock(return_value=fake_definition)

    with pytest.MonkeyPatch.context() as mp:
        ctor = Mock(return_value="job-handler")
        mp.setattr("services.workflow_service.JobMatchDiagnosisHandler", ctor)
        handler = service._get_handler("job_match_diagnosis")

    assert handler == "job-handler"
    ctor.assert_called_once_with(
        "job_match_diagnosis", service._aica_api_repository, fake_definition
    )


def test_get_handler_returns_generic_handler_for_other_workflow(service):
    fake_definition = object()
    service.get_definition = Mock(return_value=fake_definition)

    with pytest.MonkeyPatch.context() as mp:
        ctor = Mock(return_value="generic-handler")
        mp.setattr("services.workflow_service.GenericWorkflowHandler", ctor)
        handler = service._get_handler("another_workflow")

    assert handler == "generic-handler"
    ctor.assert_called_once_with("another_workflow", fake_definition)


def test_get_handler_returns_position_change_analyze_handler_for_specific_workflow(service):
    fake_definition = object()
    service.get_definition = Mock(return_value=fake_definition)

    with pytest.MonkeyPatch.context() as mp:
        ctor = Mock(return_value="position-change-analyze-handler")
        mp.setattr("services.workflow_service.PositionChangeAnalyzeHandler", ctor)
        handler = service._get_handler("position_change_analyze")

    assert handler == "position-change-analyze-handler"
    ctor.assert_called_once_with(
        "position_change_analyze",
        service._position_change_analyze_summary_svc,
        fake_definition,
    )


@pytest.mark.asyncio
async def test_process_workflow_submission_keeps_text_field_and_none_answer(service):
    handler = Mock()
    handler.get_validated_structured_answers.return_value = {
        "1": [{"label": "A", "value": 1, "text": "memo"}],
        "2": [{"label": "B", "value": 2}],
    }
    expected_history = [
        {"role": "assistant", "content": "Q1"},
        {"role": "user", "content": "ANS1"},
        {"role": "assistant", "content": "Q2"},
        {"role": "user", "content": "選択なし"},
    ]
    handler.build_history_to_save.return_value = expected_history
    handler.perform_post_processing = AsyncMock(
        return_value=SimpleNamespace(message="ok", selected_jobtypes=None)
    )
    service._get_handler = Mock(return_value=handler)

    post, history = await service.process_workflow_submission("wf", {"k": "v"})

    assert post.message == "ok"
    service._workflow_repository.save_workflow_answer.assert_called_once_with(
        "wf",
        {
            "1": [{"label": "A", "value": 1, "text": "memo"}],
            "2": [{"label": "B", "value": 2}],
        },
    )
    handler.build_history_to_save.assert_called_once_with(
        handler.get_validated_structured_answers.return_value, extra=None
    )
    assert history == expected_history


@pytest.mark.asyncio
async def test_search_job_match_diagnosis_occupations_calls_handler_chain(service):
    handler = Mock()
    handler.get_validated_answers_for_search.return_value = {"1": [{"value": 1}]}
    handler.get_job_nature_prefs.return_value = [
        {"JobNature": "N", "Preference": "やりたい"}
    ]
    handler.search_job_match_diagnosis_occupations = AsyncMock(return_value=[{"ID": 1}])
    service._get_handler = Mock(return_value=handler)

    result = await service.search_job_match_diagnosis_occupations({"1": []})

    assert result == [{"ID": 1}]
    handler.get_validated_answers_for_search.assert_called_once()
    handler.get_job_nature_prefs.assert_called_once_with({"1": [{"value": 1}]})
    handler.search_job_match_diagnosis_occupations.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_position_change_analyze_summary_calls_handler_chain(service):
    handler = Mock()
    handler.get_validated_answers_for_summary.return_value = {
        "1": [{"value": 1, "label": "A"}]
    }
    expected_summary = {
        "summary": "転職軸まとめ",
        "explanation": "AIの視点まとめ",
        "keywords": ["フルリモート"],
    }
    handler.generate_llm_summary = AsyncMock(return_value=expected_summary)
    service._get_handler = Mock(return_value=handler)

    result = await service.generate_position_change_analyze_summary(
        {"1": [{"value": 1}]}
    )

    assert result == expected_summary
    service._get_handler.assert_called_once_with("position_change_analyze")
    handler.get_validated_answers_for_summary.assert_called_once_with(
        {"1": [{"value": 1}]}
    )
    handler.generate_llm_summary.assert_awaited_once_with(
        handler.get_validated_answers_for_summary.return_value
    )


@pytest.mark.asyncio
async def test_generate_position_change_analyze_summary_propagates_validation_error(
    service,
):
    handler = Mock()
    handler.get_validated_answers_for_summary = Mock(
        side_effect=ValueError("転職理由診断要約に必要なステップ 4 の回答がありません")
    )
    service._get_handler = Mock(return_value=handler)

    with pytest.raises(ValueError, match="ステップ 4"):
        await service.generate_position_change_analyze_summary({"1": [{"value": 1}]})
