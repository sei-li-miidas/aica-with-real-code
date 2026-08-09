"""
ヒストリマッピング 完全な振る舞いアサーション (Phase 3, feature-3, task-1)。

テスト対象公開インターフェース:
- ChatService.init_session(model_name: str) -> tuple[ChatSessionStatus, bool]
- ChatService.chat(input: ChatRequestModel, client_ip: str) -> AsyncGenerator[ChatStreamResponseModel, None]
- ChatService.load_previous_chat_histories(limit: int, encrypted_position_id: str | None, before_id: str | None) -> tuple[list, bool]

DB の ChatHistory レコードが init_session() 後に _conversation 内で Agent SDK
入力アイテムへ正しく変換されること、および chat() 呼び出し時にそれらのアイテムが
_run_streamed() の ``input`` 引数としてそのまま渡されることを検証する。

テストケース一覧:
- test_history_mapping_user_assistant_to_sdk_input
    対象: init_session() が USER・ASSISTANT ロールの ChatHistory を読み込んだとき、
    chat() で _run_streamed に渡される input に
    {"type": "message", "role": "user", "content": <str>} および
    {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": <str>}]}
    が含まれること。

- test_history_mapping_tool_call_to_sdk_function_call
    対象: init_session() が TOOL ロールの ChatHistory を読み込んだとき、
    chat() で _run_streamed に渡される input に
    call_id・name・arguments を持つ {"type": "function_call"} アイテムと
    保存済み出力を持つ {"type": "function_call_output"} アイテムの
    ペアが含まれること。

- test_previous_history_payload_shape
    対象: load_previous_chat_histories() が DB の ChatHistory を
    フロント向けペイロード形式（Role, Type, MessageID, Message キーを持つ dict のリスト）に
    変換して返すこと。USER・ASSISTANT ロールそれぞれについて content と
    message_id が一致すること。

マーカー:
- rollback_di: DI ライフサイクルロールバックサブセットにヒストリマッピングを含む
- pre_extraction_parity: ヒストリマッピングは pre-extraction ゲートの一部
"""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType
from utils.enum import LLMMessageRole, PageName
from utils.log_utils import set_session_id

FIXTURES_DIR = Path(__file__).with_name("fixtures")

_SESSION_ID = "test-session-history-mapping"


def _inner(chat_svc):
    """delegating adapter をアンラップして legacy ChatService の内部属性にアクセスする。"""
    return getattr(chat_svc, "_legacy_chat_service", chat_svc)


def _load_json_fixture(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


class _EmptyRunResult:
    """イベントを何も yield しない最小限の RunResultStreaming フェイク（legacy 用）。"""

    last_response_id = None
    last_agent = None
    context_wrapper = SimpleNamespace(
        usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    )

    async def stream_events(self):
        return  # イベントなし
        yield  # pragma: no cover — async generator シグネチャを維持する

    def to_input_list(self):
        return []


class _EmptyRunStream:
    """イベントを何も yield しない最小限の LLMRunStream フェイク（real-refactored 用）。"""

    continuation_state = None
    agent_state = None
    replay_items: list = []
    usage = None

    async def stream_events(self):
        return  # イベントなし
        yield  # pragma: no cover — async generator シグネチャを維持する

    async def aclose(self) -> None:
        pass


def _make_chat_request(message: str = "続けてください") -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        message=message,
        current_message_id="msg-follow-up",
    )


pytestmark = pytest.mark.pre_extraction_parity


