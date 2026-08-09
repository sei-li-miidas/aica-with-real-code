"""Unit tests for ConversationState — 100% branch coverage required.

ConversationState is a pure data container with no external I/O or business
logic. The tests enumerate every field, verify default values, and exercise
mutation behavior.
"""

from __future__ import annotations

import pytest

from services.chat.conversation_state import ConversationState
from utils.const import MAIN_CHAT_KEY

pytestmark = pytest.mark.pre_extraction_parity


# ---------------------------------------------------------------------------
# Construction / default values
# ---------------------------------------------------------------------------


def test_default_model_name_is_empty_string():
    state = ConversationState()
    assert state.model_name == ""


def test_default_active_agent_name_is_empty_string():
    state = ConversationState()
    assert state.active_agent_name == ""


def test_default_chat_key_is_main_chat_key():
    state = ConversationState()
    assert state.chat_key == MAIN_CHAT_KEY


def test_default_position_id_is_none():
    state = ConversationState()
    assert state.position_id is None


def test_default_previous_continuation_states_is_empty_dict():
    state = ConversationState()
    assert state.previous_continuation_states == {}


def test_default_conversation_has_main_key_with_empty_list():
    state = ConversationState()
    assert state.conversation == {MAIN_CHAT_KEY: []}


def test_default_chat_histories_has_main_key_with_empty_list():
    state = ConversationState()
    assert state.chat_histories == {MAIN_CHAT_KEY: []}


# ---------------------------------------------------------------------------
# Two independent instances do not share mutable state
# ---------------------------------------------------------------------------


def test_two_instances_have_independent_previous_continuation_states():
    a = ConversationState()
    b = ConversationState()
    a.previous_continuation_states["key"] = "value"
    assert "key" not in b.previous_continuation_states


def test_two_instances_have_independent_conversation():
    a = ConversationState()
    b = ConversationState()
    a.conversation[MAIN_CHAT_KEY].append("msg")
    assert b.conversation[MAIN_CHAT_KEY] == []


def test_two_instances_have_independent_chat_histories():
    a = ConversationState()
    b = ConversationState()
    a.chat_histories[MAIN_CHAT_KEY].append("history-item")
    assert b.chat_histories[MAIN_CHAT_KEY] == []


# ---------------------------------------------------------------------------
# Mutation of all fields
# ---------------------------------------------------------------------------


def test_model_name_can_be_set():
    state = ConversationState()
    state.model_name = "gpt-4o"
    assert state.model_name == "gpt-4o"


def test_active_agent_name_can_be_set():
    state = ConversationState()
    state.active_agent_name = "CareerAdvisor"
    assert state.active_agent_name == "CareerAdvisor"


def test_chat_key_can_be_set():
    state = ConversationState()
    state.chat_key = "position-42"
    assert state.chat_key == "position-42"


def test_position_id_can_be_set():
    state = ConversationState()
    state.position_id = "pos-123"
    assert state.position_id == "pos-123"


def test_previous_continuation_states_can_be_mutated():
    state = ConversationState()
    state.previous_continuation_states["MAIN"] = "resp-abc"
    assert state.previous_continuation_states["MAIN"] == "resp-abc"


def test_conversation_can_be_mutated():
    state = ConversationState()
    state.conversation["MAIN"] = [{"type": "message", "role": "user", "content": "hi"}]
    assert len(state.conversation["MAIN"]) == 1


def test_chat_histories_can_be_mutated():
    state = ConversationState()
    state.chat_histories[MAIN_CHAT_KEY].append("item-1")
    assert state.chat_histories[MAIN_CHAT_KEY] == ["item-1"]
