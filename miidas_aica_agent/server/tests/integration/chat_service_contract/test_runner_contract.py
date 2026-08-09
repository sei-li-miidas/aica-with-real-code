from __future__ import annotations

"""
Runner contract テスト。

テストケース一覧:
- test_legacy_runner_seam_delegates_to_runner
    対象: legacy 実装の _run_streamed seam が Runner.run_streamed へ
    正しく委譲されること。
- test_responses_run_stream_normalizes_sdk_shaped_events
    対象: SDK 形状イベント列を ResponsesRunStream が
    正規化イベントへ変換すること。
- test_sdk_stream_fixture_exposes_sdk_shaped_events
    対象: fixture が SDK 互換 shape を保持し、
    契約テスト入力として妥当であること。
- test_normalize_stream_event_ignores_malformed_raw_text_delta_events
    対象: 不正な raw text delta を _normalize_stream_event が
    無視して安全に継続すること。
- test_responses_agent_runner_forwards_previous_response_id
    対象: previous_response_id が ResponsesAgentRunner 経由で
    下流へ伝播すること。
- test_stop_at_tool_replay_fixture_documents_function_call_output_shape
    対象: stop_at tool replay fixture が function_call_output 形状を
    正しく記述していること。
- test_usage_response_fixture_documents_token_accounting_shape
    対象: usage fixture が token accounting の期待 shape を
    満たすこと。
"""

import json
import runpy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from services.chat.llm_runner import (
    LLMIgnoredStreamEvent,
    LLMRawResponseEvent,
    LLMRunItemStreamEvent,
    ResponsesAgentRunner,
    ResponsesRunStream,
    _normalize_stream_event,
)


pytestmark = pytest.mark.rollback_runner

FIXTURES_DIR = Path(__file__).with_name("fixtures")


def _load_py_fixture(filename: str) -> dict:
    return runpy.run_path(str(FIXTURES_DIR / filename))


def _load_json_fixture(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


@pytest.mark.parametrize("chat_service_container", ["legacy"], indirect=True)
def test_legacy_runner_seam_delegates_to_runner(chat_service_container):
    chat_service = chat_service_container
    starting_agent = SimpleNamespace(name="CareerAdvisor")
    run_result = object()

    with patch(
        "services.chat_service.Runner.run_streamed",
        return_value=run_result,
    ) as mock_run_streamed:
        conversation_input = ["conversation turn"]
        returned = chat_service._run_streamed(
            starting_agent=starting_agent,
            input=conversation_input,
            previous_response_id="resp-prev",
        )

    assert returned is run_result
    mock_run_streamed.assert_called_once_with(
        starting_agent=starting_agent,
        input=conversation_input,
        previous_response_id="resp-prev",
    )


@pytest.mark.pre_extraction_bootstrap
@pytest.mark.pre_extraction_parity
@pytest.mark.asyncio
async def test_responses_run_stream_normalizes_sdk_shaped_events():
    fixture = _load_py_fixture("sdk_stream_events.py")
    run_result = fixture["build_run_result"]()
    run_result.last_response_id = "resp-next"
    run_result.last_agent = SimpleNamespace(name="handoff-agent")
    run_result.context_wrapper = SimpleNamespace(
        usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}
    )
    stream = ResponsesRunStream(run_result)

    events = [event async for event in stream.stream_events()]

    assert [event.type for event in events] == [
        "raw_response_event",
        "run_item_stream_event",
        "run_item_stream_event",
    ]
    assert events[0] == LLMRawResponseEvent(item_id="response-1", delta="こんにちは")
    assert events[2] == LLMRunItemStreamEvent(
        item=SimpleNamespace(
            type="tool_call_item",
            call_id="tool-call-1",
            name="jobtype_search_by_keywords",
            arguments='{"SessionID":"session-1","RequestID":"request-1"}',
        )
    )
    assert stream.continuation_state == "resp-next"
    assert stream.agent_state == SimpleNamespace(name="handoff-agent")
    assert (
        stream.replay_items
        == _load_json_fixture("stop_at_tool_replay.json")["replay_items"]
    )
    assert stream.usage == {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}


@pytest.mark.asyncio
async def test_sdk_stream_fixture_exposes_sdk_shaped_events():
    fixture = _load_py_fixture("sdk_stream_events.py")
    run_result = fixture["build_run_result"]()

    events = [event async for event in run_result.stream_events()]

    assert [event.type for event in events] == [
        "raw_response_event",
        "run_item_stream_event",
        "run_item_stream_event",
    ]
    assert events[0].data.type == "response.output_text.delta"
    assert events[0].data.item_id == "response-1"
    assert events[2].item.call_id == "tool-call-1"
    assert (
        run_result.to_input_list()
        == _load_json_fixture("stop_at_tool_replay.json")["replay_items"]
    )
    assert run_result.usage == fixture["SDK_USAGE_RESPONSE"]


def test_normalize_stream_event_ignores_malformed_raw_text_delta_events():
    event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(item_id="", delta="hello"),
    )

    normalized = _normalize_stream_event(event)

    assert normalized == LLMIgnoredStreamEvent()


def test_responses_agent_runner_forwards_previous_response_id(tmp_path):
    fixture = _load_py_fixture("sdk_stream_events.py")
    run_result = fixture["build_run_result"]()
    run_result.last_response_id = "resp-next"
    run_result.last_agent = SimpleNamespace(name="handoff-agent")
    run_result.context_wrapper = SimpleNamespace(usage=fixture["SDK_USAGE_RESPONSE"])
    starting_agent = SimpleNamespace(name="CareerAdvisor")
    conversation_input = ["conversation turn"]
    runner = ResponsesAgentRunner(action_log_repository=MagicMock())

    with patch(
        "services.chat.llm_runner.Runner.run_streamed", return_value=run_result
    ) as mock_run_streamed:
        wrapped = runner.run_streamed(
            starting_agent=starting_agent,
            input=conversation_input,
            continuation_state="resp-prev",
        )

    mock_run_streamed.assert_called_once_with(
        starting_agent=starting_agent,
        input=conversation_input,
        previous_response_id="resp-prev",
    )
    assert isinstance(wrapped, ResponsesRunStream)
    assert wrapped.continuation_state == "resp-next"
    assert wrapped.agent_state == SimpleNamespace(name="handoff-agent")
    assert wrapped.replay_items == fixture["build_run_result"]().to_input_list()
    assert wrapped.usage == fixture["SDK_USAGE_RESPONSE"]


@pytest.mark.pre_extraction_bootstrap
@pytest.mark.pre_extraction_parity
def test_stop_at_tool_replay_fixture_documents_function_call_output_shape():
    fixture = _load_json_fixture("stop_at_tool_replay.json")

    assert fixture["replay_items"] == [
        {
            "type": "function_call_output",
            "call_id": "tool-call-1",
            "output": "tool output replay",
        }
    ]


@pytest.mark.pre_extraction_bootstrap
@pytest.mark.pre_extraction_parity
def test_usage_response_fixture_documents_token_accounting_shape():
    fixture = _load_json_fixture("usage_response.json")

    assert fixture["usage"] == {
        "input_tokens": 12,
        "output_tokens": 34,
        "total_tokens": 46,
    }
