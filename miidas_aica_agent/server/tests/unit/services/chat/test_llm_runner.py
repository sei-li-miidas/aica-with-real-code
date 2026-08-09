from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from repositories.action_log_repo import ActionLogType
from services.chat import llm_runner as llm_runner_module
from services.chat.llm_runner import (
    ANYLLM_COMPLETIONS_PROVIDER,
    COMPLETIONS_PROVIDER_ENV,
    LITELLM_COMPLETIONS_PROVIDER,
    CompletionsAgentRunner,
    CompletionsRunContinuationState,
    _build_completions_model_provider,
    CompletionsRunStream,
    _CompletionsReplayUtils,
    _run_result_to_input_list,
    json_default,
    LLMRetryChunkEvent,
    LLMRetryCompleteEvent,
    LLMAgentUpdatedStreamEvent,
    LLMIgnoredStreamEvent,
    LLMRawResponseEvent,
    LLMRunItemStreamEvent,
    ResponsesAgentRunner,
    ResponsesRunStream,
    _normalize_stream_event,
)
from services.chat.tool_event_handler import RetryableToolOutputFailure


pytestmark = pytest.mark.pre_extraction_parity


def _responses_run_result(usage, *, aclose=True):
    result = SimpleNamespace(
        last_response_id="resp-1",
        last_agent="agent-1",
        context_wrapper=SimpleNamespace(usage=usage),
        to_input_list=lambda mode=None: [
            {"type": "function_call_output", "call_id": "c1"}
        ],
    )
    if aclose:
        result.aclose = AsyncMock()
    return result


def test_normalize_stream_event_raw_text_delta():
    event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(
            type="response.output_text.delta",
            item_id="item-1",
            delta="hello",
        ),
    )

    result = _normalize_stream_event(event)

    assert isinstance(result, LLMRawResponseEvent)
    assert result.item_id == "item-1"
    assert result.delta == "hello"


def test_normalize_stream_event_raw_non_text_delta_is_ignored():
    event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(
            type="response.function_call_arguments.delta",
            item_id="item-1",
            delta="{}",
        ),
    )

    result = _normalize_stream_event(event)

    assert isinstance(result, LLMIgnoredStreamEvent)


def test_normalize_stream_event_run_item_and_agent_updated():
    run_item = SimpleNamespace(type="run_item_stream_event", item={"id": 1})
    updated = SimpleNamespace(type="agent_updated_stream_event", new_agent="A")

    run_item_result = _normalize_stream_event(run_item)
    updated_result = _normalize_stream_event(updated)

    assert isinstance(run_item_result, LLMRunItemStreamEvent)
    assert run_item_result.item == {"id": 1}
    assert isinstance(updated_result, LLMAgentUpdatedStreamEvent)
    assert updated_result.new_agent == "A"


def test_normalize_stream_event_unsupported_raises():
    with pytest.raises(ValueError, match="Unsupported stream event type"):
        _normalize_stream_event(SimpleNamespace(type="other"))


def test_run_result_to_input_list_handles_non_list_iterable():
    class _RunResult:
        def to_input_list(self, mode=None):
            return (item for item in [{"type": "message", "content": "ok"}])

    result = _run_result_to_input_list(_RunResult())
    assert result == [{"type": "message", "content": "ok"}]


def test_completions_replay_utils_sanitize_replay_item_keeps_unknown_type():
    item = {"type": "unknown_event", "x": 1}
    assert _CompletionsReplayUtils.sanitize_replay_item(item) is item


def test_completions_replay_utils_build_preferred_outputs_skips_non_dict_items():
    result = _CompletionsReplayUtils.build_preferred_function_call_outputs(
        [
            "not-a-dict",
            {"type": "function_call_output", "call_id": "c1", "output": "ok"},
        ]
    )
    assert result == {
        "c1": {"type": "function_call_output", "call_id": "c1", "output": "ok"}
    }


def test_completions_replay_utils_sanitize_replay_items_skips_output_without_call_id():
    result = _CompletionsReplayUtils.sanitize_replay_items(
        [{"type": "function_call_output", "output": "orphan"}]
    )
    assert result == []


def test_completions_replay_utils_summarize_input_items_unknown_type():
    summary = _CompletionsReplayUtils.summarize_input_items([{"type": "mystery_type"}])
    assert summary == ["mystery_type"]


def test_json_default_covers_all_fallback_branches():
    @dataclass
    class _D:
        x: int

    class _M:
        def model_dump(self):
            return {"dumped": True}

    class _O:
        def __init__(self):
            self.v = 1

    class _S:
        __slots__ = ()

    assert json_default(_D(1)) == {"x": 1}
    assert json_default(_M()) == {"dumped": True}
    assert json_default(_O()) == {"v": 1}
    slot_obj = _S()
    assert json_default(slot_obj) == str(slot_obj)


