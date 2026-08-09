"""Unit tests for HistoryMapper — 100% branch coverage required.

HistoryMapper is a pure data transformation component with no external I/O.
Tests cover every branch in:
  - parse_tool_output
  - process_jobtype_search_result
  - convert_to_llm_messages
  - format_previous_chat_histories

Interface / boundary enumeration:
  Inputs:
    - histories: list[ChatHistory] with roles USER/DEVELOPER/ASSISTANT/TOOL/HANDOFF/REASONING/<unknown>
    - tool output: str (valid JSON, invalid JSON), dict, list (empty, non-dict first, dict first), other
    - jobtypes dict: None, missing "職種" key, valid
    - format_previous_chat_histories: empty list, limit 0, position tool, jobtype tool, greeting tail
  Outputs:
    - (chat_histories dict, all_messages dict) tuples
    - (previous_chat_histories list, no_more_user_message_left bool) tuples
  Side effects: logger calls only (no DB, no network)
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, call, patch

import pytest


pytestmark = pytest.mark.pre_extraction_parity
from domain.entities.chat_history import ChatHistory
from services.chat.history_mapper import (
    POSITION_SEARCH_FAKE_RESULT,
    HistoryMapper,
    _generate_position_search_fake_result,
)
from utils.chat_response import ChatResponseType
from utils.const import MAIN_CHAT_KEY, SESSION_START_MESSAGE
from utils.enum import LLMMessageRole, LocationType, ToolName


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_history(**kwargs) -> ChatHistory:
    defaults = {
        "session_id": "test-session",
        "position_id": None,
        "active_agent": "CareerAdvisor",
        "message_id": "msg-001",
        "role": LLMMessageRole.USER,
        "content": "hello",
        "tool_call_id": None,
        "tool_name": None,
        "tool_input": None,
    }
    defaults.update(kwargs)
    return ChatHistory(**defaults)


# ---------------------------------------------------------------------------
# _generate_position_search_fake_result (module-level helper)
# ---------------------------------------------------------------------------


def test_generate_position_search_fake_result_includes_count():
    result = _generate_position_search_fake_result(3)
    assert "3件" in result


def test_generate_position_search_fake_result_zero():
    result = _generate_position_search_fake_result(0)
    assert "0件" in result


# ---------------------------------------------------------------------------
# parse_tool_output — string input
# ---------------------------------------------------------------------------


def test_parse_tool_output_str_valid_json_dict():
    mapper = HistoryMapper()
    result = mapper.parse_tool_output('{"key": "value"}')
    assert result == {"key": "value"}


def test_parse_tool_output_str_invalid_json_returns_empty():
    mapper = HistoryMapper()
    result = mapper.parse_tool_output("not-json{{{")
    assert result == {}


def test_parse_tool_output_str_valid_json_with_text_key():
    """str → outer dict → inner dict via 'text' key."""
    mapper = HistoryMapper()
    inner = {"AllPositionIds": ["p1"]}
    result = mapper.parse_tool_output(json.dumps({"text": inner}))
    assert result == inner


def test_parse_tool_output_str_valid_json_with_text_key_as_str():
    """str → outer dict → inner 'text' is itself a JSON string."""
    mapper = HistoryMapper()
    inner = {"AllPositionIds": ["p1"]}
    result = mapper.parse_tool_output(json.dumps({"text": json.dumps(inner)}))
    assert result == inner


def test_parse_tool_output_str_with_text_key_that_is_invalid_json():
    """str → outer dict → inner 'text' is a non-JSON string."""
    mapper = HistoryMapper()
    result = mapper.parse_tool_output(json.dumps({"text": "not-json{{{"}))
    assert result == {}


def test_parse_tool_output_str_with_text_key_that_is_non_string_non_dict():
    """str → outer dict → inner 'text' is an int (not str, not dict)."""
    mapper = HistoryMapper()
    result = mapper.parse_tool_output(json.dumps({"text": 42}))
    assert result == {}


# ---------------------------------------------------------------------------
# parse_tool_output — dict input
# ---------------------------------------------------------------------------


def test_parse_tool_output_dict_no_text_key():
    mapper = HistoryMapper()
    result = mapper.parse_tool_output({"key": "val"})
    assert result == {"key": "val"}


def test_parse_tool_output_dict_with_text_key_dict():
    mapper = HistoryMapper()
    inner = {"nested": "data"}
    result = mapper.parse_tool_output({"text": inner})
    assert result == inner


# ---------------------------------------------------------------------------
# parse_tool_output — list input
# ---------------------------------------------------------------------------


def test_parse_tool_output_list_empty_returns_empty():
    mapper = HistoryMapper()
    result = mapper.parse_tool_output([])
    assert result == {}


def test_parse_tool_output_list_first_item_not_dict_returns_empty():
    mapper = HistoryMapper()
    result = mapper.parse_tool_output(["not-a-dict"])
    assert result == {}


def test_parse_tool_output_list_first_item_dict_with_text_str():
    mapper = HistoryMapper()
    inner = {"Jobtypes": []}
    result = mapper.parse_tool_output([{"text": json.dumps(inner)}])
    assert result == inner


def test_parse_tool_output_list_first_item_dict_without_text_key():
    mapper = HistoryMapper()
    result = mapper.parse_tool_output([{"direct": "value"}])
    assert result == {"direct": "value"}


# ---------------------------------------------------------------------------
# parse_tool_output — other types
# ---------------------------------------------------------------------------


def test_parse_tool_output_int_returns_empty():
    mapper = HistoryMapper()
    result = mapper.parse_tool_output(42)
    assert result == {}


def test_parse_tool_output_none_returns_empty():
    mapper = HistoryMapper()
    result = mapper.parse_tool_output(None)
    assert result == {}


# ---------------------------------------------------------------------------
# process_jobtype_search_result
# ---------------------------------------------------------------------------


def test_process_jobtype_search_result_none_input():
    mapper = HistoryMapper()
    assert mapper.process_jobtype_search_result("id", "name", "{}", None) is None


def test_process_jobtype_search_result_empty_dict():
    mapper = HistoryMapper()
    assert mapper.process_jobtype_search_result("id", "name", "{}", {}) is None


def test_process_jobtype_search_result_no_jobtypes_key():
    mapper = HistoryMapper()
    result = mapper.process_jobtype_search_result("id", "name", "{}", {"other_key": []})
    assert result is None


def test_process_jobtype_search_result_empty_jobtypes_list():
    mapper = HistoryMapper()
    result = mapper.process_jobtype_search_result("id", "name", "{}", {"職種": []})
    assert result is None


def test_process_jobtype_search_result_normal_with_keyword():
    mapper = HistoryMapper()
    result = mapper.process_jobtype_search_result(
        "call-001",
        "search_occupations_by_sentence",
        '{"Keyword": "engineer"}',
        {
            "職種": [{"職種名": "SE", "職種説明": "システムエンジニア"}],
            "Keyword": "engineer",
        },
    )
    assert result is not None
    assert result["Keyword"] == "engineer"
    assert result["Jobtypes"] == [{"ID": "SE", "Name": "システムエンジニア"}]
    assert result["ToolCall"]["ID"] == "call-001"
    assert result["ToolCall"]["Name"] == "search_occupations_by_sentence"


def test_process_jobtype_search_result_uses_fallback_keyword_key():
    """Keyword not found → fall back to 検索キーワード."""
    mapper = HistoryMapper()
    result = mapper.process_jobtype_search_result(
        "call-002",
        "search_occupations_by_nature",
        "{}",
        {
            "職種": [{"職種名": "PM", "職種説明": "プロジェクトマネージャー"}],
            "検索キーワード": "manager",
        },
    )
    assert result is not None
    assert result["Keyword"] == "manager"


def test_process_jobtype_search_result_keyword_not_string():
    """Keyword is non-string value → Keyword field is ""."""
    mapper = HistoryMapper()
    result = mapper.process_jobtype_search_result(
        "call-003",
        "search_occupations_by_sentence",
        "{}",
        {
            "職種": [{"職種名": "A", "職種説明": "B"}],
            "Keyword": 123,
        },
    )
    assert result is not None
    assert result["Keyword"] == ""


# ---------------------------------------------------------------------------
# convert_to_llm_messages — role routing
# ---------------------------------------------------------------------------


def test_convert_to_llm_messages_empty_list():
    mapper = HistoryMapper()
    chat_hists, all_msgs = mapper.convert_to_llm_messages([])
    assert chat_hists == {}
    assert all_msgs == {}


def test_convert_to_llm_messages_user_role():
    mapper = HistoryMapper()
    h = _make_history(role=LLMMessageRole.USER, content="hello")
    _, messages = mapper.convert_to_llm_messages([h])
    assert messages[MAIN_CHAT_KEY][0]["role"] == LLMMessageRole.USER
    assert messages[MAIN_CHAT_KEY][0]["content"] == "hello"
    assert messages[MAIN_CHAT_KEY][0]["type"] == "message"


def test_convert_to_llm_messages_developer_role():
    mapper = HistoryMapper()
    h = _make_history(role=LLMMessageRole.DEVELOPER, content="sys msg")
    _, messages = mapper.convert_to_llm_messages([h])
    assert messages[MAIN_CHAT_KEY][0]["role"] == LLMMessageRole.DEVELOPER
    assert messages[MAIN_CHAT_KEY][0]["content"] == "sys msg"


def test_convert_to_llm_messages_assistant_role():
    mapper = HistoryMapper()
    h = _make_history(role=LLMMessageRole.ASSISTANT, content="response text")
    _, messages = mapper.convert_to_llm_messages([h])
    msg = messages[MAIN_CHAT_KEY][0]
    assert msg["role"] == LLMMessageRole.ASSISTANT
    assert isinstance(msg["content"], list)
    assert msg["content"][0]["type"] == "output_text"
    assert msg["content"][0]["text"] == "response text"


def test_convert_to_llm_messages_reasoning_role_is_silently_skipped():
    mapper = HistoryMapper()
    h = _make_history(role=LLMMessageRole.REASONING, content="reasoning text")
    _, messages = mapper.convert_to_llm_messages([h])
    # REASONING role は pass なので messages リストにエントリが追加されない
    assert messages[MAIN_CHAT_KEY] == []


def test_convert_to_llm_messages_unknown_role_logs_error():
    mapper = HistoryMapper()
    h = _make_history(role="UNKNOWN_ROLE", content="bad role")
    with patch.object(mapper, "_logger") as mock_logger:
        _, messages = mapper.convert_to_llm_messages([h])
    mock_logger.error.assert_called_once()
    assert messages[MAIN_CHAT_KEY] == []


def test_convert_to_llm_messages_tool_role_basic():
    """TOOL role → function_call + function_call_output."""
    mapper = HistoryMapper()
    h = _make_history(
        role=LLMMessageRole.TOOL,
        content='{"result": "data"}',
        tool_call_id="call-001",
        tool_name="save_user_preference",
        tool_input={"key": "val"},
    )
    _, messages = mapper.convert_to_llm_messages([h])
    msgs = messages[MAIN_CHAT_KEY]
    assert len(msgs) == 2
    assert msgs[0]["type"] == "function_call"
    assert msgs[0]["call_id"] == "call-001"
    assert msgs[1]["type"] == "function_call_output"
    assert msgs[1]["output"] == '{"result": "data"}'


def test_convert_to_llm_messages_tool_role_empty_output():
    """TOOL role with empty content → fallback message."""
    mapper = HistoryMapper()
    h = _make_history(
        role=LLMMessageRole.TOOL,
        content="",
        tool_call_id="call-empty",
        tool_name="some_tool",
        tool_input={},
    )
    _, messages = mapper.convert_to_llm_messages([h])
    msgs = messages[MAIN_CHAT_KEY]
    assert msgs[1]["output"] == "ツール実行結果がまだありません。"


def test_convert_to_llm_messages_handoff_role():
    """HANDOFF role → treated like TOOL → function_call + function_call_output."""
    mapper = HistoryMapper()
    h = _make_history(
        role=LLMMessageRole.HANDOFF,
        content='{"result": "handoff"}',
        tool_call_id="call-handoff",
        tool_name="transfer_to_position_guide",
        tool_input={"target": "position_guide"},
    )
    _, messages = mapper.convert_to_llm_messages([h])
    msgs = messages[MAIN_CHAT_KEY]
    assert msgs[0]["type"] == "function_call"
    assert msgs[1]["type"] == "function_call_output"


def test_convert_to_llm_messages_position_search_tool_fake_result():
    """Position search tool → fake result message instead of real output."""
    mapper = HistoryMapper()
    content = json.dumps({"AllPositionIds": ["p1", "p2"]})
    h = _make_history(
        role=LLMMessageRole.TOOL,
        content=content,
        tool_call_id="call-pos",
        tool_name="search_job_postings",
        tool_input={},
    )
    _, messages = mapper.convert_to_llm_messages([h])
    output = messages[MAIN_CHAT_KEY][1]["output"]
    assert "2件" in output


def test_convert_to_llm_messages_position_search_tool_parse_failure_fallback():
    """Position search tool with unparseable content → count=0 fake result.

    parse_tool_output("bad-json") returns {} rather than raising, so the
    except branch (POSITION_SEARCH_FAKE_RESULT) is not triggered.
    Instead, AllPositionIds is missing → count=0 → _generate_position_search_fake_result(0).
    """
    mapper = HistoryMapper()
    h = _make_history(
        role=LLMMessageRole.TOOL,
        content="bad-json",
        tool_call_id="call-pos",
        tool_name="search_job_postings",
        tool_input={},
    )
    _, messages = mapper.convert_to_llm_messages([h])
    output = messages[MAIN_CHAT_KEY][1]["output"]
    assert output == _generate_position_search_fake_result(0)


def test_convert_to_llm_messages_position_search_tool_exception_in_parse_tool_output():
    """Position search tool where parse_tool_output raises → POSITION_SEARCH_FAKE_RESULT.

    The except branch at lines 152-157 in history_mapper.py is only reachable when
    parse_tool_output itself raises (not when it returns {}). We patch it to raise.
    """
    mapper = HistoryMapper()
    h = _make_history(
        role=LLMMessageRole.TOOL,
        content='{"AllPositionIds": ["p1"]}',
        tool_call_id="call-pos-exc",
        tool_name="search_job_postings",
        tool_input={},
    )
    with patch.object(mapper, "parse_tool_output", side_effect=RuntimeError("forced")):
        _, messages = mapper.convert_to_llm_messages([h])
    output = messages[MAIN_CHAT_KEY][1]["output"]
    assert output == POSITION_SEARCH_FAKE_RESULT


def test_convert_to_llm_messages_jobtype_search_tool():
    """Jobtype search tool →職種一覧 format."""
    mapper = HistoryMapper()
    content = json.dumps(
        {
            "職種": [{"職種名": "SE", "職種説明": "エンジニア"}],
            "Keyword": "engineer",
        }
    )
    h = _make_history(
        role=LLMMessageRole.TOOL,
        content=content,
        tool_call_id="call-jt",
        tool_name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
        tool_input={"Keyword": "engineer"},
    )
    _, messages = mapper.convert_to_llm_messages([h])
    output = messages[MAIN_CHAT_KEY][1]["output"]
    assert "職種一覧" in output
    assert "SE" in output


def test_convert_to_llm_messages_jobtype_search_tool_none_result():
    """Jobtype search tool where process_jobtype_search_result returns None → empty list."""
    mapper = HistoryMapper()
    content = json.dumps({})  # no "職種" key → None result
    h = _make_history(
        role=LLMMessageRole.TOOL,
        content=content,
        tool_call_id="call-jt2",
        tool_name=ToolName.JOBTYPE_SEARCH_BY_NATURE,
        tool_input={},
    )
    _, messages = mapper.convert_to_llm_messages([h])
    output = messages[MAIN_CHAT_KEY][1]["output"]
    assert "[]" in output


def test_convert_to_llm_messages_jobtype_search_exception_fallback():
    """Jobtype search tool that raises an exception → "[]"."""
    mapper = HistoryMapper()
    h = _make_history(
        role=LLMMessageRole.TOOL,
        content="bad-json-for-jobtype",
        tool_call_id="call-jt3",
        tool_name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
        tool_input={},
    )
    # Patch process_jobtype_search_result to raise
    with patch.object(
        mapper, "process_jobtype_search_result", side_effect=RuntimeError("err")
    ):
        _, messages = mapper.convert_to_llm_messages([h])
    output = messages[MAIN_CHAT_KEY][1]["output"]
    assert "[]" in output


def test_convert_to_llm_messages_position_id_history_key():
    """History with position_id → history_key = str(position_id)."""
    mapper = HistoryMapper()
    h = _make_history(
        position_id=42,
        role=LLMMessageRole.USER,
        content="position chat msg",
    )
    _, messages = mapper.convert_to_llm_messages([h])
    assert "42" in messages
    assert MAIN_CHAT_KEY not in messages


def test_convert_to_llm_messages_position_id_callback_called():
    """position_id truthy AND callback provided → callback is called with history_key."""
    mapper = HistoryMapper()
    callback = MagicMock()
    h = _make_history(
        position_id=42,
        role=LLMMessageRole.USER,
        content="position chat",
    )
    mapper.convert_to_llm_messages(
        [h], position_id="pos-42", create_position_agent_callback=callback
    )
    # Callback receives history_key = str(history.position_id), not the outer position_id.
    # This ensures the agent is created for the position the history entry belongs to.
    callback.assert_called_once_with("42")


def test_convert_to_llm_messages_no_callback_when_none():
    """position_id truthy but callback is None → no error."""
    mapper = HistoryMapper()
    h = _make_history(
        position_id=42,
        role=LLMMessageRole.USER,
        content="position chat",
    )
    # Should not raise
    mapper.convert_to_llm_messages([h], create_position_agent_callback=None)


def test_convert_to_llm_messages_callback_not_called_when_no_position_id():
    """history.position_id is None → callback NOT called even if provided."""
    mapper = HistoryMapper()
    callback = MagicMock()
    h = _make_history(
        position_id=None,
        role=LLMMessageRole.USER,
        content="main chat",
    )
    mapper.convert_to_llm_messages([h], create_position_agent_callback=callback)
    callback.assert_not_called()


# ---------------------------------------------------------------------------
# format_previous_chat_histories — basic paths
# ---------------------------------------------------------------------------


def test_format_previous_chat_histories_empty_list():
    mapper = HistoryMapper()
    result, no_more = mapper.format_previous_chat_histories([], 5)
    assert result == []
    assert no_more is True


def test_format_previous_chat_histories_single_user_assistant_pair():
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="question"),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="answer"),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 5)
    assert len(result) >= 1
    user_entries = [e for e in result if e["Role"] == LLMMessageRole.USER]
    assert any(
        e["MessageID"] == "u1" and e["Message"] == "question" for e in user_entries
    )
    assistant_entries = [e for e in result if e["Role"] == LLMMessageRole.ASSISTANT]
    assert any(
        e["MessageID"] == "a1" and e["Message"] == "answer" for e in assistant_entries
    )


def test_format_previous_chat_histories_no_user_messages():
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="hello"),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 5)
    assert result == []
    assert no_more is True


def test_format_previous_chat_histories_limit_zero_returns_empty():
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="hi"),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="yo"),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 0)
    assert result == []
    assert no_more is False


def test_format_previous_chat_histories_limit_enforced():
    """With limit=1 and 2 user turns, only one turn is returned."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q1"),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r1"),
        _make_history(message_id="u2", role=LLMMessageRole.USER, content="q2"),
        _make_history(message_id="a2", role=LLMMessageRole.ASSISTANT, content="r2"),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 1)
    user_entries = [e for e in result if e["Role"] == LLMMessageRole.USER]
    assert len(user_entries) == 1
    assert no_more is False


