"""Stream event processor — LLMRunStream.stream_events() の event loop と response yield を担う。

StreamEventProcessor は stream から届く event を受け取り、frontend response を yield しながら
turn の outcome（continuation_state, agent_state, stop_at_tool フラグ）を集約する。

責務
-----
- `LLMRunStream.stream_events()` の async iteration
- `event.type == "raw_response_event"` / `"run_item_stream_event"` 分岐
- `raw_response_event` → `StreamGuard.process_chunk()` 経由でセキュリティ検査してから yield（task-3）
  stream_guard が None の場合は `ChatStreamResponse.create_agent_message_response()` を直接 yield
  stream_guard が指定された場合、セキュリティ検知後は ERROR response を yield して終了する
- `run_item_stream_event` → `ChatPersistence.save_chat_history()` 呼び出しと
  `is_stop_at_tool` コールバック評価
- `ToolCallItem` → `ToolEventHandler.handle_tool_call()` へ委譲（task-2）
- `ToolCallOutputItem` → `ToolEventHandler.handle_tool_output()` へ委譲し yield（task-2）
- stream 終了後の continuation_state / agent_state 収集
- `append_stop_at_tool_outputs` コールバックによる tool replay 追加
- `run_stream.aclose()` の安全なクリーンアップ

スコープ外（後続 task で抽出する）
-----------
- WorkflowChatHandler（task-4）
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from agents import ToolCallItem, ToolCallOutputItem

from domain.entities.chat_session import ChatSessionStatus
from services.chat.chat_persistence import ChatPersistence
from services.chat.llm_runner import LLMRunStream
from utils.chat_response import (
    ChatResponseType,
    ChatStreamResponse,
    ChatStreamResponseModel,
)

if TYPE_CHECKING:
    from services.chat.stream_guard import StreamGuard
    from services.chat.tool_event_handler import ToolEventHandler


class StreamEventProcessor:
    """LLMRunStream を消費し、frontend response を yield しながら turn outcome を収集する。

    Parameters
    ----------
    chat_persistence:
        `run_item_stream_event` の item を ChatHistory として保存する。
    is_stop_at_tool:
        item が stop-at-tool 条件を満たすかを判定するコールバック。
        ``is_stop_at_tool(item) -> bool`` のシグネチャを持つ。
    append_stop_at_tool_outputs:
        stop_at_tool が発生した後に replay items を conversation へ追加する
        コールバック。
        ``append_stop_at_tool_outputs(replay_items, stop_at_tool_exists) -> None``
        のシグネチャを持つ。
    update_active_agent:
        stream 終了後に active_agent_name を更新するコールバック。
        ``update_active_agent(agent_name) -> None`` のシグネチャを持つ。
    update_continuation_state:
        stream 終了後に continuation_state を保存するコールバック。
        ``update_continuation_state(state) -> None`` のシグネチャを持つ。
    """

    def __init__(
        self,
        chat_persistence: ChatPersistence,
        is_stop_at_tool: Callable[[Any], bool],
        append_stop_at_tool_outputs: Callable[[list[Any], bool], None],
        update_active_agent: Callable[[str], None],
        update_continuation_state: Callable[[Any], None],
    ) -> None:
        self._chat_persistence = chat_persistence
        self._is_stop_at_tool = is_stop_at_tool
        self._append_stop_at_tool_outputs = append_stop_at_tool_outputs
        self._update_active_agent = update_active_agent
        self._update_continuation_state = update_continuation_state

    async def process(
        self,
        run_stream: LLMRunStream,
        chat_response: ChatStreamResponse,
        session_status: ChatSessionStatus,
        tool_event_handler: ToolEventHandler,
        client_ip: str = "",
        stream_guard: StreamGuard | None = None,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """LLMRunStream を反復し、frontend response を yield する。

        stream 終了後に continuation_state、agent_state、stop_at_tool outputs を収集する。
        run_stream.aclose() は正常終了・例外時に finally で呼ぶ。asyncio.CancelledError 時は呼ばない。

        Args:
            run_stream: `LLMRunner.run_streamed()` が返した run stream。
            chat_response: frontend response builder。session status / position_id を保持する。
            session_status: 現在のセッション状態。レスポンス生成に使う。
            tool_event_handler: ToolCallItem / ToolCallOutputItem を処理するハンドラ。
            client_ip: ToolEventHandler の rate limit チェックに使うクライアント IP。
            stream_guard: raw_response_event のセキュリティ検査を担う StreamGuard。
                None の場合はセキュリティ検査を行わずデルタをそのまま yield する。

        Yields:
            ChatStreamResponseModel: frontend へ送る各チャンクレスポンス。
        """
        stop_at_tool_exists = False
        _cancelled = False
        _security_stopped = False
        _received_message_id: str | None = None
        try:
            if stream_guard is not None:
                stream_guard.reset()
            async for event in run_stream.stream_events():
                if event.type == "raw_response_event" and event.delta:
                    if _received_message_id is None:
                        _received_message_id = event.item_id
                    elif _received_message_id != event.item_id:
                        # Lock the first item_id seen; skip any event with a different
                        # item_id to prevent duplicate text from parallel response segments.
                        continue
                    if stream_guard is not None:
                        _chunk_was_error = False
                        async for chunk in stream_guard.process_chunk(
                            event.item_id,
                            event.delta,
                            chat_response,
                            session_status,
                        ):
                            yield chunk
                            if chunk.response_type == ChatResponseType.ERROR:
                                _chunk_was_error = True
                        if _chunk_was_error:
                            _security_stopped = True
                    else:
                        yield chat_response.create_agent_message_response(
                            event.item_id,
                            event.delta,
                            session_status,
                        )
                    if _security_stopped:
                        return
                    continue

                if event.type != "run_item_stream_event":
                    continue

                await asyncio.to_thread(
                    self._chat_persistence.save_chat_history, event.item
                )
                if not stop_at_tool_exists and self._is_stop_at_tool(event.item):
                    stop_at_tool_exists = True

                if isinstance(event.item, ToolCallItem):
                    await tool_event_handler.handle_tool_call(event.item, client_ip)
                elif isinstance(event.item, ToolCallOutputItem):
                    async for chunk in tool_event_handler.handle_tool_output(
                        event.item, chat_response, session_status
                    ):
                        yield chunk
                    updated_session_status = (
                        tool_event_handler.consume_session_status_update()
                    )
                    if isinstance(updated_session_status, ChatSessionStatus):
                        session_status = updated_session_status
        except asyncio.CancelledError:
            _cancelled = True
            raise
        finally:
            if run_stream.continuation_state is not None:
                self._update_continuation_state(run_stream.continuation_state)
            agent_state = run_stream.agent_state
            if agent_state is not None and hasattr(agent_state, "name"):
                self._update_active_agent(agent_state.name)

            self._append_stop_at_tool_outputs(
                run_stream.replay_items,
                stop_at_tool_exists,
            )
            if not _cancelled:
                with suppress(Exception):
                    await run_stream.aclose()
