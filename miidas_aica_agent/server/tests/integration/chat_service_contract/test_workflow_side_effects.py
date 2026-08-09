"""
Workflow side effects 完全な振る舞いアサーション (Phase 3, feature-3, task-4)。

テスト対象公開インターフェース:
- ChatService.init_session(model_name: str) -> tuple[ChatSessionStatus, bool]
- ChatService.job_type_decided(input, client_ip) -> AsyncGenerator[ChatStreamResponseModel, None]
- ChatService.clear_jobtype(input, client_ip) -> AsyncGenerator[ChatStreamResponseModel, None]
- ChatService.workflow_submitted(input, client_ip) -> AsyncGenerator[ChatStreamResponseModel, None]
- ChatService.workflow_cancelled(input, client_ip) -> AsyncGenerator[ChatStreamResponseModel, None]

各ワークフロー系 public method が内部で chat() を起動し、legacy/delegating 両 variant で
同じ stream contract と副作用を維持することを検証する。

テストケース一覧:
- test_job_type_selected_updates_state_and_returns_stream_contract
    対象: job_type 決定時に状態更新と stream contract 返却が成立すること。
- test_job_type_clear_resets_state_and_returns_stream_contract
    対象: clear_jobtype で状態初期化と stream contract 維持を確認すること。
- test_workflow_submitted_persists_answers_and_returns_stream_contract
    対象: workflow 提出時に回答保存し、
    契約どおり stream 応答すること。
- test_workflow_cancelled_validates_definition_and_returns_stream_contract
    対象: workflow cancel 時に definition 検証と
    stream 応答契約を満たすこと。
- test_job_type_decided_returns_validation_errors_for_invalid_payloads
    対象: 不正 payload で validation error を返し、
    正常系に進まないこと。
- test_job_type_decided_returns_error_when_tool_update_fails
    対象: tool update 失敗時に
    エラー応答へフォールバックすること。
- test_workflow_submitted_returns_validation_errors_for_invalid_payloads
    対象: workflow submit の不正 payload を
    validation error として扱うこと。
- test_workflow_submitted_returns_service_errors_and_allows_no_save_path
    対象: service error 返却と no-save 分岐の両方を
    許容すること。
- test_workflow_cancelled_uses_fallback_message_for_malformed_or_unknown_workflow
    対象: malformed/unknown workflow cancel で
    fallback message を返すこと。
"""

import json
from pathlib import Path
from types import SimpleNamespace
import uuid
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import pytest

from .chat_service_contract_helpers import (
    _FakeRunResult,
    _FakeRunStream,
    _inner,
    _state,
    _setup_existing_session,
)
from domain.entities.workflow_definition import (
    DisplayType,
    SelectionType,
    WorkflowDefinition,
    WorkflowOptionItem,
    WorkflowStep,
)
from services.workflow_handlers.base import WorkflowPostProcessingResult
from openai.types.responses import ResponseTextDeltaEvent
from services.chat.llm_runner import LLMRawResponseEvent
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import (
    ChatResponseType,
    ChatStreamResponse,
    ChatStreamResponseModel,
)
from utils.enum import LLMMessageRole, PageName
from utils.log_utils import clear_session_id, set_session_id


FIXTURES_DIR = Path(__file__).with_name("fixtures")
_VARIANTS = [
    "legacy",
    "real-refactored",
]


