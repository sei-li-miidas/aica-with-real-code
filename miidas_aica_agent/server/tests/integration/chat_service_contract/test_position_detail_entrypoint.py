"""
Position detail entrypoint テスト。

テストケース一覧:
- test_position_detail_bootstrap_fetches_and_persists_developer_prompt
    対象: position detail 入口で developer prompt を取得し、
    履歴永続化まで実施されること。
- test_position_detail_bootstrap_returns_error_when_required_detail_is_missing
    対象: 必須 detail 欠損時にエラーレスポンスで早期終了すること。
- test_chat_from_position_detail_returns_to_last_non_position_guide_agent
    対象: position_detail 後の遷移で
    最後の非 PositionGuideAgent へ復帰すること。
- test_chat_returns_error_for_unknown_page
    対象: 未知ページ入力をバリデーションし、
    失敗応答を返すこと。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from .chat_service_contract_helpers import _FakeRunResult, _inner, _state
from domain.entities.chat_history import ChatHistory
from services.llm_service import AgentName
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType
from utils.enum import LLMMessageRole, PageName
from utils.log_utils import clear_session_id, set_session_id


_VARIANTS = [
    "legacy",
    "real-refactored",
]
_SESSION_ID = "test-session-position-detail-entrypoint"


def _make_request(
    *,
    current_page: PageName,
    position_id: str | None = None,
    message: str = "詳細を教えてください",
) -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=current_page,
        position_id=position_id,
        message=message,
        current_message_id="msg-position-detail-entrypoint",
    )


async def _collect(chat_svc, request):
    responses = []
    async for response in chat_svc.chat(request, "127.0.0.1"):
        responses.append(response.model_copy(deep=True))
    return responses


def _saved_histories_from_call(call):
    if "chat_histories" in call.kwargs:
        return call.kwargs["chat_histories"]
    if call.args:
        return call.args[0]
    raise AssertionError(
        "add_chat_histories() call did not include chat_histories in args or kwargs"
    )


@pytest.fixture
def position_detail_session_id():
    set_session_id(_SESSION_ID)
    yield
    clear_session_id()


pytestmark = pytest.mark.pre_extraction_parity


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_position_detail_bootstrap_fetches_and_persists_developer_prompt(
    variant, chat_service_container, position_detail_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    position_guide = MagicMock()
    position_guide.name = AgentName.POSITION_GUIDE
    position_guide.tool_use_behavior = {}
    position_agent = MagicMock()
    position_agent.name = AgentName.POSITION_GUIDE
    position_agent.tool_use_behavior = {}
    position_guide.clone.return_value = position_agent
    svc._llm_svc.clone_agents.return_value = {
        "CareerAdvisor": (default_agent, True),
        AgentName.POSITION_GUIDE: (position_guide, False),
    }
    await chat_svc.init_session("gpt-4o")
    svc._position_service.get_position_detail = AsyncMock(return_value={"id": "p1"})
    svc._position_service.get_company_detail = AsyncMock(return_value={"name": "c1"})
    svc._position_service.get_business_detail = AsyncMock(return_value={"name": "b1"})
    svc._run_streamed = MagicMock(return_value=_FakeRunResult([]))

    with (
        patch("services.chat_service.decrypt", return_value="position-001"),
        patch("services.chat_service_refactored.decrypt", return_value="position-001"),
    ):
        responses = await _collect(
            chat_svc,
            _make_request(
                current_page=PageName.POSITION_DETAIL,
                position_id="encrypted-position-id",
            ),
        )

    assert responses[-1].response_type == ChatResponseType.END
    saved_histories = _saved_histories_from_call(
        svc._chat_repository.add_chat_histories.call_args_list[0]
    )
    assert len(saved_histories) == 1
    assert saved_histories[0].position_id == "position-001"
    assert saved_histories[0].role == LLMMessageRole.DEVELOPER
    assert "求人情報" in saved_histories[0].content


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "missing_attr",
    ["get_position_detail", "get_company_detail", "get_business_detail"],
)
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_position_detail_bootstrap_returns_error_when_required_detail_is_missing(
    variant, chat_service_container, missing_attr, position_detail_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    position_guide = MagicMock()
    position_guide.name = AgentName.POSITION_GUIDE
    position_guide.tool_use_behavior = {}
    position_guide.clone.return_value = MagicMock(name="PositionGuideClone")
    svc._llm_svc.clone_agents.return_value = {
        "CareerAdvisor": (default_agent, True),
        AgentName.POSITION_GUIDE: (position_guide, False),
    }
    await chat_svc.init_session("gpt-4o")
    svc._position_service.get_position_detail = AsyncMock(return_value={"id": "p1"})
    svc._position_service.get_company_detail = AsyncMock(return_value={"name": "c1"})
    svc._position_service.get_business_detail = AsyncMock(return_value={"name": "b1"})
    setattr(svc._position_service, missing_attr, AsyncMock(return_value=None))

    with (
        patch("services.chat_service.decrypt", return_value="position-001"),
        patch("services.chat_service_refactored.decrypt", return_value="position-001"),
    ):
        responses = await _collect(
            chat_svc,
            _make_request(
                current_page=PageName.POSITION_DETAIL,
                position_id="encrypted-position-id",
            ),
        )

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_chat_from_position_detail_returns_to_last_non_position_guide_agent(
    variant, chat_service_container, position_detail_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    await chat_svc.init_session("gpt-4o")
    _state(svc).active_agent_name = AgentName.POSITION_GUIDE
    _state(svc).chat_histories["MAIN"] = [
        ChatHistory(
            session_id=_SESSION_ID,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="msg-main-history",
            role=LLMMessageRole.USER,
            content="main history",
        )
    ]
    career_agent = MagicMock()
    career_agent.name = "CareerAdvisor"
    career_agent.tool_use_behavior = {}
    svc._agents["CareerAdvisor"] = career_agent
    svc._run_streamed = MagicMock(return_value=_FakeRunResult([]))

    responses = await _collect(
        chat_svc,
        _make_request(current_page=PageName.CHAT),
    )

    assert responses[-1].response_type == ChatResponseType.END
    assert _state(svc).active_agent_name == "CareerAdvisor"


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_chat_returns_error_for_unknown_page(
    variant, chat_service_container, position_detail_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    await chat_svc.init_session("gpt-4o")

    responses = await _collect(
        chat_svc,
        ChatRequestModel(
            request_type=ChatRequestType.CHAT,
            current_page=PageName.PROFILE_BASIC_INFO,
            message="invalid page",
            current_message_id="msg-unknown-page",
        ),
    )

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR
