from unittest.mock import AsyncMock, Mock

import pytest

pytestmark = pytest.mark.pre_extraction_parity
from sqlalchemy.exc import IntegrityError
from domain.entities.chat_summary import ChatSummary
from services.conversation_summary_service import SummaryGenerationError
from services.summary_service import SummaryService


@pytest.fixture
def mock_summary_repo():
    return Mock()


@pytest.fixture
def mock_chat_repo():
    return Mock()


@pytest.fixture
def mock_conversation_summary_service():
    return Mock()


@pytest.fixture
def summary_service(
    mock_summary_repo,
    mock_chat_repo,
    mock_conversation_summary_service,
):
    return SummaryService(
        summary_repository=mock_summary_repo,
        chat_repository=mock_chat_repo,
        conversation_summary_service=mock_conversation_summary_service,
        max_retry_count=3,
    )


class TestCheckShouldStartSummary:
    @pytest.mark.parametrize(
        ("user_count", "should_start"),
        [
            (19, False),
            (20, True),
            (39, False),
            (40, True),
            (79, False),
            (80, True),
            (81, False),
        ],
    )
    @pytest.mark.asyncio
    async def test_boundary_trigger_by_user_count_mod_20(
        self,
        user_count,
        should_start,
        summary_service,
        mock_summary_repo,
        mock_chat_repo,
    ):
        mock_chat_repo.count_user_messages_by_session.return_value = user_count
        mock_chat_repo.get_nth_user_message_history_id_by_session.return_value = 1234
        mock_chat_repo.get_latest_main_history_id_by_session.return_value = 1300
        mock_summary_repo.get_latest_completed.return_value = None
        mock_summary_repo.get_in_progress.return_value = None
        summary_service.start_summary_job = Mock()

        await summary_service.check_should_start_summary("session-1")

        if should_start:
            mock_chat_repo.get_nth_user_message_history_id_by_session.assert_called_once_with(
                "session-1", user_count
            )
            summary_service.start_summary_job.assert_called_once_with("session-1", 1300)
        else:
            mock_chat_repo.get_nth_user_message_history_id_by_session.assert_not_called()
            summary_service.start_summary_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_when_in_progress_exists(
        self,
        summary_service,
        mock_summary_repo,
        mock_chat_repo,
    ):
        mock_chat_repo.count_user_messages_by_session.return_value = 40
        mock_chat_repo.get_nth_user_message_history_id_by_session.return_value = 1234
        mock_chat_repo.get_latest_main_history_id_by_session.return_value = 1300
        mock_summary_repo.get_latest_completed.return_value = None
        mock_summary_repo.get_in_progress.return_value = ChatSummary(
            summary_id=99,
            session_id="session-1",
            status="in_progress",
            summary_until_history_id=40,
        )
        mock_summary_repo.is_stale_summary_row.return_value = False

        summary_service.start_summary_job = Mock()

        await summary_service.check_should_start_summary("session-1")

        summary_service.start_summary_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_stale_in_progress_and_start(
        self,
        summary_service,
        mock_summary_repo,
        mock_chat_repo,
    ):
        mock_chat_repo.count_user_messages_by_session.return_value = 40
        mock_chat_repo.get_nth_user_message_history_id_by_session.return_value = 1234
        mock_chat_repo.get_latest_main_history_id_by_session.return_value = 1300
        mock_summary_repo.get_latest_completed.return_value = None
        mock_summary_repo.get_in_progress.return_value = ChatSummary(
            summary_id=99,
            session_id="session-1",
            status="in_progress",
            summary_until_history_id=40,
        )
        mock_summary_repo.is_stale_summary_row.return_value = True
        summary_service.start_summary_job = Mock()

        await summary_service.check_should_start_summary("session-1")

        mock_summary_repo.is_stale_summary_row.assert_called_once_with(99, 300)
        mock_summary_repo.delete_summary.assert_called_once_with(99)
        summary_service.start_summary_job.assert_called_once_with("session-1", 1300)

    @pytest.mark.asyncio
    async def test_catch_up_start_when_latest_completed_is_behind(
        self,
        summary_service,
        mock_summary_repo,
        mock_chat_repo,
    ):
        mock_chat_repo.count_user_messages_by_session.return_value = 80
        mock_chat_repo.get_nth_user_message_history_id_by_session.return_value = 2000
        mock_chat_repo.get_latest_main_history_id_by_session.return_value = 2222
        mock_summary_repo.get_latest_completed.return_value = ChatSummary(
            summary_id=1,
            session_id="session-1",
            status="completed",
            summary_text='{"upto":20}',
            summary_until_history_id=1000,
        )
        mock_summary_repo.get_in_progress.return_value = None
        summary_service.start_summary_job = Mock()

        await summary_service.check_should_start_summary("session-1")

        summary_service.start_summary_job.assert_called_once_with("session-1", 2222)

    @pytest.mark.asyncio
    async def test_no_start_when_latest_completed_already_reached_boundary(
        self,
        summary_service,
        mock_summary_repo,
        mock_chat_repo,
    ):
        mock_chat_repo.count_user_messages_by_session.return_value = 80
        mock_chat_repo.get_nth_user_message_history_id_by_session.return_value = 2000
        mock_summary_repo.get_latest_completed.return_value = ChatSummary(
            summary_id=2,
            session_id="session-1",
            status="completed",
            summary_text='{"upto":80}',
            summary_until_history_id=2000,
        )
        summary_service.start_summary_job = Mock()

        await summary_service.check_should_start_summary("session-1")

        summary_service.start_summary_job.assert_not_called()


