"""Unit tests for StreamGuard — 100% branch coverage.

Branches covered:
- reset(): delegates to llm_output_guard.reset_session_for_new_response
- process_chunk(): safe chunks yielded (non-empty), no safe chunks (empty), ForbiddenWordDetectedException raised
- finalize(): final chunks yielded when _last_item_id is set, final chunks skipped when _last_item_id is None, ForbiddenWordDetectedException raised
- cleanup(): delegates to llm_output_guard.remove_session
- _handle_security_detection(): block_session succeeds, block_session raises
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

pytestmark = pytest.mark.pre_extraction_parity
from domain.entities.chat_session import ChatSessionStatus
from security.llm_output_guard import ForbiddenWordDetectedException
from services.chat.stream_guard import StreamGuard
from utils.chat_response import ChatResponseType, ChatStreamResponse


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

SESSION_ID = "test-stream-guard-session"


def _make_guard(
    *,
    session_id: str = SESSION_ID,
    process_chunk_return: list[str] | None = None,
    process_chunk_raises: Exception | None = None,
    finalize_return: list[str] | None = None,
    finalize_raises: Exception | None = None,
    block_session_raises: Exception | None = None,
) -> tuple[StreamGuard, MagicMock, MagicMock]:
    """Build a StreamGuard with fully-mocked dependencies.

    Returns (stream_guard, mock_llm_output_guard, mock_chat_persistence).
    """
    mock_guard = MagicMock()
    mock_guard.reset_session_for_new_response.return_value = None
    if process_chunk_raises is not None:
        mock_guard.process_stream_chunk.side_effect = process_chunk_raises
    else:
        mock_guard.process_stream_chunk.return_value = (
            process_chunk_return if process_chunk_return is not None else []
        )
    if finalize_raises is not None:
        mock_guard.finalize_stream.side_effect = finalize_raises
    else:
        mock_guard.finalize_stream.return_value = (
            finalize_return if finalize_return is not None else []
        )
    mock_guard.remove_session.return_value = None

    mock_persistence = MagicMock()
    if block_session_raises is not None:
        mock_persistence.block_session.side_effect = block_session_raises
    else:
        mock_persistence.block_session.return_value = None

    guard = StreamGuard(
        llm_output_guard=mock_guard,
        chat_persistence=mock_persistence,
        session_id=session_id,
    )
    return guard, mock_guard, mock_persistence


def _make_chat_response() -> MagicMock:
    """Return a mock ChatStreamResponse with sentinel responses."""
    mock = MagicMock(spec=ChatStreamResponse)

    def create_agent_message_response(item_id, text, session_status):
        sentinel = MagicMock()
        sentinel.response_type = ChatResponseType.MESSAGE
        sentinel.message = text
        sentinel.message_id = item_id
        return sentinel

    def create_error_response(message, session_status):
        sentinel = MagicMock()
        sentinel.response_type = ChatResponseType.ERROR
        sentinel.message = message
        return sentinel

    mock.create_agent_message_response.side_effect = create_agent_message_response
    mock.create_error_response.side_effect = create_error_response
    return mock


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------


def test_reset_delegates_to_guard():
    guard, mock_guard, _ = _make_guard()
    guard.reset()
    mock_guard.reset_session_for_new_response.assert_called_once_with(SESSION_ID)


# ---------------------------------------------------------------------------
# process_chunk()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_chunk_yields_safe_chunks():
    """process_chunk yields one MESSAGE response per safe chunk."""
    guard, _, _ = _make_guard(process_chunk_return=["hello", " world"])
    chat_response = _make_chat_response()

    chunks = [
        chunk
        async for chunk in guard.process_chunk(
            "item-1", "hello world", chat_response, ChatSessionStatus.CHATTING
        )
    ]

    assert len(chunks) == 2
    assert chunks[0].response_type == ChatResponseType.MESSAGE
    assert chunks[0].message == "hello"
    assert chunks[1].response_type == ChatResponseType.MESSAGE
    assert chunks[1].message == " world"


@pytest.mark.asyncio
async def test_process_chunk_yields_nothing_when_no_safe_chunks():
    """process_chunk yields nothing when all input is in the pending buffer."""
    guard, _, _ = _make_guard(process_chunk_return=[])
    chat_response = _make_chat_response()

    chunks = [
        chunk
        async for chunk in guard.process_chunk(
            "item-1", "pending", chat_response, ChatSessionStatus.CHATTING
        )
    ]

    assert chunks == []


@pytest.mark.asyncio
async def test_process_chunk_updates_last_item_id():
    """process_chunk stores the item_id for finalize() to use."""
    guard, _, _ = _make_guard(process_chunk_return=["text"])
    chat_response = _make_chat_response()

    assert guard._last_item_id is None
    _ = [
        chunk
        async for chunk in guard.process_chunk(
            "item-xyz", "text", chat_response, ChatSessionStatus.CHATTING
        )
    ]
    assert guard._last_item_id == "item-xyz"


@pytest.mark.asyncio
async def test_process_chunk_yields_error_on_forbidden_word_detection():
    """process_chunk yields ERROR response when ForbiddenWordDetectedException is raised."""
    exc = ForbiddenWordDetectedException(word="badword", session_id=SESSION_ID)
    guard, mock_guard, mock_persistence = _make_guard(
        process_chunk_raises=exc,
    )
    chat_response = _make_chat_response()

    chunks = [
        chunk
        async for chunk in guard.process_chunk(
            "item-1", "badword", chat_response, ChatSessionStatus.CHATTING
        )
    ]

    assert len(chunks) == 1
    assert chunks[0].response_type == ChatResponseType.ERROR
    mock_guard.remove_session.assert_called_once_with(SESSION_ID)
    mock_persistence.block_session.assert_called_once()


# ---------------------------------------------------------------------------
# finalize()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_finalize_yields_final_chunks_when_last_item_id_set():
    """finalize() yields buffered chunks using the stored _last_item_id."""
    guard, _, _ = _make_guard(finalize_return=["buffered"])
    guard._last_item_id = "item-final"
    chat_response = _make_chat_response()

    chunks = [
        chunk
        async for chunk in guard.finalize(chat_response, ChatSessionStatus.CHATTING)
    ]

    assert len(chunks) == 1
    assert chunks[0].response_type == ChatResponseType.MESSAGE
    assert chunks[0].message == "buffered"
    assert chunks[0].message_id == "item-final"


@pytest.mark.asyncio
async def test_finalize_skips_final_chunks_when_last_item_id_is_none():
    """finalize() skips buffered chunks if no item_id was seen yet."""
    guard, _, _ = _make_guard(finalize_return=["orphaned-buffer"])
    # _last_item_id is None by default
    chat_response = _make_chat_response()

    chunks = [
        chunk
        async for chunk in guard.finalize(chat_response, ChatSessionStatus.CHATTING)
    ]

    assert chunks == []


@pytest.mark.asyncio
async def test_finalize_yields_nothing_when_no_pending_buffer():
    """finalize() yields nothing when finalize_stream() returns empty list."""
    guard, _, _ = _make_guard(finalize_return=[])
    guard._last_item_id = "item-1"
    chat_response = _make_chat_response()

    chunks = [
        chunk
        async for chunk in guard.finalize(chat_response, ChatSessionStatus.CHATTING)
    ]

    assert chunks == []


@pytest.mark.asyncio
async def test_finalize_yields_error_on_forbidden_word_in_buffer():
    """finalize() yields ERROR when finalize_stream() raises ForbiddenWordDetectedException."""
    exc = ForbiddenWordDetectedException(word="finalbad", session_id=SESSION_ID)
    guard, mock_guard, mock_persistence = _make_guard(
        finalize_raises=exc,
    )
    guard._last_item_id = "item-1"
    chat_response = _make_chat_response()

    chunks = [
        chunk
        async for chunk in guard.finalize(chat_response, ChatSessionStatus.CHATTING)
    ]

    assert len(chunks) == 1
    assert chunks[0].response_type == ChatResponseType.ERROR
    mock_guard.remove_session.assert_called_once_with(SESSION_ID)
    mock_persistence.block_session.assert_called_once()


# ---------------------------------------------------------------------------
# cleanup()
# ---------------------------------------------------------------------------


def test_cleanup_delegates_to_guard():
    guard, mock_guard, _ = _make_guard()
    guard.cleanup()
    mock_guard.remove_session.assert_called_once_with(SESSION_ID)


def test_cleanup_is_idempotent():
    """cleanup() can be called multiple times without error."""
    guard, mock_guard, _ = _make_guard()
    guard.cleanup()
    guard.cleanup()
    assert mock_guard.remove_session.call_count == 2
    mock_guard.remove_session.assert_called_with(SESSION_ID)


# ---------------------------------------------------------------------------
# _handle_security_detection() — block_session branch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_security_detection_still_returns_error_when_block_session_fails():
    """ERROR response is returned even if block_session() raises."""
    exc = ForbiddenWordDetectedException(word="badword", session_id=SESSION_ID)
    guard, mock_guard, mock_persistence = _make_guard(
        process_chunk_raises=exc,
        block_session_raises=RuntimeError("db error"),
    )
    chat_response = _make_chat_response()

    chunks = [
        chunk
        async for chunk in guard.process_chunk(
            "item-1", "badword", chat_response, ChatSessionStatus.CHATTING
        )
    ]

    assert len(chunks) == 1
    assert chunks[0].response_type == ChatResponseType.ERROR
    mock_guard.remove_session.assert_called_once_with(SESSION_ID)


# ---------------------------------------------------------------------------
# Integration: process_chunk → cleanup → finalize interaction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cleanup_after_process_chunk_is_idempotent():
    """After security detection (which calls remove_session), cleanup() is safe to call again."""
    exc = ForbiddenWordDetectedException(word="bad", session_id=SESSION_ID)
    guard, mock_guard, _ = _make_guard(process_chunk_raises=exc)
    chat_response = _make_chat_response()

    _ = [
        chunk
        async for chunk in guard.process_chunk(
            "item-1", "bad", chat_response, ChatSessionStatus.CHATTING
        )
    ]
    # This should not raise even though remove_session was already called
    guard.cleanup()

    assert mock_guard.remove_session.call_count == 2


def test_security_detected_false_initially():
    """security_detected is False before any detection."""
    guard, _, _ = _make_guard()
    assert guard.security_detected is False


@pytest.mark.asyncio
async def test_security_detected_true_after_process_chunk_detection():
    """security_detected becomes True after ForbiddenWordDetectedException in process_chunk."""
    exc = ForbiddenWordDetectedException(word="bad", session_id=SESSION_ID)
    guard, _, _ = _make_guard(process_chunk_raises=exc)
    chat_response = _make_chat_response()

    _ = [
        chunk
        async for chunk in guard.process_chunk(
            "item-1", "bad", chat_response, ChatSessionStatus.CHATTING
        )
    ]

    assert guard.security_detected is True


@pytest.mark.asyncio
async def test_security_detected_true_after_finalize_detection():
    """security_detected becomes True after ForbiddenWordDetectedException in finalize."""
    exc = ForbiddenWordDetectedException(word="bad", session_id=SESSION_ID)
    guard, _, _ = _make_guard(finalize_raises=exc)
    guard._last_item_id = "item-1"
    chat_response = _make_chat_response()

    _ = [
        chunk
        async for chunk in guard.finalize(chat_response, ChatSessionStatus.CHATTING)
    ]

    assert guard.security_detected is True


@pytest.mark.asyncio
async def test_process_chunk_then_finalize_with_multiple_chunks():
    """process_chunk followed by finalize yields all safe and buffered chunks."""
    guard, mock_guard, _ = _make_guard(
        process_chunk_return=["safe"],
        finalize_return=["flushed"],
    )
    guard._last_item_id = "item-1"
    chat_response = _make_chat_response()

    stream_chunks = [
        chunk
        async for chunk in guard.process_chunk(
            "item-1", "safeflushed", chat_response, ChatSessionStatus.CHATTING
        )
    ]
    final_chunks = [
        chunk
        async for chunk in guard.finalize(chat_response, ChatSessionStatus.CHATTING)
    ]

    assert len(stream_chunks) == 1
    assert stream_chunks[0].message == "safe"
    assert len(final_chunks) == 1
    assert final_chunks[0].message == "flushed"
