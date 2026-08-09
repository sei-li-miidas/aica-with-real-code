"""
Chat entrypoint guard テスト。

テストケース一覧:
- test_chat_defaults_missing_session_status_to_chatting
    対象: session_status が None の場合でも chat() の最終レスポンスが
    session_status=CHATTING へ正規化されること。
- test_chat_returns_error_for_blocked_session
    対象: DB 上の session が BLOCKED のとき、chat() が ERROR を返して
    run_streamed を呼ばないこと。
- test_chat_start_short_circuits_for_registering_or_applying_sessions
    対象: request_type=START かつ既存 status が REGISTERING/APPLYING のとき、
    START 要求を短絡し chat 実行へ進まないこと。
- test_chat_returns_error_when_position_decrypt_fails
    対象: POSITION_DETAIL 入力で position_id 復号に失敗したとき、
    chat() が ERROR を返すこと。
- test_chat_returns_end_when_prepare_does_not_populate_conversation
    対象: prepare_for_chat_turn が会話入力を構築できないとき、
    chat() が END を返して runner 呼び出しを回避すること。
- test_chat_returns_error_when_position_guide_agent_cannot_be_restored
    対象: POSITION_GUIDE から前エージェント復元に失敗したとき、
    chat() が ERROR を返すこと。
- test_chat_returns_error_when_active_agent_is_missing
    対象: active_agent_name が agents 辞書に存在しない状態では
    chat() が ERROR を返すこと。
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from contextlib import ExitStack

from .chat_service_contract_helpers import (
    _FakeRunResult,
    _FakeRunStream,
    _inner,
    _state,
)
from domain.entities.chat_session import ChatSessionStatus
from services.llm_service import AgentName
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType
from utils.const import MAIN_CHAT_KEY
from utils.enum import PageName
from utils.log_utils import clear_session_id, set_session_id


_VARIANTS = [
    "legacy",
    "real-refactored",
]
_SESSION_ID = "test-session-chat-entrypoint-guards"


def _make_request(
    *,
    request_type: ChatRequestType = ChatRequestType.CHAT,
    current_page: PageName = PageName.CHAT,
    position_id: str | None = None,
    message: str = "こんにちは",
) -> ChatRequestModel:
    return ChatRequestModel(
        request_type=request_type,
        current_page=current_page,
        position_id=position_id,
        message=message,
        current_message_id="msg-chat-entrypoint-guards",
    )


async def _collect(chat_svc, request):
    responses = []
    async for response in chat_svc.chat(request, "127.0.0.1"):
        responses.append(response.model_copy(deep=True))
    return responses


@pytest.fixture
def chat_entrypoint_guards_session_id():
    set_session_id(_SESSION_ID)
    yield
    clear_session_id()


pytestmark = pytest.mark.pre_extraction_parity


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_chat_defaults_missing_session_status_to_chatting(
    variant, chat_service_container, chat_entrypoint_guards_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    await chat_svc.init_session("gpt-4o")
    svc._chat_repository.session_status.return_value = None
    if variant == "legacy":
        svc._run_streamed = MagicMock(return_value=_FakeRunResult([]))
    else:
        svc._llm_runner.run_streamed.return_value = _FakeRunStream([])

    responses = await _collect(chat_svc, _make_request())

    assert responses[-1].response_type == ChatResponseType.END
    assert responses[-1].session_status == ChatSessionStatus.CHATTING


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_chat_returns_error_for_blocked_session(
    variant, chat_service_container, chat_entrypoint_guards_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    svc._chat_repository.is_session_blocked.return_value = True

    responses = await _collect(chat_svc, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR
    assert "会話がブロックされています" in responses[0].message


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_chat_start_short_circuits_for_registering_or_applying_sessions(
    variant, chat_service_container, chat_entrypoint_guards_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    for status in (
        ChatSessionStatus.REGISTERING,
        ChatSessionStatus.APPLYING,
    ):
        svc._chat_repository.session_status.return_value = status
        responses = await _collect(
            chat_svc,
            _make_request(request_type=ChatRequestType.START),
        )
        assert len(responses) == 1
        assert responses[0].response_type == ChatResponseType.END
        assert responses[0].session_status == status


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_chat_returns_error_when_position_decrypt_fails(
    variant, chat_service_container, chat_entrypoint_guards_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    await chat_svc.init_session("gpt-4o")

    # legacy は services.chat_service.decrypt、refactored は services.chat_service_refactored.decrypt
    # を使用するため、variant に応じて両方をパッチする。
    with ExitStack() as stack:
        stack.enter_context(
            patch("services.chat_service.decrypt", side_effect=ValueError("bad token"))
        )
        if variant != "legacy":
            stack.enter_context(
                patch(
                    "services.chat_service_refactored.decrypt",
                    side_effect=ValueError("bad token"),
                )
            )
        responses = await _collect(
            chat_svc,
            _make_request(
                current_page=PageName.POSITION_DETAIL,
                position_id="encrypted-position",
            ),
        )

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR
    assert responses[0].message


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_chat_returns_end_when_prepare_does_not_populate_conversation(
    variant, chat_service_container, chat_entrypoint_guards_session_id
):
    chat_svc = chat_service_container
    await chat_svc.init_session("gpt-4o")
    # Simulate a state where build_summary_context is skipped (previous_response_ids
    # is set) but _conversation no longer has MAIN_CHAT_KEY — e.g. after an unexpected
    # reset. This exercises the guard that returns END instead of calling the runner.
    if variant == "legacy":
        chat_svc._previous_response_ids[MAIN_CHAT_KEY] = "some-response-id"
    else:
        _state(chat_svc).previous_continuation_states[MAIN_CHAT_KEY] = (
            "some-response-id"
        )
    del _state(chat_svc).conversation[MAIN_CHAT_KEY]

    responses = await _collect(chat_svc, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_chat_returns_error_when_position_guide_agent_cannot_be_restored(
    variant, chat_service_container, chat_entrypoint_guards_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    position_guide = MagicMock()
    position_guide.name = AgentName.POSITION_GUIDE
    position_guide.tool_use_behavior = {}
    position_guide.clone.return_value = position_guide
    svc._llm_svc.clone_agents.return_value = {
        "CareerAdvisor": (default_agent, True),
        AgentName.POSITION_GUIDE: (position_guide, False),
    }
    await chat_svc.init_session("gpt-4o")

    if variant == "legacy":
        svc._get_position_detail = AsyncMock(return_value=({}, {}, {}, ""))
        svc._run_streamed = MagicMock(return_value=_FakeRunResult([]))
        with patch("services.chat_service.decrypt", return_value="position-001"):
            await _collect(
                chat_svc,
                _make_request(
                    current_page=PageName.POSITION_DETAIL,
                    position_id="encrypted-position",
                ),
            )
    else:
        # real-refactored: _get_position_detail lives on _turn_preparer, not on the
        # ChatService instance. Patch it there. The conftest default runner mock
        # (_FakeRunStream([])) is used for the position-detail turn. Both the
        # chat_service and chat_service_refactored decrypt imports must be patched
        # since _resolve_chat_key and TurnPreparer._create_position_agent_if_not_exist
        # both derive position_id from the same call in chat_service_refactored.
        chat_svc._turn_preparer._get_position_detail = AsyncMock(
            return_value=({}, {}, {}, "")
        )
        with (
            patch("services.chat_service.decrypt", return_value="position-001"),
            patch(
                "services.chat_service_refactored.decrypt",
                return_value="position-001",
            ),
        ):
            await _collect(
                chat_svc,
                _make_request(
                    current_page=PageName.POSITION_DETAIL,
                    position_id="encrypted-position",
                ),
            )

    responses = await _collect(chat_svc, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_chat_returns_error_when_active_agent_is_missing(
    variant, chat_service_container, chat_entrypoint_guards_session_id
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    svc._llm_svc.clone_agents.return_value = {}
    await chat_svc.init_session("gpt-4o")

    responses = await _collect(chat_svc, _make_request())

    assert responses[-1].response_type == ChatResponseType.ERROR
