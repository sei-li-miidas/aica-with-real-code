import asyncio
import json
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from repositories.action_log_repo import ActionLogType
from security.llm_output_guard import LLMOutputGuard
from services.chat.chat_persistence import _serialize_tool_output_for_storage
from services.chat.tool_event_handler import (
    PositionSearchRateLimitExceeded,
    RetryableToolOutputFailure,
)
from services.chat.llm_runner import (
    LLMIgnoredStreamEvent,
    LLMRawResponseEvent,
    LLMRetryChunkEvent,
    LLMRetryCompleteEvent,
    LLMRunItemStreamEvent,
    LLMRunWithRetryResult,
    _normalize_stream_event,
    json_default,
)
from services.chat.service_protocol import ChatServiceProtocol
from services.chat_service_refactored import (
    ChatService,
    json_default as ref_json_default,
)
from services.llm_service import AgentName
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType
from utils.const import INITIAL_MENU_WORKFLOW_ID, MAIN_CHAT_KEY
from utils.enum import PageName, ToolName
from utils.log_utils import clear_session_id, set_session_id


class _FakeRunStream:
    def __init__(
        self,
        events,
        *,
        continuation_state=None,
        agent_state=None,
        replay_items=None,
        usage=None,
    ):
        self._events = list(events)
        self.continuation_state = continuation_state
        self.agent_state = agent_state
        self.replay_items = [] if replay_items is None else list(replay_items)
        self.usage = usage
        self.closed = False

    async def stream_events(self):
        for event in self._events:
            yield event

    async def aclose(self):
        self.closed = True


class _FailingRunStream(_FakeRunStream):
    def __init__(self, exc: BaseException):
        super().__init__(
            [],
            continuation_state="resp-next",
            agent_state=SimpleNamespace(name="handoff-agent"),
            replay_items=[],
            usage=None,
        )
        self._exc = exc

    async def stream_events(self):
        if False:
            yield None
        raise self._exc


@pytest.fixture(autouse=True)
def session_scope():
    set_session_id("test-session-refactored")
    yield
    clear_session_id()


@pytest.fixture(autouse=True)
def mock_retry_sleep(monkeypatch):
    """Prevent the retry loop's exponential backoff from sleeping for real.

    chat_service_refactored.py retries up to MAX_LLM_RETRY_COUNT=5 times with
    asyncio.sleep delays (0.5s, 1.0s, 2.0s, 4.0s = 7.5s total). Without this
    fixture every test that triggers an error in the streaming path would block
    for 7.5 seconds of real wall-clock time, causing the test suite to appear
    frozen and accumulate significant memory from asyncio state.
    """
    monkeypatch.setattr(
        "services.chat_service_refactored.asyncio.sleep",
        AsyncMock(),
    )


@pytest.fixture
def chat_service():
    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}

    position_svc = MagicMock()
    position_svc.current_search_filter = AsyncMock(return_value=None)
    llm_svc = MagicMock()
    llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    chat_repository = MagicMock()
    chat_repository.init_chat_session.return_value = (None, False)
    chat_repository.session_status.return_value = ChatSessionStatus.CHATTING
    chat_repository.is_session_blocked.return_value = False
    action_log_repository = MagicMock()
    llm_runner = MagicMock()
    conversation_summary_svc = MagicMock()

    # Set up run_with_retry as an async iterator that wraps run_streamed behavior
    # and simulates usage recording.
    async def run_with_retry_impl(*args, **kwargs):
        process_stream = kwargs["process_stream"]
        on_before_attempt = kwargs.get("on_before_attempt")
        on_after_attempt = kwargs.get("on_after_attempt")
        on_retryable_error = kwargs.get("on_retryable_error")
        on_non_retryable_error = kwargs.get("on_non_retryable_error")

        starting_agent = kwargs.get("starting_agent")
        input_items = kwargs.get("input")
        chat_key = kwargs.get("chat_key")
        continuation_state = kwargs.get("continuation_state")
        continuation_state_supplier = kwargs.get("continuation_state_supplier")
        message_id = kwargs.get("message_id")

        last_usage = None
        for attempt in range(5):
            try:
                if on_before_attempt is not None:
                    await on_before_attempt()

                stream = llm_runner.run_streamed(
                    starting_agent=starting_agent,
                    input=input_items,
                    continuation_state=(
                        continuation_state_supplier()
                        if continuation_state_supplier is not None
                        else continuation_state
                    ),
                )
                if stream is None:
                    raise RuntimeError("stream unavailable")

                usage = getattr(stream, "usage", None)
                last_usage = usage
                if usage is not None and message_id:
                    try:
                        token_usage_str = json.dumps(usage)
                        action_log_repository.insert(
                            log_type=ActionLogType.TOKEN_USAGE,
                            source=message_id,
                            content=token_usage_str,
                        )
                    except Exception:
                        pass

                async for chunk in process_stream(stream):
                    yield LLMRetryChunkEvent(chunk=chunk)

                yield LLMRetryCompleteEvent(
                    result=LLMRunWithRetryResult(
                        succeeded=True,
                        attempts=attempt + 1,
                        usage=usage,
                        error=None,
                    )
                )
                return
            except RetryableToolOutputFailure as exc:
                if on_retryable_error is not None:
                    await on_retryable_error(exc)
                if attempt >= 4:
                    yield LLMRetryCompleteEvent(
                        result=LLMRunWithRetryResult(
                            succeeded=False,
                            attempts=attempt + 1,
                            usage=last_usage,
                            error=exc,
                        )
                    )
                    return
                continue
            except Exception as exc:
                if on_non_retryable_error is not None:
                    await on_non_retryable_error(exc)
                yield LLMRetryCompleteEvent(
                    result=LLMRunWithRetryResult(
                        succeeded=False,
                        attempts=attempt + 1,
                        usage=last_usage,
                        error=exc,
                    )
                )
                return
            finally:
                if on_after_attempt is not None:
                    await on_after_attempt()

    llm_runner.run_with_retry = run_with_retry_impl

    service = ChatService(
        position_svc=position_svc,
        llm_svc=llm_svc,
        chat_repository=chat_repository,
        position_repository=MagicMock(),
        user_repository=MagicMock(),
        action_log_repository=action_log_repository,
        rate_limit_service=MagicMock(),
        workflow_service=MagicMock(),
        llm_runner=llm_runner,
        conversation_summary_svc=conversation_summary_svc,
    )
    # Protocol 構造的適合を早期に検出するため、フィクスチャ生成時にアサートする。
    assert isinstance(service, ChatServiceProtocol)
    return service


def _make_request(
    *,
    request_type: ChatRequestType = ChatRequestType.CHAT,
    current_page: PageName = PageName.CHAT,
    position_id: str | None = None,
    message: str = "こんにちは",
) -> ChatRequestModel:
    return ChatRequestModel(
        request_type=request_type,
        current_page=current_page,
        position_id=position_id,
        message=message,
        current_message_id="msg-refactored-unit",
    )


async def _collect(chat_service, request):
    return [
        response.model_copy(deep=True)
        async for response in chat_service.chat(request, "127.0.0.1")
    ]


def test_constructor_uses_injected_or_default_llm_output_guard_and_summary_service():
    injected_guard = Mock(spec=LLMOutputGuard)
    injected_summary_service = Mock()

    injected_service = ChatService(
        position_svc=Mock(),
        llm_svc=Mock(),
        chat_repository=Mock(),
        position_repository=Mock(),
        user_repository=Mock(),
        action_log_repository=Mock(),
        rate_limit_service=Mock(),
        workflow_service=Mock(),
        llm_runner=Mock(),
        conversation_summary_svc=Mock(),
        llm_output_guard=injected_guard,
        summary_service=injected_summary_service,
    )
    default_service = ChatService(
        position_svc=Mock(),
        llm_svc=Mock(),
        chat_repository=Mock(),
        position_repository=Mock(),
        user_repository=Mock(),
        action_log_repository=Mock(),
        rate_limit_service=Mock(),
        workflow_service=Mock(),
        llm_runner=Mock(),
        conversation_summary_svc=Mock(),
    )

    assert injected_service.llm_output_guard is injected_guard
    assert injected_service._summary_service is injected_summary_service
    assert isinstance(default_service.llm_output_guard, LLMOutputGuard)
    assert default_service._summary_service is None


def test_find_last_non_position_guide_agent_returns_none_when_history_has_only_position_guide(
    chat_service,
):
    chat_service._conv_state.active_agent_name = AgentName.CAREER_ADVISOR
    chat_service._agents[AgentName.CAREER_ADVISOR] = MagicMock()
    chat_service._conv_state.chat_histories[MAIN_CHAT_KEY] = [
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent=AgentName.POSITION_GUIDE,
            message_id="hist-1",
            role="developer",
            content="summary",
        )
    ]

    resumed_agent = chat_service._find_last_non_position_guide_agent()

    assert resumed_agent is None


@pytest.mark.asyncio
async def test_init_session_returns_error_when_main_history_has_only_position_guide(
    chat_service,
):
    default_agent = MagicMock()
    default_agent.name = AgentName.CAREER_ADVISOR
    position_guide_agent = MagicMock()
    position_guide_agent.name = AgentName.POSITION_GUIDE
    chat_service._llm_svc.clone_agents.return_value = {
        AgentName.CAREER_ADVISOR: (default_agent, True),
        AgentName.POSITION_GUIDE: (position_guide_agent, False),
    }
    chat_service._chat_repository.init_chat_session.return_value = (
        SimpleNamespace(
            histories=[
                ChatHistory(
                    session_id="sess",
                    position_id=None,
                    active_agent=AgentName.POSITION_GUIDE,
                    message_id="hist-1",
                    role="developer",
                    content="summary",
                )
            ],
            status=ChatSessionStatus.CHATTING,
        ),
        False,
    )

    status, is_new_session = await chat_service.init_session("gpt-4o")

    assert status == ChatSessionStatus.ERROR
    assert is_new_session is False
    assert chat_service._conv_state.active_agent_name == AgentName.CAREER_ADVISOR


