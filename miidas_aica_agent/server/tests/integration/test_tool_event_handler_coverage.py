"""
Integration tests for ToolEventHandler — targeting 100% branch coverage.

Tests call the real ToolEventHandler directly with controlled items.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from domain.entities.chat_session import ChatSessionStatus
from repositories.action_log_repo import ActionLogRepository
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.user_repo import UserRepository
from services.chat.tool_event_handler import (
    PositionSearchRateLimitExceeded,
    RetryableToolOutputFailure,
    ToolEventHandler,
    _get_raw_item_field,
    _parse_tool_output,
)
from services.rate_limit_service import RateLimitService
from services.workflow_service import WorkflowService
from utils.enum import PageName, ToolName

pytestmark = pytest.mark.pre_extraction_parity


def _make_handler(
    *,
    current_page: PageName = PageName.CHAT,
    encrypted_position_id: str | None = None,
) -> ToolEventHandler:
    position_repo = Mock(spec=PositionRepository)
    chat_repo = Mock(spec=ChatRepository)
    user_repo = Mock(spec=UserRepository)
    action_log_repo = Mock(spec=ActionLogRepository)
    rate_limit_svc = Mock(spec=RateLimitService)
    rate_limit_svc.is_within_position_search_limit.return_value = True
    workflow_svc = Mock(spec=WorkflowService)

    return ToolEventHandler(
        position_repository=position_repo,
        rate_limit_service=rate_limit_svc,
        workflow_service=workflow_svc,
        chat_repository=chat_repo,
        user_repository=user_repo,
        action_log_repository=action_log_repo,
        current_page=current_page,
        encrypted_position_id=encrypted_position_id,
    )


# ─── _get_raw_item_field (line 74: non-dict path) ────────────────────────────


def test_get_raw_item_field_dict_path():
    result = _get_raw_item_field({"call_id": "abc"}, "call_id")
    assert result == "abc"


def test_get_raw_item_field_attribute_path():
    """Line 74: non-dict → getattr."""
    item = SimpleNamespace(call_id="xyz")
    result = _get_raw_item_field(item, "call_id")
    assert result == "xyz"


def test_get_raw_item_field_missing_returns_none():
    item = SimpleNamespace()
    result = _get_raw_item_field(item, "nonexistent")
    assert result is None


# ─── _parse_tool_output (lines 86-88) ────────────────────────────────────────


def test_parse_tool_output_invalid_json_string():
    """Lines 86-88: JSON parse fails → returns {}."""
    result = _parse_tool_output("{invalid")
    assert result == {}


def test_parse_tool_output_dict():
    result = _parse_tool_output({"key": "value"})
    assert result == {"key": "value"}


def test_parse_tool_output_dict_with_text_key():
    result = _parse_tool_output({"text": '{"nested": "value"}'})
    assert result == {"nested": "value"}


# ─── handle_tool_call ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_tool_call_unknown_tool_is_ignored():
    handler = _make_handler()
    from agents import ToolCallItem

    class FakeToolCallItem(ToolCallItem):
        def __init__(self):
            pass

    item = FakeToolCallItem()
    item.raw_item = SimpleNamespace(name="unknown_tool", call_id="tc-1")

    from utils.log_utils import set_session_id, clear_session_id

    set_session_id("sess-1")
    try:
        await handler.handle_tool_call(item, "127.0.0.1")
    finally:
        clear_session_id()

    assert "tc-1" not in handler._tool_calls


@pytest.mark.asyncio
async def test_handle_tool_call_position_search_rate_limit_exceeded():
    handler = _make_handler()
    handler._rate_limit_service.is_within_position_search_limit.return_value = False

    from agents import ToolCallItem

    class FakeToolCallItem(ToolCallItem):
        def __init__(self):
            pass

    item = FakeToolCallItem()
    item.raw_item = SimpleNamespace(
        name=ToolName.GENERIC_POSITION_SEARCH.value, call_id="tc-rate"
    )

    from utils.log_utils import set_session_id, clear_session_id

    set_session_id("sess-rate")
    try:
        with pytest.raises(PositionSearchRateLimitExceeded):
            await handler.handle_tool_call(item, "127.0.0.1")
    finally:
        clear_session_id()


# ─── handle_tool_output residuals ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_tool_output_no_call_id_returns():
    """Line 266: call_id is None → return early."""
    handler = _make_handler()
    from agents import ToolCallOutputItem

    class FakeOutputItem(ToolCallOutputItem):
        def __init__(self):
            pass

    item = FakeOutputItem()
    item.raw_item = {}  # dict with no call_id → None
    item.output = "{}"

    chat_response = MagicMock()
    from utils.log_utils import set_session_id, clear_session_id

    set_session_id("sess-no-call")
    try:
        chunks = []
        async for chunk in handler.handle_tool_output(item, chat_response, MagicMock()):
            chunks.append(chunk)
    finally:
        clear_session_id()

    assert chunks == []


@pytest.mark.asyncio
async def test_handle_tool_output_message_raises_retryable():
    """Line 152: parsed_output contains 'Message' → RetryableToolOutputFailure."""
    handler = _make_handler()
    from agents import ToolCallItem, ToolCallOutputItem

    class FakeToolCallItem(ToolCallItem):
        def __init__(self):
            pass

    class FakeOutputItem(ToolCallOutputItem):
        def __init__(self):
            pass

    # First register the tool call
    tool_item = FakeToolCallItem()
    tool_item.raw_item = SimpleNamespace(
        name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS.value, call_id="tc-msg"
    )

    from utils.log_utils import set_session_id, clear_session_id

    set_session_id("sess-msg")
    try:
        await handler.handle_tool_call(tool_item, "127.0.0.1")

        # Now send output with "Message" key → raises RetryableToolOutputFailure
        output_item = FakeOutputItem()
        output_item.raw_item = SimpleNamespace(call_id="tc-msg")
        output_item.output = '{"Message": "tool failed"}'

        with pytest.raises(RetryableToolOutputFailure):
            async for _ in handler.handle_tool_output(
                output_item, MagicMock(), MagicMock()
            ):
                pass
    finally:
        clear_session_id()


@pytest.mark.asyncio
async def test_handle_tool_output_workflow_error():
    """Lines 342-348: workflow definition raises ValueError → yield error response."""
    handler = _make_handler()
    handler._workflow_service.get_definition.side_effect = ValueError("missing")

    from agents import ToolCallItem, ToolCallOutputItem

    class FakeToolCallItem(ToolCallItem):
        def __init__(self):
            pass

    class FakeOutputItem(ToolCallOutputItem):
        def __init__(self):
            pass

    tool_item = FakeToolCallItem()
    tool_item.raw_item = SimpleNamespace(
        name=ToolName.START_WORKFLOW.value, call_id="tc-wf"
    )

    from utils.log_utils import set_session_id, clear_session_id

    set_session_id("sess-wf")
    try:
        await handler.handle_tool_call(tool_item, "127.0.0.1")

        output_item = FakeOutputItem()
        output_item.raw_item = SimpleNamespace(call_id="tc-wf")
        output_item.output = '{"WorkflowID": "bad_workflow"}'

        chat_response = MagicMock()
        error_response = SimpleNamespace(response_type="ERROR")
        chat_response.create_error_response.return_value = error_response

        chunks = []
        async for chunk in handler.handle_tool_output(
            output_item, chat_response, MagicMock()
        ):
            chunks.append(chunk)
    finally:
        clear_session_id()

    assert error_response in chunks


# ─── build_stop_at_tool_outputs residuals ────────────────────────────────────


def test_build_stop_at_tool_outputs_call_id_not_str():
    """Line 378: call_id is not a str → continue."""
    handler = _make_handler()

    items = [{"type": "function_call_output", "call_id": 42, "output": "data"}]
    result = handler.build_stop_at_tool_outputs(items, stop_at_tool_exists=True)
    assert result == []  # skipped because call_id is not str


def test_build_stop_at_tool_outputs_unknown_tool_falls_through():
    """Lines 395→411: tool_entry is not None, tool is not position search, not jobtype → appended."""
    handler = _make_handler()
    # Register a tool call for a non-position, non-jobtype tool
    handler._tool_calls["tc-other"] = (ToolName.USER_PREFERENCE, SimpleNamespace())

    items = [
        {"type": "function_call_output", "call_id": "tc-other", "output": "result"}
    ]
    result = handler.build_stop_at_tool_outputs(items, stop_at_tool_exists=True)
    # Falls through to outputs.append(item) — the item is included as-is
    assert len(result) == 1
    assert result[0]["call_id"] == "tc-other"


def test_build_stop_at_tool_outputs_position_search_uses_fake_result():
    """Line 383-394: position search tool → fake result used."""
    handler = _make_handler()
    handler._tool_calls["tc-pos"] = (
        ToolName.GENERIC_POSITION_SEARCH,
        SimpleNamespace(),
    )
    handler._position_search_counts["tc-pos"] = 5

    items = [{"type": "function_call_output", "call_id": "tc-pos", "output": "raw"}]
    result = handler.build_stop_at_tool_outputs(items, stop_at_tool_exists=True)
    assert len(result) == 1
    assert "5件" in result[0]["output"]


def test_build_stop_at_tool_outputs_not_function_call_output_type():
    """Line 374-375: item type is not function_call_output → continue."""
    handler = _make_handler()

    items = [{"type": "other_type", "call_id": "tc-1", "output": "data"}]
    result = handler.build_stop_at_tool_outputs(items, stop_at_tool_exists=True)
    assert result == []


# ─── _process_jobtype_search_result line 152 ─────────────────────────────────


def test_process_jobtype_search_result_no_jobtypes_key():
    """Line 152: _process_jobtype_search_result raw_jobtypes is falsy → return None."""
    from services.chat.tool_event_handler import _process_jobtype_search_result

    # jobtypes has no '職種' key → raw_jobtypes is None → returns None
    jobtypes = {"other_key": []}
    result = _process_jobtype_search_result(
        "tc-1", ToolName.JOBTYPE_SEARCH_BY_KEYWORDS, "{}", jobtypes
    )
    assert result is None
