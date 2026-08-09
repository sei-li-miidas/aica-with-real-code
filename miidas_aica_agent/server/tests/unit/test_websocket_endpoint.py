from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocketDisconnect

import endpoints


# WebSocket接続がキャンセルされた際に、原因別のログ出力・呼び出しが適切かを検証するテスト
class DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.headers = {}
        self.sent = []
        self.closed = False
        self.close_code = None

    async def accept(self):
        self.accepted = True

    async def close(self, code=None):
        self.closed = True
        self.close_code = code

    async def send_text(self, text):
        self.sent.append(text)


def _raise(exc: Exception):
    raise exc


async def _run_chat_with_stub(
    monkeypatch,
    handle_chat_session,
    is_local_value=True,
    headers=None,
    maintenance_mode=False,
):
    monkeypatch.setattr(endpoints, "is_local", lambda: is_local_value)
    monkeypatch.setattr(
        endpoints.maintenance_manager, "IS_MAINTENANCE_MODE", maintenance_mode
    )
    handle_mock = AsyncMock(side_effect=handle_chat_session)
    monkeypatch.setattr(endpoints, "handle_chat_session", handle_mock)
    debug_mock = MagicMock()
    exception_mock = MagicMock()
    monkeypatch.setattr(endpoints.logger, "debug", debug_mock)
    monkeypatch.setattr(endpoints.logger, "exception", exception_mock)

    ws = DummyWebSocket()
    if headers is not None:
        ws.headers = headers
    chat_svc = MagicMock()
    await endpoints.chat(
        ws,
        session_id="test-session",
        chat_svc=chat_svc,
        rate_limit_svc=MagicMock(),
        agent_runtime_config=MagicMock(),
    )
    return ws, handle_mock, chat_svc, debug_mock, exception_mock


@pytest.mark.asyncio
async def test_chat_logs_disconnect_on_websocket_disconnect(monkeypatch):
    """WebSocketDisconnect では切断ログが出ることを検証"""
    ws, handle_mock, chat_svc, debug_mock, exception_mock = await _run_chat_with_stub(
        monkeypatch,
        lambda *_args, **_kwargs: _raise(WebSocketDisconnect(code=1001)),
    )

    debug_messages = [call.args[0] for call in debug_mock.call_args_list]
    assert any("Websocket切断" in msg for msg in debug_messages)
    handle_mock.assert_awaited_once()
    chat_svc.assert_not_called()
    exception_mock.assert_not_called()
    assert ws.accepted is True


@pytest.mark.asyncio
async def test_chat_logs_generic_exception(monkeypatch):
    """一般例外では例外ログが出ることを検証"""
    ws, handle_mock, chat_svc, debug_mock, exception_mock = await _run_chat_with_stub(
        monkeypatch,
        lambda *_args, **_kwargs: _raise(RuntimeError("boom")),
    )

    exception_messages = [call.args[0] for call in exception_mock.call_args_list]
    assert any("予期しないエラー" in msg for msg in exception_messages)
    exception_mock.assert_called_once()
    handle_mock.assert_awaited_once()
    chat_svc.assert_not_called()
    assert ws.accepted is True


@pytest.mark.asyncio
async def test_chat_rejects_when_origin_host_mismatch(monkeypatch):
    """ローカル以外でorigin/host不一致なら1008で切断することを検証"""
    headers = {"origin": "https://example.com", "host": "api.example.com"}
    ws, handle_mock, chat_svc, debug_mock, exception_mock = await _run_chat_with_stub(
        monkeypatch,
        lambda *_args, **_kwargs: None,
        is_local_value=False,
        headers=headers,
    )

    assert ws.accepted is False
    assert ws.closed is True
    assert ws.close_code == 1008
    handle_mock.assert_not_awaited()
    chat_svc.assert_not_called()
    debug_mock.assert_not_called()
    exception_mock.assert_not_called()


@pytest.mark.asyncio
async def test_chat_rejects_when_origin_or_host_missing(monkeypatch):
    """ローカル以外でorigin/hostがないなら1008で切断することを検証"""
    for headers in (
        {"host": "api.example.com"},  # origin missing
        {"origin": "https://example.com"},  # host missing
        {},  # both missing
    ):
        (
            ws,
            handle_mock,
            chat_svc,
            debug_mock,
            exception_mock,
        ) = await _run_chat_with_stub(
            monkeypatch,
            lambda *_args, **_kwargs: None,
            is_local_value=False,
            headers=headers,
        )

        assert ws.accepted is False
        assert ws.closed is True
        assert ws.close_code == 1008
        handle_mock.assert_not_awaited()
        chat_svc.assert_not_called()
        debug_mock.assert_not_called()
        exception_mock.assert_not_called()


@pytest.mark.asyncio
async def test_chat_closes_during_maintenance(monkeypatch):
    """メンテナンスモード時はエラー返却して即座にクローズすることを検証"""
    ws, handle_mock, chat_svc, debug_mock, exception_mock = await _run_chat_with_stub(
        monkeypatch,
        lambda *_args, **_kwargs: None,
        maintenance_mode=True,
    )

    assert ws.accepted is True
    assert ws.closed is True
    assert ws.close_code is None  # default close code
    assert len(ws.sent) == 1  # maintenance error response sent
    debug_messages = [c.args[0] for c in debug_mock.call_args_list]
    assert any("Session ID" in msg for msg in debug_messages)
    handle_mock.assert_not_awaited()
    chat_svc.assert_not_called()
    exception_mock.assert_not_called()
