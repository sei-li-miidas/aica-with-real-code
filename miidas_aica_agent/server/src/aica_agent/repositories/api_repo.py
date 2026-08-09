"""
AICA APIリクエスト
"""

from dependency_injector import resources
import aiohttp

from utils.enum import HttpMethod
from utils.http import request


class AICAAPIRepository(resources.AsyncResource):
    _session = None

    async def init(
        self,
        timeout: int,
        aica_api_url: str,
    ):
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        self._session = aiohttp.ClientSession(
            base_url=aica_api_url, timeout=timeout_config
        )

        return self

    async def shutdown(self, _: None):
        if self._session is not None:
            await self._session.close()

    async def get(
        self,
        path: str,
        **kwargs,
    ) -> tuple[int, dict | list | None]:
        """
        指定されたURLに対してHTTP GETリクエストを実行します。
        Args:
            path (str): GETリクエストを送信する対象パス。
            **kwargs: requestメソッドに渡す追加引数。aiohttp.ClientSession.requestのkwargs参照
        Returns:
            tuple:
                - HTTPステータスコード（intまたはNone）
                - パースされたJSONレスポンス（dict、listまたはNone）
        """
        return await request(
            self._session,
            HttpMethod.GET,
            path,
            **kwargs,
        )

    async def post(self, path: str, **kwargs) -> tuple[int, dict | list | None]:
        """
        指定されたURLに対してHTTP POSTリクエストを実行します。
        Args:
            path (str): POSTリクエストを送信する対象パス。
            **kwargs: requestメソッドに渡す追加引数。aiohttp.ClientSession.requestのkwargs参照
        Returns:
            tuple:
                - HTTPステータスコード（intまたはNone）
                - パースされたJSONレスポンス（dict、listまたはNone）
        """
        return await request(
            self._session,
            HttpMethod.POST,
            path,
            **kwargs,
        )
