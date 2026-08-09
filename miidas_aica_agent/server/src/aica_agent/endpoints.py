"""
Websocket、Restful APIエンドポイントポ
"""

import asyncio
from datetime import datetime
import json
import logging
import uuid
from agents import trace
from dependency_injector.wiring import Provide, inject
from functools import partial
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    Query,
    Request,
    status,
)
from fastapi.responses import JSONResponse
from typing import Any, Optional
from urllib.parse import urlparse

from pydantic import ValidationError


from containers import Container
from core import maintenance_manager
from repositories.action_log_repo import ActionLogType
from domain.entities.chat_session import ChatSessionStatus
from domain.entities.user_profile import (
    JSONSearchName,
    JSONVerifyLocations,
    JSONLocation,
    JSONSearchKeyword,
    JSONUserProfileBasicInfo,
    JSONUserProfileCarrer,
    JSONUserProfileEducation,
    JSONUserProfileWill,
)
from schemas.workflow_requests import (
    JSONJobMatchDiagnosisSearchOccupationsRequest,
    JSONPositionChangeAnalyzeGenerateSummaryRequest,
)
from repositories.action_log_repo import ActionLogRepository
from services.chat.agent_runtime_config import (
    log_chat_turn_runtime,
    resolve_default_agent_model,
)
from services.chat.service_protocol import ChatServiceProtocol
from services.position_service import PositionService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from services.workflow_service import WorkflowService
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatStreamResponse
from utils.client_utils import get_client_ip
from utils.const import (
    API_PREFIX,
    LOGGER_PREFIX,
    MAINTENANCE_MESSAGE,
    RATE_LIMIT_EXCEEDED_MESSAGE,
)
from utils.enum import PageName
from utils.env_utils import get_env, is_local
from utils.fastapi.dependency import (
    check_rate_limit_for_load_more_positions,
    check_rate_limit_for_position_detail,
    check_rate_limit_for_position_search,
    source_component_analysis,
    session_status_validator,
)
from utils.log_utils import (
    get_session_id,
    set_request_id,
    set_session_id,
    clear_session_id,
)

logger = logging.getLogger(f"{LOGGER_PREFIX}.{__name__}")
router = APIRouter(prefix=API_PREFIX)


@router.get("/health")
async def health():
    """
    ヘルスチェックエンドポイント
    Returns:
        OK
    """
    return {"status": "OK"}


@router.get(
    "/positions/search/{search_key}/{offset}",
    dependencies=[
        Depends(check_rate_limit_for_load_more_positions),
    ],
)
@inject
async def load_more_positions(
    search_key: str,
    offset: int,
    limit: int = 5,
    position_svc: PositionService = Depends(Provide[Container.position_svc]),
    action_log_repository: ActionLogRepository = Depends(
        Provide[Container.action_log_repository]
    ),
):
    """
    求人検索結果のもっと見る
    Args:
        search_key (str): 検索キー。複数検索があるかもしれないので、区別のため
        offset (int): 読み込み開始位置
        limit (int): 読み込み件数上限（デフォルト: 5）
        position_svc: PositionServiceインスタンス
    Returns:
        dict: 求人総数と求人リスト
    """
    # 分析用のログ出力
    await asyncio.to_thread(
        action_log_repository.insert,
        log_type=ActionLogType.LOAD_MORE_POSITION,
        source=search_key,
        content={
            "offset": offset,
            "limit": limit,
        },
    )

    count, positions = await position_svc.load_more(
        search_key,
        offset,
        limit,
    )

    return {
        "TotalPositionCount": count,
        "Positions": positions,
    }


@router.get(
    "/positions/detail/{encrypted_position_id}",
    dependencies=[
        Depends(source_component_analysis),
        Depends(check_rate_limit_for_position_detail),
    ],
)
@inject
async def position_detail(
    encrypted_position_id: str,
    position_svc: PositionService = Depends(Provide[Container.position_svc]),
):
    """
    求人詳細情報取得
    Args:
        encrypted_position_id (str): 暗号化された求人ID
        position_svc: PositionServiceインスタンス
    Returns:
        dict: 求人詳細情報、見つからない場合は404エラー
    """
    detail = await position_svc.get_position_detail(encrypted_position_id)
    if detail:
        return detail
    else:
        # HTTPException利用の場合、同時にたくさんリクエストが来ている場合、サーバーが死んでしまうので、代わりにJSONResponseを利用します
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={},
        )


