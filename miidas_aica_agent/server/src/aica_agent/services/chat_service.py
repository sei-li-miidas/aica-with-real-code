import asyncio
from contextlib import suppress
from dataclasses import asdict, is_dataclass
from datetime import datetime
from copy import deepcopy
import json
import re
import time
from typing import Any, AsyncGenerator
import uuid

from pathlib import Path
from openai.types.responses import ResponseTextDeltaEvent, ResponseOutputTextParam
from openai.types.responses.response_input_item_param import Message
from openai.types.responses.response_input_text_param import ResponseInputTextParam
from agents.items import ToolCallItemTypes
from agents import (
    Agent,
    HandoffCallItem,
    HandoffOutputItem,
    MessageOutputItem,
    ReasoningItem,
    RunItem,
    RunResultStreaming,
    Runner,
    ToolCallItem,
    ToolCallOutputItem,
)

from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from repositories.action_log_repo import ActionLogRepository, ActionLogType
from services.llm_service import AgentName, LLMService
from repositories.position_repo import PositionRepository
from repositories.chat_repo import ChatRepository
from repositories.user_repo import UserRepository
from security.llm_output_guard import (
    ForbiddenWordDetectedException,
    LLMOutputGuard,
)
from services.base_service import BaseService
from services.chat.service_protocol import ChatServiceProtocol
from services.position_service import PositionService
from services.rate_limit_service import RateLimitService
from services.conversation_summary_service import ConversationSummaryService
from services.workflow_service import WorkflowService
from services.summary_service import SummaryService
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import (
    ChatResponseType,
    ChatStreamResponse,
    ChatStreamResponseModel,
)
from utils.const import (
    APPLY_POSITION_IDS_KEY,
    INITIAL_MENU_WORKFLOW_ID,
    POSITION_SEARCH_FAKE_RESULT,
    MAIN_CHAT_KEY,
    RATE_LIMIT_EXCEEDED_MESSAGE,
    SESSION_START_MESSAGE,
)
from utils.crypt import decrypt
from utils.enum import EncryptKeyType, LLMMessageRole, LocationType, PageName, ToolName
from utils.env_utils import is_local_or_dev
from utils.log_utils import get_session_id, set_session_id


def _json_default(obj: object) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[attr-defined]
    if hasattr(obj, "dict"):
        return obj.dict()  # type: ignore[attr-defined]
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


DEFAULT_ERROR_MESSAGE = (
    "大変混み合っておりますので、しばらく経ってからリロードしてご利用ください。"
)
DEFAULT_LLM_FAIL_RESPONSE = "システムエラーが発生しました。"

POSITION_DETAIL_INQUIRY_START_PROMPT = """指定ポジションは下記となります。ユーザーに求人情報について回答する時に、下記の内容を確認してください。

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

POSITION_CHAT_DETAIL_MESSAGE_ID_PREFIX = "position_detail_chat_summary_"

MAX_LLM_RETRY_COUNT = 5


class PositionSearchRateLimitExceeded(Exception):
    """
    求人検索のレート制限が超過した際に発生する例外
    """


class ChatService(BaseService, ChatServiceProtocol):
    """
    LLM会話サービス
    """

    def __init__(
        self,
        position_svc: PositionService,
        llm_svc: LLMService,
        chat_repository: ChatRepository,
        position_repository: PositionRepository,
        user_repository: UserRepository,
        action_log_repository: ActionLogRepository,
        rate_limit_service: RateLimitService,
        workflow_service: WorkflowService,
        conversation_summary_svc: ConversationSummaryService,
        llm_output_guard: LLMOutputGuard | None = None,
        summary_service: SummaryService | None = None,
    ) -> None:
        """
        インスタンス初期化

        Args:
            position_svc: ポジションサービス
            llm_svc: LLMモデルサービス
            chat_repository: 会話履歴リポジトリ
            position_repository: ポジションデータリポジトリ
            user_repository: ユーザーリポジトリ
            action_log_repository: アクションログリポジトリ
            rate_limit_service: レート制限サービス
            workflow_service: ワークフローサービス
            llm_output_guard: 禁止ワード検知ガード。未指定時はローカルで初期化
            summary_service: 会話要約サービス。未指定時は要約機能を無効化
        """
        super().__init__()

        # LLMプロバイダー（OpenAI、Bedrock）
        self._provider: str | None = None
        self._position_service = position_svc
        self._llm_svc = llm_svc
        self._chat_repository = chat_repository
        self._position_repository = position_repository
        self._user_repository = user_repository
        self._action_log_repository = action_log_repository
        self._rate_limit_service = rate_limit_service
        self._workflow_service = workflow_service
        self._conversation_summary_svc = conversation_summary_svc
        self._summary_service = summary_service
        self._agents: dict[str, Agent] = {}

        # 禁止ワード検知器（DI注入優先。未注入時のみローカル初期化）
        self.llm_output_guard = (
            llm_output_guard if llm_output_guard is not None else LLMOutputGuard()
        )

        # 今会話しているエージェント
        self._active_agent_name: str = ""

        self._previous_response_ids: dict[str, str] = {}
        # 現在ターンの会話
        self._conversation: dict[str, list] = {}
        # すべての過去会話履歴
        self._chat_histories: dict[str, list[ChatHistory]] = {MAIN_CHAT_KEY: []}
        self._chat_key: str = MAIN_CHAT_KEY
        self._position_id: str | None = None
        # MAINチャット用の要約文脈キャッシュ（差分再構築用）
        self._summary_context_cache: dict[str, Any] | None = None
        # ポジション検索結果のカウント（ツールコールIDをキーとして保存）
        self._position_search_counts: dict[str, int] = {}

    def _run_streamed(
        self,
        *,
        starting_agent: Agent,
        input: list[Any],
        previous_response_id: str | None,
    ) -> RunResultStreaming:
        """Legacy seam for contract tests around the streamed runner call."""
        return Runner.run_streamed(
            starting_agent=starting_agent,
            input=input,
            previous_response_id=previous_response_id,
        )

    async def init_session(
        self,
        model_name: str,
    ) -> tuple[ChatSessionStatus, bool]:
        """
        セッション初期化。※セッションはwebsocket接続毎に１つ

        Args:
            model_name: LLMモデル名

        Returns:
            以下を含むtuple:
            - ChatSessionStatus: セッションのステータス
            - bool: 新規セッションかどうか
        """
        self._provider = model_name

        try:
            current_search_filter = await self._position_service.current_search_filter()
            current_tool_name = self._extract_position_search_tool_name(
                current_search_filter
            )
            current_jobtypes = self._extract_selected_jobtypes(current_search_filter)
            if current_tool_name:
                agents = self._llm_svc.clone_agents(
                    self._provider,
                    current_jobtypes,
                    current_tool_name,
                )
            else:
                agents = self._llm_svc.clone_agents(self._provider)
        except Exception:
            self.logger.exception(
                "Failed to load current search filter during init_session"
            )
            agents = self._llm_svc.clone_agents(self._provider)

        for agent_name, (agent, default_agent) in agents.items():
            self._agents[agent_name] = agent
            if default_agent:
                self._active_agent_name = agent_name
        self._toolcall_trace_message = {
            "type": "message",
            "role": LLMMessageRole.DEVELOPER,
            "content": f"""### ツール呼び出すときのパラメータについて
SessionID: {get_session_id()}を利用してください。
RequestID: Pythonの`uuid.uuid4()`を使って生成してください。
""",
        }

        try:
            is_new_session = True
            (chat_session, exists) = await asyncio.to_thread(
                self._chat_repository.init_chat_session
            )
            if chat_session:
                is_new_session = False
                if chat_session.histories:
                    # 以前の会話から続くため、会話履歴をロードして、LLMに渡す。
                    self._chat_histories, self._conversation = (
                        self._convert_to_llm_messages(chat_session.histories)
                    )
                    await self.build_summary_context(get_session_id())

                    # 既存セッションの再開なので、前回のアクティブエージェントを続いて利用する。
                    # POSITION_GUIDEでないAgentを探す
                    self._active_agent_name = self._find_last_non_position_guide_agent()

                    if self._active_agent_name not in self._agents:
                        # DefaultAgentのみと会話していたユーザーが再接続
                        # → 新規セッションとして扱い、initial_menuを表示する
                        set_session_id(str(uuid.uuid4()))
                        self._conversation = {}
                        self._chat_histories = {MAIN_CHAT_KEY: []}
                        is_new_session = True
                        self._active_agent_name = ""
                else:
                    # 初期メニューワークフロー実行時にエラーが発生してセッションだけ作られたケースの
                    # → 新規セッションとして扱い、initial_menuを表示する
                    set_session_id(str(uuid.uuid4()))
                    is_new_session = True

            elif exists:
                set_session_id(str(uuid.uuid4()))

            if MAIN_CHAT_KEY not in self._conversation or not self._conversation.get(
                MAIN_CHAT_KEY
            ):
                self._conversation[MAIN_CHAT_KEY] = [
                    self._toolcall_trace_message,
                ]

            if chat_session:
                return chat_session.status, is_new_session
            else:
                return ChatSessionStatus.CHATTING, is_new_session
        except Exception:
            self.logger.exception("セッション初期化失敗")
            return ChatSessionStatus.ERROR, False

    def _convert_to_llm_messages(
        self,
        histories: list[ChatHistory],
    ) -> tuple[dict[str, list[ChatHistory]], dict[str, list]]:
        """
        DB履歴でデータからLLM会話履歴作成。

        Args:
            histories: DB履歴でデータ

        Returns:
            chatキー毎の(DB会話履歴, LLM用会話履歴)
        """
        chat_histories: dict[str, list[ChatHistory]] = {}
        all_messages: dict[str, list] = {}

        for history in histories:
            if history.position_id:
                history_key = str(history.position_id)
                self._create_position_agent_if_not_exist(self._position_id)
            else:
                history_key = MAIN_CHAT_KEY

            chat_histories.setdefault(history_key, []).append(
                ChatRepository.clone_chat_history(history)
            )
            messages = all_messages.setdefault(history_key, [])

            if history.role in [LLMMessageRole.USER, LLMMessageRole.DEVELOPER]:
                messages.append(
                    {
                        "type": "message",
                        "role": history.role,
                        "content": history.content,
                    }
                )
            elif history.role == LLMMessageRole.ASSISTANT:
                messages.append(
                    {
                        "type": "message",
                        "role": history.role,
                        "content": [
                            ResponseOutputTextParam(
                                type="output_text",
                                text=history.content,
                            )
                        ],
                    }
                )
            elif history.role in [LLMMessageRole.TOOL, LLMMessageRole.HANDOFF]:
                messages.append(
                    {
                        "type": "function_call",
                        "call_id": history.tool_call_id,
                        "name": history.tool_name,
                        "arguments": json.dumps(history.tool_input),
                    }
                )

                output = history.content
                if not output:
                    # 念の為、もしツール実行結果が保存できてない場合
                    self.logger.warning(
                        "Tool output is empty: %s",
                        history,
                    )
                    output = "ツール実行結果がまだありません。"
                elif ToolName.is_position_search_tool(history.tool_name):
                    # ポジション検索実行結果ではなく、フェイク結果をLLMに渡す
                    try:
                        parsed_output = self._parse_tool_output(history.content)
                        position_ids = parsed_output.get("AllPositionIds") or []
                        positions_count = (
                            len(position_ids) if isinstance(position_ids, list) else 0
                        )
                        output = self._generate_position_search_fake_result(
                            positions_count
                        )
                    except Exception:
                        self.logger.exception(
                            "ポジション検索結果の復元に失敗しました。tool_call_id=%s",
                            history.tool_call_id,
                        )
                        output = POSITION_SEARCH_FAKE_RESULT
                elif history.tool_name in (
                    ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
                    ToolName.JOBTYPE_SEARCH_BY_NATURE,
                ):
                    try:
                        parsed_output = self._parse_tool_output(history.content)
                        jobtypes = self._process_jobtype_search_result(
                            history.tool_call_id or "",
                            history.tool_name,
                            json.dumps(history.tool_input, ensure_ascii=False),
                            parsed_output,
                        )
                        jobtypes_for_llm = (
                            json.dumps(
                                jobtypes.get("Jobtypes", []),
                                ensure_ascii=False,
                            )
                            if jobtypes
                            else "[]"
                        )
                    except Exception:
                        self.logger.exception(
                            "職種検索結果の復元に失敗しました。tool_call_id=%s",
                            history.tool_call_id,
                        )
                        jobtypes_for_llm = "[]"

                    output = f"""###職種一覧
{jobtypes_for_llm}

