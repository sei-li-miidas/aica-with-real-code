"""LLM ターン入力準備コンポーネント。

TurnPreparer は LLM に渡すターン入力（会話リスト・エージェント種別・
ポジション詳細メッセージなど）を準備する責務を持つ。

責務
-----
- 現在ページ（CHAT / POSITION_DETAIL）に応じたエージェント切り替え
- ポジション詳細ページ初回アクセス時の位置詳細取得と会話リスト初期化
- ポジション詳細取得（PositionService 呼び出し）
- ChatHistory 保存依頼（ChatPersistence 経由）
- リクエストタイプから LLMMessageRole 解決

位置づけ
---------
- DI 注入の境界は PositionService と ChatPersistence。
- ConversationState は参照として渡し、turn 準備の結果を直接書き込む。
- stream event の処理は一切行わない。LLM 実行結果や LLMRunStream を扱わない。
- ConversationState と 1:1 のライフサイクルで生成される（ChatService が生成する）。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from domain.entities.chat_history import ChatHistory
from services.chat.constants import DEVELOPER_REQUEST_TYPES
from services.chat.conversation_state import ConversationState
from services.llm_service import AgentName
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.const import MAIN_CHAT_KEY
from utils.enum import LLMMessageRole, PageName
from utils.log_utils import get_session_id

if TYPE_CHECKING:
    from services.chat.chat_persistence import ChatPersistence
    from services.position_service import PositionService

logger = logging.getLogger(__name__)

# ターン入力準備プロンプトテンプレート（ポジション詳細画面初回）
_POSITION_DETAIL_INQUIRY_START_PROMPT = """指定ポジションは下記となります。ユーザーに求人情報について回答する時に、下記の内容を確認してください。

#求人情報
%s
#会社詳細情報
%s
#事業詳細情報
%s
#パラメータの補足解説\n下記は、各情報について、*どのパラメータを確認すると見つかりやすいか*を補足解説しています。
【必須】

##求人情報についての補足
どのような人が歓迎されるか: HREvaluationCompetency
どのような所がこの会社の魅力か: PR
会社名: Company要素内のName

##会社詳細情報についての補足
会社名: Prefectureの前にあるNameを確認してください。
何をしている会社か: Introduction,PR
特別な評価制度はあるか: HREvaluationSpecialSystem
福利厚生はどうか: Welfare,WelfareOther