@pytest.mark.asyncio
async def test_responses_run_stream_normalizes_and_closes_when_aclose_available():
    raw_events = [
        SimpleNamespace(
            type="raw_response_event",
            data=SimpleNamespace(
                type="response.output_text.delta",
                item_id="msg-1",
                delta="a",
            ),
        )
    ]

    run_result = _responses_run_result({"total_tokens": 1})

    async def _stream_events():
        for event in raw_events:
            yield event

    run_result.stream_events = _stream_events
    stream = ResponsesRunStream(run_result)

    events = [event async for event in stream.stream_events()]

    assert len(events) == 1
    assert isinstance(events[0], LLMRawResponseEvent)
    assert stream.continuation_state == "resp-1"
    assert stream.agent_state == "agent-1"
    assert stream.replay_items == [{"type": "function_call_output", "call_id": "c1"}]
    assert stream.usage == {"total_tokens": 1}

    await stream.aclose()
    run_result.aclose.assert_called_once()


def test_responses_agent_runner_forwards_previous_response_id():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)
    mock_result = MagicMock()

    with patch(
        "services.chat.llm_runner.Runner.run_streamed", return_value=mock_result
    ) as mock_run:
        stream = runner.run_streamed(
            starting_agent=MagicMock(),
            input=[{"type": "message"}],
            continuation_state="resp-prev",
        )

    mock_run.assert_called_once()
    kwargs = mock_run.call_args.kwargs
    assert kwargs["previous_response_id"] == "resp-prev"
    assert isinstance(stream, ResponsesRunStream)


@pytest.mark.asyncio
async def test_run_with_retry_uses_continuation_state_supplier_per_attempt():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)

    first_raw = _responses_run_result({"total_tokens": 1})
    second_raw = _responses_run_result({"total_tokens": 2})
    with patch(
        "services.chat.llm_runner.Runner.run_streamed",
        side_effect=[first_raw, second_raw],
    ) as mock_run:
        current_state = {"value": "resp-1"}
        attempt = {"count": 0}

        async def process_stream(_stream):
            attempt["count"] += 1
            if attempt["count"] == 1:
                raise RetryableToolOutputFailure("call-1", "retry me")
            yield "ok"

        async def on_retryable(_err):
            current_state["value"] = "resp-2"

        events = [
            event
            async for event in runner.run_with_retry(
                starting_agent=MagicMock(),
                input=[{"type": "message"}],
                process_stream=process_stream,
                continuation_state_supplier=lambda: current_state["value"],
                on_retryable_error=on_retryable,
            )
        ]

    assert len(events) == 2
    assert isinstance(events[0], LLMRetryChunkEvent)
    assert events[0].chunk == "ok"
    assert isinstance(events[1], LLMRetryCompleteEvent)
    assert events[1].result.succeeded is True
    assert events[1].result.attempts == 2

    first_call = mock_run.call_args_list[0].kwargs
    second_call = mock_run.call_args_list[1].kwargs
    assert first_call["previous_response_id"] == "resp-1"
    assert second_call["previous_response_id"] == "resp-2"


@pytest.mark.asyncio
async def test_run_with_retry_applies_backoff_on_retryable_error():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)

    raw = _responses_run_result({"total_tokens": 1})
    with (
        patch(
            "services.chat.llm_runner.Runner.run_streamed",
            side_effect=[raw, raw],
        ),
        patch("services.chat.llm_runner.asyncio.sleep", new=AsyncMock()) as mock_sleep,
    ):
        attempt = {"count": 0}

        async def process_stream(_stream):
            attempt["count"] += 1
            if attempt["count"] == 1:
                raise RetryableToolOutputFailure("call-1", "retry me")
            if False:
                yield None

        events = [
            event
            async for event in runner.run_with_retry(
                starting_agent=MagicMock(),
                input=[{"type": "message"}],
                process_stream=process_stream,
                continuation_state="resp-prev",
            )
        ]

    assert isinstance(events[-1], LLMRetryCompleteEvent)
    assert events[-1].result.succeeded is True
    mock_sleep.assert_awaited_once_with(runner.BASE_DELAY_SECONDS)


@pytest.mark.asyncio
async def test_run_with_retry_invokes_before_and_after_attempt_callbacks():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)

    before = AsyncMock()
    after = AsyncMock()
    raw = _responses_run_result(None)

    with patch("services.chat.llm_runner.Runner.run_streamed", return_value=raw):

        async def process_stream(_stream):
            yield "ok"

        events = [
            event
            async for event in runner.run_with_retry(
                starting_agent=MagicMock(),
                input=[{"type": "message"}],
                process_stream=process_stream,
                on_before_attempt=before,
                on_after_attempt=after,
            )
        ]

    assert isinstance(events[-1], LLMRetryCompleteEvent)
    assert events[-1].result.succeeded is True
    before.assert_awaited_once()
    after.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_with_retry_calls_after_when_before_raises():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)

    before = AsyncMock(side_effect=RuntimeError("before failed"))
    after = AsyncMock()
    on_non_retryable = AsyncMock()

    async def process_stream(_stream):
        if False:
            yield None

    events = [
        event
        async for event in runner.run_with_retry(
            starting_agent=MagicMock(),
            input=[{"type": "message"}],
            process_stream=process_stream,
            on_before_attempt=before,
            on_after_attempt=after,
            on_non_retryable_error=on_non_retryable,
        )
    ]

    assert len(events) == 1
    assert isinstance(events[0], LLMRetryCompleteEvent)
    assert events[0].result.succeeded is False
    assert isinstance(events[0].result.error, RuntimeError)
    assert str(events[0].result.error) == "before failed"
    before.assert_awaited_once()
    after.assert_awaited_once()
    on_non_retryable.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_with_retry_logs_when_usage_recording_fails():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)
    raw = _responses_run_result({"total_tokens": 10})

    with (
        patch("services.chat.llm_runner.Runner.run_streamed", return_value=raw),
        patch(
            "services.chat.llm_runner.asyncio.to_thread",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ),
        patch.object(runner._logger, "exception") as mock_exception,
    ):

        async def process_stream(_stream):
            if False:
                yield None

        events = [
            event
            async for event in runner.run_with_retry(
                starting_agent=MagicMock(),
                input=[{"type": "message"}],
                process_stream=process_stream,
                message_id="msg-1",
            )
        ]

    assert isinstance(events[-1], LLMRetryCompleteEvent)
    assert events[-1].result.succeeded is True
    mock_exception.assert_called_with("Failed to record LLM usage")


