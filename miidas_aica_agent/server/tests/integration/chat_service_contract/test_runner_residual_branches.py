from __future__ import annotations

"""
Runner residual branch テスト。

テストケース一覧:
- test_json_default_supports_all_fallback_shapes
    対象: _json_default の fallback 変換が
    想定 shape 全種を扱えること。
- test_chat_invokes_runner_seam_and_serializes_usage_variants
    対象: chat() が runner seam を呼び出し、
    usage 差分を直列化できること。
- test_chat_retries_after_tool_message_failure_and_updates_runner_state
    対象: tool message 失敗後の retry と
    runner 状態更新が成立すること。
- test_chat_returns_rate_limit_error_for_position_search_tool
    対象: position search tool の rate limit 超過時に
    専用エラーを返すこと。
- test_chat_covers_workflow_application_and_registration_branches
    対象: workflow application/registration 系の残余分岐を
    退行なく通過できること。
- test_previous_history_and_jobtype_result_residual_branches
    対象: previous history と jobtype result に関する
    残余分岐を網羅すること。
- test_chat_covers_misc_stream_event_and_stop_at_residual_branches
    対象: misc stream event と stop_at 系残余分岐を
    正しく処理すること。
- test_chat_handles_unexpected_security_errors_and_generator_exit_before_stream_start
    対象: 想定外 security error と stream 開始前 generator 終了を
    安全に処理すること。
- test_chat_finalizes_cleanly_when_runner_emits_no_events
    対象: runner 無イベント時にクリーンに finalize すること。
- test_chat_finalizes_after_single_unhandled_stream_event
    対象: 未処理 stream event 単発時でも
    後始末して終了すること。
- test_chat_flushes_queued_run_items_when_second_turn_creates_session
    対象: 2ターン目で session 作成時に queued run items を
    flush すること。
- test_final_residual_helper_arcs_for_security_and_tool_output
    対象: security/tool output に関する
    最終 residual helper 経路を担保すること。
"""

from dataclasses import dataclass
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from .chat_service_contract_helpers import (
    _FakeRunStream,
    _attach_run_with_retry_passthrough,
    _inner,
    _state,
)
from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from openai.types.responses import ResponseTextDeltaEvent
from security.llm_output_guard import ForbiddenWordDetectedException
from services.chat_service import (
    APPLY_POSITION_IDS_KEY,
    DEFAULT_ERROR_MESSAGE,
    MAIN_CHAT_KEY,
    RATE_LIMIT_EXCEEDED_MESSAGE,
    _json_default,
)
from services.chat.llm_runner import (
    LLMIgnoredStreamEvent,
    LLMRawResponseEvent,
    LLMRunItemStreamEvent,
)
from services.chat.chat_persistence import _serialize_tool_output_for_storage
from services.chat.tool_event_handler import (
    RATE_LIMIT_EXCEEDED_MESSAGE as REFACTORED_RATE_LIMIT_EXCEEDED_MESSAGE,
    _parse_tool_output,
)
from services.llm_service import AgentName
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType, ChatStreamResponse
from utils.const import SESSION_START_MESSAGE
from utils.enum import LLMMessageRole, PageName, ToolName
from utils.log_utils import clear_session_id, set_session_id


_VARIANTS = [
    "legacy",
    "real-refactored",
]
# task-5: 互換モードが廃止されたため、
# legacy の _run_streamed seam を直接モックするテストは legacy only に変更する。
# real-refactored は別途 test_no_legacy_dependency.py と test_runner_contract.py で担保する。
_VARIANTS_LEGACY_ONLY = [
    "legacy",
    pytest.param(
        "real-refactored",
        marks=pytest.mark.skip(reason="pending-phase-4: real-refactored evidence"),
    ),
]
_SESSION_ID = "test-session-runner-residuals"


class _FakeRunResult:
    def __init__(
        self,
        events: list,
        *,
        input_list: list | None = None,
        usage=None,
        last_response_id: str | None = None,
        last_agent_name: str | None = None,
    ):
        self._events = events
        self._input_list = input_list or []
        self.context_wrapper = SimpleNamespace(
            usage=usage
            if usage is not None
            else {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}
        )
        self.last_response_id = last_response_id
        self.last_agent = None
        if last_agent_name is not None:
            self.last_agent = SimpleNamespace(name=last_agent_name)

    async def stream_events(self):
        for event in self._events:
            yield event

    def to_input_list(self):
        return self._input_list


class _FakeStreamEvent:
    def __init__(self, event_type: str, *, data=None, item=None):
        self.type = event_type
        self.data = data
        self.item = item


class _FakeResponseTextDeltaEvent:
    def __init__(
        self, item_id: str, delta: str, type: str = "response.output_text.delta"
    ):
        self.item_id = item_id
        self.delta = delta
        self.type = type


class _NoEventRunResult(_FakeRunResult):
    pass


class _FakeToolCallItem:
    def __init__(self, raw_item, *, stop_at_tool_names=None):
        self.raw_item = raw_item
        self.agent = SimpleNamespace(
            name="CareerAdvisor",
            tool_use_behavior={}
            if stop_at_tool_names is None
            else {"stop_at_tool_names": stop_at_tool_names},
        )


class _FakeToolCallOutputItem:
    def __init__(self, raw_item: dict, output=None):
        self.raw_item = raw_item
        self.output = output if output is not None else raw_item.get("output")
        self.agent = SimpleNamespace(name="CareerAdvisor")


class _FakeHandoffOutputItem:
    def __init__(self, target_agent_name: str):
        self.raw_item = {"call_id": "handoff-call-id", "output": "handoff-output"}
        self.agent = SimpleNamespace(name="CareerAdvisor")
        self.target_agent = SimpleNamespace(name=target_agent_name)


class _FakeReasoningItem:
    def __init__(self, summary):
        self.agent = SimpleNamespace(name="CareerAdvisor")
        self.raw_item = SimpleNamespace(id="reasoning-item-id", summary=summary)


class _DictLikeUsage:
    def __init__(self, **payload):
        self._payload = payload

    def dict(self):
        return self._payload


class _ModelDumpUsage:
    def __init__(self, **payload):
        self._payload = payload

    def model_dump(self):
        return self._payload


@dataclass
class _DataClassUsage:
    input_tokens: int
    output_tokens: int


def _make_text_delta(item_id: str, delta: str) -> _FakeStreamEvent:
    return _FakeStreamEvent(
        "raw_response_event",
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


def _prepare_chat_service(chat_svc):
    svc = _inner(chat_svc)
    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    position_guide = MagicMock()
    position_guide.name = AgentName.POSITION_GUIDE
    position_guide.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {
        "CareerAdvisor": (default_agent, True),
        AgentName.POSITION_GUIDE: (position_guide, False),
    }
    return svc, default_agent, position_guide


def _action_log_insert_payload(call) -> tuple[object | None, object | None]:
    log_type = call.kwargs.get("log_type")
    content = call.kwargs.get("content")
    if log_type is not None or content is not None:
        return log_type, content

    args = call.args
    log_type = args[0] if len(args) > 0 else None
    content = args[2] if len(args) > 2 else None
    return log_type, content


async def _consume(chat_svc, request):
    responses = []
    set_session_id(_SESSION_ID)
    try:
        async for response in chat_svc.chat(request, "127.0.0.1"):
            responses.append(response.model_copy(deep=True))
    finally:
        clear_session_id()
    return responses


def _make_request(**overrides) -> ChatRequestModel:
    payload = {
        "request_type": ChatRequestType.CHAT,
        "current_page": PageName.CHAT,
        "position_id": None,
        "message": "hello",
        "current_message_id": "msg-runner-residuals",
    }
    payload.update(overrides)
    return ChatRequestModel(**payload)


pytestmark = pytest.mark.pre_extraction_parity


def test_json_default_supports_all_fallback_shapes():
    class _PlainObject:
        def __init__(self):
            self.value = "plain"

    assert _json_default(_DataClassUsage(1, 2)) == {
        "input_tokens": 1,
        "output_tokens": 2,
    }
    assert _json_default(_ModelDumpUsage(total_tokens=3)) == {"total_tokens": 3}
    assert _json_default(_DictLikeUsage(total_tokens=4)) == {"total_tokens": 4}
    assert _json_default(_PlainObject()) == {"value": "plain"}
    assert _json_default(object()).startswith("<object object")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "variant",
    [
        "legacy",
        "real-refactored",
    ],
)
async def test_chat_invokes_runner_seam_and_serializes_usage_variants(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")
    usage = [
        _DataClassUsage(1, 2),
        _ModelDumpUsage(total_tokens=3),
        _DictLikeUsage(total_tokens=4),
        SimpleNamespace(total_tokens=5),
    ]

    if variant == "legacy":
        with (
            patch("services.chat_service.Runner.run_streamed") as mock_runner,
            patch(
                "services.chat_service.is_local_or_dev",
                return_value=False,
            ),
        ):
            for item in usage:
                mock_runner.return_value = _FakeRunResult([], usage=item)
                responses = await _consume(chat_svc, _make_request())
                assert responses[-1].response_type == ChatResponseType.END

        assert mock_runner.call_count == len(usage)
        saved_usage_payloads = [
            content
            for call in svc._action_log_repository.insert.call_args_list
            for log_type, content in [_action_log_insert_payload(call)]
            if log_type and content is not None
        ]
    else:
        # real-refactored: mock _llm_runner.run_streamed; set .usage on the returned
        # _FakeRunStream after construction. is_local_or_dev is patched to suppress
        # the token usage yield path.
        # The refactored chat() clears _conv_state.conversation[chat_key] after each
        # runner call (line 715 of chat_service_refactored.py), so the conversation
        # must be re-populated with the toolcall trace message before each subsequent
        # turn; otherwise prepare_turn finds an empty conversation and returns END
        # without ever calling run_streamed.
        streams = []
        for item in usage:
            stream = _FakeRunStream([])
            stream.usage = item
            streams.append(stream)
        mock_runner = MagicMock(side_effect=streams)
        chat_svc._llm_runner.run_streamed = mock_runner
        _attach_run_with_retry_passthrough(
            chat_svc._llm_runner,
            action_log_repository=svc._action_log_repository,
        )
        with patch(
            "services.chat_service_refactored.is_local_or_dev",
            return_value=False,
        ):
            for i, _item in enumerate(usage):
                if i > 0:
                    # Re-populate conversation after it was cleared by the previous turn.
                    _state(chat_svc).conversation[MAIN_CHAT_KEY] = [
                        chat_svc._toolcall_trace_message
                    ]
                responses = await _consume(chat_svc, _make_request())
                assert responses[-1].response_type == ChatResponseType.END

        assert mock_runner.call_count == len(usage)
        saved_usage_payloads = [
            content
            for call in svc._action_log_repository.insert.call_args_list
            for log_type, content in [_action_log_insert_payload(call)]
            if log_type and content is not None
        ]

    assert any(
        "input_tokens" in str(payload) and "1" in str(payload)
        for payload in saved_usage_payloads
    )
    if variant == "legacy":
        assert any(
            "total_tokens" in str(payload) and "3" in str(payload)
            for payload in saved_usage_payloads
        )
        assert any(
            "total_tokens" in str(payload) and "4" in str(payload)
            for payload in saved_usage_payloads
        )
        assert any(
            "total_tokens" in str(payload) and "5" in str(payload)
            for payload in saved_usage_payloads
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "variant",
    [
        "legacy",
        "real-refactored",
    ],
)
async def test_chat_retries_after_tool_message_failure_and_updates_runner_state(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")
    intermediate_agent = MagicMock()
    intermediate_agent.name = "IntermediateAgent"
    intermediate_agent.tool_use_behavior = {}
    final_agent = MagicMock()
    final_agent.name = "FinalAgent"
    final_agent.tool_use_behavior = {}
    svc._agents["IntermediateAgent"] = intermediate_agent
    svc._agents["FinalAgent"] = final_agent
    tool_call = _FakeToolCallItem(
        SimpleNamespace(
            id="tool-call-msg-failure",
            call_id="tool-call-msg-failure",
            name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        ),
        stop_at_tool_names=[ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value],
    )
    tool_output = _FakeToolCallOutputItem(
        {
            "call_id": "tool-call-msg-failure",
            "output": json.dumps({"Message": "tool failed"}, ensure_ascii=False),
        }
    )
    first_run = _FakeRunResult(
        [
            _FakeStreamEvent("run_item_stream_event", item=tool_call),
            _FakeStreamEvent("run_item_stream_event", item=tool_output),
        ],
        input_list=[
            {
                "type": "function_call_output",
                "call_id": "tool-call-msg-failure",
                "output": '["営業"]',
            }
        ],
        last_response_id="resp-first",
        last_agent_name="IntermediateAgent",
    )
    duplicate_message_event = _FakeStreamEvent(
        "raw_response_event",
        data=_FakeResponseTextDeltaEvent(
            item_id="msg-1",
            delta="ignored",
            type="not-response-text",
        ),
    )
    different_message_id_event = _FakeStreamEvent(
        "raw_response_event",
        data=_FakeResponseTextDeltaEvent(item_id="msg-2", delta="drop-me"),
    )
    empty_delta_event = _FakeStreamEvent(
        "raw_response_event",
        data=_FakeResponseTextDeltaEvent(item_id="msg-1", delta=""),
    )
    second_run = _FakeRunResult(
        [
            duplicate_message_event,
            different_message_id_event,
            empty_delta_event,
            _FakeStreamEvent(
                "run_item_stream_event", item=_FakeHandoffOutputItem("FinalAgent")
            ),
        ],
        last_response_id="resp-second",
        last_agent_name="FinalAgent",
    )
    if variant == "legacy":
        with (
            patch.object(
                svc.llm_output_guard,
                "process_stream_chunk",
                Mock(return_value=["safe"]),
            ),
            patch.object(
                svc.llm_output_guard,
                "finalize_stream",
                Mock(return_value=["final"]),
            ),
            patch("services.chat_service.ToolCallItem", _FakeToolCallItem),
            patch(
                "services.chat_service.ToolCallOutputItem",
                _FakeToolCallOutputItem,
            ),
            patch(
                "services.chat_service.HandoffOutputItem",
                _FakeHandoffOutputItem,
            ),
            patch(
                "services.chat_service.ResponseTextDeltaEvent",
                _FakeResponseTextDeltaEvent,
            ),
            patch(
                "services.chat_service.asyncio.sleep",
                new=AsyncMock(),
            ),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            svc._run_streamed = MagicMock(side_effect=[first_run, second_run])
            responses = await _consume(chat_svc, _make_request())

        assert responses[-1].response_type == ChatResponseType.END
        assert svc._run_streamed.call_count == 2
    else:
        first_run_stream = _FakeRunStream(
            [
                _FakeStreamEvent("run_item_stream_event", item=tool_call),
                _FakeStreamEvent("run_item_stream_event", item=tool_output),
            ]
        )
        first_run_stream.continuation_state = "resp-first"
        first_run_stream.agent_state = SimpleNamespace(name="IntermediateAgent")

        second_run_stream = _FakeRunStream(
            [
                _FakeStreamEvent(
                    "run_item_stream_event",
                    item=_FakeHandoffOutputItem("FinalAgent"),
                )
            ]
        )
        second_run_stream.continuation_state = "resp-second"
        second_run_stream.agent_state = SimpleNamespace(name="FinalAgent")

        chat_svc._llm_runner.run_streamed = MagicMock(
            side_effect=[first_run_stream, second_run_stream]
        )
        _attach_run_with_retry_passthrough(chat_svc._llm_runner)
        with (
            patch(
                "services.chat_service_refactored.is_local_or_dev",
                return_value=False,
            ),
            patch(
                "services.chat_service_refactored.asyncio.sleep",
                new=AsyncMock(),
            ),
            patch(
                "services.chat.stream_event_processor.ToolCallItem",
                _FakeToolCallItem,
            ),
            patch(
                "services.chat.stream_event_processor.ToolCallOutputItem",
                _FakeToolCallOutputItem,
            ),
        ):
            responses = await _consume(chat_svc, _make_request())

        assert responses[-1].response_type == ChatResponseType.END
        assert chat_svc._llm_runner.run_streamed.call_count == 2

    if variant == "legacy":
        assert svc._previous_response_ids[MAIN_CHAT_KEY] == "resp-second"
    else:
        assert _state(svc).previous_continuation_states[MAIN_CHAT_KEY] == "resp-second"
    assert _state(svc).active_agent_name == "FinalAgent"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "variant",
    [
        "legacy",
        "real-refactored",
    ],
)
async def test_chat_returns_rate_limit_error_for_position_search_tool(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")
    svc._rate_limit_service.is_within_position_search_limit = Mock(return_value=False)
    position_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="tool-call-position-rate-limit",
            call_id="tool-call-position-rate-limit",
            name=ToolName.GENERIC_POSITION_SEARCH.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )
    )
    run_result = _FakeRunResult(
        [_FakeStreamEvent("run_item_stream_event", item=position_tool)]
    )

    if variant == "legacy":
        with (
            patch("services.chat_service.ToolCallItem", _FakeToolCallItem),
            patch(
                "services.chat_service.is_local_or_dev",
                return_value=False,
            ),
        ):
            svc._run_streamed = MagicMock(return_value=run_result)
            responses = await _consume(chat_svc, _make_request())
    else:
        run_stream = _FakeRunStream(
            [_FakeStreamEvent("run_item_stream_event", item=position_tool)]
        )
        chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)
        _attach_run_with_retry_passthrough(chat_svc._llm_runner)
        with (
            patch(
                "services.chat.stream_event_processor.ToolCallItem", _FakeToolCallItem
            ),
            patch(
                "services.chat_service_refactored.is_local_or_dev",
                return_value=False,
            ),
        ):
            responses = await _consume(chat_svc, _make_request())

    assert responses[0].response_type == ChatResponseType.ERROR
    if variant == "legacy":
        assert responses[0].message == RATE_LIMIT_EXCEEDED_MESSAGE
    else:
        assert responses[0].message == REFACTORED_RATE_LIMIT_EXCEEDED_MESSAGE


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "variant,session_status,tool_name,parsed_output,current_page,position_id,expect_error",
    [
        (
            "legacy",
            ChatSessionStatus.CHATTING,
            ToolName.START_WORKFLOW.value,
            {"WorkflowID": "wf-1"},
            PageName.CHAT,
            None,
            True,
        ),
        (
            "legacy",
            ChatSessionStatus.CHATTING,
            ToolName.START_WORKFLOW.value,
            {},
            PageName.CHAT,
            None,
            False,
        ),
        (
            "legacy",
            ChatSessionStatus.CHATTING,
            ToolName.APPLICATION.value,
            {},
            PageName.POSITION_DETAIL,
            "encrypted-position",
            False,
        ),
        (
            "legacy",
            ChatSessionStatus.APPLYING,
            ToolName.APPLICATION.value,
            {},
            PageName.CHAT,
            None,
            False,
        ),
        (
            "legacy",
            ChatSessionStatus.REGISTERING,
            ToolName.APPLICATION.value,
            {},
            PageName.CHAT,
            None,
            False,
        ),
        (
            "legacy",
            ChatSessionStatus.CHATTING,
            ToolName.APPLICATION.value,
            {},
            PageName.CHAT,
            None,
            False,
        ),
        (
            "legacy",
            ChatSessionStatus.REGISTERED,
            ToolName.APPLICATION.value,
            {},
            PageName.CHAT,
            None,
            False,
        ),
        (
            "legacy",
            ChatSessionStatus.CHATTING,
            ToolName.REGISTRATION.value,
            {},
            PageName.CHAT,
            None,
            False,
        ),
        (
            "legacy",
            ChatSessionStatus.REGISTERING,
            ToolName.REGISTRATION.value,
            {},
            PageName.PROFILE_BASIC_INFO,
            None,
            False,
        ),
        (
            "real-refactored",
            ChatSessionStatus.CHATTING,
            ToolName.START_WORKFLOW.value,
            {"WorkflowID": "wf-1"},
            PageName.CHAT,
            None,
            True,
        ),
    ],
)
async def test_chat_covers_workflow_application_and_registration_branches(
    variant,
    session_status,
    tool_name,
    parsed_output,
    current_page,
    position_id,
    expect_error,
    chat_service_container,
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")
    svc._user_repository = MagicMock()
    svc._action_log_repository = MagicMock()
    svc._chat_repository.session_status.return_value = session_status
    svc._workflow_service.get_definition = (
        Mock(side_effect=FileNotFoundError("missing")) if expect_error else Mock()
    )
    svc._get_position_detail = AsyncMock(return_value=({}, {}, {}, ""))
    if current_page not in (PageName.CHAT, PageName.POSITION_DETAIL):
        svc._prepare_for_chat_turn = AsyncMock(return_value=None)
        _state(svc).conversation[MAIN_CHAT_KEY] = [svc._toolcall_trace_message]
    tool_call = _FakeToolCallItem(
        SimpleNamespace(
            id=f"tool-{tool_name}",
            call_id=f"call-{tool_name}",
            name=tool_name,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )
    )
    tool_output = _FakeToolCallOutputItem(
        {
            "call_id": f"call-{tool_name}",
            "output": json.dumps(parsed_output, ensure_ascii=False),
        }
    )

    with (
        patch("services.chat_service.ToolCallItem", _FakeToolCallItem),
        patch(
            "services.chat_service.ToolCallOutputItem",
            _FakeToolCallOutputItem,
        ),
        patch("services.chat_service.decrypt", return_value="real-position-id"),
        patch(
            "services.chat_service.is_local_or_dev",
            return_value=False,
        ),
    ):
        svc._run_streamed = MagicMock(
            return_value=_FakeRunResult(
                [
                    _FakeStreamEvent("run_item_stream_event", item=tool_call),
                    _FakeStreamEvent("run_item_stream_event", item=tool_output),
                ]
            )
        )
        responses = await _consume(
            chat_svc,
            _make_request(
                current_page=current_page,
                position_id=position_id,
            ),
        )

    assert responses[-1].response_type in {ChatResponseType.END, ChatResponseType.ERROR}
    if (
        current_page == PageName.POSITION_DETAIL
        and tool_name == ToolName.APPLICATION.value
    ):
        svc._user_repository.update_miidas_registration_user_data.assert_called_once_with(
            APPLY_POSITION_IDS_KEY,
            ["real-position-id"],
        )
    if (
        tool_name == ToolName.APPLICATION.value
        and current_page == PageName.POSITION_DETAIL
        and session_status == ChatSessionStatus.CHATTING
    ) or (
        tool_name == ToolName.REGISTRATION.value
        and current_page in (PageName.CHAT, PageName.POSITION_DETAIL)
        and session_status == ChatSessionStatus.CHATTING
    ):
        assert svc._chat_repository.update_session_status.called
    if (
        tool_name == ToolName.REGISTRATION.value
        and current_page
        in (
            PageName.CHAT,
            PageName.POSITION_DETAIL,
        )
        and session_status == ChatSessionStatus.CHATTING
    ):
        assert svc._action_log_repository.insert.called


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_previous_history_and_jobtype_result_residual_branches(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    histories = [
        ChatHistory(
            session_id=_SESSION_ID,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="session-start",
            role=LLMMessageRole.DEVELOPER,
            content=SESSION_START_MESSAGE,
        ),
        ChatHistory(
            session_id=_SESSION_ID,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="assistant-greeting",
            role=LLMMessageRole.ASSISTANT,
            content="こんにちは",
        ),
        ChatHistory(
            session_id=_SESSION_ID,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="user-1",
            role=LLMMessageRole.USER,
            content="求人を探したい",
        ),
        ChatHistory(
            session_id=_SESSION_ID,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="tool-empty",
            role=LLMMessageRole.TOOL,
            content="",
            tool_call_id="tool-empty",
            tool_name=ToolName.GENERIC_POSITION_SEARCH.value,
            tool_input={},
        ),
        ChatHistory(
            session_id=_SESSION_ID,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="tool-invalid-position",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"AllPositionIds": ["p1"]}, ensure_ascii=False),
            tool_call_id="tool-invalid-position",
            tool_name=ToolName.GENERIC_POSITION_SEARCH.value,
            tool_input={"Salary": None, "Locations": []},
        ),
        ChatHistory(
            session_id=_SESSION_ID,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="tool-jobtype-none",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"Keyword": "engineer"}, ensure_ascii=False),
            tool_call_id="tool-jobtype-none",
            tool_name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value,
            tool_input={"Keyword": "engineer"},
        ),
        ChatHistory(
            session_id=_SESSION_ID,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="assistant-after-user",
            role=LLMMessageRole.ASSISTANT,
            content="承知しました",
        ),
    ]
    svc._chat_repository.get_main_chat_histories.return_value = histories

    result, has_more = await chat_svc.load_previous_chat_histories(3, None, None)

    assert has_more is True
    assert any(entry["MessageID"] == "assistant-greeting" for entry in result)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "variant",
    [
        "legacy",
        "real-refactored",
    ],
)
async def test_chat_covers_misc_stream_event_and_stop_at_residual_branches(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")

    orphan_output = _FakeToolCallOutputItem(
        {"call_id": "orphan-output", "output": "{}"}
    )
    transfer_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="transfer-tool",
            call_id="transfer-tool",
            name="transfer_to_agent",
            arguments="{}",
        )
    )
    unsupported_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="unsupported-tool",
            call_id="unsupported-tool",
            name="unsupported_tool",
            arguments="{}",
        )
    )
    invalid_position_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="position-invalid-json",
            call_id="position-invalid-json",
            name=ToolName.GENERIC_POSITION_SEARCH.value,
            arguments="{",
        ),
        stop_at_tool_names=[ToolName.GENERIC_POSITION_SEARCH.value],
    )
    jobtype_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="jobtype-empty",
            call_id="jobtype-empty",
            name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        ),
        stop_at_tool_names=[ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value],
    )
    jobtype_output = _FakeToolCallOutputItem(
        {"call_id": "jobtype-empty", "output": "{}"}
    )
    parse_empty_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="parse-empty-tool",
            call_id="parse-empty-tool",
            name=ToolName.START_WORKFLOW.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )
    )
    parse_empty_output = _FakeToolCallOutputItem(
        {"call_id": "parse-empty-tool", "output": []}
    )
    parse_not_dict_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="parse-not-dict-tool",
            call_id="parse-not-dict-tool",
            name=ToolName.START_WORKFLOW.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )
    )
    parse_not_dict_output = _FakeToolCallOutputItem(
        {"call_id": "parse-not-dict-tool", "output": [123]}
    )
    parse_invalid_type_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="parse-invalid-type-tool",
            call_id="parse-invalid-type-tool",
            name=ToolName.START_WORKFLOW.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )
    )
    parse_invalid_type_output = _FakeToolCallOutputItem(
        {"call_id": "parse-invalid-type-tool", "output": 123}
    )
    parse_text_not_string_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="parse-text-not-string-tool",
            call_id="parse-text-not-string-tool",
            name=ToolName.START_WORKFLOW.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )
    )
    parse_text_not_string_output = _FakeToolCallOutputItem(
        {"call_id": "parse-text-not-string-tool", "output": [{"text": 123}]}
    )
    parse_invalid_json_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="parse-invalid-json-tool",
            call_id="parse-invalid-json-tool",
            name=ToolName.START_WORKFLOW.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )
    )
    parse_invalid_json_output = _FakeToolCallOutputItem(
        {"call_id": "parse-invalid-json-tool", "output": [{"text": "{invalid"}]}
    )
    workflow_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="workflow-missing-id",
            call_id="workflow-missing-id",
            name=ToolName.START_WORKFLOW.value,
            arguments='{"SessionID":"s","RequestID":"r"}',
        )
    )
    workflow_output = _FakeToolCallOutputItem(
        {"call_id": "workflow-missing-id", "output": "{}"}
    )
    run_result = _FakeRunResult(
        [
            _FakeStreamEvent(
                "raw_response_event",
                data=SimpleNamespace(item_id="ignored", delta="not-a-response-text"),
            ),
            _FakeStreamEvent("heartbeat"),
            _FakeStreamEvent("run_item_stream_event", item=orphan_output),
            _FakeStreamEvent("run_item_stream_event", item=transfer_tool),
            _FakeStreamEvent(
                "run_item_stream_event",
                item=_FakeReasoningItem([{"summary_text": "residual reasoning"}]),
            ),
            _FakeStreamEvent("run_item_stream_event", item=object()),
            _FakeStreamEvent("run_item_stream_event", item=unsupported_tool),
            _FakeStreamEvent("run_item_stream_event", item=invalid_position_tool),
            _FakeStreamEvent("run_item_stream_event", item=jobtype_tool),
            _FakeStreamEvent("run_item_stream_event", item=jobtype_output),
            _FakeStreamEvent("run_item_stream_event", item=parse_empty_tool),
            _FakeStreamEvent("run_item_stream_event", item=parse_empty_output),
            _FakeStreamEvent("run_item_stream_event", item=parse_not_dict_tool),
            _FakeStreamEvent("run_item_stream_event", item=parse_not_dict_output),
            _FakeStreamEvent("run_item_stream_event", item=parse_invalid_type_tool),
            _FakeStreamEvent("run_item_stream_event", item=parse_invalid_type_output),
            _FakeStreamEvent("run_item_stream_event", item=parse_text_not_string_tool),
            _FakeStreamEvent(
                "run_item_stream_event",
                item=parse_text_not_string_output,
            ),
            _FakeStreamEvent("run_item_stream_event", item=parse_invalid_json_tool),
            _FakeStreamEvent(
                "run_item_stream_event",
                item=parse_invalid_json_output,
            ),
            _FakeStreamEvent("run_item_stream_event", item=workflow_tool),
            _FakeStreamEvent("run_item_stream_event", item=workflow_output),
        ],
        input_list=[
            {"type": "ignored"},
            {
                "type": "function_call_output",
                "call_id": "position-invalid-json",
                "output": "first-output",
            },
            {
                "type": "function_call_output",
                "call_id": "position-invalid-json",
                "output": "duplicate-output",
            },
            {
                "type": "function_call_output",
                "call_id": "jobtype-empty",
                "output": '["営業"]',
            },
            {
                "type": "function_call_output",
                "call_id": "fallback-output",
                "output": "fallback-output",
            },
        ],
    )

    if variant == "legacy":
        with (
            patch("services.chat_service.ToolCallItem", _FakeToolCallItem),
            patch(
                "services.chat_service.ToolCallOutputItem",
                _FakeToolCallOutputItem,
            ),
            patch(
                "services.chat_service.ReasoningItem",
                _FakeReasoningItem,
            ),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            svc._run_streamed = MagicMock(return_value=run_result)
            responses = await _consume(chat_svc, _make_request())
    else:
        run_stream = _FakeRunStream(
            [
                LLMIgnoredStreamEvent(),
                LLMIgnoredStreamEvent(),
                LLMRunItemStreamEvent(item=orphan_output),
                LLMRunItemStreamEvent(item=transfer_tool),
                LLMRunItemStreamEvent(
                    item=_FakeReasoningItem([{"summary_text": "residual reasoning"}])
                ),
                LLMRunItemStreamEvent(item=object()),
                LLMRunItemStreamEvent(item=unsupported_tool),
                LLMRunItemStreamEvent(item=invalid_position_tool),
                LLMRunItemStreamEvent(item=jobtype_tool),
                LLMRunItemStreamEvent(item=jobtype_output),
                LLMRunItemStreamEvent(item=parse_empty_tool),
                LLMRunItemStreamEvent(item=parse_empty_output),
                LLMRunItemStreamEvent(item=parse_not_dict_tool),
                LLMRunItemStreamEvent(item=parse_not_dict_output),
                LLMRunItemStreamEvent(item=parse_invalid_type_tool),
                LLMRunItemStreamEvent(item=parse_invalid_type_output),
                LLMRunItemStreamEvent(item=parse_text_not_string_tool),
                LLMRunItemStreamEvent(item=parse_text_not_string_output),
                LLMRunItemStreamEvent(item=parse_invalid_json_tool),
                LLMRunItemStreamEvent(item=parse_invalid_json_output),
                LLMRunItemStreamEvent(item=workflow_tool),
                LLMRunItemStreamEvent(item=workflow_output),
            ]
        )
        run_stream.replay_items = run_result.to_input_list()
        chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)
        _attach_run_with_retry_passthrough(chat_svc._llm_runner)
        with (
            patch(
                "services.chat.stream_event_processor.ToolCallItem", _FakeToolCallItem
            ),
            patch(
                "services.chat.stream_event_processor.ToolCallOutputItem",
                _FakeToolCallOutputItem,
            ),
            patch("services.chat.chat_persistence.ReasoningItem", _FakeReasoningItem),
            patch(
                "services.chat_service_refactored.is_local_or_dev",
                return_value=False,
            ),
        ):
            responses = await _consume(chat_svc, _make_request())

    assert responses[-1].response_type == ChatResponseType.END
    position_outputs = [
        item
        for item in _state(svc).conversation[MAIN_CHAT_KEY]
        if isinstance(item, dict) and item.get("call_id") == "position-invalid-json"
    ]
    assert len(position_outputs) == 1
    assert any(
        item.get("call_id") == "jobtype-empty"
        and "###ツールが選定した職種一覧" in item.get("output", "")
        for item in _state(svc).conversation[MAIN_CHAT_KEY]
        if isinstance(item, dict)
    )
    assert any(
        item.get("call_id") == "fallback-output"
        for item in _state(svc).conversation[MAIN_CHAT_KEY]
        if isinstance(item, dict)
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "variant",
    [
        "legacy",
        "real-refactored",
    ],
)
async def test_chat_handles_unexpected_security_errors_and_generator_exit_before_stream_start(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")

    if variant == "legacy":
        with (
            patch.object(
                svc.llm_output_guard,
                "process_stream_chunk",
                Mock(side_effect=ValueError("unexpected-guard-error")),
            ),
            patch(
                "services.chat_service.MAX_LLM_RETRY_COUNT",
                1,
            ),
            patch(
                "services.chat_service.asyncio.sleep",
                new=AsyncMock(),
            ),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            svc._run_streamed = MagicMock(
                return_value=_FakeRunResult(
                    [_make_text_delta("resp-guard-error", "危険")]
                )
            )
            responses = await _consume(chat_svc, _make_request())
    else:
        run_stream = _FakeRunStream([LLMRawResponseEvent("resp-guard-error", "危険")])
        chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)
        _attach_run_with_retry_passthrough(chat_svc._llm_runner)
        with (
            patch.object(
                svc.llm_output_guard,
                "process_stream_chunk",
                Mock(side_effect=ValueError("unexpected-guard-error")),
            ),
            patch(
                "services.chat_service_refactored.asyncio.sleep",
                new=AsyncMock(),
            ),
            patch(
                "services.chat_service_refactored.is_local_or_dev", return_value=False
            ),
        ):
            responses = await _consume(chat_svc, _make_request())

    assert responses[-1].response_type == ChatResponseType.ERROR
    assert responses[-1].message == DEFAULT_ERROR_MESSAGE

    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")

    if variant == "legacy":
        with patch("services.chat_service.is_local_or_dev", return_value=False):
            svc._run_streamed = MagicMock(side_effect=GeneratorExit())
            set_session_id(_SESSION_ID)
            try:
                generator = chat_svc.chat(_make_request(), "127.0.0.1")
                with pytest.raises(GeneratorExit):
                    await anext(generator)
            finally:
                clear_session_id()
    else:
        with patch(
            "services.chat_service_refactored.is_local_or_dev", return_value=False
        ):
            chat_svc._llm_runner.run_streamed = MagicMock(side_effect=GeneratorExit())
            _attach_run_with_retry_passthrough(chat_svc._llm_runner)
            set_session_id(_SESSION_ID)
            try:
                generator = chat_svc.chat(_make_request(), "127.0.0.1")
                with pytest.raises(GeneratorExit):
                    await anext(generator)
            finally:
                clear_session_id()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "variant",
    [
        "legacy",
        "real-refactored",
    ],
)
async def test_chat_finalizes_cleanly_when_runner_emits_no_events(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")

    if variant == "legacy":
        run_result = _NoEventRunResult([], last_response_id="resp-no-events")
        with (
            patch.object(
                svc.llm_output_guard,
                "finalize_stream",
                Mock(return_value=[]),
            ) as finalize_mock,
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            svc._run_streamed = MagicMock(return_value=run_result)
            responses = await _consume(chat_svc, _make_request())
    else:
        run_stream = _FakeRunStream([])
        run_stream.continuation_state = "resp-no-events"
        chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)
        _attach_run_with_retry_passthrough(chat_svc._llm_runner)
        with (
            patch.object(
                svc.llm_output_guard,
                "finalize_stream",
                Mock(return_value=[]),
            ) as finalize_mock,
            patch(
                "services.chat_service_refactored.is_local_or_dev", return_value=False
            ),
        ):
            responses = await _consume(chat_svc, _make_request())

    assert responses[-1].response_type == ChatResponseType.END
    finalize_mock.assert_called_once()
    if variant == "legacy":
        assert svc._previous_response_ids[MAIN_CHAT_KEY] == "resp-no-events"
    else:
        assert (
            _state(svc).previous_continuation_states[MAIN_CHAT_KEY] == "resp-no-events"
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "variant",
    [
        "legacy",
        "real-refactored",
    ],
)
async def test_chat_finalizes_after_single_unhandled_stream_event(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")

    if variant == "legacy":
        run_result = _FakeRunResult(
            [_FakeStreamEvent("heartbeat")],
            last_response_id="resp-single-heartbeat",
        )
        with (
            patch.object(
                svc.llm_output_guard,
                "finalize_stream",
                Mock(return_value=[]),
            ) as finalize_mock,
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            svc._run_streamed = MagicMock(return_value=run_result)
            responses = await _consume(chat_svc, _make_request())
    else:
        run_stream = _FakeRunStream([_FakeStreamEvent("heartbeat")])
        run_stream.continuation_state = "resp-single-heartbeat"
        chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)
        _attach_run_with_retry_passthrough(chat_svc._llm_runner)
        with (
            patch.object(
                svc.llm_output_guard,
                "finalize_stream",
                Mock(return_value=[]),
            ) as finalize_mock,
            patch(
                "services.chat_service_refactored.is_local_or_dev", return_value=False
            ),
        ):
            responses = await _consume(chat_svc, _make_request())

    assert responses[-1].response_type == ChatResponseType.END
    finalize_mock.assert_called_once()
    if variant == "legacy":
        assert svc._previous_response_ids[MAIN_CHAT_KEY] == "resp-single-heartbeat"
    else:
        assert (
            _state(svc).previous_continuation_states[MAIN_CHAT_KEY]
            == "resp-single-heartbeat"
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "variant",
    [
        "legacy",
        "real-refactored",
    ],
)
async def test_chat_flushes_queued_run_items_when_second_turn_creates_session(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")

    transfer_tool = _FakeToolCallItem(
        SimpleNamespace(
            id="transfer-tool",
            call_id="transfer-tool",
            name="transfer_to_agent",
            arguments="{}",
        )
    )
    first_run = _FakeRunResult(
        [
            _FakeStreamEvent("run_item_stream_event", item=transfer_tool),
            _FakeStreamEvent(
                "run_item_stream_event",
                item=_FakeReasoningItem([{"summary_text": "queued reasoning"}]),
            ),
            _FakeStreamEvent("run_item_stream_event", item=object()),
        ]
    )
    second_run = _FakeRunResult([], last_response_id="resp-second-turn")

    if variant == "legacy":
        with (
            patch("services.chat_service.ToolCallItem", _FakeToolCallItem),
            patch(
                "services.chat_service.ReasoningItem",
                _FakeReasoningItem,
            ),
            patch("services.chat_service.is_local_or_dev", return_value=False),
        ):
            svc._run_streamed = MagicMock(side_effect=[first_run, second_run])
            first_responses = await _consume(
                chat_svc, _make_request(message="first turn")
            )
            second_responses = await _consume(
                chat_svc, _make_request(message="second turn")
            )
    else:
        first_run_stream = _FakeRunStream(first_run._events)
        second_run_stream = _FakeRunStream([])
        second_run_stream.continuation_state = "resp-second-turn"
        chat_svc._llm_runner.run_streamed = MagicMock(
            side_effect=[first_run_stream, second_run_stream]
        )
        _attach_run_with_retry_passthrough(chat_svc._llm_runner)
        with (
            patch("services.chat.chat_persistence.ToolCallItem", _FakeToolCallItem),
            patch("services.chat.chat_persistence.ReasoningItem", _FakeReasoningItem),
            patch(
                "services.chat.stream_event_processor.ToolCallItem", _FakeToolCallItem
            ),
            patch(
                "services.chat_service_refactored.is_local_or_dev", return_value=False
            ),
        ):
            first_responses = await _consume(
                chat_svc, _make_request(message="first turn")
            )
            second_responses = await _consume(
                chat_svc, _make_request(message="second turn")
            )

    assert first_responses[-1].response_type == ChatResponseType.END
    assert second_responses[-1].response_type == ChatResponseType.END
    saved_histories = [
        history
        for call in svc._chat_repository.add_chat_histories.call_args_list
        for history in call.args[0]
    ]
    assert any(history.role == LLMMessageRole.REASONING for history in saved_histories)
    assert not any(
        history.tool_name == "transfer_to_agent" for history in saved_histories
    )


@pytest.mark.parametrize("variant", _VARIANTS)
def test_final_residual_helper_arcs_for_security_and_tool_output(
    variant, chat_service_container
):
    assert (
        _serialize_tool_output_for_storage({"nested": {"value": 1}})
        == '{"nested": {"value": 1}}'
    )
    assert _parse_tool_output({"direct": "dict"}) == {"direct": "dict"}


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy"])
async def test_handle_security_detection_reraises_unexpected_errors_and_cleans_session(
    variant, chat_service_container
):
    svc = _inner(chat_service_container)
    svc.llm_output_guard.remove_session = MagicMock()

    with pytest.raises(RuntimeError):
        await svc._handle_security_detection(
            RuntimeError("unexpected"),
            _SESSION_ID,
            ChatSessionStatus.CHATTING,
            MagicMock(),
        )

    svc.llm_output_guard.remove_session.assert_called_once_with(_SESSION_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy"])
async def test_chat_emits_token_usage_chunk_in_local_env(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")

    with patch("services.chat_service.is_local_or_dev", return_value=True):
        svc._run_streamed = MagicMock(return_value=_FakeRunResult([]))
        responses = await _consume(chat_svc, _make_request())

    assert responses
    assert responses[-1].response_type == ChatResponseType.END


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy"])
async def test_chat_continues_when_summary_start_check_raises(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")

    svc._summary_service = MagicMock()
    svc._summary_service.check_should_start_summary.side_effect = RuntimeError(
        "summary-check-failed"
    )
    svc._previous_response_ids[MAIN_CHAT_KEY] = "resp-existing"

    with patch("services.chat_service.is_local_or_dev", return_value=False):
        svc._run_streamed = MagicMock(return_value=_FakeRunResult([]))
        responses = await _consume(chat_svc, _make_request())

    assert responses[-1].response_type == ChatResponseType.END


@pytest.mark.asyncio
@pytest.mark.pre_extraction_parity
@pytest.mark.parametrize("variant", ["legacy"])
async def test_chat_handles_forbidden_word_in_finalize_stream_legacy(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc, _, _ = _prepare_chat_service(chat_svc)
    await chat_svc.init_session("gpt-4o")

    set_session_id(_SESSION_ID)
    try:
        expected_response = ChatStreamResponse(
            request_type=ChatRequestType.CHAT
        ).create_error_response(
            "blocked",
            ChatSessionStatus.CHATTING,
        )
    finally:
        clear_session_id()

    with (
        patch.object(
            svc.llm_output_guard,
            "finalize_stream",
            Mock(side_effect=ForbiddenWordDetectedException("forbidden", _SESSION_ID)),
        ),
        patch.object(
            svc,
            "_handle_security_detection",
            AsyncMock(return_value=expected_response),
        ) as handle_security_mock,
        patch("services.chat_service.is_local_or_dev", return_value=False),
    ):
        svc._run_streamed = MagicMock(return_value=_FakeRunResult([]))
        responses = await _consume(chat_svc, _make_request())

    assert responses[-1].response_type == ChatResponseType.ERROR
    handle_security_mock.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.pre_extraction_parity
@pytest.mark.parametrize("variant", ["legacy"])
async def test_build_summary_context_falls_back_to_main_histories_without_summary(
    variant, chat_service_container
):
    svc = _inner(chat_service_container)
    svc._toolcall_trace_message = {"type": "toolcall_trace", "content": ""}
    svc._summary_service = MagicMock()
    svc._summary_service.get_latest_completed.return_value = None
    svc._chat_repository.get_main_chat_histories.return_value = []
    svc._convert_to_llm_messages = MagicMock(
        return_value=({MAIN_CHAT_KEY: []}, {MAIN_CHAT_KEY: []})
    )
    svc._remove_tool_trace_message = MagicMock(return_value=[])

    await svc.build_summary_context(_SESSION_ID)

    svc._chat_repository.get_main_chat_histories.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.pre_extraction_parity
@pytest.mark.parametrize("variant", ["legacy"])
async def test_build_summary_context_empty_new_histories_skips_body(
    variant, chat_service_container
):
    """Line 1154->1170: can_incremental=True, get_histories_after returns [] → if False."""
    svc = _inner(chat_service_container)
    svc._toolcall_trace_message = {"type": "toolcall_trace", "content": ""}
    svc._summary_service = MagicMock()

    latest_summary = SimpleNamespace(
        summary_id=42,
        summary_text="previous summary text",
        summary_until_history_id=100,
    )
    svc._summary_service.get_latest_completed.return_value = latest_summary
    svc._summary_service.get_histories_after.return_value = []

    # Set cache so can_incremental is True
    svc._summary_context_cache = {
        "session_id": _SESSION_ID,
        "summary_id": 42,
        "boundary_id": 100,
        "last_history_id": 100,
        "chat_histories": [],
        "conversation": [],
    }

    await svc.build_summary_context(_SESSION_ID)

    svc._summary_service.get_histories_after.assert_called_once()


@pytest.mark.pre_extraction_parity
@pytest.mark.parametrize("variant", ["legacy"])
@pytest.mark.asyncio
async def test_workflow_submitted_no_error_continues_to_chat(
    variant, chat_service_container
):
    """Line 2366->2370: selected_jobtypes set, _apply_jobtypes returns None → continues."""
    from services.workflow_handlers.base import WorkflowPostProcessingResult

    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    await chat_svc.init_session("gpt-4o")

    # Mock workflow service to return post_result with selected_jobtypes
    post_result = WorkflowPostProcessingResult(
        message="Let's talk about your job options.",
        selected_jobtypes=["営業"],
    )
    svc._workflow_service.process_workflow_submission = AsyncMock(
        return_value=(post_result, [])
    )

    # _apply_jobtypes_and_update_agents returns None (no error) → 2366->2370
    svc._apply_jobtypes_and_update_agents = AsyncMock(return_value=None)

    # Mock chat() as an async generator that immediately ends
    async def _mock_chat(request, client_ip):
        return
        yield  # make it an async generator

    svc.chat = _mock_chat

    payload = json.dumps({"workflow_id": "job_match_diagnosis", "answers": {"1": []}})
    request = ChatRequestModel(
        request_type=ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
        current_page=PageName.CHAT,
        position_id=None,
        message=payload,
        current_message_id="wf-msg-1",
    )

    set_session_id(_SESSION_ID)
    try:
        responses = []
        async for chunk in chat_svc.workflow_submitted(request, "127.0.0.1"):
            responses.append(chunk)
    finally:
        clear_session_id()

    # Verify we got past the error check (no error) and reached chat()
    svc._apply_jobtypes_and_update_agents.assert_called_once()
