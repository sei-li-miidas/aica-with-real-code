"""WorkflowChatHandler — workflow/jobtype public method の前処理を担うコンポーネント。

ChatService の `job_type_decided`、`clear_jobtype`、`workflow_submitted`、
`workflow_cancelled` が呼ばれたとき、メッセージの解析・バリデーション・副作用（API 呼び出し、
DB 保存など）を行い、`chat()` に渡す準備済みメッセージを返す。

責務
-----
- job_type_decided: JSON 解析、jobtype バリデーション、`PositionService.update_jobtypes()` 呼び出し、
  エージェント更新、`chat()` 向けメッセージ生成
- clear_jobtype: `PositionService.clear_jobtypes()` 呼び出し、エージェントリセット、メッセージ生成
- workflow_submitted: JSON 解析、バリデーション、`WorkflowService.process_workflow_submission()` 呼び出し、
  履歴保存、メッセージ生成
- workflow_cancelled: JSON 解析、`WorkflowService.exists_definition()` 確認、メッセージ生成

スコープ外
-----------
- `chat()` の実行（呼び出し元 ChatService が担う）
- StreamEventProcessor / StreamGuard / ToolEventHandler（それぞれの component が担う）
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from services.llm_service import AgentName
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType, ChatStreamResponse, ChatStreamResponseModel
from utils.const import INITIAL_MENU_WORKFLOW_ID, LOGGER_PREFIX
from utils.enum import LLMMessageRole, ToolName
from utils.log_utils import get_session_id

if TYPE_CHECKING:
    from services.llm_service import LLMService
    from services.position_service import PositionService
    from services.workflow_service import WorkflowService

logger = logging.getLogger(f"{LOGGER_PREFIX}.services.chat.workflow_chat_handler")


class WorkflowChatHandlerResult:
    """前処理結果を保持する値オブジェクト。

    Attributes
    ----------
    error_response:
        前処理エラー時に caller が即座に yield すべきレスポンス。None なら正常。
    prepared_message:
        `chat()` に渡す準備済みメッセージ文字列。error_response が None の場合のみ有効。
    next_agent_name:
        caller が _conv_state.active_agent_name に適用するエージェント名。None なら変更なし。
    workflow_id:
        処理したワークフロー ID。caller が INITIAL_MENU 判定・toolcall_trace 生成に使用。
    workflow_histories:
        ChatHistory のリスト。DB 保存は caller が担当する。
    next_workflow_id_response:
        next_workflow_id がある場合に caller が yield すべきレスポンス。
    """

    def __init__(
        self,
        error_response: ChatStreamResponseModel | None = None,
        prepared_message: str | None = None,
        next_agent_name: str | None = None,
        workflow_id: str | None = None,
        workflow_histories: list[ChatHistory] | None = None,
        next_workflow_id_response: ChatStreamResponseModel | None = None,
    ) -> None:
        self.error_response = error_response
        self.prepared_message = prepared_message
        self.next_agent_name = next_agent_name
        self.workflow_id = workflow_id
        self.workflow_histories = workflow_histories or []
        self.next_workflow_id_response = next_workflow_id_response


class WorkflowChatHandler:
    """workflow/jobtype public method の前処理を担うコンポーネント。

    ChatService が生成し、DI で注入された依存（PositionService、WorkflowService、LLMService）
    と agents dict を保持する。agents dict は init_session() 後に legacy._agents と共有する。

    Parameters
    ----------
    position_service:
        `update_jobtypes()` / `clear_jobtypes()` の呼び出し先。
    workflow_service:
        `process_workflow_submission()` / `exists_definition()` の呼び出し先。
    llm_service:
        `update_agent_by_tool_name()` の呼び出し先。
    create_session:
        セッションを作成するコールバック。INITIAL_MENU_WORKFLOW_ID 処理時に呼ばれる。
    get_agents:
        現在の agents dict を返すコールバック。ターン開始時点で legacy から最新値を取得するために使う。
    get_provider:
        現在の model provider 名を返すコールバック。`update_agent_by_tool_name()` に渡す。
    get_active_agent_name:
        現在の active_agent_name を返すコールバック。ChatHistory 生成時に使う。
    """

    def __init__(
        self,
        position_service: PositionService,
        workflow_service: WorkflowService,
        llm_service: LLMService,
        create_session: Callable[[ChatSessionStatus], None],
        get_agents: Callable[[], dict[str, Any]],
        get_provider: Callable[[], str],
        get_active_agent_name: Callable[[], str],
    ) -> None:
        self._position_service = position_service
        self._workflow_service = workflow_service
        self._llm_service = llm_service
        self._create_session = create_session
        self._get_agents = get_agents
        self._get_provider = get_provider
        self._get_active_agent_name = get_active_agent_name

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def prepare_job_type_decided(
        self,
        input: ChatRequestModel,
    ) -> WorkflowChatHandlerResult:
        """job_type_decided の前処理を行い結果を返す。

        処理ステップ:
        1. JSON パース・バリデーション
        2. `PositionService.update_jobtypes()` でツール名を取得
        3. `LLMService.update_agent_by_tool_name()` でエージェントを更新
        4. input.message を日本語の通知メッセージに置き換える

        Returns
        -------
        WorkflowChatHandlerResult
            error_response が None の場合は prepared_message を input.message に設定して
            `chat()` を呼ぶ。error_response が非 None の場合は即座に yield して return。
        """
        logger.debug("prepare_job_type_decided: %s", input.message)
        chat_response = ChatStreamResponse(request_type=input.request_type)

        try:
            jobtypes = json.loads(input.message)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON format: %s", e)
            return WorkflowChatHandlerResult(
                error_response=chat_response.create_error_response("不正なJSON形式です")
            )

        if isinstance(jobtypes, list):
            jobtypes = [
                item.strip()
                for item in jobtypes
                if isinstance(item, str) and item.strip()
            ]
        else:
            jobtypes = None

        if not jobtypes:
            logger.warning("職種が選択されていない")
            return WorkflowChatHandlerResult(
                error_response=chat_response.create_error_response("職種が選択されていない")
            )

        jobtypes_error = await self._apply_jobtypes_and_update_agents(
            jobtypes,
            input.request_type,
        )
        if jobtypes_error is not None:
            return WorkflowChatHandlerResult(
                error_response=jobtypes_error
            )

        prepared_message = f"ユーザーが職種「{'、'.join(jobtypes)}」を選択しました。"
        return WorkflowChatHandlerResult(prepared_message=prepared_message)

    async def prepare_clear_jobtype(
        self,
        input: ChatRequestModel,
    ) -> WorkflowChatHandlerResult:
        """clear_jobtype の前処理を行い結果を返す。

        処理ステップ:
        1. `PositionService.clear_jobtypes()` でジョブタイプをクリア
        2. `LLMService.update_agent_by_tool_name()` でエージェントをリセット
        3. `chat()` 向けメッセージを返す
        """
        await self._position_service.clear_jobtypes()
        self._update_agents_with_position_search_tool(None, None)

        prepared_message = (
            "ユーザーからシステムを通じて、希望職種を変更したい要望がありました。"
            "具体的にどの職種がいいか確認するプロセスを進めてください。"
            "ユーザーが希望する職種について情報が得られたら、職種検索ツールを使って"
            "**職種マスターと合致する職種名**を特定してください。"
            "その後、求人検索を行なって、ユーザーのキャリア支援を継続してください。"
        )
        return WorkflowChatHandlerResult(prepared_message=prepared_message)

    async def prepare_workflow_submitted(
        self,
        input: ChatRequestModel,
    ) -> WorkflowChatHandlerResult:
        """workflow_submitted の前処理を行い結果を返す。

        処理ステップ:
        1. JSON パース・バリデーション
        2. INITIAL_MENU_WORKFLOW_ID → セッション作成（process_workflow_submission より前に必須）
        3. `WorkflowService.process_workflow_submission()` を呼び出し
        4. next_agent_name をローカルで先取り（外部状態は変更しない）
        5. history_to_save から ChatHistory オブジェクト生成（DB 保存は caller が担当）
        6. selected_jobtypes 処理
        7. next_workflow_id → レスポンス生成
        8. `chat()` 向けメッセージを返す
        """
        chat_response = ChatStreamResponse(request_type=input.request_type)

        try:
            payload = json.loads(input.message)
            workflow_id = payload.get("workflow_id")
            answers = payload.get("answers")
            extra = payload.get("extra")
            if extra is not None and not isinstance(extra, dict):
                logger.warning(
                    "extra が dict 型ではないため None にフォールバックします: %s", type(extra)
                )
                extra = None
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            logger.error("Invalid JSON format in workflow submission: %s", e)
            return WorkflowChatHandlerResult(
                error_response=chat_response.create_error_response("不正なJSON形式です")
            )

        if not workflow_id or not isinstance(answers, dict):
            logger.error(
                "workflow_id is missing or answers is not a dict: %s", type(answers)
            )
            return WorkflowChatHandlerResult(
                error_response=chat_response.create_error_response(
                    "ワークフローIDが存在しない、または不正な回答形式です"
                )
            )

        if workflow_id == INITIAL_MENU_WORKFLOW_ID:
            await asyncio.to_thread(self._create_session, ChatSessionStatus.CHATTING)

        try:
            (
                post_result,
                history_to_save,
            ) = await self._workflow_service.process_workflow_submission(
                workflow_id,
                answers,
                extra=extra,
            )
        except (ValueError, FileNotFoundError) as e:
            logger.error("Workflow submission error: %s", e)
            error_msg = str(e)
            if isinstance(e, FileNotFoundError):
                error_msg = f"ワークフロー定義が見つかりません: {workflow_id}"
            return WorkflowChatHandlerResult(
                error_response=chat_response.create_error_response(error_msg)
            )

        # initial_menu 実行時はactive_agentが設定されていないため、
        # 遷移先エージェント（next_agent_name）をactive_agentとして扱う。
        # それ以外のワークフローは実際に遂行しているエージェント（現在のactive_agent）を使う。
        if workflow_id == INITIAL_MENU_WORKFLOW_ID:
            active_agent = post_result.next_agent_name
        else:
            active_agent = self._get_active_agent_name()

        session_id = get_session_id()
        workflow_histories: list[ChatHistory] = []
        if history_to_save:
            batch_id = uuid.uuid4().hex
            for index, entry in enumerate(history_to_save):
                # ハンドラが entry["message_id_suffix"] を指定した場合（例: 転職軸要約メッセージの "summary"）は
                # workflow_id の直後に suffix を付与する
                suffix = entry.get("message_id_suffix")
                if suffix:
                    message_id = f"wf_{workflow_id}_{suffix}_{batch_id}_{index}"
                else:
                    message_id = f"wf_{workflow_id}_{batch_id}_{index}"
                workflow_histories.append(
                    ChatHistory(
                        session_id=session_id,
                        position_id=None,
                        active_agent=active_agent or AgentName.CAREER_ADVISOR,
                        message_id=message_id,
                        role=entry["role"],
                        content=entry["content"],
                    )
                )

        if post_result.selected_jobtypes:
            jobtypes_error = await self._apply_jobtypes_and_update_agents(
                post_result.selected_jobtypes,
                input.request_type,
            )
            if jobtypes_error is not None:
                return WorkflowChatHandlerResult(
                    error_response=jobtypes_error,
                    next_agent_name=post_result.next_agent_name or None,
                    workflow_id=workflow_id,
                    workflow_histories=workflow_histories,
                )

        next_workflow_id_response: ChatStreamResponseModel | None = None
        if post_result.next_workflow_id:
            try:
                next_def = self._workflow_service.get_definition(post_result.next_workflow_id)
                message_id = f"wf_{post_result.next_workflow_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                next_workflow_id_response = ChatStreamResponse().create_tool_result_response(
                    message_id,
                    ChatResponseType.WORKFLOW,
                    next_def.model_dump(by_alias=True),
                    ChatSessionStatus.CHATTING,
                )
                # LLM 経由の start_workflow と同じ形の tool レコードをセッション最後に保存する。
                # リロード時に load_previous_chat_histories がこのレコードを検知して
                # 再実行導線（restart_workflow）を生成できるようにするため。
                workflow_histories.append(
                    ChatHistory(
                        session_id=session_id,
                        position_id=None,
                        active_agent=active_agent or AgentName.CAREER_ADVISOR,
                        message_id=message_id,
                        role=LLMMessageRole.TOOL,
                        tool_call_id=f"wf_chain_{uuid.uuid4().hex}",
                        tool_name=ToolName.START_WORKFLOW,
                        tool_input={"WorkflowID": post_result.next_workflow_id},
                        content=json.dumps(
                            {"WorkflowID": post_result.next_workflow_id},
                            ensure_ascii=False,
                        ),
                    )
                )
            except (ValueError, FileNotFoundError) as e:
                logger.error(
                    "次ワークフロー定義の取得に失敗しました: %s, %s",
                    post_result.next_workflow_id,
                    e,
                )
                next_workflow_id_response = ChatStreamResponse(
                    request_type=input.request_type
                ).create_error_response("ワークフローが実行できませんでした。")

        return WorkflowChatHandlerResult(
            prepared_message=post_result.message,
            next_agent_name=post_result.next_agent_name or None,
            workflow_id=workflow_id,
            workflow_histories=workflow_histories,
            next_workflow_id_response=next_workflow_id_response,
        )

    async def prepare_workflow_cancelled(
        self,
        input: ChatRequestModel,
    ) -> WorkflowChatHandlerResult:
        """workflow_cancelled の前処理を行い結果を返す。

        処理ステップ:
        1. JSON パース（失敗してもフォールバックメッセージで継続）
        2. workflow_id の存在確認
        3. `chat()` 向けメッセージを返す
        """
        workflow_id = ""
        try:
            payload = json.loads(input.message)
            workflow_id = payload.get("workflow_id", "")
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            logger.error("Invalid JSON format in workflow cancellation: %s", e)

        if workflow_id == INITIAL_MENU_WORKFLOW_ID:
            logger.warning("initial_menu のキャンセルは許可されていません。")
            return WorkflowChatHandlerResult(
                error_response=ChatStreamResponse(
                    request_type=input.request_type
                ).create_error_response("このワークフローはキャンセルできません。")
            )

        workflow_msg = "ワークフロー"
        if not workflow_id:
            logger.error("workflow_id is missing in workflow cancellation")
        elif not self._workflow_service.exists_definition(workflow_id):
            logger.error("Attempted to cancel unknown workflow: %s", workflow_id)
        else:
            workflow_msg = f"{workflow_msg} `{workflow_id}`"

        prepared_message = f"""