# ---------------------------------------------------------------------------
# format_previous_chat_histories — start_workflow（応答ありフラグ）
# ---------------------------------------------------------------------------


def _make_start_workflow_history(
    message_id: str = "sw1",
    content: str = '{"WorkflowID": "wf-1"}',
) -> ChatHistory:
    return _make_history(
        message_id=message_id,
        role=LLMMessageRole.TOOL,
        content=content,
        tool_call_id="call-sw1",
        tool_name=ToolName.START_WORKFLOW.value,
        tool_input={"WorkflowID": "wf-1"},
    )


def test_format_previous_chat_histories_start_workflow_shows_user_message():
    """ユーザー発言の後が start_workflow のみでも、ユーザーメッセージは表示される。"""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="診断したい"),
        _make_start_workflow_history(),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 5)

    assert result == [
        {
            "Role": LLMMessageRole.USER,
            "Type": ChatResponseType.MESSAGE,
            "MessageID": "u1",
            "Message": "診断したい",
        }
    ]
    assert no_more is True


def test_format_previous_chat_histories_start_workflow_mid_history_keeps_all_users():
    """[U1, SW, U2, A2] のような連続ユーザーメッセージがすべて表示される。"""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q1"),
        _make_start_workflow_history(),
        _make_history(message_id="u2", role=LLMMessageRole.USER, content="q2"),
        _make_history(message_id="a2", role=LLMMessageRole.ASSISTANT, content="r2"),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 5)

    # 新→旧順: [A2, U2, U1]
    assert [e["MessageID"] for e in result] == ["a2", "u2", "u1"]
    assert no_more is True


