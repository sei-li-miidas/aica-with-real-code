"""Unit tests for ToolEventHandler — 100% branch coverage required.

Branch inventory
----------------
_parse_tool_output():
  PARSE-STR-OK      str input → JSON decode succeeds → dict returned
  PARSE-STR-FAIL    str input → JSON decode fails → {} returned
  PARSE-DICT        dict input (non-str) → direct dict path
  PARSE-LIST-EMPTY  list input, empty → {} returned
  PARSE-LIST-NODICT list input, first element is not dict → {} returned
  PARSE-LIST-DICT   list input, first element is dict → inner_result extracted
  PARSE-ELSE        outer_result is not str/dict/list → {} returned
  PARSE-INNER-DICT  inner_result is dict → returned directly
  PARSE-INNER-NOTSTR inner_result is not str and not dict → {} returned
  PARSE-INNER-STR-OK inner_result is str → JSON decode succeeds
  PARSE-INNER-STR-FAIL inner_result is str → JSON decode fails → {} returned

_generate_position_search_fake_result():
  FAKE-RESULT       count passed → formatted str returned

_process_jobtype_search_result():
  JOBT-EMPTY        jobtypes is falsy → None returned
  JOBT-NO-KEY       jobtypes dict has no '職種' key → None returned
  JOBT-OK           valid jobtypes → normalized list returned

ToolEventHandler.handle_tool_call():
  TC-UNKNOWN        item.raw_item.name not in ToolName → returns without recording
  TC-POS-SEARCH     position search tool → rate limit checked; keyed by call_id
  TC-NON-POS        non-position-search tool → recorded without rate limit check
  TC-PARALLEL       two calls of same tool type in one turn → both stored (call_id key)

ToolEventHandler._ensure_tool_execution_available():
  RATE-ALLOWED      rate limit allows → no exception
  RATE-DENIED       rate limit denies → PositionSearchRateLimitExceeded raised

ToolEventHandler.handle_tool_output():
  OUT-CALL-ID-NONE  raw_item has no call_id field → nothing yielded
  OUT-NO-CALL-ID    call_id not found in _tool_calls → nothing yielded
  OUT-MESSAGE-KEY   "Message" in parsed output → nothing yielded
  OUT-POS-SEARCH    GENERIC/IT/FINANCIAL position search → POSITION_SEARCH_RESULT yielded
  OUT-JOBTYPE-NONE  jobtype tool, _process_jobtype_search_result returns None → nothing yielded
  OUT-JOBTYPE-OK    jobtype tool, _process_jobtype_search_result returns dict → JOBTYPE_SEARCH_RESULT yielded
  OUT-WORKFLOW-NONE START_WORKFLOW, no WorkflowID in output → nothing yielded
  OUT-WORKFLOW-ERR  START_WORKFLOW, WorkflowID present, get_definition raises → ERROR response yielded
  OUT-WORKFLOW-OK   START_WORKFLOW, WorkflowID present, definition returned → WORKFLOW yielded
    OUT-UNHANDLED     USER_PREFERENCE tool_name → match fall-through, nothing yielded
                                        (intentional: USER_PREFERENCE result unneeded)
    OUT-APPLICATION   APPLICATION tool_name → legacy side effect only, no frontend chunk
    OUT-REGISTRATION  REGISTRATION tool_name → legacy side effect only, no frontend chunk

ToolEventHandler.build_stop_at_tool_outputs():
  BSO-NO-STOP       stop_at_tool_exists=False → [] returned
  BSO-NON-FCO       item.type != "function_call_output" → skipped
  BSO-NO-CALL-ID    item.call_id is not str → skipped
  BSO-POS-SEARCH    position search call_id → fake result output appended
  BSO-JOBTYPE-KW    JOBTYPE_SEARCH_BY_KEYWORDS call_id → jobtype output appended
  BSO-JOBTYPE-NAT   JOBTYPE_SEARCH_BY_NATURE call_id → jobtype output appended
  BSO-OTHER         tracked call_id but not position/jobtype → item appended as-is
  BSO-UNKNOWN       call_id not in _tool_calls → item appended as-is
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


pytestmark = pytest.mark.pre_extraction_parity
from domain.entities.chat_session import ChatSessionStatus
from repositories.action_log_repo import ActionLogRepository, ActionLogType
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.user_repo import UserRepository
from services.chat.tool_event_handler import (
    PositionSearchRateLimitExceeded,
    RetryableToolOutputFailure,
    ToolEventHandler,
    _generate_position_search_fake_result,
    _parse_tool_output,
    _process_jobtype_search_result,
)
from services.rate_limit_service import RateLimitService
from services.workflow_service import WorkflowService
from utils.chat_response import ChatResponseType, ChatStreamResponse
from utils.enum import PageName, ToolName


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handler(
    *,
    position_search_allowed: bool = True,
    workflow_definition: Any = None,
    workflow_definition_raises: Exception | None = None,
    current_page: PageName = PageName.CHAT,
    encrypted_position_id: str | None = None,
) -> ToolEventHandler:
    position_repository = MagicMock(spec=PositionRepository)
    position_repository.process_position_search_result.return_value = {"Positions": []}

    chat_repository = MagicMock(spec=ChatRepository)
    user_repository = MagicMock(spec=UserRepository)
    action_log_repository = MagicMock(spec=ActionLogRepository)

    rate_limit_service = MagicMock(spec=RateLimitService)
    rate_limit_service.is_within_position_search_limit.return_value = (
        position_search_allowed
    )

    workflow_service = MagicMock(spec=WorkflowService)
    if workflow_definition_raises is not None:
        workflow_service.get_definition.side_effect = workflow_definition_raises
    elif workflow_definition is not None:
        mock_def = MagicMock()
        mock_def.model_dump.return_value = workflow_definition
        workflow_service.get_definition.return_value = mock_def
    else:
        workflow_service.get_definition.side_effect = ValueError("no def")

    return ToolEventHandler(
        position_repository=position_repository,
        rate_limit_service=rate_limit_service,
        workflow_service=workflow_service,
        chat_repository=chat_repository,
        user_repository=user_repository,
        action_log_repository=action_log_repository,
        current_page=current_page,
        encrypted_position_id=encrypted_position_id,
    )


def _make_tool_call_item(
    name: str, call_id: str = "call-1", arguments: str = "{}"
) -> MagicMock:
    """Build a mock ToolCallItem with raw_item having .name, .call_id, .arguments."""
    from agents import ToolCallItem

    item = MagicMock(spec=ToolCallItem)
    item.raw_item = SimpleNamespace(name=name, call_id=call_id, arguments=arguments)
    return item


def _make_tool_output_item(call_id: str, output: Any) -> MagicMock:
    """Build a mock ToolCallOutputItem with raw_item dict containing call_id and output."""
    from agents import ToolCallOutputItem

    item = MagicMock(spec=ToolCallOutputItem)
    item.raw_item = {"call_id": call_id, "output": output}
    item.output = output
    return item


def _make_chat_response() -> MagicMock:
    mock = MagicMock(spec=ChatStreamResponse)
    mock.create_tool_result_response.side_effect = (
        lambda msg_id, resp_type, result, session_status: SimpleNamespace(
            type=resp_type,
            message_id=msg_id,
            result=result,
        )
    )
    mock.create_error_response.side_effect = (
        lambda error, session_status, is_maintenance=False: SimpleNamespace(
            type="error",
            error=error,
        )
    )
    return mock


async def _collect_output(
    handler: ToolEventHandler, item, chat_response=None, session_status=None
):
    if chat_response is None:
        chat_response = _make_chat_response()
    if session_status is None:
        session_status = ChatSessionStatus.CHATTING
    results = []
    async for chunk in handler.handle_tool_output(item, chat_response, session_status):
        results.append(chunk)
    return results


# ---------------------------------------------------------------------------
# _parse_tool_output
# ---------------------------------------------------------------------------


class TestParseToolOutput:
    """Branch coverage for _parse_tool_output()."""

    def test_str_input_json_decode_ok(self):
        """PARSE-STR-OK: str input → JSON decode succeeds → dict returned."""
        data = {"key": "value", "num": 42}
        result = _parse_tool_output(json.dumps(data))
        assert result == data

    def test_str_input_json_decode_fail(self, caplog):
        """PARSE-STR-FAIL: str input → JSON decode fails → {} returned."""
        result = _parse_tool_output("not valid json")
        assert result == {}

    def test_dict_input_returned_directly(self):
        """PARSE-DICT: dict input → returned directly."""
        data = {"AllPositionIds": [1, 2, 3]}
        result = _parse_tool_output(data)
        assert result == data

    def test_list_empty_returns_empty_dict(self):
        """PARSE-LIST-EMPTY: list input, empty → {} returned."""
        result = _parse_tool_output([])
        assert result == {}

    def test_list_first_element_not_dict(self):
        """PARSE-LIST-NODICT: list first element is not dict → {} returned."""
        result = _parse_tool_output(["string_item"])
        assert result == {}

    def test_list_first_element_is_dict(self):
        """PARSE-LIST-DICT: list first element is dict → inner dict extracted."""
        inner = {"AllPositionIds": [1]}
        result = _parse_tool_output([inner])
        assert result == inner

    def test_non_str_dict_list_input_returns_empty(self):
        """PARSE-ELSE: outer_result is int (not str/dict/list) → {} returned."""
        result = _parse_tool_output(42)
        assert result == {}

    def test_inner_result_is_dict(self):
        """PARSE-INNER-DICT: inner_result (from 'text' key) is dict → returned directly."""
        inner_dict = {"AllPositionIds": [5, 6]}
        data = {"text": inner_dict}
        result = _parse_tool_output(data)
        assert result == inner_dict

    def test_inner_result_not_str_not_dict(self):
        """PARSE-INNER-NOTSTR: inner_result is not str and not dict → {} returned."""
        data = {"text": 12345}
        result = _parse_tool_output(data)
        assert result == {}

    def test_inner_result_str_json_ok(self):
        """PARSE-INNER-STR-OK: inner_result is JSON str → decoded dict returned."""
        inner = {"AllPositionIds": [7, 8]}
        data = {"text": json.dumps(inner)}
        result = _parse_tool_output(data)
        assert result == inner

    def test_inner_result_str_json_fail(self):
        """PARSE-INNER-STR-FAIL: inner_result is non-JSON str → {} returned."""
        data = {"text": "not json"}
        result = _parse_tool_output(data)
        assert result == {}

    def test_str_input_outer_result_is_list_with_dict(self):
        """PARSE-STR-OK + PARSE-LIST-DICT path: str containing JSON array."""
        inner = {"AllPositionIds": [1]}
        result = _parse_tool_output(json.dumps([inner]))
        assert result == inner


# ---------------------------------------------------------------------------
# _generate_position_search_fake_result
# ---------------------------------------------------------------------------


class TestGeneratePositionSearchFakeResult:
    def test_returns_string_with_count(self):
        """FAKE-RESULT: count is included in returned string."""
        result = _generate_position_search_fake_result(5)
        assert "5件" in result
        assert isinstance(result, str)

    def test_returns_string_with_zero_count(self):
        """FAKE-RESULT: count=0 handled correctly."""
        result = _generate_position_search_fake_result(0)
        assert "0件" in result


# ---------------------------------------------------------------------------
# _process_jobtype_search_result
# ---------------------------------------------------------------------------


class TestProcessJobtypeSearchResult:
    def test_falsy_jobtypes_returns_none(self):
        """JOBT-EMPTY: jobtypes is None → None returned."""
        result = _process_jobtype_search_result("c1", "tool", "{}", None)
        assert result is None

    def test_empty_dict_jobtypes_returns_none(self):
        """JOBT-EMPTY: jobtypes is {} → None returned."""
        result = _process_jobtype_search_result("c1", "tool", "{}", {})
        assert result is None

    def test_no_shokushu_key_returns_none(self):
        """JOBT-NO-KEY: jobtypes has no '職種' key → None returned."""
        result = _process_jobtype_search_result("c1", "tool", "{}", {"other": []})
        assert result is None

    def test_empty_shokushu_returns_none(self):
        """JOBT-NO-KEY: jobtypes has '職種' key with empty list → None returned."""
        result = _process_jobtype_search_result("c1", "tool", "{}", {"職種": []})
        assert result is None

    def test_valid_jobtypes_returns_normalized(self):
        """JOBT-OK: valid jobtypes → normalized result dict returned."""
        jobtypes = {
            "職種": [
                {"職種名": "エンジニア", "職種説明": "software engineer"},
                {"職種名": "デザイナー", "職種説明": "designer"},
            ],
            "Keyword": "tech",
        }
        result = _process_jobtype_search_result(
            "call-1", "search_occupations_by_sentence", '{"q": "tech"}', jobtypes
        )
        assert result is not None
        assert result["Keyword"] == "tech"
        assert len(result["Jobtypes"]) == 2
        assert result["Jobtypes"][0] == {
            "ID": "エンジニア",
            "Name": "software engineer",
        }
        assert result["ToolCall"]["ID"] == "call-1"

    def test_keyword_from_japanese_key(self):
        """JOBT-OK: Keyword falls back to '検索キーワード' key."""
        jobtypes = {
            "職種": [{"職種名": "営業", "職種説明": "sales"}],
            "検索キーワード": "sales",
        }
        result = _process_jobtype_search_result("c2", "tool", "{}", jobtypes)
        assert result is not None
        assert result["Keyword"] == "sales"

    def test_keyword_non_string_becomes_empty(self):
        """JOBT-OK: keyword is non-string → empty string used."""
        jobtypes = {
            "職種": [{"職種名": "営業", "職種説明": "sales"}],
            "Keyword": 123,
        }
        result = _process_jobtype_search_result("c3", "tool", "{}", jobtypes)
        assert result is not None
        assert result["Keyword"] == ""


# ---------------------------------------------------------------------------
# ToolEventHandler.handle_tool_call
# ---------------------------------------------------------------------------


class TestHandleToolCall:
    @pytest.mark.asyncio
    async def test_unknown_tool_name_not_recorded(self):
        """TC-UNKNOWN: tool name not in ToolName enum → not recorded in _tool_calls."""
        handler = _make_handler()
        item = _make_tool_call_item("unknown_tool", call_id="c1")

        await handler.handle_tool_call(item, client_ip="1.2.3.4")

        assert handler._tool_calls == {}
        handler._rate_limit_service.is_within_position_search_limit.assert_not_called()

    @pytest.mark.asyncio
    async def test_position_search_tool_rate_limit_checked(self):
        """TC-POS-SEARCH: position search tool → rate limit checked and tool recorded."""
        handler = _make_handler(position_search_allowed=True)
        item = _make_tool_call_item(ToolName.GENERIC_POSITION_SEARCH, call_id="c-pos-1")

        with patch(
            "services.chat.tool_event_handler.asyncio.to_thread", new_callable=AsyncMock
        ) as mock_to_thread:
            mock_to_thread.return_value = True
            await handler.handle_tool_call(item, client_ip="1.2.3.4")

        assert "c-pos-1" in handler._tool_calls
        mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_position_search_tool_no_rate_limit_check(self):
        """TC-NON-POS: non-position-search tool → recorded without rate limit check."""
        handler = _make_handler()
        item = _make_tool_call_item(ToolName.START_WORKFLOW, call_id="c-wf-1")

        await handler.handle_tool_call(item, client_ip="1.2.3.4")

        assert "c-wf-1" in handler._tool_calls
        handler._rate_limit_service.is_within_position_search_limit.assert_not_called()

    @pytest.mark.asyncio
    async def test_it_position_search_tool_rate_limit_checked(self):
        """TC-POS-SEARCH: IT position search tool → rate limit checked."""
        handler = _make_handler(position_search_allowed=True)
        item = _make_tool_call_item(ToolName.IT_POSITION_SEARCH, call_id="c-it-1")

        with patch(
            "services.chat.tool_event_handler.asyncio.to_thread", new_callable=AsyncMock
        ) as mock_to_thread:
            mock_to_thread.return_value = True
            await handler.handle_tool_call(item, client_ip="10.0.0.1")

        assert "c-it-1" in handler._tool_calls
        mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_parallel_calls_same_tool_type_both_stored(self):
        """TC-PARALLEL: two GENERIC_POSITION_SEARCH calls in one turn → both stored (call_id key, no overwrite)."""
        handler = _make_handler(position_search_allowed=True)
        item_a = _make_tool_call_item(ToolName.GENERIC_POSITION_SEARCH, call_id="c-a")
        item_b = _make_tool_call_item(ToolName.GENERIC_POSITION_SEARCH, call_id="c-b")

        with patch(
            "services.chat.tool_event_handler.asyncio.to_thread", new_callable=AsyncMock
        ) as mock_to_thread:
            mock_to_thread.return_value = True
            await handler.handle_tool_call(item_a, client_ip="1.2.3.4")
            await handler.handle_tool_call(item_b, client_ip="1.2.3.4")

        assert "c-a" in handler._tool_calls
        assert "c-b" in handler._tool_calls
        assert handler._tool_calls["c-a"][0] == ToolName.GENERIC_POSITION_SEARCH
        assert handler._tool_calls["c-b"][0] == ToolName.GENERIC_POSITION_SEARCH


# ---------------------------------------------------------------------------
# ToolEventHandler._ensure_tool_execution_available
# ---------------------------------------------------------------------------


class TestEnsureToolExecutionAvailable:
    @pytest.mark.asyncio
    async def test_rate_limit_allowed_no_exception(self):
        """RATE-ALLOWED: rate limit allows → no exception raised."""
        handler = _make_handler(position_search_allowed=True)

        with patch(
            "services.chat.tool_event_handler.asyncio.to_thread", new_callable=AsyncMock
        ) as mock_to_thread:
            mock_to_thread.return_value = True
            # Should not raise
            await handler._ensure_tool_execution_available(client_ip="1.2.3.4")

    @pytest.mark.asyncio
    async def test_rate_limit_denied_raises_exception(self):
        """RATE-DENIED: rate limit denies → PositionSearchRateLimitExceeded raised."""
        handler = _make_handler(position_search_allowed=False)

        with patch(
            "services.chat.tool_event_handler.asyncio.to_thread", new_callable=AsyncMock
        ) as mock_to_thread:
            mock_to_thread.return_value = False
            with pytest.raises(PositionSearchRateLimitExceeded):
                await handler._ensure_tool_execution_available(client_ip="1.2.3.4")


# ---------------------------------------------------------------------------
# ToolEventHandler.handle_tool_output
# ---------------------------------------------------------------------------


class TestHandleToolOutput:
    @pytest.mark.asyncio
    async def test_raw_item_missing_call_id_field_yields_nothing(self):
        """OUT-CALL-ID-NONE: raw_item has no 'call_id' field → _get_raw_item_field returns None → nothing yielded."""
        from agents import ToolCallOutputItem
        from types import SimpleNamespace

        handler = _make_handler()
        # raw_item is a SimpleNamespace with no call_id attribute at all
        item = MagicMock(spec=ToolCallOutputItem)
        item.raw_item = SimpleNamespace()  # no call_id attribute
        item.output = json.dumps({"AllPositionIds": [1]})

        results = await _collect_output(handler, item)

        assert results == []

    @pytest.mark.asyncio
    async def test_call_id_not_found_yields_nothing(self):
        """OUT-NO-CALL-ID: call_id present but not in _tool_calls → nothing yielded."""
        handler = _make_handler()
        # No tool calls recorded
        output = json.dumps({"AllPositionIds": [1, 2]})
        item = _make_tool_output_item(call_id="unknown-call", output=output)

        results = await _collect_output(handler, item)

        assert results == []

    @pytest.mark.asyncio
    async def test_message_key_in_output_raises_retryable_failure(self):
        """OUT-MESSAGE-KEY: 'Message' in parsed output -> RetryableToolOutputFailure."""
        handler = _make_handler()
        # Record a tool call first
        tc_item = _make_tool_call_item(ToolName.GENERIC_POSITION_SEARCH, call_id="c1")
        handler._tool_calls["c1"] = (ToolName.GENERIC_POSITION_SEARCH, tc_item.raw_item)

        output = json.dumps({"Message": "Tool execution failed"})
        item = _make_tool_output_item(call_id="c1", output=output)

        with pytest.raises(RetryableToolOutputFailure) as exc_info:
            await _collect_output(handler, item)

        assert exc_info.value.call_id == "c1"
        assert "Tool execution failed" in exc_info.value.message_to_llm
        handler._position_repository.process_position_search_result.assert_not_called()

    @pytest.mark.asyncio
    async def test_generic_position_search_yields_result(self):
        """OUT-POS-SEARCH: GENERIC_POSITION_SEARCH → POSITION_SEARCH_RESULT yielded."""
        handler = _make_handler()
        tc_item = _make_tool_call_item(ToolName.GENERIC_POSITION_SEARCH, call_id="c1")
        handler._tool_calls["c1"] = (ToolName.GENERIC_POSITION_SEARCH, tc_item.raw_item)

        output = json.dumps({"AllPositionIds": [10, 20, 30]})
        item = _make_tool_output_item(call_id="c1", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert results[0].type == ChatResponseType.POSITION_SEARCH_RESULT
        # Check count was recorded
        assert handler._position_search_counts.get("c1") == 3

    @pytest.mark.asyncio
    async def test_it_position_search_yields_result(self):
        """OUT-POS-SEARCH: IT_POSITION_SEARCH → POSITION_SEARCH_RESULT yielded."""
        handler = _make_handler()
        tc_item = _make_tool_call_item(ToolName.IT_POSITION_SEARCH, call_id="c-it")
        handler._tool_calls["c-it"] = (ToolName.IT_POSITION_SEARCH, tc_item.raw_item)

        output = json.dumps({"AllPositionIds": [1, 2]})
        item = _make_tool_output_item(call_id="c-it", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert results[0].type == ChatResponseType.POSITION_SEARCH_RESULT

    @pytest.mark.asyncio
    async def test_financial_sales_position_search_yields_result(self):
        """OUT-POS-SEARCH: FINANCIAL_SALES_POSITION_SEARCH → POSITION_SEARCH_RESULT yielded."""
        handler = _make_handler()
        tc_item = _make_tool_call_item(
            ToolName.FINANCIAL_SALES_POSITION_SEARCH, call_id="c-fin"
        )
        handler._tool_calls["c-fin"] = (
            ToolName.FINANCIAL_SALES_POSITION_SEARCH,
            tc_item.raw_item,
        )

        output = json.dumps({"AllPositionIds": []})
        item = _make_tool_output_item(call_id="c-fin", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert results[0].type == ChatResponseType.POSITION_SEARCH_RESULT
        # Empty AllPositionIds → count 0
        assert handler._position_search_counts.get("c-fin") == 0

    @pytest.mark.asyncio
    async def test_position_search_no_all_position_ids_key(self):
        """OUT-POS-SEARCH: AllPositionIds missing → count 0."""
        handler = _make_handler()
        tc_item = _make_tool_call_item(
            ToolName.GENERIC_POSITION_SEARCH, call_id="c-noids"
        )
        handler._tool_calls["c-noids"] = (
            ToolName.GENERIC_POSITION_SEARCH,
            tc_item.raw_item,
        )

        output = json.dumps({"SomeOtherField": "data"})
        item = _make_tool_output_item(call_id="c-noids", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert handler._position_search_counts.get("c-noids") == 0

    @pytest.mark.asyncio
    async def test_position_search_non_list_all_position_ids(self):
        """OUT-POS-SEARCH: AllPositionIds is not a list → count 0."""
        handler = _make_handler()
        tc_item = _make_tool_call_item(
            ToolName.GENERIC_POSITION_SEARCH, call_id="c-nonlist"
        )
        handler._tool_calls["c-nonlist"] = (
            ToolName.GENERIC_POSITION_SEARCH,
            tc_item.raw_item,
        )

        output = json.dumps({"AllPositionIds": "not-a-list"})
        item = _make_tool_output_item(call_id="c-nonlist", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert handler._position_search_counts.get("c-nonlist") == 0

    @pytest.mark.asyncio
    async def test_jobtype_search_by_keywords_no_result_yields_nothing(self):
        """OUT-JOBTYPE-NONE: JOBTYPE_SEARCH_BY_KEYWORDS, _process_jobtype returns None → nothing yielded."""
        handler = _make_handler()
        tc_item = _make_tool_call_item(
            ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
            call_id="c-jt",
            arguments='{"query": "tech"}',
        )
        handler._tool_calls["c-jt"] = (
            ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
            tc_item.raw_item,
        )

        # Empty output → no '職種' key → None from _process_jobtype_search_result
        output = json.dumps({})
        item = _make_tool_output_item(call_id="c-jt", output=output)

        results = await _collect_output(handler, item)

        assert results == []

    @pytest.mark.asyncio
    async def test_jobtype_search_by_keywords_with_result_yields_chunk(self):
        """OUT-JOBTYPE-OK: JOBTYPE_SEARCH_BY_KEYWORDS with valid output → JOBTYPE_SEARCH_RESULT yielded."""
        handler = _make_handler()
        tc_item = _make_tool_call_item(
            ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
            call_id="c-jt2",
            arguments='{"query": "engineer"}',
        )
        handler._tool_calls["c-jt2"] = (
            ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
            tc_item.raw_item,
        )

        jobtypes_output = {
            "職種": [{"職種名": "エンジニア", "職種説明": "engineer"}],
            "Keyword": "engineer",
        }
        output = json.dumps(jobtypes_output)
        item = _make_tool_output_item(call_id="c-jt2", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert results[0].type == ChatResponseType.JOBTYPE_SEARCH_RESULT

    @pytest.mark.asyncio
    async def test_jobtype_search_by_nature_with_result_yields_chunk(self):
        """OUT-JOBTYPE-OK: JOBTYPE_SEARCH_BY_NATURE with valid output → JOBTYPE_SEARCH_RESULT yielded."""
        handler = _make_handler()
        tc_item = _make_tool_call_item(
            ToolName.JOBTYPE_SEARCH_BY_NATURE,
            call_id="c-jtn",
            arguments='{"nature": "creative"}',
        )
        handler._tool_calls["c-jtn"] = (
            ToolName.JOBTYPE_SEARCH_BY_NATURE,
            tc_item.raw_item,
        )

        jobtypes_output = {
            "職種": [{"職種名": "デザイナー", "職種説明": "designer"}],
            "Keyword": "creative",
        }
        output = json.dumps(jobtypes_output)
        item = _make_tool_output_item(call_id="c-jtn", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert results[0].type == ChatResponseType.JOBTYPE_SEARCH_RESULT

    @pytest.mark.asyncio
    async def test_start_workflow_no_workflow_id_yields_nothing(self):
        """OUT-WORKFLOW-NONE: START_WORKFLOW, no WorkflowID in output → nothing yielded."""
        handler = _make_handler()
        tc_item = _make_tool_call_item(ToolName.START_WORKFLOW, call_id="c-wf")
        handler._tool_calls["c-wf"] = (ToolName.START_WORKFLOW, tc_item.raw_item)

        output = json.dumps({"SomeField": "no workflow id here"})
        item = _make_tool_output_item(call_id="c-wf", output=output)

        results = await _collect_output(handler, item)

        assert results == []

    @pytest.mark.asyncio
    async def test_start_workflow_get_definition_raises_value_error_yields_error(self):
        """OUT-WORKFLOW-ERR: START_WORKFLOW, WorkflowID present, get_definition raises ValueError → ERROR response yielded."""
        handler = _make_handler(workflow_definition_raises=ValueError("not found"))
        tc_item = _make_tool_call_item(ToolName.START_WORKFLOW, call_id="c-wf-err")
        handler._tool_calls["c-wf-err"] = (ToolName.START_WORKFLOW, tc_item.raw_item)

        output = json.dumps({"WorkflowID": "wf-001"})
        item = _make_tool_output_item(call_id="c-wf-err", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert results[0].type == "error"
        assert results[0].error == "ワークフローが実行できませんでした。"

    @pytest.mark.asyncio
    async def test_start_workflow_get_definition_raises_file_not_found_yields_error(
        self,
    ):
        """OUT-WORKFLOW-ERR: START_WORKFLOW, WorkflowID present, get_definition raises FileNotFoundError → ERROR response yielded."""
        handler = _make_handler(workflow_definition_raises=FileNotFoundError("missing"))
        tc_item = _make_tool_call_item(ToolName.START_WORKFLOW, call_id="c-wf-fnf")
        handler._tool_calls["c-wf-fnf"] = (ToolName.START_WORKFLOW, tc_item.raw_item)

        output = json.dumps({"WorkflowID": "wf-missing"})
        item = _make_tool_output_item(call_id="c-wf-fnf", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert results[0].type == "error"
        assert results[0].error == "ワークフローが実行できませんでした。"

    @pytest.mark.asyncio
    async def test_start_workflow_with_definition_yields_workflow(self):
        """OUT-WORKFLOW-OK: START_WORKFLOW, definition returned → WORKFLOW yielded."""
        wf_def = {"id": "wf-001", "name": "OnboardingWorkflow", "steps": []}
        handler = _make_handler(workflow_definition=wf_def)
        tc_item = _make_tool_call_item(ToolName.START_WORKFLOW, call_id="c-wf-ok")
        handler._tool_calls["c-wf-ok"] = (ToolName.START_WORKFLOW, tc_item.raw_item)

        output = json.dumps({"WorkflowID": "wf-001"})
        item = _make_tool_output_item(call_id="c-wf-ok", output=output)

        results = await _collect_output(handler, item)

        assert len(results) == 1
        assert results[0].type == ChatResponseType.WORKFLOW

    @pytest.mark.asyncio
    async def test_unhandled_tool_name_in_tool_calls_yields_nothing(self):
        """OUT-UNHANDLED: tool recorded in _tool_calls but not in match cases → nothing yielded (match fall-through)."""
        handler = _make_handler()
        # USER_PREFERENCE is a valid ToolName but has no match case in handle_tool_output
        tc_item = _make_tool_call_item(ToolName.USER_PREFERENCE, call_id="c-up")
        handler._tool_calls["c-up"] = (ToolName.USER_PREFERENCE, tc_item.raw_item)

        output = json.dumps({"some": "data"})
        item = _make_tool_output_item(call_id="c-up", output=output)

        results = await _collect_output(handler, item)

        assert results == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("session_status", "expected_status_update"),
        [
            (ChatSessionStatus.CHATTING, ChatSessionStatus.APPLYING),
            (ChatSessionStatus.APPLYING, None),
            (ChatSessionStatus.REGISTERING, ChatSessionStatus.APPLYING),
        ],
    )
    async def test_application_from_position_detail_adds_position_and_sets_applying(
        self,
        session_status,
        expected_status_update,
    ):
        """OUT-APPLICATION: position detail page → 応募ポジション追加後 APPLYING に遷移する。"""
        handler = _make_handler(
            current_page=PageName.POSITION_DETAIL,
            encrypted_position_id="enc-pos-1",
        )
        tc_item = _make_tool_call_item(ToolName.APPLICATION, call_id="c-app")
        handler._tool_calls["c-app"] = (ToolName.APPLICATION, tc_item.raw_item)

        with patch("services.chat.tool_event_handler.decrypt", return_value="real-pos"):
            item = _make_tool_output_item(call_id="c-app", output=json.dumps({}))
            results = await _collect_output(
                handler,
                item,
                session_status=session_status,
            )

        assert results == []
        assert handler.consume_session_status_update() == expected_status_update
        handler._user_repository.add_apply_position.assert_called_once_with("real-pos")
        handler._user_repository.update_miidas_registration_user_data.assert_not_called()
        handler._chat_repository.update_session_status.assert_called_once_with(
            ChatSessionStatus.APPLYING,
        )
        handler._action_log_repository.insert.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "session_status",
        [
            ChatSessionStatus.REGISTERED,
            ChatSessionStatus.APPLIED,
        ],
    )
    async def test_application_when_already_completed_is_noop(self, session_status):
        """OUT-APPLICATION: completed apply/registration status → no additional side effects."""
        handler = _make_handler(
            current_page=PageName.POSITION_DETAIL,
            encrypted_position_id="enc-pos-1",
        )
        tc_item = _make_tool_call_item(ToolName.APPLICATION, call_id="c-app-noop")
        handler._tool_calls["c-app-noop"] = (ToolName.APPLICATION, tc_item.raw_item)

        with patch("services.chat.tool_event_handler.decrypt", return_value="real-pos"):
            item = _make_tool_output_item(call_id="c-app-noop", output=json.dumps({}))
            results = await _collect_output(
                handler,
                item,
                session_status=session_status,
            )

        assert results == []
        assert handler.consume_session_status_update() is None
        handler._user_repository.update_miidas_registration_user_data.assert_not_called()
        handler._chat_repository.update_session_status.assert_not_called()
        handler._action_log_repository.insert.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "session_status",
        [ChatSessionStatus.APPLYING, ChatSessionStatus.REGISTERING],
    )
    async def test_application_in_progress_from_non_position_detail_logs_error_and_noop(
        self,
        caplog,
        session_status,
    ):
        """OUT-APPLICATION: APPLYING/REGISTERING + non-position-detail → error log and no side effects."""
        handler = _make_handler(current_page=PageName.CHAT)
        tc_item = _make_tool_call_item(
            ToolName.APPLICATION, call_id="c-app-in-progress-err"
        )
        handler._tool_calls["c-app-in-progress-err"] = (
            ToolName.APPLICATION,
            tc_item.raw_item,
        )

        item = _make_tool_output_item(
            call_id="c-app-in-progress-err",
            output=json.dumps({}),
        )
        with caplog.at_level("ERROR"):
            results = await _collect_output(
                handler,
                item,
                session_status=session_status,
            )

        assert results == []
        assert handler.consume_session_status_update() is None
        handler._user_repository.add_apply_position.assert_not_called()
        handler._user_repository.update_miidas_registration_user_data.assert_not_called()
        handler._chat_repository.update_session_status.assert_not_called()
        handler._action_log_repository.insert.assert_not_called()
        assert any(
            "ポジション詳細ページ以外からの応募" in message
            for message in caplog.messages
        )

    @pytest.mark.asyncio
    async def test_application_from_non_position_detail_logs_error_and_noop(
        self, caplog
    ):
        """OUT-APPLICATION: non-position-detail page → error log and no side effects."""
        handler = _make_handler(current_page=PageName.CHAT)
        tc_item = _make_tool_call_item(ToolName.APPLICATION, call_id="c-app-err")
        handler._tool_calls["c-app-err"] = (ToolName.APPLICATION, tc_item.raw_item)

        item = _make_tool_output_item(call_id="c-app-err", output=json.dumps({}))
        with caplog.at_level("ERROR"):
            results = await _collect_output(
                handler,
                item,
                session_status=ChatSessionStatus.CHATTING,
            )

        assert results == []
        assert handler.consume_session_status_update() is None
        handler._user_repository.update_miidas_registration_user_data.assert_not_called()
        handler._chat_repository.update_session_status.assert_not_called()
        assert any(
            "ポジション詳細ページ以外からの応募" in message
            for message in caplog.messages
        )

    @pytest.mark.asyncio
    async def test_application_with_missing_encrypted_position_id_does_not_set_applying(
        self,
        caplog,
    ):
        """OUT-APPLICATION: encrypted_position_id がない場合、CHATTING から REGISTERING へフォールバックする。"""
        handler = _make_handler(
            current_page=PageName.POSITION_DETAIL,
            encrypted_position_id=None,
        )
        tc_item = _make_tool_call_item(
            ToolName.APPLICATION, call_id="c-app-missing-pos"
        )
        handler._tool_calls["c-app-missing-pos"] = (
            ToolName.APPLICATION,
            tc_item.raw_item,
        )

        item = _make_tool_output_item(
            call_id="c-app-missing-pos",
            output=json.dumps({}),
        )
        with caplog.at_level("ERROR"):
            with patch("services.chat.tool_event_handler.decrypt") as mock_decrypt:
                results = await _collect_output(
                    handler,
                    item,
                    session_status=ChatSessionStatus.CHATTING,
                )

        assert results == []
        assert handler.consume_session_status_update() == ChatSessionStatus.REGISTERING
        mock_decrypt.assert_not_called()
        handler._user_repository.add_apply_position.assert_not_called()
        handler._chat_repository.update_session_status.assert_called_once_with(
            ChatSessionStatus.REGISTERING,
        )
        assert any(
            "応募処理をスキップ: encrypted_position_id が未設定です" in message
            for message in caplog.messages
        )

    @pytest.mark.asyncio
    async def test_application_with_decrypt_failure_does_not_update_session_status(
        self,
        caplog,
    ):
        """OUT-APPLICATION: decrypt 失敗時は CHATTING から REGISTERING へフォールバックする。"""
        handler = _make_handler(
            current_page=PageName.POSITION_DETAIL,
            encrypted_position_id="enc-pos-fail",
        )
        tc_item = _make_tool_call_item(
            ToolName.APPLICATION, call_id="c-app-decrypt-fail"
        )
        handler._tool_calls["c-app-decrypt-fail"] = (
            ToolName.APPLICATION,
            tc_item.raw_item,
        )

        item = _make_tool_output_item(
            call_id="c-app-decrypt-fail",
            output=json.dumps({}),
        )
        with caplog.at_level("ERROR"):
            with patch(
                "services.chat.tool_event_handler.decrypt",
                side_effect=ValueError("decrypt failed"),
            ):
                results = await _collect_output(
                    handler,
                    item,
                    session_status=ChatSessionStatus.CHATTING,
                )

        assert results == []
        assert handler.consume_session_status_update() == ChatSessionStatus.REGISTERING
        handler._user_repository.add_apply_position.assert_not_called()
        handler._chat_repository.update_session_status.assert_called_once_with(
            ChatSessionStatus.REGISTERING,
        )
        assert any(
            "応募ポジションの追加に失敗しました" in message
            for message in caplog.messages
        )

    @pytest.mark.asyncio
    async def test_application_with_add_apply_position_failure_falls_back_to_registering(
        self,
    ):
        """OUT-APPLICATION: add_apply_position が False のとき CHATTING から REGISTERING へフォールバックする。"""
        handler = _make_handler(
            current_page=PageName.POSITION_DETAIL,
            encrypted_position_id="enc-pos-fail-save",
        )
        handler._user_repository.add_apply_position.return_value = False

        tc_item = _make_tool_call_item(ToolName.APPLICATION, call_id="c-app-save-fail")
        handler._tool_calls["c-app-save-fail"] = (
            ToolName.APPLICATION,
            tc_item.raw_item,
        )

        with patch("services.chat.tool_event_handler.decrypt", return_value="real-pos"):
            item = _make_tool_output_item(
                call_id="c-app-save-fail",
                output=json.dumps({}),
            )
            results = await _collect_output(
                handler,
                item,
                session_status=ChatSessionStatus.CHATTING,
            )

        assert results == []
        assert handler.consume_session_status_update() == ChatSessionStatus.REGISTERING
        handler._user_repository.add_apply_position.assert_called_once_with("real-pos")
        handler._chat_repository.update_session_status.assert_called_once_with(
            ChatSessionStatus.REGISTERING,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("current_page", [PageName.CHAT, PageName.POSITION_DETAIL])
    async def test_registration_from_allowed_pages_updates_status_and_logs_action(
        self, current_page
    ):
        """OUT-REGISTRATION: CHAT/POSITION_DETAIL + chatting → REGISTERING に遷移する。"""
        handler = _make_handler(current_page=current_page)
        tc_item = _make_tool_call_item(ToolName.REGISTRATION, call_id="c-reg")
        handler._tool_calls["c-reg"] = (ToolName.REGISTRATION, tc_item.raw_item)

        item = _make_tool_output_item(call_id="c-reg", output=json.dumps({}))
        results = await _collect_output(
            handler,
            item,
            session_status=ChatSessionStatus.CHATTING,
        )

        assert results == []
        assert handler.consume_session_status_update() == ChatSessionStatus.REGISTERING
        handler._action_log_repository.insert.assert_called_once_with(
            log_type=ActionLogType.REGISTRATION,
            source=current_page,
        )
        handler._chat_repository.update_session_status.assert_called_once_with(
            ChatSessionStatus.REGISTERING,
        )
        handler._user_repository.update_miidas_registration_user_data.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "session_status",
        [
            ChatSessionStatus.REGISTERING,
            ChatSessionStatus.APPLYING,
            ChatSessionStatus.REGISTERED,
            ChatSessionStatus.APPLIED,
        ],
    )
    async def test_registration_when_not_chatting_still_updates_allowed_pages(
        self, session_status
    ):
        """OUT-REGISTRATION: legacy code still registers side effects for non-chatting statuses."""
        handler = _make_handler(current_page=PageName.CHAT)
        tc_item = _make_tool_call_item(ToolName.REGISTRATION, call_id="c-reg-noop")
        handler._tool_calls["c-reg-noop"] = (ToolName.REGISTRATION, tc_item.raw_item)

        item = _make_tool_output_item(call_id="c-reg-noop", output=json.dumps({}))
        results = await _collect_output(
            handler,
            item,
            session_status=session_status,
        )

        assert results == []
        assert handler.consume_session_status_update() == ChatSessionStatus.REGISTERING
        handler._action_log_repository.insert.assert_called_once_with(
            log_type=ActionLogType.REGISTRATION,
            source=PageName.CHAT,
        )
        handler._chat_repository.update_session_status.assert_called_once_with(
            ChatSessionStatus.REGISTERING,
        )

    @pytest.mark.asyncio
    async def test_registration_from_invalid_page_logs_error_and_noop(self, caplog):
        """OUT-REGISTRATION: unsupported page → error log and no side effects."""
        handler = _make_handler(current_page=PageName.PROFILE_BASIC_INFO)
        tc_item = _make_tool_call_item(ToolName.REGISTRATION, call_id="c-reg-err")
        handler._tool_calls["c-reg-err"] = (ToolName.REGISTRATION, tc_item.raw_item)

        item = _make_tool_output_item(call_id="c-reg-err", output=json.dumps({}))
        with caplog.at_level("ERROR"):
            results = await _collect_output(
                handler,
                item,
                session_status=ChatSessionStatus.CHATTING,
            )

        assert results == []
        assert handler.consume_session_status_update() is None
        handler._action_log_repository.insert.assert_not_called()
        handler._chat_repository.update_session_status.assert_not_called()
        assert any(
            "知らないページからの会員登録" in message for message in caplog.messages
        )


# ---------------------------------------------------------------------------
# ToolEventHandler.build_stop_at_tool_outputs
# ---------------------------------------------------------------------------


class TestBuildStopAtToolOutputs:
    def test_stop_at_tool_false_returns_empty(self):
        """BSO-NO-STOP: stop_at_tool_exists=False → [] returned."""
        handler = _make_handler()
        replay = [{"type": "function_call_output", "call_id": "c1", "output": "data"}]
        result = handler.build_stop_at_tool_outputs(replay, stop_at_tool_exists=False)
        assert result == []

    def test_non_function_call_output_type_skipped(self):
        """BSO-NON-FCO: item.type != "function_call_output" → skipped."""
        handler = _make_handler()
        replay = [{"type": "other_type", "call_id": "c1", "output": "data"}]
        result = handler.build_stop_at_tool_outputs(replay, stop_at_tool_exists=True)
        assert result == []

    def test_non_str_call_id_skipped(self):
        """BSO-NO-CALL-ID: item.call_id is not str (e.g. None) → skipped."""
        handler = _make_handler()
        replay = [{"type": "function_call_output", "call_id": None, "output": "data"}]
        result = handler.build_stop_at_tool_outputs(replay, stop_at_tool_exists=True)
        assert result == []

    def test_position_search_call_id_appends_fake_result(self):
        """BSO-POS-SEARCH: position search call_id → fake result output appended."""
        handler = _make_handler()
        # Record position search tool call
        tc_raw = SimpleNamespace(call_id="c-pos", name=ToolName.GENERIC_POSITION_SEARCH)
        handler._tool_calls["c-pos"] = (ToolName.GENERIC_POSITION_SEARCH, tc_raw)
        handler._position_search_counts["c-pos"] = 7

        replay = [
            {"type": "function_call_output", "call_id": "c-pos", "output": "original"}
        ]
        result = handler.build_stop_at_tool_outputs(replay, stop_at_tool_exists=True)

        assert len(result) == 1
        assert result[0]["type"] == "function_call_output"
        assert result[0]["call_id"] == "c-pos"
        assert "7件" in result[0]["output"]

    def test_jobtype_search_by_keywords_call_id_appends_jobtype_output(self):
        """BSO-JOBTYPE-KW: JOBTYPE_SEARCH_BY_KEYWORDS call_id → jobtype output appended."""
        handler = _make_handler()
        tc_raw = SimpleNamespace(
            call_id="c-jt-kw", name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS
        )
        handler._tool_calls["c-jt-kw"] = (ToolName.JOBTYPE_SEARCH_BY_KEYWORDS, tc_raw)

        original_output = json.dumps([{"ID": "エンジニア"}])
        replay = [
            {
                "type": "function_call_output",
                "call_id": "c-jt-kw",
                "output": original_output,
            }
        ]
        result = handler.build_stop_at_tool_outputs(replay, stop_at_tool_exists=True)

        assert len(result) == 1
        assert result[0]["call_id"] == "c-jt-kw"
        # The output should be the wrapped jobtype message
        assert "職種名検索" in result[0]["output"]
        assert original_output in result[0]["output"]

    def test_jobtype_search_by_nature_call_id_appends_jobtype_output(self):
        """BSO-JOBTYPE-NAT: JOBTYPE_SEARCH_BY_NATURE call_id → jobtype output appended."""
        handler = _make_handler()
        tc_raw = SimpleNamespace(
            call_id="c-jt-nat", name=ToolName.JOBTYPE_SEARCH_BY_NATURE
        )
        handler._tool_calls["c-jt-nat"] = (ToolName.JOBTYPE_SEARCH_BY_NATURE, tc_raw)

        original_output = json.dumps([{"ID": "デザイナー"}])
        replay = [
            {
                "type": "function_call_output",
                "call_id": "c-jt-nat",
                "output": original_output,
            }
        ]
        result = handler.build_stop_at_tool_outputs(replay, stop_at_tool_exists=True)

        assert len(result) == 1
        assert result[0]["call_id"] == "c-jt-nat"
        assert "職種名検索" in result[0]["output"]

    def test_other_tool_call_id_appended_as_is(self):
        """BSO-OTHER: other tool call_id → item appended as-is."""
        handler = _make_handler()
        tc_raw = SimpleNamespace(call_id="c-wf", name=ToolName.START_WORKFLOW)
        handler._tool_calls["c-wf"] = (ToolName.START_WORKFLOW, tc_raw)

        original_item = {
            "type": "function_call_output",
            "call_id": "c-wf",
            "output": "workflow data",
        }
        replay = [original_item]
        result = handler.build_stop_at_tool_outputs(replay, stop_at_tool_exists=True)

        assert len(result) == 1
        assert result[0] is original_item

    def test_unknown_call_id_appended_as_is(self):
        """BSO-OTHER: call_id not in _tool_calls → item appended as-is."""
        handler = _make_handler()
        # No tool calls recorded — call_id "c-unknown" is not in _tool_calls
        replay = [
            {"type": "function_call_output", "call_id": "c-unknown", "output": "raw"}
        ]
        result = handler.build_stop_at_tool_outputs(replay, stop_at_tool_exists=True)

        assert len(result) == 1
        assert result[0]["call_id"] == "c-unknown"
        assert result[0]["output"] == "raw"

    def test_mixed_replay_items(self):
        """Integration: mixed replay items processed correctly."""
        handler = _make_handler()
        tc_pos = SimpleNamespace(call_id="c-pos", name=ToolName.GENERIC_POSITION_SEARCH)
        handler._tool_calls["c-pos"] = (ToolName.GENERIC_POSITION_SEARCH, tc_pos)
        handler._position_search_counts["c-pos"] = 3

        tc_other = SimpleNamespace(call_id="c-other", name=ToolName.START_WORKFLOW)
        handler._tool_calls["c-other"] = (ToolName.START_WORKFLOW, tc_other)

        replay = [
            {
                "type": "other_type",
                "call_id": "c-skip",
            },  # skipped (not function_call_output)
            {
                "type": "function_call_output",
                "call_id": None,
            },  # skipped (no str call_id)
            {"type": "function_call_output", "call_id": "c-pos", "output": "raw"},
            {"type": "function_call_output", "call_id": "c-other", "output": "wf"},
        ]
        result = handler.build_stop_at_tool_outputs(replay, stop_at_tool_exists=True)

        assert len(result) == 2
        # Position search → fake result
        assert "3件" in result[0]["output"]
        # Other → as-is
        assert result[1]["output"] == "wf"