def test_create_position_agent_if_not_exist_skips_when_position_guide_agent_missing(
    chat_service,
):
    chat_service._agents.clear()

    chat_service._create_position_agent_if_not_exist("position-1")

    assert "position-1" not in chat_service._agents


def test_normalize_stream_event_ignores_raw_event_without_item_id():
    event = SimpleNamespace(
        type="raw_response_event",
        data=SimpleNamespace(item_id="", delta="hello"),
    )

    normalized = _normalize_stream_event(event)

    assert normalized == LLMIgnoredStreamEvent()


@pytest.mark.asyncio
async def test_init_session_populates_conv_state(chat_service):
    """init_session() はネイティブ実装であり、_conv_state を直接設定する。

    task-5-legacy-dependency-removal: legacy へ委譲しない。
    """
    status, is_new_session = await chat_service.init_session("gpt-4o")

    assert status == ChatSessionStatus.CHATTING
    assert is_new_session is True
    # _conv_state が直接設定されること
    assert chat_service._conv_state.model_name == "gpt-4o"
    assert chat_service._conv_state.active_agent_name == "CareerAdvisor"
    assert MAIN_CHAT_KEY in chat_service._conv_state.conversation
    assert chat_service._conv_state.chat_key == MAIN_CHAT_KEY


@pytest.mark.asyncio
async def test_init_session_has_no_legacy_chat_service(chat_service):
    """task-5-legacy-dependency-removal: LegacyChatService を持たないことを確認する。"""
    assert not hasattr(chat_service, "_legacy_chat_service"), (
        "_legacy_chat_service must not exist after task-5 removal"
    )


@pytest.mark.asyncio
async def test_chat_returns_error_for_blocked_session(chat_service):
    chat_service._chat_repository.is_session_blocked.return_value = True

    responses = await _collect(chat_service, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR


@pytest.mark.asyncio
# ChatService line — REGISTERING と APPLYING の両方を short-circuit する。
@pytest.mark.parametrize(
    "blocked_status",
    [ChatSessionStatus.REGISTERING, ChatSessionStatus.APPLYING],
)
async def test_chat_short_circuits_start_request_for_registering_or_applying_sessions(
    chat_service, blocked_status
):
    chat_service._chat_repository.session_status.return_value = blocked_status

    responses = await _collect(
        chat_service,
        _make_request(request_type=ChatRequestType.START),
    )

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END
    assert responses[0].session_status == blocked_status


@pytest.mark.asyncio
async def test_chat_returns_end_when_prepare_does_not_populate_conversation(
    chat_service,
):
    await chat_service.init_session("gpt-4o")

    async def _clear_conversation(request):
        chat_service._conv_state.conversation.pop(MAIN_CHAT_KEY, None)

    chat_service._turn_preparer.prepare_turn = _clear_conversation

    responses = await _collect(chat_service, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END


@pytest.mark.asyncio
async def test_chat_uses_conv_state_chat_key_set_by_turn_preparer(
    chat_service, monkeypatch
):
    """TurnPreparer が _conv_state.chat_key / position_id / active_agent_name を
    直接更新した場合、chat() がその値を使って runner を呼ぶことを確認する。
    """
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")

    MUTATED_CHAT_KEY = "position-abc123"
    MUTATED_POSITION_ID = "position-abc123"
    MUTATED_AGENT = "CareerAdvisor"  # _agents に存在するエージェント名

    async def _fake_prepare(request):
        # TurnPreparer が直接 _conv_state を更新する動作を再現
        chat_service._conv_state.active_agent_name = MUTATED_AGENT
        chat_service._conv_state.chat_key = MUTATED_CHAT_KEY
        chat_service._conv_state.position_id = MUTATED_POSITION_ID
        chat_service._conv_state.conversation.pop(MAIN_CHAT_KEY, None)
        # 空でない conversation を設定して runner 呼び出しに到達させる。
        chat_service._conv_state.conversation[MUTATED_CHAT_KEY] = [
            SimpleNamespace(type="message", role="user", content="prefilled")
        ]

    chat_service._turn_preparer.prepare_turn = _fake_prepare
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage=None,
    )

    responses = await _collect(chat_service, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END
    run_call = chat_service._llm_runner.run_streamed.call_args
    assert run_call is not None
    # Verify that run_streamed was called with input from the correct (mutated) chat_key
    input_passed = run_call.kwargs["input"]
    assert len(input_passed) >= 1
    # First item should be the prefilled message set by TurnPreparer
    assert input_passed[0].type == "message"
    assert chat_service._conv_state.chat_key == MUTATED_CHAT_KEY
    assert chat_service._conv_state.position_id == MUTATED_POSITION_ID
    assert chat_service._conv_state.active_agent_name == MUTATED_AGENT


@pytest.mark.asyncio
async def test_chat_streams_runner_events_and_records_usage(chat_service, monkeypatch):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    # StreamGuard が llm_output_guard を使うため、バッファリングなしのパススルーモックに差し替える。
    passthrough_guard = MagicMock()
    passthrough_guard.reset_session_for_new_response.return_value = None
    passthrough_guard.process_stream_chunk.side_effect = lambda session_id, chunk: [
        chunk
    ]
    passthrough_guard.finalize_stream.return_value = []
    passthrough_guard.remove_session.return_value = None
    chat_service.llm_output_guard = passthrough_guard
    await chat_service.init_session("gpt-4o")

    stop_at_tool_agent = SimpleNamespace(
        tool_use_behavior={"stop_at_tool_names": ["jobtype_search_by_keywords"]}
    )
    tool_call_item = SimpleNamespace(
        call_id="tool-call-1",
        raw_item=SimpleNamespace(name="jobtype_search_by_keywords"),
        agent=stop_at_tool_agent,
    )
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [
            LLMRawResponseEvent(item_id="resp-1", delta="hello"),
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
        usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
    )

    responses = await _collect(chat_service, _make_request())

    assert [response.response_type for response in responses] == [
        ChatResponseType.MESSAGE,
        ChatResponseType.END,
    ]
    assert responses[0].message == "hello"
    # continuation_state と stop-at-tool replay は _conv_state に書かれる。
    assert (
        chat_service._conv_state.previous_continuation_states[MAIN_CHAT_KEY]
        == "resp-next"
    )
    assert chat_service._conv_state.active_agent_name == "handoff-agent"
    assert chat_service._conv_state.conversation[MAIN_CHAT_KEY] == [
        {
            "type": "function_call_output",
            "call_id": "tool-call-1",
            "output": "tool output replay",
        }
    ]
    chat_service._action_log_repository.insert.assert_called_once_with(
        log_type=ActionLogType.TOKEN_USAGE,
        source="msg-refactored-unit",
        content='{"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}',
    )


@pytest.mark.asyncio
async def test_chat_flushes_guard_buffer_before_end(chat_service, monkeypatch):
    """StreamGuard の finalize() で保留バッファが解放され END の前に届くことを検証する。"""
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    buffering_guard = MagicMock()
    buffering_guard.reset_session_for_new_response.return_value = None
    buffering_guard.process_stream_chunk.return_value = []
    buffering_guard.finalize_stream.return_value = ["buffered_tail"]
    buffering_guard.remove_session.return_value = None
    chat_service.llm_output_guard = buffering_guard
    await chat_service.init_session("gpt-4o")

    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [LLMRawResponseEvent(item_id="resp-1", delta="hello")],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage=None,
    )

    responses = await _collect(chat_service, _make_request())

    types = [r.response_type for r in responses]
    assert types == [ChatResponseType.MESSAGE, ChatResponseType.END]
    assert responses[0].message == "buffered_tail"


@pytest.mark.asyncio
async def test_chat_rebuilds_summary_context_and_starts_summary_when_configured(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")

    summary_service = Mock()
    chat_service._summary_service = summary_service
    chat_service._build_summary_context = AsyncMock()
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage=None,
    )

    responses = await _collect(chat_service, _make_request(message="summary-turn"))

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END
    chat_service._build_summary_context.assert_called_once_with(
        "test-session-refactored"
    )
    summary_service.check_should_start_summary.assert_called_once_with(
        "test-session-refactored"
    )


@pytest.mark.asyncio
async def test_chat_rebuilds_summary_context_even_without_summary_service(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")

    chat_service._summary_service = None
    chat_service._build_summary_context = AsyncMock()
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage=None,
    )

    responses = await _collect(chat_service, _make_request(message="summary-none"))

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END
    chat_service._build_summary_context.assert_called_once_with(
        "test-session-refactored"
    )


@pytest.mark.asyncio
async def test_chat_skips_summary_context_rebuild_when_continuation_exists(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")

    summary_service = Mock()
    chat_service._summary_service = summary_service
    chat_service._conv_state.previous_continuation_states[MAIN_CHAT_KEY] = "resp-prev"
    chat_service._build_summary_context = AsyncMock()
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage=None,
    )

    responses = await _collect(chat_service, _make_request(message="continue"))

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END
    chat_service._build_summary_context.assert_not_called()
    summary_service.check_should_start_summary.assert_called_once_with(
        "test-session-refactored"
    )


@pytest.mark.asyncio
async def test_chat_continues_when_summary_context_rebuild_fails(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")

    summary_service = Mock()
    chat_service._summary_service = summary_service
    chat_service._build_summary_context = AsyncMock(side_effect=RuntimeError("boom"))
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage=None,
    )

    responses = await _collect(chat_service, _make_request(message="summary-fail"))

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END
    summary_service.check_should_start_summary.assert_called_once_with(
        "test-session-refactored"
    )


@pytest.mark.asyncio
async def test_build_summary_context_uses_boundary_fallback_and_filters_tool_trace(
    chat_service,
):
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._summary_service = Mock()
    chat_service._summary_service.get_latest_completed.return_value = SimpleNamespace(
        summary_until_history_id="invalid-boundary",
        summary_text="summary text",
    )
    chat_service._summary_service.get_histories_after.return_value = [Mock()]

    chat_service._toolcall_trace_message = {
        "type": "message",
        "role": "developer",
        "content": "trace-content",
    }
    chat_service._history_mapper.convert_to_llm_messages = Mock(
        return_value=(
            {MAIN_CHAT_KEY: [Mock()]},
            {
                MAIN_CHAT_KEY: [
                    {
                        "type": "message",
                        "role": "developer",
                        "content": "trace-content",
                    },
                    {
                        "type": "message",
                        "role": "developer",
                        "content": "keep-content",
                    },
                ]
            },
        )
    )

    await chat_service._build_summary_context("test-session-refactored")

    chat_service._summary_service.get_histories_after.assert_called_once_with(
        "test-session-refactored",
        0,
    )
    rebuilt = chat_service._conv_state.conversation[MAIN_CHAT_KEY]
    assert rebuilt[0] == chat_service._toolcall_trace_message
    assert any(
        isinstance(item, dict)
        and isinstance(item.get("content"), str)
        and "###過去会話の要約" in item["content"]
        for item in rebuilt
    )
    assert any(
        isinstance(item, dict) and item.get("content") == "keep-content"
        for item in rebuilt
    )
    assert not any(
        isinstance(item, dict)
        and item is not chat_service._toolcall_trace_message
        and item.get("content") == "trace-content"
        for item in rebuilt
    )


@pytest.mark.asyncio
async def test_chat_emits_local_dev_token_usage_response(chat_service, monkeypatch):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: True
    )
    await chat_service.init_session("gpt-4o")
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
    )

    responses = await _collect(chat_service, _make_request())

    assert [response.response_type for response in responses] == [
        ChatResponseType.MESSAGE,
        ChatResponseType.END,
    ]
    assert (
        responses[0].message
        == '\nToken Usage: {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}'
    )