### その後の流れ
ユーザーに職種一覧を送りました。ユーザーが職種を選択済みなら、その職種向けの求人検索ツールを使ってください。選択が不明または未選択なら、職種選択を再度促してください。"""

                messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": history.tool_call_id,
                        "output": output,
                    }
                )
            elif history.role == LLMMessageRole.REASONING:
                # FIXME: 必要？
                pass
            else:
                self.logger.error("Unsupported message role: %s", history)
        return chat_histories, all_messages

    async def _handle_security_detection(
        self,
        error: Exception,
        session_id: str,
        session_status: ChatSessionStatus,
        chat_response: ChatStreamResponse,
        error_type: str = "",
    ) -> ChatStreamResponseModel:
        """
        セキュリティ検知時の共通処理

        Args:
            error: 検知された例外
            session_id: セッションID
            session_status: セッションステータス
            chat_response: チャットレスポンスオブジェクト
            error_type: エラータイプ（ログ用、例: "IN_STREAM", "IN_FINAL"）

        Returns:
            エラーレスポンス
        """
        try:
            if isinstance(error, ForbiddenWordDetectedException):
                # 禁止ワード検知（Trie木） → セッションブロック + 応答停止
                log_suffix = f"_{error_type}" if error_type else ""
                self.logger.warning(
                    "FORBIDDEN_WORD_DETECTED%s",
                    log_suffix,
                    extra={"stream_session_id": session_id, "word": error.word},
                )
            else:
                # 想定外のエラー
                self.logger.exception("Unexpected security check error")
                raise
        finally:
            # セッション状態をクリーンアップ（必ず実行）
            self.llm_output_guard.remove_session(session_id)

        # DBにブロックフラグを立てる
        try:
            await asyncio.to_thread(self._chat_repository.block_session)
        except Exception:
            self.logger.exception("block_session() failed")

        # エラーレスポンスを返す
        return chat_response.create_error_response(
            "不適切な出力を検知したので、応答をストップしました。",
            session_status,
        )

    async def chat(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """
        ユーザーインプットをLLMに渡して、レスポンスを返す。
        インプットごとに呼び出される

        Args:
            chat_request: フロントからのユーザーインプット
            client_ip: ユーザーのIPアドレス

        Returns:
            LLMレスポンス
        """
        self.logger.debug("Chat: %s", chat_request.model_dump(mode="json"))

        encrypted_position_id = chat_request.position_id or None
        message = chat_request.message
        session_status = await asyncio.to_thread(self._chat_repository.session_status)
        if not session_status:
            session_status = ChatSessionStatus.CHATTING

        # ========================================
        # セッションブロックチェック
        # インジェクション検知でブロックされたセッションは会話不可
        # ========================================
        if await asyncio.to_thread(self._chat_repository.is_session_blocked):
            self.logger.warning("BLOCKED_SESSION_ATTEMPT: %s", get_session_id())
            yield ChatStreamResponse(
                request_type=chat_request.request_type,
                position_id=encrypted_position_id,
            ).create_error_response(
                "不適切な出力が検知されたため、会話がブロックされています。",
                session_status,
            )
            return

        if (
            session_status
            in (ChatSessionStatus.REGISTERING, ChatSessionStatus.APPLYING)
            and chat_request.request_type == ChatRequestType.START
        ):
            # 面談応募／登録中は、メインチャットできないため、
            # 会話開始リクエストの場合、セッションステータスを返すだけで良い
            yield ChatStreamResponse(
                request_type=chat_request.request_type,
            ).create_end_response(
                session_status,
            )
            return

        try:
            # ========================================
            # 既存の処理続行
            # ========================================
            if encrypted_position_id:
                self._position_id = decrypt(
                    EncryptKeyType.POSITION,
                    encrypted_position_id,
                )
                self._chat_key = self._position_id
            else:
                self._position_id = None
                self._chat_key = MAIN_CHAT_KEY

            await self._prepare_for_chat_turn(
                chat_request,
            )
            if self._chat_key == MAIN_CHAT_KEY and not self._previous_response_ids.get(
                self._chat_key
            ):
                await self.build_summary_context(get_session_id())

            if self._chat_key not in self._conversation:
                yield ChatStreamResponse(
                    request_type=chat_request.request_type,
                    position_id=encrypted_position_id,
                ).create_end_response(
                    session_status,
                )
                return

            role = self._get_message_role(chat_request.request_type)

            self._conversation[self._chat_key].append(
                Message(
                    type="message",
                    role=role,
                    content=[ResponseInputTextParam(type="input_text", text=message)],
                ),
            )

            await self._save_user_or_developer_message(chat_request)
        except Exception:
            # LLM会話準備段階でエラーが発生した場合
            self.logger.exception("エラー発生しました。詳細はstack trace確認")
            yield ChatStreamResponse(
                request_type=chat_request.request_type,
                position_id=encrypted_position_id,
            ).create_error_response(
                DEFAULT_ERROR_MESSAGE,
                session_status,
            )
            return

        # 会話を続く（エラーが発生した場合）か、ユーザーへレスポンスする（正常の場合）かのフラグ
        llm_error = False
        base_delay_seconds = 0.5
        for attempt in range(MAX_LLM_RETRY_COUNT):
            stop_at_tool_exists = False
            llm_error = False
            tool_calls: dict[ToolName, ToolCallItemTypes] = {}
            run_result: RunResultStreaming | None = None
            session_id: str | None = None
            stream_session_id: str | None = None
            try:
                chat_response = ChatStreamResponse(
                    request_type=chat_request.request_type,
                    position_id=encrypted_position_id,
                )

                self.logger.debug(
                    "last message: %s", self._conversation[self._chat_key][-1]
                )
                start_time = time.time()
                run_result = self._run_streamed(
                    starting_agent=self._get_agent(self._active_agent_name),
                    input=self._conversation[self._chat_key],
                    previous_response_id=self._previous_response_ids.get(
                        self._chat_key
                    ),
                )
                # ResponseAPIなので、以前のINPUTを削除
                self._conversation[self._chat_key] = []

                # ========================================
                # LLMインジェクション対策: ストリーミングセキュリティ
                # ========================================
                # - Trie木による禁止ワードのリアルタイム検知（O(1)文字探索）
                # - セッションごとの状態管理（100同時接続対応）
                # - 各LLM応答ごとにバッファをリセット（会話ターン独立）
                current_item_id = None  # item_idを保持
                session_id = get_session_id()  # セッションID取得
                stream_session_id = session_id
                # 1つのリクエストに対して内容が近いレスポンスが複数来る問題対応
                # https://community.openai.com/t/how-to-prevent-the-api-returning-multiple-outputs/1251365/29
                # 必ず
                # ストリーミングメッセージ1のraw_response_event -> 完了 -> ストリーミングメッセージ1のrun_item_stream_event（保存）
                #  -> ストリーミングメッセージ2のraw_response_event -> 完了 -> ストリーミングメッセージ2のrun_item_stream_event（保存）
                # という順ではなく、
                # ストリーミングメッセージ1のraw_response_event -> 完了 -> ストリーミングメッセージ2のraw_response_event -> 完了
                #  -> ストリーミングメッセージ1のrun_item_stream_event（保存） -> ストリーミングメッセージ2のrun_item_stream_event（保存）
                # もありえますので、ストリーミングメッセージ1のrun_item_stream_event（保存）時点で受信済みフラグ設定はもう遅い
                # そのため、ストリーミング開始したメッセージレスポンスIDで判断します
                received_message_id = None

                # 新しいLLM応答の開始時にバッファをリセット
                # （1回目、2回目、3回目の会話ターンで独立してチェック）
                self.llm_output_guard.reset_session_for_new_response(session_id)
                async for event in run_result.stream_events():
                    if event.type == "raw_response_event":
                        # メッセージの場合
                        if isinstance(event.data, ResponseTextDeltaEvent):
                            if not received_message_id:
                                # ストリーミング受信開始したメッセージID
                                received_message_id = event.data.item_id
                            elif received_message_id != event.data.item_id:
                                # すでに受信したメッセージのIDと異なるメッセージが来た場合、無視
                                continue

                            if event.data.delta:
                                # item_idを保持
                                current_item_id = event.data.item_id

                                # ========================================
                                # ストリーミングセキュリティチェック
                                # - Trie木: 禁止ワードをO(1)でリアルタイム検知
                                # - 安全確認された文字列のみをユーザーに送信
                                # ========================================
                                try:
                                    safe_chunks = (
                                        self.llm_output_guard.process_stream_chunk(
                                            session_id=session_id,
                                            chunk=event.data.delta,
                                        )
                                    )

                                    # 安全確認された文字列のみ送信
                                    for safe_chunk in safe_chunks:
                                        response_chunk = (
                                            chat_response.create_agent_message_response(
                                                current_item_id,
                                                safe_chunk,
                                                session_status,
                                            )
                                        )
                                        yield response_chunk
                                        await asyncio.sleep(
                                            0.001
                                        )  # 1ms - ストリーミング体験向上

                                except ForbiddenWordDetectedException as stream_error:
                                    # セキュリティ検知時のエラーハンドリング
                                    yield await self._handle_security_detection(
                                        stream_error,
                                        session_id,
                                        session_status,
                                        chat_response,
                                        error_type="IN_STREAM",
                                    )
                                    return
                    elif event.type == "run_item_stream_event":
                        # イベント（LLMメッセージ受信完了やツール実行）の場合
                        # まずLLMレスポンス保存
                        await self._save_chat_history(event.item)

                        if isinstance(event.item, ToolCallItem):
                            stop_at_tool_exists = (
                                stop_at_tool_exists or self._is_stop_at_tool(event.item)
                            )

                            # ツール実行開始（処理対象は、ToolNameに定義されているツールのみ）
                            await self._handle_tool_call_item(
                                event.item,
                                tool_calls,
                                client_ip,
                            )
                        elif isinstance(event.item, ToolCallOutputItem):
                            # 処理対象ツールかどうか
                            tool_call_id = event.item.raw_item["call_id"]
                            tool_call = next(
                                (
                                    (tool_name, item)
                                    for tool_name, item in tool_calls.items()
                                    if item.call_id == tool_call_id
                                ),
                                None,
                            )
                            if tool_call:
                                # 処理対象は、ToolNameに定義されているツールのみ
                                parsed_output = self._parse_tool_output(
                                    event.item.raw_item["output"]
                                )

                                if "Message" in parsed_output:
                                    # "Message"キーが入っている場合、失敗とみなす
                                    # ツール実行失敗の場合、エラー扱いしないので、エラーログ出力しない
                                    self.logger.warning(
                                        "ツール実行失敗: %s", event.item.raw_item
                                    )
                                    # LLMに処理してもらう
                                    message_to_llm = f"""{parsed_output["Message"]}
