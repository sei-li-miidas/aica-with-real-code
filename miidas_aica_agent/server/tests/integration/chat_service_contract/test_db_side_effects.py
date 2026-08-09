"""
DB 副作用 完全な振る舞いアサーション (Phase 3, feature-3, task-1)。

テスト対象公開インターフェース:
- ChatService.init_session(model_name: str) -> tuple[ChatSessionStatus, bool]
- ChatService.chat(input: ChatRequestModel, client_ip: str) -> AsyncGenerator[ChatStreamResponseModel, None]

chat() が正しい ChatRepository 書き込み呼び出しをトリガーすることを検証する:
- assistant MessageOutputItem イベントに対して add_chat_histories
- ToolCallOutputItem イベントに対して update_tool_output
- LLM 失敗繰り返し時に DEVELOPER ロールで add_chat_histories
- USER メッセージに対して add_chat_histories
- DEVELOPER ロールのメッセージに対して add_chat_histories

テストケース一覧:
- test_db_history_save_for_assistant_message
    対象: _run_streamed が MessageOutputItem を持つ run_item_stream_event を
    yield したとき、add_chat_histories が role=ASSISTANT かつ content・message_id が
    一致する ChatHistory とともに呼び出されること。

- test_db_tool_output_update
    対象: _run_streamed が ToolCallItem → ToolCallOutputItem の順に yield したとき、
    update_tool_output(tool_call_id, tool_call_output) が正しい引数で呼び出され、
    かつ role=TOOL の ChatHistory が add_chat_histories で書き込まれること。

- test_db_retry_error_save
    対象: _run_streamed がすべての試行で例外を送出したとき、
    add_chat_histories が role=DEVELOPER かつ content=DEFAULT_LLM_FAIL_RESPONSE の
    ChatHistory とともに呼び出されること。
    (legacy バリアントのみ; real-refactored は retry loop なし)

- test_db_user_message_save
    対象: chat() の先頭で add_chat_histories が role=USER かつ content・message_id が
    リクエストと一致する ChatHistory とともに呼び出されること。

- test_db_developer_message_save
    対象: request_type が DEVELOPER ロールにマップされる種別（例: START）のとき、
    chat() が add_chat_histories を role=DEVELOPER かつ content・message_id が
    リクエストと一致する ChatHistory とともに呼び出すこと。

マーカー:
- rollback_runner: Runner イベント → DB 副作用の不変条件
- pre_extraction_parity: DB 副作用は pre-extraction ゲートの一部
"""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents import MessageOutputItem, ToolCallItem, ToolCallOutputItem
from .chat_service_contract_helpers import (
    _FakeRunResult,
    _FakeRunStream,
    _inner,
    _make_run_item_event,
    _setup_existing_session,
)
from services.chat_service import DEFAULT_LLM_FAIL_RESPONSE
from services.chat_service_refactored import (
    DEFAULT_LLM_FAIL_RESPONSE as REFACTORED_DEFAULT_LLM_FAIL_RESPONSE,
)
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.enum import LLMMessageRole, PageName
from utils.log_utils import set_session_id

FIXTURES_DIR = Path(__file__).with_name("fixtures")

_SESSION_ID = "test-session-db-side-effects"


def _load_json_fixture(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _make_chat_request(message: str = "よろしくお願いします") -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        message=message,
        current_message_id="msg-db-test",
    )


def _setup_runner_mock(variant: str, chat_svc, svc, events: list) -> None:
    """バリアントに応じてランナーモックを設定する。

    legacy: svc._run_streamed に _FakeRunResult を設定。
    real-refactored: chat_svc._llm_runner.run_streamed に _FakeRunStream を設定。

    """
    if variant == "legacy":
        mock_run = MagicMock(return_value=_FakeRunResult(events))
        svc._run_streamed = mock_run
    else:
        mock_stream = MagicMock(return_value=_FakeRunStream(events))
        chat_svc._llm_runner.run_streamed = mock_stream


pytestmark = pytest.mark.pre_extraction_parity


