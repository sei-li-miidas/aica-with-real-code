"""セッション作成・チャット履歴保存・ツール出力更新コンポーネント。

ChatPersistence は DB への書き込み副作用をすべて担う。読み取り責務は持たない。

責務
-----
- セッション作成（初期メニューワークフロー完了時に 1 回だけ行われる）
- チャット履歴（ChatHistory）の DB 保存
- ツール出力の DB 更新（update_tool_output）

位置づけ
---------
- DI 注入の境界は ChatRepository のみ。ConversationState は参照として渡す。
- 外部 I/O は ChatRepository 経由のみ。LLM 呼び出しなし。
- ConversationState と 1:1 のライフサイクルで生成される（ChatService が生成する）。
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from agents import (
    HandoffCallItem,
    HandoffOutputItem,
    MessageOutputItem,
    ReasoningItem,
    ToolCallItem,
    ToolCallOutputItem,
)

from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from repositories.chat_repo import ChatRepository
from services.chat.constants import DEVELOPER_REQUEST_TYPES
from services.chat.conversation_state import ConversationState
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.enum import LLMMessageRole
from utils.log_utils import get_session_id

if TYPE_CHECKING:
    from agents import RunItem

logger = logging.getLogger(__name__)


def _parse_tool_arguments(arguments: object) -> dict[str, object]:
    """ツールコール引数を dict にパースする。

    LLM が返す arguments は str（JSON）・dict・None など一定でないため、
    安全にパースしてフォールバックする。

    - dict の場合: そのまま返す。
    - str の場合: json.loads を試み、失敗したらログして {} を返す。
    - None / その他: ログして {} を返す。
    """
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            result = json.loads(arguments)
            return result if isinstance(result, dict) else {}
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse tool arguments as JSON: %r", arguments)
            return {}
    logger.warning(
        "Unexpected tool arguments type %s: %r", type(arguments).__name__, arguments
    )
    return {}


def _get_raw_item_field(raw_item: object, field: str) -> object:
    """raw_item から指定フィールドを取得する。

    agents SDK の raw_item は TypedDict（dict）と Pydantic BaseModel（属性アクセス）の
    両方になり得るため、両方に対応する。DB 更新コンテキストでは欠落が想定外のため警告ログを出す。
    tool_event_handler._get_raw_item_field は警告なしの同等の実装（呼び出し元が None を処理する）。
    """
    if isinstance(raw_item, dict):
        value = raw_item.get(field)
    else:
        value = getattr(raw_item, field, None)
    if value is None:
        logger.warning(
            "raw_item %s has no %r field; update_tool_output may be skipped.",
            type(raw_item).__name__,
            field,
        )
    return value


def _serialize_tool_output_for_storage(output: object) -> str:
    """ツール出力をストレージ向け文字列にシリアライズする。"""
    if isinstance(output, str):
        return output

    def _default(obj: object) -> object:
        if is_dataclass(obj):
            return asdict(obj)  # type: ignore[arg-type]
        if hasattr(obj, "model_dump"):
            return obj.model_dump()  # type: ignore[attr-defined]
        if hasattr(obj, "dict"):
            return obj.dict()  # type: ignore[attr-defined]
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)

    return json.dumps(output, ensure_ascii=False, default=_default)


class ChatPersistence:
    """セッション作成・チャット履歴保存・ツール出力更新を担うコンポーネント。

    ConversationState をスカラー権威として参照し、DB 書き込み副作用のみを行う。

    ライフサイクル
    --------------
    - ChatService インスタンスと 1:1 で生成される。
    - set_toolcall_trace_content() は init_session() 完了後に 1 回呼ばれ、
      トレースメッセージ内容を設定する。
    - create_session() は初期メニューワークフロー完了時に 1 回呼ばれ、DB にセッションを作成する。
    - save_toolcall_trace_message() はセッション作成後に 1 回呼ばれ、
      設定済みのトレースメッセージを DB に保存する。
    """

    def __init__(
        self,
        chat_repository: ChatRepository,
        conv_state: ConversationState,
    ) -> None:
        self._chat_repository = chat_repository
        self._conv_state = conv_state
        # init_session() で設定されるツールコールトレースメッセージの内容。
        # save_toolcall_trace_message() で DB に保存する。
        self._toolcall_trace_content: str = ""

    def set_toolcall_trace_content(self, content: str) -> None:
        """init_session() 完了後にツールコールトレースメッセージ内容を設定する。"""
        self._toolcall_trace_content = content

    def save_toolcall_trace_message(self) -> None:
        """ツールコールトレースメッセージを DB に保存する。

        _toolcall_trace_content が空の場合は何もしない。
        初期メニューワークフロー完了後（セッション作成後）に 1 回だけ呼ぶ。
        """
        if not self._toolcall_trace_content:
            return
        self._save_chat_histories(
            [
                ChatHistory(
                    session_id=get_session_id(),
                    position_id=self._conv_state.position_id,
                    active_agent=self._conv_state.active_agent_name,
                    message_id="developer_" + datetime.now().strftime("%Y%m%d%H%M%S%f"),
                    role=LLMMessageRole.DEVELOPER,
                    content=self._toolcall_trace_content,
                )
            ]
        )

    def _get_message_role(self, request_type: ChatRequestType) -> LLMMessageRole:
        """リクエストタイプに応じた LLMMessageRole を返す。"""
        if request_type in DEVELOPER_REQUEST_TYPES:
            return LLMMessageRole.DEVELOPER
        return LLMMessageRole.USER

    def save_chat_history(self, item: "RunItem") -> None:
        """RunItem を ChatHistory に変換して DB に保存する。

        Args:
            item: 変換・保存対象の RunItem。
                MessageOutputItem → ASSISTANT
                HandoffCallItem / ToolCallItem → HANDOFF / TOOL
                HandoffOutputItem / ToolCallOutputItem → update_tool_output
                ReasoningItem → REASONING
                それ以外 → エラーログ出力
        """
        session_id = get_session_id()
        chat_histories: list[ChatHistory] = []

        if isinstance(item, MessageOutputItem):
            chat_histories.append(
                ChatHistory(
                    session_id=session_id,
                    position_id=self._conv_state.position_id,
                    active_agent=item.agent.name,
                    message_id=item.raw_item.id,
                    role=LLMMessageRole.ASSISTANT,
                    content=item.raw_item.content[0].text,
                )
            )
        elif isinstance(item, (HandoffCallItem, ToolCallItem)):
            if isinstance(item, ToolCallItem) and item.raw_item.name.startswith(
                "transfer_to_"
            ):
                # ハンドオフ発生時は ToolCall と HandoffCall の両方が発生するため ToolCall をスキップ
                return
            chat_histories.append(
                ChatHistory(
                    session_id=session_id,
                    position_id=self._conv_state.position_id,
                    active_agent=item.agent.name,
                    message_id=item.raw_item.id,
                    role=(
                        LLMMessageRole.TOOL
                        if isinstance(item, ToolCallItem)
                        else LLMMessageRole.HANDOFF
                    ),
                    tool_call_id=item.raw_item.call_id,
                    tool_name=item.raw_item.name,
                    tool_input=_parse_tool_arguments(item.raw_item.arguments),
                )
            )
        elif isinstance(item, (HandoffOutputItem, ToolCallOutputItem)):
            call_id = _get_raw_item_field(item.raw_item, "call_id")
            if call_id is None:
                return
            # ToolCallOutputItem.output は SDK の正規フィールド（dataclass field）。
            # HandoffOutputItem には .output がないため raw_item から取得する。
            if isinstance(item, ToolCallOutputItem):
                output = item.output
            else:
                output = _get_raw_item_field(item.raw_item, "output")
            self._chat_repository.update_tool_output(
                tool_call_id=call_id,
                tool_call_output=_serialize_tool_output_for_storage(output),
            )
        elif isinstance(item, ReasoningItem):
            chat_histories.append(
                ChatHistory(
                    session_id=session_id,
                    position_id=self._conv_state.position_id,
                    active_agent=item.agent.name,
                    message_id=item.raw_item.id,
                    role=LLMMessageRole.REASONING,
                    content=json.dumps(item.raw_item.summary),
                )
            )
        else:
            logger.error("Unsupported item type: %s", item)

        self._save_chat_histories(chat_histories)

    def create_session(self, session_status: ChatSessionStatus) -> None:
        """初期メニューワークフロー完了後にセッションを DB に作成する。

        Args:
            session_status: 現在のセッション状態。create_chat_session() に渡す。
        """
        self._chat_repository.create_chat_session(
            session_status=session_status,
        )

    def save_user_or_developer_message(self, request: ChatRequestModel) -> None:
        """ユーザーまたはデベロッパーメッセージを DB に保存する。

        Args:
            request: 保存対象のチャットリクエスト。
        """
        role = self._get_message_role(request.request_type)
        self._save_chat_histories(
            [
                ChatHistory(
                    session_id=get_session_id(),
                    position_id=self._conv_state.position_id,
                    active_agent=self._conv_state.active_agent_name,
                    message_id=request.current_message_id,
                    role=role,
                    content=request.message,
                    is_voice=request.is_voice,
                )
            ]
        )

    def save_llm_error(self, message_to_llm: str) -> None:
        """LLM エラー発生時のデベロッパーメッセージを DB に保存する。

        Args:
            message_to_llm: LLM に送るエラーメッセージ。
        """
        chat_history = ChatHistory(
            session_id=get_session_id(),
            active_agent=self._conv_state.active_agent_name,
            message_id="developer_" + datetime.now().strftime("%Y%m%d%H%M%S%f"),
            role=LLMMessageRole.DEVELOPER,
            content=message_to_llm,
        )
        self._save_chat_histories([chat_history])

    def block_session(self) -> None:
        """DB にセッションブロックフラグを立てる。

        StreamGuard が禁止ワード検知後にセッションをブロックするために使う。
        例外は呼び出し元が処理する。
        """
        self._chat_repository.block_session()

    def save_chat_histories(self, chat_histories: list[ChatHistory]) -> None:
        """複数の ChatHistory を一括で DB に保存し、conv_state.chat_histories に追加する。

        Args:
            chat_histories: 保存対象の ChatHistory リスト。
        """
        self._save_chat_histories(chat_histories)

    def _save_chat_histories(self, chat_histories: list[ChatHistory]) -> None:
        """内部: ChatHistory リストを DB 保存し、conv_state.chat_histories に追加する。"""
        if chat_histories:
            self._chat_repository.add_chat_histories(chat_histories)
            self._conv_state.chat_histories.setdefault(
                self._conv_state.chat_key, []
            ).extend(chat_histories)