@pytest.mark.asyncio
async def test_chat_continues_when_usage_logging_fails(chat_service, monkeypatch):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
    )
    chat_service._action_log_repository.insert.side_effect = RuntimeError(
        "usage write failed"
    )

    responses = await _collect(chat_service, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END


@pytest.mark.asyncio
async def test_chat_returns_error_when_runner_fails(chat_service):
    await chat_service.init_session("gpt-4o")
    chat_service._llm_runner.run_streamed.side_effect = RuntimeError("boom")

    responses = await _collect(chat_service, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR


@pytest.mark.asyncio
async def test_chat_closes_run_stream_after_success(chat_service, monkeypatch):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    run_stream = _FakeRunStream(
        [],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage=None,
    )
    chat_service._llm_runner.run_streamed.return_value = run_stream

    await _collect(chat_service, _make_request())

    assert run_stream.closed is True


@pytest.mark.asyncio
async def test_chat_closes_run_stream_when_event_iteration_fails(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    run_stream = _FailingRunStream(RuntimeError("event boom"))
    chat_service._llm_runner.run_streamed.return_value = run_stream

    responses = await _collect(chat_service, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR
    assert run_stream.closed is True


@pytest.mark.asyncio
async def test_chat_does_not_close_run_stream_when_event_iteration_is_cancelled(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    run_stream = _FailingRunStream(asyncio.CancelledError())
    chat_service._llm_runner.run_streamed.return_value = run_stream

    with pytest.raises(asyncio.CancelledError):
        await anext(chat_service.chat(_make_request(), "127.0.0.1"))

    assert run_stream.closed is False


def test_chat_has_no_delegate_chat_attribute(chat_service):
    """task-5-legacy-dependency-removal: _delegate_chat フラグが削除されていることを検証する。"""
    assert not hasattr(chat_service, "_delegate_chat"), (
        "_delegate_chat must not exist after task-5 removal"
    )


def test_chat_service_refactored_has_no_legacy_import():
    """task-5-legacy-dependency-removal: LegacyChatService import/instantiation が
    ソースコードに含まれないことを静的に検証する。

    - LegacyChatService シンボルが存在しない
    - _legacy_chat_service インスタンス変数が存在しない
    """
    import inspect
    import services.chat_service_refactored as module

    source = inspect.getsource(module)
    assert "LegacyChatService" not in source, (
        "LegacyChatService must not appear in chat_service_refactored.py"
    )
    assert "_legacy_chat_service" not in source, (
        "_legacy_chat_service must not appear in chat_service_refactored.py"
    )


@pytest.mark.asyncio
async def test_chat_defaults_session_status_and_ignores_non_run_item_events(
    chat_service,
):
    await chat_service.init_session("gpt-4o")
    chat_service._chat_repository.session_status.return_value = None
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [SimpleNamespace(type="ignored_event", item_id="noop", delta="noop")],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage=None,
    )

    responses = await _collect(chat_service, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END
    assert responses[0].session_status == ChatSessionStatus.CHATTING


@pytest.mark.asyncio
async def test_chat_ignores_non_stop_at_tool_run_items(chat_service):
    await chat_service.init_session("gpt-4o")
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [
            LLMRunItemStreamEvent(
                item=SimpleNamespace(
                    agent=SimpleNamespace(
                        tool_use_behavior={"stop_at_tool_names": ["other_tool"]}
                    ),
                    raw_item=SimpleNamespace(name="jobtype_search_by_keywords"),
                )
            )
        ],
        continuation_state="resp-next",
        agent_state=SimpleNamespace(),
        replay_items=[
            {
                "type": "function_call_output",
                "call_id": "tool-call-1",
                "output": "tool output replay",
            }
        ],
        usage=None,
    )

    responses = await _collect(chat_service, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.END
    assert chat_service._conv_state.conversation[MAIN_CHAT_KEY] == []


@pytest.mark.asyncio
async def test_chat_returns_error_when_prepare_fails(chat_service):
    await chat_service.init_session("gpt-4o")
    chat_service._turn_preparer.prepare_turn = AsyncMock(
        side_effect=ValueError("bad prepare")
    )

    responses = await _collect(chat_service, _make_request())

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR


@pytest.mark.asyncio
async def test_check_if_previous_chat_histories_exist_decrypts_and_queries(
    chat_service,
):
    chat_service._chat_repository.has_position_chat_histories = Mock(return_value=True)

    with patch("services.chat_service_refactored.decrypt", return_value="real-pos-id"):
        result = await chat_service.check_if_previous_chat_histories_exist("encrypted")

    assert result is True
    chat_service._chat_repository.has_position_chat_histories.assert_called_once_with(
        "real-pos-id"
    )


@pytest.mark.asyncio
async def test_load_previous_chat_histories_uses_history_mapper(chat_service):
    raw = [Mock()]
    chat_service._chat_repository.get_position_detail_chat_histories = Mock(
        return_value=raw
    )
    chat_service._history_mapper.format_previous_chat_histories = Mock(
        return_value=([{"id": "1"}], False)
    )

    with patch("services.chat_service_refactored.decrypt", return_value="real-pos-id"):
        result = await chat_service.load_previous_chat_histories(
            5, "encrypted", "before"
        )

    assert result == ([{"id": "1"}], False)
    chat_service._chat_repository.get_position_detail_chat_histories.assert_called_once_with(
        "real-pos-id", "before"
    )
    chat_service._history_mapper.format_previous_chat_histories.assert_called_once_with(
        raw, 5
    )


def _make_last_history(
    *,
    role: str = "tool",
    tool_name: str | None = ToolName.START_WORKFLOW.value,
    content: str | None = '{"WorkflowID": "wf-1"}',
) -> SimpleNamespace:
    return SimpleNamespace(
        role=role,
        tool_name=tool_name,
        content=content,
        message_id="wf-msg-1",
    )


def _setup_main_chat_histories(chat_service):
    chat_service._chat_repository.get_main_chat_histories = Mock(return_value=[Mock()])
    chat_service._history_mapper.format_previous_chat_histories = Mock(
        return_value=([{"id": "1"}], False)
    )


@pytest.mark.asyncio
async def test_load_previous_chat_histories_inserts_restart_workflow_entry(
    chat_service,
):
    """最後の履歴がstart_workflowの場合、restart_workflow要素が先頭に挿入されること。"""
    _setup_main_chat_histories(chat_service)
    chat_service._chat_repository.get_last_main_chat_history = Mock(
        return_value=_make_last_history()
    )
    definition = MagicMock()
    definition.model_dump.return_value = {"id": "wf-1", "steps": []}
    chat_service._workflow_service.get_definition = Mock(return_value=definition)

    previous, no_more = await chat_service.load_previous_chat_histories(5, None, None)

    assert previous[0] == {
        "Role": "tool",
        "Type": ChatResponseType.RESTART_WORKFLOW,
        "MessageID": "wf-msg-1",
        "Message": {"id": "wf-1", "steps": []},
    }
    assert previous[1:] == [{"id": "1"}]
    assert no_more is False
    chat_service._workflow_service.get_definition.assert_called_once_with("wf-1")
    definition.model_dump.assert_called_once_with(by_alias=True)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "last_history",
    [
        None,
        _make_last_history(role="assistant", tool_name=None),
        _make_last_history(tool_name=ToolName.GENERIC_POSITION_SEARCH.value),
        _make_last_history(content=f'{{"WorkflowID": "{INITIAL_MENU_WORKFLOW_ID}"}}'),
        _make_last_history(content="{}"),
        _make_last_history(content=None),
        _make_last_history(content=""),
    ],
    ids=[
        "no_record",
        "last_is_assistant",
        "last_is_other_tool",
        "workflow_id_is_initial_menu",
        "no_workflow_id_in_content",
        "none_content",
        "empty_string_content",
    ],
)
async def test_load_previous_chat_histories_skips_restart_entry(
    chat_service, last_history
):
    """再実行対象外の場合、restart_workflow要素が追加されないこと。"""
    _setup_main_chat_histories(chat_service)
    chat_service._chat_repository.get_last_main_chat_history = Mock(
        return_value=last_history
    )

    previous, no_more = await chat_service.load_previous_chat_histories(5, None, None)

    assert previous == [{"id": "1"}]
    assert no_more is False
    chat_service._workflow_service.get_definition.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [ValueError("bad"), FileNotFoundError("missing")])
async def test_load_previous_chat_histories_skips_restart_entry_on_definition_error(
    chat_service, error
):
    """定義取得に失敗した場合、restart_workflow要素は追加されず例外も出ないこと。"""
    _setup_main_chat_histories(chat_service)
    chat_service._chat_repository.get_last_main_chat_history = Mock(
        return_value=_make_last_history()
    )
    chat_service._workflow_service.get_definition = Mock(side_effect=error)

    previous, no_more = await chat_service.load_previous_chat_histories(5, None, None)

    assert previous == [{"id": "1"}]
    assert no_more is False


@pytest.mark.asyncio
async def test_load_previous_chat_histories_skips_restart_entry_for_past_page(
    chat_service,
):
    """before_id指定あり（過去ページ取得）の場合、判定自体を行わないこと。"""
    _setup_main_chat_histories(chat_service)
    chat_service._chat_repository.get_last_main_chat_history = Mock()

    previous, _ = await chat_service.load_previous_chat_histories(5, None, "before")

    assert previous == [{"id": "1"}]
    chat_service._chat_repository.get_last_main_chat_history.assert_not_called()


@pytest.mark.asyncio
async def test_load_previous_chat_histories_skips_restart_entry_for_position_chat(
    chat_service,
):
    """ポジション詳細チャットの場合、判定自体を行わないこと。"""
    chat_service._chat_repository.get_position_detail_chat_histories = Mock(
        return_value=[Mock()]
    )
    chat_service._history_mapper.format_previous_chat_histories = Mock(
        return_value=([{"id": "1"}], False)
    )
    chat_service._chat_repository.get_last_main_chat_history = Mock()

    with patch("services.chat_service_refactored.decrypt", return_value="real-pos-id"):
        previous, _ = await chat_service.load_previous_chat_histories(
            5, "encrypted", None
        )

    assert previous == [{"id": "1"}]
    chat_service._chat_repository.get_last_main_chat_history.assert_not_called()


def test_is_stop_at_tool_covers_false_branches(chat_service):
    assert chat_service._is_stop_at_tool(SimpleNamespace()) is False
    assert (
        chat_service._is_stop_at_tool(
            SimpleNamespace(agent=SimpleNamespace(tool_use_behavior={}))
        )
        is False
    )
    assert (
        chat_service._is_stop_at_tool(
            SimpleNamespace(
                agent=SimpleNamespace(tool_use_behavior={"stop_at_tool_names": []}),
                raw_item=SimpleNamespace(name=123),
            )
        )
        is False
    )


def test_append_stop_at_tool_outputs_covers_guard_paths(chat_service):
    # _conv_state.conversation が権威。
    chat_service._conv_state.conversation = {
        MAIN_CHAT_KEY: [SimpleNamespace(type="message")]
    }
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY

    chat_service._append_stop_at_tool_outputs([], False)
    chat_service._append_stop_at_tool_outputs(
        [{"type": "message"}],
        True,
    )
    chat_service._append_stop_at_tool_outputs(
        [{"type": "function_call_output", "call_id": 123, "output": "x"}],
        True,
    )
    chat_service._append_stop_at_tool_outputs(
        [{"type": "function_call_output", "call_id": "call-1", "output": "x"}],
        True,
    )
    chat_service._append_stop_at_tool_outputs(
        [{"type": "function_call_output", "call_id": "call-1", "output": "x"}],
        True,
    )

    assert chat_service._conv_state.conversation[MAIN_CHAT_KEY] == [
        SimpleNamespace(type="message"),
        {"type": "function_call_output", "call_id": "call-1", "output": "x"},
    ]


def test_json_default_and_serialize_tool_output(chat_service):
    @dataclass
    class Data:
        value: int

    class HasModelDump:
        def model_dump(self):
            return {"model": True}

    class HasDictAttr:
        def __init__(self):
            self.answer = 42

    class Fallback:
        __slots__ = ()

    fallback = Fallback()
    assert _serialize_tool_output_for_storage("raw") == "raw"
    assert json.loads(_serialize_tool_output_for_storage(Data(1))) == {"value": 1}
    assert json.loads(_serialize_tool_output_for_storage(HasModelDump())) == {
        "model": True
    }
    assert json.loads(_serialize_tool_output_for_storage(HasDictAttr())) == {
        "answer": 42
    }
    assert _serialize_tool_output_for_storage(fallback) == json.dumps(
        str(fallback),
        ensure_ascii=False,
    )


def test_json_default_all_branches():
    @dataclass
    class DC:
        x: int

    class WithModelDump:
        def model_dump(self):
            return {"m": 1}

    class WithDict:
        def __init__(self):
            self.v = 2

    class NoDict:
        __slots__ = ()

    assert json_default(DC(3)) == {"x": 3}
    assert json_default(WithModelDump()) == {"m": 1}
    assert json_default(WithDict()) == {"v": 2}
    no_dict = NoDict()
    assert json_default(no_dict) == str(no_dict)


def test_refactored_module_json_default_all_branches():
    @dataclass
    class DC:
        x: int

    class WithModelDump:
        def model_dump(self):
            return {"m": 1}

    class WithDict:
        def __init__(self):
            self.v = 2

    class NoDict:
        __slots__ = ()

    assert ref_json_default(DC(3)) == {"x": 3}
    assert ref_json_default(WithModelDump()) == {"m": 1}
    assert ref_json_default(WithDict()) == {"v": 2}
    no_dict = NoDict()
    assert ref_json_default(no_dict) == str(no_dict)


@pytest.mark.asyncio
async def test_chat_token_usage_emit_logs_and_continues_when_json_dump_fails(
    chat_service,
):
    await chat_service.init_session("gpt-4o")
    run_stream = _FakeRunStream([], usage={"input_tokens": 1})
    chat_service._llm_runner.run_streamed = MagicMock(return_value=run_stream)

    with (
        patch("services.chat_service_refactored.is_local_or_dev", lambda: True),
        patch(
            "services.chat_service_refactored.json.dumps",
            side_effect=ValueError("serialize failed"),
        ),
        patch.object(chat_service.logger, "exception") as mock_exception,
    ):
        responses = await _collect(chat_service, _make_request())

    assert [response.response_type for response in responses] == [ChatResponseType.END]
    mock_exception.assert_any_call("Failed to emit token usage response")


def test_extract_helpers_and_agent_creation_paths(chat_service):
    assert chat_service._extract_position_search_tool_name(None) is None
    assert chat_service._extract_position_search_tool_name({}) is None
    assert chat_service._extract_position_search_tool_name({"ToolName": "  "}) is None
    assert (
        chat_service._extract_position_search_tool_name({"ToolName": " search "})
        == "search"
    )

    with patch.object(chat_service.logger, "warning") as mock_warning:
        assert chat_service._extract_selected_jobtypes(None) == []
        assert chat_service._extract_selected_jobtypes({"SearchFilters": []}) == []
        assert (
            chat_service._extract_selected_jobtypes({"SearchFilters": {"Jobtypes": []}})
            == []
        )
        assert (
            chat_service._extract_selected_jobtypes(
                {
                    "SearchFilters": {
                        "Jobtypes": {
                            "A": {"Value": "x", "Selected": True},
                            "B": [{"Value": "  ", "Selected": True}],
                        }
                    }
                }
            )
            == []
        )
        assert chat_service._extract_selected_jobtypes(
            {
                "SearchFilters": {
                    "Jobtypes": {
                        "A": [
                            {"Value": " IT ", "Selected": True},
                            {"Value": "IT", "Selected": True},
                            {"Value": "Sales", "Selected": False},
                            {"Value": None, "Selected": True},
                            "bad",
                        ],
                        "B": [
                            {"Value": "Finance", "Selected": True},
                        ],
                    }
                }
            }
        ) == ["IT", "Finance"]
    assert mock_warning.call_count >= 1

    chat_service._agents.clear()
    chat_service._create_position_agent_if_not_exist(None)
    chat_service._create_position_agent_if_not_exist("position-1")
    assert "position-1" not in chat_service._agents

    position_guide = MagicMock()
    position_guide.clone.return_value = "cloned"
    chat_service._agents = {AgentName.POSITION_GUIDE: position_guide}
    chat_service._create_position_agent_if_not_exist("position-1")
    assert chat_service._agents["position-1"] == "cloned"


def test_extract_selected_jobtypes_covers_missing_jobtypes_key(chat_service):
    assert chat_service._extract_selected_jobtypes({"SearchFilters": {}}) == []


@pytest.mark.asyncio
async def test_history_lookup_and_summary_paths(chat_service):
    chat_service._chat_repository.has_position_chat_histories = Mock(return_value=True)
    chat_service._chat_repository.get_main_chat_histories = Mock(return_value=["h1"])
    chat_service._chat_repository.get_position_detail_chat_histories = Mock(
        return_value=["h2"]
    )
    chat_service._history_mapper.format_previous_chat_histories = Mock(
        side_effect=lambda histories, limit: (list(histories), limit == 0)
    )
    chat_service._conv_state.chat_histories = {"pos-1": ["history"]}
    chat_service._conv_state.position_id = "pos-1"
    chat_service._conversation_summary_svc.summarize_position_detail_chat = AsyncMock(
        return_value="summary"
    )
    chat_service._chat_persistence.save_chat_histories = Mock()
    chat_service._chat_repository.session_status = Mock(
        return_value=ChatSessionStatus.CHATTING
    )
    chat_service._toolcall_trace_message = {"type": "message", "content": "trace"}
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: []}
    chat_service._history_mapper.convert_to_llm_messages = Mock(
        return_value=(
            {MAIN_CHAT_KEY: ["mapped"]},
            {MAIN_CHAT_KEY: [{"type": "message", "content": "trace"}]},
        )
    )
    chat_service._summary_service = Mock()
    chat_service._summary_service.get_latest_completed.return_value = None
    chat_service._summary_service.get_histories_after.return_value = []

    with patch("services.chat_service_refactored.decrypt", return_value="pos-1"):
        assert (
            await chat_service.check_if_previous_chat_histories_exist("encrypted")
            is True
        )
        assert await chat_service.load_previous_chat_histories(
            5, "encrypted", "before"
        ) == (
            ["h2"],
            False,
        )

    assert await chat_service.load_previous_chat_histories(5, None, None) == (
        ["h1"],
        False,
    )


@pytest.mark.asyncio
async def test_summarize_position_detail_chat_covers_early_returns_and_success(
    chat_service,
):
    request = _make_request(position_id="encrypted-pos")

    chat_service._chat_repository.session_status.return_value = (
        ChatSessionStatus.CHATTING
    )
    chat_service._chat_persistence.save_chat_histories = Mock()
    chat_service._conversation_summary_svc.summarize_position_detail_chat = AsyncMock(
        return_value="summary-text"
    )
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: []}
    chat_service._conv_state.chat_histories["decrypted-pos"] = [
        SimpleNamespace(id="1"),
        SimpleNamespace(id="2"),
    ]

    with patch(
        "services.chat_service_refactored.decrypt", side_effect=Exception("boom")
    ):
        assert (
            await chat_service.summarize_position_detail_chat(request)
            == ChatSessionStatus.CHATTING
        )

    with patch(
        "services.chat_service_refactored.decrypt", return_value="decrypted-pos"
    ):
        assert (
            await chat_service.summarize_position_detail_chat(
                _make_request(position_id=None)
            )
            == ChatSessionStatus.CHATTING
        )

    chat_service._conversation_summary_svc.summarize_position_detail_chat = AsyncMock(
        return_value=""
    )
    with patch(
        "services.chat_service_refactored.decrypt", return_value="decrypted-pos"
    ):
        assert (
            await chat_service.summarize_position_detail_chat(request)
            == ChatSessionStatus.CHATTING
        )

    chat_service._conversation_summary_svc.summarize_position_detail_chat = AsyncMock(
        return_value="summary-text"
    )
    with patch(
        "services.chat_service_refactored.decrypt", return_value="decrypted-pos"
    ):
        status = await chat_service.summarize_position_detail_chat(request)

    assert status == ChatSessionStatus.CHATTING
    chat_service._chat_persistence.save_chat_histories.assert_called()


@pytest.mark.asyncio
async def test_summarize_position_detail_chat_returns_status_when_no_histories(
    chat_service,
):
    request = _make_request(position_id="encrypted-pos")
    chat_service._chat_repository.session_status.return_value = (
        ChatSessionStatus.CHATTING
    )
    chat_service._conv_state.chat_histories["decrypted-pos"] = []

    with patch(
        "services.chat_service_refactored.decrypt", return_value="decrypted-pos"
    ):
        status = await chat_service.summarize_position_detail_chat(request)

    assert status == ChatSessionStatus.CHATTING


def test_find_last_non_position_guide_agent_returns_most_recent_non_guide(chat_service):
    chat_service._conv_state.chat_histories[MAIN_CHAT_KEY] = [
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent=AgentName.POSITION_GUIDE,
            message_id="1",
            role="developer",
            content="trace",
        ),
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent="OtherAgent",
            message_id="2",
            role="assistant",
            content="answer",
        ),
        ChatHistory(
            session_id="sess",
            position_id=None,
            active_agent=AgentName.POSITION_GUIDE,
            message_id="3",
            role="developer",
            content="trace-2",
        ),
    ]

    assert chat_service._find_last_non_position_guide_agent() == "OtherAgent"


