from contextlib import contextmanager
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from database import Base
from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSession
from repositories.chat_repo import ChatRepository
from utils.enum import ToolName


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, _compiler, **_kwargs):
    return "TEXT"


@pytest.fixture
def repository():
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(
            bind=engine,
            tables=[ChatSession.__table__, ChatHistory.__table__],
        )
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        @contextmanager
        def db_session():
            session = session_factory()
            try:
                yield session
                session.commit()
            finally:
                session.close()

        yield ChatRepository(session_factory=db_session), db_session
    finally:
        engine.dispose()


def _add_chat_session(db_session, session_id: str):
    with db_session() as session:
        session.add(ChatSession(session_id=session_id))


class TestChatRepositorySummaryQueries:
    def test_get_nth_user_message_history_id_ignores_non_main_and_deleted(
        self, repository
    ):
        repo, db_session = repository
        session_id = "s1"
        _add_chat_session(db_session, session_id)

        with db_session() as session:
            session.add_all(
                [
                    ChatHistory(
                        id=1,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m1",
                        role="user",
                        content="u1",
                    ),
                    ChatHistory(
                        id=2,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m2",
                        role="assistant",
                        content="a1",
                    ),
                    ChatHistory(
                        id=3,
                        session_id=session_id,
                        position_id=10,
                        active_agent="a",
                        message_id="m3",
                        role="user",
                        content="position-user",
                    ),
                    ChatHistory(
                        id=4,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m4",
                        role="user",
                        content="deleted-user",
                        deleted_at=datetime(2026, 5, 1, 0, 0, 0),
                    ),
                    ChatHistory(
                        id=5,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m5",
                        role="user",
                        content="u2",
                    ),
                ]
            )

        assert repo.get_nth_user_message_history_id_by_session(session_id, 1) == 1
        assert repo.get_nth_user_message_history_id_by_session(session_id, 2) == 5
        assert repo.get_nth_user_message_history_id_by_session(session_id, 3) is None

    def test_get_histories_between_respects_exclusive_inclusive_bounds(
        self, repository
    ):
        repo, db_session = repository
        session_id = "s2"
        _add_chat_session(db_session, session_id)

        with db_session() as session:
            session.add_all(
                [
                    ChatHistory(
                        id=10,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m10",
                        role="user",
                        content="c10",
                    ),
                    ChatHistory(
                        id=11,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m11",
                        role="assistant",
                        content="c11",
                    ),
                    ChatHistory(
                        id=12,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m12",
                        role="user",
                        content="c12",
                    ),
                    ChatHistory(
                        id=13,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m13",
                        role="tool",
                        content="included tool (start_workflow)",
                        tool_name=ToolName.START_WORKFLOW.value,
                    ),
                    ChatHistory(
                        id=14,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m14",
                        role="tool",
                        content="excluded tool",
                        tool_name=ToolName.APPLICATION.value,
                    ),
                    ChatHistory(
                        id=15,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m15",
                        role="tool",
                        content="included tool",
                        tool_name=ToolName.GENERIC_POSITION_SEARCH.value,
                    ),
                ]
            )

        rows = repo.get_main_chat_histories_between_by_session(
            session_id, from_exclusive=11, to_inclusive=15
        )
        assert [row.id for row in rows] == [12, 13, 15]

    def test_get_histories_after_returns_only_strictly_newer_main_histories(
        self, repository
    ):
        repo, db_session = repository
        session_id = "s3"
        _add_chat_session(db_session, session_id)

        with db_session() as session:
            session.add_all(
                [
                    ChatHistory(
                        id=20,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m20",
                        role="user",
                        content="c20",
                    ),
                    ChatHistory(
                        id=21,
                        session_id=session_id,
                        position_id=99,
                        active_agent="a",
                        message_id="m21",
                        role="assistant",
                        content="position-detail",
                    ),
                    ChatHistory(
                        id=22,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m22",
                        role="assistant",
                        content="c22",
                    ),
                    ChatHistory(
                        id=23,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m23",
                        role="tool",
                        content="included tool (start_workflow)",
                        tool_name=ToolName.START_WORKFLOW.value,
                    ),
                    ChatHistory(
                        id=24,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m24",
                        role="tool",
                        content="included tool",
                        tool_name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value,
                    ),
                    ChatHistory(
                        id=25,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m25",
                        role="tool",
                        content="excluded tool",
                        tool_name=ToolName.APPLICATION.value,
                    ),
                ]
            )

        rows = repo.get_main_chat_histories_after_by_session(
            session_id, history_id_exclusive=20
        )
        assert [row.id for row in rows] == [22, 23, 24]

    def test_get_latest_main_history_id_ignores_non_chat_history_tools(
        self, repository
    ):
        repo, db_session = repository
        session_id = "s3b"
        _add_chat_session(db_session, session_id)

        with db_session() as session:
            session.add_all(
                [
                    ChatHistory(
                        id=40,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m40",
                        role="assistant",
                        content="a40",
                    ),
                    ChatHistory(
                        id=41,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m41",
                        role="tool",
                        content="excluded tool",
                        tool_name=ToolName.APPLICATION.value,
                    ),
                    ChatHistory(
                        id=42,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m42",
                        role="tool",
                        content="included tool",
                        tool_name=ToolName.IT_POSITION_SEARCH.value,
                    ),
                ]
            )

        assert repo.get_latest_main_history_id_by_session(session_id) == 42

    def test_get_latest_main_history_id_includes_start_workflow(self, repository):
        repo, db_session = repository
        session_id = "s3c"
        _add_chat_session(db_session, session_id)

        with db_session() as session:
            session.add_all(
                [
                    ChatHistory(
                        id=45,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m45",
                        role="assistant",
                        content="a45",
                    ),
                    ChatHistory(
                        id=46,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m46",
                        role="tool",
                        content='{"WorkflowID": "wf-1"}',
                        tool_name=ToolName.START_WORKFLOW.value,
                    ),
                ]
            )

        assert repo.get_latest_main_history_id_by_session(session_id) == 46

    def test_count_user_messages_counts_only_main_non_deleted_user(self, repository):
        repo, db_session = repository
        session_id = "s4"
        _add_chat_session(db_session, session_id)

        with db_session() as session:
            session.add_all(
                [
                    ChatHistory(
                        id=30,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m30",
                        role="user",
                        content="u30",
                    ),
                    ChatHistory(
                        id=31,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m31",
                        role="assistant",
                        content="a31",
                    ),
                    ChatHistory(
                        id=32,
                        session_id=session_id,
                        position_id=1,
                        active_agent="a",
                        message_id="m32",
                        role="user",
                        content="position-user",
                    ),
                    ChatHistory(
                        id=33,
                        session_id=session_id,
                        position_id=None,
                        active_agent="a",
                        message_id="m33",
                        role="user",
                        content="deleted-user",
                        deleted_at=datetime(2026, 5, 1, 0, 0, 0),
                    ),
                ]
            )

        assert repo.count_user_messages_by_session(session_id) == 1
