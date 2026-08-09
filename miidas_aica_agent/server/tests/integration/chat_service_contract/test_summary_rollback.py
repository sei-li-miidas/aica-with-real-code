"""
Summary rollback 完全な振る舞いアサーション (Phase 3, feature-3, task-5)。

テスト対象公開インターフェース:
- ChatService.summarize_position_detail_chat(input) -> ChatSessionStatus

summary path が chat runtime switching の外側にあり、legacy/real-refactored の
両 variant で同じ dedicated summary model config と同じ保存/会話 handoff を使うことを
runtime で検証する。

テストケース一覧:
- test_summary_uses_dedicated_summary_model_config_and_persists_summary
    対象: summary 専用 model 設定を使い、
    生成要約を永続化すること。
- test_summary_behavior_is_identical_for_legacy_and_delegating_variants
    対象: legacy と delegating/real-refactored 間で
    summary 振る舞いが一致すること。
- test_summary_returns_current_status_when_decrypt_fails
    対象: decrypt 失敗時に状態を変更せず current status を返すこと。
- test_summary_returns_current_status_without_position_id_or_histories
    対象: position_id/履歴不足の前提未充足時に
    早期 return すること。
- test_summary_returns_current_status_when_model_returns_empty_text
    対象: model が空要約を返した場合も
    状態遷移せず維持すること。
- test_real_refactored_chat_rebuilds_summary_context_and_starts_summary_job
    対象: real-refactored で summary context を再構築し、
    summary job 開始へ接続すること。
- test_real_refactored_chat_rebuilds_summary_context_when_summary_service_is_none
    対象: summary service が None の場合でも
    context 再構築経路が壊れないこと。
"""

from datetime import datetime as real_datetime
import json
from pathlib import Path
from types import SimpleNamespace
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from .chat_service_contract_helpers import (
    _FakeRunStream,
    _get_chat_histories,
    _get_conversation,
    _inner,
    _set_chat_histories,
    _set_conversation,
)
from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from services.conversation_summary_service import ConversationSummaryService
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.enum import LLMMessageRole, PageName
from utils.log_utils import session_id_var


FIXTURES_DIR = Path(__file__).with_name("fixtures")
_VARIANTS = [
    "legacy",
    "real-refactored",
]


