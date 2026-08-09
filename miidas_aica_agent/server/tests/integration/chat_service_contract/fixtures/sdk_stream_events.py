"""SDK-shaped runner fixtures for the legacy runner contract."""

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Iterable


@dataclass(frozen=True)
class FakeStreamEvent:
    type: str
    data: Any = None
    item: Any = None


SDK_USAGE_RESPONSE = {
    "input_tokens": 12,
    "output_tokens": 34,
    "total_tokens": 46,
}

STOP_AT_TOOL_REPLAY_ITEMS = [
    {
        "type": "function_call_output",
        "call_id": "tool-call-1",
        "output": "tool output replay",
    },
]

SDK_STREAM_EVENTS = (
    FakeStreamEvent(
        type="raw_response_event",
        data=SimpleNamespace(
            type="response.output_text.delta",
            item_id="response-1",
            delta="こんにちは",
        ),
    ),
    FakeStreamEvent(
        type="run_item_stream_event",
        item=SimpleNamespace(
            type="message_output_item",
            item_id="message-1",
            role="assistant",
            content="こんにちは",
        ),
    ),
    FakeStreamEvent(
        type="run_item_stream_event",
        item=SimpleNamespace(
            type="tool_call_item",
            call_id="tool-call-1",
            name="jobtype_search_by_keywords",
            arguments='{"SessionID":"session-1","RequestID":"request-1"}',
        ),
    ),
)


class FakeRunResult:
    def __init__(
        self,
        events: Iterable[FakeStreamEvent],
        *,
        input_list: Iterable[dict[str, Any]] | None = None,
        usage: dict[str, int] | None = None,
    ) -> None:
        self._events = tuple(events)
        self._input_list = (
            list(STOP_AT_TOOL_REPLAY_ITEMS) if input_list is None else list(input_list)
        )
        self.usage = SDK_USAGE_RESPONSE if usage is None else usage

    async def stream_events(self):
        for event in self._events:
            yield event

    def to_input_list(self):
        return list(self._input_list)


def build_run_result(
    *,
    input_list: Iterable[dict[str, Any]] | None = None,
    usage: dict[str, int] | None = None,
) -> FakeRunResult:
    return FakeRunResult(
        SDK_STREAM_EVENTS,
        input_list=input_list,
        usage=usage,
    )
