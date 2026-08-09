from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from .chat_service_contract_helpers import (
    _FakeRunStream,
    _get_chat_histories,
    _get_position_id,
    _get_provider,
    _inner,
    _set_chat_histories,
    _set_position_id,
    _set_provider,
    _state,
)
from domain.entities.chat_session import ChatSessionStatus
from services.chat.chat_persistence import _serialize_tool_output_for_storage
from services.chat.llm_runner import LLMRawResponseEvent
from services.chat_service_refactored import json_default
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType
from utils.const import MAIN_CHAT_KEY
from utils.enum import LLMMessageRole, PageName
from utils.log_utils import clear_session_id, set_session_id


pytestmark = pytest.mark.pre_extraction_parity

_SESSION_ID = "test-session-refactored-residuals"


def _make_request(**overrides) -> ChatRequestModel:
    payload = {
        "request_type": ChatRequestType.CHAT,
        "current_page": PageName.CHAT,
        "position_id": None,
        "message": "hello",
        "current_message_id": "msg-refactored-residuals",
    }
    payload.update(overrides)
    return ChatRequestModel(**payload)


async def _consume(chat_svc, request):
    responses = []
    set_session_id(_SESSION_ID)
    try:
        async for response in chat_svc.chat(request, "127.0.0.1"):
            responses.append(response.model_copy(deep=True))
    finally:
        clear_session_id()
    return responses


async def _init_refactored(chat_svc):
    svc = _inner(chat_svc)
    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    await chat_svc.init_session("gpt-4o")
    return svc


def test_refactored_json_default(tmp_path):
    assert json_default(object()).startswith("<object object")


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["real-refactored"])
async def test_refactored_backcompat_setters_and_helpers(
    variant, chat_service_container
):
    svc = await _init_refactored(chat_service_container)

    _set_chat_histories(svc, {MAIN_CHAT_KEY: []})
    _set_position_id(svc, None)
    assert _get_position_id(svc) is None
    _set_provider(svc, None)
    _set_provider(svc, "gpt-4o")

    assert _serialize_tool_output_for_storage("raw-output") == "raw-output"
    svc._create_position_agent_if_not_exist(None)

    svc._agents = {}
    svc._create_position_agent_if_not_exist("123")
    assert "123" not in svc._agents

    with pytest.raises(Exception, match="Agent not found"):
        svc._get_agent("missing")


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["real-refactored"])
async def test_refactored_chat_handles_summary_context_failure_and_missing_conversation_key(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = await _init_refactored(chat_svc)

    run_stream = _FakeRunStream([])
    run_stream.usage = None
    chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)

    svc._summary_service = MagicMock()
    with (
        patch.object(
            svc, "_build_summary_context", AsyncMock(side_effect=RuntimeError("boom"))
        ),
        patch("services.chat_service_refactored.is_local_or_dev", return_value=False),
    ):
        responses = await _consume(chat_svc, _make_request())
    assert responses[-1].response_type == ChatResponseType.END

    svc._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    svc._conv_state.previous_continuation_states[MAIN_CHAT_KEY] = "resp-existing"
    svc._conv_state.conversation = {}
    with patch("services.chat_service_refactored.is_local_or_dev", return_value=False):
        responses = await _consume(chat_svc, _make_request())
    assert responses[-1].response_type == ChatResponseType.END


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["real-refactored"])
async def test_refactored_chat_agent_resolution_and_finalize_residual_paths(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = await _init_refactored(chat_svc)
    svc._conv_state.active_agent_name = "missing-agent"

    with patch("services.chat_service_refactored.is_local_or_dev", return_value=False):
        responses = await _consume(chat_svc, _make_request())
    assert responses[-1].response_type == ChatResponseType.ERROR

    svc._last_init_session_failed = True
    with patch("services.chat_service_refactored.is_local_or_dev", return_value=False):
        responses = await _consume(chat_svc, _make_request())
    assert responses[-1].response_type == ChatResponseType.END

    # Finalize yields error chunk path (_finalize_security_stopped=True)
    svc = await _init_refactored(chat_svc)
    run_stream = _FakeRunStream([LLMRawResponseEvent("msg", "ok")])
    run_stream.usage = None
    chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)

    class _FakeGuard:
        def __init__(self, *args, **kwargs):
            self.security_detected = False

        async def finalize(self, chat_response, session_status):
            yield chat_response.create_error_response("blocked", session_status)

        def cleanup(self):
            return None

    with (
        patch("services.chat_service_refactored.StreamGuard", _FakeGuard),
        patch("services.chat_service_refactored.is_local_or_dev", return_value=False),
    ):
        responses = await _consume(chat_svc, _make_request())
    assert responses[-1].response_type == ChatResponseType.ERROR


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["real-refactored"])
async def test_refactored_chat_finalize_usage_and_summary_exception_paths(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = await _init_refactored(chat_svc)

    # Finalize exception path should be non-fatal.
    run_stream = _FakeRunStream([])
    run_stream.usage = None
    chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)

    class _ExplodingFinalizeGuard:
        def __init__(self, *args, **kwargs):
            self.security_detected = False

        def reset(self):
            return None

        async def process_chunk(self, *_args, **_kwargs):
            if False:
                yield None

        async def finalize(self, *_args, **_kwargs):
            raise RuntimeError("finalize-failed")
            yield  # pragma: no cover

        def cleanup(self):
            return None

    with (
        patch("services.chat_service_refactored.StreamGuard", _ExplodingFinalizeGuard),
        patch("services.chat_service_refactored.is_local_or_dev", return_value=False),
    ):
        responses = await _consume(chat_svc, _make_request())
    assert responses[-1].response_type == ChatResponseType.END

    # Token usage local response path.
    run_stream = _FakeRunStream([])
    run_stream.usage = {"input_tokens": 1}
    chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)
    with patch("services.chat_service_refactored.is_local_or_dev", return_value=True):
        responses = await _consume(chat_svc, _make_request())
    assert any("Token Usage" in r.message for r in responses)

    # Usage logging failure is handled in runner and should remain non-fatal.
    run_stream = _FakeRunStream([])
    run_stream.usage = {"input_tokens": 1}
    chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)
    svc._action_log_repository.insert.side_effect = RuntimeError("usage-failed")
    with patch("services.chat_service_refactored.is_local_or_dev", return_value=False):
        responses = await _consume(chat_svc, _make_request())
    assert responses[-1].response_type == ChatResponseType.END
    svc._action_log_repository.insert.side_effect = None

    # Summary start check failure is logged and chat still ends.
    run_stream = _FakeRunStream([])
    run_stream.usage = None
    chat_svc._llm_runner.run_streamed = MagicMock(return_value=run_stream)
    svc._summary_service = MagicMock()
    svc._summary_service.check_should_start_summary.side_effect = RuntimeError("boom")
    with patch("services.chat_service_refactored.is_local_or_dev", return_value=False):
        responses = await _consume(chat_svc, _make_request())
    assert responses[-1].response_type == ChatResponseType.END


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["real-refactored"])
async def test_refactored_stop_at_output_and_summary_helper_residuals(
    variant, chat_service_container
):
    svc = _inner(chat_service_container)

    # _append_stop_at_tool_outputs_callback: call_id non-string is skipped.
    handler = MagicMock()
    handler.build_stop_at_tool_outputs.return_value = [
        {"type": "function_call_output", "call_id": 1}
    ]
    svc._current_tool_event_handler = handler
    svc._conv_state.chat_key = MAIN_CHAT_KEY
    svc._conv_state.conversation = {MAIN_CHAT_KEY: []}
    svc._append_stop_at_tool_outputs_callback([], True)
    assert svc._conv_state.conversation[MAIN_CHAT_KEY] == []

    # _append_stop_at_tool_outputs direct path.
    svc._append_stop_at_tool_outputs([], False)
    svc._append_stop_at_tool_outputs(
        [
            {"type": "ignored", "call_id": "a"},
            {"type": "function_call_output", "call_id": 2},
            {"type": "function_call_output", "call_id": "ok"},
            {"type": "function_call_output", "call_id": "ok"},
        ],
        True,
    )
    assert svc._conv_state.conversation[MAIN_CHAT_KEY][-1]["call_id"] == "ok"

    # _build_summary_context invalid boundary + summary insertion path.
    svc._summary_service = MagicMock()
    svc._summary_service.get_latest_completed.return_value = SimpleNamespace(
        summary_until_history_id="not-int",
        summary_text="summary-text",
    )
    svc._summary_service.get_histories_after.return_value = []
    svc._history_mapper.convert_to_llm_messages = MagicMock(
        return_value=({MAIN_CHAT_KEY: []}, {MAIN_CHAT_KEY: []})
    )
    svc._toolcall_trace_message = {"type": "message", "content": "trace"}
    svc._conv_state.chat_key = MAIN_CHAT_KEY
    await svc._build_summary_context(_SESSION_ID)
    assert any(
        isinstance(item, dict)
        and item.get("role") == LLMMessageRole.DEVELOPER
        and "###過去会話の要約" in item.get("content", "")
        for item in svc._conv_state.conversation[MAIN_CHAT_KEY]
    )

    # _remove_tool_trace_message residual branches.
    messages = [
        {"type": "message", "role": LLMMessageRole.DEVELOPER, "content": "trace"}
    ]
    svc._toolcall_trace_message = None
    assert svc._remove_tool_trace_message(messages) == messages

    svc._toolcall_trace_message = {}
    assert svc._remove_tool_trace_message(messages) == messages

    svc._toolcall_trace_message = {"content": "trace"}
    assert svc._remove_tool_trace_message(messages) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["real-refactored"])