@pytest.mark.asyncio
async def test_run_with_retry_non_retryable_error_emits_failed_complete_and_callback():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)
    raw = _responses_run_result({"total_tokens": 7})
    on_non_retryable = AsyncMock()
    after = AsyncMock()

    with (
        patch("services.chat.llm_runner.Runner.run_streamed", return_value=raw),
        patch.object(runner._logger, "exception") as mock_exception,
    ):

        async def process_stream(_stream):
            raise RuntimeError("non-retryable")
            if False:
                yield None

        events = [
            event
            async for event in runner.run_with_retry(
                starting_agent=MagicMock(),
                input=[{"type": "message"}],
                process_stream=process_stream,
                on_non_retryable_error=on_non_retryable,
                on_after_attempt=after,
            )
        ]

    assert len(events) == 1
    assert isinstance(events[0], LLMRetryCompleteEvent)
    assert events[0].result.succeeded is False
    assert isinstance(events[0].result.error, RuntimeError)
    assert events[0].result.attempts == 1
    assert events[0].result.usage is None
    on_non_retryable.assert_awaited_once()
    after.assert_awaited_once()
    mock_exception.assert_called_with("Non-retryable LLM error")


@pytest.mark.asyncio
async def test_run_with_retry_reads_usage_after_stream_consumed():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)
    raw = _responses_run_result(None)

    with patch("services.chat.llm_runner.Runner.run_streamed", return_value=raw):

        async def process_stream(stream):
            yield "chunk-1"
            stream._run_result.context_wrapper.usage = {"total_tokens": 9}

        events = [
            event
            async for event in runner.run_with_retry(
                starting_agent=MagicMock(),
                input=[{"type": "message"}],
                process_stream=process_stream,
                message_id="msg-usage",
            )
        ]

    assert isinstance(events[-1], LLMRetryCompleteEvent)
    assert events[-1].result.succeeded is True
    assert events[-1].result.usage == {"total_tokens": 9}
    action_log_repo.insert.assert_called_once_with(
        log_type=ActionLogType.TOKEN_USAGE,
        source="msg-usage",
        content='{"total_tokens": 9}',
    )


@pytest.mark.asyncio
async def test_run_with_retry_records_usage_only_on_successful_attempt():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)

    first_raw = _responses_run_result({"total_tokens": 1})
    second_raw = _responses_run_result({"total_tokens": 2})
    with patch(
        "services.chat.llm_runner.Runner.run_streamed",
        side_effect=[first_raw, second_raw],
    ):
        attempt = {"count": 0}

        async def process_stream(_stream):
            attempt["count"] += 1
            if attempt["count"] == 1:
                raise RetryableToolOutputFailure("call-1", "retry")
            yield "ok"

        events = [
            event
            async for event in runner.run_with_retry(
                starting_agent=MagicMock(),
                input=[{"type": "message"}],
                process_stream=process_stream,
                message_id="msg-retry",
            )
        ]

    assert isinstance(events[-1], LLMRetryCompleteEvent)
    assert events[-1].result.succeeded is True
    assert events[-1].result.attempts == 2
    action_log_repo.insert.assert_called_once_with(
        log_type=ActionLogType.TOKEN_USAGE,
        source="msg-retry",
        content='{"total_tokens": 2}',
    )


def test_record_usage_returns_early_when_usage_is_none():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)

    runner._record_usage(None, "msg-1")

    action_log_repo.insert.assert_not_called()


