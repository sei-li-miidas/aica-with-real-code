"""
DI lifecycle テスト。

テストケース一覧:
- test_container_chat_svc_returns_fresh_instances_for_each_variant
    対象: Container.chat_svc が legacy/refactored いずれでも
    呼び出しごとに新規インスタンスを返すこと。
- test_container_resolves_relative_workflow_dir_from_app_root
    対象: workflow_dir が相対指定でも app root 基準で解決され、
    refactored ChatService が正常生成されること。
- test_chat_websocket_sessions_forward_distinct_chat_service_instances
    対象: WebSocket セッションごとに異なる chat service instance が
    endpoints へ渡されること。
- test_refactored_workflow_methods_route_through_workflow_chat_handler
    対象: refactored の workflow 系 public method が
    WorkflowChatHandler 経由で処理されること。
- test_process_chat_messages_dispatches_workflow_requests_through_refactored_adapter
    対象: process_chat_messages が workflow request_type を
    refactored adapter の対応メソッドへディスパッチすること。
"""

import json
from types import SimpleNamespace

import pytest
from dependency_injector import providers
from fastapi import WebSocketDisconnect
from unittest.mock import AsyncMock, MagicMock

import endpoints
from containers import Container
from utils.const import MAIN_CHAT_KEY
from services import chat_service, chat_service_refactored
from utils.chat_request import ChatRequestType
from utils.enum import PageName
from utils.log_utils import clear_session_id, set_session_id


pytestmark = pytest.mark.rollback_di


class DummyWebSocket:
    def __init__(self, receive_texts=None):
        self.headers = {}
        self.client = None
        self._receive_texts = list(receive_texts or [])
        self.sent_texts = []

    async def accept(self):
        return None

    async def close(self, code=None):
        return None

    async def send_text(self, text):
        self.sent_texts.append(text)
        return None

    async def receive_text(self):
        if self._receive_texts:
            return self._receive_texts.pop(0)
        raise WebSocketDisconnect(code=1000)


@pytest.mark.parametrize(
    ("service_variant", "expected_module"),
    [
        ("legacy", chat_service.__name__),
        ("refactored", chat_service_refactored.__name__),
    ],
)
def test_container_chat_svc_returns_fresh_instances_for_each_variant(
    service_variant,
    expected_module,
    tmp_path,
):
    container = _build_container_with_stubbed_dependencies(
        service_variant, str(tmp_path)
    )

    first = container.chat_svc()
    second = container.chat_svc()

    assert first is not second
    assert first.__class__.__module__ == expected_module
    first_histories = _resolve_chat_histories(first)
    second_histories = _resolve_chat_histories(second)
    assert first_histories is not second_histories
    assert first_histories[MAIN_CHAT_KEY] is not second_histories[MAIN_CHAT_KEY]
    assert first_histories[MAIN_CHAT_KEY] == []
    assert second_histories[MAIN_CHAT_KEY] == []


def test_container_resolves_relative_workflow_dir_from_app_root():
    container = _build_container_with_stubbed_dependencies(
        "refactored",
        "files/workflows",
    )

    chat_svc = container.chat_svc()

    assert chat_svc.__class__.__module__ == chat_service_refactored.__name__


def _build_container_with_stubbed_dependencies(
    service_variant: str,
    workflow_dir: str,
) -> Container:
    container = Container()
    stub = providers.Object(SimpleNamespace())

    container.db.override(providers.Object(SimpleNamespace(session=SimpleNamespace())))
    container.config.override(
        providers.Object(
            {
                "db": {"url": "not-used://db"},
                "agent_runtime": {"service_variant": service_variant},
                "workflows": {"dir": workflow_dir},
                "model_list": [
                    {
                        "model": "gpt-4o",
                        "use_for": ["agent"],
                        "model_settings": {},
                    },
                    {
                        "model": "gpt-4o-mini",
                        "use_for": ["summary"],
                        "model_settings": {},
                    },
                ],
            }
        )
    )
    container.position_svc.override(stub)
    container.llm_svc.override(stub)
    container.workflow_svc.override(stub)
    container.chat_repository.override(stub)
    container.position_repository.override(stub)
    container.user_repository.override(stub)
    container.action_log_repository.override(stub)
    container.rate_limit_svc.override(stub)
    container.conversation_summary_svc.override(providers.Object(SimpleNamespace()))
    container.summary_svc.override(providers.Object(None))

    return container


