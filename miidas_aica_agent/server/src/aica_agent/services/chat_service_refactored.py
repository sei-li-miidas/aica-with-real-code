from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import suppress
from datetime import datetime
import json
import uuid
from typing import Any

from openai.types.responses.response_input_item_param import Message
from openai.types.responses.response_input_text_param import ResponseInputTextParam

from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from repositories.action_log_repo import ActionLogRepository
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.user_repo import UserRepository
from security.llm_output_guard import LLMOutputGuard
from services.base_service import BaseService
from services.chat.chat_persistence import ChatPersistence
from services.chat.conversation_state import ConversationState
from services.chat.history_mapper import HistoryMapper
from services.chat.llm_runner import (
    LLMRetryChunkEvent,
    LLMRetryCompleteEvent,
    LLMRunner,
    json_default,
)
from services.chat.stream_event_processor import StreamEventProcessor
from services.chat.stream_guard import StreamGuard
from services.chat.tool_event_handler import (
    PositionSearchRateLimitExceeded,
    RetryableToolOutputFailure,
    ToolEventHandler,
)
from services.chat.turn_preparer import TurnPreparer
from services.chat.workflow_chat_handler import WorkflowChatHandler
from services.conversation_summary_service import ConversationSummaryService
from services.llm_service import AgentName, LLMService
from services.position_service import PositionService
from services.rate_limit_service import RateLimitService
from services.summary_service import SummaryService
from services.workflow_service import WorkflowService
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import (
    ChatResponseType,
    ChatStreamResponse,
    ChatStreamResponseModel,
)
from utils.const import INITIAL_MENU_WORKFLOW_ID, MAIN_CHAT_KEY
from utils.crypt import decrypt
from utils.enum import EncryptKeyType, LLMMessageRole, ToolName
from utils.env_utils import is_local_or_dev
from utils.log_utils import get_session_id, set_session_id

# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

POSITION_CHAT_DETAIL_MESSAGE_ID_PREFIX = "position_detail_chat_summary_"

DEFAULT_ERROR_MESSAGE = (
    "大変混み合っておりますので、しばらく経ってからリロードしてご利用ください。"
)
DEFAULT_LLM_FAIL_RESPONSE = "システムエラーが発生しました。"


