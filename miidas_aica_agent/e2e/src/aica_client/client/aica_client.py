from __future__ import annotations

import asyncio
import json
import time
from typing import Any
from urllib.parse import urlencode, urlsplit

import websockets

from models import (
    ChatRequestPayload,
    ChatResponseType,
    ChatStreamResponseModel,
    ResponseExchange,
)
from utils.http import create_basic_auth_header


class AICAClient:
    def __init__(self, url: str, model: Any, system_prompt: str, client_id: str):
        """
        初期化

        Args:
            url (str): キャリアアドバイザーのWebSocket URL
            model (Any): 求職者LLM model
            system_prompt (str): 求職者システムプロンプト
            client_id (str): キャリアアドバイザークライアントID
        """
        self.url = url
        self.ws: Any = None
        self.client_id = client_id
        self.model = model
        self.system_prompt = system_prompt

    def _build_origin(self, endpoint: str) -> str | None:
        """
        WebSocket接続先からOriginヘッダーの値を生成します。

        Args:
            endpoint (str): 接続先のWebSocket URL

        Returns:
            str | None: Originヘッダー値。不要な場合はNone
        """
        parsed = urlsplit(endpoint)
        if parsed.scheme not in {"ws", "wss"} or not parsed.netloc:
            return None

        host = parsed.hostname or ""
        if host in {"localhost", "127.0.0.1", "::1"}:
            return None

        origin_scheme = "https" if parsed.scheme == "wss" else "http"
        return f"{origin_scheme}://{parsed.netloc}"

    async def connect(
        self,
        session_id: str | None = None,
        open_timeout_seconds: float = 30.0,
    ) -> None:
        """
        キャリアアドバイザーサーバーに接続する。

        Args:
            session_id (str | None): 再接続時に引き継ぐセッションID
            open_timeout_seconds (float): WebSocket接続タイムアウト秒数

        Returns:
            None
        """
        endpoint = self.url
        if session_id:
            query = urlencode({"session_id": session_id})
            separator = "&" if "?" in endpoint else "?"
            endpoint = f"{endpoint}{separator}{query}"

        origin = self._build_origin(endpoint)

        additional_headers: dict[str, str] = {}
        basic_auth = create_basic_auth_header()
        if basic_auth:
            additional_headers["Authorization"] = basic_auth

        try:
            self.ws = await websockets.connect(
                endpoint,
                ping_interval=None,
                ping_timeout=None,
                open_timeout=open_timeout_seconds,
                origin=origin,
                additional_headers=additional_headers or None,
            )
        except TimeoutError as exc:
            raise RuntimeError(
                f"{self.client_id} WebSocket opening handshake timed out after "
                f"{open_timeout_seconds}s: {endpoint}"
            ) from exc

    async def send_request(self, payload: ChatRequestPayload) -> None:
        """
        キャリアアドバイザーへリクエストを送信する。

        Args:
            payload (ChatRequestPayload): 送信するリクエスト情報

        Returns:
            None
        """
        if not self.ws:
            raise RuntimeError("WebSocket is not connected")
        await self.ws.send(json.dumps(payload.to_ws_payload(), ensure_ascii=False))

    async def receive_exchange(self) -> ResponseExchange:
        """
        キャリアアドバイザーサーバーからレスポンスイベント群を受信する。

        Returns:
            ResponseExchange: セッション情報と応答時間を含む受信結果
        """
        if not self.ws:
            raise RuntimeError("WebSocket is not connected")

        start_time = time.time()
        first_message_time: float | None = None
        events: list[ChatStreamResponseModel] = []

        while True:
            try:
                raw = await self.ws.recv()
            except websockets.exceptions.ConnectionClosedError as exc:
                raise RuntimeError(f"{self.client_id} 接続切断: {exc}") from exc

            event = ChatStreamResponseModel.model_validate_json(raw)
            events.append(event)

            if (
                event.response_type != ChatResponseType.END
                and first_message_time is None
            ):
                first_message_time = time.time()

            if event.response_type in (ChatResponseType.END, ChatResponseType.ERROR):
                break

        end_time = time.time()
        if first_message_time is None:
            first_message_time = end_time

        return ResponseExchange(
            events=events,
            first_msg_duration=first_message_time - start_time,
            total_duration=end_time - start_time,
        )

    def _build_job_seeker_input(
        self,
        advisor_message: str,
        recent_history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        求職者LLMに渡す入力文を構築する。

        Args:
            advisor_message (str): 最新のアドバイザーメッセージ
            recent_history (list[dict[str, str]] | None): 直近の会話履歴

        Returns:
            str: 求職者LLM向けの入力文
        """
        history_block = ""
        if recent_history:
            formatted_history = "\n".join(
                f"- {item['speaker']}: {item['message']}" for item in recent_history
            )
            history_block = f"## 直近の会話履歴\n{formatted_history}\n\n"

        return (
            "以下はミイダス AI転職アドバイザーからの最新メッセージです。\n"
            "あなたは求職者本人として、このメッセージに対する次の発話だけを日本語で返してください。\n"
            "キャリアアドバイザーとして話したり、面談を主導したりしてはいけません。\n"
            "直近の自分の発話と同じ内容を繰り返さず、会話を一歩進める返答にしてください。\n"
            "回答は自然な会話文のみを返してください。\n\n"
            f"{history_block}"
            "## キャリアアドバイザーの最新メッセージ\n"
            f"{advisor_message}"
        )

    async def ask_job_seeker(
        self,
        message: str,
        recent_history: list[dict[str, str]] | None = None,
    ) -> tuple[float, str]:
        """
        求職者LLMにメッセージを送信する。

        Args:
            message (str): 最新のアドバイザーメッセージ
            recent_history (list[dict[str, str]] | None): 直近の会話履歴

        Returns:
            tuple[float, str]: (
                agent_invoke_time: LLM応答までの経過時間
                response_message: LLM応答メッセージ
            )
        """
        started = time.time()
        response_message = await self._ask_job_seeker_with_retry(
            self._build_job_seeker_input(message, recent_history)
        )
        duration = time.time() - started
        return duration, str(response_message)

    async def _ask_job_seeker_with_retry(self, message: str) -> str:
        """
        スロットリング時にリトライしながら求職者LLMを呼び出す。

        Args:
            message (str): 求職者LLMに渡す入力文

        Returns:
            str: 求職者LLMの応答
        """
        delay_seconds = 1.0
        for attempt in range(10):
            try:
                return await self.model.ask(self.system_prompt, message)
            except Exception as exc:
                if not self._is_retryable_throttling_error(exc) or attempt == 9:
                    raise
                await asyncio.sleep(delay_seconds)
                delay_seconds *= 2
        raise RuntimeError("LLM retry loop terminated unexpectedly")

    def _is_retryable_throttling_error(self, exc: Exception) -> bool:
        """
        リトライ対象のスロットリング例外かどうかを判定する。

        Args:
            exc (Exception): 発生した例外

        Returns:
            bool: リトライ対象ならTrue
        """
        return (
            exc.__class__.__name__ == "ThrottlingException"
            or "ThrottlingException" in str(exc)
        ) and "Too many requests" in str(exc)

    async def close(self) -> None:
        """
        キャリアアドバイザーサーバーとの接続を切断する。

        Returns:
            None
        """
        if self.ws:
            await self.ws.close()
            self.ws = None