@pytest.mark.rollback_runner
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_db_history_save_for_assistant_message(
    variant, chat_service_container_db_side_effects
):
    """MessageOutputItem イベントにより ASSISTANT ChatHistory の DB 書き込みが発生する。

    不変条件: _run_streamed が MessageOutputItem を持つ run_item_stream_event を yield すると、
    add_chat_histories が role=ASSISTANT かつ content がレスポンス出力のテキストと一致する
    ChatHistory とともに呼び出される。
    """
    chat_svc = chat_service_container_db_side_effects
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)

    msg_item = MessageOutputItem(
        agent=agent_mock,
        raw_item=SimpleNamespace(
            id="resp-msg-001",
            content=[SimpleNamespace(type="output_text", text="了解しました。")],
        ),
    )
    events = [_make_run_item_event(msg_item)]
    _setup_runner_mock(variant, chat_svc, svc, events)

    async for _ in chat_svc.chat(_make_chat_request(), "127.0.0.1"):
        pass

    all_saved = [
        h
        for call in svc._chat_repository.add_chat_histories.call_args_list
        for h in call.args[0]
    ]
    assistant_entries = [h for h in all_saved if h.role == LLMMessageRole.ASSISTANT]
    assert any(
        h.content == "了解しました。" and h.message_id == "resp-msg-001"
        for h in assistant_entries
    ), f"No matching ASSISTANT history found; all saved: {all_saved}"

    # フィクスチャスキーマとの照合。
    fixture = _load_json_fixture("db_side_effects.json")
    assert fixture["scenarios"]["history_save"]["_expected_keys"] == [
        "history_input",
        "expected_db_state",
        "message_types",
    ]


@pytest.mark.rollback_runner
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_db_tool_output_update(variant, chat_service_container_db_side_effects):
    """ToolCallOutputItem イベントにより update_tool_output が正しい引数で呼び出される。

    不変条件: ToolCallItem → TOOL ChatHistory が書き込まれる; ToolCallOutputItem →
    update_tool_output(tool_call_id, シリアライズ済み出力) が呼び出される。
    """
    chat_svc = chat_service_container_db_side_effects
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)

    tool_call_raw = SimpleNamespace(
        id="tc-item-001",
        call_id="call-pref-001",
        name="save_user_preference",
        arguments="{}",
    )
    tool_item = ToolCallItem(agent=agent_mock, raw_item=tool_call_raw)

    tool_output_str = '{"result": "saved"}'
    output_item = ToolCallOutputItem(
        agent=agent_mock,
        raw_item={
            "call_id": "call-pref-001",
            "output": tool_output_str,
            "type": "function_call_output",
        },
        output=tool_output_str,
    )
    events = [_make_run_item_event(tool_item), _make_run_item_event(output_item)]
    _setup_runner_mock(variant, chat_svc, svc, events)

    async for _ in chat_svc.chat(_make_chat_request(), "127.0.0.1"):
        pass

    # ToolCallOutputItem に対して update_tool_output が呼ばれる
    svc._chat_repository.update_tool_output.assert_called_once_with(
        tool_call_id="call-pref-001",
        tool_call_output=tool_output_str,
    )

    # ToolCallItem に対して TOOL ヒストリが書き込まれる
    all_saved = [
        h
        for call in svc._chat_repository.add_chat_histories.call_args_list
        for h in call.args[0]
    ]
    tool_entries = [h for h in all_saved if h.role == LLMMessageRole.TOOL]
    assert any(
        h.tool_call_id == "call-pref-001" and h.tool_name == "save_user_preference"
        for h in tool_entries
    ), f"No matching TOOL history found; all saved: {all_saved}"

    # フィクスチャスキーマとの照合。
    fixture = _load_json_fixture("db_side_effects.json")
    assert fixture["scenarios"]["tool_output_update"]["_expected_keys"] == [
        "tool_output",
        "expected_db_state",
        "update_validation",
    ]