### SessionIDかRequestIDが設定されていないエラーの場合、
SessionID: {get_session_id()}
RequestID: {uuid.uuid4()}
を使ってください。
"""
                                    self._conversation[self._chat_key].append(
                                        {
                                            "type": "function_call_output",
                                            "call_id": tool_call_id,
                                            "output": message_to_llm,
                                        }
                                    )
                                    llm_error = True
                                else:
                                    # ツール実行成功の場合
                                    match tool_call[0]:
                                        # TODO: ツールが増えたら、長くなる
                                        case (
                                            ToolName.GENERIC_POSITION_SEARCH
                                            | ToolName.IT_POSITION_SEARCH
                                            | ToolName.FINANCIAL_SALES_POSITION_SEARCH
                                        ):
                                            # ポジション検索結果
                                            # 分析用のログ出力
                                            # ポジション検索ツール結果分析し、結果をLLMに渡さず、直接フロントに返す。
                                            position_search_result = self._position_repository.process_position_search_result(
                                                tool_call_id,
                                                parsed_output,
                                            )
                                            yield chat_response.create_tool_result_response(
                                                tool_call_id,
                                                ChatResponseType.POSITION_SEARCH_RESULT,
                                                position_search_result,
                                                session_status,
                                            )

                                            # フェークのポジション検索結果を次ターンでユーザーメッセージと一緒に送るため
                                            position_ids = (
                                                parsed_output.get("AllPositionIds")
                                                or []
                                            )
                                            positions_count = (
                                                len(position_ids)
                                                if isinstance(position_ids, list)
                                                else 0
                                            )
                                            self._position_search_counts[
                                                tool_call_id
                                            ] = positions_count
                                            # stop_at_tool の function_call_output は finally 側でも
                                            # run_result.to_input_list() から回収できる前提なので、
                                            # ここでは即時に self._conversation へ積まない。
                                            # 先に積むと、finally 側の回収と責務が二重になり、
                                            # どちらが正なのか分かりづらくなる。
                                            # fake_result = self._generate_position_search_fake_result(
                                            #     positions_count
                                            # )
                                            # # self._conversation[self._chat_key].append(
                                            #     {
                                            #         "type": "function_call_output",
                                            #         "call_id": tool_call_id,
                                            #         "output": fake_result,
                                            #     }
                                            # )
                                        case ToolName.JOBTYPE_SEARCH_BY_KEYWORDS:
                                            jobtypes_search_result = (
                                                self._process_jobtype_search_result(
                                                    tool_call_id,
                                                    tool_call[0],
                                                    tool_call[1].arguments,
                                                    parsed_output,
                                                )
                                            )
                                            if jobtypes_search_result:
                                                yield chat_response.create_tool_result_response(
                                                    tool_call_id,
                                                    ChatResponseType.JOBTYPE_SEARCH_RESULT,
                                                    jobtypes_search_result,
                                                    session_status,
                                                )

                                                # ここで break すると、この turn で既に発行済みの他ツールの
                                                # ToolCallOutputItem まで読み切れず、DB に保存されないことがある。
                                                # 例:
                                                # 1. ToolCallItem(search_occupations_by_sentence)
                                                # 2. ToolCallItem(search_industries_by_sentence)
                                                # 3. ToolCallOutputItem(search_occupations_by_sentence)
                                                # 4. ここで break
                                                # 5. ToolCallOutputItem(search_industries_by_sentence) が未処理になり、
                                                #    tool call と結果の履歴が欠ける。
                                                # そのため stop_at_tool の結果は先にユーザーへ返しても、
                                                # stream 自体は最後まで読み切って全ツール結果を保存する。
                                        case ToolName.START_WORKFLOW:
                                            workflow_id = parsed_output.get(
                                                "WorkflowID"
                                            )
                                            if workflow_id == INITIAL_MENU_WORKFLOW_ID:
                                                self.logger.warning(
                                                    "start_workflow に initial_menu が渡されました。スキップします。"
                                                )
                                                continue
                                            if workflow_id:
                                                try:
                                                    definition = self._workflow_service.get_definition(
                                                        str(workflow_id)
                                                    )
                                                    yield chat_response.create_tool_result_response(
                                                        tool_call_id,
                                                        ChatResponseType.WORKFLOW,
                                                        definition.model_dump(
                                                            by_alias=True
                                                        ),
                                                        session_status,
                                                    )
                                                except (
                                                    ValueError,
                                                    FileNotFoundError,
                                                ) as e:
                                                    self.logger.error(
                                                        "ワークフロー定義の取得に失敗しました: %s, %s",
                                                        workflow_id,
                                                        e,
                                                    )
                                                    yield chat_response.create_error_response(
                                                        "ワークフローが実行できませんでした。",
                                                        session_status,
                                                    )
                                        case ToolName.APPLICATION:
                                            # 応募
                                            if session_status in (
                                                ChatSessionStatus.REGISTERED,
                                                ChatSessionStatus.APPLIED,
                                            ):
                                                # TODO: すでに会員登録済みの場合、応募する
                                                # ログイン済みクッキー情報をフロントからもらう必要
                                                pass
                                            elif (
                                                session_status
                                                == ChatSessionStatus.APPLYING
                                            ):
                                                # TODO: 応募中の場合、応募ポジション追加
                                                # フロントでも応募ボタンステータス変更の必要もある
                                                pass
                                            elif (
                                                session_status
                                                == ChatSessionStatus.REGISTERING
                                            ):
                                                # TODO: 会員登録中の場合、応募ポジション追加＆セッションステータス変更
                                                # フロントでも応募ボタンステータス変更の必要もある
                                                pass
                                            elif (
                                                chat_request.current_page
                                                == PageName.POSITION_DETAIL
                                            ):
                                                # ポジション詳細ページしかできない
                                                real_id = decrypt(
                                                    EncryptKeyType.POSITION,
                                                    encrypted_position_id,
                                                )
                                                await asyncio.to_thread(
                                                    self._user_repository.update_miidas_registration_user_data,
                                                    APPLY_POSITION_IDS_KEY,
                                                    [real_id],
                                                )

                                                await asyncio.to_thread(
                                                    self._chat_repository.update_session_status,
                                                    ChatSessionStatus.APPLYING,
                                                )

                                                session_status = (
                                                    ChatSessionStatus.APPLYING
                                                )
                                            else:
                                                self.logger.error(
                                                    "ポジション詳細ページ以外からの応募: %s",
                                                    chat_request.current_page,
                                                )
                                        case ToolName.REGISTRATION:
                                            # 登録
                                            if (
                                                session_status
                                                != ChatSessionStatus.CHATTING
                                            ):
                                                # すでに会員登録ずみなので、無視
                                                # TODO: V2の時に、ログインに誘導する
                                                pass

                                            current_page = chat_request.current_page
                                            if (
                                                current_page == PageName.CHAT
                                                or current_page
                                                == PageName.POSITION_DETAIL
                                            ):
                                                # 分析用のログ出力
                                                await asyncio.to_thread(
                                                    self._action_log_repository.insert,
                                                    log_type=ActionLogType.REGISTRATION,
                                                    source=current_page,
                                                )

                                                session_status = (
                                                    ChatSessionStatus.REGISTERING
                                                )
                                                await asyncio.to_thread(
                                                    self._chat_repository.update_session_status,
                                                    session_status,
                                                )
                                            else:
                                                self.logger.error(
                                                    "知らないページ以外からの会員登録: %s",
                                                    current_page,
                                                )
                        elif isinstance(event.item, HandoffOutputItem):
                            # Agentハンドオフ
                            self._active_agent_name = event.item.target_agent.name

                # ========================================
                # ストリーミング終了時の最終処理
                #
                # 1. Trie木の保留バッファ解放
                #    - ストリーミング中に禁止ワードの途中一致で保留された文字列
                #    - 応答終了 = 完全一致しなかった = 安全確定 → ユーザーに送信
                #    - 例: "trans" (保留) → 応答終了 → "transfer"ではない → 送信OK
                # ========================================
                try:
                    final_chunks = self.llm_output_guard.finalize_stream(session_id)

                    # 残りの安全な文字列を送信
                    for final_chunk in final_chunks:
                        if current_item_id:
                            response_chunk = (
                                chat_response.create_agent_message_response(
                                    current_item_id,
                                    final_chunk,
                                    session_status,
                                )
                            )
                            yield response_chunk

                except ForbiddenWordDetectedException as final_error:
                    # 最終チェックでのセキュリティ検知
                    yield await self._handle_security_detection(
                        final_error,
                        session_id,
                        session_status,
                        chat_response,
                        error_type="IN_FINAL",
                    )
                    return

                end_time = time.time()
                elapsed = end_time - start_time
                self.logger.info(
                    "chat_service.py: chat turn took %.2f seconds.", elapsed
                )

                token_usage = run_result.context_wrapper.usage
                token_usage_str = json.dumps(token_usage, default=_json_default)

                # 分析用のログ出力
                # 挨拶だけの場合、chat_historiesに保存しないので、トークン使用詳細をaction_logテーブルに保存します。
                await asyncio.to_thread(
                    self._action_log_repository.insert,
                    log_type=ActionLogType.TOKEN_USAGE,
                    source=chat_request.current_message_id,
                    content=token_usage_str,
                )

                if is_local_or_dev():
                    yield chat_response.create_token_usage_response(
                        f"\nToken Usage: {token_usage_str}",
                        session_status,
                    )

                if not llm_error:
                    if self._summary_service and self._chat_key == MAIN_CHAT_KEY:
                        try:
                            await self._summary_service.check_should_start_summary(
                                get_session_id(),
                            )
                        except Exception:
                            self.logger.exception("会話要約起動判定に失敗")
                    # 正常に会話が行われた場合、会話終了
                    break

            except GeneratorExit:
                # chat() の呼び出し元が async generator を aclose() すると、
                # 通常の finalize_stream() まで到達せずここへ入る。
                # ストリーム途中で作った LLMOutputGuard の session state は
                # chat() 側が所有している。close 時点の ContextVar は呼び出し元で
                # 変更済みの可能性があるため、stream 開始時に捕捉した ID を使う。
                if stream_session_id:
                    with suppress(Exception):
                        self.llm_output_guard.remove_session(stream_session_id)
                raise
            except PositionSearchRateLimitExceeded as rate_limit_error:
                yield chat_response.create_error_response(
                    str(rate_limit_error),
                    session_status,
                )
                return
            # エラーが発生して、LLMに処理して貰う場合、会話続く
            except Exception:
                self.logger.exception("エラー発生しました。詳細はstack trace確認")
                # LLM会話中エラーが発生した場合、リトライ
                self._conversation[self._chat_key].append(
                    {
                        "type": "message",
                        "role": LLMMessageRole.DEVELOPER,
                        "content": DEFAULT_LLM_FAIL_RESPONSE,
                    }
                )
                await self._save_llm_error(DEFAULT_LLM_FAIL_RESPONSE)
            finally:
                if session_id:
                    self.llm_output_guard.remove_session(session_id)

                if run_result:
                    if run_result.last_response_id:
                        # OpenAI 側の response chain が確立していれば、ローカル後処理で例外になっても
                        # 次回リトライは最新 chain を継続する必要がある。
                        self._previous_response_ids[self._chat_key] = (
                            run_result.last_response_id
                        )

                    if run_result.last_agent:
                        self._active_agent_name = run_result.last_agent.name

                    self._append_stop_at_tool_outputs(
                        run_result,
                        stop_at_tool_exists,
                        tool_calls,
                    )

            # 次の試行に向けて指数バックオフで待機
            if attempt < MAX_LLM_RETRY_COUNT - 1 and llm_error:
                # TODO: リトライ回数の多い場合、一度ユーザーになにかのメッセージを送信？
                delay = base_delay_seconds * (2**attempt)
                # 上限は8秒に制限
                delay = min(delay, 8.0)
                self.logger.info(
                    "chat_service.py: retrying with backoff %.2f s (attempt %d/%d)",
                    delay,
                    attempt + 1,
                    MAX_LLM_RETRY_COUNT,
                )
                await asyncio.sleep(delay)
        else:
            # リトライを全部消費した場合、エラーとみなす
            llm_error = True

        if llm_error:
            # リトライしても失敗
            yield chat_response.create_error_response(
                DEFAULT_ERROR_MESSAGE,
                session_status,
            )
        else:
            # 会話が正常に行われた
            yield chat_response.create_end_response(
                session_status,
            )

    def _is_stop_at_tool(self, item: ToolCallItem) -> bool:
        """return directツールかどうか"""
        if not isinstance(item.agent.tool_use_behavior, dict):
            return False
        if "stop_at_tool_names" not in item.agent.tool_use_behavior or not isinstance(
            item.agent.tool_use_behavior["stop_at_tool_names"], list
        ):
            return False
        return item.raw_item.name in item.agent.tool_use_behavior["stop_at_tool_names"]

    async def build_summary_context(self, session_id: str) -> None:
        """
        最新 completed 要約と境界以降履歴からメインチャット文脈を再構築する。
        """
        if self._summary_service is None or self._chat_key != MAIN_CHAT_KEY:
            return

        latest_completed = await asyncio.to_thread(
            self._summary_service.get_latest_completed, session_id
        )
        summary_id = int(latest_completed.summary_id) if latest_completed else None
        boundary_id = (
            int(latest_completed.summary_until_history_id) if latest_completed else 0
        )

        cache = self._summary_context_cache
        can_incremental = (
            cache is not None
            and cache.get("session_id") == session_id
            and cache.get("summary_id") == summary_id
            and cache.get("boundary_id") == boundary_id
        )

        if can_incremental:
            last_history_id = int(cache.get("last_history_id", boundary_id))
            new_histories = await asyncio.to_thread(
                self._summary_service.get_histories_after,
                session_id,
                last_history_id,
            )
            if new_histories:
                new_chat_histories, new_all_messages = self._convert_to_llm_messages(
                    new_histories
                )
                cache_chat_histories: list[ChatHistory] = cache.get(
                    "chat_histories", []
                )
                cache_chat_histories.extend(new_chat_histories.get(MAIN_CHAT_KEY, []))

                new_messages = self._remove_tool_trace_message(
                    new_all_messages.get(MAIN_CHAT_KEY, [])
                )
                cache_conversation: list[dict[str, Any]] = cache.get("conversation", [])
                cache_conversation.extend(new_messages)
                cache["last_history_id"] = max(int(h.id) for h in new_histories)

            self._chat_histories[MAIN_CHAT_KEY] = deepcopy(
                cache.get("chat_histories", [])
            )
            self._conversation[MAIN_CHAT_KEY] = deepcopy(cache.get("conversation", []))
            return

        # ここでreturnしない場合は、下記の通常ルートで必ずフル再構築する。
        # latest_completed があれば要約も反映される。
        if latest_completed and latest_completed.summary_text:
            main_histories = await asyncio.to_thread(
                self._summary_service.get_histories_after,
                session_id,
                boundary_id,
            )
        else:
            main_histories = await asyncio.to_thread(
                self._chat_repository.get_main_chat_histories
            )

        chat_histories, all_messages = self._convert_to_llm_messages(main_histories)
        self._chat_histories[MAIN_CHAT_KEY] = chat_histories.get(MAIN_CHAT_KEY, [])

        messages = self._remove_tool_trace_message(all_messages.get(MAIN_CHAT_KEY, []))

        rebuilt_conversation: list[dict[str, Any]] = [self._toolcall_trace_message]
        # 増分更新不可時の通常ルート。要約があれば developer メッセージとして挿入する。
        if latest_completed and latest_completed.summary_text:
            rebuilt_conversation.append(
                {
                    "type": "message",
                    "role": LLMMessageRole.DEVELOPER,
                    "content": (
                        "###過去会話の要約\n"
                        f"{latest_completed.summary_text}\n\n"
                        "### 指示\n"
                        "この要約は、これまでの会話内容を短くまとめたものです。"
                        "このメッセージの後ろに続く会話履歴は、要約より新しいユーザーとの生会話です。"
                        "要約と生会話に矛盾や重複がある場合は、必ず生会話（より新しい発話）を優先して応答を生成してください。"
                    ),
                }
            )
        rebuilt_conversation.extend(messages)
        self._conversation[MAIN_CHAT_KEY] = rebuilt_conversation

        self._summary_context_cache = {
            "session_id": session_id,
            "summary_id": summary_id,
            "boundary_id": boundary_id,
            "last_history_id": (
                max(int(history.id) for history in main_histories)
                if main_histories
                else boundary_id
            ),
            "chat_histories": deepcopy(self._chat_histories[MAIN_CHAT_KEY]),
            "conversation": deepcopy(rebuilt_conversation),
        }

    def _remove_tool_trace_message(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        return [
            message
            for message in messages
            if not (
                isinstance(message, dict)
                and message.get("type") == "message"
                and message.get("role") == LLMMessageRole.DEVELOPER
                and message.get("content") == self._toolcall_trace_message["content"]
            )
        ]

    def _append_stop_at_tool_outputs(
        self,
        run_result: RunResultStreaming,
        stop_at_tool_exists: bool,
        tool_calls: dict[ToolName, ToolCallItemTypes],
    ) -> None:
        """stop_at_tool時に次ターンへ渡す function_call_output を会話履歴へ追加する。"""
        # return directツールが存在する場合、LLMへのツールアウトプットを手動設定する必要があります？
        # 以前設定しないとエラーが発生してましたが、いま大丈夫そう
        # 一旦念の為、このロジックを残す。
        # また試して、特に設定しても問題なさそうですが、
        # ここやってもやらなくても、Traceではツール結果レスポンスは１回だけ
        # たぶんOpenAIが対応してくれてるかと思われます。
        if not stop_at_tool_exists:
            return

        conversation = self._conversation.get(self._chat_key)
        for item in run_result.to_input_list():
            if item.get("type") != "function_call_output" or "call_id" not in item:
                continue

            call_id = item["call_id"]

            if any(
                ToolName.is_position_search_tool(tool_name)
                and call_id == tool_call.call_id
                for tool_name, tool_call in tool_calls.items()
            ):
                # フェークのポジション検索結果を次ターンでユーザーメッセージと一緒に送るため
                if any(
                    conv_item.get("call_id") == call_id for conv_item in conversation
                ):
                    continue
                positions_count = self._position_search_counts.get(call_id, 0)
                fake_result = self._generate_position_search_fake_result(
                    positions_count
                )
                conversation.append(
                    {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": fake_result,
                    }
                )
            elif (
                ToolName.JOBTYPE_SEARCH_BY_KEYWORDS in tool_calls
                and call_id == tool_calls[ToolName.JOBTYPE_SEARCH_BY_KEYWORDS].call_id
            ):
                if any(
                    conv_item.get("call_id") == call_id for conv_item in conversation
                ):
                    continue
                conversation.append(
                    {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": f"""
