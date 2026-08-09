"""
Endpoint / config boundary テスト。

テストケース一覧:
- test_startup_validation_rejects_invalid_agent_model
    対象: agent_runtime.agent_model が model_list と不整合な設定は
    startup validation で明示的に拒否されること。
- test_default_config_compatibility_uses_fixture_expected_agent_model
    対象: default config が fixture の期待 agent model を解決し、
    validation を通過すること。
- test_checked_in_config_declares_responses_api_style
    対象: checked-in config.yml の default api_style が意図せず変更される
    ことを防ぐドリフト検知ガードとして、"responses" を維持していること。
- test_endpoint_boundary_does_not_import_concrete_chat_service
    対象: endpoints が concrete ChatService 実装や固定 model literal に
    直接依存していないこと。
- test_handle_chat_session_uses_resolved_agent_model
    対象: handle_chat_session が config 解決済み model_name を
    init_session へ渡すこと。
"""

import inspect
import json
import runpy
from types import SimpleNamespace
from pathlib import Path

import pytest
import yaml
from fastapi import WebSocketDisconnect
from unittest.mock import AsyncMock, Mock

import endpoints
from domain.entities.chat_session import ChatSessionStatus
from services.chat.service_protocol import ChatServiceProtocol
from services.chat_service import ChatService as LegacyChatService
from services.chat_service_refactored import ChatService as RefactoredChatService
from services.chat.config_validator import (
    InvalidAgentRuntimeConfigError,
    validate_agent_runtime_config,
)
from services.chat.agent_runtime_config import resolve_default_api_style
from utils.chat_request import ChatRequestType
from utils.enum import PageName
from utils.log_utils import clear_session_id, set_session_id


pytestmark = pytest.mark.rollback_endpoint_config

FIXTURES_DIR = Path(__file__).with_name("fixtures")