def _load_json_fixture(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _make_agent_mock() -> MagicMock:
    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    agent_mock.tool_use_behavior = {}
    return agent_mock


def _make_text_delta(item_id: str, delta: str):
    return SimpleNamespace(
        type="raw_response_event",
        data=ResponseTextDeltaEvent(
            type="response.output_text.delta",
            item_id=item_id,
            output_index=0,
            content_index=0,
            delta=delta,
            sequence_number=0,
            logprobs=[],
        ),
    )


def _make_workflow_definition(
    workflow_id: str,
    workflow_name: str,
) -> WorkflowDefinition:
    return WorkflowDefinition(
        id=workflow_id,
        name=workflow_name,
        displayType=DisplayType.MODAL,
        steps=[
            WorkflowStep(
                id=1,
                question="どの職種に興味がありますか？",
                questionPrompt="どの職種に興味がありますか？",
                selectionType=SelectionType.SINGLE,
                options=[
                    WorkflowOptionItem(
                        label="エンジニア",
                        value=1,
                        allowFreeText=False,
                    )
                ],
            )
        ],
    )


def _make_run_streamed_mock(svc, run_result):
    return create_autospec(svc._run_streamed, spec_set=True, return_value=run_result)


def _make_normalized_text_delta(item_id: str, delta: str) -> LLMRawResponseEvent:
    """real-refactored バリアント向けの正規化済みストリームイベントを生成する。

    StreamEventProcessor は LLMRawResponseEvent を期待するため、
    _FakeRunStream に渡すイベントは正規化済みである必要がある。
    """
    return LLMRawResponseEvent(item_id=item_id, delta=delta)


def _setup_runner_mock(
    variant: str, chat_svc, svc, events_sdk: list, events_normalized: list
) -> None:
    """バリアントに応じてランナーモックを設定する。

    legacy: svc._run_streamed に _FakeRunResult（SDK 形式）を設定。
    real-refactored: chat_svc._llm_runner.run_streamed に _FakeRunStream（正規化済み）を設定。

    """
    if variant == "legacy":
        mock_run = MagicMock(return_value=_FakeRunResult(events_sdk))
        svc._run_streamed = mock_run
    else:
        mock_stream = MagicMock(return_value=_FakeRunStream(events_normalized))
        chat_svc._llm_runner.run_streamed = mock_stream


def _flatten_saved_histories(chat_svc):
    svc = _inner(chat_svc)
    flattened = []
    for call in svc._chat_repository.add_chat_histories.call_args_list:
        if "chat_histories" in call.kwargs:
            histories = call.kwargs["chat_histories"]
        elif call.args:
            histories = call.args[0]
        else:
            raise AssertionError(
                "add_chat_histories() call did not include chat_histories in args or kwargs"
            )

        flattened.extend(histories)

    return flattened


async def _collect_responses(generator) -> list[ChatStreamResponseModel]:
    responses = []
    async for response in generator:
        responses.append(response.model_copy(deep=True))
    return responses


def _assert_stream_contract(
    responses: list[ChatStreamResponseModel],
    request_type: ChatRequestType,
    stream_contract: dict,
) -> None:
    assert responses, "Expected the workflow entrypoint to emit at least one response"

    actual_response_types = [response.response_type.value for response in responses]
    assert responses[-1].response_type == ChatResponseType.END
    assert all(
        response.response_type == ChatResponseType.MESSAGE
        for response in responses[:-1]
    ), f"Unexpected non-MESSAGE response before END: {actual_response_types}"
    assert [
        responses[0].response_type.value,
        responses[-1].response_type.value,
    ] == stream_contract["response_types"]

    message_responses = responses[:-1]
    assert message_responses, (
        "Expected at least one streamed assistant MESSAGE response; "
        f"got {[response.response_type for response in responses]}"
    )
    reconstructed_message = "".join(
        response.message or "" for response in message_responses
    )
    assert reconstructed_message == stream_contract["assistant_message"]

    expected_response_keys = sorted(stream_contract["_expected_response_keys"])
    for response in responses:
        # Explicitly set exclude_none and by_alias for stable contract
        actual_keys = sorted(
            response.model_dump(exclude_none=False, by_alias=False).keys()
        )
        assert actual_keys == expected_response_keys
        assert response.request_type == request_type


@pytest.fixture
def workflow_session_id(request):
    # `set_session_id()` / `clear_session_id()` are backed by ContextVar in
    # `utils.log_utils`, so this fixture is isolated across concurrent pytest
    # workers/tasks unless the implementation changes away from context-local state.
    session_id = f"test-session-workflow-{request.node.name}-{uuid.uuid4()}"
    set_session_id(session_id)
    yield session_id
    clear_session_id()


@pytest.fixture
def non_local_env():
    """Force non-local env behavior so token-usage MESSAGE chunks stay out of assertions."""
    with patch("services.chat_service.is_local_or_dev", return_value=False):
        with patch(
            "services.chat_service_refactored.is_local_or_dev", return_value=False
        ):
            yield


pytestmark = pytest.mark.pre_extraction_parity


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_job_type_selected_updates_state_and_returns_stream_contract(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
    non_local_env,
):
    fixture = _load_json_fixture("workflow_side_effects.json")
    scenario = fixture["workflow_scenarios"]["job_type_selected"]

    chat_svc = chat_service_container_workflow
    svc = _inner(chat_svc)
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)

    selected_jobtypes = scenario["input_action"]["jobtypes"]
    tool_name = scenario["expected_state_change"]["tool_name"]
    svc._position_service._aica_api_repository.post = AsyncMock(
        return_value=(None, {"ToolName": tool_name})
    )
    svc._llm_svc.update_agent_by_tool_name.return_value = (svc._agents, tool_name)
    sdk_events = [
        _make_text_delta(
            "resp-jobtype-selected-001",
            scenario["stream_contract"]["assistant_message"],
        )
    ]
    normalized_events = [
        _make_normalized_text_delta(
            "resp-jobtype-selected-001",
            scenario["stream_contract"]["assistant_message"],
        )
    ]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)

    request = ChatRequestModel(
        request_type=ChatRequestType(scenario["input_action"]["request_type"]),
        current_page=PageName.CHAT,
        message=json.dumps(selected_jobtypes, ensure_ascii=False),
        current_message_id="msg-jobtype-selected-001",
    )

    responses = await _collect_responses(
        chat_svc.job_type_decided(request, "127.0.0.1")
    )

    svc._position_service._aica_api_repository.post.assert_awaited_once_with(
        scenario["side_effects"]["position_api_path"],
        json={"JobtypeNames": selected_jobtypes},
    )
    svc._llm_svc.update_agent_by_tool_name.assert_called_once_with(
        _state(svc).model_name,
        tool_name,
        selected_jobtypes,
        svc._agents,
    )
    developer_histories = [
        history
        for history in _flatten_saved_histories(chat_svc)
        if history.role == LLMMessageRole.DEVELOPER
    ]
    assert any(
        history.content == scenario["expected_state_change"]["developer_message"]
        for history in developer_histories
    )

    _assert_stream_contract(
        responses,
        ChatRequestType(scenario["input_action"]["request_type"]),
        scenario["stream_contract"],
    )


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_job_type_clear_resets_state_and_returns_stream_contract(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
    non_local_env,
):
    fixture = _load_json_fixture("workflow_side_effects.json")
    scenario = fixture["workflow_scenarios"]["job_type_clear"]

    chat_svc = chat_service_container_workflow
    svc = _inner(chat_svc)
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)

    svc._position_service._aica_api_repository.post = AsyncMock(
        return_value=(None, None)
    )
    svc._llm_svc.update_agent_by_tool_name.return_value = (svc._agents, None)
    sdk_events = [
        _make_text_delta(
            "resp-jobtype-clear-001",
            scenario["stream_contract"]["assistant_message"],
        )
    ]
    normalized_events = [
        _make_normalized_text_delta(
            "resp-jobtype-clear-001",
            scenario["stream_contract"]["assistant_message"],
        )
    ]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)

    request = ChatRequestModel(
        request_type=ChatRequestType(scenario["input_action"]["request_type"]),
        current_page=PageName.CHAT,
        message="{}",
        current_message_id="msg-jobtype-clear-001",
    )

    responses = await _collect_responses(chat_svc.clear_jobtype(request, "127.0.0.1"))

    svc._position_service._aica_api_repository.post.assert_awaited_once()
    clear_post_args = svc._position_service._aica_api_repository.post.await_args
    assert clear_post_args is not None
    assert clear_post_args.args
    assert clear_post_args.args[0] == scenario["side_effects"]["position_api_path"]
    assert clear_post_args.kwargs.get("json") in (None, {})
    svc._llm_svc.update_agent_by_tool_name.assert_called_once_with(
        _state(svc).model_name,
        None,
        None,
        svc._agents,
    )
    developer_histories = [
        history
        for history in _flatten_saved_histories(chat_svc)
        if history.role == LLMMessageRole.DEVELOPER
    ]
    assert any(
        scenario["expected_state_change"]["developer_message_contains"]
        in history.content
        for history in developer_histories
    )

    _assert_stream_contract(
        responses,
        ChatRequestType(scenario["input_action"]["request_type"]),
        scenario["stream_contract"],
    )


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_workflow_submitted_persists_answers_and_returns_stream_contract(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
    non_local_env,
):
    fixture = _load_json_fixture("workflow_side_effects.json")
    scenario = fixture["workflow_scenarios"]["workflow_submitted"]

    chat_svc = chat_service_container_workflow
    svc = _inner(chat_svc)
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)

    workflow_id = scenario["workflow_input"]["workflow_id"]
    workflow_name = scenario["side_effects"]["workflow_definition_name"]
    svc._workflow_service._workflow_definition_repository.get_definition.return_value = _make_workflow_definition(
        workflow_id, workflow_name
    )
    sdk_events = [
        _make_text_delta(
            "resp-workflow-submitted-001",
            scenario["stream_contract"]["assistant_message"],
        )
    ]
    normalized_events = [
        _make_normalized_text_delta(
            "resp-workflow-submitted-001",
            scenario["stream_contract"]["assistant_message"],
        )
    ]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)

    request = ChatRequestModel(
        request_type=ChatRequestType(scenario["workflow_input"]["request_type"]),
        current_page=PageName.CHAT,
        message=json.dumps(
            {
                "workflow_id": workflow_id,
                "answers": scenario["workflow_input"]["answers"],
            },
            ensure_ascii=False,
        ),
        current_message_id="msg-workflow-submitted-001",
    )

    responses = await _collect_responses(
        chat_svc.workflow_submitted(request, "127.0.0.1")
    )

    svc._workflow_service._workflow_repository.save_workflow_answer.assert_called_once_with(
        workflow_id,
        scenario["expected_state_change"]["saved_answers"],
    )
    saved_histories = _flatten_saved_histories(chat_svc)
    workflow_histories = [
        history
        for history in saved_histories
        if history.message_id.startswith(f"wf_{workflow_id}_")
    ]
    assert len(workflow_histories) == 2
    assert [
        {
            "role": getattr(history.role, "value", history.role),
            "content": history.content,
        }
        for history in workflow_histories
    ] == scenario["expected_state_change"]["saved_history_pairs"]
    developer_histories = [
        history
        for history in saved_histories
        if history.role == LLMMessageRole.DEVELOPER
    ]
    developer_content = "\n".join(history.content for history in developer_histories)
    for expected_substring in scenario["expected_state_change"][
        "developer_message_contains"
    ]:
        assert expected_substring in developer_content

    _assert_stream_contract(
        responses,
        ChatRequestType(scenario["workflow_input"]["request_type"]),
        scenario["stream_contract"],
    )


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_workflow_cancelled_validates_definition_and_returns_stream_contract(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
    non_local_env,
):
    fixture = _load_json_fixture("workflow_side_effects.json")
    scenario = fixture["workflow_scenarios"]["workflow_cancelled"]

    chat_svc = chat_service_container_workflow
    svc = _inner(chat_svc)
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)

    workflow_id = scenario["cancel_action"]["workflow_id"]
    svc._workflow_service._workflow_definition_repository.get_definition.return_value = _make_workflow_definition(
        workflow_id,
        scenario["side_effects"]["workflow_definition_name"],
    )
    sdk_events = [
        _make_text_delta(
            "resp-workflow-cancelled-001",
            scenario["stream_contract"]["assistant_message"],
        )
    ]
    normalized_events = [
        _make_normalized_text_delta(
            "resp-workflow-cancelled-001",
            scenario["stream_contract"]["assistant_message"],
        )
    ]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)

    request = ChatRequestModel(
        request_type=ChatRequestType(scenario["cancel_action"]["request_type"]),
        current_page=PageName.CHAT,
        message=json.dumps({"workflow_id": workflow_id}, ensure_ascii=False),
        current_message_id="msg-workflow-cancelled-001",
    )

    responses = await _collect_responses(
        chat_svc.workflow_cancelled(request, "127.0.0.1")
    )

    svc._workflow_service._workflow_definition_repository.get_definition.assert_called_once_with(
        workflow_id
    )
    svc._workflow_service._workflow_repository.save_workflow_answer.assert_not_called()
    developer_histories = [
        history
        for history in _flatten_saved_histories(chat_svc)
        if history.role == LLMMessageRole.DEVELOPER
    ]
    developer_content = "\n".join(history.content for history in developer_histories)
    for expected_substring in scenario["expected_state_change"][
        "developer_message_contains"
    ]:
        assert expected_substring in developer_content

    _assert_stream_contract(
        responses,
        ChatRequestType(scenario["cancel_action"]["request_type"]),
        scenario["stream_contract"],
    )


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_job_type_decided_returns_validation_errors_for_invalid_payloads(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
):
    chat_svc = chat_service_container_workflow
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)

    invalid_json_request = ChatRequestModel(
        request_type=ChatRequestType.JOB_TYPES_SELECTED,
        current_page=PageName.CHAT,
        message="{invalid",
        current_message_id="msg-jobtype-invalid-json",
    )
    non_list_request = ChatRequestModel(
        request_type=ChatRequestType.JOB_TYPES_SELECTED,
        current_page=PageName.CHAT,
        message=json.dumps({"jobtypes": ["x"]}, ensure_ascii=False),
        current_message_id="msg-jobtype-non-list",
    )
    empty_list_request = ChatRequestModel(
        request_type=ChatRequestType.JOB_TYPES_SELECTED,
        current_page=PageName.CHAT,
        message=json.dumps(["", "   "], ensure_ascii=False),
        current_message_id="msg-jobtype-empty-list",
    )

    invalid_json_responses = await _collect_responses(
        chat_svc.job_type_decided(invalid_json_request, "127.0.0.1")
    )
    non_list_responses = await _collect_responses(
        chat_svc.job_type_decided(non_list_request, "127.0.0.1")
    )
    empty_list_responses = await _collect_responses(
        chat_svc.job_type_decided(empty_list_request, "127.0.0.1")
    )

    assert len(invalid_json_responses) == 1
    assert invalid_json_responses[0].response_type == ChatResponseType.ERROR
    assert invalid_json_responses[0].message == "不正なJSON形式です"

    assert len(non_list_responses) == 1
    assert non_list_responses[0].response_type == ChatResponseType.ERROR
    assert non_list_responses[0].message == "職種が選択されていない"

    assert len(empty_list_responses) == 1
    assert empty_list_responses[0].response_type == ChatResponseType.ERROR
    assert empty_list_responses[0].message == "職種が選択されていない"


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_job_type_decided_returns_error_when_tool_update_fails(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
):
    chat_svc = chat_service_container_workflow
    svc = _inner(chat_svc)
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)

    request = ChatRequestModel(
        request_type=ChatRequestType.JOB_TYPES_SELECTED,
        current_page=PageName.CHAT,
        message=json.dumps(["データサイエンティスト"], ensure_ascii=False),
        current_message_id="msg-jobtype-tool-failure",
    )

    svc._position_service.update_jobtypes = AsyncMock(
        side_effect=[
            None,
            "search_job_postings",
            "search_job_postings",
        ]
    )

    responses = await _collect_responses(
        chat_svc.job_type_decided(request, "127.0.0.1")
    )
    assert responses[0].message == "該当職種がまだサポートされていません。"

    svc._llm_svc.update_agent_by_tool_name.return_value = ({}, "search_job_postings")
    responses = await _collect_responses(
        chat_svc.job_type_decided(request, "127.0.0.1")
    )
    assert responses[0].message == "求人検索ツールの設定に失敗しました。"

    svc._llm_svc.update_agent_by_tool_name.return_value = (
        svc._agents,
        "other_tool",
    )
    responses = await _collect_responses(
        chat_svc.job_type_decided(request, "127.0.0.1")
    )
    assert responses[0].message == "求人検索ツールの設定に失敗しました。"
    assert svc._position_service.update_jobtypes.await_count == 3


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_workflow_submitted_returns_validation_errors_for_invalid_payloads(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
):
    chat_svc = chat_service_container_workflow
    svc = _inner(chat_svc)
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)

    invalid_json_request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
        current_page=PageName.CHAT,
        message="{invalid",
        current_message_id="msg-workflow-invalid-json",
    )
    missing_fields_request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
        current_page=PageName.CHAT,
        message=json.dumps({"workflow_id": "", "answers": []}, ensure_ascii=False),
        current_message_id="msg-workflow-missing-fields",
    )

    invalid_responses = await _collect_responses(
        chat_svc.workflow_submitted(invalid_json_request, "127.0.0.1")
    )
    missing_responses = await _collect_responses(
        chat_svc.workflow_submitted(missing_fields_request, "127.0.0.1")
    )

    assert invalid_responses[0].message == "不正なJSON形式です"
    assert (
        missing_responses[0].message
        == "ワークフローIDが存在しない、または不正な回答形式です"
    )


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_workflow_submitted_returns_service_errors_and_allows_no_save_path(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
):
    chat_svc = chat_service_container_workflow
    svc = _inner(chat_svc)
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)

    request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
        current_page=PageName.CHAT,
        message=json.dumps(
            {"workflow_id": "career-fit", "answers": {"1": [{"value": 1}]}},
            ensure_ascii=False,
        ),
        current_message_id="msg-workflow-service-errors",
    )

    svc._workflow_service.process_workflow_submission = AsyncMock(
        side_effect=ValueError("bad answers")
    )
    responses = await _collect_responses(
        chat_svc.workflow_submitted(request, "127.0.0.1")
    )
    assert responses[0].message == "bad answers"

    svc._workflow_service.process_workflow_submission = AsyncMock(
        side_effect=FileNotFoundError("missing")
    )
    responses = await _collect_responses(
        chat_svc.workflow_submitted(request, "127.0.0.1")
    )
    assert responses[0].message == "ワークフロー定義が見つかりません: career-fit"

    svc._workflow_service.process_workflow_submission = AsyncMock(
        return_value=(
            WorkflowPostProcessingResult(message="回答ありがとうございました。"),
            [],
        )
    )
    sdk_events = [_make_text_delta("resp-workflow-no-save", "続けます。")]
    normalized_events = [
        _make_normalized_text_delta("resp-workflow-no-save", "続けます。")
    ]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)
    responses = await _collect_responses(
        chat_svc.workflow_submitted(request, "127.0.0.1")
    )
    assert responses[-1].response_type == ChatResponseType.END


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy"])
async def test_workflow_submitted_returns_jobtype_update_error_before_chat(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
):
    chat_svc = chat_service_container_workflow
    svc = _inner(chat_svc)
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)

    request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
        current_page=PageName.CHAT,
        message=json.dumps(
            {"workflow_id": "career-fit", "answers": {"1": [{"value": 1}]}},
            ensure_ascii=False,
        ),
        current_message_id="msg-workflow-selected-jobtypes-error",
    )

    svc._workflow_service.process_workflow_submission = AsyncMock(
        return_value=(
            WorkflowPostProcessingResult(
                message="回答ありがとうございました。",
                selected_jobtypes=["データサイエンティスト"],
            ),
            [],
        )
    )
    expected_error = ChatStreamResponse(
        request_type=request.request_type
    ).create_error_response("職種更新に失敗しました")
    svc._apply_jobtypes_and_update_agents = AsyncMock(return_value=expected_error)
    svc._run_streamed = MagicMock()

    responses = await _collect_responses(
        chat_svc.workflow_submitted(request, "127.0.0.1")
    )

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR
    assert responses[0].message == "職種更新に失敗しました"
    svc._run_streamed.assert_not_called()


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_workflow_cancelled_uses_fallback_message_for_malformed_or_unknown_workflow(
    variant,
    chat_service_container_workflow,
    workflow_session_id,
    non_local_env,
):
    chat_svc = chat_service_container_workflow
    svc = _inner(chat_svc)
    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, workflow_session_id)
    svc._workflow_service.exists_definition = MagicMock(
        side_effect=lambda workflow_id: workflow_id != "unknown"
    )
    sdk_events = [_make_text_delta("resp-workflow-cancelled", "案内を続けます。")]
    normalized_events = [
        _make_normalized_text_delta("resp-workflow-cancelled", "案内を続けます。")
    ]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)

    malformed_request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_CANCELLED,
        current_page=PageName.CHAT,
        message="{invalid",
        current_message_id="msg-workflow-cancelled-malformed",
    )
    missing_request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_CANCELLED,
        current_page=PageName.CHAT,
        message=json.dumps({}, ensure_ascii=False),
        current_message_id="msg-workflow-cancelled-missing",
    )
    unknown_request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_CANCELLED,
        current_page=PageName.CHAT,
        message=json.dumps({"workflow_id": "unknown"}, ensure_ascii=False),
        current_message_id="msg-workflow-cancelled-unknown",
    )

    malformed_responses = await _collect_responses(
        chat_svc.workflow_cancelled(malformed_request, "127.0.0.1")
    )
    missing_responses = await _collect_responses(
        chat_svc.workflow_cancelled(missing_request, "127.0.0.1")
    )
    unknown_responses = await _collect_responses(
        chat_svc.workflow_cancelled(unknown_request, "127.0.0.1")
    )

    for responses in (malformed_responses, missing_responses, unknown_responses):
        assert responses[-1].response_type == ChatResponseType.END

    developer_histories = [
        history
        for history in _flatten_saved_histories(chat_svc)
        if history.role == LLMMessageRole.DEVELOPER
    ]
    developer_content = "\n".join(history.content for history in developer_histories)
    assert "ユーザーがワークフローを中断しました。" in developer_content
    assert svc._workflow_service.exists_definition.call_args_list[-1].args == (
        "unknown",
    )
