from __future__ import annotations

import base64
import os
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp


def create_request_id() -> str:
    """
    タイムスタンプとランダム値を組み合わせた一意なリクエストIDを生成する。

    Returns:
        str: 生成されたリクエストID
    """
    now = datetime.now()
    return f"{now:%Y%m%d%H%M%S}.{now.microsecond:06d}.{random.randint(0, 999999):06d}"


def create_basic_auth_header() -> str | None:
    """
    環境変数からBasic認証ヘッダー値を生成する。

    Returns:
        str | None: `Basic <token>` 形式の文字列。未設定の場合は None。
    """
    username = os.getenv("BASIC_AUTH_USERNAME", "")
    password = os.getenv("BASIC_AUTH_PASSWORD", "")
    if not username or not password:
        return None
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


@dataclass
class HTTPResult:
    data: Any
    http_status: int
    error: str | None = None


class HeadlessAPIClient:
    def __init__(self, api_url: str, user_agent: str = "AICA E2E Headless") -> None:
        """
        APIクライアントを初期化する。

        Args:
            api_url (str): APIのベースURL
            user_agent (str): User-Agentヘッダー値

        Returns:
            None
        """
        self.api_url = api_url.rstrip("/")
        self.user_agent = user_agent
        self._session: aiohttp.ClientSession | None = None
        self.session_id = ""

    async def __aenter__(self) -> "HeadlessAPIClient":
        """
        非同期コンテキストマネージャの開始処理。

        Returns:
            HeadlessAPIClient: 自身のインスタンス
        """
        await self.open()
        return self

    async def __aexit__(self, *_args) -> None:
        """
        非同期コンテキストマネージャの終了処理。

        Returns:
            None
        """
        await self.close()

    async def open(self) -> None:
        """
        HTTPセッションを開く。未開の場合のみ新規作成する。

        Returns:
            None
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar(),
                headers={"User-Agent": self.user_agent},
                timeout=aiohttp.ClientTimeout(total=60),
            )

    async def close(self) -> None:
        """
        HTTPセッションを閉じて破棄する。

        Returns:
            None
        """
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    def set_session_id(self, session_id: str) -> None:
        """
        リクエストヘッダーに付与するセッションIDを設定する。

        Args:
            session_id (str): セッションID

        Returns:
            None
        """
        self.session_id = session_id

    def _headers(self, source_component: str | None = None) -> dict[str, str]:
        """
        リクエストヘッダー辞書を構築して返す。

        Args:
            source_component (str | None): X-SOURCE-COMPONENT ヘッダー値

        Returns:
            dict[str, str]: リクエストヘッダー辞書
        """
        headers = {
            "Content-Type": "application/json",
            "X-REQUEST-ID": create_request_id(),
        }
        if self.session_id:
            headers["X-SESSION-ID"] = self.session_id
        basic_auth = create_basic_auth_header()
        if basic_auth:
            headers["Authorization"] = basic_auth
        if source_component:
            headers["X-SOURCE-COMPONENT"] = source_component
        return headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
        source_component: str | None = None,
    ) -> HTTPResult:
        """
        HTTPリクエストを送信して結果を返す。

        Args:
            method (str): HTTPメソッド (GET/POST/PUT など)
            path (str): APIパス
            data (Any | None): リクエストボディ (JSON)
            params (dict[str, Any] | None): クエリパラメータ
            source_component (str | None): X-SOURCE-COMPONENT ヘッダー値

        Returns:
            HTTPResult: レスポンスデータ・ステータスコード・エラー情報
        """
        await self.open()
        assert self._session is not None

        async with self._session.request(
            method=method,
            url=f"{self.api_url}/{path.lstrip('/')}",
            json=data,
            params=params,
            headers=self._headers(source_component=source_component),
        ) as response:
            content_type = response.headers.get("content-type", "")
            payload = None
            if "application/json" in content_type:
                payload = await response.json()
            else:
                payload = await response.text()
            return HTTPResult(
                data=payload,
                http_status=response.status,
                error=None if response.ok else str(payload),
            )

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        source_component: str | None = None,
    ) -> HTTPResult:
        """
        GETリクエストを送信して結果を返す。

        Args:
            path (str): APIパス
            params (dict[str, Any] | None): クエリパラメータ
            source_component (str | None): X-SOURCE-COMPONENT ヘッダー値

        Returns:
            HTTPResult: レスポンスデータ・ステータスコード・エラー情報
        """
        return await self.request(
            "GET",
            path,
            params=params,
            source_component=source_component,
        )

    async def post(
        self,
        path: str,
        *,
        data: Any | None = None,
        source_component: str | None = None,
    ) -> HTTPResult:
        """
        POSTリクエストを送信して結果を返す。

        Args:
            path (str): APIパス
            data (Any | None): リクエストボディ (JSON)
            source_component (str | None): X-SOURCE-COMPONENT ヘッダー値

        Returns:
            HTTPResult: レスポンスデータ・ステータスコード・エラー情報
        """
        return await self.request(
            "POST",
            path,
            data=data,
            source_component=source_component,
        )

    async def put(
        self,
        path: str,
        *,
        data: Any | None = None,
        source_component: str | None = None,
    ) -> HTTPResult:
        """
        PUTリクエストを送信して結果を返す。

        Args:
            path (str): APIパス
            data (Any | None): リクエストボディ (JSON)
            source_component (str | None): X-SOURCE-COMPONENT ヘッダー値

        Returns:
            HTTPResult: レスポンスデータ・ステータスコード・エラー情報
        """
        return await self.request(
            "PUT",
            path,
            data=data,
            source_component=source_component,
        )
