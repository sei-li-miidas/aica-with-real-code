import logging
from contextlib import AbstractContextManager
from typing import Callable, Tuple, Optional
from sqlalchemy import and_, asc, select, func, update, or_
from sqlalchemy.orm import Session, joinedload, aliased

from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSession, ChatSessionStatus
from domain.entities.user_profile import UserProfile
from utils.const import LOGGER_PREFIX
from utils.enum import LLMMessageRole, ToolName
from utils.log_utils import get_session_id


class ChatRepository:
    _CHAT_HISTORY_TOOL_NAMES = tuple(
        tool_name for tool_name in ToolName if ToolName.is_chat_history_tool(tool_name)
    )

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
    ) -> None:
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._session_factory = session_factory

    def init_chat_session(self) -> Tuple[Optional[ChatSession], bool]:
        """
        会話履歴とユーザー検索条件取得

        Args:
            None

        Returns:
            会話履歴 or None
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            HistoryAlias = aliased(ChatHistory)
            ProfileAlias = aliased(UserProfile)
            stmt = (
                select(ChatSession)
                .options(
                    joinedload(
                        ChatSession.histories.of_type(HistoryAlias).and_(
                            HistoryAlias.deleted_at.is_(None)
                        )
                    ),
                    joinedload(
                        ChatSession.user_profile.of_type(ProfileAlias).and_(
                            ProfileAlias.deleted_at.is_(None)
                        )
                    ),
                )
                .filter(
                    ChatSession.session_id == session_id,
                    ChatSession.deleted_at.is_(None),
                )
                .order_by(HistoryAlias.id)
            )
            chat_session = session.scalars(stmt).unique().first()
            if chat_session:
                return (chat_session, True)
            else:
                # 指定session_idのセッションは期限切れで削除されたかを確認します。
                count_stmt = (
                    select(func.count())
                    .select_from(ChatSession)
                    .where(
                        ChatSession.session_id == session_id,
                        ChatSession.deleted_at.isnot(None),
                    )
                )
                count = session.execute(count_stmt).scalar_one()
                return (None, count > 0)

    def create_chat_session(
        self,
        session_status: ChatSessionStatus,
    ):
        """
        会話セッション作成する。

        Args:
            session_status: セッション作成時のセッションステータス
        """
        with self._session_factory() as session:
            chat_session = ChatSession(
                session_id=get_session_id(),
                status=session_status,
            )
            session.add(chat_session)
            session.commit()

    def add_chat_histories(
        self,
        chat_histories: list[ChatHistory],
    ):
        """
        複数会話を追加する。

        Args:
            chat_histories: 会話履歴
        """
        with self._session_factory() as session:
            # 同じChatHistoryインスタンスが他の場所で再利用されたり、以前に別のセッションに
            # 添付されていた場合のSQLAlchemyセッションバインディング問題を避けるためにクローンが必要。
            for chat_history in chat_histories:
                session.add(self.clone_chat_history(chat_history))
            session.commit()

    @staticmethod
    def clone_chat_history(
        chat_history: ChatHistory,
    ) -> ChatHistory:
        """
        SQLAlchemyのセッションバインディング問題を防ぐためにChatHistoryオブジェクトをクローンする。

        SQLAlchemyセッションにオブジェクトを追加すると、そのオブジェクトはセッションにバインドされる。
        セッションが非アクティブになった後にオブジェクトを変更すると、エラーが発生する可能性がある。
        クローンを作成することで、安全に使用できる新しいインスタンスを作成する。

        Args:
            chat_history: クローンする元のChatHistoryオブジェクト

        Returns:
            同じデータを持つ新しいChatHistoryインスタンス
        """
        return ChatHistory(
            session_id=chat_history.session_id,
            position_id=chat_history.position_id,
            active_agent=chat_history.active_agent,
            message_id=chat_history.message_id,
            role=chat_history.role,
            content=chat_history.content,
            tool_call_id=chat_history.tool_call_id,
            tool_name=chat_history.tool_name,
            tool_input=chat_history.tool_input,
            is_voice=chat_history.is_voice,
        )

    def session_status(
        self,
    ) -> ChatSessionStatus | None:
        """
        該当セッションのステータス

        Args:
            None

        Returns:
            セッション存在する場合、status
            存在してない場合、None
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            stmt = select(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.deleted_at.is_(None),
            )
            chat_session = session.scalars(stmt).first()
            if chat_session:
                return chat_session.status
            return None

    def update_session_status(
        self,
        session_status: ChatSessionStatus,
    ) -> ChatSessionStatus | None:
        """
        該当セッションのステータスを更新する

        Args:
            session_status: 新しいステータス

        Returns:
            セッション存在する場合、新しいステータス
            存在してない場合、None
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            stmt = select(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.deleted_at.is_(None),
            )
            chat_session = session.scalars(stmt).first()
            if chat_session:
                chat_session.status = session_status
                session.commit()
                return session_status
            return None

    def register_user_id(
        self,
        session_status: ChatSessionStatus,
        user_id: int | None,
    ) -> ChatSessionStatus | None:
        """
        ユーザーIDを保存&セッションステータスを更新する

        Args:
            session_status: 新しいステータス
            user_id: ユーザーID
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            stmt = select(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.deleted_at.is_(None),
            )
            chat_session = session.scalars(stmt).first()
            if chat_session:
                chat_session.miidas_user_id = user_id
                chat_session.status = session_status
                session.commit()
                return session_status

        return None

    def get_tool_input(
        self,
        tool_call_id: str,
    ) -> dict | None:
        """
        ツールINPUT取得
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            stmt = (
                select(ChatHistory)
                .filter(
                    ChatHistory.session_id == session_id,
                    ChatHistory.tool_call_id == tool_call_id,
                    ChatHistory.deleted_at.is_(None),
                )
                .order_by(ChatHistory.id.desc())
            )
            chat_history = session.scalars(stmt).first()
            if chat_history:
                return chat_history.tool_input
            return None

    def get_tool_output(
        self,
        tool_call_id: str,
    ) -> str | None:
        """
        ツールOUTPUT取得
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            stmt = (
                select(ChatHistory)
                .filter(
                    ChatHistory.session_id == session_id,
                    ChatHistory.tool_call_id == tool_call_id,
                    ChatHistory.deleted_at.is_(None),
                )
                .order_by(ChatHistory.id.desc())
            )
            chat_history = session.scalars(stmt).first()
            if chat_history:
                return chat_history.content
            return None

    def update_tool_output(
        self,
        tool_call_id: str,
        tool_call_output: str,
    ) -> bool:
        """
        ツールOUTPUT更新

        指定された `tool_call_id` に対応する最新の `ChatHistory` レコードの
        `content` を与えられた `tool_call_output` に更新します。

        Args:
            tool_call_id: ツール呼び出しID
            tool_call_output: 更新後の出力文字列

        Returns:
            更新が成功した場合 True、対象が見つからない場合 False
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            upd = (
                update(ChatHistory)
                .where(
                    ChatHistory.session_id == session_id,
                    ChatHistory.tool_call_id == tool_call_id,
                    ChatHistory.deleted_at.is_(None),
                )
                .values(content=tool_call_output)
            )
            result = session.execute(upd)
            session.commit()
            return result.rowcount is not None and result.rowcount > 0

    def is_session_blocked(self) -> bool:
        """
        セッションがブロックされているかチェック

        Returns:
            True: ブロックされている（会話不可）
            False: ブロックされていない（会話可能）
        """
        session_id = get_session_id()
        try:
            with self._session_factory() as session:
                from sqlalchemy import text

                result = session.execute(
                    text(
                        "SELECT is_blocked FROM chat_sessions WHERE session_id = :session_id AND deleted_at IS NULL"
                    ),
                    {"session_id": session_id},
                ).first()

                if result:
                    return bool(result[0])
                return False
        except Exception as e:
            self._logger.warning(
                "is_session_blocked failed for %s: %s", session_id, e, exc_info=True
            )
            return False

    def block_session(self) -> bool:
        """
        セッションをブロック状態にする（LLM出力でインジェクション検知時）

        Returns:
            True: ブロック成功
            False: セッションが見つからない
        """
        session_id = get_session_id()

        try:
            with self._session_factory() as session:
                from sqlalchemy import text

                result = session.execute(
                    text(
                        "UPDATE chat_sessions SET is_blocked = true WHERE session_id = :session_id AND deleted_at IS NULL"
                    ),
                    {"session_id": session_id},
                )
                session.commit()

                if result.rowcount > 0:
                    self._logger.info("Session %s blocked successfully", session_id)
                    return True
                else:
                    return False
        except Exception:
            self._logger.exception("block_session failed")
            return False

    def has_position_chat_histories(self, position_id: str) -> bool:
        """
        指定されたposition_idのチャット履歴が存在するかチェック

        Args:
            position_id: 確認対象のポジションID

        Returns:
            True: チャット履歴が存在する
            False: チャット履歴が存在しない
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            stmt = (
                select(func.count())
                .select_from(ChatHistory)
                .where(
                    ChatHistory.session_id == session_id,
                    ChatHistory.position_id == int(position_id),
                    ChatHistory.deleted_at.is_(None),
                )
            )
            count = session.execute(stmt).scalar_one()
            return count > 0

    def _get_chat_histories(
        self,
        position_id: str | None,
        message_id: str | None,
    ) -> list[ChatHistory]:
        """
        チャット履歴取得の共通処理

        Args:
            position_id: ポジションID（Noneの場合はメインチャット）
            message_id: メッセージID（指定された場合、そのIDより前のメッセージのみ取得）

        Returns:
            チャット履歴リスト
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            # position_idがNoneの場合はis_(None)、そうでない場合は==で比較
            position_filter = (
                ChatHistory.position_id.is_(None)
                if position_id is None
                else ChatHistory.position_id == int(position_id)
            )

            stmt = select(ChatHistory).filter(
                ChatHistory.session_id == session_id,
                position_filter,
                ChatHistory.deleted_at.is_(None),
                # roleがtoolの場合、tool_nameがPOSITION_SEARCHのみ取得
                or_(
                    ChatHistory.role != LLMMessageRole.TOOL,
                    ChatHistory.tool_name.in_(self._CHAT_HISTORY_TOOL_NAMES),
                ),
            )

            # message_idが指定されている場合のみ、IDフィルタを追加
            if message_id is not None:
                target_id_subquery = (
                    select(ChatHistory.id)
                    .filter(
                        ChatHistory.session_id == session_id,
                        position_filter,
                        ChatHistory.message_id == message_id,
                        ChatHistory.deleted_at.is_(None),
                    )
                    .scalar_subquery()
                )
                stmt = stmt.filter(ChatHistory.id < target_id_subquery)

            stmt = stmt.order_by(ChatHistory.id.asc())
            chat_histories = session.scalars(stmt).all()
            return chat_histories

    def get_main_chat_histories(self, message_id: str = None) -> list[ChatHistory]:
        """
        メインチャット履歴取得
        message_idが指定された場合、そのメッセージのIDより小さいIDを持つメッセージのみを取得
        message_idがNoneの場合、すべてのメッセージを取得
        """
        return self._get_chat_histories(position_id=None, message_id=message_id)

    def get_last_main_chat_history(self) -> ChatHistory | None:
        """
        メインチャットの最終レコードを1件取得する
        """
        session_id = get_session_id()
        with self._session_factory() as session:
            stmt = (
                select(ChatHistory)
                .filter(
                    ChatHistory.session_id == session_id,
                    ChatHistory.position_id.is_(None),
                    ChatHistory.deleted_at.is_(None),
                )
                .order_by(ChatHistory.id.desc())
                .limit(1)
            )
            return session.scalars(stmt).first()

    def get_position_detail_chat_histories(
        self,
        position_id: str,
        message_id: str = None,
    ) -> list[ChatHistory]:
        """
        ポジション詳細チャット履歴取得
        message_idが指定された場合、そのメッセージのIDより小さいIDを持つメッセージのみを取得
        message_idがNoneの場合、すべてのメッセージを取得
        """
        return self._get_chat_histories(position_id=position_id, message_id=message_id)

    # summary
    def count_user_messages_by_session(self, session_id: str) -> int:
        with self._session_factory() as session:
            stmt = (
                select(func.count())
                .select_from(ChatHistory)
                .where(
                    ChatHistory.session_id == session_id,
                    ChatHistory.position_id.is_(None),
                    ChatHistory.role == LLMMessageRole.USER.value,
                    ChatHistory.deleted_at.is_(None),
                )
            )
            return int(session.execute(stmt).scalar_one())

    def get_nth_user_message_history_id_by_session(
        self, session_id: str, n: int
    ) -> int | None:
        if n <= 0:
            return None

        with self._session_factory() as session:
            stmt = (
                select(ChatHistory.id)
                .where(
                    ChatHistory.session_id == session_id,
                    ChatHistory.position_id.is_(None),
                    ChatHistory.role == LLMMessageRole.USER.value,
                    ChatHistory.deleted_at.is_(None),
                )
                .order_by(asc(ChatHistory.id))
                .offset(n - 1)
                .limit(1)
            )
            history_id = session.execute(stmt).scalar_one_or_none()
            return int(history_id) if history_id is not None else None

    def get_latest_main_history_id_by_session(self, session_id: str) -> int | None:
        with self._session_factory() as session:
            stmt = select(func.max(ChatHistory.id)).where(
                ChatHistory.session_id == session_id,
                ChatHistory.position_id.is_(None),
                ChatHistory.deleted_at.is_(None),
                or_(
                    ChatHistory.role != LLMMessageRole.TOOL.value,
                    ChatHistory.tool_name.in_(self._CHAT_HISTORY_TOOL_NAMES),
                ),
            )
            history_id = session.execute(stmt).scalar_one_or_none()
            return int(history_id) if history_id is not None else None

    def get_main_chat_histories_after_by_session(
        self, session_id: str, history_id_exclusive: int
    ) -> list[ChatHistory]:
        with self._session_factory() as session:
            stmt = (
                select(ChatHistory)
                .where(
                    ChatHistory.session_id == session_id,
                    ChatHistory.position_id.is_(None),
                    ChatHistory.deleted_at.is_(None),
                    ChatHistory.id > history_id_exclusive,
                    or_(
                        ChatHistory.role != LLMMessageRole.TOOL.value,
                        ChatHistory.tool_name.in_(self._CHAT_HISTORY_TOOL_NAMES),
                    ),
                )
                .order_by(asc(ChatHistory.id))
            )
            return list(session.scalars(stmt).all())

    def get_main_chat_histories_between_by_session(
        self,
        session_id: str,
        from_exclusive: int,
        to_inclusive: int,
    ) -> list[ChatHistory]:
        with self._session_factory() as session:
            stmt = (
                select(ChatHistory)
                .where(
                    ChatHistory.session_id == session_id,
                    ChatHistory.position_id.is_(None),
                    ChatHistory.deleted_at.is_(None),
                    and_(
                        ChatHistory.id > from_exclusive,
                        ChatHistory.id <= to_inclusive,
                    ),
                    or_(
                        ChatHistory.role != LLMMessageRole.TOOL.value,
                        ChatHistory.tool_name.in_(self._CHAT_HISTORY_TOOL_NAMES),
                    ),
                )
                .order_by(asc(ChatHistory.id))
            )
            return list(session.scalars(stmt).all())