def test_remove_tool_trace_message_covers_none_branches(chat_service):
    messages = [{"type": "message", "role": "developer", "content": "keep"}]

    chat_service._toolcall_trace_message = None
    assert chat_service._remove_tool_trace_message(messages) is messages

    chat_service._toolcall_trace_message = {"type": "message"}
    assert chat_service._remove_tool_trace_message(messages) is messages


@pytest.mark.pre_extraction_parity
@pytest.mark.asyncio
async def test_build_summary_context_returns_early_when_summary_service_is_none(
    chat_service,
):
    chat_service._summary_service = None
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    await chat_service._build_summary_context("any-session")


@pytest.mark.pre_extraction_parity
@pytest.mark.asyncio
async def test_build_summary_context_returns_early_when_not_main_chat_key(chat_service):
    chat_service._summary_service = Mock()
    chat_service._conv_state.chat_key = "position-chat"
    await chat_service._build_summary_context("any-session")
    chat_service._summary_service.get_latest_completed.assert_not_called()


@pytest.mark.asyncio
async def test_build_summary_context_handles_empty_summary_text(chat_service):
    chat_service._summary_service = Mock()
    chat_service._summary_service.get_latest_completed.return_value = SimpleNamespace(
        summary_until_history_id="1",
        summary_text="",
    )
    chat_service._chat_repository.get_main_chat_histories.return_value = ["main"]
    chat_service._history_mapper.convert_to_llm_messages = Mock(
        return_value=({MAIN_CHAT_KEY: []}, {MAIN_CHAT_KEY: []})
    )
    chat_service._toolcall_trace_message = {"type": "message", "content": "trace"}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: []}

    await chat_service._build_summary_context("session-1")

    assert (
        chat_service._conv_state.conversation[MAIN_CHAT_KEY][0]
        == chat_service._toolcall_trace_message
    )


