from contextlib import AbstractContextManager
from enum import IntEnum
from typing import Callable

from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from utils.log_utils import get_session_id


class ActionLogType(IntEnum):
    """ログタイプ"""

    # ツールIDよりのポジション再検索結果
    POSITION_SEARCH_RESULT = 1
    # もっと見る回数
    LOAD_MORE_POSITION = 2
    # おすすめ件数
    RECOMMENDATION = 3
    # ポジション詳細
    POSITION_DETAIL = 4
    # 登録
    REGISTRATION = 5
    # トークン使用
    TOKEN_USAGE = 6


class ActionLogRepository:
    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
    ) -> None:
        self._session_factory = session_factory

    def insert(
        self,
        log_type: ActionLogType,
        source: str | None = None,
        content: dict | str | None = None,
    ) -> None:
        """
        ActionLog を 1 件挿入します（append-only）。ORM の主キーに依存せず、Core で直接挿入します。

        Args:
            log_type: ログタイプ（smallint）。
            source: 任意のソース文字列。
            content: 任意の JSONB ペイロード。
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            stmt = text(
                """
                INSERT INTO action_logs (session_id, log_type, source, content)
                VALUES (:session_id, :log_type, :source, :content)
                """
            ).bindparams(
                bindparam("content", type_=JSONB),
            )
            session.execute(
                stmt,
                {
                    "session_id": session_id if session_id else "",
                    "log_type": log_type,
                    "source": source,
                    "content": content,
                },
            )
            session.commit()
