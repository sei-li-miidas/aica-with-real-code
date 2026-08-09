from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domain.entities.chat_summary import ChatSummary, ChatSummaryStatus


class SummaryRepository:
    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
    ) -> None:
        self._session_factory = session_factory

    def get_latest_completed(self, session_id: str) -> ChatSummary | None:
        with self._session_factory() as session:
            stmt = (
                select(ChatSummary)
                .where(
                    ChatSummary.session_id == session_id,
                    ChatSummary.status == ChatSummaryStatus.COMPLETED,
                )
                .order_by(desc(ChatSummary.summary_id))
            )
            return session.scalars(stmt).first()

    def get_in_progress(self, session_id: str) -> ChatSummary | None:
        with self._session_factory() as session:
            stmt = (
                select(ChatSummary)
                .where(
                    ChatSummary.session_id == session_id,
                    ChatSummary.status == ChatSummaryStatus.IN_PROGRESS,
                )
                .order_by(desc(ChatSummary.summary_id))
            )
            return session.scalars(stmt).first()

    def get_summary_by_id(self, summary_id: int) -> ChatSummary | None:
        with self._session_factory() as session:
            stmt = select(ChatSummary).where(ChatSummary.summary_id == summary_id)
            return session.scalars(stmt).first()

    def create_in_progress_row(self, session_id: str, summary_until_history_id: int) -> int:
        with self._session_factory() as session:
            row = ChatSummary(
                session_id=session_id,
                status=ChatSummaryStatus.IN_PROGRESS,
                summary_until_history_id=summary_until_history_id,
            )
            session.add(row)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                raise
            session.refresh(row)
            return int(row.summary_id)

    def update_completed(self, summary_id: int, summary_text: str) -> None:
        with self._session_factory() as session:
            stmt = (
                update(ChatSummary)
                .where(ChatSummary.summary_id == summary_id)
                .values(
                    status=ChatSummaryStatus.COMPLETED,
                    summary_text=summary_text,
                )
            )
            session.execute(stmt)
            session.commit()

    def delete_summary(self, summary_id: int) -> None:
        with self._session_factory() as session:
            stmt = delete(ChatSummary).where(ChatSummary.summary_id == summary_id)
            session.execute(stmt)
            session.commit()

    def is_stale_summary_row(self, summary_id: int, stale_seconds: int) -> bool:
        with self._session_factory() as session:
            stmt = (
                select(
                    (
                        func.extract(
                            "epoch",
                            func.now() - ChatSummary.created_at,
                        )
                        > stale_seconds
                    )
                )
                .where(ChatSummary.summary_id == summary_id)
            )
            result = session.execute(stmt).scalar_one_or_none()
            return bool(result)