職種名検索ツールの実行されています。ツールが選定したユーザーの希望に合う職種リストをユーザーに提示しています。ユーザーは現在、そのリストの中から希望職種を選択しています。ユーザーから希望職種が届いたら、求人検索ツールを使って求人検索を実行してください。ただし、希望勤務地、希望年収の確認がまだできていない場合は、先にユーザーに確認した後に、求人検索を行ってください。
###ツールが選定した職種一覧
{item["output"]}
""",
                    }
                )
            else:
                conversation.append(item)

    # FIXME: バックエンドで処理していますが、LLMがサマル作成に時間がかかる場合、会話をブロックしてしまいます。
    # ユーザーがメッセージを送っても、アプリが反応しなくなるように見えます。
    async def summarize_position_detail_chat(
        self,
        chat_request: ChatRequestModel,
    ) -> ChatSessionStatus:
        encrypted_position_id = chat_request.position_id
        if encrypted_position_id:
            try:
                self._position_id = decrypt(
                    EncryptKeyType.POSITION,
                    encrypted_position_id,
                )
            except Exception:
                self.logger.exception(
                    "Failed to decrypt position id: %s",
                    encrypted_position_id,
                )
                return await asyncio.to_thread(self._chat_repository.session_status)
        else:
            self.logger.info("No position id found")
            return await asyncio.to_thread(self._chat_repository.session_status)

        position_chat_histories = self._chat_histories.get(self._position_id, [])
        if not position_chat_histories:
            self.logger.info(
                "No position chat histories found: %s",
                self._position_id,
            )
            return await asyncio.to_thread(self._chat_repository.session_status)

        # devでのサマリ結果がおかしいので、調査ログ追加
        self.logger.info(
            "Summarizing position detail chat: %s, %s, %s, %s",
            get_session_id(),
            self._position_id,
            len(position_chat_histories),
            [history.id for history in position_chat_histories],
        )

        summary_text = (
            await self._conversation_summary_svc.summarize_position_detail_chat(
                position_chat_histories,
            )
        )
        if not summary_text:
            self.logger.error(
                "OpenAI summary response contained no text: %s, %s",
                get_session_id(),
                self._position_id,
            )
            return await asyncio.to_thread(self._chat_repository.session_status)

        # message_idを生成（タイムスタンプを使用）
        timestamp = int(datetime.now().timestamp())
        message_id = (
            f"{POSITION_CHAT_DETAIL_MESSAGE_ID_PREFIX}{self._position_id}_{timestamp}"
        )

        # LLMから返答をもらった後DBに保存するのは、ユーザーからのメッセージとLLMからの返答のみ、
        # また、ポジション詳細からメインチャットに戻った後、ユーザーはもうメッセージを送ってくれない可能性もあります。
        # なので、いまサマリをDBに保存するしかない
        await self._save_chat_histories(
            [
                ChatHistory(
                    session_id=get_session_id(),
                    position_id=None,
                    active_agent=AgentName.POSITION_GUIDE,
                    message_id=message_id,
                    role=LLMMessageRole.DEVELOPER,
                    content=summary_text,
                )
            ]
        )

        # ポジション詳細から戻ってきた時点では、LLMからの返答が必要ないので、いますぐさまった情報をLLMに送らず、メインチャット会話履歴を入れたら終わり
        # 次のメインチャットでのユーザーからのメッセージが来たら、一緒にLLMに送る。
        self._conversation[MAIN_CHAT_KEY].append(
            {
                "type": "message",
                "role": LLMMessageRole.DEVELOPER.value,
                "content": [
                    ResponseInputTextParam(
                        type="input_text",
                        text=summary_text,
                    )
                ],
            }
        )

        return await asyncio.to_thread(self._chat_repository.session_status)

    async def _prepare_for_chat_turn(
        self,
        input: ChatRequestModel,
    ):
        """
        フロントからのINPUT解析

        Args:
            input: フロントからのINPUT
            ChatSessionStatus: セッションステータス
        """
        session_id = get_session_id()
        current_page = input.current_page
        encrypted_position_id = input.position_id or None
        message = input.message

        if current_page == PageName.CHAT:
            # `/chat`
            # OR
            # if prev_page == PageName.POSITION_DETAIL:
            # `/positions/{position_id}` => `/chat`
            if self._active_agent_name == AgentName.POSITION_GUIDE:
                # ポジション詳細画面でチャットしてからメインチャットに戻ってきた場合、強制的にアクティブAgentを戻します。
                self._active_agent_name = self._find_last_non_position_guide_agent()
        elif current_page == PageName.POSITION_DETAIL and encrypted_position_id:
            # `/chat` => `/positions/{position_id}`
            self._active_agent_name = AgentName.POSITION_GUIDE
            self._create_position_agent_if_not_exist(self._position_id)

            if not self._conversation.get(self._chat_key):
                (
                    position_detail,
                    company_detail,
                    business_detail,
                    error_message,
                ) = await self._get_position_detail(encrypted_position_id)

                if error_message:
                    self.logger.error(error_message)
                    raise ValueError(error_message)

                # 当初の想定ではポジション詳細をLLMに伝えるにはシステムプロンプトを利用できるようになるのはポジション詳細Agentクローンのメリットの1つかと思ってましたが、
                # 中村さんと相談（https://miidas-dev.slack.com/archives/C08BU50QS3Y/p1751329093253549?thread_ts=1750744115.699779&cid=C08BU50QS3Y）して、
                # 「求人詳細については一旦今のまま(developerロールでのメッセージ扱い)が安定しそうです！」なので、システムプロンプトの利用はをやめました。
                message = POSITION_DETAIL_INQUIRY_START_PROMPT % (
                    json.dumps(position_detail),
                    json.dumps(company_detail),
                    json.dumps(business_detail),
                )

                self._conversation[self._chat_key] = [
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
                        position_id=self._position_id,
                        active_agent=AgentName.POSITION_GUIDE,
                        message_id=None,
                        role=LLMMessageRole.DEVELOPER,
                        content=message,
                    ),
                ]
                # 現在DB保存対象となるのは、LLMから返答をもらった後の、ユーザーからのメッセージとLLMからの返答のみです。
                # つまり、そのときは上記2つのメッセージは保存対象ではないので、ここでDBに保存します。
                await self._save_chat_histories(chat_histories)
        else:
            error_msg = f"Unknown page: {current_page}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    def _serialize_tool_output_for_storage(
        self,
        output: Any,
    ) -> str:
        if isinstance(output, str):
            return output
        return json.dumps(output, ensure_ascii=False, default=_json_default)

    def _parse_tool_output(
        self,
        output: Any,
    ) -> dict:
        """
        ツール結果解析

        Args:
            output: 生のツール結果

        Returns:
            解析後のツール結果
        """
        self.logger.debug("ツールのoutput: %s", output)
        outer_result = output
        if isinstance(output, str):
            try:
                outer_result = json.loads(output)
            except (json.JSONDecodeError, TypeError):
                self.logger.exception(
                    "ツールのoutputのJSON解析に失敗しました. 入力: %s",
                    output,
                )
                return {}

        if isinstance(outer_result, dict):
            inner_result = outer_result.get("text", outer_result)
        elif isinstance(outer_result, list):
            if not outer_result:
                self.logger.warning("ツールのoutputリストが空です")
                return {}
            first_item = outer_result[0]
            if not isinstance(first_item, dict):
                self.logger.error(
                    "ツールのoutputリスト先頭要素はdictである必要があります: %s",
                    type(first_item).__name__,
                )
                return {}
            inner_result = first_item.get("text", first_item)
        else:
            self.logger.error(
                "ツールのoutputはlist/dictまたはJSON文字列である必要があります: %s",
                type(outer_result).__name__,
            )
            return {}

        if isinstance(inner_result, dict):
            return inner_result
        if not isinstance(inner_result, str):
            self.logger.error(
                "ツールのoutputの'text'フィールドは文字列またはdictではありません: %s",
                output,
            )
            return {}
        try:
            return json.loads(inner_result)
        except (json.JSONDecodeError, TypeError):
            self.logger.exception(
                "ツールのoutputの'text'フィールドのJSON解析に失敗しました. 入力: %s",
                inner_result,
            )
            return {}

    def _generate_position_search_fake_result(self, count: int) -> str:
        """
        ポジション検索のフェイク結果メッセージを生成

        Args:
            count: 検索結果の件数

        Returns:
            フェイク結果メッセージ
        """
        return f"{count}件の求人が見つかりました。ユーザーには別の手段で求人の検索結果を見せていますが、ユーザーから条件変更や再度見たいとの要望があれば、検索条件の差異に関わらず、再度このツールを実行してください。"

    async def _handle_tool_call_item(
        self,
        item: ToolCallItem,
        tool_calls: dict[ToolName, ToolCallItemTypes],
        client_ip: str,
    ):
        """
        指定ツールコールの記録・処理

        Args:
            item: ツールコール入力
            tool_calls: 該当会話中のツールコール

        Returns:
        """
        try:
            tool_name = ToolName(item.raw_item.name)
            tool_calls[tool_name] = item.raw_item
        except ValueError:
            # 処理対象外ツールなので、無視
            return

        if ToolName.is_position_search_tool(tool_name):
            await self._ensure_tool_execution_available(client_ip)
            try:
                # FIXME: 職種別も必要だが、フォーマットは統一しないと会員登録に使えない
                # ポジション検索条件解析
                tool_input = json.loads(item.raw_item.arguments)
            except (json.JSONDecodeError, TypeError):
                self.logger.exception(
                    "ポジション検索条件（ツールパラメータ）解析失敗しました"
                )
                return

            # ポジション検索条件保存
            preference_input = tool_input.copy()
            preference_input.pop("SessionID", None)
            preference_input.pop("RequestID", None)

    async def _ensure_tool_execution_available(self, client_ip: str) -> None:
        """
        ツール実行前にレート制限を確認し、上限を超えていたら例外を投げる。
        """
        is_allowed = await asyncio.to_thread(
            self._rate_limit_service.is_within_position_search_limit,
            get_session_id(),
            client_ip,
        )
        if not is_allowed:
            raise PositionSearchRateLimitExceeded(RATE_LIMIT_EXCEEDED_MESSAGE)

    async def _save_chat_history(
        self,
        item: RunItem,
    ):
        """
        RunItem を ChatHistory に変換し、指定の `chat_histories` リストへ追加します。

        引数:
            item: 変換対象の RunItem。対象タイプは MessageOutputItem、HandoffCallItem、ToolCallItem、
                HandoffOutputItem、ToolCallOutputItem、ReasoningItem をサポートします。

        動作:
            - MessageOutputItem: assistant ロールでメッセージ本文を持つ ChatHistory を作成します。
            - HandoffCallItem / ToolCallItem: tool / handoff ロールでツールコールの詳細を持つ ChatHistory を作成します。
            - HandoffOutputItem / ToolCallOutputItem: 対応する ChatHistory を探し、出力内容で更新します。
            - ReasoningItem: reasoning ロールで要約コンテンツを持つ ChatHistory を作成します。
            - 上記以外のタイプ: サポート外としてエラーログを出力します。
        """
        session_id = get_session_id()
        chat_histories: list[ChatHistory] = []

        if isinstance(item, MessageOutputItem):
            chat_histories.append(
                ChatHistory(
                    session_id=session_id,
                    position_id=self._position_id,
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
                # ハンドオフ発生する際に、ToolCallとHandoffCallのどちらも発生しますので、
                # ToolCallをスキップ
                return

            try:
                tool_input = json.loads(item.raw_item.arguments)
            except (json.JSONDecodeError, ValueError):
                tool_input = {}
            chat_histories.append(
                ChatHistory(
                    session_id=session_id,
                    position_id=self._position_id,
                    active_agent=item.agent.name,
                    message_id=item.raw_item.id,
                    role=(
                        LLMMessageRole.TOOL
                        if isinstance(item, ToolCallItem)
                        else LLMMessageRole.HANDOFF
                    ),
                    tool_call_id=item.raw_item.call_id,
                    tool_name=item.raw_item.name,
                    tool_input=tool_input,
                )
            )
        elif isinstance(item, (HandoffOutputItem, ToolCallOutputItem)):
            await asyncio.to_thread(
                self._chat_repository.update_tool_output,
                tool_call_id=item.raw_item["call_id"],
                tool_call_output=self._serialize_tool_output_for_storage(
                    item.raw_item["output"]
                ),
            )
        elif isinstance(item, ReasoningItem):
            chat_histories.append(
                ChatHistory(
                    session_id=session_id,
                    position_id=self._position_id,
                    active_agent=item.agent.name,
                    message_id=item.raw_item.id,
                    role=LLMMessageRole.REASONING,
                    content=json.dumps(item.raw_item.summary),
                )
            )
        else:
            self.logger.error("Unsupported item type: %s", item)

        await self._save_chat_histories(chat_histories)

    def _get_message_role(
        self,
        request_type: ChatRequestType,
    ) -> LLMMessageRole:
        """
        ・開始
        ・再開
        ・職種決定
        ・職種解除
        ・ワークフロー回答送信
        ・ワークフロー中断
        のいずれかのメッセージであればDeveloper roleにする
        """
        if request_type in [
            ChatRequestType.START,
            ChatRequestType.RESTART_CHAT,
            ChatRequestType.JOB_TYPES_SELECTED,
            ChatRequestType.JOB_TYPES_CLEAR,
            ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            ChatRequestType.WORKFLOW_CANCELLED,
        ]:
            return LLMMessageRole.DEVELOPER
        else:
            return LLMMessageRole.USER

    async def _save_user_or_developer_message(
        self,
        input: ChatRequestModel,
    ):
        """
        ユーザーまたはデベロッパーのインプットをDB保存する

        Args:
            input: ユーザーまたはデベロッパーのインプット
        """
        role = self._get_message_role(input.request_type)

        await self._save_chat_histories(
            [
                ChatHistory(
                    session_id=get_session_id(),
                    position_id=self._position_id,
                    active_agent=self._active_agent_name,
                    message_id=input.current_message_id,
                    role=role,
                    content=input.message,
                    is_voice=input.is_voice,
                )
            ]
        )

    async def _save_llm_error(
        self,
        message_to_llm: str,
    ):
        chat_history = ChatHistory(
            session_id=get_session_id(),
            active_agent=self._active_agent_name,
            message_id="developer_" + datetime.now().strftime("%Y%m%d%H%M%S%f"),
            role=LLMMessageRole.DEVELOPER,
            content=message_to_llm,
        )
        await self._save_chat_histories([chat_history])

    async def _get_position_detail(
        self,
        encrypted_position_id: str,
    ) -> tuple[dict, dict, dict, str]:
        """
        キャッシュからポジション詳細、会社詳細、業界詳細を取得

        Args:
            encrypted_position_id: ポジションUUID

        Returns:
            成功時：ポジション詳細、会社詳細、業界詳細
            失敗時：エラーメッセージ
        """
        postion_detail = await self._position_service.get_position_detail(
            encrypted_position_id,
        )
        if not postion_detail:
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

        return (postion_detail, company_detail, business_detail, None)

    def _get_agent(self, agent_name: str) -> Agent:
        """
        エージェントを取得する。

        Args:
            agent_name: エージェント名

        Returns:
            エージェント
        """
        agent = (
            self._agents.get(self._position_id)
            if agent_name == AgentName.POSITION_GUIDE
            else self._agents.get(agent_name)
        )
        if not agent:
            raise Exception(f"Agent not found: {agent_name}")

        return agent

    # TODO: 複数のタブやWindowsで異なるポジション詳細が見れると思ってましたので、ポジション詳細Agentをクローンをしていますが、
    # 試したところ、確かポジション詳細が見れますが、websocketはもう利用できなくなります。
    # なので、複数タブやWindowsでのポジション詳細確認を辞めるか、websocketを利用できるようにするかを一度検討の必要があるかも
    # 前者（やめる）のほうがやりやすいかと思われます。
    # https://miidas-dev.slack.com/lists/TJWTV7T7C/F08BU50QS3Y?record_id=Rec093HHSAVAS
    def _create_position_agent_if_not_exist(self, position_id: int):
        """
        ポジションエージェントがない場合、作成する。

        Args:
            position_id: ポジションID

        Returns:
            None
        """
        position_id_str = str(position_id)
        if position_id_str not in self._agents:
            self._agents[position_id_str] = self._agents.get(
                AgentName.POSITION_GUIDE,
            ).clone()

    async def _save_chat_histories(
        self,
        chat_histories,
    ):
        """
        会話履歴をDB保存する。

        Returns:
            None
        """
        if chat_histories:
            await asyncio.to_thread(
                self._chat_repository.add_chat_histories, chat_histories
            )
            self._chat_histories.setdefault(self._chat_key, []).extend(chat_histories)

    async def check_if_previous_chat_histories_exist(
        self,
        encrypted_position_id: str,
    ) -> bool:
        """
        Args:
            encrypted_position_id: 暗号化されたポジションID

        Returns:
            True: チャット履歴が存在する
            False: チャット履歴が存在しない
        """
        position_id = decrypt(
            EncryptKeyType.POSITION,
            encrypted_position_id,
        )
        return await asyncio.to_thread(
            self._chat_repository.has_position_chat_histories,
            position_id,
        )

    async def load_previous_chat_histories(
        self,
        limit: int,
        encrypted_position_id: str | None,
        before_id: str | None,
    ) -> tuple[list[dict], bool]:
        """
        指定したメッセージIDより前の会話履歴を取得する

        Args:
            encrypted_position_id: 暗号化されたポジションID
            before_id: メッセージID
            limit: 取得件数上限

        Returns:
            会話履歴、過去会話履歴はまだあるか
        """
        if encrypted_position_id:
            position_id = decrypt(
                EncryptKeyType.POSITION,
                encrypted_position_id,
            )
            histories = await asyncio.to_thread(
                self._chat_repository.get_position_detail_chat_histories,
                position_id,
                before_id,
            )
        else:
            histories = await asyncio.to_thread(
                self._chat_repository.get_main_chat_histories, before_id
            )

        if not histories:
            return [], True

        stop_index = len(histories)
        # 新->旧順
        previous_chat_histories = []
        while limit > 0:
            # まず最後のユーザーメッセージを探します
            last_user_message_index = next(
                (
                    i
                    for i in range(stop_index - 1, -1, -1)
                    if (
                        # ユーザーメッセージ
                        histories[i].role == LLMMessageRole.USER
                        or (
                            # 最初の挨拶
                            histories[i].content == SESSION_START_MESSAGE
                            and histories[i].role == LLMMessageRole.DEVELOPER
                        )
                    )
                ),
                None,
            )

            if last_user_message_index is None:
                # ユーザーメッセージが見つからなかった場合、終了
                break

            user_message = histories[last_user_message_index]
            assistant_message_added = False
            # 新->旧順
            llm_responses = []
            # 旧->新 該当ユーザーメッセージに対してのLLMレスポンス（ポジション検索結果を含む）を探す
            for index in range(last_user_message_index + 1, stop_index):
                history = histories[index]

                if history.role == LLMMessageRole.TOOL:
                    if not history.content:
                        # ツール結果が空の場合はスキップ
                        continue

                    if ToolName.is_position_search_tool(history.tool_name):
                        # ポジション検索ツールの場合
                        parsed_output = self._parse_tool_output(
                            history.content,
                        )

                        if "Message" not in parsed_output:
                            # 成功したポジション検索
                            tool_call_id = history.tool_call_id
                            tool_input = history.tool_input
                            salary = tool_input.get("Salary")
                            locations = tool_input.get("Locations")
                            if not tool_call_id or not salary or not locations:
                                self.logger.error(
                                    "ポジション検索条件が正しくありません。",
                                    extra={
                                        "tool_call_id": tool_call_id,
                                        "tool_input": tool_input,
                                    },
                                )
                                continue

                            residence = ""
                            work_locations: list[str] = []
                            is_full_remote = tool_input.get("FullyRemoteWork", False)
                            for location in locations:
                                if location["LocationType"] == LocationType.RESIDENCE:
                                    residence = (
                                        location["PrefectureName"]
                                        + location["CityName"]
                                    )
                                elif (
                                    location["LocationType"] == LocationType.FULL_REMOTE
                                ):
                                    is_full_remote = True
                                elif (
                                    location["LocationType"]
                                    == LocationType.WORK_LOCATION
                                ):
                                    work_locations.append(
                                        location["PrefectureName"]
                                        + location["CityName"]
                                    )
                                else:
                                    self.logger.error(
                                        "不明なロケーションタイプです。",
                                        extra={
                                            "tool_call_id": tool_call_id,
                                            "tool_input": tool_input,
                                        },
                                    )
                                    continue

                            # LLMがPositionKeyword=nullを渡す場合、.get("key", "")はNoneを返す（キーが存在するため）。or ""でNoneを空文字列に変換する
                            position_keyword = tool_input.get("PositionKeyword") or ""
                            jobtype_names = tool_input.get("JobtypeNames", [])

                            llm_responses.insert(
                                0,
                                {
                                    "Role": LLMMessageRole.TOOL,
                                    "Type": ChatResponseType.POSITION_SEARCH_LINK,
                                    "MessageID": history.message_id,
                                    "Message": {
                                        "ToolCallId": tool_call_id,
                                        "Salary": salary,
                                        "Residence": residence,
                                        "WorkLocations": work_locations,
                                        "IsFullyRemoteWork": is_full_remote,
                                        "PositionKeyword": position_keyword,
                                        "JobtypeNames": jobtype_names,
                                    },
                                },
                            )
                    elif history.tool_name in (
                        ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
                        ToolName.JOBTYPE_SEARCH_BY_NATURE,
                    ):
                        parsed_output = self._parse_tool_output(history.content)
                        jobtypes_search_result = self._process_jobtype_search_result(
                            history.tool_call_id or "",
                            history.tool_name,
                            json.dumps(history.tool_input, ensure_ascii=False),
                            parsed_output,
                        )
                        if not jobtypes_search_result:
                            continue

                        selected_jobtype_name = None
                        for next_index in range(index + 1, stop_index):
                            next_history = histories[next_index]
                            if next_history.role != LLMMessageRole.DEVELOPER:
                                continue
                            if not next_history.content:
                                continue

                            matched = re.search(
                                r"ユーザーが職種「(.+?)」を選択しました。",
                                next_history.content,
                            )
                            if matched:
                                selected_jobtype_name = matched.group(1)
                                break

                        jobtypes_search_result["SelectedJobtypeName"] = (
                            selected_jobtype_name
                        )
                        llm_responses.insert(
                            0,
                            {
                                "Role": LLMMessageRole.TOOL,
                                "Type": ChatResponseType.JOBTYPE_SEARCH_RESULT,
                                "MessageID": history.message_id,
                                "Message": jobtypes_search_result,
                            },
                        )
                elif history.role == LLMMessageRole.ASSISTANT:
                    if assistant_message_added:
                        # 重複LLMレスポンスをスキップ
                        continue

                    llm_responses.insert(
                        0,
                        {
                            "Role": LLMMessageRole.ASSISTANT,
                            "Type": ChatResponseType.MESSAGE,
                            "MessageID": history.message_id,
                            "Message": history.content,
                        },
                    )
                    assistant_message_added = True

            if llm_responses:
                limit -= 1

                # セッション開始メッセージは送信しない
                if not (
                    user_message.content == SESSION_START_MESSAGE
                    and user_message.role == LLMMessageRole.DEVELOPER
                ):
                    llm_responses.append(
                        {
                            "Role": LLMMessageRole.USER,
                            "Type": ChatResponseType.MESSAGE,
                            "MessageID": user_message.message_id,
                            "Message": user_message.content,
                        }
                    )

                previous_chat_histories.extend(llm_responses)

            stop_index = last_user_message_index

        no_more_user_message_left = not any(
            h.role == LLMMessageRole.USER for h in histories[:stop_index]
        )
        if no_more_user_message_left:
            # 初めてのLLMからの挨拶が残ってる場合、それも一緒にレスポンスします
            greeting_message: ChatHistory | None = None
            for i in range(stop_index - 1, -1, -1):
                h = histories[i]
                if (
                    h.role == LLMMessageRole.DEVELOPER
                    and h.content == SESSION_START_MESSAGE
                    and greeting_message
                    and greeting_message.role == LLMMessageRole.ASSISTANT
                ):
                    previous_chat_histories.append(
                        {
                            "Role": LLMMessageRole.ASSISTANT,
                            "Type": ChatResponseType.MESSAGE,
                            "MessageID": greeting_message.message_id,
                            "Message": greeting_message.content,
                        }
                    )

                    break

                greeting_message = h

        return previous_chat_histories, no_more_user_message_left

    def _find_last_non_position_guide_agent(self):
        """
        メインチャット履歴から最後のPOSITION_GUIDE以外のactive_agentを返す。
        """
        histories = self._chat_histories.get(MAIN_CHAT_KEY, [])
        for history in reversed(histories):
            if history.active_agent != AgentName.POSITION_GUIDE:
                return history.active_agent
        raise ValueError("POSITION_GUIDE以外のActive Agentが履歴に見つかりませんでした")

    def _process_jobtype_search_result(
        self,
        tool_call_id: str,
        tool_call_name: str,
        tool_call_arguments: str,
        jobtypes: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """
        職種検索結果を処理します。

        Args:
            tool_call_id: ツール呼び出しID
            jobtypes: 職種検索結果

        Returns:
            処理された職種検索結果
        """
        if not jobtypes:
            return None

        jobtypes_output = jobtypes
        jobtypes = jobtypes_output.get("職種")
        if not jobtypes:
            return None

        jobtypes = [
            {"ID": item.get("職種名"), "Name": item.get("職種説明")}
            for item in jobtypes
        ]
        keyword = jobtypes_output.get(
            "Keyword", jobtypes_output.get("検索キーワード", "")
        )

        return {
            "ToolCall": {
                "ID": tool_call_id,
                "Name": tool_call_name,
                "Arguments": tool_call_arguments,
            },
            "Keyword": keyword if isinstance(keyword, str) else "",
            "Jobtypes": jobtypes,
        }

    async def job_type_decided(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """
        職種が決定した場合の処理を行います。

        Args:
            chat_request: フロントからのINPUT
            client_ip: ユーザーのIPアドレス
        """
        self.logger.debug("job_type_decided: %s", chat_request.message)

        try:
            jobtypes = json.loads(chat_request.message)
        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON format: %s", e)
            yield ChatStreamResponse(
                request_type=chat_request.request_type
            ).create_error_response("不正なJSON形式です")
            return

        if isinstance(jobtypes, list):
            jobtypes = [
                item.strip()
                for item in jobtypes
                if isinstance(item, str) and item.strip()
            ]
        else:
            jobtypes = None

        if not jobtypes:
            self.logger.warning("職種が選択されていない")
            yield ChatStreamResponse(
                request_type=chat_request.request_type
            ).create_error_response("職種が選択されていない")
            return

        error_response = await self._apply_jobtypes_and_update_agents(
            jobtypes, chat_request.request_type
        )
        if error_response:
            yield error_response
            return

        chat_request.message = (
            f"ユーザーが職種「{'、'.join(jobtypes)}」を選択しました。"
        )
        async for chunk in self.chat(chat_request, client_ip):
            yield chunk

    async def clear_jobtype(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        await self._position_service.clear_jobtypes()
        self._update_agents_with_position_search_tool(None, None)

        chat_request.message = "ユーザーからシステムを通じて、希望職種を変更したい要望がありました。具体的にどの職種がいいか確認するプロセスを進めてください。ユーザーが希望する職種について情報が得られたら、職種検索ツールを使って**職種マスターと合致する職種名**を特定してください。その後、求人検索を行なって、ユーザーのキャリア支援を継続してください。"
        async for chunk in self.chat(chat_request, client_ip):
            yield chunk

    def get_initial_menu_response(self) -> ChatStreamResponseModel:
        """LLMを介さず初期メニューワークフロー定義を直接返す"""
        try:
            definition = self._workflow_service.get_definition(INITIAL_MENU_WORKFLOW_ID)
            message_id = (
                "wf_"
                + INITIAL_MENU_WORKFLOW_ID
                + "_"
                + datetime.now().strftime("%Y%m%d%H%M%S%f")
            )
            return ChatStreamResponse().create_tool_result_response(
                message_id,
                ChatResponseType.WORKFLOW,
                definition.model_dump(by_alias=True),
                ChatSessionStatus.CHATTING,
            )
        except (ValueError, FileNotFoundError) as e:
            self.logger.error("初期メニューワークフロー定義の取得に失敗: %s", e)
            return ChatStreamResponse().create_error_response(
                "セッションの開始に失敗しました。"
            )

    async def workflow_submitted(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """
        ワークフローの回答が送信された場合の処理を行います。

        Args:
            chat_request: フロントからのINPUT
            client_ip: ユーザーのIPアドレス
        """
        try:
            payload = json.loads(chat_request.message)
            workflow_id = payload.get("workflow_id")
            answers = payload.get("answers")
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.error("Invalid JSON format in workflow submission: %s", e)
            yield ChatStreamResponse(
                request_type=chat_request.request_type
            ).create_error_response("不正なJSON形式です")
            return

        if not workflow_id or not isinstance(answers, dict):
            self.logger.error(
                "workflow_id is missing or answers is not a dict: %s", type(answers)
            )
            yield ChatStreamResponse(
                request_type=chat_request.request_type
            ).create_error_response(
                "ワークフローIDが存在しない、または不正な回答形式です"
            )
            return

        if workflow_id == INITIAL_MENU_WORKFLOW_ID:
            await asyncio.to_thread(
                self._chat_repository.create_chat_session,
                session_status=ChatSessionStatus.CHATTING,
            )

        try:
            (
                post_result,
                history_to_save,
            ) = await self._workflow_service.process_workflow_submission(
                workflow_id,
                answers,
            )
        except (ValueError, FileNotFoundError) as e:
            self.logger.error("Workflow submission error: %s", e)
            error_msg = str(e)
            if isinstance(e, FileNotFoundError):
                error_msg = f"ワークフロー定義が見つかりません: {workflow_id}"
            yield ChatStreamResponse(
                request_type=chat_request.request_type
            ).create_error_response(error_msg)
            return

        if post_result.next_agent_name:
            self._active_agent_name = post_result.next_agent_name

        session_id = get_session_id()
        if workflow_id == INITIAL_MENU_WORKFLOW_ID:
            await self._save_chat_histories(
                [
                    ChatHistory(
                        session_id=session_id,
                        active_agent=self._active_agent_name,
                        message_id="developer_"
                        + datetime.now().strftime("%Y%m%d%H%M%S%f"),
                        role=LLMMessageRole.DEVELOPER,
                        content=self._toolcall_trace_message["content"],
                    )
                ]
            )
        # ワークフローの質問と回答の履歴を保存
        if history_to_save:
            chat_histories = []
            for entry in history_to_save:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                chat_histories.append(
                    ChatHistory(
                        session_id=session_id,
                        position_id=None,
                        active_agent=self._active_agent_name,
                        message_id=f"wf_{workflow_id}_{timestamp}",
                        role=entry["role"],
                        content=entry["content"],
                    )
                )
            await self._save_chat_histories(chat_histories)

        # 職種情報が存在する場合、APIに登録してエージェントに求人検索ツールを追加する
        if post_result.selected_jobtypes:
            error_response = await self._apply_jobtypes_and_update_agents(
                post_result.selected_jobtypes, chat_request.request_type
            )
            if error_response:
                yield error_response
                return

        if post_result.next_workflow_id:
            try:
                next_def = self._workflow_service.get_definition(
                    post_result.next_workflow_id
                )
                message_id = f"wf_{post_result.next_workflow_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                yield ChatStreamResponse().create_tool_result_response(
                    message_id,
                    ChatResponseType.WORKFLOW,
                    next_def.model_dump(by_alias=True),
                    ChatSessionStatus.CHATTING,
                )
            except (ValueError, FileNotFoundError) as e:
                self.logger.error(
                    "次ワークフロー定義の取得に失敗しました: %s, %s",
                    post_result.next_workflow_id,
                    e,
                )
                yield ChatStreamResponse(
                    request_type=chat_request.request_type
                ).create_error_response("ワークフローが実行できませんでした。")
            return

        chat_request.message = post_result.message
        async for chunk in self.chat(chat_request, client_ip):
            yield chunk

    async def workflow_cancelled(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """
        ワークフローが中断された場合の処理を行います。

        Args:
            chat_request: フロントからのINPUT
            client_ip: ユーザーのIPアドレス
        """
        workflow_id = ""
        try:
            payload = json.loads(chat_request.message)
            workflow_id = payload.get("workflow_id", "")
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.error("Invalid JSON format in workflow cancellation: %s", e)

        if workflow_id == INITIAL_MENU_WORKFLOW_ID:
            self.logger.warning("initial_menu のキャンセルは許可されていません。")
            yield ChatStreamResponse(
                request_type=chat_request.request_type
            ).create_error_response("このワークフローはキャンセルできません。")
            return

        workflow_msg = "ワークフロー"
        if not workflow_id:
            self.logger.error("workflow_id is missing in workflow cancellation")
        elif not self._workflow_service.exists_definition(workflow_id):
            self.logger.error("Attempted to cancel unknown workflow: %s", workflow_id)
        else:
            workflow_msg = f"{workflow_msg} `{workflow_id}`"

        chat_request.message = f"""