@pytest.mark.asyncio
async def test_init_session_covers_filter_error_and_resume_paths(chat_service):
    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    chat_service._llm_svc.clone_agents.return_value = {
        "CareerAdvisor": (default_agent, True)
    }

    chat_service._position_service.current_search_filter = AsyncMock(
        side_effect=RuntimeError("boom")
    )
    status, is_new = await chat_service.init_session("gpt-4o")
    assert status == ChatSessionStatus.CHATTING
    assert is_new is True

    resumed_agent = MagicMock()
    resumed_agent.name = "CareerAdvisor"
    chat_service._position_service.current_search_filter = AsyncMock(
        return_value={
            "ToolName": "search_job_postings",
            "SearchFilters": {"Jobtypes": {"A": [{"Value": "IT", "Selected": True}]}},
        }
    )
    chat_service._llm_svc.clone_agents.return_value = {
        "CareerAdvisor": (resumed_agent, True)
    }
    chat_service._chat_repository.init_chat_session.return_value = (
        SimpleNamespace(
            histories=[
                ChatHistory(
                    session_id="sess",
                    position_id=None,
                    active_agent="CareerAdvisor",
                    message_id="1",
                    role="assistant",
                    content="hello",
                )
            ],
            status=ChatSessionStatus.CHATTING,
        ),
        False,
    )
    chat_service._history_mapper.convert_to_llm_messages = Mock(
        return_value=({MAIN_CHAT_KEY: []}, {MAIN_CHAT_KEY: []})
    )
    chat_service._find_last_non_position_guide_agent = Mock(
        return_value="CareerAdvisor"
    )

    status, is_new = await chat_service.init_session("gpt-4o")
    assert status == ChatSessionStatus.CHATTING
    assert is_new is False
    assert chat_service._conv_state.active_agent_name == "CareerAdvisor"


@pytest.mark.asyncio
async def test_init_session_sets_session_id_when_repository_reports_existing_only(
    chat_service,
):
    chat_service._position_service.current_search_filter = AsyncMock(return_value=None)
    chat_service._chat_repository.init_chat_session.return_value = (None, True)
    with (
        patch("services.chat_service_refactored.uuid.uuid4", return_value="uuid-1"),
        patch("services.chat_service_refactored.set_session_id") as mock_set_session_id,
    ):
        status, is_new = await chat_service.init_session("gpt-4o")

    assert status == ChatSessionStatus.CHATTING
    assert is_new is True
    mock_set_session_id.assert_called_once_with("uuid-1")


@pytest.mark.asyncio
async def test_init_session_treats_default_agent_only_history_as_new_session(
    chat_service,
):
    """DefaultAgentのみの履歴がある場合、新規セッションとして扱うこと。"""
    history = ChatHistory(
        session_id="sess",
        position_id=None,
        active_agent="DefaultAgent",
        message_id="1",
        role="assistant",
        content="こんにちは",
    )
    mock_session = SimpleNamespace(
        status=ChatSessionStatus.CHATTING,
        histories=[history],
    )
    chat_service._chat_repository.init_chat_session.return_value = (mock_session, False)
    chat_service._history_mapper.convert_to_llm_messages = Mock(
        return_value=({MAIN_CHAT_KEY: [history]}, {MAIN_CHAT_KEY: []})
    )
    chat_service._find_last_non_position_guide_agent = Mock(return_value="DefaultAgent")

    with (
        patch("services.chat_service_refactored.uuid.uuid4", return_value="new-uuid"),
        patch("services.chat_service_refactored.set_session_id") as mock_set_session_id,
    ):
        status, is_new = await chat_service.init_session("gpt-4o")

    assert status == ChatSessionStatus.CHATTING
    assert is_new is True
    assert chat_service._conv_state.active_agent_name == ""
    assert chat_service._conv_state.chat_histories == {MAIN_CHAT_KEY: []}
    mock_set_session_id.assert_called_once_with("new-uuid")


@pytest.mark.asyncio
async def test_chat_returns_end_when_agent_lookup_fails_before_stream(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: ["input"]}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.active_agent_name = "MissingAgent"
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    chat_service._toolcall_trace_message = {"type": "message", "content": "trace"}
    chat_service._last_init_session_failed = True

    responses = await _collect(chat_service, _make_request())
    assert responses[-1].response_type == ChatResponseType.END


