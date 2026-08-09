"""Unit tests for StreamEventProcessor — 100% branch coverage required.

Branch inventory
----------------
process() — event loop:
  SEP-RAW-DELTA   event.type == "raw_response_event" AND event.delta truthy
                  → yield agent_message_response, continue
  SEP-RAW-NODELTA event.type == "raw_response_event" AND event.delta falsy
                  → skip yield, fall through to second-if → continue
  SEP-OTHER       event.type is not "raw_response_event" and not "run_item_stream_event"
                  → continue via second-if
  SEP-RUNITEM     event.type == "run_item_stream_event"
                  → save_chat_history + is_stop_at_tool check
  SEP-STOP-TRUE   is_stop_at_tool returns True → stop_at_tool_exists = True
  SEP-STOP-FALSE  is_stop_at_tool returns False → no change
  SEP-TOOL-CALL   run_item_stream_event, event.item is ToolCallItem, tool_event_handler not None
                  → handle_tool_call() called
  SEP-TOOL-OUTPUT run_item_stream_event, event.item is ToolCallOutputItem, tool_event_handler not None
                  → chunks yielded from handle_tool_output()

process() — exception handling:
  SEP-CANCELLED   asyncio.CancelledError raised during stream_events()
                  → _cancelled = True, re-raise, aclose() NOT called

process() — finally block:
  SEP-CONT-YES    run_stream.continuation_state is not None (including falsy non-None values like "") → update_continuation_state called
  SEP-CONT-NO     run_stream.continuation_state is None → update_continuation_state not called
  SEP-AGENT-NONE  run_stream.agent_state is None → update_active_agent not called
  SEP-AGENT-NAME  run_stream.agent_state not None and has .name → update_active_agent called
  SEP-AGENT-NONAME run_stream.agent_state not None but no .name attr → update_active_agent not called
  SEP-CLOSE-ERR   run_stream.aclose() raises → exception suppressed, no yield
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


pytestmark = pytest.mark.pre_extraction_parity
from domain.entities.chat_session import ChatSessionStatus
from services.chat.chat_persistence import ChatPersistence
from services.chat.stream_event_processor import StreamEventProcessor
from utils.chat_response import ChatResponseType, ChatStreamResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_raw_event(item_id: str = "item-1", delta: str = "hello") -> SimpleNamespace:
    return SimpleNamespace(type="raw_response_event", item_id=item_id, delta=delta)


def _make_run_item_event(item: object = None) -> SimpleNamespace:
    return SimpleNamespace(type="run_item_stream_event", item=item or SimpleNamespace())


def _make_other_event(event_type: str = "unknown_event") -> SimpleNamespace:
    return SimpleNamespace(type=event_type, item_id="x", delta="x")


async def _async_gen(*events):
    for event in events:
        yield event


def _make_stream(
    events=(),
    continuation_state=None,
    agent_state=None,
    replay_items=None,
    usage=None,
    aclose_raises=False,
):
    """Build a mock LLMRunStream."""
    stream = MagicMock()
    stream.stream_events = MagicMock(return_value=_async_gen(*events))
    stream.continuation_state = continuation_state
    stream.agent_state = agent_state
    stream.replay_items = [] if replay_items is None else replay_items
    stream.usage = usage

    if aclose_raises:
        stream.aclose = AsyncMock(side_effect=RuntimeError("close error"))
    else:
        stream.aclose = AsyncMock()

    return stream


def _make_cancelling_stream(
    continuation_state=None,
    agent_state=None,
    replay_items=None,
):
    """Build a mock LLMRunStream whose stream_events() raises asyncio.CancelledError."""

    async def _raise_cancelled():
        if False:  # make it an async generator
            yield None
        raise asyncio.CancelledError()

    stream = MagicMock()
    stream.stream_events = MagicMock(return_value=_raise_cancelled())
    stream.continuation_state = continuation_state
    stream.agent_state = agent_state
    stream.replay_items = [] if replay_items is None else replay_items
    stream.aclose = AsyncMock()
    return stream


def _make_processor(
    *,
    is_stop_at_tool_result: bool = False,
) -> tuple[StreamEventProcessor, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock]:
    chat_persistence = MagicMock(spec=ChatPersistence)
    is_stop_at_tool = MagicMock(return_value=is_stop_at_tool_result)
    append_stop_at_tool_outputs = MagicMock()
    update_active_agent = MagicMock()
    update_continuation_state = MagicMock()

    processor = StreamEventProcessor(
        chat_persistence=chat_persistence,
        is_stop_at_tool=is_stop_at_tool,
        append_stop_at_tool_outputs=append_stop_at_tool_outputs,
        update_active_agent=update_active_agent,
        update_continuation_state=update_continuation_state,
    )
    return (
        processor,
        chat_persistence,
        is_stop_at_tool,
        append_stop_at_tool_outputs,
        update_active_agent,
        update_continuation_state,
    )


def _make_chat_response() -> MagicMock:
    """Return a mock ChatStreamResponse that returns a sentinel for each factory method."""
    mock = MagicMock(spec=ChatStreamResponse)
    mock.create_agent_message_response.side_effect = (
        lambda item_id, delta, status: SimpleNamespace(
            type="agent_message", item_id=item_id, delta=delta
        )
    )
    return mock


def _make_noop_tool_event_handler() -> SimpleNamespace:
    async def _handle_tool_call(_item, _client_ip):
        return None

    async def _handle_tool_output(_item, _chat_response, _session_status):
        if False:
            yield None

    return SimpleNamespace(
        handle_tool_call=_handle_tool_call,
        handle_tool_output=_handle_tool_output,
        consume_session_status_update=lambda: None,
    )


async def _collect(processor, stream, chat_response=None, session_status=None):
    if chat_response is None:
        chat_response = _make_chat_response()
    if session_status is None:
        session_status = ChatSessionStatus.CHATTING
    results = []
    async for chunk in processor.process(
        stream,
        chat_response,
        session_status,
        tool_event_handler=_make_noop_tool_event_handler(),
    ):
        results.append(chunk)
    return results


# ---------------------------------------------------------------------------
# SEP-RAW-DELTA: raw_response_event with truthy delta → yield
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_raw_event_with_delta_yields_agent_message():
    """SEP-RAW-DELTA: raw_response_event with delta → agent_message_response yielded."""
    processor, persistence, is_stop, append_out, upd_agent, upd_cont = _make_processor()
    event = _make_raw_event(item_id="item-1", delta="hello")
    stream = _make_stream(events=[event])

    results = await _collect(processor, stream)

    assert len(results) == 1
    persistence.save_chat_history.assert_not_called()
    is_stop.assert_not_called()


@pytest.mark.asyncio
async def test_raw_event_with_delta_does_not_call_save_chat_history():
    """SEP-RAW-DELTA: raw_response_event processing does not call save_chat_history."""
    processor, persistence, *_ = _make_processor()
    stream = _make_stream(events=[_make_raw_event(delta="data")])
    await _collect(processor, stream)
    persistence.save_chat_history.assert_not_called()


# ---------------------------------------------------------------------------
# SEP-RAW-NODELTA: raw_response_event with falsy delta → no yield
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_raw_event_empty_delta_yields_nothing():
    """SEP-RAW-NODELTA: raw_response_event with empty delta → no yield."""
    processor, persistence, is_stop, *_ = _make_processor()
    event = _make_raw_event(delta="")
    stream = _make_stream(events=[event])

    results = await _collect(processor, stream)

    assert len(results) == 0
    persistence.save_chat_history.assert_not_called()
    is_stop.assert_not_called()


@pytest.mark.asyncio
async def test_raw_event_none_delta_yields_nothing():
    """SEP-RAW-NODELTA: raw_response_event with None delta → no yield."""
    processor, *_ = _make_processor()
    event = SimpleNamespace(type="raw_response_event", item_id="x", delta=None)
    stream = _make_stream(events=[event])

    results = await _collect(processor, stream)

    assert len(results) == 0


# ---------------------------------------------------------------------------
# SEP-OTHER: unrecognised event type → continue
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_event_type_is_skipped():
    """SEP-OTHER: event with unknown type → no yield, no save."""
    processor, persistence, is_stop, *_ = _make_processor()
    stream = _make_stream(events=[_make_other_event("agent_updated")])

    results = await _collect(processor, stream)

    assert len(results) == 0
    persistence.save_chat_history.assert_not_called()
    is_stop.assert_not_called()


# ---------------------------------------------------------------------------
# SEP-RUNITEM: run_item_stream_event → save_chat_history + is_stop_at_tool
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_item_event_calls_save_chat_history():
    """SEP-RUNITEM: run_item_stream_event → save_chat_history called."""
    processor, persistence, is_stop, *_ = _make_processor()
    item = SimpleNamespace(name="tool_call")
    stream = _make_stream(events=[_make_run_item_event(item=item)])

    await _collect(processor, stream)

    persistence.save_chat_history.assert_called_once_with(item)
    is_stop.assert_called_once_with(item)


@pytest.mark.asyncio
async def test_run_item_event_yields_nothing():
    """SEP-RUNITEM: run_item_stream_event does not yield any response."""
    processor, *_ = _make_processor()
    stream = _make_stream(events=[_make_run_item_event()])

    results = await _collect(processor, stream)

    assert len(results) == 0


# ---------------------------------------------------------------------------
# SEP-STOP-TRUE: is_stop_at_tool returns True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stop_at_tool_true_passes_true_to_append_callback():
    """SEP-STOP-TRUE: is_stop_at_tool True → append_stop_at_tool_outputs called with True."""
    processor, _, _, append_out, *_ = _make_processor(is_stop_at_tool_result=True)
    stream = _make_stream(events=[_make_run_item_event()])

    await _collect(processor, stream)

    append_out.assert_called_once()
    _, stop_flag = append_out.call_args[0]
    assert stop_flag is True


# ---------------------------------------------------------------------------
# SEP-STOP-FALSE: is_stop_at_tool returns False
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stop_at_tool_false_passes_false_to_append_callback():
    """SEP-STOP-FALSE: is_stop_at_tool False → append_stop_at_tool_outputs called with False."""
    processor, _, _, append_out, *_ = _make_processor(is_stop_at_tool_result=False)
    stream = _make_stream(events=[_make_run_item_event()])

    await _collect(processor, stream)

    append_out.assert_called_once()
    _, stop_flag = append_out.call_args[0]
    assert stop_flag is False


@pytest.mark.asyncio
async def test_stop_at_tool_no_events_passes_false_to_append_callback():
    """SEP-STOP-FALSE: no events → stop_at_tool_exists starts False → append called with False."""
    processor, _, _, append_out, *_ = _make_processor()
    stream = _make_stream(events=[])

    await _collect(processor, stream)

    append_out.assert_called_once()
    _, stop_flag = append_out.call_args[0]
    assert stop_flag is False


# ---------------------------------------------------------------------------
# SEP-CONT-YES: continuation_state is not None → update_continuation_state called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_continuation_state_truthy_calls_update():
    """SEP-CONT-YES: continuation_state is not None → update_continuation_state called with value."""
    processor, _, _, _, _, upd_cont = _make_processor()
    stream = _make_stream(continuation_state="resp-id-42")

    await _collect(processor, stream)

    upd_cont.assert_called_once_with("resp-id-42")


# ---------------------------------------------------------------------------
# SEP-CONT-NO: continuation_state is None → update_continuation_state not called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_continuation_state_falsy_skips_update():
    """SEP-CONT-NO: continuation_state is None → update_continuation_state not called."""
    processor, _, _, _, _, upd_cont = _make_processor()
    stream = _make_stream(continuation_state=None)

    await _collect(processor, stream)

    upd_cont.assert_not_called()


@pytest.mark.asyncio
async def test_continuation_state_empty_string_calls_update():
    """SEP-CONT-YES: continuation_state empty string is not None → update_continuation_state called."""
    processor, _, _, _, _, upd_cont = _make_processor()
    stream = _make_stream(continuation_state="")

    await _collect(processor, stream)

    upd_cont.assert_called_once_with("")


# ---------------------------------------------------------------------------
# SEP-AGENT-NONE: agent_state is None → update_active_agent not called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_state_none_skips_update_active_agent():
    """SEP-AGENT-NONE: agent_state None → update_active_agent not called."""
    processor, _, _, _, upd_agent, _ = _make_processor()
    stream = _make_stream(agent_state=None)

    await _collect(processor, stream)

    upd_agent.assert_not_called()


# ---------------------------------------------------------------------------
# SEP-AGENT-NAME: agent_state not None and has .name → update_active_agent called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_state_with_name_calls_update_active_agent():
    """SEP-AGENT-NAME: agent_state with .name → update_active_agent called with name."""
    processor, _, _, _, upd_agent, _ = _make_processor()
    agent = SimpleNamespace(name="WorkflowAgent")
    stream = _make_stream(agent_state=agent)

    await _collect(processor, stream)

    upd_agent.assert_called_once_with("WorkflowAgent")


# ---------------------------------------------------------------------------
# SEP-AGENT-NONAME: agent_state not None but no .name → update_active_agent not called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_state_without_name_skips_update_active_agent():
    """SEP-AGENT-NONAME: agent_state without .name attr → update_active_agent not called."""
    processor, _, _, _, upd_agent, _ = _make_processor()
    # object() has no 'name' attribute
    stream = _make_stream(agent_state=object())

    await _collect(processor, stream)

    upd_agent.assert_not_called()


# ---------------------------------------------------------------------------
# SEP-CLOSE-ERR: aclose() raises → exception suppressed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aclose_exception_is_suppressed():
    """SEP-CLOSE-ERR: aclose() raises RuntimeError → suppressed, no propagation."""
    processor, *_ = _make_processor()
    stream = _make_stream(aclose_raises=True)

    # Should not raise
    results = await _collect(processor, stream)

    # Normal completion, just no events
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_aclose_always_called_even_on_exception():
    """SEP-CLOSE-ERR: aclose() is always attempted, even when other processing raises."""
    processor, persistence, *_ = _make_processor()
    persistence.save_chat_history.side_effect = RuntimeError("db error")
    stream = _make_stream(events=[_make_run_item_event()], aclose_raises=True)

    with pytest.raises(RuntimeError, match="db error"):
        await _collect(processor, stream)

    stream.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_aclose_called_when_stream_guard_reset_raises():
    """SEP-CLOSE-ERR: reset() failure still triggers run_stream.aclose() via finally."""
    processor, *_ = _make_processor()
    stream = _make_stream()
    chat_response = _make_chat_response()
    stream_guard = MagicMock()
    stream_guard.reset.side_effect = RuntimeError("reset error")

    with pytest.raises(RuntimeError, match="reset error"):
        async for _ in processor.process(
            stream,
            chat_response,
            ChatSessionStatus.CHATTING,
            tool_event_handler=_make_noop_tool_event_handler(),
            stream_guard=stream_guard,
        ):
            pass

    stream.aclose.assert_called_once()


# ---------------------------------------------------------------------------
# SEP-CANCELLED: asyncio.CancelledError → re-raised, aclose() NOT called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancelled_error_propagates():
    """SEP-CANCELLED: CancelledError from stream_events() propagates out of process()."""
    processor, *_ = _make_processor()
    stream = _make_cancelling_stream()

    with pytest.raises(asyncio.CancelledError):
        await _collect(processor, stream)


@pytest.mark.asyncio
async def test_cancelled_error_does_not_call_aclose():
    """SEP-CANCELLED: CancelledError → aclose() must NOT be called (avoids double-close)."""
    processor, *_ = _make_processor()
    stream = _make_cancelling_stream()

    with pytest.raises(asyncio.CancelledError):
        await _collect(processor, stream)

    stream.aclose.assert_not_called()


@pytest.mark.asyncio
async def test_cancelled_error_still_runs_state_callbacks():
    """SEP-CANCELLED: CancelledError → finally block still runs; state callbacks are invoked."""
    processor, _, _, append_out, upd_agent, upd_cont = _make_processor()
    agent = SimpleNamespace(name="CancelAgent")
    stream = _make_cancelling_stream(
        continuation_state="resp-cancel",
        agent_state=agent,
    )

    with pytest.raises(asyncio.CancelledError):
        await _collect(processor, stream)

    upd_cont.assert_called_once_with("resp-cancel")
    upd_agent.assert_called_once_with("CancelAgent")
    append_out.assert_called_once()


# ---------------------------------------------------------------------------
# Integration: mixed event sequence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mixed_events_processed_in_order():
    """Integration: raw + run_item + unknown events all processed correctly."""
    processor, persistence, is_stop, append_out, upd_agent, upd_cont = _make_processor(
        is_stop_at_tool_result=False
    )
    item1 = SimpleNamespace(name="item1")
    item2 = SimpleNamespace(name="item2")
    events = [
        _make_raw_event(item_id="r1", delta="Hello"),
        _make_run_item_event(item=item1),
        _make_other_event("agent_updated"),
        _make_raw_event(item_id="r2", delta=" world"),
        _make_run_item_event(item=item2),
    ]
    agent_state = SimpleNamespace(name="FinalAgent")
    stream = _make_stream(
        events=events,
        continuation_state="resp-99",
        agent_state=agent_state,
    )

    results = await _collect(processor, stream)

    # Different raw item_id values are filtered to keep only the first stream.
    assert len(results) == 1
    # Two run_item events → two save_chat_history calls
    assert persistence.save_chat_history.call_count == 2
    # is_stop_at_tool called for both run_item events
    assert is_stop.call_count == 2
    # continuation_state was truthy
    upd_cont.assert_called_once_with("resp-99")
    # agent_state had .name
    upd_agent.assert_called_once_with("FinalAgent")
    # append called with False (no stop_at_tool)
    append_out.assert_called_once()
    _, stop_flag = append_out.call_args[0]
    assert stop_flag is False


@pytest.mark.asyncio
async def test_raw_events_ignore_second_item_id_when_stream_guard_is_used():
    """Only the first raw message item_id is processed to avoid mixed guard buffers."""
    processor, *_ = _make_processor()
    chat_response = _make_chat_response()
    stream_guard = MagicMock()

    async def _guard_chunks(item_id, delta, _chat_response, _session_status):
        yield SimpleNamespace(response_type="agent")

    stream_guard.process_chunk.side_effect = _guard_chunks
    events = [
        _make_raw_event(item_id="msg-1", delta="hello"),
        _make_raw_event(item_id="msg-2", delta="drop-me"),
        _make_raw_event(item_id="msg-1", delta=" world"),
    ]
    stream = _make_stream(events=events)

    results = []
    async for chunk in processor.process(
        stream,
        chat_response,
        ChatSessionStatus.CHATTING,
        tool_event_handler=_make_noop_tool_event_handler(),
        stream_guard=stream_guard,
    ):
        results.append(chunk)

    assert len(results) == 2
    assert stream_guard.process_chunk.call_count == 2
    first_call = stream_guard.process_chunk.call_args_list[0]
    second_call = stream_guard.process_chunk.call_args_list[1]
    assert first_call.args[0] == "msg-1"
    assert second_call.args[0] == "msg-1"


@pytest.mark.asyncio
async def test_raw_event_without_stream_guard_uses_chat_response_factory():
    """Raw delta without stream_guard should directly yield create_agent_message_response output."""
    processor, *_ = _make_processor()
    chat_response = _make_chat_response()
    stream = _make_stream(events=[_make_raw_event(item_id="msg-plain", delta="hello")])

    results = []
    async for chunk in processor.process(
        stream,
        chat_response,
        ChatSessionStatus.CHATTING,
        tool_event_handler=_make_noop_tool_event_handler(),
        stream_guard=None,
    ):
        results.append(chunk)

    assert len(results) == 1
    assert results[0].item_id == "msg-plain"
    chat_response.create_agent_message_response.assert_called_once()


@pytest.mark.asyncio
async def test_stream_guard_error_chunk_stops_following_raw_chunks():
    """When stream_guard emits an ERROR chunk, processing should stop immediately."""
    processor, *_ = _make_processor()
    chat_response = _make_chat_response()
    stream_guard = MagicMock()

    async def _guard_chunks(item_id, delta, _chat_response, _session_status):
        err = SimpleNamespace(response_type=ChatResponseType.ERROR, message="blocked")
        yield err

    stream_guard.process_chunk.side_effect = _guard_chunks
    stream = _make_stream(
        events=[
            _make_raw_event(item_id="msg-1", delta="first"),
            _make_raw_event(item_id="msg-1", delta="second"),
        ]
    )

    results = []
    async for chunk in processor.process(
        stream,
        chat_response,
        ChatSessionStatus.CHATTING,
        tool_event_handler=_make_noop_tool_event_handler(),
        stream_guard=stream_guard,
    ):
        results.append(chunk)

    assert len(results) == 1
    assert results[0].response_type == ChatResponseType.ERROR
    assert stream_guard.process_chunk.call_count == 1


@pytest.mark.asyncio
async def test_stop_at_tool_true_once_remains_true_for_subsequent_false():
    """Once stop_at_tool_exists is True, it stays True even if later items return False."""
    call_count = 0

    def alternating_stop(item):
        nonlocal call_count
        call_count += 1
        return call_count == 1  # True for first item only

    chat_persistence = MagicMock(spec=ChatPersistence)
    append_out = MagicMock()
    processor = StreamEventProcessor(
        chat_persistence=chat_persistence,
        is_stop_at_tool=alternating_stop,
        append_stop_at_tool_outputs=append_out,
        update_active_agent=MagicMock(),
        update_continuation_state=MagicMock(),
    )
    stream = _make_stream(events=[_make_run_item_event(), _make_run_item_event()])

    await _collect(processor, stream)

    append_out.assert_called_once()
    _, stop_flag = append_out.call_args[0]
    assert stop_flag is True


# ---------------------------------------------------------------------------
# append_stop_at_tool_outputs called with correct replay_items
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_append_stop_at_tool_outputs_receives_replay_items():
    """append_stop_at_tool_outputs is called with replay_items from run_stream."""
    processor, _, _, append_out, *_ = _make_processor()
    replay_items = [{"type": "function_call_output", "call_id": "c1"}]
    stream = _make_stream(replay_items=replay_items)

    await _collect(processor, stream)

    append_out.assert_called_once()
    items_arg, _ = append_out.call_args[0]
    assert items_arg is replay_items


@pytest.mark.asyncio
async def test_append_stop_at_tool_outputs_passes_full_replay_items_when_stop_at_true():
    """Legacy parity: stop-at-tool True should pass full replay_items to append callback."""
    processor, _, _, append_out, *_ = _make_processor()
    processor._is_stop_at_tool = MagicMock(return_value=True)

    replay_items = [
        {"type": "function_call_output", "call_id": "stop-1", "output": "a"},
        {"type": "function_call_output", "call_id": "other-1", "output": "b"},
    ]
    stream = _make_stream(
        events=[_make_run_item_event(item=SimpleNamespace())],
        replay_items=replay_items,
    )

    await _collect(processor, stream)

    append_out.assert_called_once()
    items_arg, stop_flag = append_out.call_args[0]
    assert stop_flag is True
    assert items_arg is replay_items


# ---------------------------------------------------------------------------
# Empty stream → finally block runs, aclose called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_stream_runs_finally_block():
    """Empty event stream → finally block still runs, aclose called."""
    processor, _, _, _, _, _ = _make_processor()
    stream = _make_stream(events=[])

    await _collect(processor, stream)

    stream.aclose.assert_called_once()


# ---------------------------------------------------------------------------
# SEP-TOOL-CALL / SEP-TOOL-OUTPUT: tool_event_handler dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tool_call_item_dispatches_to_handler():
    """SEP-TOOL-CALL: run_item_stream_event whose item is ToolCallItem → handle_tool_call() called."""
    from agents import ToolCallItem

    processor, chat_persistence, *_ = _make_processor()
    tool_item = MagicMock(spec=ToolCallItem)
    event = _make_run_item_event(item=tool_item)
    stream = _make_stream(events=[event])

    tool_event_handler = MagicMock()
    tool_event_handler.handle_tool_call = AsyncMock()

    async for _ in processor.process(
        stream,
        _make_chat_response(),
        ChatSessionStatus.CHATTING,
        tool_event_handler=tool_event_handler,
        client_ip="127.0.0.1",
    ):
        pass

    tool_event_handler.handle_tool_call.assert_awaited_once_with(tool_item, "127.0.0.1")


@pytest.mark.asyncio
async def test_tool_output_item_chunks_are_yielded():
    """SEP-TOOL-OUTPUT: run_item_stream_event whose item is ToolCallOutputItem → handle_tool_output() chunks yielded."""
    from agents import ToolCallOutputItem

    processor, chat_persistence, *_ = _make_processor()
    output_item = MagicMock(spec=ToolCallOutputItem)
    event = _make_run_item_event(item=output_item)
    stream = _make_stream(events=[event])

    sentinel_chunk = SimpleNamespace(response_type="tool_result")

    async def _fake_handle_tool_output(item, chat_response, session_status):
        yield sentinel_chunk

    tool_event_handler = MagicMock()
    tool_event_handler.handle_tool_output = _fake_handle_tool_output

    results = []
    async for chunk in processor.process(
        stream,
        _make_chat_response(),
        ChatSessionStatus.CHATTING,
        tool_event_handler=tool_event_handler,
    ):
        results.append(chunk)

    assert sentinel_chunk in results
