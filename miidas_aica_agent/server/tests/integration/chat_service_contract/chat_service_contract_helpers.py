"""Shared helpers for chat service contract tests."""

import json
from collections.abc import AsyncIterator, Callable
from types import SimpleNamespace
from typing import Any

from dependency_injector import providers

from containers import Container
from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from repositories.api_repo import AICAAPIRepository
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.rate_limit_repo import BaseRateLimitRepository
from repositories.summary_repo import SummaryRepository
from repositories.user_repo import UserRepository
from repositories.workflow_definition_repo import WorkflowDefinitionRepository
from repositories.workflow_repo import WorkflowRepository
from services.chat.llm_runner import (
    LLMRetryChunkEvent,
    LLMRetryCompleteEvent,
    LLMRunWithRetryResult,
    json_default,
)
from services.chat.tool_event_handler import RetryableToolOutputFailure
from services.conversation_summary_service import ConversationSummaryService
from services.position_change_analyze_summary_service import (
    PositionChangeAnalyzeSummaryService,
)
from services.position_service import PositionService
from services.rate_limit_service import RateLimitService
from services.summary_service import SummaryService
from services.workflow_service import WorkflowService
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.enum import LLMMessageRole
from utils.enum import PageName
from unittest.mock import AsyncMock, MagicMock, Mock, patch


class _FakeRunStream:
    """固定のイベントリストをリプレイする最小限の LLMRunner run_streamed フェイク。

    real-refactored バリアントで LLMRunner.run_streamed の戻り値として使用する。
    """

    def __init__(
        self,
        events: list,
        continuation_state=None,
        agent_state=None,
        tool_replay_items=None,
        usage=None,
    ):
        self._events = events
        self.continuation_state = continuation_state
        self.agent_state = agent_state
        self.replay_items = tool_replay_items or []
        self.usage = usage

    async def stream_events(self):
        for event in self._events:
            yield event

    async def aclose(self) -> None:
        pass


def _inner(chat_svc):
    """テストから内部依存へアクセスするときの統一エントリ。

    legacy / real-refactored のどちらでも `chat_svc` 自体を返す。
    """
    return chat_svc


def _get_conversation(svc):
    """Get conversation from service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        return svc._conv_state.conversation
    return svc._conversation


def _set_conversation(svc, value):
    """Set conversation on service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        svc._conv_state.conversation = value
    else:
        svc._conversation = value


def _get_chat_histories(svc):
    """Get chat_histories from service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        return svc._conv_state.chat_histories
    return svc._chat_histories


def _set_chat_histories(svc, value):
    """Set chat_histories on service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        svc._conv_state.chat_histories = value
    else:
        svc._chat_histories = value


def _get_active_agent_name(svc):
    """Get active_agent_name from service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        return svc._conv_state.active_agent_name
    return svc._active_agent_name


def _set_active_agent_name(svc, value):
    """Set active_agent_name on service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        svc._conv_state.active_agent_name = value
    else:
        svc._active_agent_name = value


def _get_position_id(svc):
    """Get position_id from service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        return svc._conv_state.position_id
    return svc._position_id


def _set_position_id(svc, value):
    """Set position_id on service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        svc._conv_state.position_id = value
    else:
        svc._position_id = value