def _load_json_fixture(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _make_chat_history(
    session_id: str,
    position_id: str,
    history: dict,
) -> ChatHistory:
    return ChatHistory(
        id=history["id"],
        session_id=session_id,
        position_id=position_id,
        active_agent=history["active_agent"],
        message_id=history["message_id"],
        role=history["role"],
        content=history["content"],
    )


def _make_summary_conversation_service(scenario: dict):
    summary_model = dict(scenario["summary_model"])
    summary_model["use_for"] = ["summary"]
    with patch(
        "services.conversation_summary_service.AsyncOpenAI",
        return_value=SimpleNamespace(),
    ):
        summary_svc = ConversationSummaryService(model_list=[summary_model])
    create_mock = AsyncMock(
        return_value=SimpleNamespace(output_text=scenario["summary_text"])
    )
    summary_svc._openai_client = SimpleNamespace(
        responses=SimpleNamespace(create=create_mock),
    )
    return summary_svc, create_mock


def _frozen_chat_service_datetime(timestamp: int):
    class _FrozenDateTime:
        @classmethod
        def now(cls):
            return real_datetime.fromtimestamp(timestamp)

    return _FrozenDateTime


async def _exercise_summary_behavior(chat_svc, scenario: dict, session_id: str) -> dict:
    svc = _inner(chat_svc)
    summary_svc, create_mock = _make_summary_conversation_service(scenario)
    svc._conversation_summary_svc = summary_svc
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING
    _set_conversation(svc, {"MAIN": []})
    _get_chat_histories(svc)[scenario["decrypted_position_id"]] = [
        _make_chat_history(
            session_id,
            scenario["decrypted_position_id"],
            history,
        )
        for history in scenario["position_chat_histories"]
    ]

    request = ChatRequestModel(
        request_type=ChatRequestType.SUMMARIZE_POSITION,
        current_page=PageName.POSITION_DETAIL,
        position_id=scenario["encrypted_position_id"],
        current_message_id="msg-summary-rollback-001",
    )

    with (
        patch(
            "services.chat_service.decrypt",
            return_value=scenario["decrypted_position_id"],
        ),
        patch(
            "services.chat_service_refactored.decrypt",
            return_value=scenario["decrypted_position_id"],
        ),
        patch(
            "services.chat_service.datetime",
            _frozen_chat_service_datetime(scenario["fixed_timestamp"]),
        ),
        patch(
            "services.chat_service_refactored.datetime",
            _frozen_chat_service_datetime(scenario["fixed_timestamp"]),
        ),
    ):
        session_status = await chat_svc.summarize_position_detail_chat(request)

    assert svc._chat_repository.add_chat_histories.call_count == 1
    saved_histories = svc._chat_repository.add_chat_histories.call_args.args[0]
    assert len(saved_histories) == 1
    assert len(_get_conversation(svc)["MAIN"]) == 1

    return {
        "session_status": session_status,
        "openai_call_kwargs": create_mock.await_args.kwargs,
        "saved_history": saved_histories[0],
        "conversation_entry": _get_conversation(svc)["MAIN"][0],
        "summary_svc": summary_svc,
    }


pytestmark = pytest.mark.pre_extraction_parity


@pytest.fixture
def summary_session_id(request):
    session_id = f"test-session-summary-{request.node.name}-{uuid.uuid4()}"
    token = session_id_var.set(session_id)
    try:
        yield session_id
    finally:
        session_id_var.reset(token)


@pytest.mark.rollback_summary
@pytest.mark.asyncio
@pytest.mark.parametrize("chat_service_container", _VARIANTS, indirect=True)
async def test_summary_uses_dedicated_summary_model_config_and_persists_summary(
    chat_service_container,
    summary_session_id,
):
    fixture = _load_json_fixture("summary_rollback.json")
    scenario = fixture["summary_scenarios"]["independent_config"]

    result = await _exercise_summary_behavior(
        chat_service_container,
        scenario,
        summary_session_id,
    )
    call_kwargs = result["openai_call_kwargs"]
    saved_history = result["saved_history"]
    conversation_entry = result["conversation_entry"]

    assert result["session_status"] == ChatSessionStatus.CHATTING
    assert call_kwargs["model"] == scenario["summary_model"]["model"]
    assert (
        call_kwargs["temperature"]
        == scenario["summary_model"]["model_settings"]["temperature"]
    )
    assert (
        call_kwargs["max_output_tokens"]
        == scenario["summary_model"]["model_settings"]["max_output_tokens"]
    )

    expected_histories = scenario["position_chat_histories"]
    summary_inputs = call_kwargs["input"]
    assert len(summary_inputs) == len(expected_histories) + 1
    for actual_input, expected_history in zip(summary_inputs[:-1], expected_histories):
        assert actual_input["type"] == "message"
        assert actual_input["role"] == expected_history["role"]
        assert actual_input["content"] == [
            {
                "type": (
                    "output_text"
                    if expected_history["role"] == LLMMessageRole.ASSISTANT.value
                    else "input_text"
                ),
                "text": expected_history["content"],
            }
        ]
    assert summary_inputs[-1] == {
        "type": "message",
        "role": LLMMessageRole.DEVELOPER.value,
        "content": [
            {
                "type": "input_text",
                "text": result["summary_svc"]._position_detail_inquiry_summary_prompt,
            }
        ],
    }

    assert saved_history.session_id == summary_session_id
    assert saved_history.position_id is None
    assert (
        saved_history.active_agent == scenario["expected_saved_history"]["active_agent"]
    )
    assert saved_history.role == scenario["expected_saved_history"]["role"]
    assert saved_history.content == scenario["summary_text"]
    assert saved_history.message_id == scenario["expected_saved_history"]["message_id"]

    assert conversation_entry == scenario["expected_main_conversation_entry"]


@pytest.mark.rollback_summary
@pytest.mark.asyncio
@pytest.mark.parametrize("chat_service_container", _VARIANTS, indirect=True)
async def test_summary_behavior_is_identical_for_legacy_and_delegating_variants(
    chat_service_container,
    summary_session_id,
):
    fixture = _load_json_fixture("summary_rollback.json")
    scenario = fixture["summary_scenarios"]["independent_config"]
    expected_snapshot = fixture["summary_scenarios"]["unaffected_by_variant"][
        "expected_snapshot"
    ]

    result = await _exercise_summary_behavior(
        chat_service_container,
        scenario,
        summary_session_id,
    )
    call_kwargs = result["openai_call_kwargs"]
    saved_history = result["saved_history"]
    conversation_entry = result["conversation_entry"]

    actual_snapshot = {
        "session_status": result["session_status"].name,
        "summary_model": call_kwargs["model"],
        "summary_model_settings": {
            "temperature": call_kwargs["temperature"],
            "max_output_tokens": call_kwargs["max_output_tokens"],
        },
        "saved_history_role": saved_history.role,
        "saved_history_content": saved_history.content,
        "saved_history_message_id": saved_history.message_id,
        "main_conversation_role": conversation_entry["role"],
        "main_conversation_text": conversation_entry["content"][0]["text"],
    }

    assert actual_snapshot == expected_snapshot


@pytest.mark.rollback_summary
@pytest.mark.asyncio
@pytest.mark.parametrize("chat_service_container", _VARIANTS, indirect=True)
async def test_summary_returns_current_status_when_decrypt_fails(
    chat_service_container,
    summary_session_id,
):
    svc = _inner(chat_service_container)
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING

    request = ChatRequestModel(
        request_type=ChatRequestType.SUMMARIZE_POSITION,
        current_page=PageName.POSITION_DETAIL,
        position_id="broken-position-id",
        current_message_id="msg-summary-decrypt-failure",
    )

    with (
        patch("services.chat_service.decrypt", side_effect=ValueError("bad token")),
        patch(
            "services.chat_service_refactored.decrypt",
            side_effect=ValueError("bad token"),
        ),
    ):
        session_status = await chat_service_container.summarize_position_detail_chat(
            request
        )

    assert session_status == ChatSessionStatus.CHATTING
    svc._chat_repository.add_chat_histories.assert_not_called()


@pytest.mark.rollback_summary
@pytest.mark.asyncio
@pytest.mark.parametrize("chat_service_container", _VARIANTS, indirect=True)
async def test_summary_returns_current_status_without_position_id_or_histories(
    chat_service_container,
    summary_session_id,
):
    svc = _inner(chat_service_container)
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING

    no_position_request = ChatRequestModel(
        request_type=ChatRequestType.SUMMARIZE_POSITION,
        current_page=PageName.POSITION_DETAIL,
        current_message_id="msg-summary-no-position",
    )
    assert (
        await chat_service_container.summarize_position_detail_chat(no_position_request)
        == ChatSessionStatus.CHATTING
    )

    with (
        patch("services.chat_service.decrypt", return_value="missing-position"),
        patch(
            "services.chat_service_refactored.decrypt",
            return_value="missing-position",
        ),
    ):
        missing_history_request = ChatRequestModel(
            request_type=ChatRequestType.SUMMARIZE_POSITION,
            current_page=PageName.POSITION_DETAIL,
            position_id="encrypted-position-id",
            current_message_id="msg-summary-missing-history",
        )
        assert (
            await chat_service_container.summarize_position_detail_chat(
                missing_history_request
            )
            == ChatSessionStatus.CHATTING
        )


@pytest.mark.rollback_summary
@pytest.mark.asyncio
@pytest.mark.parametrize("chat_service_container", _VARIANTS, indirect=True)
async def test_summary_returns_current_status_when_model_returns_empty_text(
    chat_service_container,
    summary_session_id,
):
    fixture = _load_json_fixture("summary_rollback.json")
    scenario = fixture["summary_scenarios"]["independent_config"]
    svc = _inner(chat_service_container)
    svc._chat_repository.session_status.return_value = ChatSessionStatus.CHATTING
    _set_conversation(svc, {"MAIN": []})
    _get_chat_histories(svc)[scenario["decrypted_position_id"]] = [
        _make_chat_history(
            summary_session_id,
            scenario["decrypted_position_id"],
            history,
        )
        for history in scenario["position_chat_histories"]
    ]
    svc._conversation_summary_svc = MagicMock()
    svc._conversation_summary_svc.summarize_position_detail_chat = AsyncMock(
        return_value=""
    )

    request = ChatRequestModel(
        request_type=ChatRequestType.SUMMARIZE_POSITION,
        current_page=PageName.POSITION_DETAIL,
        position_id=scenario["encrypted_position_id"],
        current_message_id="msg-summary-empty-text",
    )

    with (
        patch(
            "services.chat_service.decrypt",
            return_value=scenario["decrypted_position_id"],
        ),
        patch(
            "services.chat_service_refactored.decrypt",
            return_value=scenario["decrypted_position_id"],
        ),
    ):
        session_status = await chat_service_container.summarize_position_detail_chat(
            request
        )

    assert session_status == ChatSessionStatus.CHATTING
    svc._chat_repository.add_chat_histories.assert_not_called()
    assert _get_conversation(svc)["MAIN"] == []


@pytest.mark.rollback_summary
@pytest.mark.asyncio
async def test_real_refactored_chat_rebuilds_summary_context_and_starts_summary_job(
    real_refactored_chat_service_container,
    summary_session_id,
):
    svc = _inner(real_refactored_chat_service_container)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    await real_refactored_chat_service_container.init_session("gpt-4o")

    summary_service = MagicMock()
    summary_service.get_latest_completed.return_value = None
    svc._summary_service = summary_service
    svc._build_summary_context = MagicMock()
    svc._llm_runner.run_streamed.return_value = _FakeRunStream([])

    request = ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        message="summary parity",
        current_message_id="msg-summary-turn-rebuild",
    )

    responses = [
        response
        async for response in real_refactored_chat_service_container.chat(
            request,
            "127.0.0.1",
        )
    ]

    assert len(responses) == 1
    assert responses[0].response_type.name == "END"
    svc._build_summary_context.assert_called_once_with(summary_session_id)
    summary_service.check_should_start_summary.assert_called_once_with(
        summary_session_id
    )


