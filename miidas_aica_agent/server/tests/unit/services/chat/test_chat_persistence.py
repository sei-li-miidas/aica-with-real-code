"""Unit tests for ChatPersistence — 100% branch coverage required.

ChatPersistence は DB 書き込み副作用（チャット履歴保存・
ツール出力更新）を担うコンポーネント。

テスト設計方針
--------------
- ChatRepository はモック（Mock(spec=ChatRepository)）を使用する。
- ConversationState は実インスタンスを使用する（外部 I/O なし・副作用なし）。
- RunItem の各サブタイプ（MessageOutputItem, ToolCallItem, HandoffCallItem,
  HandoffOutputItem, ToolCallOutputItem, ReasoningItem）を網羅する。
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest


pytestmark = pytest.mark.pre_extraction_parity
from agents import (
    HandoffCallItem,
    HandoffOutputItem,
    MessageOutputItem,
    ReasoningItem,
    ToolCallItem,
    ToolCallOutputItem,
)
from domain.entities.chat_history import ChatHistory
from repositories.chat_repo import ChatRepository
from services.chat.chat_persistence import ChatPersistence
from services.chat.conversation_state import ConversationState
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.const import MAIN_CHAT_KEY
from utils.enum import LLMMessageRole, PageName
from utils.log_utils import clear_session_id, set_session_id


@pytest.fixture(autouse=True)
def session_scope():
    set_session_id("test-session-persistence")
    yield
    clear_session_id()


@pytest.fixture
def chat_repository():
    return Mock(spec=ChatRepository)


@pytest.fixture
def conv_state():
    state = ConversationState()
    return state


@pytest.fixture
def persistence(chat_repository, conv_state):
    p = ChatPersistence(
        chat_repository=chat_repository,
        conv_state=conv_state,
    )
    p.set_toolcall_trace_content("SessionID: test\nRequestID: uuid4()")
    return p


def _make_request(
    *,
    request_type: ChatRequestType = ChatRequestType.CHAT,
    message: str = "テストメッセージ",
    message_id: str = "msg-001",
    is_voice: bool = False,
) -> ChatRequestModel:
    return ChatRequestModel(
        request_type=request_type,
        current_page=PageName.CHAT,
        message=message,
        current_message_id=message_id,
        is_voice=is_voice,
    )


def _make_agent(name: str = "CareerAdvisor") -> MagicMock:
    """weakref-able agent mock for RunItem constructors."""
    agent = MagicMock()
    agent.name = name
    return agent


def _make_message_output_item(
    agent_name: str = "CareerAdvisor",
    item_id: str = "resp-001",
    text: str = "テスト応答",
) -> MessageOutputItem:
    agent = _make_agent(agent_name)
    raw_item = SimpleNamespace(
        id=item_id,
        content=[SimpleNamespace(type="output_text", text=text)],
    )
    return MessageOutputItem(agent=agent, raw_item=raw_item)


def _make_tool_call_item(
    agent_name: str = "CareerAdvisor",
    item_id: str = "tc-001",
    call_id: str = "call-001",
    name: str = "test_tool",
    arguments: object = '{"key": "value"}',
) -> ToolCallItem:
    agent = _make_agent(agent_name)
    raw_item = SimpleNamespace(
        id=item_id,
        call_id=call_id,
        name=name,
        arguments=arguments,
    )
    return ToolCallItem(agent=agent, raw_item=raw_item)


def _make_handoff_call_item(
    agent_name: str = "CareerAdvisor",
    item_id: str = "hc-001",
    call_id: str = "hcall-001",
    name: str = "transfer_to_agent",
    arguments: str = "{}",
) -> HandoffCallItem:
    agent = _make_agent(agent_name)
    raw_item = SimpleNamespace(
        id=item_id,
        call_id=call_id,
        name=name,
        arguments=arguments,
    )
    return HandoffCallItem(agent=agent, raw_item=raw_item)


def _make_tool_call_output_item(
    agent_name: str = "CareerAdvisor",
    call_id: str = "call-001",
    output: str = '{"result": "ok"}',
) -> ToolCallOutputItem:
    agent = _make_agent(agent_name)
    raw_item = {
        "call_id": call_id,
        "output": output,
        "type": "function_call_output",
    }
    return ToolCallOutputItem(agent=agent, raw_item=raw_item, output=output)


def _make_handoff_output_item(
    agent_name: str = "CareerAdvisor",
    call_id: str = "hcall-001",
    output: str = "handoff result",
) -> HandoffOutputItem:
    agent = _make_agent(agent_name)
    source_agent = _make_agent("SourceAgent")
    target_agent = _make_agent("TargetAgent")
    raw_item = {
        "call_id": call_id,
        "output": output,
        "type": "function_call_output",
    }
    return HandoffOutputItem(
        agent=agent,
        raw_item=raw_item,
        source_agent=source_agent,
        target_agent=target_agent,
    )


def _make_reasoning_item(
    agent_name: str = "CareerAdvisor",
    item_id: str = "reasoning-001",
    summary: list | None = None,
) -> ReasoningItem:
    agent = _make_agent(agent_name)
    raw_item = SimpleNamespace(
        id=item_id,
        summary=summary or [{"text": "思考中..."}],
    )
    return ReasoningItem(agent=agent, raw_item=raw_item)


# ---------------------------------------------------------------------------
# set_toolcall_trace_content / save_toolcall_trace_message
# ---------------------------------------------------------------------------


def test_set_toolcall_trace_content(persistence):
    persistence.set_toolcall_trace_content("trace content")
    assert persistence._toolcall_trace_content == "trace content"


def test_save_toolcall_trace_message_saves_developer_history(
    persistence, chat_repository, conv_state
):
    """_toolcall_trace_content が設定済みの場合、DEVELOPER ロールの ChatHistory を保存する。"""
    conv_state.active_agent_name = "CareerAdvisor"
    persistence.set_toolcall_trace_content("trace content")

    persistence.save_toolcall_trace_message()

    chat_repository.add_chat_histories.assert_called_once()
    saved: list[ChatHistory] = chat_repository.add_chat_histories.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].role == LLMMessageRole.DEVELOPER
    assert saved[0].content == "trace content"
    assert saved[0].session_id == "test-session-persistence"
    assert saved[0].active_agent == "CareerAdvisor"
    assert saved[0].message_id.startswith("developer_")


def test_save_toolcall_trace_message_skips_when_empty(persistence, chat_repository):
    """_toolcall_trace_content が空の場合は何もしない。"""
    persistence.set_toolcall_trace_content("")

    persistence.save_toolcall_trace_message()

    chat_repository.add_chat_histories.assert_not_called()


def test_create_session_delegates_to_repository(persistence, chat_repository):
    """create_session が chat_repository.create_chat_session に委譲する。"""
    from domain.entities.chat_session import ChatSessionStatus

    persistence.create_session(ChatSessionStatus.CHATTING)

    chat_repository.create_chat_session.assert_called_once_with(
        session_status=ChatSessionStatus.CHATTING
    )


# ---------------------------------------------------------------------------
# _get_message_role
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("request_type", "expected_role"),
    [
        (ChatRequestType.CHAT, LLMMessageRole.USER),
        (ChatRequestType.START, LLMMessageRole.DEVELOPER),
        (ChatRequestType.RESTART_CHAT, LLMMessageRole.DEVELOPER),
        (ChatRequestType.JOB_TYPES_SELECTED, LLMMessageRole.DEVELOPER),
        (ChatRequestType.JOB_TYPES_CLEAR, LLMMessageRole.DEVELOPER),
        (ChatRequestType.WORKFLOW_ANSWERS_SUBMITTED, LLMMessageRole.DEVELOPER),
        (ChatRequestType.WORKFLOW_CANCELLED, LLMMessageRole.DEVELOPER),
    ],
)
def test_get_message_role(persistence, request_type, expected_role):
    role = persistence._get_message_role(request_type)
    assert role == expected_role


# ---------------------------------------------------------------------------
# save_chat_history — MessageOutputItem
# ---------------------------------------------------------------------------


def test_save_chat_history_message_output_saves_assistant(
    persistence, conv_state, chat_repository
):
    item = _make_message_output_item(text="了解しました。", item_id="resp-asst")

    persistence.save_chat_history(item)

    chat_repository.add_chat_histories.assert_called_once()
    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert len(saved) == 1
    h = saved[0]
    assert h.role == LLMMessageRole.ASSISTANT
    assert h.content == "了解しました。"
    assert h.message_id == "resp-asst"


# ---------------------------------------------------------------------------
# save_chat_history — ToolCallItem (regular, not transfer_to_)
# ---------------------------------------------------------------------------


def test_save_chat_history_tool_call_saves_tool_history(
    persistence, conv_state, chat_repository
):
    item = _make_tool_call_item(
        name="save_preference", call_id="call-abc", arguments='{"k": "v"}'
    )

    persistence.save_chat_history(item)

    chat_repository.add_chat_histories.assert_called_once()
    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert len(saved) == 1
    h = saved[0]
    assert h.role == LLMMessageRole.TOOL
    assert h.tool_call_id == "call-abc"
    assert h.tool_name == "save_preference"
    assert h.tool_input == {"k": "v"}


# ---------------------------------------------------------------------------
# save_chat_history — ToolCallItem starting with "transfer_to_" is skipped
# ---------------------------------------------------------------------------


def test_save_chat_history_transfer_to_tool_call_is_skipped(
    persistence, conv_state, chat_repository
):
    item = _make_tool_call_item(name="transfer_to_other_agent")

    persistence.save_chat_history(item)

    chat_repository.add_chat_histories.assert_not_called()


# ---------------------------------------------------------------------------
# save_chat_history — HandoffCallItem saves HANDOFF history
# ---------------------------------------------------------------------------


def test_save_chat_history_handoff_call_saves_handoff_history(
    persistence, conv_state, chat_repository
):
    item = _make_handoff_call_item(call_id="hcall-xyz")

    persistence.save_chat_history(item)

    chat_repository.add_chat_histories.assert_called_once()
    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert len(saved) == 1
    h = saved[0]
    assert h.role == LLMMessageRole.HANDOFF
    assert h.tool_call_id == "hcall-xyz"


# ---------------------------------------------------------------------------
# save_chat_history — ToolCallOutputItem updates tool output
# ---------------------------------------------------------------------------


def test_save_chat_history_tool_call_output_calls_update_tool_output(
    persistence, conv_state, chat_repository
):
    item = _make_tool_call_output_item(
        call_id="call-output-001", output='{"r": "done"}'
    )

    persistence.save_chat_history(item)

    chat_repository.update_tool_output.assert_called_once_with(
        tool_call_id="call-output-001",
        tool_call_output='{"r": "done"}',
    )
    chat_repository.add_chat_histories.assert_not_called()


# ---------------------------------------------------------------------------
# save_chat_history — HandoffOutputItem updates tool output
# ---------------------------------------------------------------------------


def test_save_chat_history_handoff_output_calls_update_tool_output(
    persistence, conv_state, chat_repository
):
    item = _make_handoff_output_item(call_id="hout-001", output="handoff output")

    persistence.save_chat_history(item)

    chat_repository.update_tool_output.assert_called_once_with(
        tool_call_id="hout-001",
        tool_call_output="handoff output",
    )
    chat_repository.add_chat_histories.assert_not_called()


# ---------------------------------------------------------------------------
# save_chat_history — ReasoningItem saves REASONING history
# ---------------------------------------------------------------------------


def test_save_chat_history_reasoning_item_saves_reasoning_history(
    persistence, conv_state, chat_repository
):
    summary = [{"text": "thinking..."}]
    item = _make_reasoning_item(summary=summary, item_id="reasoning-xyz")

    persistence.save_chat_history(item)

    chat_repository.add_chat_histories.assert_called_once()
    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert len(saved) == 1
    h = saved[0]
    assert h.role == LLMMessageRole.REASONING
    assert h.content == json.dumps(summary)
    assert h.message_id == "reasoning-xyz"


# ---------------------------------------------------------------------------
# save_chat_history — unsupported item type logs an error
# ---------------------------------------------------------------------------


def test_save_chat_history_unsupported_item_logs_error(
    persistence, conv_state, chat_repository
):
    unknown_item = SimpleNamespace(type="unknown")

    with patch("services.chat.chat_persistence.logger") as mock_logger:
        persistence.save_chat_history(unknown_item)
        mock_logger.error.assert_called_once()

    chat_repository.add_chat_histories.assert_not_called()


# ---------------------------------------------------------------------------
# save_chat_history — position_id is included in ChatHistory
# ---------------------------------------------------------------------------


def test_save_chat_history_includes_position_id_from_conv_state(
    persistence, conv_state, chat_repository
):
    conv_state.position_id = "pos-123"
    item = _make_message_output_item()

    persistence.save_chat_history(item)

    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert saved[0].position_id == "pos-123"


# ---------------------------------------------------------------------------
# save_user_or_developer_message
# ---------------------------------------------------------------------------


def test_save_user_or_developer_message_saves_user(
    persistence, conv_state, chat_repository
):
    request = _make_request(
        request_type=ChatRequestType.CHAT,
        message="ユーザーメッセージ",
        message_id="msg-user-1",
    )

    persistence.save_user_or_developer_message(request)

    chat_repository.add_chat_histories.assert_called_once()
    saved = chat_repository.add_chat_histories.call_args.args[0]
    h = saved[0]
    assert h.role == LLMMessageRole.USER
    assert h.content == "ユーザーメッセージ"
    assert h.message_id == "msg-user-1"


def test_save_user_or_developer_message_saves_developer_for_start_type(
    persistence, conv_state, chat_repository
):
    request = _make_request(
        request_type=ChatRequestType.START,
        message="再開します",
        message_id="msg-dev-1",
    )

    persistence.save_user_or_developer_message(request)

    saved = chat_repository.add_chat_histories.call_args.args[0]
    h = saved[0]
    assert h.role == LLMMessageRole.DEVELOPER
    assert h.content == "再開します"


def test_save_user_or_developer_message_includes_is_voice(
    persistence, conv_state, chat_repository
):
    request = _make_request(is_voice=True)

    persistence.save_user_or_developer_message(request)

    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert saved[0].is_voice is True


# ---------------------------------------------------------------------------
# save_llm_error
# ---------------------------------------------------------------------------


def test_save_llm_error_saves_developer_history(
    persistence, conv_state, chat_repository
):
    persistence.save_llm_error("システムエラーが発生しました。")

    chat_repository.add_chat_histories.assert_called_once()
    saved = chat_repository.add_chat_histories.call_args.args[0]
    h = saved[0]
    assert h.role == LLMMessageRole.DEVELOPER
    assert h.content == "システムエラーが発生しました。"


# ---------------------------------------------------------------------------
# block_session
# ---------------------------------------------------------------------------


def test_block_session_delegates_to_chat_repository(persistence, chat_repository):
    persistence.block_session()
    chat_repository.block_session.assert_called_once()


# ---------------------------------------------------------------------------
# save_chat_histories — public wrapper
# ---------------------------------------------------------------------------


def test_save_chat_histories_saves_to_db_and_conv_state(
    persistence, conv_state, chat_repository
):
    conv_state.chat_key = MAIN_CHAT_KEY
    histories = [
        ChatHistory(
            session_id="test-session",
            active_agent="CareerAdvisor",
            message_id="pub-001",
            role=LLMMessageRole.ASSISTANT,
            content="テスト",
        )
    ]

    persistence.save_chat_histories(histories)

    chat_repository.add_chat_histories.assert_called_once_with(histories)
    assert histories[0] in conv_state.chat_histories[MAIN_CHAT_KEY]


def test_save_chat_histories_noop_for_empty_list(
    persistence, conv_state, chat_repository
):
    persistence.save_chat_histories([])
    chat_repository.add_chat_histories.assert_not_called()


# ---------------------------------------------------------------------------
# _save_chat_histories — updates conv_state.chat_histories
# ---------------------------------------------------------------------------


def test_internal_save_chat_histories_appends_to_chat_key(
    persistence, conv_state, chat_repository
):
    conv_state.chat_key = "position-42"
    history = ChatHistory(
        session_id="test-session",
        active_agent="CareerAdvisor",
        message_id="test-001",
        role=LLMMessageRole.USER,
        content="テスト",
    )

    persistence._save_chat_histories([history])

    assert "position-42" in conv_state.chat_histories
    assert history in conv_state.chat_histories["position-42"]


def test_internal_save_chat_histories_uses_setdefault_for_new_key(
    persistence, conv_state, chat_repository
):
    conv_state.chat_key = "new-key"
    assert "new-key" not in conv_state.chat_histories

    history = ChatHistory(
        session_id="s",
        active_agent="CareerAdvisor",
        message_id="m",
        role=LLMMessageRole.ASSISTANT,
        content="c",
    )

    persistence._save_chat_histories([history])

    assert "new-key" in conv_state.chat_histories
    assert history in conv_state.chat_histories["new-key"]


# ---------------------------------------------------------------------------
# Non-string tool output serialization
# ---------------------------------------------------------------------------


def test_save_chat_history_tool_output_serializes_dict_output(
    persistence, conv_state, chat_repository
):
    """dict 型のツール出力は JSON 文字列にシリアライズされて update_tool_output に渡される。"""
    agent = _make_agent()
    raw_item = {
        "call_id": "call-dict-001",
        "output": {"key": "value"},
        "type": "function_call_output",
    }
    item = ToolCallOutputItem(agent=agent, raw_item=raw_item, output={"key": "value"})

    persistence.save_chat_history(item)

    call_kwargs = chat_repository.update_tool_output.call_args.kwargs
    assert call_kwargs["tool_call_id"] == "call-dict-001"
    # dict がシリアライズされていること
    assert json.loads(call_kwargs["tool_call_output"]) == {"key": "value"}


# ---------------------------------------------------------------------------
# _serialize_tool_output_for_storage — branch coverage for _default function
# ---------------------------------------------------------------------------


def test_serialize_tool_output_str_passthrough(
    persistence, conv_state, chat_repository
):
    """str 型のツール出力はそのまま渡される（JSON シリアライズなし）。"""
    agent = _make_agent()
    raw_item = {
        "call_id": "call-str-001",
        "output": '{"result": "direct string"}',
        "type": "function_call_output",
    }
    item = ToolCallOutputItem(
        agent=agent, raw_item=raw_item, output='{"result": "direct string"}'
    )

    persistence.save_chat_history(item)

    call_kwargs = chat_repository.update_tool_output.call_args.kwargs
    assert call_kwargs["tool_call_output"] == '{"result": "direct string"}'


def test_serialize_tool_output_dataclass_uses_asdict(
    persistence, conv_state, chat_repository
):
    """dataclass 型のツール出力は asdict でシリアライズされる。"""
    from dataclasses import dataclass

    @dataclass
    class SomeResult:
        value: str

    agent = _make_agent()
    output_obj = SomeResult(value="test-data")
    raw_item = {
        "call_id": "call-dc-001",
        "output": output_obj,
        "type": "function_call_output",
    }
    item = ToolCallOutputItem(agent=agent, raw_item=raw_item, output=output_obj)

    persistence.save_chat_history(item)

    call_kwargs = chat_repository.update_tool_output.call_args.kwargs
    assert json.loads(call_kwargs["tool_call_output"]) == {"value": "test-data"}


def test_serialize_tool_output_model_dump_object(
    persistence, conv_state, chat_repository
):
    """model_dump() メソッドを持つオブジェクトはその結果でシリアライズされる。"""
    agent = _make_agent()

    class PydanticLike:
        def model_dump(self):
            return {"pydantic": True}

    output_obj = PydanticLike()
    raw_item = {
        "call_id": "call-md-001",
        "output": output_obj,
        "type": "function_call_output",
    }
    item = ToolCallOutputItem(agent=agent, raw_item=raw_item, output=output_obj)

    persistence.save_chat_history(item)

    call_kwargs = chat_repository.update_tool_output.call_args.kwargs
    assert json.loads(call_kwargs["tool_call_output"]) == {"pydantic": True}


def test_serialize_tool_output_dict_method_object(
    persistence, conv_state, chat_repository
):
    """dict() メソッドを持つオブジェクト（model_dump なし）はその結果でシリアライズされる。"""
    agent = _make_agent()

    class OldStyleModel:
        def dict(self):
            return {"old": "style"}

    output_obj = OldStyleModel()
    raw_item = {
        "call_id": "call-dct-001",
        "output": output_obj,
        "type": "function_call_output",
    }
    item = ToolCallOutputItem(agent=agent, raw_item=raw_item, output=output_obj)

    persistence.save_chat_history(item)

    call_kwargs = chat_repository.update_tool_output.call_args.kwargs
    assert json.loads(call_kwargs["tool_call_output"]) == {"old": "style"}


def test_serialize_tool_output_dunder_dict_object(
    persistence, conv_state, chat_repository
):
    """__dict__ を持つオブジェクト（dict/model_dump なし）は __dict__ でシリアライズされる。"""
    agent = _make_agent()

    class PlainObject:
        def __init__(self):
            self.attr = "plain"

    output_obj = PlainObject()
    raw_item = {
        "call_id": "call-dd-001",
        "output": output_obj,
        "type": "function_call_output",
    }
    item = ToolCallOutputItem(agent=agent, raw_item=raw_item, output=output_obj)

    persistence.save_chat_history(item)

    call_kwargs = chat_repository.update_tool_output.call_args.kwargs
    assert json.loads(call_kwargs["tool_call_output"]) == {"attr": "plain"}


def test_serialize_tool_output_fallback_str(persistence, conv_state, chat_repository):
    """str() フォールバック: __dict__ のない JSON 非シリアライズオブジェクト。

    bytes は JSON シリアライズ不可かつ __dict__ を持たないため、str() フォールバックを通る。
    """
    agent = _make_agent()

    # bytes は JSON 非シリアライズかつ __dict__ なし → str() フォールバック
    output_obj = b"binary data"
    raw_item = {
        "call_id": "call-fb-001",
        "output": output_obj,
        "type": "function_call_output",
    }
    item = ToolCallOutputItem(agent=agent, raw_item=raw_item, output=output_obj)

    persistence.save_chat_history(item)

    call_kwargs = chat_repository.update_tool_output.call_args.kwargs
    # str(b"binary data") = "b'binary data'" が JSON 文字列として保存される
    assert "binary data" in call_kwargs["tool_call_output"]


# ---------------------------------------------------------------------------
# active_agent_name is included in saved ChatHistory
# ---------------------------------------------------------------------------


def test_save_user_or_developer_message_includes_active_agent_name(
    persistence, conv_state, chat_repository
):
    conv_state.active_agent_name = "CareerAdvisor"
    request = _make_request()

    persistence.save_user_or_developer_message(request)

    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert saved[0].active_agent == "CareerAdvisor"


# ---------------------------------------------------------------------------
# _parse_tool_arguments — branch coverage
# ---------------------------------------------------------------------------


def test_tool_call_with_dict_arguments_is_used_directly(
    persistence, conv_state, chat_repository
):
    """arguments が dict のときは json.loads せずそのまま tool_input に使う。"""
    item = _make_tool_call_item(
        name="my_tool", call_id="call-dict", arguments={"already": "parsed"}
    )

    persistence.save_chat_history(item)

    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert saved[0].tool_input == {"already": "parsed"}


def test_tool_call_with_invalid_json_string_falls_back_to_empty_dict(
    persistence, conv_state, chat_repository
):
    """arguments が不正 JSON 文字列のときは {} にフォールバックしてログを残す。"""
    item = _make_tool_call_item(
        name="my_tool", call_id="call-bad", arguments="{not valid json"
    )

    persistence.save_chat_history(item)

    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert saved[0].tool_input == {}


def test_tool_call_with_non_dict_json_falls_back_to_empty_dict(
    persistence, conv_state, chat_repository
):
    """arguments が JSON 配列など dict 以外にパースされる場合は {} にフォールバックする。"""
    item = _make_tool_call_item(
        name="my_tool", call_id="call-list", arguments="[1, 2, 3]"
    )

    persistence.save_chat_history(item)

    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert saved[0].tool_input == {}


def test_tool_call_with_none_arguments_falls_back_to_empty_dict(
    persistence, conv_state, chat_repository
):
    """arguments が None のときは {} にフォールバックしてログを残す。"""
    item = _make_tool_call_item(name="my_tool", call_id="call-none", arguments=None)

    persistence.save_chat_history(item)

    saved = chat_repository.add_chat_histories.call_args.args[0]
    assert saved[0].tool_input == {}


# ---------------------------------------------------------------------------
# _get_raw_item_field — attribute-shape raw_item (Pydantic BaseModel style)
# ---------------------------------------------------------------------------


def test_tool_call_output_with_object_raw_item_uses_item_output(
    persistence, conv_state, chat_repository
):
    """raw_item が dict でなく属性アクセス型（BaseModel 等）の場合も call_id を取得し、
    ToolCallOutputItem.output（SDK 正規フィールド）でシリアライズする。"""
    raw_item = SimpleNamespace(
        call_id="call-obj-001", output='{"result": "ok"}', type="function_call_output"
    )
    agent = _make_agent("CareerAdvisor")
    item = ToolCallOutputItem(agent=agent, raw_item=raw_item, output='{"result": "ok"}')

    persistence.save_chat_history(item)

    chat_repository.update_tool_output.assert_called_once_with(
        tool_call_id="call-obj-001",
        tool_call_output='{"result": "ok"}',
    )


def test_handoff_output_with_object_raw_item_uses_raw_item_output_attr(
    persistence, conv_state, chat_repository
):
    """HandoffOutputItem.raw_item が属性アクセス型の場合も call_id / output を取得する。"""
    raw_item = SimpleNamespace(
        call_id="hcall-obj-001", output="handoff done", type="function_call_output"
    )
    agent = _make_agent("CareerAdvisor")
    source = _make_agent("SourceAgent")
    target = _make_agent("TargetAgent")
    item = HandoffOutputItem(
        agent=agent, raw_item=raw_item, source_agent=source, target_agent=target
    )

    persistence.save_chat_history(item)

    chat_repository.update_tool_output.assert_called_once_with(
        tool_call_id="hcall-obj-001",
        tool_call_output="handoff done",
    )


def test_tool_call_output_with_missing_call_id_skips_update(
    persistence, conv_state, chat_repository
):
    """raw_item に call_id がない場合は update_tool_output を呼ばずに警告ログを残す。"""
    raw_item = SimpleNamespace(output="some output", type="function_call_output")
    agent = _make_agent("CareerAdvisor")
    item = ToolCallOutputItem(agent=agent, raw_item=raw_item, output="some output")

    with patch("services.chat.chat_persistence.logger") as mock_logger:
        persistence.save_chat_history(item)
        mock_logger.warning.assert_called()

    chat_repository.update_tool_output.assert_not_called()
