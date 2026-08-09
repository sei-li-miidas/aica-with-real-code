"""DB ChatHistory から Agent SDK 入力形式・フロントエンドペイロードへの変換コンポーネント。

HistoryMapper は DB の ChatHistory レコードと Agent SDK 入力フォーマット・
フロントエンドレスポンスペイロード間の双方向変換を担う純粋なデータ変換コンポーネント。
DB の読み書きは一切行わない。

責務
-----
- `convert_to_llm_messages` — DB ChatHistory リストを LLM 会話入力形式に変換
- `parse_tool_output` — ツール実行結果 (JSON 文字列 or dict) をパースして dict を返す
- `process_jobtype_search_result` — 職種検索結果を処理してフロントエンド向け構造に変換
- `format_previous_chat_histories` — DB ChatHistory をフロントエンド向けペイロードリストに変換

位置づけ
---------
- 外部 I/O なし・副作用なし。モックが不要な純粋変換ロジック。
- REST history path (`load_previous_chat_histories`) は stateless のまま維持される。
  `ConversationState` の初期化を前提としない。
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from openai.types.responses import ResponseOutputTextParam

from domain.entities.chat_history import ChatHistory
from repositories.chat_repo import ChatRepository
from utils.chat_response import ChatResponseType
from utils.const import (
    MAIN_CHAT_KEY,
    POSITION_SEARCH_FAKE_RESULT,
    SESSION_START_MESSAGE,
    format_position_search_fake_result,
)
from utils.enum import LLMMessageRole, LocationType, ToolName

if TYPE_CHECKING:
    pass

# backward-compat alias — import path kept for existing test imports
_generate_position_search_fake_result = format_position_search_fake_result


class HistoryMapper:
    """DB ChatHistory と Agent SDK 入力形式・フロントエンドペイロード間の変換コンポーネント。

    外部 I/O を持たない純粋なデータ変換クラス。DB の読み書きは行わない。
    `ConversationState` の初期化も前提としない（REST history path は stateless）。
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__module__)

    def convert_to_llm_messages(
        self,
        histories: list[ChatHistory],
        *,
        position_id: str | None = None,
        create_position_agent_callback: Callable[[str | None], None] | None = None,
    ) -> tuple[dict[str, list[ChatHistory]], dict[str, list]]:
        """DB 履歴レコードから LLM 会話履歴を作成する。

        Args:
            histories: DB から取得した ChatHistory リスト
            position_id: 現在は使用しない（chat キーは各 history レコードの history.position_id から決定）
            create_position_agent_callback: history.position_id をキーとして agent を生成するコールバック

        Returns:
            (chat_histories, all_messages) のタプル:
            - chat_histories: chat キー → ChatHistory リストの辞書
            - all_messages: chat キー → LLM 入力メッセージリストの辞書
        """
        chat_histories: dict[str, list[ChatHistory]] = {}
        all_messages: dict[str, list] = {}

        for history in histories:
            if history.position_id:
                history_key = str(history.position_id)
                if create_position_agent_callback is not None:
                    create_position_agent_callback(history_key)
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
                    self._logger.warning(
                        "Tool output is empty: %s",
                        history,
                    )
                    output = "ツール実行結果がまだありません。"
                elif ToolName.is_position_search_tool(history.tool_name):
                    try:
                        parsed_output = self.parse_tool_output(history.content)
                        position_ids = parsed_output.get("AllPositionIds") or []
                        positions_count = (
                            len(position_ids) if isinstance(position_ids, list) else 0
                        )
                        output = _generate_position_search_fake_result(positions_count)
                    except Exception:
                        self._logger.exception(
                            "ポジション検索結果の復元に失敗しました。tool_call_id=%s",
                            history.tool_call_id,
                        )
                        output = POSITION_SEARCH_FAKE_RESULT
                elif history.tool_name in (
                    ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
                    ToolName.JOBTYPE_SEARCH_BY_NATURE,
                ):
                    try:
                        parsed_output = self.parse_tool_output(history.content)
                        jobtypes = self.process_jobtype_search_result(
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
                        self._logger.exception(
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
                # REASONING ロールは現状スキップ。
                # legacy の REASONING ロール使用状況が確認でき次第、対処方針を決定する。
                pass
            else:
                self._logger.error("Unsupported message role: %s", history)

        return chat_histories, all_messages

    def parse_tool_output(
        self,
        output: Any,
    ) -> dict:
        """ツール実行結果を解析して dict を返す。

        Args:
            output: 生のツール実行結果（JSON 文字列・dict・list など）

        Returns:
            解析後の dict。解析失敗時は空の dict。
        """
        self._logger.debug("ツールのoutput: %s", output)
        outer_result = output
        if isinstance(output, str):
            try:
                outer_result = json.loads(output)
            except (json.JSONDecodeError, TypeError):
                self._logger.exception(
                    "ツールのoutputのJSON解析に失敗しました. 入力: %s",
                    output,
                )
                return {}

        if isinstance(outer_result, dict):
            inner_result = outer_result.get("text", outer_result)
        elif isinstance(outer_result, list):
            if not outer_result:
                self._logger.warning("ツールのoutputリストが空です")
                return {}
            first_item = outer_result[0]
            if not isinstance(first_item, dict):
                self._logger.error(
                    "ツールのoutputリスト先頭要素はdictである必要があります: %s",
                    type(first_item).__name__,
                )
                return {}
            inner_result = first_item.get("text", first_item)
        else:
            self._logger.error(
                "ツールのoutputはlist/dictまたはJSON文字列である必要があります: %s",
                type(outer_result).__name__,
            )
            return {}

        if isinstance(inner_result, dict):
            return inner_result
        if not isinstance(inner_result, str):
            self._logger.error(
                "ツールのoutputの'text'フィールドは文字列またはdictではありません: %s",
                output,
            )
            return {}
        try:
            return json.loads(inner_result)
        except (json.JSONDecodeError, TypeError):
            self._logger.exception(
                "ツールのoutputの'text'フィールドのJSON解析に失敗しました. 入力: %s",
                inner_result,
            )
            return {}

    def process_jobtype_search_result(
        self,
        tool_call_id: str,
        tool_call_name: str,
        tool_call_arguments: str,
        jobtypes: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """職種検索結果を処理してフロントエンド向け構造に変換する。

        Args:
            tool_call_id: ツール呼び出し ID
            tool_call_name: ツール名
            tool_call_arguments: ツール引数（JSON 文字列）
            jobtypes: 職種検索結果の dict

        Returns:
            処理済みの職種検索結果 dict、または変換不可の場合 None。
        """
        if not jobtypes:
            return None

        jobtypes_output = jobtypes
        jobtypes_items = jobtypes_output.get("職種")
        if not jobtypes_items:
            return None

        jobtypes_list = [
            {"ID": item.get("職種名"), "Name": item.get("職種説明")}
            for item in jobtypes_items
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
            "Jobtypes": jobtypes_list,
        }

    def format_previous_chat_histories(
        self,
        histories: list[ChatHistory],
        limit: int,
    ) -> tuple[list[dict], bool]:
        """DB ChatHistory リストをフロントエンド向けペイロードに変換する。

        `load_previous_chat_histories` の出力整形ロジックを担う。
        stateless — DB アクセスなし。

        Args:
            histories: DB から取得した ChatHistory リスト（古い順）
            limit: 返す会話ペア（ユーザーターン）の上限数

        Returns:
            (previous_chat_histories, no_more_user_message_left) のタプル:
            - previous_chat_histories: フロントエンド向けペイロードリスト（新→旧順）
            - no_more_user_message_left: これ以上ユーザーメッセージがない場合 True
        """
        if not histories:
            return [], True

        stop_index = len(histories)
        previous_chat_histories: list[dict] = []

        while limit > 0:
            last_user_message_index = next(
                (
                    i
                    for i in range(stop_index - 1, -1, -1)
                    if (
                        histories[i].role == LLMMessageRole.USER
                        or (
                            histories[i].content == SESSION_START_MESSAGE
                            and histories[i].role == LLMMessageRole.DEVELOPER
                        )
                    )
                ),
                None,
            )

            if last_user_message_index is None:
                break

            user_message = histories[last_user_message_index]
            assistant_message_added = False
            workflow_response_exists = False
            llm_responses: list[dict] = []

            for index in range(last_user_message_index + 1, stop_index):
                history = histories[index]

                if history.role == LLMMessageRole.TOOL:
                    if not history.content:
                        continue

                    if history.tool_name == ToolName.START_WORKFLOW:
                        # ワークフロー実行前のユーザーメッセージを取得するためのフラグ
                        workflow_response_exists = True
                    elif ToolName.is_position_search_tool(history.tool_name):
                        parsed_output = self.parse_tool_output(history.content)

                        if "Message" not in parsed_output:
                            tool_call_id = history.tool_call_id
                            tool_input = history.tool_input
                            salary = tool_input.get("Salary")
                            locations = tool_input.get("Locations")
                            if not tool_call_id or not salary or not locations:
                                self._logger.error(
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
                                    self._logger.error(
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
                        parsed_output = self.parse_tool_output(history.content)
                        jobtypes_search_result = self.process_jobtype_search_result(
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

            if llm_responses or workflow_response_exists:
                limit -= 1

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
