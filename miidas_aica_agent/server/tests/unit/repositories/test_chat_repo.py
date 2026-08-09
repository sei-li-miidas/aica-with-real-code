"""
ChatRepositoryのチャット履歴関連メソッドの単体テスト。
"""

from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock

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
from utils.log_utils import set_session_id, clear_session_id


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, _compiler, **_kwargs):
    return "TEXT"


@pytest.fixture(autouse=True)
def session_scope():
    """全テストでセッションIDをセットアップする。"""
    set_session_id("test-session-id")
    yield
    clear_session_id()


@pytest.fixture
def mock_session():
    """SQLAlchemy Sessionのモックを作成する。"""
    return MagicMock()


@pytest.fixture
def chat_repo(mock_session):
    """モックのセッションファクトリでChatRepositoryを作成する。"""

    @contextmanager
    def session_factory():
        yield mock_session

    return ChatRepository(session_factory=session_factory)


class TestHasPositionChatHistories:
    """has_position_chat_historiesのテスト。"""

    def test_returns_true_when_histories_exist(self, chat_repo, mock_session):
        """count > 0 の場合にTrueを返すこと。"""
        # count=5 を返すように設定
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute.return_value = mock_result

        result = chat_repo.has_position_chat_histories("123")

        assert result is True
        mock_session.execute.assert_called_once()

    def test_returns_false_when_no_histories(self, chat_repo, mock_session):
        """count=0 の場合にFalseを返すこと。"""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_result

        result = chat_repo.has_position_chat_histories("123")

        assert result is False


@pytest.fixture
def db_repository():
    """SQLiteインメモリDBを使うChatRepositoryを作成する。"""
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


class TestGetLastMainChatHistory:
    """get_last_main_chat_historyのテスト。"""

    SESSION_ID = "test-session-id"  # session_scope フィクスチャと同じ値

    def _add_chat_session(self, db_session):
        with db_session() as session:
            session.add(ChatSession(session_id=self.SESSION_ID))

    def _make_history(self, history_id: int, **kwargs) -> ChatHistory:
        params = {
            "id": history_id,
            "session_id": self.SESSION_ID,
            "position_id": None,
            "active_agent": "a",
            "message_id": f"m{history_id}",
            "role": "assistant",
            "content": f"c{history_id}",
        }
        params.update(kwargs)
        return ChatHistory(**params)

    def test_returns_last_record_without_tool_filter(self, db_repository):
        """toolフィルタなしで最後の1件を返すこと（start_workflowも対象）。"""
        repo, db_session = db_repository
        self._add_chat_session(db_session)

        with db_session() as session:
            session.add_all(
                [
                    self._make_history(1, role="user"),
                    self._make_history(2),
                    self._make_history(
                        3,
                        role="tool",
                        tool_name=ToolName.START_WORKFLOW.value,
                        content='{"WorkflowID": "job_match_diagnosis"}',
                    ),
                ]
            )

        result = repo.get_last_main_chat_history()

        assert result is not None
        assert result.id == 3
        assert result.tool_name == ToolName.START_WORKFLOW.value

    def test_ignores_position_detail_records(self, db_repository):
        """position_id付きレコードは無視してメインチャットの最後を返すこと。"""
        repo, db_session = db_repository
        self._add_chat_session(db_session)

        with db_session() as session:
            session.add_all(
                [
                    self._make_history(1),
                    self._make_history(2, position_id=99),
                ]
            )

        result = repo.get_last_main_chat_history()

        assert result is not None
        assert result.id == 1

    def test_excludes_deleted_records(self, db_repository):
        """deleted_atが設定されたレコードは除外されること。"""
        repo, db_session = db_repository
        self._add_chat_session(db_session)

        with db_session() as session:
            session.add_all(
                [
                    self._make_history(1),
                    self._make_history(
                        2, deleted_at=datetime(2026, 7, 1, 0, 0, 0)
                    ),
                ]
            )

        result = repo.get_last_main_chat_history()

        assert result is not None
        assert result.id == 1

    def test_returns_none_when_no_records(self, db_repository):
        """レコードがない場合Noneを返すこと。"""
        repo, db_session = db_repository
        self._add_chat_session(db_session)

        assert repo.get_last_main_chat_history() is None
