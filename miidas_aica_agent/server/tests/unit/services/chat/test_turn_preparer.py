"""Unit tests for TurnPreparer — 100% branch coverage required.

Branch inventory
----------------
get_message_role:
  B1  request_type in _DEVELOPER_REQUEST_TYPES → DEVELOPER
  B2  request_type not in _DEVELOPER_REQUEST_TYPES → USER

prepare_turn:
  P-CHAT-A   current_page == CHAT, active_agent != POSITION_GUIDE → no switch
  P-CHAT-B   current_page == CHAT, active_agent == POSITION_GUIDE → switch via _find_last
  P-POS-A    current_page == POSITION_DETAIL, encrypted_position_id truthy,
             conversation already populated → skip fetch
  P-POS-B    current_page == POSITION_DETAIL, conversation empty, fetch ok → init conv
  P-POS-ERR  current_page == POSITION_DETAIL, conversation empty, fetch fails → ValueError
  P-ELSE     unknown page / POSITION_DETAIL without position_id → ValueError

_get_position_detail:
  G1  position_detail falsy → error tuple
  G2  position_detail ok, company_detail falsy → error tuple
  G3  company_detail ok, business_detail falsy → error tuple
  G4  all ok → success tuple

_find_last_non_position_guide_agent:
  F1  found non-POSITION_GUIDE in reversed histories → return it
  F2  empty histories → ValueError
  F3  all histories are POSITION_GUIDE → ValueError

_create_position_agent_if_not_exist:
  C1  position_id_str already in agents → no-op
  C2  position_id_str missing, base_agent None → no-op
  C3  position_id_str missing, base_agent present → clone and register
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


pytestmark = pytest.mark.pre_extraction_parity
from services.chat.conversation_state import ConversationState
from services.chat.turn_preparer import TurnPreparer
from services.llm_service import AgentName
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.const import MAIN_CHAT_KEY
from utils.enum import LLMMessageRole, PageName


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_preparer(
    *,
    active_agent: str = "",
    chat_key: str = MAIN_CHAT_KEY,
    position_id: str | None = None,
    conversation: dict | None = None,
    chat_histories: dict | None = None,
    agents: dict | None = None,
    position_svc: MagicMock | None = None,
    persistence: MagicMock | None = None,
) -> tuple[TurnPreparer, ConversationState]:
    conv_state = ConversationState()
    conv_state.active_agent_name = active_agent
    conv_state.chat_key = chat_key
    conv_state.position_id = position_id
    if conversation is not None:
        conv_state.conversation = conversation
    if chat_histories is not None:
        conv_state.chat_histories = chat_histories

    position_svc = position_svc or MagicMock()
    persistence = persistence or MagicMock()
    agents = agents if agents is not None else {}

    preparer = TurnPreparer(
        position_service=position_svc,
        chat_persistence=persistence,
        conv_state=conv_state,
        agents=agents,
    )
    return preparer, conv_state


def _chat_request(
    page: PageName = PageName.CHAT,
    request_type: ChatRequestType = ChatRequestType.CHAT,
    position_id: str | None = None,
) -> ChatRequestModel:
    return ChatRequestModel(
        current_page=page,
        request_type=request_type,
        position_id=position_id,
    )


def _history(active_agent: str) -> SimpleNamespace:
    return SimpleNamespace(active_agent=active_agent)


# ---------------------------------------------------------------------------
# get_message_role — B1 / B2
# ---------------------------------------------------------------------------

DEVELOPER_TYPES = [
    ChatRequestType.START,
    ChatRequestType.RESTART_CHAT,
    ChatRequestType.JOB_TYPES_SELECTED,
    ChatRequestType.JOB_TYPES_CLEAR,
    ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
    ChatRequestType.WORKFLOW_CANCELLED,
]


@pytest.mark.parametrize("request_type", DEVELOPER_TYPES)
def test_get_message_role_returns_developer_for_developer_types(request_type):
    preparer, _ = _make_preparer()
    assert preparer.get_message_role(request_type) == LLMMessageRole.DEVELOPER


def test_get_message_role_returns_user_for_chat_type():
    preparer, _ = _make_preparer()
    assert preparer.get_message_role(ChatRequestType.CHAT) == LLMMessageRole.USER


# ---------------------------------------------------------------------------
# prepare_turn — CHAT page
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prepare_turn_chat_page_non_position_guide_agent_unchanged():
    """P-CHAT-A: active_agent != POSITION_GUIDE → agent name left as-is."""
    preparer, state = _make_preparer(active_agent="CareerAdvisor")
    await preparer.prepare_turn(_chat_request(PageName.CHAT))
    assert state.active_agent_name == "CareerAdvisor"


@pytest.mark.asyncio
async def test_prepare_turn_chat_page_position_guide_switches_to_last_non_guide():
    """P-CHAT-B: active_agent == POSITION_GUIDE → switched via _find_last."""
    histories = [
        _history(AgentName.POSITION_GUIDE),
        _history("CareerAdvisor"),
        _history(AgentName.POSITION_GUIDE),
    ]
    preparer, state = _make_preparer(
        active_agent=AgentName.POSITION_GUIDE,
        chat_histories={MAIN_CHAT_KEY: histories},
    )
    await preparer.prepare_turn(_chat_request(PageName.CHAT))
    assert state.active_agent_name == "CareerAdvisor"


# ---------------------------------------------------------------------------
# prepare_turn — POSITION_DETAIL page, conversation already populated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prepare_turn_position_detail_skips_fetch_when_conversation_exists():
    """P-POS-A: conversation already populated → no position service call."""
    position_svc = MagicMock()
    position_svc.get_position_detail = AsyncMock()
    chat_key = "pos-key"
    conversation = {chat_key: [{"existing": True}]}
    preparer, state = _make_preparer(
        chat_key=chat_key,
        conversation=conversation,
        position_svc=position_svc,
    )

    await preparer.prepare_turn(
        _chat_request(PageName.POSITION_DETAIL, position_id="enc-pos-1")
    )

    position_svc.get_position_detail.assert_not_called()
    assert state.active_agent_name == AgentName.POSITION_GUIDE


# ---------------------------------------------------------------------------
# prepare_turn — POSITION_DETAIL page, first access (conversation empty)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prepare_turn_position_detail_initialises_conversation_on_first_access():
    """P-POS-B: empty conversation → fetch details, build conv, save histories."""
    chat_key = "pos-key-2"
    position_svc = MagicMock()
    position_svc.get_position_detail = AsyncMock(return_value={"pos": "data"})
    position_svc.get_company_detail = AsyncMock(return_value={"company": "data"})
    position_svc.get_business_detail = AsyncMock(return_value={"biz": "data"})

    persistence = MagicMock()
    persistence.save_chat_histories = MagicMock()

    trace_msg = {"type": "tool_trace"}
    agents = {AgentName.POSITION_GUIDE: MagicMock()}

    preparer, state = _make_preparer(
        chat_key=chat_key,
        conversation={},
        position_id="pos-uuid",
        position_svc=position_svc,
        persistence=persistence,
        agents=agents,
    )
    preparer.set_toolcall_trace_message(trace_msg)

    await preparer.prepare_turn(
        _chat_request(PageName.POSITION_DETAIL, position_id="enc-pos-2")
    )

    # Active agent set to POSITION_GUIDE
    assert state.active_agent_name == AgentName.POSITION_GUIDE

    # Conversation initialised with trace message + developer message
    conv = state.conversation[chat_key]
    assert len(conv) == 2
    assert conv[0] is trace_msg
    assert conv[1]["role"] == LLMMessageRole.DEVELOPER

    # Chat history saved
    persistence.save_chat_histories.assert_called_once()
    saved_histories = persistence.save_chat_histories.call_args[0][0]
    assert len(saved_histories) == 1
    assert saved_histories[0].role == LLMMessageRole.DEVELOPER
    assert saved_histories[0].active_agent == AgentName.POSITION_GUIDE


@pytest.mark.asyncio
async def test_prepare_turn_position_detail_raises_on_fetch_error():
    """P-POS-ERR: _get_position_detail returns error → ValueError raised."""
    chat_key = "pos-key-3"
    position_svc = MagicMock()
    position_svc.get_position_detail = AsyncMock(return_value=None)  # triggers error

    agents = {AgentName.POSITION_GUIDE: MagicMock()}
    preparer, _ = _make_preparer(
        chat_key=chat_key,
        conversation={},
        position_id="pos-uuid",
        position_svc=position_svc,
        agents=agents,
    )

    with pytest.raises(ValueError, match="ポジション詳細が見つからなかった"):
        await preparer.prepare_turn(
            _chat_request(PageName.POSITION_DETAIL, position_id="enc-pos-3")
        )


# ---------------------------------------------------------------------------
# prepare_turn — unknown page / POSITION_DETAIL without position_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prepare_turn_unknown_page_raises_value_error():
    """P-ELSE (unknown page string): unknown PageName → ValueError."""
    preparer, _ = _make_preparer()
    request = _chat_request(PageName.CHAT)
    # Override current_page to something that matches neither branch
    object.__setattr__(request, "current_page", "UnknownPage")

    with pytest.raises(ValueError, match="Unknown page"):
        await preparer.prepare_turn(request)


@pytest.mark.asyncio
async def test_prepare_turn_position_detail_without_position_id_raises():
    """P-ELIF (POSITION_DETAIL without id): missing position_id → ValueError."""
    preparer, _ = _make_preparer()
    with pytest.raises(
        ValueError, match=r"POSITION_DETAIL requires encrypted_position_id, got: None"
    ):
        await preparer.prepare_turn(
            _chat_request(PageName.POSITION_DETAIL, position_id=None)
        )


async def _assert_raises_unknown_page(preparer, page, position_id):
    with pytest.raises(ValueError, match="Unknown page"):
        await preparer.prepare_turn(_chat_request(page, position_id=position_id))


# ---------------------------------------------------------------------------
# _get_position_detail — G1 / G2 / G3 / G4
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_position_detail_returns_error_when_position_not_found():
    """G1: get_position_detail returns falsy → error tuple."""
    position_svc = MagicMock()
    position_svc.get_position_detail = AsyncMock(return_value=None)
    preparer, _ = _make_preparer(position_svc=position_svc)

    pos, company, biz, err = await preparer._get_position_detail("enc-id")

    assert pos is None and company is None and biz is None
    assert "ポジション詳細が見つからなかった" in err


@pytest.mark.asyncio
async def test_get_position_detail_returns_error_when_company_not_found():
    """G2: company_detail falsy → error tuple."""
    position_svc = MagicMock()
    position_svc.get_position_detail = AsyncMock(return_value={"pos": "ok"})
    position_svc.get_company_detail = AsyncMock(return_value=None)
    preparer, _ = _make_preparer(position_svc=position_svc)

    pos, company, biz, err = await preparer._get_position_detail("enc-id")

    assert pos is None and company is None and biz is None
    assert "会社詳細が見つからなかった" in err


@pytest.mark.asyncio
async def test_get_position_detail_returns_error_when_business_not_found():
    """G3: business_detail falsy → error tuple."""
    position_svc = MagicMock()
    position_svc.get_position_detail = AsyncMock(return_value={"pos": "ok"})
    position_svc.get_company_detail = AsyncMock(return_value={"company": "ok"})
    position_svc.get_business_detail = AsyncMock(return_value=None)
    preparer, _ = _make_preparer(position_svc=position_svc)

    pos, company, biz, err = await preparer._get_position_detail("enc-id")

    assert pos is None and company is None and biz is None
    assert "業界詳細が見つからなかった" in err


@pytest.mark.asyncio
async def test_get_position_detail_returns_all_details_on_success():
    """G4: all services return data → success tuple with None error."""
    position_svc = MagicMock()
    position_svc.get_position_detail = AsyncMock(return_value={"pos": "ok"})
    position_svc.get_company_detail = AsyncMock(return_value={"company": "ok"})
    position_svc.get_business_detail = AsyncMock(return_value={"biz": "ok"})
    preparer, _ = _make_preparer(position_svc=position_svc)

    pos, company, biz, err = await preparer._get_position_detail("enc-id")

    assert pos == {"pos": "ok"}
    assert company == {"company": "ok"}
    assert biz == {"biz": "ok"}
    assert err is None


# ---------------------------------------------------------------------------
# _find_last_non_position_guide_agent — F1 / F2 / F3
# ---------------------------------------------------------------------------


def test_find_last_non_position_guide_returns_most_recent_non_guide():
    """F1: last non-POSITION_GUIDE in reversed order is returned."""
    histories = [
        _history("CareerAdvisor"),
        _history(AgentName.POSITION_GUIDE),
        _history("WorkflowAgent"),
        _history(AgentName.POSITION_GUIDE),
    ]
    preparer, _ = _make_preparer(chat_histories={MAIN_CHAT_KEY: histories})
    result = preparer._find_last_non_position_guide_agent()
    assert result == "WorkflowAgent"


def test_find_last_non_position_guide_raises_when_histories_empty():
    """F2: empty histories → ValueError."""
    preparer, _ = _make_preparer(chat_histories={MAIN_CHAT_KEY: []})
    with pytest.raises(ValueError, match="POSITION_GUIDE以外"):
        preparer._find_last_non_position_guide_agent()


def test_find_last_non_position_guide_raises_when_all_are_position_guide():
    """F3: every history has POSITION_GUIDE → ValueError."""
    histories = [_history(AgentName.POSITION_GUIDE), _history(AgentName.POSITION_GUIDE)]
    preparer, _ = _make_preparer(chat_histories={MAIN_CHAT_KEY: histories})
    with pytest.raises(ValueError, match="POSITION_GUIDE以外"):
        preparer._find_last_non_position_guide_agent()


# ---------------------------------------------------------------------------
# _create_position_agent_if_not_exist — C1 / C2 / C3
# ---------------------------------------------------------------------------


def test_create_position_agent_no_op_when_already_exists():
    """C1: position_id_str already in agents → agents unchanged."""
    agents = {"pos-42": MagicMock()}
    original_agent = agents["pos-42"]
    preparer, _ = _make_preparer(agents=agents)

    preparer._create_position_agent_if_not_exist("pos-42")

    assert agents["pos-42"] is original_agent


def test_create_position_agent_no_op_when_base_agent_missing():
    """C2: position_id_str absent, base POSITION_GUIDE also absent → nothing added."""
    agents: dict = {}
    preparer, _ = _make_preparer(agents=agents)

    preparer._create_position_agent_if_not_exist("pos-99")

    assert "pos-99" not in agents


def test_create_position_agent_clones_base_when_absent():
    """C3: position_id_str absent, base POSITION_GUIDE present → clone registered."""
    cloned = MagicMock()
    base_agent = MagicMock()
    base_agent.clone.return_value = cloned
    agents = {AgentName.POSITION_GUIDE: base_agent}
    preparer, _ = _make_preparer(agents=agents)

    preparer._create_position_agent_if_not_exist("new-pos")

    assert agents["new-pos"] is cloned
    base_agent.clone.assert_called_once()


def test_create_position_agent_converts_none_position_id_to_string():
    """None position_id is str()-converted before lookup and insert."""
    cloned = MagicMock()
    base_agent = MagicMock()
    base_agent.clone.return_value = cloned
    agents = {AgentName.POSITION_GUIDE: base_agent}
    preparer, _ = _make_preparer(agents=agents)

    preparer._create_position_agent_if_not_exist(None)

    assert "None" in agents


# ---------------------------------------------------------------------------
# set_toolcall_trace_message
# ---------------------------------------------------------------------------


def test_set_toolcall_trace_message_stores_value():
    preparer, _ = _make_preparer()
    msg = {"type": "trace", "id": "abc"}
    preparer.set_toolcall_trace_message(msg)
    assert preparer._toolcall_trace_message is msg
