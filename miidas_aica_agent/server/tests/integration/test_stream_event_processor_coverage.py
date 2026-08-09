"""
Integration tests for StreamEventProcessor — targeting 100% branch coverage.

Tests call the real StreamEventProcessor with controlled fake run streams.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from domain.entities.chat_session import ChatSessionStatus
from services.chat.llm_runner import (
    LLMRawResponseEvent,
    LLMRunItemStreamEvent,
)
from services.chat.stream_event_processor import StreamEventProcessor

pytestmark = pytest.mark.pre_extraction_parity


class _FakeRunStream:
    """Fake LLMRunStream that replays a list of events."""

    def __init__(self, events: list, *, continuation_state=None, agent_state=None):
        self._events = events
        self.continuation_state = continuation_state
        self.agent_state = agent_state
        self.replay_items: list = []
        self.usage = None
        self._aclose_called = False

    async def stream_events(self):
        for event in self._events:
            yield event

    async def aclose(self):
        self._aclose_called = True


def _make_processor():
    """Create a StreamEventProcessor with mock callbacks."""
    from repositories.chat_repo import ChatRepository
    from services.chat.chat_persistence import ChatPersistence
    from services.chat.conversation_state import ConversationState

    chat_repo = Mock(spec=ChatRepository)
    conv_state = ConversationState()
    conv_state.active_agent_name = "CareerAdvisor"
    chat_persistence = ChatPersistence(chat_repo, conv_state)

    processor = StreamEventProcessor(
        chat_persistence=chat_persistence,
        is_stop_at_tool=Mock(return_value=False),
        append_stop_at_tool_outputs=Mock(),
        update_active_agent=Mock(),
        update_continuation_state=Mock(),
    )
    return processor


def _make_chat_response():
    chat_response = MagicMock()
    mock_model = SimpleNamespace(response_type="TEXT")
    chat_response.create_agent_message_response.return_value = mock_model
    return chat_response


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


# ─── stream_guard=None path (line 139) ───────────────────────────────────────


@pytest.mark.asyncio
async def test_process_no_stream_guard_yields_directly():
    """Line 139: stream_guard=None → yield directly without guard."""
    from utils.log_utils import set_session_id, clear_session_id

    processor = _make_processor()
    run_stream = _FakeRunStream([LLMRawResponseEvent(item_id="item-1", delta="hello")])
    chat_response = _make_chat_response()
    session_status = ChatSessionStatus.CHATTING

    chunks = []
    set_session_id("sess-processor")
    try:
        async for chunk in processor.process(
            run_stream,
            chat_response,
            session_status,
            tool_event_handler=_make_noop_tool_event_handler(),
            stream_guard=None,
        ):
            chunks.append(chunk)
    finally:
        clear_session_id()

    assert len(chunks) == 1
    chat_response.create_agent_message_response.assert_called_once_with(
        "item-1", "hello", session_status
    )
    assert run_stream._aclose_called is True


# ─── stream_guard=not None path (lines 115→117) ──────────────────────────────


@pytest.mark.asyncio
async def test_process_with_stream_guard_resets_and_yields():
    """Lines 115→117: stream_guard is not None → reset() called, chunks yielded."""
    from services.chat.stream_guard import StreamGuard
    from utils.log_utils import set_session_id, clear_session_id

    processor = _make_processor()

    guard = MagicMock()
    guard.process_stream_chunk.return_value = ["safe-chunk"]
    guard.finalize_stream.return_value = []

    chat_persistence = MagicMock()
    stream_guard = StreamGuard(guard, chat_persistence, "sess-guard")

    run_stream = _FakeRunStream([LLMRawResponseEvent(item_id="item-1", delta="hello")])
    chat_response = _make_chat_response()
    session_status = ChatSessionStatus.CHATTING

    # Override create_agent_message_response to return a non-ERROR chunk
    safe_chunk = SimpleNamespace(response_type="TEXT")
    chat_response.create_agent_message_response.return_value = safe_chunk

    chunks = []
    set_session_id("sess-guard")
    try:
        async for chunk in processor.process(
            run_stream,
            chat_response,
            session_status,
            tool_event_handler=_make_noop_tool_event_handler(),
            stream_guard=stream_guard,
        ):
            chunks.append(chunk)
    finally:
        clear_session_id()

    guard.reset_session_for_new_response.assert_called_once()


# ─── second item_id from different message ignored (lines 121-124) ────────────


@pytest.mark.asyncio
async def test_process_ignores_delta_from_different_item_id():
    """Lines 121-124: second delta has different item_id → ignored."""
    from utils.log_utils import set_session_id, clear_session_id

    processor = _make_processor()
    run_stream = _FakeRunStream(
        [
            LLMRawResponseEvent(item_id="item-1", delta="first"),
            LLMRawResponseEvent(
                item_id="item-2", delta="second-ignored"
            ),  # different id
            LLMRawResponseEvent(
                item_id="item-1", delta="back-to-first"
            ),  # same as first
        ]
    )
    chat_response = _make_chat_response()
    session_status = ChatSessionStatus.CHATTING

    chunks = []
    set_session_id("sess-multi-id")
    try:
        async for chunk in processor.process(
            run_stream,
            chat_response,
            session_status,
            tool_event_handler=_make_noop_tool_event_handler(),
            stream_guard=None,
        ):
            chunks.append(chunk)
    finally:
        clear_session_id()

    # Only "first" and "back-to-first" should be yielded (item-2 is ignored)
    assert len(chunks) == 2


# ─── tool_event_handler handles ToolCallItem (lines 155→117) ─────────────────


@pytest.mark.asyncio
async def test_process_tool_event_handler_handles_tool_call():
    """Lines 155→117: tool_event_handler is not None AND item is ToolCallItem."""
    from agents import ToolCallItem
    from utils.log_utils import set_session_id, clear_session_id

    processor = _make_processor()

    class FakeToolCallItem(ToolCallItem):
        def __init__(self):
            pass

    fake_tool_call = FakeToolCallItem()
    fake_tool_call.raw_item = SimpleNamespace(
        id="tc-1", call_id="tc-1", name="some_tool", arguments="{}"
    )
    fake_tool_call.agent = SimpleNamespace(name="CareerAdvisor", tool_use_behavior={})

    run_stream = _FakeRunStream([LLMRunItemStreamEvent(item=fake_tool_call)])
    chat_response = _make_chat_response()
    session_status = ChatSessionStatus.CHATTING

    tool_event_handler = MagicMock()
    tool_event_handler.handle_tool_call = AsyncMock()
    tool_event_handler.handle_tool_output = AsyncMock(return_value=iter([]))

    async def empty_output_gen(*args, **kwargs):
        return
        yield  # makes it an async generator

    tool_event_handler.handle_tool_output = empty_output_gen

    set_session_id("sess-tool-call")
    try:
        chunks = []
        async for chunk in processor.process(
            run_stream,
            chat_response,
            session_status,
            tool_event_handler=tool_event_handler,
        ):
            chunks.append(chunk)
    finally:
        clear_session_id()

    tool_event_handler.handle_tool_call.assert_called_once()


# ─── tool_event_handler handles ToolCallOutputItem (lines 161→117) ───────────


@pytest.mark.asyncio
async def test_process_tool_event_handler_handles_tool_output():
    """Lines 161→117: tool_event_handler is not None AND item is ToolCallOutputItem."""
    from agents import ToolCallOutputItem
    from utils.chat_response import ChatResponseType
    from utils.log_utils import set_session_id, clear_session_id

    processor = _make_processor()

    class FakeToolCallOutputItem(ToolCallOutputItem):
        def __init__(self):
            pass

    fake_output = FakeToolCallOutputItem()
    fake_output.raw_item = {"call_id": "tc-1", "output": "{}"}
    fake_output.output = "{}"
    fake_output.agent = SimpleNamespace(name="CareerAdvisor")

    run_stream = _FakeRunStream([LLMRunItemStreamEvent(item=fake_output)])
    chat_response = _make_chat_response()
    session_status = ChatSessionStatus.CHATTING

    tool_chunk = SimpleNamespace(response_type="POSITION_SEARCH_RESULT")

    async def output_gen(*args, **kwargs):
        yield tool_chunk

    tool_event_handler = MagicMock()
    tool_event_handler.handle_tool_call = AsyncMock()
    tool_event_handler.handle_tool_output = output_gen

    set_session_id("sess-tool-output")
    try:
        chunks = []
        async for chunk in processor.process(
            run_stream,
            chat_response,
            session_status,
            tool_event_handler=tool_event_handler,
        ):
            chunks.append(chunk)
    finally:
        clear_session_id()

    assert tool_chunk in chunks


# ─── non-tool run_item with required tool_event_handler ───────────────────────


@pytest.mark.asyncio
async def test_process_run_item_with_non_tool_item_and_required_handler():
    """run_item_stream_event が non-tool item の場合、必須 handler があっても副作用なく継続する。"""
    from utils.log_utils import set_session_id, clear_session_id

    processor = _make_processor()

    # Use a SimpleNamespace item that passes save_chat_history without crashing
    non_tool_item = SimpleNamespace(
        agent=SimpleNamespace(name="CareerAdvisor"), raw_item=SimpleNamespace()
    )

    run_stream = _FakeRunStream([LLMRunItemStreamEvent(item=non_tool_item)])
    chat_response = _make_chat_response()
    session_status = ChatSessionStatus.CHATTING

    set_session_id("sess-no-tool-handler")
    try:
        chunks = []
        async for chunk in processor.process(
            run_stream,
            chat_response,
            session_status,
            tool_event_handler=_make_noop_tool_event_handler(),
        ):
            chunks.append(chunk)
    finally:
        clear_session_id()

    # No chunks (item was a run_item, no text output)
    assert chunks == []


# ─── tool_event_handler is not None but item is not ToolCallItem/Output ───────


@pytest.mark.asyncio
async def test_process_tool_event_handler_with_non_tool_item():
    """Lines 155→117, 161→117: tool_event_handler not None but item is neither
    ToolCallItem nor ToolCallOutputItem → both isinstance checks are False → loop continues."""
    from utils.log_utils import set_session_id, clear_session_id

    processor = _make_processor()

    # Use a non-tool item (e.g., a SimpleNamespace that passes through)
    non_tool_item = SimpleNamespace(
        agent=SimpleNamespace(name="CareerAdvisor"), raw_item=SimpleNamespace()
    )

    run_stream = _FakeRunStream([LLMRunItemStreamEvent(item=non_tool_item)])
    chat_response = _make_chat_response()
    session_status = ChatSessionStatus.CHATTING

    tool_event_handler = MagicMock()
    tool_event_handler.handle_tool_call = AsyncMock()

    async def empty_output(*args, **kwargs):
        return
        yield

    tool_event_handler.handle_tool_output = empty_output

    set_session_id("sess-non-tool")
    try:
        chunks = []
        async for chunk in processor.process(
            run_stream,
            chat_response,
            session_status,
            tool_event_handler=tool_event_handler,
        ):
            chunks.append(chunk)
    finally:
        clear_session_id()

    # handler should not be called since item is neither ToolCallItem nor ToolCallOutputItem
    tool_event_handler.handle_tool_call.assert_not_called()


# ─── CancelledError prevents aclose (line 178→exit) ──────────────────────────


@pytest.mark.asyncio
async def test_process_cancelled_error_skips_aclose():
    """Line 178→exit: asyncio.CancelledError → aclose() is NOT called."""
    from utils.log_utils import set_session_id, clear_session_id

    processor = _make_processor()

    class CancellingRunStream:
        continuation_state = None
        agent_state = None
        replay_items: list = []
        usage = None
        _aclose_called = False

        async def stream_events(self):
            raise asyncio.CancelledError()
            yield  # make it async generator

        async def aclose(self):
            self._aclose_called = True

    run_stream = CancellingRunStream()
    chat_response = _make_chat_response()
    session_status = ChatSessionStatus.CHATTING

    set_session_id("sess-cancelled")
    try:
        with pytest.raises(asyncio.CancelledError):
            async for _ in processor.process(
                run_stream,
                chat_response,
                session_status,
                tool_event_handler=_make_noop_tool_event_handler(),
            ):
                pass
    finally:
        clear_session_id()

    # CancelledError → aclose() should NOT be called
    assert run_stream._aclose_called is False