def test_record_usage_persists_token_usage_payload():
    action_log_repo = MagicMock()
    runner = ResponsesAgentRunner(action_log_repository=action_log_repo)

    runner._record_usage({"input_tokens": 1, "total_tokens": 3}, "msg-2")

    action_log_repo.insert.assert_called_once_with(
        log_type=ActionLogType.TOKEN_USAGE,
        source="msg-2",
        content='{"input_tokens": 1, "total_tokens": 3}',
    )


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_exposes_replay_state_and_closable_stream():
    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(
                type="raw_response_event",
                data=SimpleNamespace(
                    type="response.output_text.delta",
                    item_id="__fake_id__",
                    delta="hello",
                ),
            )

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())

    events = [event async for event in stream.stream_events()]

    assert len(events) == 1
    assert isinstance(events[0], LLMRawResponseEvent)
    assert events[0].item_id.startswith("msg_")
    assert events[0].item_id != "__fake_id__"
    assert events[0].delta == "hello"
    assert isinstance(stream.continuation_state, CompletionsRunContinuationState)
    assert stream.continuation_state.run_state == SimpleNamespace(turn="state")
    assert stream.agent_state == SimpleNamespace(name="completions-agent")
    assert stream.replay_items == [{"type": "message", "content": "hello"}]
    assert stream.usage == {"total_tokens": 8}

    await stream.aclose()
    stream._run_result.aclose.assert_called_once()


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_uses_stable_generated_message_id():
    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(
                type="raw_response_event",
                data=SimpleNamespace(
                    type="response.output_text.delta",
                    item_id="__fake_id__",
                    delta="hello",
                ),
            )
            yield SimpleNamespace(
                type="raw_response_event",
                data=SimpleNamespace(
                    type="response.output_text.delta",
                    item_id="__fake_id__",
                    delta=" world",
                ),
            )

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())

    events = [event async for event in stream.stream_events()]
    assert len(events) == 2
    assert all(isinstance(event, LLMRawResponseEvent) for event in events)
    assert events[0].item_id.startswith("msg_")
    assert events[0].item_id != "__fake_id__"
    assert events[0].item_id == events[1].item_id
    assert events[0].delta == "hello"
    assert events[1].delta == " world"


@pytest.mark.completions_runner_internal
def test_completions_run_stream_continuation_state_accessible_before_stream_consumption():
    """continuation_state はストリーム消費前にアクセスしても有効な継続状態を返す。"""

    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 4})
            self.aclose = AsyncMock()

        async def stream_events(self):
            if False:  # pragma: no cover
                yield None

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())

    state = stream.continuation_state
    assert isinstance(state, CompletionsRunContinuationState)
    assert state.run_state == SimpleNamespace(turn="state")
    assert state.agent_state == SimpleNamespace(name="completions-agent")
    assert state.replay_items == [{"type": "message", "content": "hello"}]
    assert state.usage == {"total_tokens": 4}


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_rewrites_fake_run_item_message_id():
    fake_message_item = SimpleNamespace(
        raw_item=SimpleNamespace(
            id="__fake_id__", content=[SimpleNamespace(text="hello")]
        )
    )

    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(
                type="raw_response_event",
                data=SimpleNamespace(
                    type="response.output_text.delta",
                    item_id="__fake_id__",
                    delta="hello",
                ),
            )
            yield SimpleNamespace(
                type="run_item_stream_event",
                item=fake_message_item,
            )

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())

    events = [event async for event in stream.stream_events()]
    raw_event = events[0]
    run_item_event = events[1]

    assert isinstance(raw_event, LLMRawResponseEvent)
    assert isinstance(run_item_event, LLMRunItemStreamEvent)
    assert raw_event.item_id != "__fake_id__"
    assert raw_event.item_id.startswith("msg_")
    assert run_item_event.item.raw_item.id == raw_event.item_id


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_rewrites_fake_tool_call_id_with_fc_prefix():
    fake_tool_call_item = SimpleNamespace(
        raw_item=SimpleNamespace(
            id="__fake_id__",
            type="function_call",
            call_id="call-1",
            name="search_positions",
            arguments="{}",
        )
    )

    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(
                type="run_item_stream_event",
                item=fake_tool_call_item,
            )

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())
    events = [event async for event in stream.stream_events()]

    assert len(events) == 1
    assert isinstance(events[0], LLMRunItemStreamEvent)
    assert events[0].item.raw_item.id.startswith("fc_")


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_generates_distinct_ids_for_empty_source_keys():
    item_with_none_id = SimpleNamespace(raw_item=SimpleNamespace(id=None, content=[]))
    item_with_empty_id = SimpleNamespace(raw_item=SimpleNamespace(id="", content=[]))

    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(type="run_item_stream_event", item=item_with_none_id)
            yield SimpleNamespace(type="run_item_stream_event", item=item_with_empty_id)

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())
    events = [event async for event in stream.stream_events()]

    assert len(events) == 2
    assert all(isinstance(event, LLMRunItemStreamEvent) for event in events)
    first_id = events[0].item.raw_item.id
    second_id = events[1].item.raw_item.id
    assert isinstance(first_id, str)
    assert isinstance(second_id, str)
    assert first_id.startswith("msg_")
    assert second_id.startswith("msg_")
    assert first_id != second_id


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_keeps_run_item_when_raw_item_absent():
    rawless_item = SimpleNamespace(kind="no-raw-item")

    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(type="run_item_stream_event", item=rawless_item)

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())
    events = [event async for event in stream.stream_events()]

    assert len(events) == 1
    assert isinstance(events[0], LLMRunItemStreamEvent)
    assert events[0].item is rawless_item


@pytest.mark.completions_runner_internal
def test_completions_run_stream_preserves_raw_replay_items_in_continuation_state():
    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [
                {
                    "id": "msg_1",
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "hello"}],
                    "status": "completed",
                    "provider_data": {"tool_calls": [{"id": "call-1"}]},
                },
                {
                    "id": "fc_1",
                    "type": "function_call",
                    "call_id": "call-1",
                    "name": "search_positions",
                    "arguments": "{}",
                    "provider_data": {"debug": True},
                },
                {
                    "type": "function_call_output",
                    "call_id": "call-1",
                    "output": '{"ok": true}',
                    "provider_data": {"debug": True},
                },
            ]

    stream = CompletionsRunStream(_RunResult())

    assert stream.replay_items == [
        {
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "hello"}],
            "status": "completed",
            "provider_data": {"tool_calls": [{"id": "call-1"}]},
        },
        {
            "id": "fc_1",
            "type": "function_call",
            "call_id": "call-1",
            "name": "search_positions",
            "arguments": "{}",
            "provider_data": {"debug": True},
        },
        {
            "type": "function_call_output",
            "call_id": "call-1",
            "output": '{"ok": true}',
            "provider_data": {"debug": True},
        },
    ]