def test_format_previous_chat_histories_start_workflow_no_display_entry():
    """start_workflow レコード自体の表示要素は生成されない（フラグのみ）。"""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q1"),
        _make_start_workflow_history(),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r1"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)

    assert [e["MessageID"] for e in result] == ["a1", "u1"]
    assert all(e["Role"] != LLMMessageRole.TOOL for e in result)


def test_format_previous_chat_histories_start_workflow_empty_content_keeps_user_hidden():
    """content が空の start_workflow はフラグにならず、従来どおりユーザーメッセージは非表示。"""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q1"),
        _make_start_workflow_history(content=""),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 5)

    assert result == []
    assert no_more is True


# ---------------------------------------------------------------------------
# format_previous_chat_histories — SESSION_START_MESSAGE
# ---------------------------------------------------------------------------


def test_format_previous_chat_histories_session_start_message_dev():
    """SESSION_START_MESSAGE as DEVELOPER is treated as user message origin but not appended."""
    mapper = HistoryMapper()
    histories = [
        _make_history(
            message_id="start-dev",
            role=LLMMessageRole.DEVELOPER,
            content=SESSION_START_MESSAGE,
        ),
        _make_history(
            message_id="a1",
            role=LLMMessageRole.ASSISTANT,
            content="greeting reply",
        ),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 5)
    # SESSION_START_MESSAGE DEVELOPER triggers greeting assistant tail logic
    # but the user message itself should NOT be added to result
    user_entries = [e for e in result if e["Role"] == LLMMessageRole.USER]
    assert len(user_entries) == 0
    assert no_more is True


