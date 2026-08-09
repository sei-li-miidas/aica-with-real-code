import asyncio
from copy import deepcopy
import random
from typing import Any

from sqlalchemy.exc import IntegrityError

from domain.entities.chat_history import ChatHistory
from domain.entities.chat_summary import ChatSummary
from repositories.chat_repo import ChatRepository
from repositories.summary_repo import SummaryRepository
from services.base_service import BaseService
from services.conversation_summary_service import (
    ConversationSummaryService,
    SummaryGenerationError,
)


class SummaryService(BaseService):
    def __init__(
        self,
        summary_repository: SummaryRepository,
        chat_repository: ChatRepository,
        conversation_summary_service: ConversationSummaryService,
        max_retry_count: int = 3,
        in_progress_stale_minutes: int = 5,
    ) -> None:
        super().__init__()
        self._summary_repository = summary_repository
        self._chat_repository = chat_repository
        self._conversation_summary_service = conversation_summary_service
        self._max_retry_count = max_retry_count
        self._in_progress_stale_minutes = in_progress_stale_minutes
        # 要約ジョブは同時刻に複数失敗しやすいため、同時再試行で再度429/5xxを踏まないよう
        # 指数バックオフ + ジッター（ランダム待機）を使う。
        # max_retry_count=3 の現設定では主に 0.5s, 1.0s, 2.0s 付近で再試行される。
        self._retry_base_delay_seconds = 0.5
        self._retry_max_delay_seconds = 8.0
        self._tasks: set[asyncio.Task[Any]] = set()

    async def check_should_start_summary(self, session_id: str) -> None:
        user_count = await asyncio.to_thread(
            self._chat_repository.count_user_messages_by_session, session_id
        )
        if user_count == 0 or user_count % 20 != 0:
            return

        boundary_history_id = await asyncio.to_thread(
            self._chat_repository.get_nth_user_message_history_id_by_session,
            session_id,
            user_count,
        )
        if boundary_history_id is None:
            self.logger.warning(
                "Summary boundary not found: session_id=%s, user_count=%s",
                session_id,
                user_count,
            )
            return

        latest_completed = await asyncio.to_thread(
            self._summary_repository.get_latest_completed, session_id
        )
        if (
            latest_completed is not None
            and latest_completed.summary_until_history_id >= boundary_history_id
        ):
            return

        in_progress = await asyncio.to_thread(
            self._summary_repository.get_in_progress, session_id
        )
        if in_progress is not None:
            if await asyncio.to_thread(
                self._summary_repository.is_stale_summary_row,
                int(in_progress.summary_id),
                self._in_progress_stale_minutes * 60,
            ):
                self.logger.warning(
                    "Deleting stale in_progress summary row: session_id=%s, summary_id=%s",
                    session_id,
                    in_progress.summary_id,
                )
                await asyncio.to_thread(
                    self._summary_repository.delete_summary, int(in_progress.summary_id)
                )
            else:
                return

        latest_main_history_id = await asyncio.to_thread(
            self._chat_repository.get_latest_main_history_id_by_session, session_id
        )
        if latest_main_history_id is None:
            self.logger.warning(
                "Latest main history not found: session_id=%s, user_count=%s",
                session_id,
                user_count,
            )
            return

        # 要約の保存境界は「20n件目ユーザー発言そのもの」ではなく、
        # その判定時点で保存済みのメインチャット最新履歴までにする。
        # （assistant応答や同ターンのツール関連履歴を含む）
        # start_summary_job は asyncio.create_task を呼び出すため、
        # asyncio.to_thread 内ではなくイベントループスレッド上で実行する必要がある。
        self.start_summary_job(session_id, latest_main_history_id)

    def start_summary_job(self, session_id: str, summary_until_history_id: int) -> None:
        try:
            summary_id = self._summary_repository.create_in_progress_row(
                session_id,
                summary_until_history_id,
            )
        except IntegrityError:
            # DBの部分ユニーク制約（session_id x in_progress）競合時は
            # 先行ジョブがあるとみなしてスキップ
            self.logger.info(
                "Summary job already started by another request: session_id=%s",
                session_id,
            )
            return

        task = asyncio.create_task(
            self.execute_summary_job(summary_id),
            name=f"summary-job-{summary_id}",
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def execute_summary_job(self, summary_id: int) -> None:
        summary_row = await asyncio.to_thread(
            self._summary_repository.get_summary_by_id, summary_id
        )
        if summary_row is None:
            return

        session_id = summary_row.session_id
        boundary_history_id = summary_row.summary_until_history_id

        latest_completed = await asyncio.to_thread(
            self._summary_repository.get_latest_completed, session_id
        )
        previous_summary_text = latest_completed.summary_text if latest_completed else None
        previous_boundary_id = (
            int(latest_completed.summary_until_history_id) if latest_completed else 0
        )

        histories = await asyncio.to_thread(
            self._chat_repository.get_main_chat_histories_between_by_session,
            session_id,
            previous_boundary_id,
            boundary_history_id,
        )

        for attempt in range(1, self._max_retry_count + 1):
            try:
                summary_text = await self._conversation_summary_service.summarize_conversation(
                    previous_summary_text=previous_summary_text,
                    chat_histories=deepcopy(histories),
                )
                await asyncio.to_thread(
                    self._summary_repository.update_completed, summary_id, summary_text
                )
                return
            except SummaryGenerationError as e:
                if not e.retryable or attempt >= self._max_retry_count:
                    break
                delay = self._calculate_retry_delay_seconds(attempt)
                self.logger.warning(
                    "Summary generation retry %d/%d: session_id=%s, summary_id=%s, delay=%.2fs, reason=%s",
                    attempt,
                    self._max_retry_count,
                    session_id,
                    summary_id,
                    delay,
                    str(e),
                )
                await asyncio.sleep(delay)
            except Exception as e:
                # 想定外は再試行しない
                self.logger.exception(
                    "Summary generation failed unexpectedly: session_id=%s, summary_id=%s, reason=%s",
                    session_id,
                    summary_id,
                    str(e),
                )
                break

        await asyncio.to_thread(self._summary_repository.delete_summary, summary_id)
        self.logger.error(
            "Summary generation failed after retries. in_progress row deleted: session_id=%s, summary_id=%s, summary_until_history_id=%s",
            session_id,
            summary_id,
            boundary_history_id,
        )

    def _calculate_retry_delay_seconds(self, attempt: int) -> float:
        """
        retry attempt は 1始まり。指数バックオフ + 少量ジッターで再試行間隔を決める。
        ジッターは同時再試行を分散して、短時間の負荷集中を避けるためのランダム遅延。
        """
        exponential = self._retry_base_delay_seconds * (2 ** (attempt - 1))
        jitter = random.uniform(0.0, self._retry_base_delay_seconds)
        return min(exponential + jitter, self._retry_max_delay_seconds)

    def get_latest_completed(self, session_id: str) -> ChatSummary | None:
        return self._summary_repository.get_latest_completed(session_id)

    def get_histories_after(
        self, session_id: str, history_id_exclusive: int
    ) -> list[ChatHistory]:
        return self._chat_repository.get_main_chat_histories_after_by_session(
            session_id, history_id_exclusive
        )