@pytest.mark.completions_runner_internal
def test_completions_run_stream_builds_state_when_to_state_is_missing():
    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())
    continuation_state = stream.continuation_state

    assert continuation_state.run_state is None
    assert continuation_state.agent_state == SimpleNamespace(name="completions-agent")


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_uses_call_id_for_tool_call_id_stability():
    fake_tool_call_item_1 = SimpleNamespace(
        raw_item=SimpleNamespace(
            id="__fake_id__",
            type="function_call",
            call_id="call-1",
            name="search_positions",
            arguments="{}",
        )
    )
    fake_tool_call_item_2 = SimpleNamespace(
        raw_item=SimpleNamespace(
            id="__fake_id__",
            type="function_call",
            call_id="call-2",
            name="search_positions",
            arguments="{}",
        )
    )

    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(
                type="run_item_stream_event", item=fake_tool_call_item_1
            )
            yield SimpleNamespace(
                type="run_item_stream_event", item=fake_tool_call_item_2
            )
            yield SimpleNamespace(
                type="run_item_stream_event", item=fake_tool_call_item_1
            )

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())
    events = [event async for event in stream.stream_events()]

    assert len(events) == 3
    first_id = events[0].item.raw_item.id
    second_id = events[1].item.raw_item.id
    third_id = events[2].item.raw_item.id

    assert first_id.startswith("fc_")
    assert second_id.startswith("fc_")
    assert first_id != second_id
    assert third_id == first_id


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_tolerates_run_item_raw_id_none():
    fake_message_item = SimpleNamespace(
        raw_item=SimpleNamespace(id=None, content=[SimpleNamespace(text="hello")])
    )

    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(type="run_item_stream_event", item=fake_message_item)

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())

    events = [event async for event in stream.stream_events()]
    assert len(events) == 1
    assert isinstance(fake_message_item.raw_item.id, str)


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_tolerates_run_item_raw_id_not_string():
    fake_message_item = SimpleNamespace(
        raw_item={"id": 123, "type": "message", "role": "assistant", "content": []}
    )

    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(type="run_item_stream_event", item=fake_message_item)

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())

    events = [event async for event in stream.stream_events()]
    assert len(events) == 1
    assert isinstance(fake_message_item.raw_item["id"], str)


@pytest.mark.completions_runner_internal
def test_completions_run_stream_builds_state_without_optional_attrs():
    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())

    continuation_state = stream.continuation_state
    assert isinstance(continuation_state, CompletionsRunContinuationState)
    assert continuation_state.run_state == SimpleNamespace(turn="state")
    assert continuation_state.agent_state == SimpleNamespace(name="completions-agent")
    assert continuation_state.replay_items == [{"type": "message", "content": "hello"}]
    assert continuation_state.usage == {"total_tokens": 8}


@pytest.mark.completions_runner_internal
def test_completions_runner_builds_anyllm_run_config_by_default(monkeypatch):
    monkeypatch.delenv(COMPLETIONS_PROVIDER_ENV, raising=False)
    runner = CompletionsAgentRunner(action_log_repository=MagicMock())

    run_config = runner._get_run_config()

    assert type(run_config.model_provider).__name__ == "AnyLLMProvider"


@pytest.mark.completions_runner_internal
def test_anyllm_provider_uses_chat_completions_api():
    # CompletionsAgentRunner は Chat Completions style 用。Responses API を選ぶと履歴の
    # assistant(output_text) item が Responses の input schema 検証で弾かれるため固定する。
    provider = llm_runner_module._build_anyllm_model_provider()

    assert type(provider).__name__ == "AnyLLMProvider"
    assert provider.api == "chat_completions"


@pytest.mark.completions_runner_internal
def test_completions_provider_flag_selects_backend(monkeypatch):
    litellm_sentinel = object()
    anyllm_sentinel = object()
    # builder の dispatch のみを検証し、optional dependency の install 有無に依存させない。
    monkeypatch.setattr(
        llm_runner_module,
        "_COMPLETIONS_PROVIDER_BUILDERS",
        {
            LITELLM_COMPLETIONS_PROVIDER: lambda: litellm_sentinel,
            ANYLLM_COMPLETIONS_PROVIDER: lambda: anyllm_sentinel,
        },
    )

    monkeypatch.delenv(COMPLETIONS_PROVIDER_ENV, raising=False)
    assert _build_completions_model_provider() is anyllm_sentinel

    monkeypatch.setenv(COMPLETIONS_PROVIDER_ENV, "litellm")
    assert _build_completions_model_provider() is litellm_sentinel

    monkeypatch.setenv(COMPLETIONS_PROVIDER_ENV, "  AnyLLM  ")
    assert _build_completions_model_provider() is anyllm_sentinel