# ---------------------------------------------------------------------------
# format_previous_chat_histories — TOOL role
# ---------------------------------------------------------------------------


def test_format_previous_chat_histories_tool_empty_content_skipped():
    """TOOL history with empty content is skipped."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content="",
            tool_call_id="c1",
            tool_name="some_tool",
            tool_input={},
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    tool_entries = [
        e for e in result if e.get("Type") == ChatResponseType.POSITION_SEARCH_LINK
    ]
    assert len(tool_entries) == 0


def test_format_previous_chat_histories_tool_unknown_name_skipped():
    """TOOL with unknown tool name → no TOOL entry in result."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content='{"data": "ignored"}',
            tool_call_id="c1",
            tool_name="some_unknown_tool",
            tool_input={},
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    tool_entries = [
        e for e in result if e.get("Type") == ChatResponseType.POSITION_SEARCH_LINK
    ]
    assert len(tool_entries) == 0


def test_format_previous_chat_histories_position_search_with_message_key_skipped():
    """Position search TOOL with 'Message' key in parsed output → skip (failure case)."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"Message": "tool failed"}),
            tool_call_id="c1",
            tool_name="search_job_postings",
            tool_input={"Salary": 700, "Locations": []},
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    pos_entries = [
        e for e in result if e.get("Type") == ChatResponseType.POSITION_SEARCH_LINK
    ]
    assert len(pos_entries) == 0


def test_format_previous_chat_histories_position_search_missing_required_fields():
    """Position search TOOL missing salary → skipped with error log."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"AllPositionIds": ["p1"]}),
            tool_call_id="c1",
            tool_name="search_job_postings",
            tool_input={},  # missing Salary and Locations
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    pos_entries = [
        e for e in result if e.get("Type") == ChatResponseType.POSITION_SEARCH_LINK
    ]
    assert len(pos_entries) == 0


def test_format_previous_chat_histories_position_search_with_all_location_types():
    """Position search with RESIDENCE, FULL_REMOTE, WORK_LOCATION, unknown."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"AllPositionIds": ["p1"]}),
            tool_call_id="c1",
            tool_name="search_job_postings",
            tool_input={
                "Salary": 700,
                "Locations": [
                    {
                        "LocationType": LocationType.RESIDENCE,
                        "PrefectureName": "東京都",
                        "CityName": "千代田区",
                    },
                    {
                        "LocationType": LocationType.FULL_REMOTE,
                        "PrefectureName": "",
                        "CityName": "",
                    },
                    {
                        "LocationType": LocationType.WORK_LOCATION,
                        "PrefectureName": "神奈川県",
                        "CityName": "横浜市",
                    },
                    {
                        "LocationType": "mystery-type",
                        "PrefectureName": "Unknown",
                        "CityName": "X",
                    },
                ],
                "PositionKeyword": "backend",
                "JobtypeNames": ["SE"],
            },
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    pos_entries = [
        e for e in result if e.get("Type") == ChatResponseType.POSITION_SEARCH_LINK
    ]
    assert len(pos_entries) == 1
    msg = pos_entries[0]["Message"]
    assert msg["Residence"] == "東京都千代田区"
    assert msg["IsFullyRemoteWork"] is True
    assert "神奈川県横浜市" in msg["WorkLocations"]


def test_format_previous_chat_histories_position_search_none_keyword_becomes_empty_string():
    """PositionKeyword=None should be normalized to empty string."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"AllPositionIds": ["p1"]}),
            tool_call_id="c1",
            tool_name="search_job_postings",
            tool_input={
                "Salary": 700,
                "Locations": [
                    {
                        "LocationType": LocationType.WORK_LOCATION,
                        "PrefectureName": "東京都",
                        "CityName": "港区",
                    }
                ],
                "PositionKeyword": None,
            },
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]

    result, _ = mapper.format_previous_chat_histories(histories, 5)
    pos_entries = [
        e for e in result if e.get("Type") == ChatResponseType.POSITION_SEARCH_LINK
    ]
    assert len(pos_entries) == 1
    assert pos_entries[0]["Message"]["PositionKeyword"] == ""


def test_format_previous_chat_histories_position_search_fully_remote_from_tool_input():
    """FullyRemoteWork=True in tool_input sets is_full_remote initially.

    The code reads FullyRemoteWork from tool_input before iterating over Locations.
    Locations must be non-empty to pass the validation guard (not locations → continue).
    A single WORK_LOCATION entry satisfies the guard while FullyRemoteWork=True in
    tool_input provides the initial True value read at line 387.
    """
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"AllPositionIds": ["p1"]}),
            tool_call_id="c1",
            tool_name="search_job_postings",
            tool_input={
                "Salary": 700,
                "Locations": [
                    {
                        "LocationType": LocationType.WORK_LOCATION,
                        "PrefectureName": "東京都",
                        "CityName": "港区",
                    }
                ],
                "FullyRemoteWork": True,
            },
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    pos_entries = [
        e for e in result if e.get("Type") == ChatResponseType.POSITION_SEARCH_LINK
    ]
    assert len(pos_entries) == 1
    assert pos_entries[0]["Message"]["IsFullyRemoteWork"] is True
    assert pos_entries[0]["Message"]["WorkLocations"] == ["東京都港区"]


# ---------------------------------------------------------------------------
# format_previous_chat_histories — JOBTYPE tool
# ---------------------------------------------------------------------------


def test_format_previous_chat_histories_jobtype_search_with_selection():
    """Jobtype search TOOL with selected jobtype developer message."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content=json.dumps(
                {
                    "職種": [{"職種名": "SE", "職種説明": "システムエンジニア"}],
                    "Keyword": "engineer",
                }
            ),
            tool_call_id="c1",
            tool_name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
            tool_input={"Keyword": "engineer"},
        ),
        _make_history(
            message_id="dev1",
            role=LLMMessageRole.DEVELOPER,
            content="ユーザーが職種「システムエンジニア」を選択しました。",
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    jt_entries = [
        e for e in result if e.get("Type") == ChatResponseType.JOBTYPE_SEARCH_RESULT
    ]
    assert len(jt_entries) == 1
    assert jt_entries[0]["Message"]["SelectedJobtypeName"] == "システムエンジニア"


def test_format_previous_chat_histories_jobtype_search_no_selection():
    """Jobtype search TOOL with no matching developer selection message."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content=json.dumps(
                {
                    "職種": [{"職種名": "SE", "職種説明": "SE"}],
                    "Keyword": "engineer",
                }
            ),
            tool_call_id="c1",
            tool_name=ToolName.JOBTYPE_SEARCH_BY_NATURE,
            tool_input={"Keyword": "engineer"},
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    jt_entries = [
        e for e in result if e.get("Type") == ChatResponseType.JOBTYPE_SEARCH_RESULT
    ]
    assert len(jt_entries) == 1
    assert jt_entries[0]["Message"]["SelectedJobtypeName"] is None


