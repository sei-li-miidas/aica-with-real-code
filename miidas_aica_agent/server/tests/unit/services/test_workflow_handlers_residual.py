from unittest.mock import AsyncMock, Mock

import pytest

from domain.entities.workflow_definition import WorkflowDefinition
from services.workflow_handlers.base import (
    WorkflowHandler,
    WorkflowPostProcessingResult,
)
from services.workflow_handlers.generic import GenericWorkflowHandler
from services.workflow_handlers.job_match_diagnosis import JobMatchDiagnosisHandler

pytestmark = pytest.mark.pre_extraction_parity


class _SuperCallHandler(WorkflowHandler):
    async def perform_post_processing(self, structured_answers):
        return await super().perform_post_processing(structured_answers)


@pytest.fixture
def wf_def():
    return WorkflowDefinition.model_validate(
        {
            "id": "job_match_diagnosis",
            "name": "wf",
            "displayType": "modal",
            "steps": [
                {
                    "id": 1,
                    "question": "Q1",
                    "questionPrompt": "P1",
                    "selectionType": "multiple",
                    "options": [
                        {
                            "id": "cat",
                            "name": "cat",
                            "items": [
                                {
                                    "label": "A",
                                    "value": 1,
                                    "allowFreeText": False,
                                    "jobNature": "N1",
                                },
                                {
                                    "label": "B",
                                    "value": 2,
                                    "allowFreeText": False,
                                    "jobNature": "N2",
                                },
                                {
                                    "label": "C",
                                    "value": 3,
                                    "allowFreeText": False,
                                    "jobNature": "N3",
                                },
                                {
                                    "label": "D",
                                    "value": 4,
                                    "allowFreeText": False,
                                    "jobNature": "N4",
                                },
                                {
                                    "label": "E",
                                    "value": 5,
                                    "allowFreeText": False,
                                    "jobNature": "N5",
                                },
                                {
                                    "label": "F",
                                    "value": 6,
                                    "allowFreeText": False,
                                    "jobNature": "N6",
                                },
                            ],
                        }
                    ],
                },
                {
                    "id": 2,
                    "question": "Q2",
                    "questionPrompt": "P2",
                    "selectionType": "multiple",
                    "options": [
                        {
                            "id": "cat",
                            "name": "cat",
                            "items": [
                                {
                                    "label": "A",
                                    "value": 1,
                                    "allowFreeText": False,
                                    "jobNature": "N1",
                                },
                                {
                                    "label": "B",
                                    "value": 2,
                                    "allowFreeText": False,
                                    "jobNature": "N2",
                                },
                                {
                                    "label": "C",
                                    "value": 3,
                                    "allowFreeText": False,
                                    "jobNature": "N3",
                                },
                                {
                                    "label": "D",
                                    "value": 4,
                                    "allowFreeText": False,
                                    "jobNature": "N4",
                                },
                                {
                                    "label": "E",
                                    "value": 5,
                                    "allowFreeText": False,
                                    "jobNature": "N5",
                                },
                                {
                                    "label": "F",
                                    "value": 6,
                                    "allowFreeText": False,
                                    "jobNature": "N6",
                                },
                            ],
                        }
                    ],
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
    )


def test_extract_options_by_step_raises_for_non_dict_item(wf_def):
    handler = JobMatchDiagnosisHandler("job_match_diagnosis", AsyncMock(), wf_def)
    with pytest.raises(ValueError):
        handler.extract_options_by_step("1", ["invalid-item"])


def test_get_conversation_pair_from_options_returns_none_when_empty(wf_def):
    handler = JobMatchDiagnosisHandler("job_match_diagnosis", AsyncMock(), wf_def)
    question, answer = handler.get_conversation_pair_from_options("1", [])
    assert question == "P1"
    assert answer is None


@pytest.mark.asyncio
async def test_abstract_super_pass_line_is_executed(wf_def):
    handler = _SuperCallHandler("job_match_diagnosis", wf_def)
    assert await handler.perform_post_processing({}) is None


def test_validate_job_nature_step2_too_many_raises(wf_def):
    handler = JobMatchDiagnosisHandler("job_match_diagnosis", AsyncMock(), wf_def)
    with pytest.raises(ValueError):
        handler.validate_job_nature_steps(
            {
                "1": [{"value": 1}, {"value": 2}, {"value": 3}],
                "2": [
                    {"value": 1},
                    {"value": 2},
                    {"value": 3},
                    {"value": 4},
                    {"value": 5},
                    {"value": 6},
                ],
            }
        )


def test_validate_job_nature_removes_duplicate_step2_values(wf_def, caplog):
    handler = JobMatchDiagnosisHandler("job_match_diagnosis", AsyncMock(), wf_def)
    structured = {
        "1": [{"value": 1}, {"value": 2}, {"value": 3}],
        "2": [{"value": 2}, {"value": 4}],
    }

    handler.validate_job_nature_steps(structured)

    assert structured["2"] == [{"value": 4}]
    assert "重複を除外します" in caplog.text


def test_validate_job_type_step_invalid_item_type_raises(wf_def):
    handler = JobMatchDiagnosisHandler("job_match_diagnosis", AsyncMock(), wf_def)
    with pytest.raises(ValueError):
        handler.validate_job_type_step({"3": ["not-dict"]})


def test_validate_job_type_step_returns_normalized_label_value(wf_def):
    handler = JobMatchDiagnosisHandler("job_match_diagnosis", AsyncMock(), wf_def)
    result = handler.validate_job_type_step({"3": [{"label": "X", "value": 9}]})
    assert result == [{"label": "X", "value": 9}]


def test_get_validated_structured_answers_includes_step3(wf_def):
    handler = JobMatchDiagnosisHandler("job_match_diagnosis", AsyncMock(), wf_def)
    raw = {
        "1": [{"value": 1}, {"value": 2}, {"value": 3}],
        "2": [{"value": 4}],
        "3": [{"label": "職種", "value": "j1"}],
    }

    structured = handler.get_validated_structured_answers(raw)

    assert "3" in structured
    assert structured["3"] == [{"label": "職種", "value": "j1"}]


@pytest.mark.asyncio
async def test_search_job_match_diagnosis_occupations_non_200_raises(wf_def):
    api_repo = AsyncMock()
    api_repo.post.return_value = (500, {"error": "x"})
    handler = JobMatchDiagnosisHandler("job_match_diagnosis", api_repo, wf_def)

    with pytest.raises(RuntimeError):
        await handler.search_job_match_diagnosis_occupations([])


@pytest.fixture
def generic_wf_def():
    return WorkflowDefinition.model_validate(
        {
            "id": "onboarding",
            "name": "オンボーディング",
            "displayType": "modal",
            "steps": [
                {
                    "id": 1,
                    "question": "希望職種は？",
                    "questionPrompt": "希望する職種を教えてください。",
                    "selectionType": "single",
                    "options": [
                        {"label": "エンジニア", "value": 1, "allowFreeText": False},
                    ],
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_generic_workflow_handler_init_and_post_processing(generic_wf_def):
    """GenericWorkflowHandler.__init__ and perform_post_processing are exercised."""
    handler = GenericWorkflowHandler("onboarding", generic_wf_def)
    assert handler.workflow_id == "onboarding"

    structured_answers = {
        "1": [{"label": "エンジニア", "value": 1}],
    }
    result = await handler.perform_post_processing(structured_answers)

    assert isinstance(result, WorkflowPostProcessingResult)
    assert "オンボーディング" in result.message
    assert "エンジニア" in result.message
