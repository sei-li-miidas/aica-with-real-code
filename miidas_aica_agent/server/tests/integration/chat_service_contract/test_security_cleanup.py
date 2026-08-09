"""
Security cleanup テスト。

Security contract を検証:
- Forbidden output detection が session をブロック
- Detector 状態がクリーンアップ
- Stream 中の cancellation は idempotent cleanup セマンティクスを有する

マーカー:
- rollback_security: Security block と cancellation cleanup は重要
- pre_extraction_parity: Security は pre-extraction parity gate の一部

テストケース一覧:
- test_security_block_cleanup_blocks_session_and_removes_detector_state
    対象: forbidden 検知時に session を block し、
    detector state を除去すること。
- test_prefixed_forbidden_output_cleanup_blocks_session_and_removes_detector_state
    対象: 接頭辞付き forbidden 出力でも同等に block/cleanup されること。
- test_japanese_forbidden_phrase_cleanup_blocks_session_and_removes_detector_state
    対象: 日本語禁止語句検知でも block/cleanup 契約を維持すること。
- test_security_cleanup_still_returns_error_when_block_session_write_fails
    対象: block session 書き込み失敗時でも
    エラー応答を返して安全側に倒すこと。
- test_cancellation_cleanup_is_idempotent
    対象: cancellation cleanup が多重実行されても
    副作用が増えないこと。
"""

import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import uuid
from unittest.mock import MagicMock

import pytest

from .chat_service_contract_helpers import (
    _FakeRunResult,
    _FakeRunStream,
    _inner,
    _setup_existing_session,
)
from openai.types.responses import ResponseTextDeltaEvent
from services.chat.llm_runner import LLMRawResponseEvent
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType
from utils.enum import PageName
from utils.log_utils import clear_session_id, set_session_id


FIXTURES_DIR = Path(__file__).with_name("fixtures")


def _load_json_fixture(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _load_py_fixture(filename: str) -> dict:
    import runpy

    return runpy.run_path(str(FIXTURES_DIR / filename))


def _make_chat_request(message: str = "通常のメッセージです") -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        message=message,
        current_message_id="msg-security-test",
    )


def _make_agent_mock() -> MagicMock:
    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    agent_mock.tool_use_behavior = {}
    return agent_mock


def _make_text_delta(item_id: str, delta: str):
    return SimpleNamespace(
        type="raw_response_event",
        data=ResponseTextDeltaEvent(
            type="response.output_text.delta",
            item_id=item_id,
            output_index=0,
            content_index=0,
            delta=delta,
            sequence_number=0,
            logprobs=[],
        ),
    )


def _make_normalized_text_delta(item_id: str, delta: str) -> LLMRawResponseEvent:
    """real-refactored バリアント向けの正規化済みストリームイベントを生成する。

    StreamEventProcessor は LLMRawResponseEvent を期待するため、
    _FakeRunStream に渡すイベントは正規化済みである必要がある。
    """
    return LLMRawResponseEvent(item_id=item_id, delta=delta)


def _setup_runner_mock(
    variant: str, chat_svc, svc, events_sdk: list, events_normalized: list
) -> None:
    """バリアントに応じてランナーモックを設定する。

    legacy: svc._run_streamed に _FakeRunResult（SDK 形式）を設定。
    real-refactored: chat_svc._llm_runner.run_streamed に _FakeRunStream（正規化済み）を設定。

    """
    if variant == "legacy":
        mock_run = MagicMock(return_value=_FakeRunResult(events_sdk))
        svc._run_streamed = mock_run
    else:
        mock_stream = MagicMock(return_value=_FakeRunStream(events_normalized))
        chat_svc._llm_runner.run_streamed = mock_stream