##事業詳細についての補足
この会社の業界(業種)での立ち位置がわかります。
有形商材か無形商材か: Tangibleness"""


class TurnPreparer:
    """LLM ターン入力準備コンポーネント。

    ChatService から prepare_turn() を呼ばれ、ConversationState の
    conversation / active_agent_name を更新する。
    chat_key / position_id は呼び出し元の _resolve_chat_key() で事前設定される。

    ライフサイクル
    --------------
    - ChatService インスタンスと 1:1 で生成される。
    - set_toolcall_trace_message() は init_session() 完了後に 1 回呼ばれる。
    """

    def __init__(
        self,
        position_service: "PositionService",
        chat_persistence: "ChatPersistence",
        conv_state: ConversationState,
        agents: dict,
    ) -> None:
        self._position_service = position_service
        self._chat_persistence = chat_persistence
        self._conv_state = conv_state
        self._agents = agents
        # init_session() で設定されるツールコールトレースメッセージ。
        # ポジション詳細初回アクセス時に会話リストの先頭として使う。
        self._toolcall_trace_message: dict = {}

    def set_toolcall_trace_message(self, toolcall_trace_message: dict) -> None:
        """init_session() 完了後にツールコールトレースメッセージを設定する。"""
        self._toolcall_trace_message = toolcall_trace_message

    def get_message_role(self, request_type: ChatRequestType) -> LLMMessageRole:
        """リクエストタイプに応じた LLMMessageRole を返す。

        START / RESTART_CHAT / JOB_TYPES_SELECTED / JOB_TYPES_CLEAR /
        WORKFLOW_ANSWERS_SUBMITTED / WORKFLOW_CANCELLED は DEVELOPER、
        それ以外は USER を返す。
        """
        if request_type in DEVELOPER_REQUEST_TYPES:
            return LLMMessageRole.DEVELOPER
        return LLMMessageRole.USER

    async def prepare_turn(self, request: ChatRequestModel) -> None:
        """LLM ターン入力を準備し ConversationState を更新する。

        ConversationState の conversation / active_agent_name を更新する。
        chat_key / position_id は呼び出し元で事前設定済みであること（_resolve_chat_key 参照）。
        ポジション詳細初回アクセス時は
        ChatPersistence.save_chat_histories() を呼んで位置詳細メッセージを保存する。

        Args:
            request: フロントからのチャットリクエスト。

        Raises:
            ValueError: ポジション詳細取得失敗、または未知ページ指定。
        """
        session_id = get_session_id()
        current_page = request.current_page
        # `or None` はフロントから空文字列が来た場合の保護。
        encrypted_position_id = request.position_id or None

        if current_page == PageName.CHAT:
            # メインチャットページ
            # ポジション詳細からメインチャットに戻ってきた場合、アクティブエージェントを戻す
            if self._conv_state.active_agent_name == AgentName.POSITION_GUIDE:
                self._conv_state.active_agent_name = (
                    self._find_last_non_position_guide_agent()
                )
        elif current_page == PageName.POSITION_DETAIL and encrypted_position_id:
            # ポジション詳細ページ
            self._conv_state.active_agent_name = AgentName.POSITION_GUIDE
            self._create_position_agent_if_not_exist(self._conv_state.position_id)

            if self._conv_state.chat_key not in self._conv_state.conversation:
                (
                    position_detail,
                    company_detail,
                    business_detail,
                    error_message,
                ) = await self._get_position_detail(encrypted_position_id)

                if error_message:
                    logger.error(error_message)
                    raise ValueError(error_message)

                message = _POSITION_DETAIL_INQUIRY_START_PROMPT % (
                    json.dumps(position_detail),
                    json.dumps(company_detail),
                    json.dumps(business_detail),
                )

                self._conv_state.conversation[self._conv_state.chat_key] = [
                    self._toolcall_trace_message,
                    {
                        "type": "message",
                        "role": LLMMessageRole.DEVELOPER,
                        "content": message,
                    },
                ]
                chat_histories = [
                    ChatHistory(
                        session_id=session_id,
                        position_id=self._conv_state.position_id,
                        active_agent=AgentName.POSITION_GUIDE,
                        message_id=None,
                        role=LLMMessageRole.DEVELOPER,
                        content=message,
                    ),
                ]
                # ポジション詳細の開始メッセージは通常の会話ターン外なので即時保存する。
                await asyncio.to_thread(self._chat_persistence.save_chat_histories, chat_histories)
        elif current_page == PageName.POSITION_DETAIL:
            # encrypted_position_id was falsy — POSITION_DETAIL requires a position ID.
            error_msg = f"POSITION_DETAIL requires encrypted_position_id, got: {encrypted_position_id!r}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            error_msg = f"Unknown page: {current_page}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def _get_position_detail(
        self,
        encrypted_position_id: str,
    ) -> tuple[dict | None, dict | None, dict | None, str | None]:
        """ポジション詳細・会社詳細・業界詳細を取得する。

        Args:
            encrypted_position_id: 暗号化されたポジション UUID。

        Returns:
            (position_detail, company_detail, business_detail, error_message) の tuple。
            成功時 error_message は None。失敗時は (None, None, None, error_message)。
        """
        position_detail = await self._position_service.get_position_detail(
            encrypted_position_id,
        )
        if not position_detail:
            return (
                None,
                None,
                None,
                f"ポジション詳細が見つからなかった: {encrypted_position_id}",
            )

        company_detail = await self._position_service.get_company_detail(
            encrypted_position_id,
        )
        if not company_detail:
            return (
                None,
                None,
                None,
                f"会社詳細が見つからなかった: {encrypted_position_id}",
            )

        business_detail = await self._position_service.get_business_detail(
            encrypted_position_id,
        )
        if not business_detail:
            return (
                None,
                None,
                None,
                f"業界詳細が見つからなかった: {encrypted_position_id}",
            )

        return (position_detail, company_detail, business_detail, None)

    def _find_last_non_position_guide_agent(self) -> str:
        """メインチャット履歴から最後の POSITION_GUIDE 以外のアクティブエージェントを返す。

        Raises:
            ValueError: POSITION_GUIDE 以外のエージェントが履歴に見つからない場合。
        """
        histories = self._conv_state.chat_histories.get(MAIN_CHAT_KEY, [])
        for history in reversed(histories):
            if history.active_agent != AgentName.POSITION_GUIDE:
                return history.active_agent
        raise ValueError("POSITION_GUIDE以外のActive Agentが履歴に見つかりませんでした")

    def _create_position_agent_if_not_exist(self, position_id: object) -> None:
        """ポジション詳細エージェントが存在しない場合にクローンを作成する。

        Args:
            position_id: ポジション ID（str または None）。
        """
        position_id_str = str(position_id)
        if position_id_str not in self._agents:
            base_agent = self._agents.get(AgentName.POSITION_GUIDE)
            # 意図的に legacy と異なる: legacy は base_agent が None の場合に AttributeError を
            # 送出するが、init_session() 後は POSITION_GUIDE が必ず存在するため実害はない。
            if base_agent is not None:
                self._agents[position_id_str] = base_agent.clone()
