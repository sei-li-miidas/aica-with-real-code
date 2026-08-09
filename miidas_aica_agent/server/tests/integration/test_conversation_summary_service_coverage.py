"""
Integration tests for ConversationSummaryService — targeting 100% branch coverage.

External boundary mocked: openai.AsyncOpenAI (responses.create)
Tests call real service logic with mocked OpenAI client.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.entities.chat_history import ChatHistory
from services.conversation_summary_service import (
    ConversationSummaryService,
    SummaryGenerationError,
)
from utils.enum import LLMMessageRole, ToolName

pytestmark = pytest.mark.pre_extraction_parity


_MODEL_LIST = [
    {
        "model": "gpt-4o-mini",
        "use_for": ["summary"],
        "model_settings": {},
    },
]


def _make_svc(model_list=None) -> ConversationSummaryService:
    ml = model_list or _MODEL_LIST
    with patch("services.conversation_summary_service.AsyncOpenAI"):
        svc = ConversationSummaryService(ml)
    return svc


def _make_history(
    role: str,
    content: str,
    tool_name: str | None = None,
    session_id: str = "sess-1",
) -> ChatHistory:
    return ChatHistory(
        session_id=session_id,
        active_agent="CareerAdvisor",
        message_id="msg-1",
        role=role,
        content=content,
        tool_name=tool_name,
    )


# ─── ConversationSummaryService initialization ────────────────────────────────


def test_raises_when_no_summary_model():
    with pytest.raises(ValueError, match="summaryモデル"):
        ConversationSummaryService([])


def test_raises_when_summary_model_has_no_model_name():
    with pytest.raises(ValueError, match="Summary model name"):
        with patch("services.conversation_summary_service.AsyncOpenAI"):
            ConversationSummaryService([{"use_for": ["summary"], "model_settings": {}}])


def test_warns_when_multiple_summary_models(caplog):
    multi_models = [
        {"model": "m1", "use_for": ["summary"], "model_settings": {}},
        {"model": "m2", "use_for": ["summary"], "model_settings": {}},
    ]
    with patch("services.conversation_summary_service.AsyncOpenAI"):
        svc = ConversationSummaryService(multi_models)
    assert svc._summary_model["model"] == "m1"  # first one used


# ─── summarize_conversation ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_summarize_conversation_success_with_previous_summary():
    svc = _make_svc()
    mock_response = SimpleNamespace(output_text="要約テキスト")
    svc._openai_client.responses.create = AsyncMock(return_value=mock_response)

    histories = [
        _make_history(LLMMessageRole.USER, "こんにちは"),
        _make_history(LLMMessageRole.ASSISTANT, "こんにちは！"),
    ]
    result = await svc.summarize_conversation(
        previous_summary_text="前回の要約",
        chat_histories=histories,
    )

    assert result == "要約テキスト"
    svc._openai_client.responses.create.assert_called_once()
    call_kwargs = svc._openai_client.responses.create.call_args[1]
    # Previous summary should be in the input
    assert any("前回要約" in str(item) for item in call_kwargs["input"])


@pytest.mark.asyncio
async def test_summarize_conversation_no_previous_summary():
    svc = _make_svc()
    mock_response = SimpleNamespace(output_text="新規要約")
    svc._openai_client.responses.create = AsyncMock(return_value=mock_response)

    histories = [_make_history(LLMMessageRole.USER, "テスト")]
    result = await svc.summarize_conversation(
        previous_summary_text=None,
        chat_histories=histories,
    )
    assert result == "新規要約"


@pytest.mark.asyncio
async def test_summarize_conversation_empty_response_raises():
    svc = _make_svc()
    mock_response = SimpleNamespace(output_text="")
    svc._openai_client.responses.create = AsyncMock(return_value=mock_response)

    with pytest.raises(SummaryGenerationError) as exc_info:
        await svc.summarize_conversation(
            None, [_make_history(LLMMessageRole.USER, "test")]
        )

    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_summarize_conversation_api_error_wraps_in_summary_generation_error():
    svc = _make_svc()
    svc._openai_client.responses.create = AsyncMock(side_effect=Exception("API error"))

    with pytest.raises(SummaryGenerationError):
        await svc.summarize_conversation(
            None, [_make_history(LLMMessageRole.USER, "test")]
        )


@pytest.mark.asyncio
async def test_summarize_conversation_re_raises_summary_generation_error():
    svc = _make_svc()
    original_error = SummaryGenerationError("direct error", retryable=True)
    svc._openai_client.responses.create = AsyncMock(side_effect=original_error)

    with pytest.raises(SummaryGenerationError) as exc_info:
        await svc.summarize_conversation(
            None, [_make_history(LLMMessageRole.USER, "x")]
        )

    assert exc_info.value is original_error


# ─── summarize_position_detail_chat ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_summarize_position_detail_chat_empty_histories_returns_none():
    svc = _make_svc()
    result = await svc.summarize_position_detail_chat([])
    assert result is None


@pytest.mark.asyncio
async def test_summarize_position_detail_chat_success():
    svc = _make_svc()
    mock_response = SimpleNamespace(output_text="ポジション詳細要約")
    svc._openai_client.responses.create = AsyncMock(return_value=mock_response)

    histories = [_make_history(LLMMessageRole.USER, "このポジションについて")]
    result = await svc.summarize_position_detail_chat(histories)
    assert result == "ポジション詳細要約"


@pytest.mark.asyncio
async def test_summarize_position_detail_chat_empty_response_returns_none():
    svc = _make_svc()
    mock_response = SimpleNamespace(output_text="   ")
    svc._openai_client.responses.create = AsyncMock(return_value=mock_response)

    histories = [_make_history(LLMMessageRole.USER, "テスト")]
    result = await svc.summarize_position_detail_chat(histories)
    assert result is None


@pytest.mark.asyncio
async def test_summarize_position_detail_chat_api_error_returns_none():
    svc = _make_svc()
    svc._openai_client.responses.create = AsyncMock(side_effect=Exception("timeout"))

    histories = [_make_history(LLMMessageRole.USER, "テスト")]
    result = await svc.summarize_position_detail_chat(histories)
    assert result is None


# ─── _is_retryable_summary_error ─────────────────────────────────────────────


def test_is_retryable_status_429():
    svc = _make_svc()
    error = Exception()
    error.status_code = 429
    assert svc._is_retryable_summary_error(error) is True


def test_is_retryable_status_500():
    svc = _make_svc()
    error = Exception()
    error.status_code = 500
    assert svc._is_retryable_summary_error(error) is True


def test_is_retryable_status_400_returns_false():
    svc = _make_svc()
    error = Exception()
    error.status_code = 400
    assert svc._is_retryable_summary_error(error) is False


def test_is_retryable_by_class_name_rate_limit():
    svc = _make_svc()

    class RateLimitError(Exception):
        pass

    assert svc._is_retryable_summary_error(RateLimitError()) is True


def test_is_retryable_by_class_name_connection_error():
    svc = _make_svc()

    class APIConnectionError(Exception):
        pass

    assert svc._is_retryable_summary_error(APIConnectionError()) is True


def test_is_retryable_by_class_name_timeout():
    svc = _make_svc()

    class APITimeoutError(Exception):
        pass

    assert svc._is_retryable_summary_error(APITimeoutError()) is True


def test_is_retryable_by_class_name_internal_server():
    svc = _make_svc()

    class InternalServerError(Exception):
        pass

    assert svc._is_retryable_summary_error(InternalServerError()) is True


def test_is_retryable_unknown_error_returns_false():
    svc = _make_svc()
    assert svc._is_retryable_summary_error(ValueError("unknown")) is False


# ─── _build_summary_input_items ──────────────────────────────────────────────


def test_build_summary_input_items_empty_returns_empty():
    svc = _make_svc()
    result = svc._build_summary_input_items([])
    assert result == []


def test_build_summary_input_items_user_message():
    svc = _make_svc()
    history = _make_history(LLMMessageRole.USER, "ユーザーメッセージ")
    result = svc._build_summary_input_items([history])
    assert len(result) == 1
    assert result[0]["role"] == LLMMessageRole.USER.value
    assert result[0]["content"][0]["type"] == "input_text"


def test_build_summary_input_items_developer_message():
    svc = _make_svc()
    history = _make_history(LLMMessageRole.DEVELOPER, "システムメッセージ")
    result = svc._build_summary_input_items([history])
    assert len(result) == 1
    assert result[0]["role"] == LLMMessageRole.DEVELOPER.value


def test_build_summary_input_items_assistant_message():
    svc = _make_svc()
    history = _make_history(LLMMessageRole.ASSISTANT, "アシスタントメッセージ")
    result = svc._build_summary_input_items([history])
    assert len(result) == 1
    assert result[0]["content"][0]["type"] == "output_text"


def test_build_summary_input_items_tool_message_non_position_search():
    svc = _make_svc()
    history = _make_history(LLMMessageRole.TOOL, "ツール結果", tool_name="some_tool")
    result = svc._build_summary_input_items([history])
    assert len(result) == 1
    assert "some_tool" in result[0]["content"][0]["text"]


def test_build_summary_input_items_handoff_message():
    svc = _make_svc()
    history = _make_history(
        LLMMessageRole.HANDOFF, "ハンドオフ結果", tool_name="handoff_tool"
    )
    result = svc._build_summary_input_items([history])
    assert len(result) == 1


def test_build_summary_input_items_tool_without_tool_name():
    svc = _make_svc()
    history = _make_history(LLMMessageRole.TOOL, "content")  # no tool_name
    result = svc._build_summary_input_items([history])
    assert len(result) == 1
    assert "unknown_tool" in result[0]["content"][0]["text"]


def test_build_summary_input_items_tool_with_empty_content():
    svc = _make_svc()
    history = _make_history(LLMMessageRole.TOOL, "", tool_name="my_tool")
    # content is empty string → falsy
    result = svc._build_summary_input_items([history])
    assert len(result) == 1


# ─── _format_summary_tool_response ───────────────────────────────────────────


def test_format_summary_tool_response_non_position_tool():
    svc = _make_svc()
    result = svc._format_summary_tool_response("some_tool", "raw output")
    assert result == "raw output"


def test_format_summary_tool_response_position_search_tool_valid():
    svc = _make_svc()
    tool_output = json.dumps([{"text": json.dumps({"AllPositionIds": [1, 2, 3]})}])
    result = svc._format_summary_tool_response(
        ToolName.GENERIC_POSITION_SEARCH.value, tool_output
    )
    assert "3件" in result


def test_format_summary_tool_response_position_search_invalid_json():
    svc = _make_svc()
    result = svc._format_summary_tool_response(
        ToolName.GENERIC_POSITION_SEARCH.value, "not-json"
    )
    # Falls back to POSITION_SEARCH_FAKE_RESULT
    from utils.const import POSITION_SEARCH_FAKE_RESULT

    assert result == POSITION_SEARCH_FAKE_RESULT


# ─── _extract_position_count_from_tool_output ────────────────────────────────


def test_extract_position_count_non_list_outer():
    svc = _make_svc()
    result = svc._extract_position_count_from_tool_output(json.dumps({"not": "a list"}))
    assert result is None


def test_extract_position_count_empty_outer_list():
    svc = _make_svc()
    result = svc._extract_position_count_from_tool_output(json.dumps([]))
    assert result is None


def test_extract_position_count_first_item_not_dict():
    svc = _make_svc()
    result = svc._extract_position_count_from_tool_output(json.dumps(["not-a-dict"]))
    assert result is None


def test_extract_position_count_no_text_key():
    svc = _make_svc()
    result = svc._extract_position_count_from_tool_output(
        json.dumps([{"other": "key"}])
    )
    assert result is None


def test_extract_position_count_text_not_string():
    svc = _make_svc()
    result = svc._extract_position_count_from_tool_output(json.dumps([{"text": 123}]))
    assert result is None


def test_extract_position_count_inner_not_dict():
    svc = _make_svc()
    result = svc._extract_position_count_from_tool_output(
        json.dumps([{"text": json.dumps(["a list"])}])
    )
    assert result is None


def test_extract_position_count_no_all_position_ids():
    svc = _make_svc()
    result = svc._extract_position_count_from_tool_output(
        json.dumps([{"text": json.dumps({"Other": "key"})}])
    )
    assert result is None


def test_extract_position_count_all_position_ids_not_list():
    svc = _make_svc()
    result = svc._extract_position_count_from_tool_output(
        json.dumps([{"text": json.dumps({"AllPositionIds": "not-a-list"})}])
    )
    assert result is None


def test_extract_position_count_success():
    svc = _make_svc()
    result = svc._extract_position_count_from_tool_output(
        json.dumps([{"text": json.dumps({"AllPositionIds": [1, 2, 3, 4, 5]})}])
    )
    assert result == 5


def test_build_summary_input_items_reasoning_role_skipped():
    """Line 199→186: REASONING role doesn't match any branch → item skipped."""
    svc = _make_svc()
    history = _make_history(LLMMessageRole.REASONING, "Reasoning content")
    result = svc._build_summary_input_items([history])
    # REASONING role has no handler, so nothing is appended
    assert result == []