@pytest.mark.rollback_runner
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_db_retry_error_save(variant, chat_service_container_db_side_effects):
    """すべての LLM リトライ失敗により DEVELOPER エラー ChatHistory が書き込まれる。

    不変条件: _run_streamed がすべての試行で例外を送出すると、_save_llm_error が
    DEFAULT_LLM_FAIL_RESPONSE とともに呼び出され、DEVELOPER ロールの ChatHistory 行が
    add_chat_histories 経由で永続化される。

    注意: 公開挙動（DEVELOPER エラー履歴保存）を検証し、内部実装差分には依存しない。
    """
    chat_svc = chat_service_container_db_side_effects
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)

    if variant == "legacy":
        svc._run_streamed = MagicMock(side_effect=RuntimeError("simulated LLM failure"))
        with patch("services.chat_service.asyncio.sleep", new=AsyncMock()):
            async for _ in chat_svc.chat(_make_chat_request(), "127.0.0.1"):
                pass
    else:
        chat_svc._llm_runner.run_streamed = MagicMock(
            side_effect=RuntimeError("simulated LLM failure")
        )
        with patch("services.chat_service_refactored.asyncio.sleep", new=AsyncMock()):
            async for _ in chat_svc.chat(_make_chat_request(), "127.0.0.1"):
                pass

    all_saved = [
        h
        for call in svc._chat_repository.add_chat_histories.call_args_list
        for h in call.args[0]
    ]
    developer_errors = [
        h
        for h in all_saved
        if h.role == LLMMessageRole.DEVELOPER and h.content == DEFAULT_LLM_FAIL_RESPONSE
    ]
    assert developer_errors, (
        f"Expected at least one DEVELOPER error history; all saved: {all_saved}"
    )

    # フィクスチャスキーマとの照合。
    fixture = _load_json_fixture("db_side_effects.json")
    assert fixture["scenarios"]["retry_error_save"]["_expected_keys"] == [
        "retry_error",
        "expected_db_state",
        "error_persistence",
    ]


@pytest.mark.rollback_runner
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_db_user_message_save(variant, chat_service_container_db_side_effects):
    """chat() の先頭で USER メッセージが add_chat_histories で書き込まれる。

    不変条件: chat() はリクエストの content と message_id を持つ role=USER の
    ChatHistory を add_chat_histories 経由で永続化する。
    """
    chat_svc = chat_service_container_db_side_effects
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)

    _setup_runner_mock(variant, chat_svc, svc, [])

    request = ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        message="テストメッセージです",
        current_message_id="msg-user-save-test",
    )

    async for _ in chat_svc.chat(request, "127.0.0.1"):
        pass

    all_saved = [
        h
        for call in svc._chat_repository.add_chat_histories.call_args_list
        for h in call.args[0]
    ]
    user_entries = [h for h in all_saved if h.role == LLMMessageRole.USER]
    assert any(
        h.content == "テストメッセージです" and h.message_id == "msg-user-save-test"
        for h in user_entries
    ), f"No matching USER history found; all saved: {all_saved}"


@pytest.mark.rollback_runner
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_db_developer_message_save(
    variant, chat_service_container_db_side_effects
):
    """chat() の先頭で DEVELOPER メッセージが add_chat_histories で書き込まれる。

    不変条件: _get_message_role が DEVELOPER を返す request_type（例: START）のとき、
    chat() は role=DEVELOPER かつ content・message_id がリクエストと一致する
    ChatHistory を add_chat_histories 経由で永続化する。
    """
    chat_svc = chat_service_container_db_side_effects
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)

    _setup_runner_mock(variant, chat_svc, svc, [])

    request = ChatRequestModel(
        request_type=ChatRequestType.START,
        current_page=PageName.CHAT,
        message="再開します",
        current_message_id="msg-developer-save-test",
    )

    async for _ in chat_svc.chat(request, "127.0.0.1"):
        pass

    all_saved = [
        h
        for call in svc._chat_repository.add_chat_histories.call_args_list
        for h in call.args[0]
    ]
    developer_entries = [h for h in all_saved if h.role == LLMMessageRole.DEVELOPER]
    assert any(
        h.content == "再開します" and h.message_id == "msg-developer-save-test"
        for h in developer_entries
    ), f"No matching DEVELOPER history found; all saved: {all_saved}"


def test_default_llm_fail_response_constant_parity():
    """legacy と refactored の DEFAULT_LLM_FAIL_RESPONSE が同一であること。"""
    assert DEFAULT_LLM_FAIL_RESPONSE == REFACTORED_DEFAULT_LLM_FAIL_RESPONSE