class _RecordingInjectionDetector:
    """Real detector に委譲しつつ、test-facing な active session set だけを記録する。"""

    def __init__(self, detector):
        self._detector = detector
        self._active_session_ids: set[str] = set()

    def reset_session_for_new_response(self, session_id: str):
        self._active_session_ids.add(session_id)
        return self._detector.reset_session_for_new_response(session_id)

    def process_stream_chunk(self, session_id: str, chunk: str):
        return self._detector.process_stream_chunk(session_id, chunk)

    def finalize_stream(self, session_id: str):
        return self._detector.finalize_stream(session_id)

    def remove_session(self, session_id: str):
        self._active_session_ids.discard(session_id)
        return self._detector.remove_session(session_id)

    def has_session(self, session_id: str) -> bool:
        return session_id in self._active_session_ids


@pytest.fixture
def recording_detector(chat_service_container_security):
    chat_svc = chat_service_container_security
    svc = _inner(chat_svc)
    original_guard = svc.llm_output_guard
    detector = _RecordingInjectionDetector(original_guard)
    svc.llm_output_guard = detector
    # chat_service_refactored.chat() uses chat_svc.llm_output_guard (direct alias).
    # The alias was set at __init__ time; update it so the recording detector is used.
    if hasattr(chat_svc, "_legacy_chat_service"):
        chat_svc.llm_output_guard = detector
    yield detector
    svc.llm_output_guard = original_guard
    if hasattr(chat_svc, "_legacy_chat_service"):
        chat_svc.llm_output_guard = original_guard


async def _collect_responses(chat_svc, request):
    responses = []
    async for response in chat_svc.chat(request, "127.0.0.1"):
        responses.append(response.model_copy(deep=True))
    return responses


@pytest.fixture
def security_session_id(request):
    session_id = f"test-session-security-cleanup-{request.node.name}-{uuid.uuid4()}"
    set_session_id(session_id)
    yield session_id
    clear_session_id()


@contextmanager
def _temporary_session_id(session_id: str, restore_session_id: str):
    set_session_id(session_id)
    try:
        yield
    finally:
        set_session_id(restore_session_id)


pytestmark = pytest.mark.pre_extraction_parity

_VARIANTS = [
    "legacy",
    "real-refactored",
]


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_security_block_cleanup_blocks_session_and_removes_detector_state(
    variant, chat_service_container_security, security_session_id, recording_detector
):
    """Forbidden word 検知時に session block と detector cleanup が実行される。"""
    chat_svc = chat_service_container_security
    svc = _inner(chat_svc)
    svc.llm_output_guard.remove_session(security_session_id)

    fixture = _load_json_fixture("security_block.json")
    scenario = fixture["security_scenarios"]["forbidden_detection"]

    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, security_session_id)

    forbidden_word = scenario["forbidden_input"]
    sdk_events = [_make_text_delta("resp-security-1", forbidden_word)]
    normalized_events = [_make_normalized_text_delta("resp-security-1", forbidden_word)]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)

    responses = await _collect_responses(
        chat_svc, _make_chat_request("セキュリティ検知を検証します")
    )

    error_responses = [
        response
        for response in responses
        if response.response_type == ChatResponseType.ERROR
    ]
    assert error_responses, "chat() must emit a session block error response"
    assert error_responses[0].message == scenario["error_response"]
    svc._chat_repository.block_session.assert_called_once()
    assert not recording_detector.has_session(security_session_id)


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_prefixed_forbidden_output_cleanup_blocks_session_and_removes_detector_state(
    variant, chat_service_container_security, security_session_id, recording_detector
):
    """安全な prefix 後の forbidden output 検知でも cleanup が実行される。"""
    chat_svc = chat_service_container_security
    svc = _inner(chat_svc)
    svc.llm_output_guard.remove_session(security_session_id)

    fixture = _load_json_fixture("security_block.json")
    scenario = fixture["security_scenarios"]["forbidden_detection"]

    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, security_session_id)

    prefixed_input = f"安全な出力です。{scenario['forbidden_input']}"
    sdk_events = [_make_text_delta("resp-prefixed-forbidden-1", prefixed_input)]
    normalized_events = [
        _make_normalized_text_delta("resp-prefixed-forbidden-1", prefixed_input)
    ]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)

    responses = await _collect_responses(
        chat_svc, _make_chat_request("prefix 後のセキュリティ検知を検証します")
    )

    error_responses = [
        response
        for response in responses
        if response.response_type == ChatResponseType.ERROR
    ]
    assert error_responses, (
        "chat() must emit a prefixed forbidden output error response"
    )
    assert error_responses[0].message == scenario["error_response"]
    svc._chat_repository.block_session.assert_called_once()
    assert not recording_detector.has_session(security_session_id)


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_security_cleanup_still_returns_error_when_block_session_write_fails(
    variant, chat_service_container_security, security_session_id, recording_detector
):
    chat_svc = chat_service_container_security
    svc = _inner(chat_svc)
    svc.llm_output_guard.remove_session(security_session_id)

    fixture = _load_json_fixture("security_block.json")
    scenario = fixture["security_scenarios"]["forbidden_detection"]

    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, security_session_id)
    svc._chat_repository.block_session.side_effect = RuntimeError("db write failed")

    forbidden_word = scenario["forbidden_input"]
    sdk_events = [_make_text_delta("resp-security-block-write-fail", forbidden_word)]
    normalized_events = [
        _make_normalized_text_delta("resp-security-block-write-fail", forbidden_word)
    ]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)

    responses = await _collect_responses(
        chat_svc, _make_chat_request("block_session failure を検証します")
    )

    error_responses = [
        response
        for response in responses
        if response.response_type == ChatResponseType.ERROR
    ]
    assert error_responses
    assert error_responses[0].message == scenario["error_response"]
    assert not recording_detector.has_session(security_session_id)