@pytest.mark.rollback_di
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_history_mapping_user_assistant_to_sdk_input(
    variant, chat_service_container_history_parity
):
    """DB ChatHistory（USER + ASSISTANT ロール）が正しい Agent SDK アイテムにマップされる。

    不変条件: init_session() が既存セッションを読み込んだ後、_run_streamed() に
    渡される ``input`` リストには以下が含まれる:
    - USER ロールの各ヒストリに対して ``{"type": "message", "role": "user", "content": <str>}``
    - ASSISTANT ロールの各ヒストリに対して ``{"type": "message", "role": "assistant",
      "content": [{"type": "output_text", "text": <str>}]}``
    """
    chat_svc = chat_service_container_history_parity
    svc = _inner(chat_svc)  # delegating adapter をアンラップする
    set_session_id(_SESSION_ID)

    # Arrange: USER と ASSISTANT ヒストリを持つ既存セッション。
    histories = [
        ChatHistory(
            id=1,
            session_id=_SESSION_ID,
            active_agent="CareerAdvisor",
            message_id="msg-user-1",
            role=LLMMessageRole.USER,
            content="こんにちは",
        ),
        ChatHistory(
            id=2,
            session_id=_SESSION_ID,
            active_agent="CareerAdvisor",
            message_id="msg-asst-1",
            role=LLMMessageRole.ASSISTANT,
            content="いらっしゃいませ！",
        ),
    ]
    mock_session = SimpleNamespace(
        session_id=_SESSION_ID,
        status=ChatSessionStatus.CHATTING,
        histories=histories,
    )
    svc._chat_repository.init_chat_session.return_value = (mock_session, True)
    svc._chat_repository.get_main_chat_histories.return_value = histories

    # chat() が名前でエージェントを解決できるよう設定する。
    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    agent_mock.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (agent_mock, True)}

    # Act: init_session() がヒストリを読み込み _conversation を構築する。
    status, is_new_session = await chat_svc.init_session("gpt-4o")

    assert status == ChatSessionStatus.CHATTING
    assert is_new_session is False

    # バリアントごとにランナーを差し替えて ``input`` をキャプチャし、実際の LLM 呼び出しを回避する。
    # real-refactored は LLMRunner プロトコルを使う。
    captured_input_snapshot: list | None = None

    if variant == "legacy":
        empty_result = _EmptyRunResult()

        def _capture_legacy(**kwargs):
            nonlocal captured_input_snapshot
            captured_input_snapshot = copy.deepcopy(kwargs.get("input", []))
            return empty_result

        mock_run = MagicMock(side_effect=_capture_legacy)
        svc._run_streamed = mock_run
    else:
        # real-refactored は LLMRunner プロトコルを使う。
        empty_stream = _EmptyRunStream()

        def _capture_refactored(**kwargs):
            nonlocal captured_input_snapshot
            captured_input_snapshot = copy.deepcopy(kwargs.get("input", []))
            return empty_stream

        mock_run = MagicMock(side_effect=_capture_refactored)
        chat_svc._llm_runner.run_streamed = mock_run

    async for _ in chat_svc.chat(_make_chat_request(), "127.0.0.1"):
        pass

    mock_run.assert_called_once()
    captured_input = captured_input_snapshot or []

    # USER ヒストリ → {"type": "message", "role": "user", "content": <str>}
    user_messages = [
        m
        for m in captured_input
        if isinstance(m, dict)
        and m.get("type") == "message"
        and m.get("role") == LLMMessageRole.USER
        and m.get("content") == "こんにちは"
    ]
    assert user_messages, (
        f"Expected USER history as SDK message in input; got: {captured_input}"
    )

    # ASSISTANT ヒストリ → {"type": "message", "role": "assistant",
    #   "content": [{"type": "output_text", "text": <str>}]}
    assistant_messages = [
        m
        for m in captured_input
        if isinstance(m, dict)
        and m.get("type") == "message"
        and m.get("role") == LLMMessageRole.ASSISTANT
        and isinstance(m.get("content"), list)
        and m["content"][0].get("type") == "output_text"
        and m["content"][0].get("text") == "いらっしゃいませ！"
    ]
    assert assistant_messages, (
        f"Expected ASSISTANT history as SDK message in input; got: {captured_input}"
    )

    # フィクスチャスキーマドキュメントとの照合。
    fixture = _load_json_fixture("history_mapping.json")
    mapping = fixture["history_scenarios"]["db_to_sdk_mapping"]
    assert "_expected_keys" in mapping
    assert "_description" in mapping