ユーザーが{workflow_msg}を中断しました。
「中断されました。」のように中断した事実を伝えた上で、これまでの会話の文脈に沿って次の案内や提案を自然に行ってください。
"""

        async for chunk in self.chat(chat_request, client_ip):
            yield chunk

    async def _apply_jobtypes_and_update_agents(
        self,
        jobtypes: list[str],
        request_type: ChatRequestType,
    ) -> ChatStreamResponseModel | None:
        """
        職種を適用し、エージェントに求人検索ツールを追加する。
        失敗した場合はエラーレスポンスを返し、成功した場合は None を返す。

        Args:
            jobtypes: 職種一覧
            request_type: リクエストタイプ（エラーレスポンス生成に使用）

        Returns:
            ChatStreamResponseModel | None: 失敗時はエラーレスポンス、成功時は None
        """
        tool_name = await self._position_service.update_jobtypes(jobtypes)
        if not tool_name:
            self.logger.error("職種の更新に失敗しました (jobtypes=%s)", jobtypes)
            return ChatStreamResponse(request_type=request_type).create_error_response(
                "該当職種がまだサポートされていません。"
            )

        result = self._update_agents_with_position_search_tool(tool_name, jobtypes)
        if not result:
            self.logger.error(
                "求人検索ツールの設定に失敗しました (tool_name=%s, jobtypes=%s)",
                tool_name,
                jobtypes,
            )
            return ChatStreamResponse(request_type=request_type).create_error_response(
                "求人検索ツールの設定に失敗しました。"
            )

        return None

    def _update_agents_with_position_search_tool(
        self, tool_name: str | None, jobtype_names: list[str] | None
    ) -> bool:
        """
        指定ツールのポジション検索ツールをポジション検索可能なAgentに追加する

        Args:
            tool_name: API が返したツール名
            jobtype_names: 職種名一覧

        Return:
            bool: 更新に成功したかどうか
        """
        updated_agents, configured_tool_name = self._llm_svc.update_agent_by_tool_name(
            self._provider, tool_name, jobtype_names, self._agents
        )

        if not updated_agents:
            return False
        if tool_name is not None and configured_tool_name != tool_name:
            self.logger.error(
                "Failed to update position search tool: requested=%s configured=%s (jobtypes=%s)",
                tool_name,
                configured_tool_name,
                jobtype_names,
            )
            return False

        return True

    def _extract_position_search_tool_name(
        self, current_search_filter: dict[str, Any] | None
    ) -> str | None:
        if not isinstance(current_search_filter, dict):
            return None

        tool_name = current_search_filter.get("ToolName")
        if not isinstance(tool_name, str):
            return None

        normalized_tool_name = tool_name.strip()
        return normalized_tool_name or None

    def _extract_selected_jobtypes(
        self, current_search_filter: dict[str, Any] | None
    ) -> list[str]:
        if not isinstance(current_search_filter, dict):
            return []

        filters = current_search_filter.get("SearchFilters", current_search_filter)
        if not isinstance(filters, dict):
            return []

        raw_jobtypes = filters.get("Jobtypes")
        if raw_jobtypes is None:
            return []
        if not isinstance(raw_jobtypes, dict):
            self.logger.warning(
                "Unexpected SearchFilters.Jobtypes shape: expected dict, got %s",
                type(raw_jobtypes).__name__,
            )
            return []

        selected_jobtypes: list[str] = []
        seen_selected: set[str] = set()
        for group_name, group_items in raw_jobtypes.items():
            if not isinstance(group_items, list):
                self.logger.warning(
                    "Unexpected SearchFilters.Jobtypes[%s] shape: expected list, got %s",
                    group_name,
                    type(group_items).__name__,
                )
                continue
            for item in group_items:
                if not isinstance(item, dict):
                    continue
                value = item.get("Value")
                if not isinstance(value, str):
                    continue
                normalized_value = value.strip()
                if not normalized_value:
                    continue
                if item.get("Selected") and normalized_value not in seen_selected:
                    seen_selected.add(normalized_value)
                    selected_jobtypes.append(normalized_value)

        return selected_jobtypes