@pytest.mark.asyncio
async def test_chat_covers_missing_active_agent_and_stream_errors(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    monkeypatch.setattr("services.chat_service_refactored.asyncio.sleep", AsyncMock())
    await chat_service.init_session("gpt-4o")
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: []}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.active_agent_name = ""
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    chat_service._toolcall_trace_message = {"type": "message", "content": "trace"}

    responses = await _collect(chat_service, _make_request())
    assert responses[-1].response_type == ChatResponseType.ERROR

    chat_service._last_init_session_failed = True
    responses = await _collect(chat_service, _make_request())
    assert responses[-1].response_type == ChatResponseType.END

    await chat_service.init_session("gpt-4o")
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: ["input"]}
    chat_service._conv_state.active_agent_name = "CareerAdvisor"

    async def _raise_limit(*_args, **_kwargs):
        if False:
            yield None
        raise PositionSearchRateLimitExceeded("limit")

    async def _raise_retryable(*_args, **_kwargs):
        if False:
            yield None
        raise RetryableToolOutputFailure("call-1", "retry")

    async def _raise_generic(*_args, **_kwargs):
        if False:
            yield None
        raise RuntimeError("boom")

    chat_service._stream_event_processor.process = _raise_limit
    responses = await _collect(chat_service, _make_request())
    assert responses[-1].response_type == ChatResponseType.ERROR

    chat_service._stream_event_processor.process = _raise_retryable
    responses = await _collect(chat_service, _make_request())
    assert responses[-1].response_type == ChatResponseType.ERROR

    chat_service._stream_event_processor.process = _raise_generic
    responses = await _collect(chat_service, _make_request())
    assert responses[-1].response_type == ChatResponseType.ERROR


@pytest.mark.pre_extraction_parity
@pytest.mark.asyncio
async def test_chat_retryable_failure_then_success(chat_service, monkeypatch):
    """RetryableToolOutputFailure on attempt 0 triggers retry; attempt 1 succeeds.

    Verifies that after a RetryableToolOutputFailure the loop proceeds to the
    next attempt and yields a successful END response, confirming the retry path
    works end-to-end.
    """
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    save_llm_error_mock = Mock()
    chat_service._chat_persistence.save_llm_error = save_llm_error_mock

    await chat_service.init_session("gpt-4o")
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: ["input"]}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.active_agent_name = "CareerAdvisor"

    call_count = 0

    async def _first_fails_then_ok(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            if False:
                yield None
            raise RetryableToolOutputFailure("call-retry", "retry msg")
        # Second call succeeds — yields nothing and returns normally
        if False:
            yield None

    chat_service._stream_event_processor.process = _first_fails_then_ok
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream([])

    responses = await _collect(chat_service, _make_request())

    assert call_count == 2, f"Expected 2 process() calls (retry), got {call_count}"
    assert responses[-1].response_type == ChatResponseType.END

    # Error message must be persisted on the failed attempt
    save_llm_error_mock.assert_called_once_with("retry msg")


@pytest.mark.asyncio
async def test_chat_covers_finalize_and_summary_service_paths(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: ["input"]}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.active_agent_name = "CareerAdvisor"
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream([])

    from utils.chat_response import ChatStreamResponse

    class FakeStreamGuard:
        def __init__(self, *_args, **_kwargs):
            self.security_detected = False

        def reset(self):
            pass

        async def finalize(self, *_args, **_kwargs):
            yield ChatStreamResponse(
                request_type=ChatRequestType.CHAT,
                position_id=None,
            ).create_error_response("blocked", ChatSessionStatus.CHATTING)

        def cleanup(self):
            return None

    chat_service._summary_service = Mock()
    chat_service._summary_service.check_should_start_summary.side_effect = RuntimeError(
        "boom"
    )

    with patch("services.chat_service_refactored.StreamGuard", FakeStreamGuard):
        responses = await _collect(chat_service, _make_request())

    # finalize() yielded an ERROR chunk → _finalize_security_stopped=True → early return
    assert any(r.response_type == ChatResponseType.ERROR for r in responses)
    assert not any(r.response_type == ChatResponseType.END for r in responses)


@pytest.mark.asyncio
async def test_chat_continues_when_finalize_raises(chat_service, monkeypatch):
    """Lines 811-814: stream_guard.finalize() raises → logged, chat continues to END."""
    from utils.chat_response import ChatStreamResponse

    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: ["input"]}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.active_agent_name = "CareerAdvisor"
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream([])

    class FakeStreamGuardRaises:
        def __init__(self, *_args, **_kwargs):
            self.security_detected = False

        def reset(self):
            pass

        async def finalize(self, *_args, **_kwargs):
            if False:
                yield None
            raise RuntimeError("finalize failure")

        def cleanup(self):
            return None

    with patch("services.chat_service_refactored.StreamGuard", FakeStreamGuardRaises):
        responses = await _collect(chat_service, _make_request())

    # finalize() raised → except catches it → chat continues → END
    assert responses[-1].response_type == ChatResponseType.END


@pytest.mark.pre_extraction_parity
@pytest.mark.asyncio
async def test_chat_finalize_non_error_chunk_does_not_stop_early(
    chat_service, monkeypatch
):
    """824->819: finalize() yields a non-ERROR chunk → loop continues without early return."""
    from utils.chat_response import ChatStreamResponse

    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: ["input"]}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.active_agent_name = "CareerAdvisor"
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream([])

    class FakeStreamGuardTextOnly:
        def __init__(self, *_args, **_kwargs):
            self.security_detected = False

        def reset(self):
            pass

        async def finalize(self, *_args, **_kwargs):
            yield ChatStreamResponse(
                request_type=ChatRequestType.CHAT,
                position_id=None,
            ).create_agent_message_response(
                "item-1", "safe text", ChatSessionStatus.CHATTING
            )

        def cleanup(self):
            return None

    with patch("services.chat_service_refactored.StreamGuard", FakeStreamGuardTextOnly):
        responses = await _collect(chat_service, _make_request())

    assert any(r.response_type == ChatResponseType.MESSAGE for r in responses)
    assert responses[-1].response_type == ChatResponseType.END


@pytest.mark.asyncio
async def test_chat_returns_end_when_stream_guard_reports_security_detected(
    chat_service, monkeypatch
):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: ["input"]}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.active_agent_name = "CareerAdvisor"
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)

    async def _empty_process(*_args, **_kwargs):
        if False:
            yield None

    class FakeStreamGuard:
        def __init__(self, *_args, **_kwargs):
            self.security_detected = True

        async def finalize(self, *_args, **_kwargs):
            if False:
                yield None

        def cleanup(self):
            return None

    chat_service._stream_event_processor.process = _empty_process

    with patch("services.chat_service_refactored.StreamGuard", FakeStreamGuard):
        responses = await _collect(chat_service, _make_request())

    assert responses == []


@pytest.mark.asyncio
async def test_chat_handles_summary_service_check_failure(chat_service, monkeypatch):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: ["input"]}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.active_agent_name = "CareerAdvisor"
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)

    async def _empty_process(*_args, **_kwargs):
        if False:
            yield None

    class FakeStreamGuard:
        def __init__(self, *_args, **_kwargs):
            self.security_detected = False

        async def finalize(self, *_args, **_kwargs):
            if False:
                yield None

        def cleanup(self):
            return None

    chat_service._stream_event_processor.process = _empty_process
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream([], usage=None)
    chat_service._summary_service = Mock()
    chat_service._summary_service.check_should_start_summary.side_effect = RuntimeError(
        "boom"
    )

    with patch("services.chat_service_refactored.StreamGuard", FakeStreamGuard):
        responses = await _collect(chat_service, _make_request())

    assert responses[-1].response_type == ChatResponseType.END


def test_append_stop_at_tool_outputs_callback_covers_handler_and_fallback_paths(
    chat_service,
):
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: []}

    chat_service._current_tool_event_handler = None
    chat_service._append_stop_at_tool_outputs_callback([], True)

    handler = Mock()
    handler.build_stop_at_tool_outputs.return_value = [
        {"type": "function_call_output", "call_id": 1, "output": "skip"},
        {"type": "function_call_output", "call_id": "dup", "output": "a"},
        {"type": "function_call_output", "call_id": "dup", "output": "b"},
        {"type": "function_call_output", "call_id": "new", "output": "c"},
    ]
    chat_service._current_tool_event_handler = handler
    chat_service._conv_state.conversation[MAIN_CHAT_KEY] = [
        {"type": "function_call_output", "call_id": "dup", "output": "existing"}
    ]
    chat_service._append_stop_at_tool_outputs_callback([{"call_id": "x"}], True)

    assert chat_service._conv_state.conversation[MAIN_CHAT_KEY][-1]["call_id"] == "new"


@pytest.mark.asyncio
async def test_chat_covers_agent_lookup_failure(chat_service, monkeypatch):
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    chat_service._conv_state.conversation = {MAIN_CHAT_KEY: ["input"]}
    chat_service._conv_state.chat_key = MAIN_CHAT_KEY
    chat_service._conv_state.active_agent_name = "MissingAgent"
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    chat_service._toolcall_trace_message = {"type": "message", "content": "trace"}

    responses = await _collect(chat_service, _make_request())
    assert responses[-1].response_type == ChatResponseType.ERROR


@pytest.mark.asyncio
async def test_summarize_position_detail_chat_is_native_no_legacy(chat_service):
    """summarize_position_detail_chat はネイティブ実装であり、_legacy_chat_service へ委譲しない。

    task-5-legacy-dependency-removal: 委譲パターンを削除して直接実装に置き換えた。
    """
    assert not hasattr(chat_service, "_legacy_chat_service"), (
        "summarize must not delegate to _legacy_chat_service after task-5"
    )