def _get_provider(svc):
    """Get provider (model_name) from service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        return svc._conv_state.model_name or None
    return svc._provider


def _set_provider(svc, value):
    """Set provider (model_name) on service, handling both legacy and refactored variants."""
    if hasattr(svc, "_conv_state"):
        svc._conv_state.model_name = value or ""
    else:
        svc._provider = value


class _LegacyStateAdapter:
    """Expose legacy ChatService private fields via ConversationState-like names."""

    def __init__(self, legacy_svc):
        self._svc = legacy_svc

    @property
    def active_agent_name(self):
        return self._svc._active_agent_name

    @active_agent_name.setter
    def active_agent_name(self, value):
        self._svc._active_agent_name = value

    @property
    def session_created(self):
        return self._svc._session_created

    @session_created.setter
    def session_created(self, value):
        self._svc._session_created = value

    @property
    def should_save(self):
        return self._svc._should_save

    @should_save.setter
    def should_save(self, value):
        self._svc._should_save = value

    @property
    def conversation(self):
        return self._svc._conversation

    @conversation.setter
    def conversation(self, value):
        self._svc._conversation = value

    @property
    def chat_histories(self):
        return self._svc._chat_histories

    @chat_histories.setter
    def chat_histories(self, value):
        self._svc._chat_histories = value

    @property
    def position_id(self):
        return self._svc._position_id

    @position_id.setter
    def position_id(self, value):
        self._svc._position_id = value

    @property
    def previous_continuation_states(self):
        return self._svc._previous_response_ids

    @previous_continuation_states.setter
    def previous_continuation_states(self, value):
        self._svc._previous_response_ids = value

    @property
    def model_name(self):
        return self._svc._provider

    @model_name.setter
    def model_name(self, value):
        self._svc._provider = value

    @property
    def chat_key(self):
        return self._svc._chat_key

    @chat_key.setter
    def chat_key(self, value):
        self._svc._chat_key = value


def _state(chat_svc):
    """variant 差異を吸収して state object を返す。

    - real-refactored: `ConversationState` (`chat_svc._conv_state`)
    - legacy: private field を ConversationState 互換名で公開する adapter
    """
    svc = _inner(chat_svc)
    return svc._conv_state if hasattr(svc, "_conv_state") else _LegacyStateAdapter(svc)


def _existing_session(session_id: str):
    """USER ヒストリを 1 件持つ偽の ChatSession を返す。"""
    histories = [
        ChatHistory(
            id=1,
            session_id=session_id,
            active_agent="CareerAdvisor",
            message_id="msg-prev-1",
            role=LLMMessageRole.USER,
            content="以前のメッセージです",
        )
    ]
    return SimpleNamespace(
        session_id=session_id,
        status=ChatSessionStatus.CHATTING,
        histories=histories,
    )


async def _setup_existing_session(
    chat_svc,
    agent_mock: MagicMock,
    session_id: str,
) -> None:
    """既存セッションを持つ状態で init_session を実行する。"""
    svc = _inner(chat_svc)
    existing = _existing_session(session_id)
    svc._chat_repository.init_chat_session.return_value = (existing, True)
    # build_summary_context は init_session() 内で get_main_chat_histories() を呼ぶ。
    # init_chat_session が返す histories と一致させることで _chat_histories の整合性を保つ。
    svc._chat_repository.get_main_chat_histories.return_value = existing.histories
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (agent_mock, True)}
    await chat_svc.init_session("gpt-4o")


class _FakeRunResult:
    """固定のイベントリストをリプレイする最小限の RunResultStreaming フェイク。"""

    last_response_id = None
    last_agent = None

    def __init__(self, events: list):
        self._events = events
        self.context_wrapper = SimpleNamespace(
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        )

    async def stream_events(self):
        for event in self._events:
            yield event

    def to_input_list(self):
        return []


def _make_run_item_event(item):
    return SimpleNamespace(type="run_item_stream_event", item=item)


def _attach_run_with_retry_passthrough(
    mock_runner: Any,
    *,
    action_log_repository: Any | None = None,
    usage_content_builder: Callable[[Any], str] | None = None,
) -> None:
    """Attach a single-attempt run_with_retry passthrough to a mocked runner.

    The helper keeps contract tests aligned with the current `LLMRunner.run_with_retry`
    interface while avoiding per-test copy/paste drift.
    """

    async def _run_with_retry_impl(*args, **kwargs) -> AsyncIterator[Any]:
        process_stream = kwargs["process_stream"]
        on_before_attempt = kwargs.get("on_before_attempt")
        on_after_attempt = kwargs.get("on_after_attempt")
        on_retryable_error = kwargs.get("on_retryable_error")
        on_non_retryable_error = kwargs.get("on_non_retryable_error")
        max_retry_count = 5
        last_usage = None

        for attempt in range(max_retry_count):
            error: Exception | None = None
            retryable_error = False
            usage = None
            try:
                if on_before_attempt is not None:
                    await on_before_attempt()

                run_stream = mock_runner.run_streamed(
                    starting_agent=kwargs.get("starting_agent"),
                    input=kwargs.get("input"),
                    continuation_state=(
                        kwargs["continuation_state_supplier"]()
                        if kwargs.get("continuation_state_supplier") is not None
                        else kwargs.get("continuation_state")
                    ),
                )

                async for chunk in process_stream(run_stream):
                    yield LLMRetryChunkEvent(chunk=chunk)

                usage = getattr(run_stream, "usage", None)
                last_usage = usage
                message_id = kwargs.get("message_id")
                if (
                    usage is not None
                    and message_id
                    and action_log_repository is not None
                ):
                    try:
                        if usage_content_builder is not None:
                            content = usage_content_builder(usage)
                        else:
                            content = json.dumps(
                                usage,
                                default=json_default,
                                ensure_ascii=False,
                            )
                        action_log_repository.insert(
                            log_type="TOKEN_USAGE",
                            source=message_id,
                            content=content,
                        )
                    except Exception:
                        pass

                yield LLMRetryCompleteEvent(
                    result=LLMRunWithRetryResult(
                        succeeded=True,
                        attempts=attempt + 1,
                        usage=usage,
                        error=None,
                    )
                )
                return
            except RetryableToolOutputFailure as e:
                error = e
                retryable_error = True
                if on_retryable_error is not None:
                    await on_retryable_error(e)
            except Exception as e:
                error = e
                if on_non_retryable_error is not None:
                    await on_non_retryable_error(e)
            finally:
                if on_after_attempt is not None:
                    await on_after_attempt()

            if not retryable_error or attempt >= max_retry_count - 1:
                yield LLMRetryCompleteEvent(
                    result=LLMRunWithRetryResult(
                        succeeded=False,
                        attempts=attempt + 1,
                        usage=last_usage,
                        error=error,
                    )
                )
                return

    # Always replace the attribute directly so callers receive an async generator
    # (autospec AsyncMock side_effect wraps the result into a coroutine).
    setattr(mock_runner, "run_with_retry", _run_with_retry_impl)


def build_parity_container(
    api_style: str, workflow_dir: str
) -> tuple[Container, MagicMock]:
    """refactored + 指定 api_style のコンテナと注入済みランナーモックを返す。

    parity / rollback behavior テスト用。同一の fake イベントを両 style に注入するために使う。
    """
    container = Container()
    stub = providers.Object(SimpleNamespace())

    chat_repository = Mock(spec=ChatRepository)
    chat_repository.init_chat_session.return_value = (None, False)
    chat_repository.session_status.return_value = ChatSessionStatus.CHATTING
    chat_repository.is_session_blocked.return_value = False
    chat_repository.get_main_chat_histories.return_value = []
    chat_repository.get_main_chat_histories_after_by_session.return_value = []
    chat_repository.count_user_messages_by_session.return_value = 0

    llm_svc = MagicMock()
    llm_svc.clone_agents.return_value = {}

    action_log_repository = MagicMock()

    aica_api_repository = MagicMock(spec=AICAAPIRepository)
    aica_api_repository.get = AsyncMock(return_value=(None, None))
    position_svc = PositionService(
        position_repository=Mock(spec=PositionRepository),
        aica_api_repository=aica_api_repository,
        chat_repository=chat_repository,
        user_repository=Mock(spec=UserRepository),
        action_log_repository=action_log_repository,
    )

    container.db.override(providers.Object(SimpleNamespace(session=SimpleNamespace())))
    container.config.override(
        providers.Object(
            {
                "db": {"url": "not-used://db"},
                "agent_runtime": {
                    "service_variant": "refactored",
                    "api_style": api_style,
                },
                "workflows": {"dir": workflow_dir},
                "model_list": [
                    {"model": "gpt-4o", "use_for": ["agent"], "model_settings": {}},
                    {
                        "model": "gpt-4o-mini",
                        "use_for": ["summary"],
                        "model_settings": {},
                    },
                ],
            }
        )
    )
    container.position_svc.override(providers.Object(position_svc))
    container.llm_svc.override(providers.Object(llm_svc))

    workflow_definition_repository = Mock(spec=WorkflowDefinitionRepository)
    workflow_svc = WorkflowService(
        aica_api_repository=Mock(spec=AICAAPIRepository),
        workflow_repository=Mock(spec=WorkflowRepository),
        workflow_definition_repository=workflow_definition_repository,
        position_change_analyze_summary_svc=Mock(spec=PositionChangeAnalyzeSummaryService),
    )
    container.workflow_svc.override(providers.Object(workflow_svc))
    container.chat_repository.override(providers.Object(chat_repository))
    container.position_repository.override(stub)
    container.user_repository.override(stub)
    container.action_log_repository.override(providers.Object(action_log_repository))

    rate_limit_svc = RateLimitService(
        rate_limit_repository=Mock(spec=BaseRateLimitRepository),
        rate_limit={
            "chat_request": {},
            "position_detail": {},
            "position_search": {},
            "load_more_positions": {},
        },
    )
    container.rate_limit_svc.override(providers.Object(rate_limit_svc))

    with patch("services.conversation_summary_service.AsyncOpenAI"):
        conversation_summary_svc = ConversationSummaryService(
            model_list=[
                {"model": "gpt-4o-mini", "use_for": ["summary"], "model_settings": {}}
            ]
        )
    conversation_summary_svc._openai_client = SimpleNamespace(
        responses=SimpleNamespace(create=AsyncMock())
    )
    container.conversation_summary_svc.override(
        providers.Object(conversation_summary_svc)
    )

    summary_repository = Mock(spec=SummaryRepository)
    summary_repository.get_latest_completed.return_value = None
    summary_svc = SummaryService(
        summary_repository=summary_repository,
        chat_repository=chat_repository,
        conversation_summary_service=conversation_summary_svc,
    )
    container.summary_svc.override(providers.Object(summary_svc))

    mock_llm_runner = MagicMock()
    mock_llm_runner.run_streamed.return_value = _FakeRunStream([])
    _attach_run_with_retry_passthrough(
        mock_llm_runner,
        action_log_repository=action_log_repository,
    )
    container.refactored_llm_runner.override(providers.Object(mock_llm_runner))

    return container, mock_llm_runner


def make_chat_request(
    *,
    message: str = "こんにちは",
    message_id: str,
) -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        message=message,
        current_message_id=message_id,
    )


def make_agent_mock() -> MagicMock:
    """DefaultAgent 用最小限のエージェントモックを返す。"""
    agent_mock = MagicMock()
    agent_mock.name = "DefaultAgent"
    agent_mock.tool_use_behavior = {}
    return agent_mock