async def test_refactored_build_summary_context_falls_back_to_main_histories(
    variant, chat_service_container
):
    svc = _inner(chat_service_container)
    svc._summary_service = MagicMock()
    svc._summary_service.get_latest_completed.return_value = None
    svc._chat_repository.get_main_chat_histories.return_value = []
    svc._history_mapper.convert_to_llm_messages = MagicMock(
        return_value=({MAIN_CHAT_KEY: []}, {MAIN_CHAT_KEY: []})
    )
    svc._toolcall_trace_message = None
    svc._conv_state.chat_key = MAIN_CHAT_KEY

    await svc._build_summary_context(_SESSION_ID)

    svc._chat_repository.get_main_chat_histories.assert_called_once()


# ─── chat_service_refactored.py:978 ──────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["real-refactored"])
async def test_refactored_build_summary_context_returns_early_when_no_summary_service(
    variant, chat_service_container
):
    """Line 978: _summary_service is None → early return."""
    svc = _inner(chat_service_container)
    svc._summary_service = None
    svc._conv_state.chat_key = MAIN_CHAT_KEY
    await svc._build_summary_context(_SESSION_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["real-refactored"])
async def test_refactored_build_summary_context_returns_early_when_not_main_chat(
    variant, chat_service_container
):
    """Line 977->978: chat_key != MAIN_CHAT_KEY → early return."""
    svc = _inner(chat_service_container)
    svc._summary_service = MagicMock()
    svc._conv_state.chat_key = "position-chat"
    await svc._build_summary_context(_SESSION_ID)
    svc._summary_service.get_latest_completed.assert_not_called()


# ─── chat_service_refactored.py:823-825, 832 ─────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["real-refactored"])
async def test_refactored_chat_finalize_yields_error_chunk_stops_early(
    variant, chat_service_container
):
    """Lines 823-825, 832: stream_guard.finalize() yields ERROR chunk → early return."""
    from utils.chat_response import ChatStreamResponse

    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    await chat_svc.init_session("gpt-4o")
    svc._llm_runner.run_streamed.return_value = _FakeRunStream([])

    class _FinalizeSecurity:
        def __init__(self, *_a, **_kw):
            self.security_detected = False

        def reset(self):
            pass

        async def finalize(self, *_a, **_kw):
            yield ChatStreamResponse(
                request_type=ChatRequestType.CHAT,
                position_id=None,
            ).create_error_response("blocked", ChatSessionStatus.CHATTING)

        def cleanup(self):
            pass

    set_session_id(_SESSION_ID)
    try:
        with patch("services.chat_service_refactored.StreamGuard", _FinalizeSecurity):
            responses = []
            async for r in chat_svc.chat(
                ChatRequestModel(
                    request_type=ChatRequestType.CHAT,
                    current_page=PageName.CHAT,
                    position_id=None,
                    message="hello",
                    current_message_id="msg-fin-sec",
                ),
                "127.0.0.1",
            ):
                responses.append(r.model_copy(deep=True))
    finally:
        clear_session_id()

    assert any(r.response_type == ChatResponseType.ERROR for r in responses)
    assert not any(r.response_type == ChatResponseType.END for r in responses)


# ─── chat_service.py:1132, 2182->2181 ────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy"])
async def test_legacy_build_summary_context_returns_early_when_no_summary_service(
    variant, chat_service_container
):
    """Line 1132: legacy build_summary_context with _summary_service=None → early return."""
    svc = _inner(chat_service_container)
    svc._summary_service = None
    svc._chat_key = MAIN_CHAT_KEY
    await svc.build_summary_context(_SESSION_ID)


@pytest.mark.parametrize("variant", ["legacy"])
def test_legacy_find_last_non_position_guide_skips_position_guide_entries(
    variant, chat_service_container
):
    """Arc 2182->2181: loop continues when active_agent is POSITION_GUIDE."""
    from domain.entities.chat_history import ChatHistory
    from services.llm_service import AgentName

    svc = _inner(chat_service_container)
    guide_hist = MagicMock(spec=ChatHistory)
    guide_hist.active_agent = AgentName.POSITION_GUIDE
    default_hist = MagicMock(spec=ChatHistory)
    default_hist.active_agent = "CareerAdvisor"
    _get_chat_histories(svc)[MAIN_CHAT_KEY] = [default_hist, guide_hist]
    result = svc._find_last_non_position_guide_agent()
    assert result == "CareerAdvisor"