@pytest.mark.asyncio
async def test_workflow_submitted_saves_histories_from_result(chat_service):
    """workflow_submitted でチャット履歴保存することを確認する。"""
    from domain.entities.chat_history import ChatHistory
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult
    from utils.enum import LLMMessageRole

    history = ChatHistory(
        session_id="sess-001",
        position_id=None,
        active_agent="CareerAdvisor",
        message_id="wf_test_001",
        role=LLMMessageRole.USER,
        content="Q1",
    )
    chat_service._workflow_chat_handler.prepare_workflow_submitted = AsyncMock(
        return_value=WorkflowChatHandlerResult(
            prepared_message="workflow-ready",
            workflow_id="other-wf",
            workflow_histories=[history],
        )
    )
    chat_service._chat_persistence.save_chat_histories = Mock()

    async def _yield_once(_request, _client_ip):
        yield SimpleNamespace(response_type=ChatResponseType.END)

    chat_service.chat = _yield_once

    responses = [
        item
        async for item in chat_service.workflow_submitted(_make_request(), "127.0.0.1")
    ]

    assert responses[0].response_type == ChatResponseType.END
    chat_service._chat_persistence.save_chat_histories.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_submitted_applies_next_agent_name_to_conv_state(chat_service):
    """result.next_agent_name が _conv_state.active_agent_name に反映される。"""
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult

    chat_service._workflow_chat_handler.prepare_workflow_submitted = AsyncMock(
        return_value=WorkflowChatHandlerResult(
            prepared_message="ready",
            next_agent_name="CareerAdvisor",
            workflow_id="other-wf",
            workflow_histories=[],
            next_workflow_id_response=None,
        )
    )
    chat_service._chat_persistence.save_chat_histories = Mock()

    async def _yield_end(_request, _client_ip):
        yield SimpleNamespace(response_type=ChatResponseType.END)

    chat_service.chat = _yield_end
    await chat_service.init_session("gpt-4o")

    async for _ in chat_service.workflow_submitted(_make_request(), "127.0.0.1"):
        pass

    assert chat_service._conv_state.active_agent_name == "CareerAdvisor"


@pytest.mark.asyncio
async def test_workflow_submitted_saves_workflow_histories_from_result(chat_service):
    """result.workflow_histories が _chat_persistence.save_chat_histories へ渡される。"""
    from domain.entities.chat_history import ChatHistory
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult
    from utils.enum import LLMMessageRole

    history = ChatHistory(
        session_id="sess-001",
        position_id=None,
        active_agent="CareerAdvisor",
        message_id="wf_test_001",
        role=LLMMessageRole.USER,
        content="Q1",
    )
    chat_service._workflow_chat_handler.prepare_workflow_submitted = AsyncMock(
        return_value=WorkflowChatHandlerResult(
            prepared_message="ready",
            workflow_id="other-wf",
            workflow_histories=[history],
        )
    )
    save_mock = Mock()
    chat_service._chat_persistence.save_chat_histories = save_mock

    async def _yield_end(_request, _client_ip):
        yield SimpleNamespace(response_type=ChatResponseType.END)

    chat_service.chat = _yield_end

    async for _ in chat_service.workflow_submitted(_make_request(), "127.0.0.1"):
        pass

    save_mock.assert_called_once()
    saved = save_mock.call_args[0][0]
    assert any(h.message_id == "wf_test_001" for h in saved)


@pytest.mark.asyncio
async def test_workflow_submitted_initial_menu_saves_toolcall_trace_before_histories(
    chat_service,
):
    """save_toolcall_trace_message が先に呼ばれ、その後 workflow_histories が保存される（順序保証）。"""
    from domain.entities.chat_history import ChatHistory
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult
    from utils.const import INITIAL_MENU_WORKFLOW_ID
    from utils.enum import LLMMessageRole

    await chat_service.init_session("gpt-4o")
    history = ChatHistory(
        session_id="sess-001",
        position_id=None,
        active_agent="CareerAdvisor",
        message_id="wf_initial_menu_001",
        role=LLMMessageRole.USER,
        content="Q1",
    )
    chat_service._workflow_chat_handler.prepare_workflow_submitted = AsyncMock(
        return_value=WorkflowChatHandlerResult(
            prepared_message="ready",
            workflow_id=INITIAL_MENU_WORKFLOW_ID,
            workflow_histories=[history],
        )
    )
    call_order: list[str] = []
    trace_mock = Mock(side_effect=lambda: call_order.append("trace"))
    save_mock = Mock(side_effect=lambda _: call_order.append("histories"))
    chat_service._chat_persistence.save_toolcall_trace_message = trace_mock
    chat_service._chat_persistence.save_chat_histories = save_mock

    async def _yield_end(_request, _client_ip):
        yield SimpleNamespace(response_type=ChatResponseType.END)

    chat_service.chat = _yield_end

    async for _ in chat_service.workflow_submitted(_make_request(), "127.0.0.1"):
        pass

    trace_mock.assert_called_once()
    save_mock.assert_called_once()
    assert call_order == ["trace", "histories"]
    saved = save_mock.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].message_id == "wf_initial_menu_001"


@pytest.mark.asyncio
async def test_workflow_submitted_non_initial_menu_no_toolcall_trace_save(chat_service):
    """INITIAL_MENU 以外では _toolcall_trace_message が保存対象に含まれない。"""
    from domain.entities.chat_history import ChatHistory
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult
    from utils.enum import LLMMessageRole

    await chat_service.init_session("gpt-4o")
    chat_service._toolcall_trace_message = {
        "type": "message",
        "role": LLMMessageRole.DEVELOPER,
        "content": "trace content",
    }
    history = ChatHistory(
        session_id="sess-001",
        position_id=None,
        active_agent="CareerAdvisor",
        message_id="wf_other_001",
        role=LLMMessageRole.USER,
        content="Q1",
    )
    chat_service._workflow_chat_handler.prepare_workflow_submitted = AsyncMock(
        return_value=WorkflowChatHandlerResult(
            prepared_message="ready",
            workflow_id="other-wf",
            workflow_histories=[history],
        )
    )
    save_mock = Mock()
    chat_service._chat_persistence.save_chat_histories = save_mock

    async def _yield_end(_request, _client_ip):
        yield SimpleNamespace(response_type=ChatResponseType.END)

    chat_service.chat = _yield_end

    async for _ in chat_service.workflow_submitted(_make_request(), "127.0.0.1"):
        pass

    save_mock.assert_called_once()
    saved = save_mock.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].message_id == "wf_other_001"


@pytest.mark.asyncio
async def test_workflow_submitted_saves_histories_even_when_error_response(
    chat_service,
):
    """result.error_response が非 None でも result.workflow_histories が保存される。"""
    from domain.entities.chat_history import ChatHistory
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult
    from utils.chat_response import ChatStreamResponse
    from utils.enum import LLMMessageRole

    error_resp = ChatStreamResponse(
        request_type=_make_request().request_type
    ).create_error_response("jobtypes error")
    history = ChatHistory(
        session_id="sess-001",
        position_id=None,
        active_agent="CareerAdvisor",
        message_id="wf_err_001",
        role=LLMMessageRole.USER,
        content="Q1",
    )
    chat_service._workflow_chat_handler.prepare_workflow_submitted = AsyncMock(
        return_value=WorkflowChatHandlerResult(
            error_response=error_resp,
            workflow_id="other-wf",
            workflow_histories=[history],
        )
    )
    save_mock = Mock()
    chat_service._chat_persistence.save_chat_histories = save_mock

    responses = [
        item
        async for item in chat_service.workflow_submitted(_make_request(), "127.0.0.1")
    ]

    assert responses[0].response_type == ChatResponseType.ERROR
    save_mock.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_submitted_next_workflow_id_response_yields_and_skips_chat(
    chat_service,
):
    """result.next_workflow_id_response が yield されて chat() が呼ばれない。"""
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult

    wf_response = SimpleNamespace(response_type=ChatResponseType.WORKFLOW)
    chat_service._workflow_chat_handler.prepare_workflow_submitted = AsyncMock(
        return_value=WorkflowChatHandlerResult(
            workflow_id="next-wf",
            workflow_histories=[],
            next_workflow_id_response=wf_response,
        )
    )
    chat_service._chat_persistence.save_chat_histories = Mock()
    chat_called = []

    async def _chat_spy(_request, _client_ip):
        chat_called.append(True)
        yield SimpleNamespace(response_type=ChatResponseType.END)

    chat_service.chat = _chat_spy

    responses = [
        item
        async for item in chat_service.workflow_submitted(_make_request(), "127.0.0.1")
    ]

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.WORKFLOW
    assert not chat_called


@pytest.mark.asyncio
async def test_workflow_cancelled_initial_menu_returns_error_response(chat_service):
    """INITIAL_MENU の cancel で error_response が yield され、chat() が呼ばれない。"""
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult
    from utils.chat_response import ChatStreamResponse

    error_resp = ChatStreamResponse(
        request_type=_make_request().request_type
    ).create_error_response("このワークフローはキャンセルできません。")
    chat_service._workflow_chat_handler.prepare_workflow_cancelled = AsyncMock(
        return_value=WorkflowChatHandlerResult(error_response=error_resp)
    )
    chat_called = []

    async def _chat_spy(_request, _client_ip):
        chat_called.append(True)
        yield SimpleNamespace(response_type=ChatResponseType.END)

    chat_service.chat = _chat_spy

    responses = [
        item
        async for item in chat_service.workflow_cancelled(_make_request(), "127.0.0.1")
    ]

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR
    assert not chat_called


@pytest.mark.asyncio
async def test_get_initial_menu_response_returns_workflow_type(chat_service):
    """正常系: response_type == ChatResponseType.WORKFLOW のレスポンスが返る。"""
    from utils.const import INITIAL_MENU_WORKFLOW_ID

    definition_mock = MagicMock()
    definition_mock.model_dump.return_value = {"id": INITIAL_MENU_WORKFLOW_ID}
    chat_service._workflow_service.get_definition.return_value = definition_mock

    response = chat_service.get_initial_menu_response()

    assert response.response_type == ChatResponseType.WORKFLOW
    chat_service._workflow_service.get_definition.assert_called_once_with(
        INITIAL_MENU_WORKFLOW_ID
    )


