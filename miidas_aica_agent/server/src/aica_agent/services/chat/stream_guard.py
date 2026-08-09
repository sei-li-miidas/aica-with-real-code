"""StreamGuard — LLMOutputGuard のストリーミングセキュリティ検査を担うコンポーネント。

StreamGuard は raw_response_event に届くテキストデルタに対して LLMOutputGuard を呼び出し、
禁止ワード検知時にセッションブロックと detector state cleanup を行う。

責務
-----
- `LLMOutputGuard.reset_session_for_new_response()` による per-response リセット
- `LLMOutputGuard.process_stream_chunk()` による逐次チャンク検査
- `LLMOutputGuard.finalize_stream()` によるストリーム終了後の保留バッファ解放
- `LLMOutputGuard.remove_session()` による idempotent cleanup
- 禁止ワード検知時: `ChatPersistence.block_session()` を起動後 ERROR レスポンスを返す

スコープ外
-----------
- WorkflowChatHandler（task-4）
- ToolEventHandler（task-2）
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator

from domain.entities.chat_session import ChatSessionStatus
from security.llm_output_guard import ForbiddenWordDetectedException, LLMOutputGuard
from services.chat.chat_persistence import ChatPersistence
from utils.chat_response import ChatStreamResponse, ChatStreamResponseModel
from utils.const import LOGGER_PREFIX

logger = logging.getLogger(f"{LOGGER_PREFIX}.services.chat.stream_guard")


class StreamGuard:
    """LLMOutputGuard のストリーミングセキュリティ検査を担うコンポーネント。

    1 つの chat() ターンに対して 1 インスタンスを生成する。
    session_id は生成時に LLM レスポンス開始前に固定し、GeneratorExit 時でも正しい ID で
    cleanup を行う（ContextVar の変更に影響されない）。

    Parameters
    ----------
    llm_output_guard:
        禁止ワード検知ガード（LLMOutputGuard 互換インスタンス）。
    chat_persistence:
        セッション作成・ブロック書き込み委譲先。
    session_id:
        このターンの LLM ストリームに使う session_id。
        ストリーム開始前（reset() 呼び出し前）に確定させること。
    """

    def __init__(
        self,
        llm_output_guard: LLMOutputGuard,
        chat_persistence: ChatPersistence,
        session_id: str,
    ) -> None:
        self._guard = llm_output_guard
        self._chat_persistence = chat_persistence
        self._session_id = session_id
        # ストリーム中に受け取った最後の item_id。finalize() 時に保留バッファを送信するために使う。
        self._last_item_id: str | None = None
        self._security_detected = False

    @property
    def security_detected(self) -> bool:
        """禁止ワード検知が発生した場合 True を返す。"""
        return self._security_detected

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """LLM 応答開始前にバッファをリセットし、detector session を登録する。"""
        self._guard.reset_session_for_new_response(self._session_id)

    async def process_chunk(
        self,
        item_id: str,
        delta: str,
        chat_response: ChatStreamResponse,
        session_status: ChatSessionStatus,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """テキストデルタを検査し、安全なチャンクのみを yield する。

        禁止ワードが検知された場合は cleanup とセッションブロックを行い、
        ERROR レスポンスを yield してから StopAsyncIteration する。

        Yields
        ------
        ChatStreamResponseModel
            安全確認済みのテキストデルタ、またはエラー時の ERROR レスポンス。
        """
        self._last_item_id = item_id
        try:
            safe_chunks = self._guard.process_stream_chunk(
                session_id=self._session_id,
                chunk=delta,
            )
            for safe_chunk in safe_chunks:
                yield chat_response.create_agent_message_response(
                    item_id,
                    safe_chunk,
                    session_status,
                )
        except ForbiddenWordDetectedException as exc:
            yield await self._handle_security_detection(exc, session_status, chat_response)

    async def finalize(
        self,
        chat_response: ChatStreamResponse,
        session_status: ChatSessionStatus,
    ) -> AsyncGenerator[ChatStreamResponseModel, None]:
        """ストリーム終了後の保留バッファを解放し、残余チャンクを yield する。

        finalize_stream() が ForbiddenWordDetectedException を上げた場合は
        cleanup とセッションブロックを行い、ERROR レスポンスを yield する。

        保留バッファは `_last_item_id` に紐づけて送信する。
        ストリーム中に 1 件もチャンクが届かなかった場合（`_last_item_id=None`）は
        保留バッファを送信しない（item_id が不明なため）。

        Yields
        ------
        ChatStreamResponseModel
            保留バッファから解放されたテキストデルタ、またはエラー時の ERROR レスポンス。
        """
        try:
            final_chunks = self._guard.finalize_stream(self._session_id)
            if self._last_item_id:
                for final_chunk in final_chunks:
                    yield chat_response.create_agent_message_response(
                        self._last_item_id,
                        final_chunk,
                        session_status,
                    )
        except ForbiddenWordDetectedException as exc:
            yield await self._handle_security_detection(exc, session_status, chat_response)

    def cleanup(self) -> None:
        """Detector の session state を idempotent に解放する。

        すでに解放済みの場合は no-op（LLMOutputGuard.remove_session() が冪等のため）。
        """
        self._guard.remove_session(self._session_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _handle_security_detection(
        self,
        error: ForbiddenWordDetectedException,
        session_status: ChatSessionStatus,
        chat_response: ChatStreamResponse,
    ) -> ChatStreamResponseModel:
        """禁止ワード検知時の共通処理。

        1. `remove_session()` で detector state を cleanup（finally 保証）
        2. `block_session()` を呼ぶ（失敗時もログのみで握りつぶす）
        3. ERROR レスポンスを返す
        """
        self._security_detected = True
        try:
            logger.warning(
                "FORBIDDEN_WORD_DETECTED_IN_STREAM",
                extra={"stream_session_id": self._session_id, "word": error.word},
            )
        finally:
            # guarantee remove_session() runs even if logger.warning() somehow raises
            self._guard.remove_session(self._session_id)

        try:
            await asyncio.to_thread(self._chat_persistence.block_session)
        except Exception:
            logger.exception("block_session() failed")

        return chat_response.create_error_response(
            "不適切な出力を検知したので、応答をストップしました。",
            session_status,
        )
