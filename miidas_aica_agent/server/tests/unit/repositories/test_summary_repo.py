from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database import Base
from domain.entities.chat_session import ChatSession
from domain.entities.chat_summary import ChatSummary, ChatSummaryStatus
from repositories.summary_repo import SummaryRepository


@pytest.fixture
def repository():
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(
            bind=engine,
            tables=[ChatSession.__table__, ChatSummary.__table__],
        )
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX uq_chat_summaries_in_progress_per_session "
                    "ON chat_summaries(session_id) WHERE status = 'in_progress'"
                )
            )
            conn.commit()

        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        @contextmanager
        def db_session():
            session = session_factory()
            try:
                yield session
                session.commit()
            finally:
                session.close()

        yield SummaryRepository(session_factory=db_session), db_session
    finally:
        engine.dispose()


def _add_chat_session(db_session, session_id: str):
    with db_session() as session:
        session.add(ChatSession(session_id=session_id))


class TestSummaryRepository:
    def test_in_progress_unique_index_enforces_single_row_per_session(self, repository):
        _repo, db_session = repository
        session_id = "s5"
        _add_chat_session(db_session, session_id)

        with db_session() as session:
            session.add(
                ChatSummary(
                    summary_id=1001,
                    session_id=session_id,
                    status=ChatSummaryStatus.IN_PROGRESS,
                    summary_text=None,
                    summary_until_history_id=100,
                )
            )

        with pytest.raises(IntegrityError):
            with db_session() as session:
                session.add(
                    ChatSummary(
                        summary_id=1002,
                        session_id=session_id,
                        status=ChatSummaryStatus.IN_PROGRESS,
                        summary_text=None,
                        summary_until_history_id=120,
                    )
                )

    def test_get_latest_completed_returns_max_summary_id(self, repository):
        repo, db_session = repository
        session_id = "s6"
        _add_chat_session(db_session, session_id)

        with db_session() as session:
            session.add_all(
                [
                    ChatSummary(
                        summary_id=1,
                        session_id=session_id,
                        status=ChatSummaryStatus.COMPLETED,
                        summary_text='{"v":1}',
                        summary_until_history_id=100,
                    ),
                    ChatSummary(
                        summary_id=2,
                        session_id=session_id,
                        status=ChatSummaryStatus.IN_PROGRESS,
                        summary_text=None,
                        summary_until_history_id=110,
                    ),
                    ChatSummary(
                        summary_id=3,
                        session_id=session_id,
                        status=ChatSummaryStatus.COMPLETED,
                        summary_text='{"v":3}',
                        summary_until_history_id=130,
                    ),
                ]
            )

        latest = repo.get_latest_completed(session_id)
        assert latest is not None
        assert int(latest.summary_id) == 3
        assert latest.summary_text == '{"v":3}'