@pytest.mark.completions_runner_internal
def test_completions_provider_flag_rejects_unknown_backend(monkeypatch):
    monkeypatch.setenv(COMPLETIONS_PROVIDER_ENV, "bogus")
    with pytest.raises(ValueError):
        _build_completions_model_provider()


@pytest.mark.completions_runner_internal
def test_completions_runner_forwards_run_config_and_reconstructs_input_from_continuation_state():
    action_log_repo = MagicMock()
    run_config = MagicMock(name="run_config")
    runner = CompletionsAgentRunner(
        action_log_repository=action_log_repo,
        run_config=run_config,
    )
    run_result = MagicMock()

    continuation_state = CompletionsRunContinuationState(
        run_state=SimpleNamespace(turn="resume"),
        agent_state=SimpleNamespace(name="agent"),
        replay_items=[
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "hello"}],
                "provider_data": {"tool_calls": [{"id": "call-1"}]},
                "id": "msg_1",
                "status": "completed",
            },
            {
                "type": "function_call",
                "call_id": "call-1",
                "name": "search_positions",
                "arguments": "{}",
                "provider_data": {"debug": True},
            },
            {
                "type": "function_call_output",
                "call_id": "call-1",
                "output": '{"ok": true}',
                "provider_data": {"debug": True},
            },
        ],
        usage={"total_tokens": 5},
    )

    with patch(
        "services.chat.llm_runner.Runner.run_streamed", return_value=run_result
    ) as mock_run:
        input_items = [{"type": "message"}]
        stream = runner.run_streamed(
            starting_agent=MagicMock(),
            input=input_items,
            continuation_state=continuation_state,
        )

    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["run_config"] is run_config
    assert mock_run.call_args.kwargs["input"] == [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "hello"}],
        },
        {
            "type": "function_call",
            "call_id": "call-1",
            "name": "search_positions",
            "arguments": "{}",
        },
        {
            "type": "function_call_output",
            "call_id": "call-1",
            "output": '{"ok": true}',
        },
        {"type": "message"},
    ]
    assert isinstance(stream, CompletionsRunStream)


@pytest.mark.completions_runner_internal
def test_completions_runner_extract_replay_items_returns_empty_for_none():
    runner = CompletionsAgentRunner(
        action_log_repository=MagicMock(),
        run_config=MagicMock(name="run_config"),
    )

    assert runner._extract_replay_items(None) == []


@pytest.mark.completions_runner_internal
@pytest.mark.asyncio
async def test_completions_run_stream_rewrites_dict_tool_item_with_call_id_key_stability():
    fake_tool_call_item = SimpleNamespace(
        raw_item={
            "id": "__fake_id__",
            "call_id": "call-42",
            "name": "search_positions",
            "arguments": "{}",
        }
    )

    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})
            self.aclose = AsyncMock()

        async def stream_events(self):
            yield SimpleNamespace(
                type="run_item_stream_event", item=fake_tool_call_item
            )

        def to_state(self):
            return SimpleNamespace(turn="state")

        def to_input_list(self, mode="preserve_all"):
            return [{"type": "message", "content": "hello"}]

    stream = CompletionsRunStream(_RunResult())
    events = [event async for event in stream.stream_events()]

    assert len(events) == 1
    assert isinstance(events[0], LLMRunItemStreamEvent)
    assert events[0].item.raw_item["id"].startswith("fc_")


@pytest.mark.completions_runner_internal
def test_completions_run_stream_is_tool_call_item_true_for_toolcallitem_instance():
    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})

        def to_input_list(self, mode="preserve_all"):
            return []

    class _FakeToolCallItem:
        pass

    stream = CompletionsRunStream(_RunResult())

    with patch("services.chat.llm_runner.ToolCallItem", _FakeToolCallItem):
        assert stream._is_tool_call_item(_FakeToolCallItem(), raw_item={}) is True


@pytest.mark.completions_runner_internal
def test_completions_run_stream_is_tool_call_item_true_for_dict_function_call_type():
    class _RunResult:
        def __init__(self):
            self.last_agent = SimpleNamespace(name="completions-agent")
            self.context_wrapper = SimpleNamespace(usage={"total_tokens": 8})

        def to_input_list(self, mode="preserve_all"):
            return []

    stream = CompletionsRunStream(_RunResult())

    assert stream._is_tool_call_item(
        item=SimpleNamespace(),
        raw_item={"type": "function_call"},
    )


@pytest.mark.completions_runner_internal
def test_completions_runner_reconstructs_input_from_dict_continuation_state():
    action_log_repo = MagicMock()
    run_config = MagicMock(name="run_config")
    runner = CompletionsAgentRunner(
        action_log_repository=action_log_repo,
        run_config=run_config,
    )
    run_result = MagicMock()

    continuation_state = {
        "replay_items": [
            {
                "type": "function_call",
                "call_id": "call-1",
                "name": "search_positions",
                "arguments": "{}",
            },
            {
                "type": "function_call_output",
                "call_id": "call-1",
                "output": "ok",
            },
        ]
    }

    with patch(
        "services.chat.llm_runner.Runner.run_streamed", return_value=run_result
    ) as mock_run:
        stream = runner.run_streamed(
            starting_agent=MagicMock(),
            input=[{"type": "message", "role": "user", "content": "latest"}],
            continuation_state=continuation_state,
        )

    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["run_config"] is run_config
    assert mock_run.call_args.kwargs["input"] == [
        {
            "type": "function_call",
            "call_id": "call-1",
            "name": "search_positions",
            "arguments": "{}",
        },
        {
            "type": "function_call_output",
            "call_id": "call-1",
            "output": "ok",
        },
        {"type": "message", "role": "user", "content": "latest"},
    ]
    assert isinstance(stream, CompletionsRunStream)