class TestStartSummaryJob:
    def test_skip_when_integrity_error_on_concurrent_start(
        self,
        summary_service,
        mock_summary_repo,
    ):
        mock_summary_repo.create_in_progress_row.side_effect = IntegrityError(
            "INSERT", {}, Exception("duplicate")
        )

        summary_service.start_summary_job("session-1", 100)

        assert len(summary_service._tasks) == 0


class TestExecuteSummaryJob:
    @pytest.mark.asyncio
    async def test_update_completed_on_success(
        self,
        summary_service,
        mock_summary_repo,
        mock_chat_repo,
        mock_conversation_summary_service,
    ):
        summary_row = ChatSummary(
            summary_id=1,
            session_id="session-1",
            status="in_progress",
            summary_until_history_id=80,
        )
        latest_completed = ChatSummary(
            summary_id=2,
            session_id="session-1",
            status="completed",
            summary_text='{"old": true}',
            summary_until_history_id=20,
        )

        mock_summary_repo.get_summary_by_id.return_value = summary_row
        mock_summary_repo.get_latest_completed.return_value = latest_completed
        mock_chat_repo.get_main_chat_histories_between_by_session.return_value = []

        mock_conversation_summary_service.summarize_conversation = AsyncMock(
            return_value='{"new": true}'
        )

        await summary_service.execute_summary_job(1)

        mock_summary_repo.update_completed.assert_called_once_with(1, '{"new": true}')
        mock_summary_repo.delete_summary.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_summary_after_three_retryable_failures(
        self,
        summary_service,
        mock_summary_repo,
        mock_chat_repo,
        mock_conversation_summary_service,
    ):
        summary_row = ChatSummary(
            summary_id=1,
            session_id="session-1",
            status="in_progress",
            summary_until_history_id=80,
        )

        mock_summary_repo.get_summary_by_id.return_value = summary_row
        mock_summary_repo.get_latest_completed.return_value = None
        mock_chat_repo.get_main_chat_histories_between_by_session.return_value = []

        mock_conversation_summary_service.summarize_conversation = AsyncMock(
            side_effect=SummaryGenerationError("retry", retryable=True)
        )
        sleep_mock = AsyncMock()
        summary_service._calculate_retry_delay_seconds = Mock(return_value=0.1)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("services.summary_service.asyncio.sleep", sleep_mock)
            await summary_service.execute_summary_job(1)

        assert mock_conversation_summary_service.summarize_conversation.call_count == 3
        assert sleep_mock.await_count == 2
        mock_summary_repo.delete_summary.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_retryable_error_waits_before_retry(
        self,
        summary_service,
        mock_summary_repo,
        mock_chat_repo,
        mock_conversation_summary_service,
    ):
        summary_row = ChatSummary(
            summary_id=1,
            session_id="session-1",
            status="in_progress",
            summary_until_history_id=80,
        )
        mock_summary_repo.get_summary_by_id.return_value = summary_row
        mock_summary_repo.get_latest_completed.return_value = None
        mock_chat_repo.get_main_chat_histories_between_by_session.return_value = []

        mock_conversation_summary_service.summarize_conversation = AsyncMock(
            side_effect=[
                SummaryGenerationError("retry", retryable=True),
                '{"ok": true}',
            ]
        )
        sleep_mock = AsyncMock()
        summary_service._calculate_retry_delay_seconds = Mock(return_value=0.2)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("services.summary_service.asyncio.sleep", sleep_mock)
            await summary_service.execute_summary_job(1)

        sleep_mock.assert_awaited_once_with(0.2)
        mock_summary_repo.update_completed.assert_called_once_with(1, '{"ok": true}')

    @pytest.mark.asyncio
    async def test_execute_summary_job_uses_catch_up_range(
        self,
        summary_service,
        mock_summary_repo,
        mock_chat_repo,
        mock_conversation_summary_service,
    ):
        summary_row = ChatSummary(
            summary_id=10,
            session_id="session-1",
            status="in_progress",
            summary_until_history_id=8000,
        )
        latest_completed = ChatSummary(
            summary_id=9,
            session_id="session-1",
            status="completed",
            summary_text='{"upto":20}',
            summary_until_history_id=2000,
        )

        mock_summary_repo.get_summary_by_id.return_value = summary_row
        mock_summary_repo.get_latest_completed.return_value = latest_completed
        mock_chat_repo.get_main_chat_histories_between_by_session.return_value = []
        mock_conversation_summary_service.summarize_conversation = AsyncMock(
            return_value='{"upto":80}'
        )

        await summary_service.execute_summary_job(10)

        mock_chat_repo.get_main_chat_histories_between_by_session.assert_called_once_with(
            "session-1", 2000, 8000
        )