@router.get(
    "/companies/detail/{encrypted_position_id}",
)
@inject
async def company_detail(
    encrypted_position_id: str,
    position_svc: PositionService = Depends(Provide[Container.position_svc]),
):
    """
    企業詳細情報取得
    Args:
        encrypted_position_id (str): 暗号化された求人ID
        position_svc: PositionServiceインスタンス
    Returns:
        dict: 企業詳細情報、見つからない場合は404エラー
    """
    detail = await position_svc.get_company_detail(encrypted_position_id)
    if detail:
        return detail
    else:
        # Use JSONResponse instead of HTTPException to avoid concurrency issues
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={},
        )


@router.get(
    "/businesses/detail/{encrypted_position_id}",
)
@inject
async def business_detail(
    encrypted_position_id: str,
    position_svc: PositionService = Depends(Provide[Container.position_svc]),
):
    """
    事業詳細情報取得
    Args:
        encrypted_position_id (str): 暗号化された求人ID
        position_svc: PositionServiceインスタンス
    Returns:
        dict: 事業詳細情報、見つからない場合は404エラー
    """
    detail = await position_svc.get_business_detail(encrypted_position_id)
    if detail:
        return detail
    else:
        # Use JSONResponse instead of HTTPException to avoid concurrency issues
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={},
        )


@router.get(
    "/positions/recommendations/{search_key}/{encrypted_theme}",
)
@inject
async def position_recommendations(
    search_key: str,
    encrypted_theme: str,
    position_svc: PositionService = Depends(Provide[Container.position_svc]),
):
    """
    求人提案取得
    Args:
        search_key (str): 検索キー。複数検索があるかもしれないので、区別のため
        encrypted_theme (str): 暗号化されたテーマ
        position_svc: PositionServiceインスタンス
    Returns:
        dict: 検索キーと提案求人リスト
    """
    positions = await position_svc.get_position_recommendation(encrypted_theme)

    if not positions:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "SearchKey": search_key,
                "Positions": [],
            },
        )

    return {
        "SearchKey": search_key,
        "Positions": positions,
    }


@router.get(
    "/positions/re-search/{tool_call_id}",
    dependencies=[
        Depends(check_rate_limit_for_position_search),
    ],
)
@inject
async def position_search_by_tool_call_id(
    tool_call_id: str,
    position_svc: PositionService = Depends(Provide[Container.position_svc]),
):
    """
    ポジション検索ツールパラメータでの再検索
    Args:
        tool_call_id (str): ツールコールID。
        position_svc: PositionServiceインスタンス
    Returns:
        ツール実行と同じフォーマットのポジション検索結果
    """
    positions = await position_svc.search_positions_by_tool_call_id(tool_call_id)

    if not positions:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={},
        )

    return positions


@router.post(
    "/positions/search/jobtype_specific",
    dependencies=[
        Depends(check_rate_limit_for_position_search),
    ],
)
@inject
async def jobtype_specific_position_search(
    json_request: dict[str, Any],
    position_svc: PositionService = Depends(Provide[Container.position_svc]),
):
    """
    職種別のポジション検索
    Args:
        json_request: クライアントからの検索条件
        position_svc: PositionServiceインスタンス
    Returns:
        ツール実行と同じフォーマットのポジション検索結果
    """
    positions = await position_svc.jobtype_specific_position_search(json_request)

    return positions


@router.get("/positions/search_filter/current")
@inject
async def current_search_filter(
    position_svc: PositionService = Depends(Provide[Container.position_svc]),
):
    """
    最新ポジション検索条件取得
    Args:
        position_svc: PositionServiceインスタンス
    Returns:
        最新ポジション検索条件取得
    """
    result = await position_svc.current_search_filter()
    return result


@router.get("/positions/search_filter/jobtype")
@inject
async def jobtype_other_filter(
    jobtype_name: str = Query(..., alias="JobtypeName", description="職種名"),
    position_svc: PositionService = Depends(Provide[Container.position_svc]),
):
    """
    指定職種の詳細検索条件取得
    Args:
        jobtype_name: クライアントからの職種名
        position_svc: PositionServiceインスタンス
    Returns:
        指定職種の詳細検索条件
    """
    result = await position_svc.jobtype_other_filter(jobtype_name)
    return result