@pytest.mark.completions_runner_internal
def test_completions_runner_raises_on_unsupported_continuation_state_shape():
    runner = CompletionsAgentRunner(
        action_log_repository=MagicMock(),
        run_config=MagicMock(name="run_config"),
    )

    with pytest.raises(
        TypeError,
        match="Unsupported continuation_state type.*Migration hint",
    ):
        runner.run_streamed(
            starting_agent=MagicMock(),
            input=[{"type": "message"}],
            continuation_state="legacy-state-id",
        )


@pytest.mark.completions_runner_internal
def test_completions_runner_raises_with_migration_hint_on_dict_missing_replay_items():
    runner = CompletionsAgentRunner(
        action_log_repository=MagicMock(),
        run_config=MagicMock(name="run_config"),
    )

    with pytest.raises(
        ValueError,
        match="missing 'replay_items'.*Migration hint",
    ):
        runner.run_streamed(
            starting_agent=MagicMock(),
            input=[{"type": "message"}],
            continuation_state={"run_state": "legacy"},
        )


@pytest.mark.completions_runner_internal
def test_completions_runner_raises_with_migration_hint_on_replay_items_non_list():
    runner = CompletionsAgentRunner(
        action_log_repository=MagicMock(),
        run_config=MagicMock(name="run_config"),
    )

    with pytest.raises(
        TypeError,
        match="expected list.*Migration hint",
    ):
        runner.run_streamed(
            starting_agent=MagicMock(),
            input=[{"type": "message"}],
            continuation_state={"replay_items": "not-a-list"},
        )


@pytest.mark.completions_runner_internal
def test_completions_runner_reconstructs_input_with_only_matched_tool_pairs():
    action_log_repo = MagicMock()
    run_config = MagicMock(name="run_config")
    runner = CompletionsAgentRunner(
        action_log_repository=action_log_repo,
        run_config=run_config,
    )
    run_result = MagicMock()

    continuation_state = CompletionsRunContinuationState(
        run_state=SimpleNamespace(turn="resume"),
        agent_state=SimpleNamespace(name="agent"),
        replay_items=[
            {"type": "message", "role": "assistant", "content": "a1"},
            {
                "type": "function_call",
                "call_id": "call-1",
                "name": "tool_a",
                "arguments": "{}",
            },
            {"type": "function_call_output", "call_id": "call-1", "output": "ok"},
            {
                "type": "function_call",
                "call_id": "call-2",
                "name": "tool_b",
                "arguments": "{}",
            },
            # Crossing message should clear unmatched pending tool calls for replay.
            {"type": "message", "role": "user", "content": "next"},
            # Duplicate/orphan output should be dropped.
            {"type": "function_call_output", "call_id": "call-1", "output": "dup"},
        ],
        usage={"total_tokens": 5},
    )

    with patch(
        "services.chat.llm_runner.Runner.run_streamed", return_value=run_result
    ) as mock_run:
        stream = runner.run_streamed(
            starting_agent=MagicMock(),
            input=[{"type": "message", "role": "user", "content": "latest"}],
            continuation_state=continuation_state,
        )

    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["run_config"] is run_config
    assert mock_run.call_args.kwargs["input"] == [
        {"type": "message", "role": "assistant", "content": "a1"},
        {
            "type": "function_call",
            "call_id": "call-1",
            "name": "tool_a",
            "arguments": "{}",
        },
        {"type": "function_call_output", "call_id": "call-1", "output": "ok"},
        {"type": "message", "role": "user", "content": "next"},
        {"type": "message", "role": "user", "content": "latest"},
    ]
    assert isinstance(stream, CompletionsRunStream)


@pytest.mark.completions_runner_internal
def test_completions_runner_logs_warning_for_function_call_without_call_id():
    action_log_repo = MagicMock()
    run_config = MagicMock(name="run_config")
    runner = CompletionsAgentRunner(
        action_log_repository=action_log_repo,
        run_config=run_config,
    )
    run_result = MagicMock()

    continuation_state = CompletionsRunContinuationState(
        run_state=SimpleNamespace(turn="resume"),
        agent_state=SimpleNamespace(name="agent"),
        replay_items=[
            {
                "type": "function_call",
                "name": "tool_a",
                "arguments": "{}",
            },
            {
                "type": "function_call_output",
                "call_id": "call-1",
                "output": "orphan",
            },
        ],
        usage={"total_tokens": 5},
    )

    with (
        patch(
            "services.chat.llm_runner.Runner.run_streamed", return_value=run_result
        ) as mock_run,
        patch.object(_CompletionsReplayUtils._logger, "warning") as mock_warning,
    ):
        stream = runner.run_streamed(
            starting_agent=MagicMock(),
            input=[{"type": "message", "role": "user", "content": "latest"}],
            continuation_state=continuation_state,
        )

    mock_run.assert_called_once()
    mock_warning.assert_called_once_with(
        "Discard function_call replay item without valid call_id"
    )
    assert mock_run.call_args.kwargs["input"] == [
        {"type": "message", "role": "user", "content": "latest"},
    ]
    assert isinstance(stream, CompletionsRunStream)


