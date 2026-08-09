"""
FastAPI入口
"""

import asyncio
from contextlib import asynccontextmanager
from core.maintenance_manager import startup_poller, shutdown_poller
from logging import getLogger
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from websockets.exceptions import ConnectionClosedError

from containers import Container
import endpoints
from services.chat.agent_runtime_config import log_startup_runtime_config
from services.chat.config_validator import validate_agent_runtime_config
from utils.log_utils import add_tracing_info, clear_tracing_info
from utils.const import LOGGER_PREFIX
from utils.env_utils import is_local

container = Container()
logger = getLogger(f"{LOGGER_PREFIX}.{__name__}")


def make_loop_exception_handler(prev_handler=None):
    def handler(loop, context):
        exc = context.get("exception")
        if isinstance(exc, ConnectionClosedError):
            # ConnectionClosedError (e.g., keepalive task) 無視
            logger.debug("ConnectionClosedError: %s", exc)
            return
        if prev_handler is not None:
            prev_handler(loop, context)
        else:
            loop.default_exception_handler(context)

    return handler


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_agent_runtime_config(container.config)
    log_startup_runtime_config(logger, container.config)
    await container.init_resources()

    await startup_poller()

    loop = asyncio.get_running_loop()
    prev = loop.get_exception_handler()
    loop.set_exception_handler(make_loop_exception_handler(prev))

    yield

    await shutdown_poller()

    await container.shutdown_resources()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def add_tracing_info_context(request: Request, call_next):
    """
    リクエスト毎にセッションIDとリクエストIDをcontextに追加する

    Args:
        request: リクエスト
        call_next: 次の処理

    Returns:
        レスポンス
    """
    add_tracing_info(request)
    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception(
            "Unhandled exception while processing %s %s",
            request.method,
            request.url.path,
        )
        raise
    finally:
        clear_tracing_info()


# CORSミドルウェアを追加（HTTPミドルウェアの後に追加することで全てのレスポンスに適用される）
# ローカル開発環境のみCORSを有効化（本番等は同一ドメインなので不要）
if is_local():
    # ローカル開発環境: 全てのオリジン、メソッド、ヘッダーを許可
    logger.info("CORS enabled (local development mode)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 本番、ステージング、開発環境: 同一ドメインなのでCORS不要
    logger.info("CORS disabled (same-origin access only)")


app.container = container
app.include_router(endpoints.router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    リクエストバリデーションエラー処理
    現在リクエストパラメータバリデーションはプロフィール入力しかないですが、
    フロントの方は制御しているので、サーバー側のバリデーションエラーが発生しないはず
    発生する場合、Attackかいたずらとしか考えられないので、詳細エラー内容を返さない。
    フロント側もサーバー側バリデーションエラーの発生を考慮してない。

    Args:
        request: リクエスト
        exc: 例外

    Returns:
        JSONResponse: エラーレスポンス
    """
    logger.error("ValidationError caught: %s for URL: %s", exc, request.url)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={},
    )


# 500エラー時にもCORSヘッダーを付与するグローバル例外ハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    グローバル例外ハンドラー

    Args:
        request: リクエスト
        exc: 例外

    Returns:
        JSONResponse: エラーレスポンス
    """
    # モジュールレベルのロガーを使用
    logger.exception("Unhandled Exception for URL: %s", request.url)
    # HTTPExceptionの場合はFastAPIのデフォルトハンドラーを使用
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)

    # ローカル開発環境の場合のみCORSヘッダーを付与
    cors_headers = {}
    if is_local():
        origin = request.headers.get("origin", "")
        if origin:
            cors_headers["Access-Control-Allow-Origin"] = origin
            cors_headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
        headers=cors_headers,
    )