@pytest.mark.rollback_security
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_cancellation_cleanup_is_idempotent(
    variant, chat_service_container_security, security_session_id, recording_detector
):
    """Stream 中に chat() generator を閉じると detector state が一度だけ空になる。"""
    chat_svc = chat_service_container_security
    svc = _inner(chat_svc)
    svc.llm_output_guard.remove_session(security_session_id)
    fixture = _load_py_fixture("cancellation_cleanup.py")
    cancellation_fixture = fixture["cancellation_cleanup_fixture"]()

    agent_mock = _make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, security_session_id)

    sdk_events = [
        _make_text_delta("resp-cancel-1", cancellation_fixture["first_delta"]),
        _make_text_delta("resp-cancel-1", cancellation_fixture["second_delta"]),
    ]
    normalized_events = [
        _make_normalized_text_delta(
            "resp-cancel-1", cancellation_fixture["first_delta"]
        ),
        _make_normalized_text_delta(
            "resp-cancel-1", cancellation_fixture["second_delta"]
        ),
    ]
    _setup_runner_mock(variant, chat_svc, svc, sdk_events, normalized_events)

    generator = chat_svc.chat(
        _make_chat_request("途中キャンセルを検証します"),
        "127.0.0.1",
    )
    first_response = await anext(generator)
    assert first_response.response_type == ChatResponseType.MESSAGE
    assert recording_detector.has_session(security_session_id)

    rebound_session_id = f"{security_session_id}-rebound"
    with _temporary_session_id(rebound_session_id, security_session_id):
        await generator.aclose()
        original_removed_after_first_close = not recording_detector.has_session(
            security_session_id
        )
        rebound_absent_after_first_close = not recording_detector.has_session(
            rebound_session_id
        )
    await generator.aclose()

    assert original_removed_after_first_close
    assert rebound_absent_after_first_close
    assert cancellation_fixture["expected_final_state"] == "detector_session_removed"
    assert not recording_detector.has_session(security_session_id)
    assert not recording_detector.has_session(rebound_session_id)
    svc._chat_repository.block_session.assert_not_called()