ユーザーが{workflow_msg}を中断しました。
「中断されました。」のように中断した事実を伝えた上で、これまでの会話の文脈に沿って次の案内や提案を自然に行ってください。
"""
        return WorkflowChatHandlerResult(prepared_message=prepared_message)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _apply_jobtypes_and_update_agents(
        self,
        jobtypes: list[str],
        request_type: ChatRequestType,
    ) -> ChatStreamResponseModel | None:
        """職種を登録しエージェントに求人検索ツールを追加する。

        Returns
        -------
        ChatStreamResponseModel | None
            エラー時はエラーレスポンスを返す。成功時は None。
        """
        chat_response = ChatStreamResponse(request_type=request_type)
        tool_name = await self._position_service.update_jobtypes(jobtypes)
        if not tool_name:
            logger.error(
                "Failed to update position search tool: ToolName is empty (jobtypes=%s)",
                jobtypes,
            )
            return chat_response.create_error_response("該当職種がまだサポートされていません。")
        result = self._update_agents_with_position_search_tool(tool_name, jobtypes)
        if not result:
            logger.error(
                "Failed to update position search tool: requested=%s (jobtypes=%s)",
                tool_name,
                jobtypes,
            )
            return chat_response.create_error_response("求人検索ツールの設定に失敗しました。")
        return None

    def _update_agents_with_position_search_tool(
        self,
        tool_name: str | None,
        jobtype_names: list[str] | None,
    ) -> bool:
        """エージェントにポジション検索ツールを設定または解除する。

        Returns
        -------
        bool
            更新に成功した場合 True。
        """
        agents = self._get_agents()
        provider = self._get_provider()
        updated_agents, configured_tool_name = self._llm_service.update_agent_by_tool_name(
            provider, tool_name, jobtype_names, agents
        )

        if not updated_agents:
            return False
        if tool_name is not None and configured_tool_name != tool_name:
            logger.error(
                "Failed to update position search tool: requested=%s configured=%s (jobtypes=%s)",
                tool_name,
                configured_tool_name,
                jobtype_names,
            )
            return False

        return True