@router.get(
    "/master/",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def search_master_data(
    names: list[str] = Query(..., description="取得するマスターデータ名のリスト"),
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    マスターデータ取得
    Args:
        names: 取得するマスターデータ名のリスト
        user_svc: UserServiceインスタンス
    Returns:
        dict: マスターデータ、エラーの場合は500エラー
    """
    logger.debug("endpoint search_master_data names: %s", names)
    result = await user_svc.search_master_data(names)
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )
    else:
        return result


@router.post(
    "/location/verify/prefecture/city",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def search_location_by_prefecture_city(
    json_request: JSONVerifyLocations,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    指定の都道府県・市区町村検索
    Args:
        json_request: JSONVerifyLocationsモデル
        user_svc: UserServiceインスタンス
    Returns:
        list: 検索結果の都道府県、市区町村リスト、エラーの場合は500エラー
    """
    logger.debug("endpoint search_location_by_prefecture_city %s", json_request)
    result = await user_svc.search_by_prefecture_city_name(
        [
            {
                "PrefectureName": location.prefecture_name
                if location.prefecture_name
                else "",
                "CityName": location.city_name,
            }
            for location in json_request.locations
        ]
    )
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )
    else:
        return result


@router.post("/location/search/commuting_areas")
@inject
async def search_commuting_areas(
    json_request: JSONLocation,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    勤務地検索
    Args:
        json_request: JSONLocationモデル
        user_svc: UserServiceインスタンス
    Returns:
        list: 検索結果の都道府県、市区町村リスト、エラーの場合は500エラー
    """
    logger.debug("endpoint search_commuting_areas %s", json_request)

    result = await user_svc.search_commuting_areas(
        json_request.prefecture_name if json_request.prefecture_name else "",
        json_request.city_name,
    )
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )
    else:
        return result


@router.post("/location/search/keyword")
@inject
async def search_location_by_keyword(
    json_request: JSONSearchKeyword,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    所在地検索
    Args:
        json_request: JSONSearchKeywordモデル
        user_svc: UserServiceインスタンス
    Returns:
        list: 検索結果の都道府県、市区町村リスト、エラーの場合は500エラー
    """
    logger.debug("endpoint search_location_by_keyword %s", json_request)
    result = await user_svc.search_location(json_request.keyword)
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )
    else:
        return result


@router.post(
    "/industry/search/keyword",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def search_industry(
    json_request: JSONSearchKeyword,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    業界検索
    Args:
        json_request: JSONSearchKeywordモデル
        user_svc: UserServiceインスタンス
    Returns:
        list: 検索結果の業界リスト、エラーの場合は500エラー
    """
    logger.debug("endpoint search_industry %s", json_request)
    result = await user_svc.search_industry(json_request.keyword)
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )
    else:
        return result


@router.post(
    "/jobtype/search/keyword",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def search_jobtype_by_keyword(
    json_request: JSONSearchKeyword,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    職種検索
    Args:
        json_request: JSONSearchKeywordモデル
        user_svc: UserServiceインスタンス
    Returns:
        list: 検索結果の職種リスト、エラーの場合は500エラー
    """
    logger.debug("endpoint search_jobtype_by_keyword %s", json_request)
    result = await user_svc.search_jobtype_by_keyword(json_request.keyword)
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )
    else:
        return result


@router.post(
    "/jobtype/search/names",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def search_jobtype_by_names(
    json_request: JSONSearchName,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    職種検索
    Args:
        json_request: JSONSearchNameモデル
        user_svc: UserServiceインスタンス
    Returns:
        list: 検索結果の職種リスト、エラーの場合は500エラー
    """
    logger.debug("endpoint search_jobtype_by_name %s", json_request)
    result = await user_svc.search_jobtype_by_names(json_request.names)
    if result is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )
    else:
        return result


@router.get(
    "/profile",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def get_profile(
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    保存プロフィール取得

    Args:
        user_svc: UserServiceインスタンス

    Returns:
        dict: 保存プロフィール
    """
    logger.debug("endpoint get_profile")
    result = user_svc.get_profile()

    if not result or not result.miidas_registration_user_data:
        return {}

    return result.miidas_registration_user_data


@router.post(
    "/profile/basic",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def save_basic_profile(
    basic_profile: JSONUserProfileBasicInfo,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    基本情報保存

    Args:
        basic_profile: 基本情報
        user_svc: UserServiceインスタンス

    Returns:
        dict: 保存結果
    """
    logger.debug(
        "endpoint save_basic_profile %s",
        basic_profile,
    )
    result = user_svc.save_basic_profile(
        basic_profile,
    )

    if not result:
        # raise HTTPException(status_code=404...) will make the server hang.
        # So instead of raising HTTPException, return a normal response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Success": False,
                "Message": "プロフィールの保存に失敗しました",
            },
        )

    return {
        "Success": True,
        "Message": "プロフィールを保存しました",
    }


@router.post(
    "/profile/education",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def save_education_profile(
    education_profile: JSONUserProfileEducation,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    学歴保存

    Args:
        education_profile: 学歴
        user_svc: UserServiceインスタンス

    Returns:
        dict: 保存結果
    """
    logger.debug(
        "endpoint save_education_profile %s",
        education_profile,
    )

    result = user_svc.save_education_profile(
        education_profile,
    )

    if not result:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Success": False,
                "Message": "学歴情報の保存に失敗しました",
            },
        )

    return {
        "Success": True,
        "Message": "学歴情報を保存しました",
    }


@router.post(
    "/profile/experience",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def save_experience_profile(
    experience_profile: JSONUserProfileCarrer,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    職歴保存

    Args:
        education_profile: 職歴
        user_svc: UserServiceインスタンス

    Returns:
        dict: 保存結果
    """
    logger.debug(
        "endpoint save_experience_profile %s",
        experience_profile,
    )

    result = user_svc.save_experience_profile(
        experience_profile,
    )

    if not result:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Success": False,
                "Message": "職務経歴の保存に失敗しました",
            },
        )

    return {
        "Success": True,
        "Message": "職務経歴を保存しました",
    }


@router.post(
    "/profile/preferences",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def save_preferences_profile(
    preferences_profile: JSONUserProfileWill,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    希望条件保存

    Args:
        education_profile: 希望条件
        user_svc: UserServiceインスタンス

    Returns:
        dict: 保存結果
    """
    logger.debug(
        "endpoint save_preferences_profile %s",
        preferences_profile,
    )

    result = user_svc.save_preferences_profile(
        preferences_profile,
    )

    if not result:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "Success": False,
                "Message": "希望条件の保存に失敗しました",
            },
        )

    return {
        "Success": True,
        "Message": "希望条件を保存しました",
    }


@router.post(
    "/apply/start",
)
@router.post(
    "/apply/{encrypted_position_id}/start",
)
@inject
async def apply_start(
    encrypted_position_id: str | None = None,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    応募開始

    Args:
        encrypted_position_id: 暗号化されたポジションID
        user_svc: UserServiceインスタンス

    Returns:
        チャットセッションステータス
    """
    session_status = await user_svc.start_apply(encrypted_position_id)
    if session_status:
        return {
            "session_status": session_status,
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={},
        )


@router.put(
    "/apply/{encrypted_position_id}/add",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def apply_add(
    encrypted_position_id: str,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    応募ポジション追加

    Args:
        encrypted_position_id: 暗号化されたポジションID
        user_svc: UserServiceインスタンス

    Returns:
    """
    session_status = await user_svc.apply_add_position(encrypted_position_id)
    if session_status:
        return {
            "session_status": session_status,
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={},
        )


@router.post(
    "/apply/finish",
    dependencies=[
        Depends(
            session_status_validator,
        ),
    ],
)
@inject
async def finish_apply(
    request: Request,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    面談応募・登録する

    Args:
        request: FastAPI Request
        user_svc: UserServiceインスタンス

    Returns:
        チャットセッションステータス
    """
    http_status, session_status, apply_result, detail = await user_svc.finish_apply(
        user_agent=request.headers.get("User-Agent"),
    )
    cookies = detail.pop("Cookies", None) if detail else None

    response = JSONResponse(
        status_code=http_status,
        content={
            "SessionStatus": session_status,
            "ApplyResult": apply_result,
            "Detail": detail,
        },
    )

    if cookies:
        for cookie in cookies:
            response.set_cookie(
                key=cookie.key,
                value=cookie.value,
                max_age=cookie.get("max-age"),
                expires=cookie.get("expires"),
                path=cookie.get("path") or "/",
                domain=cookie.get("domain"),
                secure=cookie.get("secure", False),
                httponly=cookie.get("httponly", False),
                samesite=cookie.get("samesite"),
            )

    return response


@router.post(
    "/apply/position/{encrypted_position_id}",
    dependencies=[
        Depends(
            partial(
                session_status_validator,
                required_session_statuses=[
                    ChatSessionStatus.APPLIED,
                    ChatSessionStatus.REGISTERED,
                ],
            ),
        ),
    ],
)
@inject
async def apply(
    encrypted_position_id: str,
    request: Request,
    user_svc: UserService = Depends(Provide[Container.user_svc]),
):
    """
    ポジション応募

    Args:
        encrypted_position_id: 暗号化されたポジションID（オプション）
        request: FastAPI Request
        user_svc: UserServiceインスタンス

    Returns:
        チャットセッションステータス
    """
    http_status, position_id = await user_svc.apply_position(
        encrypted_position_id,
        cookies=request.cookies,
        user_agent=request.headers.get("User-Agent"),
    )

    if http_status == status.HTTP_200_OK:
        return JSONResponse(
            status_code=http_status,
            content={
                "PositionID": position_id,
            },
        )

    return JSONResponse(
        status_code=http_status,
        content={},
    )


@router.get(
    "/chat/{position_id}/exist",
)
@inject
async def has_position_chat(
    position_id: str,
    chat_svc: ChatServiceProtocol = Depends(Provide[Container.chat_svc]),
):
    """
    指定ポジションの過去会話履歴が存在するか

    Args:
        position_id: 暗号化されたポジションID
        chat_svc: ChatServiceインスタンス

    Returns:
        200: チャット履歴が存在する
        404: チャット履歴が存在しない
    """
    try:
        exist = await chat_svc.check_if_previous_chat_histories_exist(position_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK if exist else status.HTTP_404_NOT_FOUND,
            content={},
        )
    except Exception:
        logger.exception("予期しないエラー")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )


@router.get(
    "/chat/previous",
)
@router.get(
    "/chat/previous/{position_id}",
)
@inject
async def load_previous_chat_histories(
    position_id: str | None = None,
    before_id: str = Query(None),
    limit: int = Query(5),
    chat_svc: ChatServiceProtocol = Depends(Provide[Container.chat_svc]),
):
    """
    過去会話履歴取得

    Args:
        position_id: 暗号化されたポジションID
        before_id: フロント側は取得済みメッセージの中に一番古いメッセージのID
        limit: 読み込み件数上限（デフォルト: 5）
        chat_svc: ChatServiceインスタンス

    Returns:
        過去会話履歴
    """
    try:
        (
            previous_chat_histories,
            no_more_user_message_left,
        ) = await chat_svc.load_previous_chat_histories(
            limit=limit,
            encrypted_position_id=position_id,
            before_id=before_id,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "PreviousChatHistories": previous_chat_histories,
                "NoMoreUserMessageLeft": no_more_user_message_left,
            },
        )
    except Exception:
        logger.exception("予期しないエラー")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )


@router.post("/workflow/job_match_diagnosis/search_occupations")
@inject
async def search_job_match_diagnosis_occupations(
    request: JSONJobMatchDiagnosisSearchOccupationsRequest,
    workflow_svc: WorkflowService = Depends(Provide[Container.workflow_svc]),
):
    """
    仕事の性質に基づく適職診断ワークフローの回答を元に職種を検索する

    Args:
        request: JSONJobMatchDiagnosisSearchOccupationsRequestモデル
        workflow_svc: WorkflowServiceインスタンス

    Returns:
        職種のリスト
    """
    try:
        return await workflow_svc.search_job_match_diagnosis_occupations(
            request.answers
        )
    except Exception:
        logger.exception("予期しないエラー")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=[],
        )


@router.post("/workflow/position_change_analyze/generate_summary")
@inject
async def generate_position_change_analyze_summary(
    request: JSONPositionChangeAnalyzeGenerateSummaryRequest,
    workflow_svc: WorkflowService = Depends(Provide[Container.workflow_svc]),
):
    """
    転職理由診断ワークフローのstep1〜4の回答から転職軸の要約を生成する

    Args:
        request: JSONPositionChangeAnalyzeGenerateSummaryRequestモデル
        workflow_svc: WorkflowServiceインスタンス

    Returns:
        {"summary": "...", "explanation": "...", "keywords": ["...", "..."]}
    """
    try:
        return await workflow_svc.generate_position_change_analyze_summary(
            request.answers
        )
    except Exception:
        logger.exception("予期しないエラー")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={},
        )


@router.websocket("/chat")
@inject
async def chat(
    websocket: WebSocket,
    session_id: Optional[str] = None,
    chat_svc: ChatServiceProtocol = Depends(Provide[Container.chat_svc]),
    rate_limit_svc: RateLimitService = Depends(Provide[Container.rate_limit_svc]),
    agent_runtime_config: Any = Depends(Provide[Container.config]),
):
    """
    会話

    Args:
        websocket: WebSocketオブジェクト
        session_id: セッションID
        chat_svc: ChatServiceインスタンス
        rate_limit_svc: RateLimitServiceインスタンス

    Returns:
        None
    """
    if not is_local():
        origin = websocket.headers.get("origin")
        host = websocket.headers.get("host")
        if not origin or not host:
            await websocket.close(code=1008)
            return
        origin_host = urlparse(origin).netloc
        if origin_host != host:
            await websocket.close(code=1008)
            return

    await websocket.accept()

    try:
        if session_id is None:
            session_id = str(uuid.uuid4())
        set_session_id(session_id)
        logger.debug("Session ID: %s", session_id)

        # 接続成立後、すぐメンテモード判断しないと、会話開始／再開は無駄に走る。
        if maintenance_manager.IS_MAINTENANCE_MODE:
            logger.info("メンテナンス中につきwebsocket切断")
            error_response = ChatStreamResponse().create_error_response(
                MAINTENANCE_MESSAGE,
                is_maintenance=True,
            )
            await websocket.send_text(error_response.model_dump_json())
            await websocket.close()
            return

        await handle_chat_session(
            websocket,
            chat_svc,
            rate_limit_svc,
            agent_runtime_config,
        )
    except WebSocketDisconnect as e:
        logger.debug("Websocket切断: %s", e, exc_info=True)
    except Exception:
        logger.exception("予期しないエラー")
    finally:
        clear_session_id()


async def handle_chat_session(
    websocket: WebSocket,
    chat_svc: ChatServiceProtocol,
    rate_limit_svc: RateLimitService,
    agent_runtime_config: Any,
):
    """
    会話初期化

    Args:
        websocket: WebSocketオブジェクト
        chat_svc: ChatServiceインスタンス
        rate_limit_svc: RateLimitServiceインスタンス
        agent_runtime_config: チャット用のAgentモデルを解決するために使用する、注入された設定オブジェクト

    Returns:
        None
    """
    client_ip = get_client_ip(websocket)
    agent_model = resolve_default_agent_model(agent_runtime_config)
    session_status, is_new_session = await chat_svc.init_session(agent_model)
    if session_status == ChatSessionStatus.ERROR:
        # 初期化失敗した場合、エラー
        # TODO: フロント側のエラー処理
        await send_error_response(websocket)
    else:
        if is_new_session:
            # 新規 or 履歴がDefaultAgentのみの再接続: LLM呼び出しなし、initial_menuを即時送信
            initial_menu_response = chat_svc.get_initial_menu_response()
            await websocket.send_text(initial_menu_response.model_dump_json())
            log_chat_turn_runtime(
                logger,
                agent_runtime_config,
                chat_svc,
                request_type=ChatRequestType.START,
            )
        else:
            # 既存再開: RESTART_CHATでフロントに履歴取得させる
            chat_response = ChatStreamResponse(
                request_type=ChatRequestType.RESTART_CHAT,
            ).create_end_response(
                session_status=session_status,
            )
            await websocket.send_text(chat_response.model_dump_json())

        # Start processing regular messages
        await process_chat_messages(
            websocket,
            client_ip,
            chat_svc,
            rate_limit_svc,
            agent_runtime_config,
        )


async def send_error_response(
    websocket: WebSocket,
):
    """
    エラーレスポンス

    Args:
        websocket: WebSocketオブジェクト

    Returns:
        None
    """
    error_response = ChatStreamResponse().create_error_response("セッション初期化失敗")
    await websocket.send_text(error_response.model_dump_json())


async def process_chat_messages(
    websocket: WebSocket,
    client_ip: str,
    chat_svc: ChatServiceProtocol,
    rate_limit_svc: RateLimitService,
    agent_runtime_config: Any,
):
    """
    会話ループ

    Args:
        websocket: WebSocketオブジェクト
        chat_svc: ChatServiceインスタンス
        rate_limit_svc: RateLimitServiceインスタンス

    Returns:
        None
    """
    with trace(
        "AICA workflow",
        trace_id=f"trace_{get_session_id()}",
        metadata={
            "AICA_ENV": get_env(),
        },
    ):
        while True:
            # RESTful APIの場合、HTTPリクエストヘッダーのX-REQUEST-IDより設定します。
            # WebSocketの場合も設定が必要。
            # なければ、他サーバへのHTTPリクエスト時にHttpヘッダー設定できないため、
            # 「Cannot serialize non-str key None」が発生するかもしれない。
            set_request_id(str(uuid.uuid4()))

            message = await websocket.receive_text()

            # サーバーが正常な受信→送信の後、すぐメンテモード送信すると、
            # LLMが無駄に動くし、ユーザーが返信をもらってからすぐメンテモードモーダルが出るのはちょっと不自然な感じなので、
            # メンテモード判断は受信後にしています。
            if maintenance_manager.IS_MAINTENANCE_MODE:
                logger.info("メンテナンス中につきwebsocket切断")
                error_response = ChatStreamResponse().create_error_response(
                    MAINTENANCE_MESSAGE,
                    is_maintenance=True,
                )
                await websocket.send_text(error_response.model_dump_json())
                await websocket.close()
                return

            try:
                raw_input = json.loads(message)
                chat_request = ChatRequestModel.model_validate(raw_input)
            except json.JSONDecodeError:
                logger.exception("Invalid JSON: %s", message)
                invalid_response = ChatStreamResponse().create_error_response(
                    "入力内容が正しくありません。",
                )
                await websocket.send_text(invalid_response.model_dump_json())
            except ValidationError:
                logger.exception("不正なリクエスト: %s", message)
                invalid_response = ChatStreamResponse().create_error_response(
                    "入力内容が正しくありません。",
                )
                await websocket.send_text(invalid_response.model_dump_json())
            else:
                log_chat_turn_runtime(
                    logger,
                    agent_runtime_config,
                    chat_svc,
                    request_type=chat_request.request_type,
                )

                # レート制限チェック
                is_allowed = await asyncio.to_thread(
                    rate_limit_svc.is_within_chat_request_limit,
                    get_session_id(),
                    client_ip,
                )

                if not is_allowed:
                    invalid_response = ChatStreamResponse(
                        request_type=chat_request.request_type,
                        position_id=chat_request.position_id,
                    ).create_error_response(RATE_LIMIT_EXCEEDED_MESSAGE)
                    await websocket.send_text(invalid_response.model_dump_json())
                    continue

                if chat_request.request_type == ChatRequestType.SUMMARIZE_POSITION:
                    # ポジション詳細チャットまとめ
                    session_status = await chat_svc.summarize_position_detail_chat(
                        chat_request
                    )
                    chat_response = ChatStreamResponse(
                        request_type=chat_request.request_type,
                        position_id=chat_request.position_id,
                    ).create_end_response(
                        session_status,
                    )
                    await websocket.send_text(chat_response.model_dump_json())
                elif chat_request.request_type == ChatRequestType.JOB_TYPES_SELECTED:
                    async for chunk in chat_svc.job_type_decided(
                        chat_request, client_ip
                    ):
                        await websocket.send_text(chunk.model_dump_json())
                elif chat_request.request_type == ChatRequestType.JOB_TYPES_CLEAR:
                    async for chunk in chat_svc.clear_jobtype(chat_request, client_ip):
                        await websocket.send_text(chunk.model_dump_json())
                elif (
                    chat_request.request_type
                    == ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED
                ):
                    async for chunk in chat_svc.workflow_submitted(
                        chat_request, client_ip
                    ):
                        await websocket.send_text(chunk.model_dump_json())
                elif chat_request.request_type == ChatRequestType.WORKFLOW_CANCELLED:
                    async for chunk in chat_svc.workflow_cancelled(
                        chat_request, client_ip
                    ):
                        await websocket.send_text(chunk.model_dump_json())
                else:
                    if chat_request.message:
                        async for chunk in chat_svc.chat(chat_request, client_ip):
                            await websocket.send_text(chunk.model_dump_json())