@pytest.mark.rollback_di
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_history_mapping_tool_call_to_sdk_function_call(
    variant, chat_service_container_history_parity
):
    """DB ChatHistory（TOOL ロール）が function_call + function_call_output にマップされる。

    不変条件: TOOL ロールのヒストリから SDK 入力アイテムが正確に 2 つ生成される:
    call_id・name・arguments を持つ ``function_call`` アイテムと、
    保存済みツール出力を持つ ``function_call_output`` アイテム。
    """
    chat_svc = chat_service_container_history_parity
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    histories = [
        ChatHistory(
            id=1,
            session_id=_SESSION_ID,
            active_agent="CareerAdvisor",
            message_id="msg-tool-1",
            role=LLMMessageRole.TOOL,
            content='{"result": "some output"}',
            tool_call_id="call-tool-001",
            tool_name="save_user_preference",
            tool_input={"Keyword": "エンジニア"},
        ),
    ]
    mock_session = SimpleNamespace(
        session_id=_SESSION_ID,
        status=ChatSessionStatus.CHATTING,
        histories=histories,
    )
    svc._chat_repository.init_chat_session.return_value = (mock_session, True)
    svc._chat_repository.get_main_chat_histories.return_value = histories

    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    agent_mock.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (agent_mock, True)}

    await chat_svc.init_session("gpt-4o")

    # real-refactored は LLMRunner プロトコルを使う。
    captured_input_snapshot: list | None = None

    if variant == "legacy":
        empty_result = _EmptyRunResult()

        def _capture_legacy(**kwargs):
            nonlocal captured_input_snapshot
            captured_input_snapshot = copy.deepcopy(kwargs.get("input", []))
            return empty_result

        mock_run = MagicMock(side_effect=_capture_legacy)
        svc._run_streamed = mock_run
    else:
        empty_stream = _EmptyRunStream()

        def _capture_refactored(**kwargs):
            nonlocal captured_input_snapshot
            captured_input_snapshot = copy.deepcopy(kwargs.get("input", []))
            return empty_stream

        mock_run = MagicMock(side_effect=_capture_refactored)
        chat_svc._llm_runner.run_streamed = mock_run

    async for _ in chat_svc.chat(_make_chat_request("次の質問"), "127.0.0.1"):
        pass

    captured_input = captured_input_snapshot or []

    # TOOL ヒストリ → function_call アイテム
    function_call_items = [
        m
        for m in captured_input
        if isinstance(m, dict)
        and m.get("type") == "function_call"
        and m.get("call_id") == "call-tool-001"
        and m.get("name") == "save_user_preference"
    ]
    assert function_call_items, (
        f"Expected function_call item in SDK input; got: {captured_input}"
    )
    assert function_call_items[0]["arguments"] == json.dumps(
        {"Keyword": "エンジニア"}
    ), f"function_call arguments mismatch: {function_call_items[0]}"

    # TOOL ヒストリ → function_call_output アイテム
    function_call_output_items = [
        m
        for m in captured_input
        if isinstance(m, dict)
        and m.get("type") == "function_call_output"
        and m.get("call_id") == "call-tool-001"
    ]
    assert function_call_output_items, (
        f"Expected function_call_output item in SDK input; got: {captured_input}"
    )
    assert function_call_output_items[0]["output"] == '{"result": "some output"}', (
        f"function_call_output output mismatch: {function_call_output_items[0]}"
    )

    # フィクスチャスキーマドキュメントとの照合。
    fixture = _load_json_fixture("history_mapping.json")
    payload = fixture["history_scenarios"]["previous_history_payload"]
    assert payload["_expected_keys"] == [
        "db_previous_history",
        "sdk_previous_history",
        "compatibility_validation",
    ]


@pytest.mark.asyncio
@pytest.mark.rollback_di
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_previous_history_payload_shape(
    variant, chat_service_container_history_parity
):
    """load_previous_chat_histories() が DB ChatHistory をフロント向けペイロードに変換する。

    不変条件: USER・ASSISTANT の ChatHistory を渡したとき、
    load_previous_chat_histories() の戻り値リストの各要素は
    Role, Type, MessageID, Message キーを持ち、
    USER エントリの MessageID・Message が元 ChatHistory と一致する。
    """
    chat_svc = chat_service_container_history_parity
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    histories = [
        ChatHistory(
            session_id=_SESSION_ID,
            active_agent="CareerAdvisor",
            message_id="msg-prev-user-1",
            role=LLMMessageRole.USER,
            content="前回のメッセージです",
        ),
        ChatHistory(
            session_id=_SESSION_ID,
            active_agent="CareerAdvisor",
            message_id="msg-prev-asst-1",
            role=LLMMessageRole.ASSISTANT,
            content="前回の返答です",
        ),
    ]
    # svc._chat_repository と chat_svc._chat_repository は同一オブジェクト。
    # refactored variant では chat_repository が legacy と refactored の両方に注入されるため、
    # _inner() でアンラップした legacy 側をモックすれば refactored path にも反映される。
    svc._chat_repository.get_main_chat_histories.return_value = histories

    result, no_more = await chat_svc.load_previous_chat_histories(
        limit=5,
        encrypted_position_id=None,
        before_id=None,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    for entry in result:
        assert "Role" in entry, f"Missing 'Role' key in entry: {entry}"
        assert "Type" in entry, f"Missing 'Type' key in entry: {entry}"
        assert "MessageID" in entry, f"Missing 'MessageID' key in entry: {entry}"
        assert "Message" in entry, f"Missing 'Message' key in entry: {entry}"

    user_entries = [e for e in result if e["Role"] == LLMMessageRole.USER]
    assert any(
        e["MessageID"] == "msg-prev-user-1" and e["Message"] == "前回のメッセージです"
        for e in user_entries
    ), f"No matching USER entry found; result: {result}"

    assistant_entries = [e for e in result if e["Role"] == LLMMessageRole.ASSISTANT]
    assert any(
        e["MessageID"] == "msg-prev-asst-1"
        and e["Type"] == ChatResponseType.MESSAGE
        and e["Message"] == "前回の返答です"
        for e in assistant_entries
    ), f"No matching ASSISTANT entry found; result: {result}"