def _load_yaml_fixture(filename: str) -> dict:
    """YAML fixture を読み込む。"""
    return yaml.safe_load((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _load_py_fixture(filename: str) -> dict:
    """Python fixture を読み込む。"""
    return runpy.run_path(str(FIXTURES_DIR / filename))


class DummyWebSocket:
    """WebSocket 依存を差し替えるための最小モック。"""

    def __init__(self, receive_texts=None):
        self.headers = {}
        self.client = None
        self._receive_texts = list(receive_texts or [])

    async def accept(self):
        return None

    async def close(self, code=None):
        return None

    async def send_text(self, text):
        return None

    async def receive_text(self):
        if self._receive_texts:
            return self._receive_texts.pop(0)
        raise WebSocketDisconnect(code=1000)


class _NullTrace:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_startup_validation_rejects_invalid_agent_model():
    """不正な agent model は startup validation で落ちることを確認する。"""
    config = _load_yaml_fixture("config_invalid_agent_model.yml")

    with pytest.raises(
        InvalidAgentRuntimeConfigError, match="not present in model_list"
    ):
        validate_agent_runtime_config(config)


def test_default_config_compatibility_uses_fixture_expected_agent_model():
    """default config が fixture で定義した期待値を解決することを確認する。"""
    fixture = _load_yaml_fixture("default_config_compatibility.yml")

    assert (
        endpoints.resolve_default_agent_model(fixture["config"])
        == fixture["expected_default_agent_model"]
    )
    assert (
        resolve_default_api_style(fixture["config"])
        == fixture["expected_default_api_style"]
    )
    validate_agent_runtime_config(fixture["config"])


@pytest.mark.completions_contract
def test_checked_in_config_declares_responses_api_style():
    """checked-in config.yml の default api_style の意図しない変更を検知するガード。

    このテストは fixture ではなく実ファイルを検査し、
    default api_style が誤って書き換わった場合に失敗させる。
    """
    config_path = (
        FIXTURES_DIR.resolve().parents[3] / "src" / "aica_agent" / "config.yml"
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    # checked-in default contract のドリフト検知。
    assert resolve_default_api_style(config) == "responses"
    validate_agent_runtime_config(config)


@pytest.mark.rollback_api_style
def test_startup_validation_rejects_legacy_completions_api_style():
    """legacy + completions の組み合わせは startup validation で落ちることを確認する。"""
    config = _load_yaml_fixture("config_invalid_legacy_completions.yml")

    with pytest.raises(
        InvalidAgentRuntimeConfigError, match="not supported for service_variant=legacy"
    ):
        validate_agent_runtime_config(config)


def test_endpoint_boundary_does_not_import_concrete_chat_service():
    """endpoint が concrete chat service を import しないことを確認する。"""
    fixture = _load_py_fixture("endpoint_boundary.py")
    source = inspect.getsource(endpoints)
    for forbidden in fixture["FORBIDDEN_IMPORT_STRINGS"]:
        assert forbidden not in source
    assert fixture["FORBIDDEN_MODEL_LITERAL"] not in source


def test_init_session_public_parameter_name_matches_plan():
    """公開 contract の init_session 引数名が model_name に揃っていることを確認する。"""
    for target in (ChatServiceProtocol, LegacyChatService, RefactoredChatService):
        parameters = inspect.signature(target.init_session).parameters

        assert list(parameters)[:2] == ["self", "model_name"]


@pytest.mark.asyncio
async def test_handle_chat_session_uses_resolved_agent_model(monkeypatch):
    """handle_chat_session が設定から解決した agent model を init_session に渡すことを確認する。"""
    chat_svc = AsyncMock()
    chat_svc.init_session = AsyncMock(return_value=(ChatSessionStatus.CHATTING, False))
    rate_limit_svc = AsyncMock()

    monkeypatch.setattr(endpoints, "process_chat_messages", AsyncMock())

    websocket = DummyWebSocket()
    agent_runtime_config = SimpleNamespace(
        agent_runtime=SimpleNamespace(
            service_variant="legacy",
            agent_model="custom/model",
        )
    )
    set_session_id("test-session")
    try:
        await endpoints.handle_chat_session(
            websocket,
            chat_svc,
            rate_limit_svc,
            agent_runtime_config,
        )
    finally:
        clear_session_id()

    chat_svc.init_session.assert_awaited_once_with("custom/model")
    endpoints.process_chat_messages.assert_awaited_once_with(
        websocket,
        "Unknown",
        chat_svc,
        rate_limit_svc,
        agent_runtime_config,
    )


@pytest.mark.asyncio
async def test_handle_chat_session_logs_start_chat_turn_runtime(monkeypatch):
    """新規セッション START turn で runtime variant/backend をログ出力する。"""
    chat_svc = AsyncMock()
    chat_svc.init_session = AsyncMock(return_value=(ChatSessionStatus.CHATTING, True))
    chat_svc.get_initial_menu_response = Mock(return_value=Mock())

    async def fake_chat(*_args, **_kwargs):
        if False:  # pragma: no cover - async generator marker
            yield None

    chat_svc.chat = fake_chat
    rate_limit_svc = AsyncMock()
    info_mock = Mock()
    monkeypatch.setattr(endpoints.logger, "info", info_mock)
    monkeypatch.setattr(endpoints, "process_chat_messages", AsyncMock())
    monkeypatch.setattr(endpoints, "trace", lambda *_args, **_kwargs: _NullTrace())

    websocket = DummyWebSocket()
    agent_runtime_config = SimpleNamespace(
        agent_runtime=SimpleNamespace(
            service_variant="refactored",
            agent_model="custom/model",
        )
    )

    set_session_id("test-session")
    try:
        await endpoints.handle_chat_session(
            websocket,
            chat_svc,
            rate_limit_svc,
            agent_runtime_config,
        )
    finally:
        clear_session_id()

    info_mock.assert_any_call(
        "chat turn runtime: service_variant=%s agent_model=%s backend=%s chat_service=%s request_type=%s",
        "refactored",
        "custom/model",
        "responses",
        "unittest.mock.AsyncMock",
        ChatRequestType.START.value,
    )


@pytest.mark.asyncio
async def test_process_chat_messages_logs_chat_turn_runtime(monkeypatch):
    """通常メッセージ turn でも runtime variant/backend をログ出力する。"""

    class ChatServiceStub:
        async def chat(self, *_args, **_kwargs):
            if False:  # pragma: no cover - async generator marker
                yield None

    websocket = DummyWebSocket(
        [
            json.dumps(
                {
                    "request_type": ChatRequestType.CHAT.value,
                    "current_page": PageName.CHAT.value,
                    "message": "hello",
                }
            )
        ]
    )
    chat_svc = ChatServiceStub()
    rate_limit_svc = SimpleNamespace(
        is_within_chat_request_limit=lambda *_args, **_kwargs: True
    )
    agent_runtime_config = SimpleNamespace(
        agent_runtime=SimpleNamespace(
            service_variant="legacy",
            agent_model="custom/model",
        )
    )
    info_mock = Mock()
    monkeypatch.setattr(endpoints.logger, "info", info_mock)
    monkeypatch.setattr(endpoints, "trace", lambda *_args, **_kwargs: _NullTrace())

    set_session_id("test-session")
    try:
        with pytest.raises(WebSocketDisconnect):
            await endpoints.process_chat_messages(
                websocket,
                "127.0.0.1",
                chat_svc,
                rate_limit_svc,
                agent_runtime_config,
            )
    finally:
        clear_session_id()

    info_mock.assert_any_call(
        "chat turn runtime: service_variant=%s agent_model=%s backend=%s chat_service=%s request_type=%s",
        "legacy",
        "custom/model",
        "responses",
        f"{ChatServiceStub.__module__}.ChatServiceStub",
        ChatRequestType.CHAT.value,
    )
