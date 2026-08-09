from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from containers import _build_refactored_llm_runner
from repositories.action_log_repo import ActionLogRepository
from services.chat.config_validator import InvalidAgentRuntimeConfigError
from services.chat.agent_runtime_config import COMPLETIONS_API_STYLE, DEFAULT_API_STYLE
from services.chat.chat_persistence import _serialize_tool_output_for_storage
from services.chat.history_mapper import HistoryMapper
from services.chat.llm_runner import CompletionsAgentRunner, ResponsesAgentRunner


pytestmark = pytest.mark.completions_contract


def _action_log_repository() -> ActionLogRepository:
    return Mock(spec=ActionLogRepository)


def test_build_refactored_llm_runner_uses_responses_for_default_api_style():
    runner = _build_refactored_llm_runner(
        DEFAULT_API_STYLE,
        action_log_repository=_action_log_repository(),
    )

    assert isinstance(runner, ResponsesAgentRunner)


def test_build_refactored_llm_runner_uses_completions_for_completions_api_style():
    runner = _build_refactored_llm_runner(
        COMPLETIONS_API_STYLE,
        action_log_repository=_action_log_repository(),
    )

    assert isinstance(runner, CompletionsAgentRunner)


def test_build_refactored_llm_runner_raises_for_unsupported_api_style():
    with pytest.raises(InvalidAgentRuntimeConfigError) as exc_info:
        _build_refactored_llm_runner(
            "invalid",
            action_log_repository=_action_log_repository(),
        )

    message = str(exc_info.value)
    assert "agent_runtime.api_style" in message
    assert "invalid" in message
    assert "responses" in message
    assert "completions" in message
    assert "is not supported" in message


def test_history_mapper_parses_tool_output_with_completions_text_wrapper():
    mapper = HistoryMapper()

    parsed = mapper.parse_tool_output({"text": '{"AllPositionIds": ["p-1"]}'})

    assert parsed == {"AllPositionIds": ["p-1"]}


def test_chat_persistence_serialization_stays_json_compatible_for_dict_payloads():
    import json

    payload = {
        "result": "ok",
        "meta": {"source": "completions"},
        "items": [SimpleNamespace(id="1")],
    }

    serialized = _serialize_tool_output_for_storage(payload)

    parsed = json.loads(serialized)
    assert parsed["meta"]["source"] == "completions"
    assert parsed["items"][0]["id"] == "1"
