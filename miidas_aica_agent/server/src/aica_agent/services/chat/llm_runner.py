from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

from agents import (
    Agent,
    AgentUpdatedStreamEvent,
    RawResponsesStreamEvent,
    RunConfig,
    RunItem,
    RunItemStreamEvent,
    RunState,
    Runner,
    StreamEvent,
    ToolCallItem,
    Usage,
)
from agents.result import RunResultStreaming
from repositories.action_log_repo import ActionLogRepository, ActionLogType
from services.chat.tool_event_handler import RetryableToolOutputFailure


@dataclass(frozen=True, slots=True)
class LLMRawResponseEvent:
    item_id: str
    delta: str
    type: str = field(init=False, default="raw_response_event")


@dataclass(frozen=True, slots=True)
class LLMRunItemStreamEvent:
    item: RunItem
    type: str = field(init=False, default="run_item_stream_event")


@dataclass(frozen=True, slots=True)
class LLMAgentUpdatedStreamEvent:
    new_agent: Agent[Any]
    type: str = field(init=False, default="agent_updated_stream_event")


@dataclass(frozen=True, slots=True)
class LLMIgnoredStreamEvent:
    type: str = field(init=False, default="ignored_stream_event")


LLMStreamEvent = (
    LLMRawResponseEvent
    | LLMRunItemStreamEvent
    | LLMAgentUpdatedStreamEvent
    | LLMIgnoredStreamEvent
)


@runtime_checkable
class LLMRunStream(Protocol):
    def stream_events(self) -> AsyncIterator[LLMStreamEvent]: ...

    async def aclose(self) -> None: ...

    @property
    def continuation_state(
        self,
    ) -> str | RunState[Any, Agent[Any]] | "CompletionsRunContinuationState" | None: ...

    @property
    def agent_state(self) -> Agent[Any]: ...

    @property
    def replay_items(self) -> list[Any]: ...

    @property
    def usage(self) -> Usage | None: ...


@runtime_checkable
class LLMRunner(Protocol):
    def run_streamed(
        self,
        starting_agent: Agent,
        input: list[Any],
        continuation_state: Any | None = None,
    ) -> LLMRunStream: ...

    async def run_with_retry(
        self,
        starting_agent: Agent,
        input: list[Any],
        process_stream: Callable[[LLMRunStream], AsyncIterator[Any]],
        input_supplier: Callable[[], list[Any]] | None = None,
        continuation_state: Any | None = None,
        continuation_state_supplier: Callable[[], Any] | None = None,
        message_id: str | None = None,
        on_before_attempt: Callable[[], Awaitable[None]] | None = None,
        on_after_attempt: Callable[[], Awaitable[None]] | None = None,
        on_retryable_error: Callable[[RetryableToolOutputFailure], Awaitable[None]]
        | None = None,
        on_non_retryable_error: Callable[[Exception], Awaitable[None]] | None = None,
    ) -> AsyncGenerator["LLMRetryEvent", None]: ...


def _normalize_stream_event(event: StreamEvent) -> LLMStreamEvent:
    """SDK の stream event を内部の統一イベント型へ正規化する。"""
    event_type = event.type

    if event_type == "raw_response_event" or isinstance(event, RawResponsesStreamEvent):
        data = event.data
        item_id = getattr(data, "item_id", None)
        delta = getattr(data, "delta", None)
        # output_text.delta サブタイプのみ text-delta イベントを発行する。
        # function_call_arguments.delta イベントは item_id/delta の shape は同じだが、
        # テキストとして転送してはいけない — run_item_stream_event 経由で処理される。
        data_type = getattr(data, "type", None)
        if (
            data_type == "response.output_text.delta"
            and isinstance(item_id, str)
            and item_id
            and isinstance(delta, str)
        ):
            return LLMRawResponseEvent(item_id=item_id, delta=delta)
        return LLMIgnoredStreamEvent()
    if event_type == "run_item_stream_event" or isinstance(event, RunItemStreamEvent):
        return LLMRunItemStreamEvent(item=event.item)
    if event_type == "agent_updated_stream_event" or isinstance(
        event, AgentUpdatedStreamEvent
    ):
        return LLMAgentUpdatedStreamEvent(new_agent=event.new_agent)
    raise ValueError(
        "Unsupported stream event type: "
        f"{event.type!r}. "
        "Expected 'raw_response_event', 'run_item_stream_event', or 'agent_updated_stream_event'."
    )


