"""
Integration tests for SummaryService — targeting 100% branch coverage.

Tests call the real service with mocked repositories and mocked ConversationSummaryService.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from repositories.chat_repo import ChatRepository
from repositories.summary_repo import SummaryRepository
from services.conversation_summary_service import (
    ConversationSummaryService,
    SummaryGenerationError,
)
from services.summary_service import SummaryService

pytestmark = pytest.mark.pre_extraction_parity


def _make_svc(
    *,
    summary_repo_override=None,
    chat_repo_override=None,
    conv_summary_svc_override=None,
    max_retry_count: int = 3,
) -> SummaryService:
    summary_repo = summary_repo_override or Mock(spec=SummaryRepository)
    chat_repo = chat_repo_override or Mock(spec=ChatRepository)
    conv_svc = conv_summary_svc_override or MagicMock(spec=ConversationSummaryService)

    svc = SummaryService(
        summary_repository=summary_repo,
        chat_repository=chat_repo,
        conversation_summary_service=conv_svc,
        max_retry_count=max_retry_count,
        in_progress_stale_minutes=5,
    )
    return svc


# ─── check_should_start_summary ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_should_start_summary_zero_user_messages_does_nothing():
    svc = _make_svc()
    svc._chat_repository.count_user_messages_by_session.return_value = 0
    await svc.check_should_start_summary("sess-1")
    svc._summary_repository.get_latest_completed.assert_not_called()


@pytest.mark.asyncio
async def test_check_should_start_summary_non_multiple_of_20_does_nothing():
    svc = _make_svc()
    svc._chat_repository.count_user_messages_by_session.return_value = 5
    await svc.check_should_start_summary("sess-1")
    svc._summary_repository.get_latest_completed.assert_not_called()


@pytest.mark.asyncio
async def test_check_should_start_summary_boundary_id_none_returns():
    svc = _make_svc()
    svc._chat_repository.count_user_messages_by_session.return_value = 20
    svc._chat_repository.get_nth_user_message_history_id_by_session.return_value = None
    await svc.check_should_start_summary("sess-1")
    svc._summary_repository.get_latest_completed.assert_not_called()


@pytest.mark.asyncio
async def test_check_should_start_summary_latest_completed_covers_boundary():
    svc = _make_svc()
    svc._chat_repository.count_user_messages_by_session.return_value = 20
    svc._chat_repository.get_nth_user_message_history_id_by_session.return_value = 100
    latest = SimpleNamespace(summary_until_history_id=100)
    svc._summary_repository.get_latest_completed.return_value = latest
    await svc.check_should_start_summary("sess-1")
    # Already covered → no in_progress check needed
    svc._summary_repository.get_in_progress.assert_not_called()


@pytest.mark.asyncio
async def test_check_should_start_summary_in_progress_not_stale_skips():
    svc = _make_svc()
    svc._chat_repository.count_user_messages_by_session.return_value = 20
    svc._chat_repository.get_nth_user_message_history_id_by_session.return_value = 100
    svc._summary_repository.get_latest_completed.return_value = None
    in_progress = SimpleNamespace(summary_id=5)
    svc._summary_repository.get_in_progress.return_value = in_progress
    svc._summary_repository.is_stale_summary_row.return_value = False

    await svc.check_should_start_summary("sess-1")
    svc._chat_repository.get_latest_main_history_id_by_session.assert_not_called()


@pytest.mark.asyncio
async def test_check_should_start_summary_in_progress_stale_deletes_and_continues():
    svc = _make_svc()
    svc._chat_repository.count_user_messages_by_session.return_value = 20
    svc._chat_repository.get_nth_user_message_history_id_by_session.return_value = 100
    svc._summary_repository.get_latest_completed.return_value = None
    in_progress = SimpleNamespace(summary_id=5)
    svc._summary_repository.get_in_progress.return_value = in_progress
    svc._summary_repository.is_stale_summary_row.return_value = True
    svc._chat_repository.get_latest_main_history_id_by_session.return_value = None

    await svc.check_should_start_summary("sess-1")
    svc._summary_repository.delete_summary.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_check_should_start_summary_latest_main_history_none_returns():
    svc = _make_svc()
    svc._chat_repository.count_user_messages_by_session.return_value = 20
    svc._chat_repository.get_nth_user_message_history_id_by_session.return_value = 100
    svc._summary_repository.get_latest_completed.return_value = None
    svc._summary_repository.get_in_progress.return_value = None
    svc._chat_repository.get_latest_main_history_id_by_session.return_value = None

    await svc.check_should_start_summary("sess-1")
    svc._summary_repository.create_in_progress_row.assert_not_called()


@pytest.mark.asyncio
async def test_check_should_start_summary_triggers_summary_job():
    svc = _make_svc()
    svc._chat_repository.count_user_messages_by_session.return_value = 20
    svc._chat_repository.get_nth_user_message_history_id_by_session.return_value = 100
    svc._summary_repository.get_latest_completed.return_value = None
    svc._summary_repository.get_in_progress.return_value = None
    svc._chat_repository.get_latest_main_history_id_by_session.return_value = 150
    svc._summary_repository.create_in_progress_row.return_value = 42

    with patch("services.summary_service.asyncio.create_task") as mock_create_task:
        mock_task = MagicMock()
        mock_task.add_done_callback = MagicMock()
        # Close the coroutine immediately so it is not GC'd as unawaited.
        mock_create_task.side_effect = lambda coro, **kw: (coro.close(), mock_task)[1]
        await svc.check_should_start_summary("sess-1")

    mock_create_task.assert_called_once()


# ─── start_summary_job ────────────────────────────────────────────────────────


def test_start_summary_job_integrity_error_skips():
    svc = _make_svc()
    svc._summary_repository.create_in_progress_row.side_effect = IntegrityError(
        "unique constraint", [], None
    )

    # Should not raise, just return
    with patch("services.summary_service.asyncio.create_task") as mock_create_task:
        svc.start_summary_job("sess-1", 100)
    mock_create_task.assert_not_called()


def test_start_summary_job_creates_task():
    svc = _make_svc()
    svc._summary_repository.create_in_progress_row.return_value = 7

    with patch("services.summary_service.asyncio.create_task") as mock_create_task:
        mock_task = MagicMock()
        mock_task.add_done_callback = MagicMock()
        mock_create_task.side_effect = lambda coro, **kw: (coro.close(), mock_task)[1]
        svc.start_summary_job("sess-1", 100)

    mock_create_task.assert_called_once()


# ─── execute_summary_job ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_summary_job_row_not_found_returns():
    svc = _make_svc()
    svc._summary_repository.get_summary_by_id.return_value = None

    await svc.execute_summary_job(99)
    svc._conversation_summary_service.summarize_conversation.assert_not_called()


@pytest.mark.asyncio
async def test_execute_summary_job_success_with_previous_summary():
    svc = _make_svc()
    summary_row = SimpleNamespace(
        session_id="sess-exec",
        summary_until_history_id=200,
    )
    svc._summary_repository.get_summary_by_id.return_value = summary_row

    latest_completed = SimpleNamespace(
        summary_text="前回要約",
        summary_until_history_id=100,
    )
    svc._summary_repository.get_latest_completed.return_value = latest_completed
    svc._chat_repository.get_main_chat_histories_between_by_session.return_value = []
    svc._conversation_summary_service.summarize_conversation = AsyncMock(
        return_value="新要約テキスト"
    )

    await svc.execute_summary_job(1)

    svc._summary_repository.update_completed.assert_called_once_with(
        1, "新要約テキスト"
    )


@pytest.mark.asyncio
async def test_execute_summary_job_success_no_previous_summary():
    svc = _make_svc()
    summary_row = SimpleNamespace(
        session_id="sess-exec",
        summary_until_history_id=100,
    )
    svc._summary_repository.get_summary_by_id.return_value = summary_row
    svc._summary_repository.get_latest_completed.return_value = None
    svc._chat_repository.get_main_chat_histories_between_by_session.return_value = []
    svc._conversation_summary_service.summarize_conversation = AsyncMock(
        return_value="要約"
    )

    await svc.execute_summary_job(2)
    svc._summary_repository.update_completed.assert_called_once()


@pytest.mark.asyncio
async def test_execute_summary_job_retryable_error_retries_and_fails():
    svc = _make_svc(max_retry_count=2)
    summary_row = SimpleNamespace(
        session_id="sess-retry",
        summary_until_history_id=50,
    )
    svc._summary_repository.get_summary_by_id.return_value = summary_row
    svc._summary_repository.get_latest_completed.return_value = None
    svc._chat_repository.get_main_chat_histories_between_by_session.return_value = []
    svc._conversation_summary_service.summarize_conversation = AsyncMock(
        side_effect=SummaryGenerationError("rate limit", retryable=True)
    )

    with patch("services.summary_service.asyncio.sleep", new=AsyncMock()):
        await svc.execute_summary_job(3)

    svc._summary_repository.delete_summary.assert_called_once_with(3)
    # Should have retried max_retry_count times
    assert svc._conversation_summary_service.summarize_conversation.call_count == 2


@pytest.mark.asyncio
async def test_execute_summary_job_non_retryable_error_breaks_immediately():
    svc = _make_svc(max_retry_count=3)
    summary_row = SimpleNamespace(
        session_id="sess-nonretry",
        summary_until_history_id=50,
    )
    svc._summary_repository.get_summary_by_id.return_value = summary_row
    svc._summary_repository.get_latest_completed.return_value = None
    svc._chat_repository.get_main_chat_histories_between_by_session.return_value = []
    svc._conversation_summary_service.summarize_conversation = AsyncMock(
        side_effect=SummaryGenerationError("hard fail", retryable=False)
    )

    await svc.execute_summary_job(4)

    # Called only once — immediately stops
    assert svc._conversation_summary_service.summarize_conversation.call_count == 1
    svc._summary_repository.delete_summary.assert_called_once()


@pytest.mark.asyncio
async def test_execute_summary_job_unexpected_exception_breaks():
    svc = _make_svc(max_retry_count=3)
    summary_row = SimpleNamespace(
        session_id="sess-unexpected",
        summary_until_history_id=50,
    )
    svc._summary_repository.get_summary_by_id.return_value = summary_row
    svc._summary_repository.get_latest_completed.return_value = None
    svc._chat_repository.get_main_chat_histories_between_by_session.return_value = []
    svc._conversation_summary_service.summarize_conversation = AsyncMock(
        side_effect=RuntimeError("unexpected!")
    )

    await svc.execute_summary_job(5)

    assert svc._conversation_summary_service.summarize_conversation.call_count == 1
    svc._summary_repository.delete_summary.assert_called_once()


@pytest.mark.asyncio
async def test_execute_summary_job_zero_max_retry_skips_loop():
    """Line 138->170: max_retry_count=0 → range(1,1) is empty → delete immediately."""
    svc = _make_svc(max_retry_count=0)
    summary_row = SimpleNamespace(
        session_id="sess-zero-retry",
        summary_until_history_id=10,
    )
    svc._summary_repository.get_summary_by_id.return_value = summary_row
    svc._summary_repository.get_latest_completed.return_value = None
    svc._chat_repository.get_main_chat_histories_between_by_session.return_value = []

    await svc.execute_summary_job(99)

    svc._conversation_summary_service.summarize_conversation.assert_not_called()
    svc._summary_repository.delete_summary.assert_called_once_with(99)


# ─── _calculate_retry_delay_seconds ──────────────────────────────────────────


def test_calculate_retry_delay_returns_float():
    svc = _make_svc()
    delay = svc._calculate_retry_delay_seconds(1)
    assert isinstance(delay, float)
    assert delay >= svc._retry_base_delay_seconds  # at least 0.5s
    assert delay <= svc._retry_max_delay_seconds


def test_calculate_retry_delay_respects_max():
    svc = _make_svc()
    # attempt=100 → exponential would be huge, should be capped
    delay = svc._calculate_retry_delay_seconds(100)
    assert delay <= svc._retry_max_delay_seconds


# ─── get_latest_completed ─────────────────────────────────────────────────────


def test_get_latest_completed_delegates_to_repo():
    svc = _make_svc()
    expected = SimpleNamespace(summary_text="text")
    svc._summary_repository.get_latest_completed.return_value = expected

    result = svc.get_latest_completed("sess-1")
    assert result is expected


# ─── get_histories_after ─────────────────────────────────────────────────────


def test_get_histories_after_delegates_to_repo():
    svc = _make_svc()
    svc._chat_repository.get_main_chat_histories_after_by_session.return_value = []

    result = svc.get_histories_after("sess-1", 50)
    assert result == []
    svc._chat_repository.get_main_chat_histories_after_by_session.assert_called_once_with(
        "sess-1", 50
    )
