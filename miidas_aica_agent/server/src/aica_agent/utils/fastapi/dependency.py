import asyncio
import logging
import re
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Request, status

from containers import Container
from domain.entities.chat_session import ChatSessionStatus
from repositories.action_log_repo import ActionLogRepository, ActionLogType
from repositories.chat_repo import ChatRepository
from services.rate_limit_service import RateLimitService
from utils.client_utils import get_client_ip
from utils.const import LOGGER_PREFIX
from utils.crypt import decrypt
from utils.enum import ComponentName, EncryptKeyType
from utils.log_utils import get_session_id

logger = logging.getLogger(f"{LOGGER_PREFIX}.{__name__}")


# 分析用のログ出力
@inject
async def source_component_analysis(
    request: Request,
    action_log_repository: ActionLogRepository = Depends(
        Provide[Container.action_log_repository]
    ),
):
    """遷移元コンポーネントの情報を分析ログへ出力する依存関数"""

    source_component = request.headers.get("X-SOURCE-COMPONENT")
    if source_component is None or source_component == ComponentName.POSITION:
        # 遷移元情報がない場合（リロード時）、および遷移元がポジション一覧の場合はそのままログ出力
        await asyncio.to_thread(
            action_log_repository.insert,
            log_type=ActionLogType.POSITION_DETAIL,
            source=source_component,
        )
        return

    # 遷移元がおすすめ一覧の場合は「recommendation_[暗号化済みテーマ名]」の形式
    # アンダースコアで分割しテーマを取得
    parts = source_component.split("_", 1)
    if len(parts) == 2 and parts[0] == ComponentName.RECOMMENDATION:
        source_component = parts[0]
        encrypted_theme = parts[1]

        try:
            decoded_theme = decrypt(EncryptKeyType.POSITION, encrypted_theme)
            sanitized_theme = re.sub(r"[^a-zA-Z0-9_.-]", "", decoded_theme)
            await asyncio.to_thread(
                action_log_repository.insert,
                log_type=ActionLogType.POSITION_DETAIL,
                source=f"{source_component}_{sanitized_theme}",
            )
        except Exception:
            logger.exception("Failed to decrypt theme")


@inject
def session_status_validator(
    chat_repository: ChatRepository = Depends(Provide[Container.chat_repository]),
    required_session_statuses=[
        ChatSessionStatus.APPLYING,
        ChatSessionStatus.REGISTERING,
    ],
):
    session_status = chat_repository.session_status()
    if session_status not in required_session_statuses:
        raise HTTPException(status_code=400, detail="Invalid session status")


@inject
async def check_rate_limit_for_position_detail(
    request: Request,
    rate_limit_svc: RateLimitService = Depends(Provide[Container.rate_limit_svc]),
):
    """
    求人詳細閲覧のレート制限をチェックする依存関数
    """
    is_allowed = await asyncio.to_thread(
        rate_limit_svc.is_within_position_detail_limit,
        get_session_id(),
        get_client_ip(request),
    )
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )


@inject
async def check_rate_limit_for_load_more_positions(
    request: Request,
    rate_limit_svc: RateLimitService = Depends(Provide[Container.rate_limit_svc]),
):
    """
    求人をもっと見るのレート制限をチェックする依存関数
    """
    is_allowed = await asyncio.to_thread(
        rate_limit_svc.is_within_load_more_positions_limit,
        get_session_id(),
        get_client_ip(request),
    )
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )


@inject
async def check_rate_limit_for_position_search(
    request: Request,
    rate_limit_svc: RateLimitService = Depends(Provide[Container.rate_limit_svc]),
):
    """
    求人検索のレート制限をチェックする依存関数
    """
    is_allowed = await asyncio.to_thread(
        rate_limit_svc.is_within_position_search_limit,
        get_session_id(),
        get_client_ip(request),
    )
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
        )
