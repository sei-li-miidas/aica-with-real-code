"""
Refactored bootstrap shell テスト。

テストケース一覧:
- test_real_refactored_shell_streams_runner_events_and_preserves_bootstrap_state
    対象: real-refactored shell が runner event をそのまま stream し、
    bootstrap で初期化した state を保持したまま継続できること。
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from .chat_service_contract_helpers import (
    _attach_run_with_retry_passthrough,
    _get_active_agent_name,
    _inner,
)
from services.chat.llm_runner import (
    LLMRawResponseEvent,
    LLMRunItemStreamEvent,
)
from utils.const import MAIN_CHAT_KEY
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType
from utils.enum import PageName
from utils.log_utils import clear_session_id, set_session_id


pytestmark = [pytest.mark.pre_extraction_bootstrap, pytest.mark.pre_extraction_parity]

_SESSION_ID = "phase4-bootstrap-real-refactored"


@pytest.fixture(autouse=True)
def session_scope():
    set_session_id(_SESSION_ID)
    yield
    clear_session_id()


class _FakeRunStream:
    def __init__(self, events, *, continuation_state, agent_state, replay_items, usage):
        self._events = list(events)
        self.continuation_state = continuation_state
        self.agent_state = agent_state
        self.replay_items = list(replay_items)
        self.usage = usage
        self.closed = False

    async def stream_events(self):
        for event in self._events:
            yield event

    async def aclose(self):
        self.closed = True


def _make_request() -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        position_id=None,
        message="こんにちは",
        current_message_id="msg-phase4-bootstrap",
    )


@pytest.mark.asyncio
async def test_real_refactored_shell_streams_runner_events_and_preserves_bootstrap_state(
    real_refactored_chat_service_container,
    monkeypatch,
):
    chat_svc = real_refactored_chat_service_container
    inner = _inner(chat_svc)
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    # StreamGuard が llm_output_guard を使うため、バッファリングなしのパススルーモックに差し替える。
    # このテストはセキュリティ検知ではなく stream event の流れと bootstrap state を検証するため。
    passthrough_guard = MagicMock()
    passthrough_guard.reset_session_for_new_response.return_value = None
    passthrough_guard.process_stream_chunk.side_effect = lambda session_id, chunk: [
        chunk
    ]
    passthrough_guard.finalize_stream.return_value = []
    passthrough_guard.remove_session.return_value = None
    inner.llm_output_guard = passthrough_guard
    # chat_service_refactored.chat() uses self.llm_output_guard (direct alias set at __init__).
    # Update the alias directly so StreamGuard uses the passthrough mock.
    chat_svc.llm_output_guard = passthrough_guard

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    inner._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    inner._position_service.current_search_filter = AsyncMock(return_value=None)

    status, is_new_session = await chat_svc.init_session("gpt-4o")

    assert status.name == "CHATTING"
    assert is_new_session is True

    stop_at_tool_agent = SimpleNamespace(
        tool_use_behavior={"stop_at_tool_names": ["jobtype_search_by_keywords"]}
    )
    tool_call_item = SimpleNamespace(
        call_id="tool-call-1",
        raw_item=SimpleNamespace(name="jobtype_search_by_keywords"),
        agent=stop_at_tool_agent,
    )
    run_stream = _FakeRunStream(
        [
            LLMRawResponseEvent(item_id="resp-item-1", delta="こんにちは"),
            LLMRunItemStreamEvent(item=tool_call_item),
        ],
        continuation_state="resp-next",
        agent_state=SimpleNamespace(name="handoff-agent"),
        replay_items=[
            {
                "type": "function_call_output",
                "call_id": "tool-call-1",
                "output": "tool output replay",
            }
        ],
        usage={"input_tokens": 12, "output_tokens": 34, "total_tokens": 46},
    )
    chat_svc._llm_runner = MagicMock(
        return_value=None,
    )
    chat_svc._llm_runner.run_streamed.return_value = run_stream

    _attach_run_with_retry_passthrough(
        chat_svc._llm_runner,
        action_log_repository=inner._action_log_repository,
        usage_content_builder=str,
    )

    responses = [
        response.model_copy(deep=True)
        async for response in chat_svc.chat(_make_request(), "127.0.0.1")
    ]

    assert [response.response_type for response in responses] == [
        ChatResponseType.MESSAGE,
        ChatResponseType.END,
    ]
    assert responses[0].message_id == "resp-item-1"
    assert responses[0].message == "こんにちは"
    saved_histories = [
        history
        for call in inner._chat_repository.add_chat_histories.call_args_list
        for history in call.args[0]
    ]
    assert any(
        history.message_id == "msg-phase4-bootstrap" and history.content == "こんにちは"
        for history in saved_histories
    )
    # TurnPreparer 抽出後は _conv_state が権威: previous_continuation_states / conversation は
    # legacy との alias ではなく独立したコピーになった。
    assert (
        chat_svc._conv_state.previous_continuation_states[MAIN_CHAT_KEY] == "resp-next"
    )
    assert _get_active_agent_name(inner) == "handoff-agent"
    assert chat_svc._conv_state.conversation[MAIN_CHAT_KEY] == [
        {
            "type": "function_call_output",
            "call_id": "tool-call-1",
            "output": "tool output replay",
        }
    ]
    inner._action_log_repository.insert.assert_called_once()
    assert chat_svc.__class__.__module__ == "services.chat_service_refactored"
    assert run_stream.closed is True