@pytest.mark.rollback_summary
@pytest.mark.asyncio
async def test_real_refactored_chat_rebuilds_summary_context_when_summary_service_is_none(
    real_refactored_chat_service_container,
    summary_session_id,
):
    svc = _inner(real_refactored_chat_service_container)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    await real_refactored_chat_service_container.init_session("gpt-4o")

    svc._summary_service = None
    svc._build_summary_context = MagicMock()
    svc._llm_runner.run_streamed.return_value = _FakeRunStream([])

    request = ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        message="summary none parity",
        current_message_id="msg-summary-turn-no-summary-service",
    )

    responses = [
        response
        async for response in real_refactored_chat_service_container.chat(
            request,
            "127.0.0.1",
        )
    ]

    assert len(responses) == 1
    assert responses[0].response_type.name == "END"
    svc._build_summary_context.assert_called_once_with(summary_session_id)


@pytest.mark.rollback_summary
@pytest.mark.asyncio
@pytest.mark.parametrize("chat_service_container", ["legacy"], indirect=True)
async def test_legacy_build_summary_context_uses_incremental_cache_path(
    chat_service_container,
    summary_session_id,
):
    svc = _inner(chat_service_container)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}

    # init_session() で tool trace を含むベース状態を作る
    await chat_service_container.init_session("gpt-4o")
    svc._chat_key = "MAIN"

    latest_completed = SimpleNamespace(summary_id="1", summary_until_history_id="10")
    svc._summary_service = MagicMock()
    svc._summary_service.get_latest_completed.return_value = latest_completed
    new_histories = [
        ChatHistory(
            id=11,
            session_id=summary_session_id,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="msg-new-1",
            role=LLMMessageRole.USER,
            content="新しい履歴",
        )
    ]
    svc._summary_service.get_histories_after.return_value = new_histories

    existing_history = ChatHistory(
        id=10,
        session_id=summary_session_id,
        position_id=None,
        active_agent="CareerAdvisor",
        message_id="msg-old-1",
        role=LLMMessageRole.USER,
        content="既存履歴",
    )
    svc._summary_context_cache = {
        "session_id": summary_session_id,
        "summary_id": 1,
        "boundary_id": 10,
        "last_history_id": 10,
        "chat_histories": [existing_history],
        "conversation": [{"type": "message", "role": "user", "content": "old"}],
    }
    svc._convert_to_llm_messages = MagicMock(
        return_value=(
            {"MAIN": new_histories},
            {"MAIN": [{"type": "message", "role": "user", "content": "new"}]},
        )
    )

    await svc.build_summary_context(summary_session_id)

    assert len(_get_chat_histories(svc)["MAIN"]) == 2
    assert _get_conversation(svc)["MAIN"][-1]["content"] == "new"
    assert svc._summary_context_cache["last_history_id"] == 11