def _run_result_to_input_list(
    run_result: RunResultStreaming,
    *,
    mode: str | None = None,
) -> list[Any]:
    """Responses / Completions の API モード差分を吸収しながら run result の replay items を返す。"""
    to_input_list = run_result.to_input_list

    replay_items = to_input_list() if mode is None else to_input_list(mode=mode)

    if isinstance(replay_items, list):
        return replay_items
    return list(replay_items)


class _CompletionsReplayUtils:
    """Completions 再投入用 input の整形と要約を扱う内部ユーティリティ。"""

    _logger = logging.getLogger(__name__)

    @staticmethod
    def sanitize_replay_item(item: Any) -> Any:
        """Completions 用 replay item から必要最小限のフィールドだけを残す。"""
        if not isinstance(item, dict):
            return item

        item_type = item.get("type")
        if item_type == "message":
            sanitized: dict[str, Any] = {"type": "message"}
            if "role" in item:
                sanitized["role"] = item["role"]
            if "content" in item:
                sanitized["content"] = item["content"]
            return sanitized

        if item_type == "function_call":
            sanitized = {"type": "function_call"}
            for key in ("call_id", "name", "arguments"):
                if key in item:
                    sanitized[key] = item[key]
            return sanitized

        if item_type == "function_call_output":
            sanitized = {"type": "function_call_output"}
            for key in ("call_id", "output"):
                if key in item:
                    sanitized[key] = item[key]
            return sanitized

        return item

    @staticmethod
    def build_preferred_function_call_outputs(
        items: list[Any],
    ) -> dict[str, dict[str, Any]]:
        """入力アイテムから function_call_output を抽出する。"""
        preferred_outputs: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "function_call_output":
                continue
            call_id = item.get("call_id")
            if isinstance(call_id, str) and call_id:
                preferred_outputs[call_id] = (
                    _CompletionsReplayUtils.sanitize_replay_item(item)
                )
        return preferred_outputs

    @staticmethod
    def sanitize_replay_items(
        items: list[Any],
        preferred_outputs_by_call_id: dict[str, dict[str, Any]] | None = None,
    ) -> list[Any]:
        """Completions 再投入用に replay item 群を正規化し、完全な tool pair だけを残す。"""
        sanitized_items = [
            _CompletionsReplayUtils.sanitize_replay_item(item) for item in items
        ]

        # Chat Completions では assistant の tool call の直後に対応する
        # tool message が必要なため、完全な function_call -> function_call_output
        # ペアのみを残す。
        canonical: list[Any] = []
        pending_calls: dict[str, dict[str, Any]] = {}
        for item in sanitized_items:
            if not isinstance(item, dict):
                # 非 dict アイテム（SDK 独自オブジェクト等）は保持する。
                # あわせて message 境界と同様に pending call をクリアし、
                # 別境界をまたいだ誤ペアリングを防ぐ。
                pending_calls.clear()
                canonical.append(item)
                continue

            item_type = item.get("type")
            if item_type == "function_call":
                call_id = item.get("call_id")
                if isinstance(call_id, str) and call_id:
                    pending_calls[call_id] = item
                else:
                    _CompletionsReplayUtils._logger.warning(
                        "Discard function_call replay item without valid call_id"
                    )
                continue

            if item_type == "function_call_output":
                call_id = item.get("call_id")
                if not isinstance(call_id, str) or not call_id:
                    continue
                pending_call = pending_calls.pop(call_id, None)
                if pending_call is None:
                    # 対応する call がない output（孤立・重複）は、
                    # replay の整合性維持のためスキップする。
                    continue
                canonical.append(pending_call)

                output_item = item
                if preferred_outputs_by_call_id:
                    preferred_output = preferred_outputs_by_call_id.get(call_id)
                    if isinstance(preferred_output, dict):
                        output_item = preferred_output

                canonical.append(output_item)
                continue

            # 通常メッセージに到達した時点で未対応の tool call は
            # replay 対象として古い状態とみなし破棄する。
            pending_calls.clear()
            canonical.append(item)

        return canonical

    @staticmethod
    def summarize_input_items(items: list[Any]) -> list[str]:
        """Completions に投入する input の概要をデバッグログ向けに要約する。"""
        summary: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                summary.append(type(item).__name__)
                continue
            item_type = item.get("type")
            if item_type == "message":
                summary.append(f"message:{item.get('role')}")
                continue
            if item_type in ("function_call", "function_call_output"):
                summary.append(f"{item_type}:{item.get('call_id')}")
                continue
            summary.append(str(item_type))
        return summary