@pytest.mark.completions_runner_internal
def test_completions_runner_prefers_input_function_call_output_for_same_call_id():
    action_log_repo = MagicMock()
    run_config = MagicMock(name="run_config")
    runner = CompletionsAgentRunner(
        action_log_repository=action_log_repo,
        run_config=run_config,
    )
    run_result = MagicMock()

    continuation_state = CompletionsRunContinuationState(
        run_state=SimpleNamespace(turn="resume"),
        agent_state=SimpleNamespace(name="agent"),
        replay_items=[
            {
                "type": "function_call",
                "call_id": "call-1",
                "name": "search_job_postings",
                "arguments": "{}",
            },
            {
                "type": "function_call_output",
                "call_id": "call-1",
                "output": '{"AllPositionIds":[1,2,3]}',
            },
        ],
        usage={"total_tokens": 5},
    )

    with patch(
        "services.chat.llm_runner.Runner.run_streamed", return_value=run_result
    ) as mock_run:
        stream = runner.run_streamed(
            starting_agent=MagicMock(),
            input=[
                {
                    "type": "function_call_output",
                    "call_id": "call-1",
                    "output": "fake-output-from-conversation",
                },
                {"type": "message", "role": "user", "content": "latest"},
            ],
            continuation_state=continuation_state,
        )

    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["run_config"] is run_config
    assert mock_run.call_args.kwargs["input"] == [
        {
            "type": "function_call",
            "call_id": "call-1",
            "name": "search_job_postings",
            "arguments": "{}",
        },
        {
            "type": "function_call_output",
            "call_id": "call-1",
            "output": "fake-output-from-conversation",
        },
        {"type": "message", "role": "user", "content": "latest"},
    ]
    assert isinstance(stream, CompletionsRunStream)


@pytest.mark.completions_runner_internal
def test_completions_runner_preserves_non_dict_replay_items_as_boundaries():
    action_log_repo = MagicMock()
    run_config = MagicMock(name="run_config")
    runner = CompletionsAgentRunner(
        action_log_repository=action_log_repo,
        run_config=run_config,
    )
    run_result = MagicMock()
    sentinel = SimpleNamespace(kind="sdk-sentinel")

    continuation_state = CompletionsRunContinuationState(
        run_state=SimpleNamespace(turn="resume"),
        agent_state=SimpleNamespace(name="agent"),
        replay_items=[
            {
                "type": "message",
                "role": "assistant",
                "content": "before",
            },
            {
                "type": "function_call",
                "call_id": "call-2",
                "name": "tool_b",
                "arguments": "{}",
            },
            sentinel,
            {
                "type": "function_call_output",
                "call_id": "call-2",
                "output": "stale",
            },
            {
                "type": "message",
                "role": "user",
                "content": "after",
            },
        ],
        usage={"total_tokens": 5},
    )

    with patch(
        "services.chat.llm_runner.Runner.run_streamed", return_value=run_result
    ) as mock_run:
        stream = runner.run_streamed(
            starting_agent=MagicMock(),
            input=[{"type": "message", "role": "user", "content": "latest"}],
            continuation_state=continuation_state,
        )

    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["run_config"] is run_config
    assert mock_run.call_args.kwargs["input"] == [
        {"type": "message", "role": "assistant", "content": "before"},
        sentinel,
        {"type": "message", "role": "user", "content": "after"},
        {"type": "message", "role": "user", "content": "latest"},
    ]
    assert isinstance(stream, CompletionsRunStream)


@pytest.mark.completions_runner_internal
def test_completions_runner_drops_pending_tool_pair_across_non_dict_boundary():
    action_log_repo = MagicMock()
    run_config = MagicMock(name="run_config")
    runner = CompletionsAgentRunner(
        action_log_repository=action_log_repo,
        run_config=run_config,
    )
    run_result = MagicMock()
    sentinel = SimpleNamespace(kind="sdk-boundary")

    continuation_state = CompletionsRunContinuationState(
        run_state=SimpleNamespace(turn="resume"),
        agent_state=SimpleNamespace(name="agent"),
        replay_items=[
            {
                "type": "function_call",
                "call_id": "call-3",
                "name": "tool_c",
                "arguments": "{}",
            },
            sentinel,
            {
                "type": "function_call_output",
                "call_id": "call-3",
                "output": "stale",
            },
        ],
        usage={"total_tokens": 5},
    )

    with patch(
        "services.chat.llm_runner.Runner.run_streamed", return_value=run_result
    ) as mock_run:
        stream = runner.run_streamed(
            starting_agent=MagicMock(),
            input=[{"type": "message", "role": "user", "content": "latest"}],
            continuation_state=continuation_state,
        )

    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["run_config"] is run_config
    assert mock_run.call_args.kwargs["input"] == [
        sentinel,
        {"type": "message", "role": "user", "content": "latest"},
    ]
    assert isinstance(stream, CompletionsRunStream)