def _resolve_chat_histories(chat_svc):
    # Intentionally inspect private state to verify DI lifecycle isolation.
    if hasattr(chat_svc, "_conv_state"):
        return chat_svc._conv_state.chat_histories
    if hasattr(chat_svc, "_chat_histories"):
        return chat_svc._chat_histories
    return chat_svc._legacy_chat_service._chat_histories


@pytest.mark.parametrize("service_variant", ["legacy", "refactored"])
@pytest.mark.asyncio
async def test_chat_websocket_sessions_forward_distinct_chat_service_instances(
    service_variant,
    monkeypatch,
    tmp_path,
):
    container = _build_container_with_stubbed_dependencies(
        service_variant, str(tmp_path)
    )
    first = container.chat_svc()
    second = container.chat_svc()
    seen_chat_services = []

    async def fake_handle_chat_session(
        websocket, chat_svc, rate_limit_svc, agent_runtime_config
    ):
        seen_chat_services.append(chat_svc)

    monkeypatch.setattr(
        endpoints,
        "handle_chat_session",
        AsyncMock(side_effect=fake_handle_chat_session),
    )
    monkeypatch.setattr(endpoints, "is_local", lambda: True)
    monkeypatch.setattr(endpoints.maintenance_manager, "IS_MAINTENANCE_MODE", False)
    monkeypatch.setattr(endpoints, "set_session_id", lambda session_id: None)
    monkeypatch.setattr(endpoints, "clear_session_id", lambda: None)

    websocket = DummyWebSocket()
    agent_runtime_config = SimpleNamespace(
        agent_runtime=SimpleNamespace(agent_model="openai/gpt-4.1")
    )

    await endpoints.chat(
        websocket,
        session_id="session-1",
        chat_svc=first,
        rate_limit_svc=SimpleNamespace(),
        agent_runtime_config=agent_runtime_config,
    )
    await endpoints.chat(
        websocket,
        session_id="session-2",
        chat_svc=second,
        rate_limit_svc=SimpleNamespace(),
        agent_runtime_config=agent_runtime_config,
    )

    assert seen_chat_services == [first, second]
    assert first is not second
    if service_variant == "refactored":
        assert first.__class__.__module__ == chat_service_refactored.__name__
    else:
        assert first.__class__.__module__ == chat_service.__name__


