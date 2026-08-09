import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from domain.entities.chat_history import ChatHistory
from services.conversation_summary_service import (
    ConversationSummaryService,
    SummaryGenerationError,
)
from utils.enum import LLMMessageRole, ToolName

pytestmark = pytest.mark.pre_extraction_parity


def _create_mock_chat_history(role, content, position_id=None, tool_name=None):
    history = Mock(spec=ChatHistory)
    history.role = role
    history.content = content
    history.position_id = position_id
    history.tool_name = tool_name
    return history


@pytest.fixture
def service():
    with patch("services.conversation_summary_service.AsyncOpenAI"):
        svc = ConversationSummaryService(
            model_list=[
                {
                    "model": "gpt-4o-mini",
                    "use_for": ["summary"],
                    "model_settings": {"temperature": 0.3},
                }
            ]
        )
    svc._openai_client = AsyncMock()
    return svc


class TestSummarizeConversation:
    @pytest.mark.asyncio
    async def test_returns_summary_text_successfully(self, service):
        histories = [
            _create_mock_chat_history(LLMMessageRole.USER.value, "質問1", 123),
            _create_mock_chat_history(LLMMessageRole.ASSISTANT.value, "回答1", 123),
        ]

        mock_response = Mock()
        mock_response.output_text = '{"foo":"bar"}'

        mock_openai_client = AsyncMock()
        mock_openai_client.responses.create = AsyncMock(return_value=mock_response)
        service._openai_client = mock_openai_client

        result = await service.summarize_conversation("前回要約", histories)

        assert result == '{"foo":"bar"}'
        call_args = mock_openai_client.responses.create.call_args[1]
        assert call_args["model"] == "gpt-4o-mini"
        assert call_args["text"]["format"]["type"] == "json_schema"
        assert call_args["text"]["format"]["strict"] is True
        assert (
            call_args["text"]["format"]["schema"]
            == service._conversation_summary_schema
        )
        assert call_args["temperature"] == 0.3
        input_items = call_args["input"]
        assert any(
            item["role"] == LLMMessageRole.DEVELOPER.value
            and "前回要約:\n前回要約" in item["content"][0]["text"]
            for item in input_items
        )

    @pytest.mark.asyncio
    async def test_raises_non_retryable_when_output_text_is_empty(self, service):
        mock_response = Mock()
        mock_response.output_text = ""

        mock_openai_client = AsyncMock()
        mock_openai_client.responses.create = AsyncMock(return_value=mock_response)
        service._openai_client = mock_openai_client

        with pytest.raises(SummaryGenerationError) as exc:
            await service.summarize_conversation(None, [])

        assert "contained no text" in str(exc.value)
        assert exc.value.retryable is False

    @pytest.mark.asyncio
    async def test_wraps_retryable_error(self, service):
        RetryableError = type("APITimeoutError", (Exception,), {})
        mock_openai_client = AsyncMock()
        mock_openai_client.responses.create = AsyncMock(
            side_effect=RetryableError("timeout")
        )
        service._openai_client = mock_openai_client

        with pytest.raises(SummaryGenerationError) as exc:
            await service.summarize_conversation(None, [])

        assert "Failed to summarize conversation" in str(exc.value)
        assert exc.value.retryable is True


class TestSummaryInputItems:
    def test_position_search_tool_response_is_count_based(self, service):
        tool_output = json.dumps(
            [
                {
                    "type": "text",
                    "text": json.dumps(
                        {"AllPositionIds": [1, 2, 3]},
                        ensure_ascii=False,
                    ),
                }
            ],
            ensure_ascii=False,
        )
        histories = [
            _create_mock_chat_history(
                LLMMessageRole.TOOL.value,
                tool_output,
                123,
                tool_name=ToolName.GENERIC_POSITION_SEARCH,
            ),
        ]

        result = service._build_summary_input_items(histories)

        assert len(result) == 1
        assert "3件の求人が見つかりました。" in result[0]["content"][0]["text"]


