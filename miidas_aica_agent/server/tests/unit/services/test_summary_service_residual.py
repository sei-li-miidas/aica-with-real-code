from unittest.mock import AsyncMock, Mock

import pytest

from domain.entities.chat_summary import ChatSummary
from services.conversation_summary_service import SummaryGenerationError
from services.summary_service import SummaryService

pytestmark = pytest.mark.pre_extraction_parity


@pytest.fixture
def deps():
    return Mock(), Mock(), Mock()


@pytest.fixture
def svc(deps):
    summary_repo, chat_repo, conv = deps
    return SummaryService(summary_repo, chat_repo, conv, max_retry_count=3)


@pytest.mark.asyncio
async def test_check_should_start_summary_boundary_not_found_logs_and_returns(svc, deps):
    summary_repo, chat_repo, _ = deps
    chat_repo.count_user_messages_by_session.return_value = 20
    chat_repo.get_nth_user_message_history_id_by_session.return_value = None

    svc.start_summary_job = Mock()
    await svc.check_should_start_summary("sid")

    svc.start_summary_job.assert_not_called()
    summary_repo.get_latest_completed.assert_not_called()


@pytest.mark.asyncio
async def test_check_should_start_summary_latest_main_not_found_returns(svc, deps):
    summary_repo, chat_repo, _ = deps
    chat_repo.count_user_messages_by_session.return_value = 20
    chat_repo.get_nth_user_message_history_id_by_session.return_value = 100
    chat_repo.get_latest_main_history_id_by_session.return_value = None
    summary_repo.get_latest_completed.return_value = None
    summary_repo.get_in_progress.return_value = None

    svc.start_summary_job = Mock()
    await svc.check_should_start_summary("sid")

    svc.start_summary_job.assert_not_called()


@pytest.mark.asyncio
async def test_execute_summary_job_returns_when_row_not_found(svc, deps):
    summary_repo, _, _ = deps
    summary_repo.get_summary_by_id.return_value = None

    await svc.execute_summary_job(1)

    summary_repo.delete_summary.assert_not_called()


@pytest.mark.asyncio
async def test_execute_summary_job_non_retryable_error_deletes_summary(svc, deps):
    summary_repo, chat_repo, conv = deps
    summary_repo.get_summary_by_id.return_value = ChatSummary(
        summary_id=1,
        session_id="sid",
        status="in_progress",
        summary_until_history_id=10,
    )
    summary_repo.get_latest_completed.return_value = None
    chat_repo.get_main_chat_histories_between_by_session.return_value = []
    conv.summarize_conversation = AsyncMock(
        side_effect=SummaryGenerationError("fatal", retryable=False)
    )

    await svc.execute_summary_job(1)

    summary_repo.delete_summary.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_execute_summary_job_unexpected_exception_deletes_summary(svc, deps):
    summary_repo, chat_repo, conv = deps
    summary_repo.get_summary_by_id.return_value = ChatSummary(
        summary_id=2,
        session_id="sid",
        status="in_progress",
        summary_until_history_id=20,
    )
    summary_repo.get_latest_completed.return_value = None
    chat_repo.get_main_chat_histories_between_by_session.return_value = []
    conv.summarize_conversation = AsyncMock(side_effect=RuntimeError("boom"))

    await svc.execute_summary_job(2)

    summary_repo.delete_summary.assert_called_once_with(2)


def test_calculate_retry_delay_clamps_to_max(svc):
    svc._retry_base_delay_seconds = 2.0
    svc._retry_max_delay_seconds = 2.5

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("services.summary_service.random.uniform", lambda a, b: 2.0)
        delay = svc._calculate_retry_delay_seconds(attempt=4)

    assert delay == 2.5


def test_get_latest_completed_and_histories_after_delegate(svc, deps):
    summary_repo, chat_repo, _ = deps
    summary_repo.get_latest_completed.return_value = "row"
    chat_repo.get_main_chat_histories_after_by_session.return_value = ["h1"]

    assert svc.get_latest_completed("sid") == "row"
    assert svc.get_histories_after("sid", 10) == ["h1"]


def test_start_summary_job_creates_task_and_registers_callback(svc, deps):
    summary_repo, _, _ = deps
    summary_repo.create_in_progress_row.return_value = 77

    created_task = Mock()
    created_task.add_done_callback = Mock()

    def _fake_create_task(coro, name):
        coro.close()
        return created_task

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("services.summary_service.asyncio.create_task", _fake_create_task)
        svc.start_summary_job("sid", 999)

    assert created_task in svc._tasks
    created_task.add_done_callback.assert_called_once_with(svc._tasks.discard)
