"""ToolEventHandler — tool call/output dispatch と frontend tool response を担う。

StreamEventProcessor の run_item_stream_event ハンドラから呼ばれ、
ToolCallItem / ToolCallOutputItem の処理を担う。

責務
-----
- ToolCallItem の記録・rate limit チェック（_handle_tool_call）
- ToolCallOutputItem の解析・frontend response 生成（handle_tool_output）
- position search / jobtype search / workflow start の tool 別分岐
- stop-at-tool / tool replay items への追加（append_stop_at_tool_outputs）
- ToolCallItem から ToolCallOutputItem への call_id マッピング管理

スコープ外
----------
- DB 保存（ChatPersistence の責務）
- security 検知・block session（StreamGuard の責務）
- workflow submit/cancel の前処理（WorkflowChatHandler の責務）
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from agents import ToolCallItem, ToolCallOutputItem

from domain.entities.chat_session import ChatSessionStatus
from repositories.action_log_repo import ActionLogRepository, ActionLogType
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.user_repo import UserRepository
from services.rate_limit_service import RateLimitService
from services.workflow_service import WorkflowService
from utils.chat_response import (
    ChatResponseType,
    ChatStreamResponse,
    ChatStreamResponseModel,
)
from utils.const import INITIAL_MENU_WORKFLOW_ID, format_position_search_fake_result
from utils.crypt import decrypt
from utils.enum import EncryptKeyType, PageName, ToolName
from utils.log_utils import get_session_id

logger = logging.getLogger(__name__)

RATE_LIMIT_EXCEEDED_MESSAGE = "申し訳ありませんが、求人検索の利用上限に達しました。しばらく経ってから再度お試しください。"


class PositionSearchRateLimitExceeded(Exception):
    """求人検索のレート制限が超過した際に発生する例外。"""


class RetryableToolOutputFailure(Exception):
    """ツール出力が LLM リトライ対象の失敗だったことを示す例外。"""

    def __init__(self, call_id: str, message_to_llm: str) -> None:
        super().__init__(message_to_llm)
        self.call_id = call_id
        self.message_to_llm = message_to_llm


def _get_raw_item_field(raw_item: object, field: str) -> object:
    """raw_item から指定フィールドを取得する。

    agents SDK の raw_item は TypedDict（dict）と Pydantic BaseModel（属性アクセス）の
    両方になり得るため、両方に対応する。フィールドが存在しない場合は None を返す。
    意図的に None でも警告を出さない（呼び出し元が None を処理する）。
    chat_persistence._get_raw_item_field は DB 更新コンテキスト専用で警告を出す同等の実装。
    """
    if isinstance(raw_item, dict):
        return raw_item.get(field)
    return getattr(raw_item, field, None)


def _parse_tool_output(output: Any) -> dict:
    """ツール結果 JSON を解析して dict を返す。

    legacy chat_service.py の _parse_tool_output と同一ロジック。
    """
    outer_result = output
    if isinstance(output, str):
        try:
            outer_result = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            logger.exception("ツールのoutputのJSON解析に失敗しました. 入力: %s", output)
            return {}

    if isinstance(outer_result, dict):
        inner_result = outer_result.get("text", outer_result)
    elif isinstance(outer_result, list):
        if not outer_result:
            logger.warning("ツールのoutputリストが空です")
            return {}
        first_item = outer_result[0]
        if not isinstance(first_item, dict):
            logger.error(
                "ツールのoutputリスト先頭要素はdictである必要があります: %s",
                type(first_item).__name__,
            )
            return {}
        inner_result = first_item.get("text", first_item)
    else:
        logger.error(
            "ツールのoutputはlist/dictまたはJSON文字列である必要があります: %s",
            type(outer_result).__name__,
        )
        return {}

    if isinstance(inner_result, dict):
        return inner_result
    if not isinstance(inner_result, str):
        logger.error(
            "ツールのoutputの'text'フィールドは文字列またはdictではありません: %s",
            output,
        )
        return {}
    try:
        return json.loads(inner_result)
    except (json.JSONDecodeError, TypeError):
        logger.exception(
            "ツールのoutputの'text'フィールドのJSON解析に失敗しました. 入力: %s",
            inner_result,
        )
        return {}


# backward-compat alias — import path kept for existing test imports
_generate_position_search_fake_result = format_position_search_fake_result


def _process_jobtype_search_result(
    tool_call_id: str,
    tool_call_name: ToolName,
    tool_call_arguments: str,
    jobtypes: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """職種検索結果を処理して frontend payload を返す。"""
    if not jobtypes:
        return None

    jobtypes_output = jobtypes
    raw_jobtypes = jobtypes_output.get("職種")
    if not raw_jobtypes:
        return None

    normalized = [
        {"ID": item.get("職種名"), "Name": item.get("職種説明")}
        for item in raw_jobtypes
    ]
    keyword = jobtypes_output.get("Keyword", jobtypes_output.get("検索キーワード", ""))

    return {
        "ToolCall": {
            "ID": tool_call_id,
            "Name": tool_call_name,
            "Arguments": tool_call_arguments,
        },
        "Keyword": keyword if isinstance(keyword, str) else "",
        "Jobtypes": normalized,
    }


class ToolEventHandler:
    """ToolCallItem / ToolCallOutputItem を処理し frontend response を yield する。

    Parameters
    ----------
    position_repository:
        position search result を処理するリポジトリ。
    rate_limit_service:
        position search の rate limit を確認するサービス。
    workflow_service:
        workflow start の定義を取得するサービス。
    """

    def __init__(
        self,
        position_repository: PositionRepository,
        rate_limit_service: RateLimitService,
        workflow_service: WorkflowService,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        action_log_repository: ActionLogRepository,
        current_page: PageName,
        encrypted_position_id: str | None,
    ) -> None:
        self._position_repository = position_repository
        self._rate_limit_service = rate_limit_service
        self._workflow_service = workflow_service
        self._chat_repository = chat_repository
        self._user_repository = user_repository
        self._action_log_repository = action_log_repository
        self._current_page = current_page
        self._encrypted_position_id = encrypted_position_id
        # call_id -> (ToolName, raw_item) マッピング（ToolCallItem から ToolCallOutputItem の照合に使う）
        self._tool_calls: dict[str, tuple[ToolName, Any]] = {}
        # position search の call_id -> 件数マッピング（fake result 生成に使う）
        self._position_search_counts: dict[str, int] = {}
        self._session_status_update: ChatSessionStatus | None = None

    async def handle_tool_call(
        self,
        item: ToolCallItem,
        client_ip: str,
    ) -> None:
        """ToolCallItem を処理する。

        - ToolName に定義されていないツールは無視する。
        - position search ツールの場合は rate limit を確認する。
        - tool_calls マップに記録する。

        Raises
        ------
        PositionSearchRateLimitExceeded
            position search の rate limit が超過した場合。
        """
        try:
            tool_name = ToolName(item.raw_item.name)
        except ValueError:
            # 処理対象外ツール — 無視
            return

        # エントリを先に記録してから rate limit を確認する。
        # 例外が発生しても ToolEventHandler ごとターン終了時に破棄されるため孤立エントリは無害。
        self._tool_calls[item.raw_item.call_id] = (tool_name, item.raw_item)

        if ToolName.is_position_search_tool(tool_name):
            await self._ensure_tool_execution_available(client_ip)

    async def _ensure_tool_execution_available(self, client_ip: str) -> None:
        """rate limit を確認し、超過していれば例外を投げる。"""
        is_allowed = await asyncio.to_thread(
            self._rate_limit_service.is_within_position_search_limit,
            get_session_id(),
            client_ip,
        )
        if not is_allowed:
            raise PositionSearchRateLimitExceeded(RATE_LIMIT_EXCEEDED_MESSAGE)

    async def handle_tool_output(
        self,
        item: ToolCallOutputItem,
        chat_response: ChatStreamResponse,
        session_status: ChatSessionStatus,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """ToolCallOutputItem を処理し frontend response を yield する。

        ToolCallItem が未記録（_tool_calls に call_id が存在しない）場合は何もしない。
        ツール実行失敗（"Message" キーが出力に含まれる場合）は RetryableToolOutputFailure を
        raise して呼び出し元（chat_service_refactored.py）のリトライループへ制御を戻す。

        Yields
        ------
        ChatStreamResponseModel
            POSITION_SEARCH_RESULT / JOBTYPE_SEARCH_RESULT / WORKFLOW のいずれか。

        Note
        ----
        以下のツールは handle_tool_call() で記録されるが、handle_tool_output() で
        match ケースを持たないため frontend response は生成しない（意図的な省略）:
        - USER_PREFERENCE: LLM がサイドエフェクトとして実行するため結果は不要。
        """
        tool_call_id = _get_raw_item_field(item.raw_item, "call_id")
        if not isinstance(tool_call_id, str) or not tool_call_id:
            logger.warning("tool_call_id が無効です: %s", tool_call_id)
            return

        tool_call = self._tool_calls.get(tool_call_id)
        if not tool_call:
            # 処理対象外ツール
            return

        parsed_output = _parse_tool_output(item.output)

        if "Message" in parsed_output:
            # ツール実行失敗 — LLM 再試行ループへ制御を戻す。
            logger.warning("ツール実行失敗: %s", item.raw_item)
            message_to_llm = (
                str(parsed_output["Message"])
                + "\n### SessionIDかRequestIDが設定されていないエラーの場合、\n"
                + f"SessionID: {get_session_id()}\n"
                + f"RequestID: {uuid.uuid4()}\n"
                + "を使ってください。"
            )
            raise RetryableToolOutputFailure(tool_call_id, message_to_llm)

        tool_name, tc_item = tool_call

        match tool_name:
            case (
                ToolName.GENERIC_POSITION_SEARCH
                | ToolName.IT_POSITION_SEARCH
                | ToolName.FINANCIAL_SALES_POSITION_SEARCH
            ):
                position_search_result = (
                    self._position_repository.process_position_search_result(
                        tool_call_id,
                        parsed_output,
                    )
                )
                yield chat_response.create_tool_result_response(
                    tool_call_id,
                    ChatResponseType.POSITION_SEARCH_RESULT,
                    position_search_result,
                    session_status,
                )
                # fake result 件数を記録（stop-at-tool replay 時に使う）
                position_ids = parsed_output.get("AllPositionIds") or []
                self._position_search_counts[tool_call_id] = (
                    len(position_ids) if isinstance(position_ids, list) else 0
                )

            case (
                ToolName.JOBTYPE_SEARCH_BY_KEYWORDS | ToolName.JOBTYPE_SEARCH_BY_NATURE
            ):
                jobtypes_search_result = _process_jobtype_search_result(
                    tool_call_id,
                    tool_name,
                    tc_item.arguments,
                    parsed_output,
                )
                if jobtypes_search_result:
                    yield chat_response.create_tool_result_response(
                        tool_call_id,
                        ChatResponseType.JOBTYPE_SEARCH_RESULT,
                        jobtypes_search_result,
                        session_status,
                    )

            case ToolName.START_WORKFLOW:
                workflow_id = parsed_output.get("WorkflowID")
                if workflow_id == INITIAL_MENU_WORKFLOW_ID:
                    logger.warning(
                        "start_workflow に initial_menu が渡されました。スキップします。"
                    )
                    return
                if workflow_id:
                    try:
                        definition = self._workflow_service.get_definition(
                            str(workflow_id)
                        )
                        yield chat_response.create_tool_result_response(
                            tool_call_id,
                            ChatResponseType.WORKFLOW,
                            definition.model_dump(by_alias=True),
                            session_status,
                        )
                    except (ValueError, FileNotFoundError) as e:
                        logger.error(
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
                # NOTE: ここは legacy chat_service.py と意図的に異なる。
                # legacy は CHATTING のみ応募開始し、APPLYING / REGISTERING は no-op だった。
                # refactored ではユーザーがポジション詳細ページで APPLICATION した場合、
                # CHATTING / APPLYING / REGISTERING を同じ「応募ポジション追加」導線として扱う。
                # REGISTERED / APPLIED は cookie 情報が必要なため、legacy と同じく未実装のままにする。
                if self._current_page != PageName.POSITION_DETAIL:
                    logger.error(
                        "ポジション詳細ページ以外からの応募: %s",
                        self._current_page,
                    )
                elif session_status in (
                    ChatSessionStatus.REGISTERED,
                    ChatSessionStatus.APPLIED,
                ):
                    # TODO: すでに会員登録済みの場合、応募する
                    # ログイン済みクッキー情報をフロントからもらう必要
                    pass
                else:
                    # 応募ポジション追加＆セッションステータス変更
                    # フロントでも応募ボタンステータス変更の必要もある
                    add_apply_position_succeeded = await self._add_apply_position()
                    if add_apply_position_succeeded:
                        await asyncio.to_thread(
                            self._chat_repository.update_session_status,
                            ChatSessionStatus.APPLYING,
                        )
                        if session_status != ChatSessionStatus.APPLYING:
                            self._session_status_update = ChatSessionStatus.APPLYING
                    elif session_status == ChatSessionStatus.CHATTING:
                        # 応募導線で応募情報追加に失敗した場合、
                        # CHATTING からは会員登録導線へフォールバックする。
                        await asyncio.to_thread(
                            self._chat_repository.update_session_status,
                            ChatSessionStatus.REGISTERING,
                        )
                        self._session_status_update = ChatSessionStatus.REGISTERING

            case ToolName.REGISTRATION:
                # 登録
                # NOTE: legacy parity を維持するため、非 CHATTING でも
                # ページ条件を満たせば下の登録サイドエフェクトは継続する。
                # TODO: V2 の時に、ここを早期 return に変更してログイン誘導へ寄せる。

                if self._current_page in (PageName.CHAT, PageName.POSITION_DETAIL):
                    # 分析用のログ出力
                    await asyncio.to_thread(
                        self._action_log_repository.insert,
                        log_type=ActionLogType.REGISTRATION,
                        source=self._current_page,
                    )
                    await asyncio.to_thread(
                        self._chat_repository.update_session_status,
                        ChatSessionStatus.REGISTERING,
                    )
                    self._session_status_update = ChatSessionStatus.REGISTERING
                else:
                    logger.error(
                        "知らないページからの会員登録: %s",
                        self._current_page,
                    )

    async def _add_apply_position(self) -> bool:
        if not self._encrypted_position_id:
            logger.error("応募処理をスキップ: encrypted_position_id が未設定です")
            return False
        try:
            real_id = decrypt(
                EncryptKeyType.POSITION,
                self._encrypted_position_id,
            )
            add_succeeded = await asyncio.to_thread(
                self._user_repository.add_apply_position,
                real_id,
            )
            return bool(add_succeeded)
        except Exception:
            logger.exception("応募ポジションの追加に失敗しました")
            return False

    def consume_session_status_update(self) -> ChatSessionStatus | None:
        """ツール処理で更新された session_status を 1 回だけ取り出す。"""
        session_status = self._session_status_update
        self._session_status_update = None
        return session_status

    def build_stop_at_tool_outputs(
        self,
        replay_items: list[Any],
        stop_at_tool_exists: bool,
    ) -> list[dict[str, Any]]:
        """stop_at_tool 発生時に次ターンへ渡す function_call_output リストを返す。

        legacy _append_stop_at_tool_outputs と同一ロジック。
        caller が conversation に追加する責務を持つ。

        Returns
        -------
        list[dict[str, Any]]
            conversation に追加すべき function_call_output エントリのリスト。
            stop_at_tool_exists が False の場合は空リストを返す。
        """
        if not stop_at_tool_exists:
            return []

        outputs: list[dict[str, Any]] = []
        for item in replay_items:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "function_call_output":
                continue
            call_id = item.get("call_id")
            if not isinstance(call_id, str):
                continue

            tool_entry = self._tool_calls.get(call_id)
            if tool_entry is not None:
                tool_name, _ = tool_entry
                if ToolName.is_position_search_tool(tool_name):
                    positions_count = self._position_search_counts.get(call_id, 0)
                    outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": _generate_position_search_fake_result(
                                positions_count
                            ),
                        }
                    )
                    continue
                if tool_name in (
                    ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
                    ToolName.JOBTYPE_SEARCH_BY_NATURE,
                ):
                    outputs.append(
                        {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": f"""
職種名検索ツールが実行されました。ツールが選定したユーザーの希望に合う職種リストをユーザーに提示しています。ユーザーは現在、そのリストの中から希望職種を選択しています。ユーザーから希望職種が届いたら、求人検索ツールを使って求人検索を実行してください。ただし、希望勤務地、希望年収の確認がまだできていない場合は、先にユーザーに確認した後に、求人検索を行ってください。
###ツールが選定した職種一覧
{item["output"]}
""",
                        }
                    )
                    continue
            outputs.append(item)

        return outputs