class ChatService(BaseService):
    """
    Phase 4 refactored shell — legacy ChatService への依存なし。

    main `chat()` path は `TurnPreparer` と `LLMRunner` contract 経由で動作する。
    `init_session()` および `summarize_position_detail_chat()` はネイティブ実装。
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
        llm_runner: LLMRunner,
        conversation_summary_svc: ConversationSummaryService,
        llm_output_guard: LLMOutputGuard | None = None,
        summary_service: SummaryService | None = None,
    ) -> None:
        super().__init__()

        # Direct dependencies (no legacy delegation)
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

        # 禁止ワード検知器（DI優先。未注入時のみローカル初期化）
        self.llm_output_guard = (
            llm_output_guard if llm_output_guard is not None else LLMOutputGuard()
        )

        # LLMRunner (injected)
        self._llm_runner = llm_runner

        # Agent registry: populated by init_session()
        self._agents: dict[str, Any] = {}

        # ConversationState と HistoryMapper は外部 I/O も副作用もない純粋なオブジェクト。
        self._conv_state = ConversationState()
        self._history_mapper = HistoryMapper()

        # ChatPersistence は chat_repository と _conv_state への参照を持つ。
        self._chat_persistence = ChatPersistence(
            chat_repository=self._chat_repository,
            conv_state=self._conv_state,
        )

        # TurnPreparer は position_svc / chat_persistence / conv_state / agents を使う。
        self._turn_preparer = TurnPreparer(
            position_service=position_svc,
            chat_persistence=self._chat_persistence,
            conv_state=self._conv_state,
            agents=self._agents,
        )

        # StreamEventProcessor は stream event loop と response yield を担う。
        self._stream_event_processor = StreamEventProcessor(
            chat_persistence=self._chat_persistence,
            is_stop_at_tool=self._is_stop_at_tool,
            append_stop_at_tool_outputs=self._append_stop_at_tool_outputs_callback,
            update_active_agent=self._update_active_agent,
            update_continuation_state=self._update_continuation_state,
        )

        # ToolEventHandler はターンごとに fresh 生成する。
        self._current_tool_event_handler: ToolEventHandler | None = None

        # WorkflowChatHandler は workflow/jobtype public method の前処理を担う。
        self._workflow_chat_handler = WorkflowChatHandler(
            position_service=position_svc,
            workflow_service=self._workflow_service,
            llm_service=llm_svc,
            create_session=self._chat_persistence.create_session,
            get_agents=lambda: self._agents,
            get_provider=lambda: self._conv_state.model_name,
            get_active_agent_name=lambda: self._conv_state.active_agent_name,
        )

        # _toolcall_trace_message はテスト互換性のために init_session() で設定する。
        self._toolcall_trace_message: dict | None = None
        self._last_init_session_failed = False

    # ------------------------------------------------------------------
    # init_session — native implementation (no legacy delegation)
    # ------------------------------------------------------------------

    async def init_session(
        self,
        model_name: str,
    ) -> tuple[ChatSessionStatus, bool]:
        self._conv_state.model_name = model_name

        try:
            current_search_filter = await self._position_service.current_search_filter()
            current_tool_name = self._extract_position_search_tool_name(
                current_search_filter
            )
            current_jobtypes = self._extract_selected_jobtypes(current_search_filter)
            if current_tool_name:
                agents = self._llm_svc.clone_agents(
                    model_name,
                    current_jobtypes,
                    current_tool_name,
                )
            else:
                agents = self._llm_svc.clone_agents(model_name)
        except Exception:
            self.logger.exception(
                "Failed to load current search filter during init_session"
            )
            agents = self._llm_svc.clone_agents(model_name)

        for agent_name, (agent, default_agent) in agents.items():
            self._agents[agent_name] = agent
            if default_agent:
                self._conv_state.active_agent_name = agent_name

        toolcall_trace_message = {
            "type": "message",
            "role": LLMMessageRole.DEVELOPER,
            "content": (
                f"### ツール呼び出すときのパラメータについて\n"
                f"SessionID: {get_session_id()}を利用してください。\n"
                f"RequestID: Pythonの`uuid.uuid4()`を使って生成してください。\n"
            ),
        }
        self._toolcall_trace_message = toolcall_trace_message
        self._turn_preparer.set_toolcall_trace_message(toolcall_trace_message)
        self._chat_persistence.set_toolcall_trace_content(
            toolcall_trace_message.get("content", "")
        )

        try:
            is_new_session = True
            (chat_session, exists) = await asyncio.to_thread(
                self._chat_repository.init_chat_session
            )
            if chat_session:
                is_new_session = False
                if chat_session.histories:
                    self._conv_state.chat_histories, self._conv_state.conversation = (
                        self._history_mapper.convert_to_llm_messages(
                            chat_session.histories,
                            create_position_agent_callback=self._create_position_agent_if_not_exist,
                        )
                    )
                    resumed_agent_name = self._find_last_non_position_guide_agent()
                    if resumed_agent_name is None:
                        raise ValueError(
                            "No non-position-guide agent found in resumed MAIN history"
                        )
                    if resumed_agent_name not in self._agents:
                        # DefaultAgentのみと会話していたユーザーが再接続
                        # → 新規セッションとして扱い、initial_menuを表示する
                        set_session_id(str(uuid.uuid4()))
                        self._conv_state.conversation = {}
                        self._conv_state.chat_histories = {MAIN_CHAT_KEY: []}
                        is_new_session = True
                        self._conv_state.active_agent_name = ""
                    else:
                        self._conv_state.active_agent_name = resumed_agent_name
                else:
                    # 初期メニューワークフロー実行時にエラーが発生してセッションだけ作られたケース
                    # → 新規セッションとして扱い、initial_menuを表示する
                    set_session_id(str(uuid.uuid4()))
                    is_new_session = True
            elif exists:
                set_session_id(str(uuid.uuid4()))

            if (
                MAIN_CHAT_KEY not in self._conv_state.conversation
                or not self._conv_state.conversation.get(MAIN_CHAT_KEY)
            ):
                self._conv_state.conversation[MAIN_CHAT_KEY] = [
                    toolcall_trace_message,
                ]

            if chat_session:
                self._last_init_session_failed = False
                return chat_session.status, is_new_session
            else:
                self._last_init_session_failed = False
                return ChatSessionStatus.CHATTING, is_new_session
        except Exception:
            self.logger.exception("セッション初期化失敗")
            self._last_init_session_failed = True
            return ChatSessionStatus.ERROR, False

    # ------------------------------------------------------------------
    # Private helpers for init_session
    # ------------------------------------------------------------------

    def _extract_position_search_tool_name(
        self, current_search_filter: dict | None
    ) -> str | None:
        if not isinstance(current_search_filter, dict):
            return None
        tool_name = current_search_filter.get("ToolName")
        if not isinstance(tool_name, str):
            return None
        normalized_tool_name = tool_name.strip()
        return normalized_tool_name or None

    def _extract_selected_jobtypes(
        self, current_search_filter: dict | None
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

    def _find_last_non_position_guide_agent(self) -> str | None:
        # Intentionally returns None (not raises) when no match is found.
        # TurnPreparer._find_last_non_position_guide_agent raises ValueError instead —
        # the divergence is documented in turn_preparer.py.
        histories = self._conv_state.chat_histories.get(MAIN_CHAT_KEY, [])
        for history in reversed(histories):
            if history.active_agent != AgentName.POSITION_GUIDE:
                return history.active_agent
        self.logger.warning("No non-position-guide agent found in MAIN history")
        return None

    def _create_position_agent_if_not_exist(
        self, position_id: str | int | None
    ) -> None:
        if position_id is None:
            return
        position_id_str = str(position_id)
        if position_id_str not in self._agents:
            position_guide_agent = self._agents.get(AgentName.POSITION_GUIDE)
            if position_guide_agent is None:
                self.logger.warning(
                    "Skipping position agent creation because %s is not registered",
                    AgentName.POSITION_GUIDE,
                )
                return
            self._agents[position_id_str] = position_guide_agent.clone()

    # ------------------------------------------------------------------
    # Public non-chat methods
    # ------------------------------------------------------------------

    async def check_if_previous_chat_histories_exist(
        self, encrypted_position_id: str
    ) -> bool:
        position_id = decrypt(
            EncryptKeyType.POSITION,
            encrypted_position_id,
        )
        return await asyncio.to_thread(
            self._chat_repository.has_position_chat_histories, position_id
        )

    async def load_previous_chat_histories(
        self,
        limit: int,
        encrypted_position_id: str | None,
        before_id: str | None,
    ) -> tuple[list[dict], bool]:
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
        previous, no_more = self._history_mapper.format_previous_chat_histories(
            histories or [],
            limit,
        )
        # メインチャットの最新ページ取得時のみ、ワークフロー再実行導線を埋め込む
        if not encrypted_position_id and before_id is None:
            restart_entry = await asyncio.to_thread(
                self._build_restart_workflow_entry
            )
            if restart_entry:
                # ペイロードは新→旧順のため先頭に挿入する
                previous.insert(0, restart_entry)
        return previous, no_more

    def _build_restart_workflow_entry(self) -> dict | None:
        """セッション最後の履歴が start_workflow の場合、再実行用要素を生成する。

        リロード等でワークフロー実行中の状態が失われた場合に、フロントが
        再実行導線を表示できるようワークフロー定義を含む要素を返す。
        対象外の場合や定義取得に失敗した場合は None を返す。
        """
        last = self._chat_repository.get_last_main_chat_history()
        if (
            last is None
            or last.role != LLMMessageRole.TOOL
            or last.tool_name != ToolName.START_WORKFLOW
            or not last.content
        ):
            return None
        parsed_output = self._history_mapper.parse_tool_output(last.content)
        workflow_id = parsed_output.get("WorkflowID")
        if not workflow_id or str(workflow_id) == INITIAL_MENU_WORKFLOW_ID:
            # 初期メニューのワークフローの途中でリロードされた場合、
            # まだセッション未作成 = 再度初期メニューワークフローが実行されるため、ここでの再実行導線は不要。
            return None
        try:
            definition = self._workflow_service.get_definition(str(workflow_id))
        except (ValueError, FileNotFoundError):
            self.logger.exception(
                "ワークフロー定義の取得に失敗しました: %s", workflow_id
            )
            return None
        return {
            "Role": LLMMessageRole.TOOL,
            "Type": ChatResponseType.RESTART_WORKFLOW,
            "MessageID": last.message_id,
            "Message": definition.model_dump(by_alias=True),
        }

    async def summarize_position_detail_chat(
        self,
        chat_request: ChatRequestModel,
    ) -> ChatSessionStatus:
        encrypted_position_id = chat_request.position_id
        if encrypted_position_id:
            try:
                self._conv_state.position_id = decrypt(
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

        position_chat_histories = self._conv_state.chat_histories.get(
            self._conv_state.position_id, []
        )
        if not position_chat_histories:
            self.logger.info(
                "No position chat histories found: %s",
                self._conv_state.position_id,
            )
            return await asyncio.to_thread(self._chat_repository.session_status)

        self.logger.info(
            "Summarizing position detail chat: %s, %s, %s, %s",
            get_session_id(),
            self._conv_state.position_id,
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
                self._conv_state.position_id,
            )
            return await asyncio.to_thread(self._chat_repository.session_status)

        timestamp = int(datetime.now().timestamp())
        message_id = f"{POSITION_CHAT_DETAIL_MESSAGE_ID_PREFIX}{self._conv_state.position_id}_{timestamp}"

        await asyncio.to_thread(
            self._chat_persistence.save_chat_histories,
            [
                ChatHistory(
                    session_id=get_session_id(),
                    position_id=None,
                    active_agent=AgentName.POSITION_GUIDE,
                    message_id=message_id,
                    role=LLMMessageRole.DEVELOPER,
                    content=summary_text,
                )
            ],
        )

        self._conv_state.conversation[MAIN_CHAT_KEY].append(
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

    # ------------------------------------------------------------------
    # chat() — main streaming path
    # ------------------------------------------------------------------

    async def chat(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        encrypted_position_id = chat_request.position_id or None
        session_status = await asyncio.to_thread(self._chat_repository.session_status)
        if not session_status:
            session_status = ChatSessionStatus.CHATTING

        chat_response = ChatStreamResponse(
            request_type=chat_request.request_type,
            position_id=encrypted_position_id,
        )

        if await asyncio.to_thread(self._chat_repository.is_session_blocked):
            self.logger.warning("BLOCKED_SESSION_ATTEMPT: %s", get_session_id())
            yield chat_response.create_error_response(
                "不適切な出力が検知されたため、会話がブロックされています。",
                session_status,
            )
            return

        if (
            session_status
            in (ChatSessionStatus.REGISTERING, ChatSessionStatus.APPLYING)
            and chat_request.request_type == ChatRequestType.START
        ):
            yield chat_response.create_end_response(session_status)
            return

        try:
            self._resolve_chat_key(chat_request)

            await self._turn_preparer.prepare_turn(chat_request)

            if (
                self._conv_state.chat_key == MAIN_CHAT_KEY
                and not self._conv_state.previous_continuation_states.get(
                    self._conv_state.chat_key
                )
            ):
                try:
                    await self._build_summary_context(get_session_id())
                except Exception:
                    # Summary context rebuild is best-effort; keep the chat turn progressing.
                    self.logger.exception("会話要約文脈の再構築に失敗")

            if self._conv_state.chat_key not in self._conv_state.conversation:
                yield chat_response.create_end_response(session_status)
                return

            self._conv_state.conversation[self._conv_state.chat_key].append(
                Message(
                    type="message",
                    role=self._turn_preparer.get_message_role(
                        chat_request.request_type
                    ),
                    content=[
                        ResponseInputTextParam(
                            type="input_text",
                            text=chat_request.message,
                        )
                    ],
                )
            )
            await asyncio.to_thread(
                self._chat_persistence.save_user_or_developer_message, chat_request
            )
        except Exception:
            self.logger.exception("Failed to prepare refactored chat turn")
            yield chat_response.create_error_response(
                DEFAULT_ERROR_MESSAGE,
                session_status,
            )
            return

        stream_guard = StreamGuard(
            llm_output_guard=self.llm_output_guard,
            chat_persistence=self._chat_persistence,
            session_id=get_session_id(),
        )

        last_run_result = None
        rate_limit_error: PositionSearchRateLimitExceeded | None = None
        try:
            active_agent_name = self._conv_state.active_agent_name
            if not active_agent_name:
                if (
                    self._last_init_session_failed
                    or self._toolcall_trace_message is None
                ):
                    yield chat_response.create_end_response(session_status)
                else:
                    yield chat_response.create_error_response(
                        DEFAULT_ERROR_MESSAGE,
                        session_status,
                    )
                return

            try:
                starting_agent = self._get_agent(active_agent_name)
            except Exception:
                self.logger.warning(
                    "No runnable agent found for active_agent_name=%s",
                    active_agent_name,
                )
                if (
                    self._last_init_session_failed
                    or self._toolcall_trace_message is None
                ):
                    yield chat_response.create_end_response(session_status)
                else:
                    yield chat_response.create_error_response(
                        DEFAULT_ERROR_MESSAGE,
                        session_status,
                    )
                return

            async def _before_attempt() -> None:
                self._current_tool_event_handler = ToolEventHandler(
                    position_repository=self._position_repository,
                    rate_limit_service=self._rate_limit_service,
                    workflow_service=self._workflow_service,
                    chat_repository=self._chat_repository,
                    user_repository=self._user_repository,
                    action_log_repository=self._action_log_repository,
                    current_page=chat_request.current_page,
                    encrypted_position_id=encrypted_position_id,
                )

            async def _after_attempt() -> None:
                nonlocal session_status
                self._current_tool_event_handler = None
                # APPLICATION / REGISTRATION ツールは stream 処理中に session_status を更新する。
                # 以降の finalize / END response へ最新状態を反映するため、repository から再取得する。
                session_status = (
                    await asyncio.to_thread(self._chat_repository.session_status)
                    or session_status
                )

            async def _handle_retryable_error(
                retryable_error: RetryableToolOutputFailure,
            ) -> None:
                # function_call_output のみを追加する（function_call は不要）。
                # StreamEventProcessor.process() の finally ブロックが
                # update_continuation_state を呼び出し、continuation_state が
                # run_stream.last_response_id にセットされる。
                # 次の試行で previous_response_id として渡すことで
                # Responses API が function_call を含む前のレスポンスを
                # 暗黙的に引き継ぐため、function_call_output 単体で完結する。
                self._conv_state.conversation[self._conv_state.chat_key].append(
                    {
                        "type": "function_call_output",
                        "call_id": retryable_error.call_id,
                        "output": retryable_error.message_to_llm,
                    }
                )
                await asyncio.to_thread(
                    self._chat_persistence.save_llm_error,
                    retryable_error.message_to_llm,
                )

            async def _handle_non_retryable_error(error: Exception) -> None:
                nonlocal rate_limit_error
                if isinstance(error, PositionSearchRateLimitExceeded):
                    rate_limit_error = error
                    return
                self.logger.exception("Refactored chat shell runner failed")
                # No call_id to answer — this branch cannot self-heal via retry.
                # Persist the error for audit and exit immediately.
                await asyncio.to_thread(
                    self._chat_persistence.save_llm_error,
                    DEFAULT_LLM_FAIL_RESPONSE,
                )

            async def _process_stream(
                run_stream: object,
            ) -> AsyncGenerator[ChatStreamResponseModel, None]:
                # Start the next turn from a fresh list after the runner has received
                # the current attempt input via input_supplier.
                self._conv_state.conversation[self._conv_state.chat_key] = []
                if self._current_tool_event_handler is None:
                    raise RuntimeError(
                        "ToolEventHandler must be initialized before stream processing"
                    )
                async for chunk in self._stream_event_processor.process(
                    run_stream,
                    chat_response,
                    session_status,
                    tool_event_handler=self._current_tool_event_handler,
                    client_ip=client_ip,
                    stream_guard=stream_guard,
                ):
                    yield chunk

            async for retry_event in self._llm_runner.run_with_retry(
                starting_agent=starting_agent,
                input=self._conv_state.conversation[self._conv_state.chat_key],
                process_stream=_process_stream,
                input_supplier=lambda: self._conv_state.conversation[
                    self._conv_state.chat_key
                ],
                continuation_state_supplier=lambda: self._conv_state.previous_continuation_states.get(
                    self._conv_state.chat_key
                ),
                message_id=chat_request.current_message_id,
                on_before_attempt=_before_attempt,
                on_after_attempt=_after_attempt,
                on_retryable_error=_handle_retryable_error,
                on_non_retryable_error=_handle_non_retryable_error,
            ):
                if isinstance(retry_event, LLMRetryChunkEvent):
                    yield retry_event.chunk
                elif isinstance(retry_event, LLMRetryCompleteEvent):
                    last_run_result = retry_event.result
        finally:
            with suppress(Exception):
                stream_guard.cleanup()

        if rate_limit_error is not None:
            yield chat_response.create_error_response(
                str(rate_limit_error),
                session_status,
            )
            return

        if stream_guard.security_detected:
            return

        if last_run_result is None or not last_run_result.succeeded:
            yield chat_response.create_error_response(
                DEFAULT_ERROR_MESSAGE,
                session_status,
            )
            return

        _finalize_security_stopped = False
        try:
            async for chunk in stream_guard.finalize(
                chat_response,
                session_status,
            ):
                yield chunk
                if chunk.response_type == ChatResponseType.ERROR:
                    _finalize_security_stopped = True
        except Exception:
            # Log and continue: a finalize() failure is non-fatal.
            # The client receives END (not ERROR) so the session stays usable.
            self.logger.exception("Failed to finalize stream guard")

        if _finalize_security_stopped:
            return

        # Note: Usage recording is now handled by llm_runner.run_with_retry(),
        # so we don't need a separate _record_usage() method anymore.
        # But for dev/local environments, emit token usage for UI feedback.
        if is_local_or_dev() and last_run_result and last_run_result.usage is not None:
            try:
                token_usage_str = json.dumps(
                    last_run_result.usage, default=json_default
                )
                yield chat_response.create_token_usage_response(
                    f"\nToken Usage: {token_usage_str}",
                    session_status,
                )
            except Exception:
                self.logger.exception("Failed to emit token usage response")

        if (
            self._conv_state.chat_key == MAIN_CHAT_KEY
            and self._summary_service is not None
        ):
            try:
                await self._summary_service.check_should_start_summary(get_session_id())
            except Exception:
                # This check is a non-critical post-turn side effect; keep chat response flow alive.
                self.logger.exception("会話要約起動判定に失敗")

        yield chat_response.create_end_response(session_status)

    def _get_agent(self, agent_name: str) -> object:
        agent = (
            self._agents.get(self._conv_state.position_id)
            if agent_name == AgentName.POSITION_GUIDE
            else self._agents.get(agent_name)
        )
        if not agent:
            raise KeyError(f"Agent not found: {agent_name}")
        return agent

    def _resolve_chat_key(self, chat_request: ChatRequestModel) -> None:
        encrypted_position_id = chat_request.position_id or None
        if encrypted_position_id:
            self._conv_state.position_id = decrypt(
                EncryptKeyType.POSITION,
                encrypted_position_id,
            )
            self._conv_state.chat_key = self._conv_state.position_id
        else:
            self._conv_state.position_id = None
            self._conv_state.chat_key = MAIN_CHAT_KEY

    def _is_stop_at_tool(self, item: object) -> bool:
        agent = getattr(item, "agent", None)
        tool_use_behavior = getattr(agent, "tool_use_behavior", None)
        if not isinstance(tool_use_behavior, dict):
            return False

        stop_at_tool_names = tool_use_behavior.get("stop_at_tool_names")
        if not isinstance(stop_at_tool_names, list):
            return False

        raw_item = getattr(item, "raw_item", None)
        tool_name = getattr(raw_item, "name", None)
        return isinstance(tool_name, str) and tool_name in stop_at_tool_names

    def _update_continuation_state(self, state: object) -> None:
        self._conv_state.previous_continuation_states[self._conv_state.chat_key] = state

    def _update_active_agent(self, agent_name: str) -> None:
        self._conv_state.active_agent_name = agent_name

    def _append_stop_at_tool_outputs_callback(
        self,
        replay_items: list[Any],
        stop_at_tool_exists: bool,
    ) -> None:
        if self._current_tool_event_handler is not None:
            outputs = self._current_tool_event_handler.build_stop_at_tool_outputs(
                replay_items,
                stop_at_tool_exists,
            )
            if not outputs:
                return

            conversation = self._conv_state.conversation.setdefault(
                self._conv_state.chat_key, []
            )
            for item in outputs:
                call_id = item.get("call_id")
                if not isinstance(call_id, str):
                    continue
                if any(
                    isinstance(conv_item, dict) and conv_item.get("call_id") == call_id
                    for conv_item in conversation
                ):
                    continue
                conversation.append(item)
        else:
            self._append_stop_at_tool_outputs(
                replay_items,
                stop_at_tool_exists,
            )

    def _append_stop_at_tool_outputs(
        self,
        replay_items: list[Any],
        stop_at_tool_exists: bool,
    ) -> None:
        if not stop_at_tool_exists:
            return

        conversation = self._conv_state.conversation.setdefault(
            self._conv_state.chat_key, []
        )
        for item in replay_items:
            if item.get("type") != "function_call_output":
                continue
            call_id = item.get("call_id")
            if not isinstance(call_id, str):
                continue
            if any(
                isinstance(conv_item, dict) and conv_item.get("call_id") == call_id
                for conv_item in conversation
            ):
                continue
            conversation.append(item)

    async def _build_summary_context(self, session_id: str) -> None:
        if self._summary_service is None or self._conv_state.chat_key != MAIN_CHAT_KEY:
            return

        latest_completed = self._summary_service.get_latest_completed(session_id)
        # Boundary `0` means there is no completed summary yet and all histories are eligible.
        boundary_id = 0
        if latest_completed is not None:
            try:
                boundary_id = int(latest_completed.summary_until_history_id)
            except (TypeError, ValueError):
                self.logger.warning(
                    "Invalid summary_until_history_id=%r, fallback to boundary=0",
                    latest_completed.summary_until_history_id,
                )

        # Use incremental fetch after the latest completed summary; otherwise load full MAIN history.
        if latest_completed and latest_completed.summary_text:
            main_histories = self._summary_service.get_histories_after(
                session_id,
                boundary_id,
            )
        else:
            main_histories = await asyncio.to_thread(
                self._chat_repository.get_main_chat_histories
            )

        chat_histories, all_messages = self._history_mapper.convert_to_llm_messages(
            main_histories,
            create_position_agent_callback=self._create_position_agent_if_not_exist,
        )
        self._conv_state.chat_histories[MAIN_CHAT_KEY] = chat_histories.get(
            MAIN_CHAT_KEY, []
        )

        rebuilt_conversation: list[dict[str, Any]] = []
        if self._toolcall_trace_message is not None:
            rebuilt_conversation.append(self._toolcall_trace_message)

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

        rebuilt_conversation.extend(
            self._remove_tool_trace_message(all_messages.get(MAIN_CHAT_KEY, []))
        )
        self._conv_state.conversation[MAIN_CHAT_KEY] = rebuilt_conversation

    def _remove_tool_trace_message(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if self._toolcall_trace_message is None:
            return messages

        tool_trace_content = self._toolcall_trace_message.get("content")
        if tool_trace_content is None:
            return messages

        return [
            message
            for message in messages
            if not (
                isinstance(message, dict)
                and message.get("type") == "message"
                and message.get("role") == LLMMessageRole.DEVELOPER
                and message.get("content") == tool_trace_content
            )
        ]

    # ------------------------------------------------------------------
    # Workflow public methods
    # ------------------------------------------------------------------

    async def job_type_decided(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        result = await self._workflow_chat_handler.prepare_job_type_decided(
            chat_request
        )
        if result.error_response is not None:
            yield result.error_response
            return
        chat_request.message = result.prepared_message
        async for chunk in self.chat(chat_request, client_ip):
            yield chunk

    async def clear_jobtype(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        result = await self._workflow_chat_handler.prepare_clear_jobtype(chat_request)
        chat_request.message = result.prepared_message
        async for chunk in self.chat(chat_request, client_ip):
            yield chunk

    async def workflow_submitted(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        result = await self._workflow_chat_handler.prepare_workflow_submitted(
            chat_request
        )

        if result.next_agent_name:
            self._conv_state.active_agent_name = result.next_agent_name

        # jobtypes_errorのエラーの場合でもワークフローの履歴は保存するため、エラー応答を返す前に履歴保存処理を行う。
        if result.workflow_id == INITIAL_MENU_WORKFLOW_ID:
            await asyncio.to_thread(self._chat_persistence.save_toolcall_trace_message)
        if result.workflow_histories:
            await asyncio.to_thread(
                self._chat_persistence.save_chat_histories, result.workflow_histories
            )

        if result.error_response is not None:
            yield result.error_response
            return

        if result.next_workflow_id_response is not None:
            yield result.next_workflow_id_response
            return

        chat_request.message = result.prepared_message
        async for chunk in self.chat(chat_request, client_ip):
            yield chunk

    async def workflow_cancelled(
        self,
        chat_request: ChatRequestModel,
        client_ip: str,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        result = await self._workflow_chat_handler.prepare_workflow_cancelled(
            chat_request
        )
        if result.error_response is not None:
            yield result.error_response
            return
        chat_request.message = result.prepared_message
        async for chunk in self.chat(chat_request, client_ip):
            yield chunk

    def get_initial_menu_response(self) -> ChatStreamResponseModel:
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
