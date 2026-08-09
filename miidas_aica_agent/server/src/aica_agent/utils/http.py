import asyncio
from datetime import datetime
import secrets
from aiohttp import ClientSession
from fastapi import status
from logging import getLogger

from utils.const import LOGGER_PREFIX
from utils.log_utils import get_request_id, get_session_id

_logger = getLogger(f"{LOGGER_PREFIX}.{__name__}")


def _generate_request_id() -> str:
    now = datetime.now()
    return (
        f"{now.strftime('%Y%m%d%H%M%S')}.{now.microsecond:06d}.{secrets.token_hex(4)}"
    )


async def request(
    client: ClientSession,
    method: str,
    path: str,
    **kwargs,
) -> tuple[int, dict | list | None]:
    """
    指定されたAPIパスに対して指定されたメソッドでHTTP リクエストを実行します。
    Args:
        path (str): リクエストを送信する対象パス。
        method (str): GET or POST
        **kwargs: requestメソッドに渡す追加引数。aiohttp.ClientSession.requestのkwargs参照
    Returns:
        HTTP Status
        Response Body
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # valueがNoneの場合、「Cannot serialize non-str key None」が発生するかもしれない。
    # 基本設定がないのはないはずですが、念の為
    session_id = get_session_id()
    if session_id is not None:
        headers["X-SESSION-ID"] = session_id

    request_id = get_request_id()
    if not request_id:
        request_id = _generate_request_id()
    headers["X-REQUEST-ID"] = request_id

    # Merge with kwargs headers, filtering None values
    if "headers" in kwargs:
        kwargs_headers = {k: v for k, v in kwargs["headers"].items() if v is not None}
        headers.update(kwargs_headers)

    kwargs["headers"] = headers
    _logger.debug("AICA APIリクエスト: %s %s %s", method, path, kwargs)

    try:
        async with client.request(method, path, **kwargs) as response:
            _logger.debug(
                "AICA APIレスポンス: %s %s %s",
                response.status,
                response.reason,
                await response.text(),
            )
            if response.status == status.HTTP_200_OK:
                if response.content_length == 0:
                    _logger.warning(
                        "API request to %s returned empty body: %s",
                        path,
                        response.status,
                    )
                    return response.status, None

                body = await response.text()
                if not body.strip():
                    _logger.warning(
                        "API request to %s returned empty body: %s",
                        path,
                        response.status,
                    )
                    return response.status, None

            return response.status, await response.json()
    except asyncio.TimeoutError:
        _logger.exception("Timeout calling AICA API: %s", path)
        return status.HTTP_408_REQUEST_TIMEOUT, None
    except Exception:
        _logger.exception("Error calling AICA API %s", path)
        return status.HTTP_500_INTERNAL_SERVER_ERROR, None