def test_format_previous_chat_histories_jobtype_search_none_result_skipped():
    """Jobtype search TOOL where process_jobtype_search_result returns None → skipped."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content=json.dumps({}),  # no 職種 key → None result
            tool_call_id="c1",
            tool_name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
            tool_input={},
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    jt_entries = [
        e for e in result if e.get("Type") == ChatResponseType.JOBTYPE_SEARCH_RESULT
    ]
    assert len(jt_entries) == 0


def test_format_previous_chat_histories_jobtype_search_skips_dev_with_empty_content():
    """Developer message with empty content is skipped when searching for selected jobtype."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="t1",
            role=LLMMessageRole.TOOL,
            content=json.dumps(
                {
                    "職種": [{"職種名": "SE", "職種説明": "SE"}],
                    "Keyword": "engineer",
                }
            ),
            tool_call_id="c1",
            tool_name=ToolName.JOBTYPE_SEARCH_BY_KEYWORDS,
            tool_input={},
        ),
        _make_history(
            message_id="dev-empty",
            role=LLMMessageRole.DEVELOPER,
            content="",  # empty content → skip
        ),
        _make_history(
            message_id="dev-unmatched",
            role=LLMMessageRole.DEVELOPER,
            content="ユーザーはまだ選んでいません。",  # no match
        ),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    jt_entries = [
        e for e in result if e.get("Type") == ChatResponseType.JOBTYPE_SEARCH_RESULT
    ]
    assert len(jt_entries) == 1
    assert jt_entries[0]["Message"]["SelectedJobtypeName"] is None


# ---------------------------------------------------------------------------
# format_previous_chat_histories — ASSISTANT deduplication
# ---------------------------------------------------------------------------


def test_format_previous_chat_histories_assistant_duplicate_deduplication():
    """Second ASSISTANT history in same turn is skipped."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(
            message_id="a1", role=LLMMessageRole.ASSISTANT, content="first reply"
        ),
        _make_history(
            message_id="a2", role=LLMMessageRole.ASSISTANT, content="duplicate"
        ),
    ]
    result, _ = mapper.format_previous_chat_histories(histories, 5)
    asst_entries = [e for e in result if e["Role"] == LLMMessageRole.ASSISTANT]
    assert len(asst_entries) == 1
    assert asst_entries[0]["MessageID"] == "a1"


# ---------------------------------------------------------------------------
# format_previous_chat_histories — greeting tail
# ---------------------------------------------------------------------------


def test_format_previous_chat_histories_greeting_tail_appended():
    """After all user turns exhausted, greeting assistant tail is appended."""
    mapper = HistoryMapper()
    histories = [
        _make_history(
            message_id="start-dev",
            role=LLMMessageRole.DEVELOPER,
            content=SESSION_START_MESSAGE,
        ),
        _make_history(
            message_id="greet-asst",
            role=LLMMessageRole.ASSISTANT,
            content="ようこそ！",
        ),
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 1)
    assert no_more is True
    greet_entries = [
        e
        for e in result
        if e["Role"] == LLMMessageRole.ASSISTANT and e["MessageID"] == "greet-asst"
    ]
    assert len(greet_entries) == 1


def test_format_previous_chat_histories_no_more_left_without_greeting():
    """When no more user messages and no greeting tail condition, no_more=True."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r"),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 5)
    assert no_more is True


def test_format_previous_chat_histories_no_more_false_when_more_exist():
    """When limit reached before all users exhausted, no_more=False."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q1"),
        _make_history(message_id="a1", role=LLMMessageRole.ASSISTANT, content="r1"),
        _make_history(message_id="u2", role=LLMMessageRole.USER, content="q2"),
        _make_history(message_id="a2", role=LLMMessageRole.ASSISTANT, content="r2"),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 1)
    assert no_more is False


# ---------------------------------------------------------------------------
# format_previous_chat_histories — llm_responses empty (no assistant in turn)
# ---------------------------------------------------------------------------


def test_format_previous_chat_histories_user_with_no_llm_response():
    """User message followed by nothing → llm_responses empty → not counted."""
    mapper = HistoryMapper()
    histories = [
        _make_history(message_id="u1", role=LLMMessageRole.USER, content="q"),
    ]
    result, no_more = mapper.format_previous_chat_histories(histories, 5)
    assert result == []
    assert no_more is True