@pytest.mark.rollback_summary
@pytest.mark.asyncio
@pytest.mark.parametrize("chat_service_container", ["legacy"], indirect=True)
async def test_legacy_build_summary_context_rebuilds_with_summary_message_and_strips_tool_trace(
    chat_service_container,
    summary_session_id,
):
    svc = _inner(chat_service_container)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}

    await chat_service_container.init_session("gpt-4o")
    svc._chat_key = "MAIN"

    latest_completed = SimpleNamespace(
        summary_id="2",
        summary_until_history_id="20",
        summary_text="要約本文",
    )
    svc._summary_service = MagicMock()
    svc._summary_service.get_latest_completed.return_value = latest_completed
    svc._summary_service.get_histories_after.return_value = [
        ChatHistory(
            id=21,
            session_id=summary_session_id,
            position_id=None,
            active_agent="CareerAdvisor",
            message_id="msg-21",
            role=LLMMessageRole.USER,
            content="履歴21",
        )
    ]
    tool_trace_content = svc._toolcall_trace_message["content"]
    svc._convert_to_llm_messages = MagicMock(
        return_value=(
            {"MAIN": []},
            {
                "MAIN": [
                    {
                        "type": "message",
                        "role": LLMMessageRole.DEVELOPER,
                        "content": tool_trace_content,
                    },
                    {"type": "message", "role": "user", "content": "新規会話"},
                ]
            },
        )
    )

    await svc.build_summary_context(summary_session_id)

    rebuilt = _get_conversation(svc)["MAIN"]
    assert rebuilt[0]["content"] == tool_trace_content
    assert any(
        isinstance(item, dict)
        and item.get("role") == LLMMessageRole.DEVELOPER
        and "###過去会話の要約" in item.get("content", "")
        for item in rebuilt
    )
    assert not any(
        isinstance(item, dict)
        and item.get("role") == LLMMessageRole.DEVELOPER
        and item.get("content") == tool_trace_content
        for item in rebuilt[1:]
    )