class ResponsesRunStream:
    # OpenAI Responses 形式のラン結果をラップし、イベントを安定した `LLMRunStream` コントラクトに正規化するクラス。
    #
    # - 入力: OpenAI Responses 形式の run_result
    # - 出力: 正規化された LLMStreamEvent（`LLMRawResponseEvent` または `LLMRunItemStreamEvent`）を返す
    # - 継続状態や usage なども property で取得可能

    def __init__(self, run_result: RunResultStreaming) -> None:
        self._run_result = run_result

    async def stream_events(self) -> AsyncIterator[LLMStreamEvent]:
        """Responses API の stream event を内部イベントへ変換しながら列挙する。"""
        async for event in self._run_result.stream_events():
            yield _normalize_stream_event(event)

    async def aclose(self) -> None:
        """基底の run_result を安全に close する。"""
        await self._run_result.aclose()

    @property
    def continuation_state(self) -> str | None:
        """次の Responses 呼び出しに渡す previous_response_id を返す。"""
        return self._run_result.last_response_id

    @property
    def agent_state(self) -> Agent[Any]:
        """最後に観測された agent を返す。"""
        return self._run_result.last_agent

    @property
    def replay_items(self) -> list[Any]:
        """次 turn に再投入可能な入力アイテム一式を返す。"""
        return _run_result_to_input_list(self._run_result)

    @property
    def usage(self) -> Usage | None:
        """Responses ランが報告した usage を返す。"""
        return self._run_result.context_wrapper.usage


@dataclass(frozen=True, slots=True)
class CompletionsRunContinuationState:
    """`CompletionsRunStream` が返す completions 用の内部継続状態。"""

    run_state: RunState[Any, Agent[Any]] | None
    agent_state: Agent[Any]
    # `to_input_list()` 由来の再投入可能アイテム全体。
    # Completions では (1) 次 turn の `input` 再構成 と
    # (2) stop-at-tool 共通後処理 の両方でこの replay_items を使う。
    replay_items: list[Any]
    usage: Usage | None