@pytest.mark.asyncio
async def test_get_initial_menu_response_returns_error_when_definition_not_found(
    chat_service,
):
    """workflow_service.get_definition が FileNotFoundError → エラーレスポンスが返る。"""
    chat_service._workflow_service.get_definition.side_effect = FileNotFoundError(
        "not found"
    )

    response = chat_service.get_initial_menu_response()

    assert response.response_type == ChatResponseType.ERROR


@pytest.mark.asyncio
async def test_summarize_position_detail_chat_returns_session_status_when_no_position_id(
    chat_service,
):
    """summarize: position_id が空の場合は session_status を返す。"""
    from utils.chat_request import ChatRequestType

    request = ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        position_id=None,
        message="",
        current_message_id="msg-summarize-test",
    )
    chat_service._chat_repository.session_status.return_value = (
        ChatSessionStatus.CHATTING
    )

    status = await chat_service.summarize_position_detail_chat(request)

    assert status == ChatSessionStatus.CHATTING


@pytest.mark.asyncio
async def test_workflow_methods_use_workflow_chat_handler(chat_service, monkeypatch):
    """job_type_decided / clear_jobtype / workflow_submitted / workflow_cancelled が
    WorkflowChatHandler 経由でメッセージを準備し chat() に転送することを確認する。
    """
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult

    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")
    chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
        [],
        continuation_state=None,
        agent_state=SimpleNamespace(),
        replay_items=[],
        usage=None,
    )

    # _workflow_chat_handler の各 prepare_* メソッドをモックする。
    prepare_result = WorkflowChatHandlerResult(
        error_response=None,
        prepared_message="prepared",
        workflow_id=None,
        next_agent_name=None,
        workflow_histories=[],
        next_workflow_id_response=None,
    )
    chat_service._workflow_chat_handler.prepare_job_type_decided = AsyncMock(
        return_value=prepare_result
    )
    chat_service._workflow_chat_handler.prepare_clear_jobtype = AsyncMock(
        return_value=prepare_result
    )
    chat_service._workflow_chat_handler.prepare_workflow_submitted = AsyncMock(
        return_value=prepare_result
    )
    chat_service._workflow_chat_handler.prepare_workflow_cancelled = AsyncMock(
        return_value=prepare_result
    )

    for method_name in (
        "job_type_decided",
        "clear_jobtype",
        "workflow_submitted",
        "workflow_cancelled",
    ):
        chat_service._llm_runner.run_streamed.return_value = _FakeRunStream(
            [],
            continuation_state=None,
            agent_state=SimpleNamespace(),
            replay_items=[],
            usage=None,
        )
        responses = [
            item
            async for item in getattr(chat_service, method_name)(
                _make_request(), "127.0.0.1"
            )
        ]
        assert responses[-1].response_type == ChatResponseType.END, (
            f"{method_name} did not end with END response"
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name,current_page,position_id,conversation_key,expected_status,session_status_side_effect",
    [
        (
            ToolName.APPLICATION.value,
            PageName.POSITION_DETAIL,
            "enc-pos",
            "real-pos",
            ChatSessionStatus.APPLYING,
            [ChatSessionStatus.CHATTING, ChatSessionStatus.APPLYING],
        ),
        (
            ToolName.REGISTRATION.value,
            PageName.CHAT,
            None,
            MAIN_CHAT_KEY,
            ChatSessionStatus.REGISTERING,
            [ChatSessionStatus.CHATTING, ChatSessionStatus.REGISTERING],
        ),
    ],
)
async def test_tool_side_effects_preserve_legacy_status_transitions(
    chat_service,
    monkeypatch,
    tool_name,
    current_page,
    position_id,
    conversation_key,
    expected_status,
    session_status_side_effect,
):
    """APPLICATION / REGISTRATION tool outputs update session state the same way as legacy."""

    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    monkeypatch.setattr(
        "services.chat.tool_event_handler.decrypt",
        lambda *_args, **_kwargs: conversation_key,
    )
    monkeypatch.setattr(
        "services.chat_service_refactored.decrypt",
        lambda *_args, **_kwargs: conversation_key,
    )

    await chat_service.init_session("gpt-4o")
    chat_service._turn_preparer.prepare_turn = AsyncMock(return_value=None)
    chat_service._conv_state.active_agent_name = "CareerAdvisor"
    chat_service._conv_state.chat_key = conversation_key
    chat_service._conv_state.position_id = conversation_key if position_id else None
    chat_service._conv_state.conversation = {
        conversation_key: [chat_service._toolcall_trace_message]
    }
    chat_service._chat_repository.session_status.side_effect = (
        session_status_side_effect
    )

    class FakeToolCallItem:
        def __init__(self):
            self.raw_item = SimpleNamespace(
                id="tool-1",
                call_id="call-1",
                name=tool_name,
                arguments="{}",
            )
            self.agent = SimpleNamespace(name="CareerAdvisor", tool_use_behavior={})

    class FakeToolCallOutputItem:
        def __init__(self):
            self.raw_item = {"call_id": "call-1", "output": json.dumps({})}
            self.output = json.dumps({})
            self.agent = SimpleNamespace(name="CareerAdvisor")

    run_stream = _FakeRunStream(
        [
            LLMRunItemStreamEvent(item=FakeToolCallItem()),
            LLMRunItemStreamEvent(item=FakeToolCallOutputItem()),
        ],
        continuation_state=None,
        agent_state=SimpleNamespace(name="CareerAdvisor"),
        replay_items=[],
        usage=None,
    )
    chat_service._llm_runner.run_streamed.return_value = run_stream

    with (
        patch("services.chat.stream_event_processor.ToolCallItem", FakeToolCallItem),
        patch(
            "services.chat.stream_event_processor.ToolCallOutputItem",
            FakeToolCallOutputItem,
        ),
    ):
        responses = await _collect(
            chat_service,
            _make_request(current_page=current_page, position_id=position_id),
        )

    assert responses[-1].response_type == ChatResponseType.END
    chat_service._chat_repository.update_session_status.assert_called_once_with(
        expected_status
    )

    if tool_name == ToolName.APPLICATION.value:
        chat_service._user_repository.add_apply_position.assert_called_once_with(
            conversation_key
        )
        chat_service._user_repository.update_miidas_registration_user_data.assert_not_called()
        chat_service._action_log_repository.insert.assert_not_called()
    else:
        chat_service._action_log_repository.insert.assert_called_once()
        chat_service._user_repository.add_apply_position.assert_not_called()
        chat_service._user_repository.update_miidas_registration_user_data.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_chat_key_sets_conv_state_before_prepare_turn(
    chat_service, monkeypatch
):
    """_resolve_chat_key() は prepare_turn() より前に _conv_state.chat_key / position_id を設定する。"""
    await chat_service.init_session("gpt-4o")

    captured = {}

    async def _spy_prepare(request):
        captured["chat_key"] = chat_service._conv_state.chat_key
        captured["position_id"] = chat_service._conv_state.position_id

    chat_service._turn_preparer.prepare_turn = _spy_prepare

    DECRYPTED_ID = "pos-decrypted-abc"
    monkeypatch.setattr(
        "services.chat_service_refactored.decrypt", lambda _kt, _enc: DECRYPTED_ID
    )

    await _collect(
        chat_service,
        _make_request(current_page=PageName.POSITION_DETAIL, position_id="enc-pos-xyz"),
    )

    assert captured.get("chat_key") == DECRYPTED_ID
    assert captured.get("position_id") == DECRYPTED_ID


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name",
    ["job_type_decided", "workflow_submitted"],
)
async def test_streaming_public_methods_yield_error_on_prepare_failure(
    chat_service,
    method_name,
):
    """job_type_decided と workflow_submitted が WorkflowChatHandler の prepare_* エラーレスポンスを
    適切に yield することを確認する。
    """
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult
    from utils.chat_response import ChatStreamResponse

    chat_response = ChatStreamResponse(
        request_type=_make_request().request_type, position_id=None
    )
    error_resp = chat_response.create_error_response(
        "prepare failed", ChatSessionStatus.CHATTING
    )

    error_result = WorkflowChatHandlerResult(
        error_response=error_resp,
        prepared_message="",
        workflow_id=None,
        next_agent_name=None,
        workflow_histories=[],
        next_workflow_id_response=None,
    )

    prepare_attr = f"prepare_{method_name}"
    setattr(
        chat_service._workflow_chat_handler,
        prepare_attr,
        AsyncMock(return_value=error_result),
    )

    responses = []
    async for item in getattr(chat_service, method_name)(_make_request(), "127.0.0.1"):
        responses.append(item)

    assert len(responses) == 1
    assert responses[0].response_type == ChatResponseType.ERROR


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name",
    ["job_type_decided", "clear_jobtype", "workflow_submitted", "workflow_cancelled"],
)
async def test_workflow_methods_propagate_cancellation_from_runner(
    chat_service,
    method_name,
    monkeypatch,
):
    """workflow public methods は chat() 経由で LLMRunner が CancelledError を送出した場合、
    それを呼び出し元に伝播する（ストリームは close しない）。
    """
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult

    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    await chat_service.init_session("gpt-4o")

    prepare_result = WorkflowChatHandlerResult(
        error_response=None,
        prepared_message="prepared",
        workflow_id=None,
        next_agent_name=None,
        workflow_histories=[],
        next_workflow_id_response=None,
    )
    prepare_attr = f"prepare_{method_name}"
    setattr(
        chat_service._workflow_chat_handler,
        prepare_attr,
        AsyncMock(return_value=prepare_result),
    )

    run_stream = _FailingRunStream(asyncio.CancelledError())
    chat_service._llm_runner.run_streamed.return_value = run_stream

    with pytest.raises(asyncio.CancelledError):
        async for _ in getattr(chat_service, method_name)(_make_request(), "127.0.0.1"):
            pass

    assert run_stream.closed is False