@pytest.mark.asyncio
async def test_refactored_workflow_methods_route_through_workflow_chat_handler(
    tmp_path,
):
    """workflow_submitted / workflow_cancelled が WorkflowChatHandler 経由でルーティングされることを確認する。

    phase-4 task-5 で delegating adapter が削除されたため、legacy への直接委譲は行われない。
    代わりに WorkflowChatHandler.prepare_* が呼ばれ、その結果が chat() に渡される。
    このテストでは prepare_* の戻り値をモックし、
    chat_svc が workflow_submitted は error_response を短絡し、
    workflow_cancelled は prepared_message を chat() に渡すことを確認する。
    """
    from services.chat.workflow_chat_handler import WorkflowChatHandlerResult
    from utils.chat_response import ChatResponseType, ChatStreamResponseModel
    from domain.entities.chat_session import ChatSessionStatus

    container = _build_container_with_stubbed_dependencies("refactored", str(tmp_path))
    chat_svc = container.chat_svc()

    submitted_response = ChatStreamResponseModel(
        session_id="test-session",
        session_status=ChatSessionStatus.CHATTING,
        request_type=None,
        response_type=ChatResponseType.ERROR,
        message_id="",
        message="submitted-via-handler",
        position_id=None,
        is_maintenance=False,
    )
    cancelled_response = ChatStreamResponseModel(
        session_id="test-session",
        session_status=ChatSessionStatus.CHATTING,
        request_type=None,
        response_type=ChatResponseType.ERROR,
        message_id="",
        message="cancelled-via-handler",
        position_id=None,
        is_maintenance=False,
    )

    chat_svc._workflow_chat_handler = MagicMock()
    chat_svc._workflow_chat_handler.prepare_workflow_submitted = AsyncMock(
        return_value=WorkflowChatHandlerResult(error_response=submitted_response)
    )
    chat_svc._workflow_chat_handler.prepare_workflow_cancelled = AsyncMock(
        return_value=WorkflowChatHandlerResult(prepared_message="cancelled-via-handler")
    )

    async def _fake_chat(chat_request, client_ip):
        assert chat_request.message == "cancelled-via-handler"
        yield cancelled_response

    chat_svc.chat = _fake_chat

    submitted_chunks = []
    cancelled_chunks = []

    async for chunk in chat_svc.workflow_submitted(
        SimpleNamespace(message="{}", request_type="workflow_submitted"),
        "127.0.0.1",
    ):
        submitted_chunks.append(chunk)

    async for chunk in chat_svc.workflow_cancelled(
        SimpleNamespace(message="{}", request_type="workflow_cancelled"),
        "127.0.0.1",
    ):
        cancelled_chunks.append(chunk)

    assert len(submitted_chunks) == 1
    assert submitted_chunks[0].message == "submitted-via-handler"
    assert len(cancelled_chunks) == 1
    assert cancelled_chunks[0].message == "cancelled-via-handler"
    chat_svc._workflow_chat_handler.prepare_workflow_submitted.assert_called_once()
    chat_svc._workflow_chat_handler.prepare_workflow_cancelled.assert_called_once()


@pytest.mark.parametrize(
    ("request_type", "method_name", "payload"),
    [
        (
            ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED,
            "workflow_submitted",
            {"workflow_id": "workflow-123", "answers": {"foo": "bar"}},
        ),
        (
            ChatRequestType.WORKFLOW_CANCELLED,
            "workflow_cancelled",
            {"workflow_id": "workflow-123"},
        ),
    ],
)
@pytest.mark.asyncio
async def test_process_chat_messages_dispatches_workflow_requests_through_refactored_adapter(
    request_type,
    method_name,
    payload,
    monkeypatch,
    tmp_path,
):
    container = _build_container_with_stubbed_dependencies("refactored", str(tmp_path))
    chat_svc = container.chat_svc()

    async def fake_workflow_handler(chat_request, client_ip):
        assert chat_request.request_type == request_type
        assert client_ip == "127.0.0.1"
        yield SimpleNamespace(model_dump_json=lambda: json.dumps({"type": method_name}))

    setattr(chat_svc, method_name, fake_workflow_handler)

    websocket = DummyWebSocket(
        [
            json.dumps(
                {
                    "request_type": request_type.value,
                    "current_page": PageName.CHAT,
                    "message": json.dumps(payload),
                }
            )
        ]
    )
    rate_limit_svc = SimpleNamespace(
        is_within_chat_request_limit=lambda session_id, client_ip: True
    )

    monkeypatch.setattr(endpoints, "is_local", lambda: True)
    monkeypatch.setattr(endpoints.maintenance_manager, "IS_MAINTENANCE_MODE", False)
    monkeypatch.setattr(endpoints, "set_request_id", lambda request_id: None)
    monkeypatch.setattr(endpoints, "set_session_id", lambda session_id: None)
    monkeypatch.setattr(endpoints, "clear_session_id", lambda: None)

    set_session_id("test-session-id")
    try:
        with pytest.raises(WebSocketDisconnect):
            await endpoints.process_chat_messages(
                websocket,
                "127.0.0.1",
                chat_svc,
                rate_limit_svc,
                SimpleNamespace(
                    agent_runtime=SimpleNamespace(
                        service_variant="refactored",
                        agent_model="openai/gpt-4.1",
                    )
                ),
            )
    finally:
        clear_session_id()

    assert websocket.sent_texts == [json.dumps({"type": method_name})]