class CompletionsRunStream:
    """completions runner の出力を安定した `LLMRunStream` 契約に正規化する。"""

    def __init__(self, run_result: RunResultStreaming) -> None:
        self._run_result = run_result
        self._continuation_state: CompletionsRunContinuationState | None = None
        self._generated_ids: dict[tuple[str, str], str] = {}
        self._logger = logging.getLogger(__name__)

    def _get_or_create_generated_id(self, source_id: str, prefix: str) -> str:
        key = (prefix, source_id)
        generated = self._generated_ids.get(key)
        if generated is None:
            generated = f"{prefix}{uuid.uuid4()}"
            self._generated_ids[key] = generated
        return generated

    def _get_generated_id_with_fallback(self, source_id: str, prefix: str) -> str:
        """Return stable generated id; fallback to per-item uniqueness when source id is empty."""
        if source_id:
            return self._get_or_create_generated_id(source_id, prefix)
        return f"{prefix}{uuid.uuid4()}"

    def _get_item_source_key(self, item: Any, raw_item: Any, raw_id: str) -> str:
        if not self._is_tool_call_item(item, raw_item):
            return raw_id

        if isinstance(raw_item, dict):
            call_id = raw_item.get("call_id")
            return call_id if isinstance(call_id, str) and call_id else raw_id

        call_id = getattr(raw_item, "call_id", None)
        return call_id if isinstance(call_id, str) and call_id else raw_id

    def _is_tool_call_item(self, item: Any, raw_item: Any) -> bool:
        if isinstance(item, ToolCallItem):
            return True
        if isinstance(raw_item, dict):
            raw_type = raw_item.get("type")
            if raw_type == "function_call":
                return True
            return all(k in raw_item for k in ("call_id", "name", "arguments"))

        raw_type = getattr(raw_item, "type", None)
        if raw_type == "function_call":
            return True
        return all(
            getattr(raw_item, key, None) is not None
            for key in ("call_id", "name", "arguments")
        )

    def _rewrite_fake_run_item_message_id_if_needed(self, item: Any) -> None:
        raw_item = getattr(item, "raw_item", None)
        if raw_item is None:
            return

        if isinstance(raw_item, dict):
            raw_id = raw_item.get("id", "")
            if not isinstance(raw_id, str):
                # Defensive fallback for unexpected SDK payload shape.
                raw_id = ""
            prefix = "fc_" if self._is_tool_call_item(item, raw_item) else "msg_"
            source_key = self._get_item_source_key(item, raw_item, raw_id)
            raw_item["id"] = self._get_generated_id_with_fallback(source_key, prefix)
            return

        raw_id = getattr(raw_item, "id", "")
        if not isinstance(raw_id, str):
            # Defensive fallback for unexpected SDK payload shape.
            raw_id = ""
        prefix = "fc_" if self._is_tool_call_item(item, raw_item) else "msg_"
        source_key = self._get_item_source_key(item, raw_item, raw_id)
        setattr(
            raw_item,
            "id",
            self._get_generated_id_with_fallback(source_key, prefix),
        )

    async def stream_events(self) -> AsyncIterator[LLMStreamEvent]:
        """基底 SDK の結果から正規化済みの semantic stream event を返す。"""
        async for event in self._run_result.stream_events():
            normalized_event = _normalize_stream_event(event)
            if isinstance(normalized_event, LLMRawResponseEvent):
                item_id = self._get_or_create_generated_id(
                    normalized_event.item_id,
                    "msg_",
                )
                yield LLMRawResponseEvent(
                    item_id=item_id,
                    delta=normalized_event.delta,
                )
                continue

            if isinstance(normalized_event, LLMRunItemStreamEvent):
                self._rewrite_fake_run_item_message_id_if_needed(normalized_event.item)
            yield normalized_event

    async def aclose(self) -> None:
        """基底 SDK が async close を提供する場合にストリームを閉じる。"""
        await self._run_result.aclose()

    def _build_continuation_state(self) -> CompletionsRunContinuationState:
        """次の Completions 呼び出しに渡す継続ペイロードを構築してキャッシュする。"""
        if self._continuation_state is None:
            run_state = None
            try:
                run_state = self._run_result.to_state()
            except AttributeError:
                run_state = None
                self._logger.warning(
                    "continuation_state accessed before stream_events() fully consumed. "
                    "Call stream_events() and consume all events to populate run_state correctly."
                )

            self._continuation_state = CompletionsRunContinuationState(
                run_state=run_state,
                agent_state=self._run_result.last_agent,
                # Completions では replay_items を
                # (1) 次 turn の input 再構成
                # (2) stop-at-tool 共通後処理
                # の 2 目的で使う。
                # 正規化は run_streamed() の最終投入直前で一度だけ行う。
                replay_items=_run_result_to_input_list(self._run_result),
                usage=self.usage,
            )
        return self._continuation_state

    @property
    def continuation_state(self) -> CompletionsRunContinuationState:
        """次の run に渡すキャッシュ済み継続ペイロードを返す。

        production で意味のある run_state / replay_items を得るには、
        先に stream_events() を最後まで消費すること。
        """
        return self._build_continuation_state()

    @property
    def agent_state(self) -> Agent[Any]:
        """基底 run で最後に観測された agent を返す。"""
        return self._build_continuation_state().agent_state

    @property
    def replay_items(self) -> list[Any]:
        """次の Completions 呼び出しで再利用する入力アイテム全体を返す。"""
        return self._build_continuation_state().replay_items

    @property
    def usage(self) -> Usage | None:
        """基底 SDK run が報告した usage ペイロードを返す。"""
        return self._run_result.context_wrapper.usage


