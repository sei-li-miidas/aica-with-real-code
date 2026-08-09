import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from domain.entities.chat_history import ChatHistory
from services.base_service import BaseService
from utils.const import POSITION_SEARCH_FAKE_RESULT, format_position_search_fake_result
from utils.enum import LLMMessageRole, ToolName


class SummaryGenerationError(Exception):
    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class ConversationSummaryService(BaseService):
    def __init__(self, model_list: list[dict[str, Any]]) -> None:
        super().__init__()
        summary_models = [
            model for model in model_list if "summary" in model["use_for"]
        ]
        if not summary_models:
            raise ValueError("会話要約用のsummaryモデルが定義されていません")
        if len(summary_models) > 1:
            self.logger.warning("複数の会話要約モデルが定義されています")

        self._summary_model = summary_models[0]
        if "model" not in self._summary_model:
            raise ValueError("Summary model name is not configured")

        prompt_path = (
            Path(__file__).resolve().parent.parent
            / "files"
            / "prompts"
            / "6_ConversationSummary.txt"
        )
        schema_path = (
            Path(__file__).resolve().parent.parent
            / "files"
            / "prompts"
            / "6_ConversationSummary.schema.json"
        )
        position_detail_prompt_path = (
            Path(__file__).resolve().parent.parent
            / "files"
            / "prompts"
            / "7_PositionDetailInquirySummary.txt"
        )
        self._conversation_summary_prompt = prompt_path.read_text(encoding="utf-8")
        self._conversation_summary_schema = json.loads(
            schema_path.read_text(encoding="utf-8")
        )
        self._position_detail_inquiry_summary_prompt = (
            position_detail_prompt_path.read_text(encoding="utf-8")
        )
        self._openai_client = AsyncOpenAI()

    async def summarize_conversation(
        self,
        previous_summary_text: str | None,
        chat_histories: list[ChatHistory],
    ) -> str:
        summary_inputs = self._build_summary_input_items(chat_histories)
        if previous_summary_text:
            summary_inputs.append(
                {
                    "type": "message",
                    "role": LLMMessageRole.DEVELOPER.value,
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"前回要約:\n{previous_summary_text}",
                        }
                    ],
                }
            )
        summary_inputs.append(
            {
                "type": "message",
                "role": LLMMessageRole.DEVELOPER.value,
                "content": [
                    {
                        "type": "input_text",
                        "text": self._conversation_summary_prompt,
                    }
                ],
            }
        )

        model_name = self._summary_model["model"]
        model_settings = self._summary_model.get("model_settings", {})

        try:
            response = await self._openai_client.responses.create(
                model=model_name,
                input=summary_inputs,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "conversation_summary",
                        "strict": True,
                        "schema": self._conversation_summary_schema,
                    }
                },
                **model_settings,
            )
            if not response.output_text:
                raise SummaryGenerationError(
                    "OpenAI summary response contained no text",
                    retryable=False,
                )
            return response.output_text
        except SummaryGenerationError:
            raise
        except Exception as e:
            self.logger.exception("Failed to summarize conversation")
            raise SummaryGenerationError(
                "Failed to summarize conversation",
                retryable=self._is_retryable_summary_error(e),
            ) from e

    async def summarize_position_detail_chat(
        self,
        chat_histories: list[ChatHistory],
    ) -> str | None:
        summary_inputs = self._build_summary_input_items(chat_histories)
        if not summary_inputs:
            return None

        summary_inputs.append(
            {
                "type": "message",
                "role": LLMMessageRole.DEVELOPER.value,
                "content": [
                    {
                        "type": "input_text",
                        "text": self._position_detail_inquiry_summary_prompt,
                    }
                ],
            }
        )

        model_name = self._summary_model["model"]
        model_settings = self._summary_model.get("model_settings", {})

        try:
            response = await self._openai_client.responses.create(
                model=model_name,
                input=summary_inputs,
                **model_settings,
            )
            if not response.output_text or not response.output_text.strip():
                return None
            return response.output_text
        except Exception:
            self.logger.exception("Failed to summarize position detail chat")
            return None

    def _is_retryable_summary_error(self, error: Exception) -> bool:
        status_code = getattr(error, "status_code", None)
        if status_code == 429:
            return True
        if isinstance(status_code, int) and status_code >= 500:
            return True

        error_type_name = type(error).__name__
        retryable_names = {
            "APITimeoutError",
            "APIConnectionError",
            "RateLimitError",
            "InternalServerError",
        }
        return error_type_name in retryable_names

    def _build_summary_input_items(
        self,
        histories: list[ChatHistory],
    ) -> list[dict[str, Any]]:
        if not histories:
            return []

        summary_inputs: list[dict[str, Any]] = []
        for history in histories:
            role = history.role
            if role in (
                LLMMessageRole.USER.value,
                LLMMessageRole.DEVELOPER.value,
            ):
                summary_inputs.append(
                    self._build_text_message(role, history.content, output=False)
                )
            elif role == LLMMessageRole.ASSISTANT.value:
                summary_inputs.append(
                    self._build_text_message(role, history.content, output=True)
                )
            elif role in (LLMMessageRole.TOOL.value, LLMMessageRole.HANDOFF.value):
                tool_name = getattr(history, "tool_name", None) or "unknown_tool"
                tool_response = self._format_summary_tool_response(
                    tool_name=tool_name,
                    tool_response=history.content if history.content else "",
                )
                summary_inputs.append(
                    self._build_text_message(
                        LLMMessageRole.ASSISTANT.value,
                        (
                            f"（システム実行）ツール {tool_name} を実行しました。\n"
                            f"結果:\n{tool_response}"
                        ),
                        output=True,
                    )
                )
        return summary_inputs

    def _build_text_message(
        self,
        role: str,
        content: str,
        output: bool,
    ) -> dict[str, Any]:
        return {
            "type": "message",
            "role": role,
            "content": [
                {
                    "type": "output_text" if output else "input_text",
                    "text": content,
                }
            ],
        }

    def _format_summary_tool_response(self, tool_name: str, tool_response: str) -> str:
        if not ToolName.is_position_search_tool(tool_name):
            return tool_response

        positions_count = self._extract_position_count_from_tool_output(tool_response)
        if positions_count is None:
            return POSITION_SEARCH_FAKE_RESULT
        return format_position_search_fake_result(positions_count)

    def _extract_position_count_from_tool_output(
        self, tool_response: str
    ) -> int | None:
        try:
            parsed = json.loads(tool_response)
            if not isinstance(parsed, list) or not parsed:
                return None
            first = parsed[0]
            if not isinstance(first, dict):
                return None
            text = first.get("text")
            if not isinstance(text, str):
                return None
            inner = json.loads(text)
            if not isinstance(inner, dict):
                return None
            position_ids = inner.get("AllPositionIds")
            if not isinstance(position_ids, list):
                return None
            return len(position_ids)
        except (TypeError, json.JSONDecodeError):
            return None