class TestSummarizePositionDetailChat:
    @pytest.mark.asyncio
    async def test_returns_summary_text_successfully(self, service):
        histories = [
            _create_mock_chat_history(LLMMessageRole.USER.value, "質問1", 123),
            _create_mock_chat_history(LLMMessageRole.ASSISTANT.value, "回答1", 123),
        ]

        mock_response = Mock()
        mock_response.output_text = "要約結果"

        mock_openai_client = AsyncMock()
        mock_openai_client.responses.create = AsyncMock(return_value=mock_response)
        service._openai_client = mock_openai_client

        result = await service.summarize_position_detail_chat(histories)

        assert result == "要約結果"

    @pytest.mark.asyncio
    async def test_returns_none_when_output_text_is_blank(self, service):
        histories = [
            _create_mock_chat_history(LLMMessageRole.USER.value, "質問1", 123),
        ]

        mock_response = Mock()
        mock_response.output_text = "   "

        mock_openai_client = AsyncMock()
        mock_openai_client.responses.create = AsyncMock(return_value=mock_response)
        service._openai_client = mock_openai_client

        result = await service.summarize_position_detail_chat(histories)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_chat_histories(self, service):
        result = await service.summarize_position_detail_chat([])

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_api_failure(self, service):
        histories = [
            _create_mock_chat_history(LLMMessageRole.USER.value, "質問1", 123),
        ]

        mock_openai_client = AsyncMock()
        mock_openai_client.responses.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        service._openai_client = mock_openai_client

        result = await service.summarize_position_detail_chat(histories)

        assert result is None

    @pytest.mark.asyncio
    async def test_builds_correct_input_format(self, service):
        histories = [
            _create_mock_chat_history(LLMMessageRole.USER.value, "ユーザー質問", 123),
            _create_mock_chat_history(
                LLMMessageRole.ASSISTANT.value, "アシスタント回答", 123
            ),
            _create_mock_chat_history(
                LLMMessageRole.DEVELOPER.value, "開発者メッセージ", 123
            ),
        ]

        mock_response = Mock()
        mock_response.output_text = "要約"

        mock_openai_client = AsyncMock()
        mock_openai_client.responses.create = AsyncMock(return_value=mock_response)
        service._openai_client = mock_openai_client

        await service.summarize_position_detail_chat(histories)

        call_args = mock_openai_client.responses.create.call_args
        input_items = call_args[1]["input"]

        assert len(input_items) == 4
        assert input_items[0]["role"] == LLMMessageRole.USER.value
        assert input_items[0]["content"][0]["type"] == "input_text"
        assert input_items[0]["content"][0]["text"] == "ユーザー質問"

        assert input_items[1]["role"] == LLMMessageRole.ASSISTANT.value
        assert input_items[1]["content"][0]["type"] == "output_text"
        assert input_items[1]["content"][0]["text"] == "アシスタント回答"

        assert input_items[2]["role"] == LLMMessageRole.DEVELOPER.value
        assert input_items[2]["content"][0]["type"] == "input_text"
        assert input_items[2]["content"][0]["text"] == "開発者メッセージ"

        assert input_items[3] == {
            "type": "message",
            "role": LLMMessageRole.DEVELOPER.value,
            "content": [
                {
                    "type": "input_text",
                    "text": service._position_detail_inquiry_summary_prompt,
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_uses_summary_model_settings(self, service):
        service._summary_model = {
            "model": "gpt-4o-mini",
            "model_settings": {"temperature": 0.5, "max_output_tokens": 2000},
        }

        histories = [
            _create_mock_chat_history(LLMMessageRole.USER.value, "質問", 123),
        ]

        mock_response = Mock()
        mock_response.output_text = "要約"

        mock_openai_client = AsyncMock()
        mock_openai_client.responses.create = AsyncMock(return_value=mock_response)
        service._openai_client = mock_openai_client

        await service.summarize_position_detail_chat(histories)

        call_args = mock_openai_client.responses.create.call_args
        assert call_args[1]["model"] == "gpt-4o-mini"
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["max_output_tokens"] == 2000


def test_raises_when_no_summary_models_defined():
    with pytest.raises(ValueError) as exc_info:
        ConversationSummaryService(
            model_list=[
                {
                    "model": "gpt-4o",
                    "use_for": ["agent"],
                    "model_settings": {"temperature": 0.7},
                }
            ]
        )

    assert "会話要約用のsummaryモデルが定義されていません" in str(exc_info.value)