@dataclass(frozen=True)
class LLMRunWithRetryResult:
    """Result from retry-capable LLM runner."""

    succeeded: bool
    attempts: int

    usage: Usage | None
    """Usage data from the last attempt (if available)."""

    error: Exception | None = None
    """Exception that occurred (if any)."""


@dataclass(frozen=True)
class LLMRetryChunkEvent:
    chunk: Any
    type: str = field(init=False, default="chunk")


@dataclass(frozen=True)
class LLMRetryCompleteEvent:
    result: LLMRunWithRetryResult
    type: str = field(init=False, default="complete")


LLMRetryEvent = LLMRetryChunkEvent | LLMRetryCompleteEvent


def json_default(obj: Any) -> Any:
    """JSON serialization fallback for dataclasses and Pydantic models."""
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


class ResponsesAgentRunner:
    """Retry-aware `LLMRunner`-conforming wrapper around `Runner.run_streamed`.

    Responsibilities:
    - Forward `continuation_state` as `previous_response_id` to Responses SDK
    - Normalize Responses format into stable `LLMRunStream` protocol
    - Hide usage recording and log retriable/non-retryable errors
    - Provide backoff constants and helper for service retry orchestration
    """

    MAX_RETRY_COUNT = 5
    BASE_DELAY_SECONDS = 0.5
    MAX_DELAY_SECONDS = 8.0

    def __init__(
        self,
        action_log_repository: ActionLogRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._action_log_repo = action_log_repository
        self._logger = logger or logging.getLogger(__name__)

    def run_streamed(
        self,
        starting_agent: Agent,
        input: list[Any],
        continuation_state: Any | None = None,
    ) -> ResponsesRunStream:
        """単発の Responses 実行を行い、usage 記録は行わずにストリームを返す。"""
        run_result = Runner.run_streamed(
            starting_agent=starting_agent,
            input=input,
            previous_response_id=continuation_state,
        )
        return ResponsesRunStream(run_result)

    async def run_with_retry(
        self,
        starting_agent: Agent,
        input: list[Any],
        process_stream: Callable[[LLMRunStream], AsyncIterator[Any]],
        input_supplier: Callable[[], list[Any]] | None = None,
        continuation_state: Any | None = None,
        continuation_state_supplier: Callable[[], Any] | None = None,
        message_id: str | None = None,
        on_before_attempt: Callable[[], Awaitable[None]] | None = None,
        on_after_attempt: Callable[[], Awaitable[None]] | None = None,
        on_retryable_error: Callable[[RetryableToolOutputFailure], Awaitable[None]]
        | None = None,
        on_non_retryable_error: Callable[[Exception], Awaitable[None]] | None = None,
    ) -> AsyncGenerator[LLMRetryEvent, None]:
        """リトライとバックオフを管理しながら LLM 実行結果を逐次返す。"""
        last_usage: Any = None

        for attempt in range(self.MAX_RETRY_COUNT):
            error: Exception | None = None
            retryable_error = False

            try:
                if on_before_attempt is not None:
                    await on_before_attempt()

                current_continuation_state = (
                    continuation_state_supplier()
                    if continuation_state_supplier is not None
                    else continuation_state
                )
                current_input = (
                    input_supplier() if input_supplier is not None else input
                )
                run_stream = self.run_streamed(
                    starting_agent=starting_agent,
                    input=current_input,
                    continuation_state=current_continuation_state,
                )
                async for chunk in process_stream(run_stream):
                    yield LLMRetryChunkEvent(chunk=chunk)

                usage = run_stream.usage
                last_usage = usage

                if usage is not None and message_id:
                    try:
                        await asyncio.to_thread(self._record_usage, usage, message_id)
                    except Exception:
                        self._logger.exception("Failed to record LLM usage")

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
                self._logger.info("Retryable LLM error: %s", e.call_id)
                if on_retryable_error is not None:
                    await on_retryable_error(e)
            except Exception as e:
                error = e
                self._logger.exception("Non-retryable LLM error")
                if on_non_retryable_error is not None:
                    await on_non_retryable_error(e)
            finally:
                if on_after_attempt is not None:
                    await on_after_attempt()

            if not retryable_error or attempt >= self.MAX_RETRY_COUNT - 1:
                yield LLMRetryCompleteEvent(
                    result=LLMRunWithRetryResult(
                        succeeded=False,
                        attempts=attempt + 1,
                        usage=last_usage,
                        error=error,
                    )
                )
                return

            delay = min(
                self.BASE_DELAY_SECONDS * (2**attempt),
                self.MAX_DELAY_SECONDS,
            )
            self._logger.info(
                "retrying with backoff %.2f s (attempt %d/%d)",
                delay,
                attempt + 1,
                self.MAX_RETRY_COUNT,
            )
            await asyncio.sleep(delay)

    def _record_usage(self, usage: Any, message_id: str) -> None:
        """usage を action log に記録する。"""
        if usage is None:
            return
        token_usage_str = json.dumps(usage, default=json_default)
        self._action_log_repo.insert(
            log_type=ActionLogType.TOKEN_USAGE,
            source=message_id,
            content=token_usage_str,
        )


def _build_litellm_model_provider() -> Any:
    """LiteLLM provider を遅延生成し、optional dependency の import を遅らせる。"""
    try:
        from agents.extensions.models.litellm_provider import LitellmProvider
    except (
        ImportError
    ) as exc:  # pragma: no cover - depends on optional dependency install
        raise ImportError(
            "`litellm` is required to use CompletionsAgentRunner. "
            "Install the server dependencies with LiteLLM support."
        ) from exc

    return LitellmProvider()


def _build_anyllm_model_provider() -> Any:
    """any-llm provider を遅延生成し、optional dependency の import を遅らせる。"""
    try:
        from agents.extensions.models.any_llm_provider import AnyLLMProvider
    except (
        ImportError
    ) as exc:  # pragma: no cover - depends on optional dependency install
        raise ImportError(
            "`any-llm-sdk` is required to use the any-llm completions provider. "
            "Install the server dependencies with any-llm support "
            "(any-llm-sdk)."
        ) from exc

    # CompletionsAgentRunner は Chat Completions API style 用。api=None だと AnyLLMModel が
    # provider 次第で Responses API を選び、履歴の assistant(output_text) item が Responses の
    # input schema 検証で弾かれる。LiteLLM 同様 chat_completions に固定する。
    return AnyLLMProvider(api="chat_completions")


# LiteLLM は Python 3.14 を 1.83.7 までしか支えず、その版は aiohttp/python-dotenv を
# 脆弱なバージョンに固定してしまう。そのため Python 3.14 対応で脆弱依存を回避できる any-llm を
# 既定の completions provider とし、LiteLLM は fallback として feature flag で選べるよう残す。
# 現行 config の利用 provider は OpenAI。Bedrock/Claude 等は any-llm が対応する将来オプション。
COMPLETIONS_PROVIDER_ENV = "AICA_COMPLETIONS_PROVIDER"
LITELLM_COMPLETIONS_PROVIDER = "litellm"
ANYLLM_COMPLETIONS_PROVIDER = "anyllm"
DEFAULT_COMPLETIONS_PROVIDER = ANYLLM_COMPLETIONS_PROVIDER
_COMPLETIONS_PROVIDER_BUILDERS = {
    LITELLM_COMPLETIONS_PROVIDER: _build_litellm_model_provider,
    ANYLLM_COMPLETIONS_PROVIDER: _build_anyllm_model_provider,
}


def _build_completions_model_provider() -> Any:
    """`AICA_COMPLETIONS_PROVIDER` に応じて completions 用 provider を生成する。

    既定は `anyllm`。`litellm` を指定すると従来の LiteLLM 経路に fallback する。
    """
    backend = (
        os.environ.get(COMPLETIONS_PROVIDER_ENV, DEFAULT_COMPLETIONS_PROVIDER)
        .strip()
        .lower()
        or DEFAULT_COMPLETIONS_PROVIDER
    )
    builder = _COMPLETIONS_PROVIDER_BUILDERS.get(backend)
    if builder is None:
        allowed = ", ".join(sorted(_COMPLETIONS_PROVIDER_BUILDERS))
        raise ValueError(
            f"{COMPLETIONS_PROVIDER_ENV}: {backend!r} is not supported. "
            f"Only {allowed} are valid."
        )
    return builder()


class CompletionsAgentRunner(ResponsesAgentRunner):
    """Gate B 用に LiteLLM ベースの completions 実行を行う runner wrapper。"""

    def __init__(
        self,
        action_log_repository: ActionLogRepository,
        logger: logging.Logger | None = None,
        model_provider: Any | None = None,
        run_config: RunConfig | None = None,
    ) -> None:
        super().__init__(action_log_repository=action_log_repository, logger=logger)
        self._model_provider = model_provider
        self._run_config = run_config

    def _get_run_config(self) -> RunConfig:
        """run config を一度だけ生成し、以降の Completions 実行で再利用する。"""
        if self._run_config is not None:
            return self._run_config

        if self._model_provider is None:
            self._model_provider = _build_completions_model_provider()

        self._run_config = RunConfig(model_provider=self._model_provider)
        return self._run_config

    def _extract_replay_items(self, continuation_state: Any | None) -> list[Any]:
        """Completions 継続状態から replay_items を抽出する。"""
        migration_hint = (
            "Migration hint: this can occur during mixed-version rollout or when "
            "stale continuation_state is reused. Clear stale state and restart workers "
            "with a single version."
        )
        if continuation_state is None:
            return []

        if isinstance(continuation_state, CompletionsRunContinuationState):
            return list(continuation_state.replay_items)

        if isinstance(continuation_state, dict):
            replay_items = continuation_state.get("replay_items")
            if replay_items is None:
                raise ValueError(
                    "Invalid continuation_state dict for CompletionsAgentRunner: "
                    "missing 'replay_items'. "
                    "Expected dict shape: {'replay_items': list}. "
                    f"{migration_hint}"
                )
            if not isinstance(replay_items, list):
                raise TypeError(
                    "Invalid continuation_state['replay_items'] type for "
                    "CompletionsAgentRunner: expected list. "
                    f"{migration_hint}"
                )
            return list(replay_items)

        raise TypeError(
            "Unsupported continuation_state type for CompletionsAgentRunner: "
            f"{type(continuation_state).__name__}. "
            "Expected CompletionsRunContinuationState, dict with 'replay_items', or None. "
            f"{migration_hint}"
        )

    def run_streamed(
        self,
        starting_agent: Agent,
        input: list[Any],
        continuation_state: Any | None = None,
    ) -> CompletionsRunStream:
        """Completions 形式の継続状態で agent を実行し、結果ストリームを返す。"""
        # Completions API には previous_response_id ベースの継続がないため、
        # 前 turn の replay items を次の input へ明示的に合成する。
        replay_items = self._extract_replay_items(continuation_state)

        preferred_outputs = (
            _CompletionsReplayUtils.build_preferred_function_call_outputs(input)
        )

        # current turn input 側にも stop-at-tool 後処理や retry 経路で
        # function_call/_output が混在しうるため、最終投入前に全体を正規化する。
        current_input = _CompletionsReplayUtils.sanitize_replay_items(
            [*replay_items, *input],
            preferred_outputs_by_call_id=preferred_outputs,
        )
        self._logger.debug(
            "Completions merged input summary: %s",
            _CompletionsReplayUtils.summarize_input_items(current_input),
        )
        run_result = Runner.run_streamed(
            starting_agent=starting_agent,
            input=current_input,
            run_config=self._get_run_config(),
        )
        return CompletionsRunStream(run_result)
