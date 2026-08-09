"""
init_session residual branch テスト。

テストケース一覧:
- test_init_session_uses_current_filter_tool_name_and_selected_jobtypes
    対象: init_session 復元時に current filter から tool_name と
    selected jobtypes を正しく復元すること。
- test_init_session_falls_back_when_current_search_filter_lookup_fails
    対象: current filter 取得失敗時に例外伝播せず fallback すること。
- test_init_session_ignores_invalid_current_filter_shapes
    対象: current filter の不正 shape を無視し、init_session が継続すること。
- test_init_session_generates_new_session_id_when_repository_reports_exists
    対象: 既存 session_id 衝突時に新しい session_id を再生成すること。
- test_init_session_returns_error_when_resume_history_has_only_position_guide
    対象: resume history が POSITION_GUIDE のみの不正状態では
    init_session がエラー扱いになること。
- test_init_session_restores_position_and_tool_histories_into_chat_input
    対象: 位置情報系・tool 系履歴を Agent 入力形式へ復元できること。
- test_init_session_uses_generic_fake_result_when_position_output_is_invalid
    対象: position tool output が不正な場合に generic fake result へ
    フォールバックすること。
- test_init_session_restores_existing_session_without_histories
    対象: 履歴ゼロの既存セッションでも init_session が復元成功すること。
- test_init_session_falls_back_when_restored_tool_outputs_raise
    対象: 復元済み tool output 処理で例外が起きても init_session が
    fallback して継続できること。
"""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from .chat_service_contract_helpers import (
    _FakeRunResult,
    _FakeRunStream,
    _get_active_agent_name,
    _get_conversation,
    _get_position_id,
    _inner,
    _set_position_id,
)
from domain.entities.chat_history import ChatHistory
from domain.entities.chat_session import ChatSessionStatus
from services.chat_service import POSITION_SEARCH_FAKE_RESULT
from services.llm_service import AgentName
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.enum import LLMMessageRole, PageName
from utils.log_utils import get_session_id, set_session_id


FIXTURES_DIR = Path(__file__).with_name("fixtures")
_VARIANTS = [
    "legacy",
    "real-refactored",
]
_SESSION_ID = "test-session-init-residuals"


def _load_json_fixture(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _make_history(**kwargs) -> ChatHistory:
    defaults = {
        "id": 1,
        "session_id": _SESSION_ID,
        "position_id": None,
        "active_agent": "CareerAdvisor",
        "message_id": "history-message",
        "role": LLMMessageRole.USER,
        "content": "history content",
        "tool_call_id": None,
        "tool_name": None,
        "tool_input": None,
    }
    defaults.update(kwargs)
    return ChatHistory(**defaults)


def _make_chat_request(
    *,
    current_page: PageName = PageName.CHAT,
    position_id: str | None = None,
    message: str = "続けてください",
) -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=current_page,
        position_id=position_id,
        message=message,
        current_message_id="msg-init-residuals",
    )


class _ExplodingDict(dict):
    def get(self, key, default=None):
        raise RuntimeError(f"boom:{key}")


pytestmark = pytest.mark.pre_extraction_parity


@pytest.mark.rollback_di
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_init_session_uses_current_filter_tool_name_and_selected_jobtypes(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    position_guide = MagicMock()
    position_guide.name = AgentName.POSITION_GUIDE
    position_guide.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {
        "CareerAdvisor": (default_agent, True),
        AgentName.POSITION_GUIDE: (position_guide, False),
    }
    svc._position_service.current_search_filter = AsyncMock(
        return_value={
            "ToolName": "  search_job_postings  ",
            "SearchFilters": {
                "Jobtypes": {
                    "selected": [
                        {"Value": " データサイエンティスト ", "Selected": True},
                        {"Value": "データサイエンティスト", "Selected": True},
                        {"Value": "", "Selected": True},
                        {"Value": "機械学習エンジニア", "Selected": False},
                    ],
                    "ignored": "not-a-list",
                }
            },
        }
    )
    svc._chat_repository.init_chat_session.return_value = (None, False)

    status, is_new_session = await chat_svc.init_session("gpt-4o")

    assert status == ChatSessionStatus.CHATTING
    assert is_new_session is True
    svc._llm_svc.clone_agents.assert_called_once_with(
        "gpt-4o",
        ["データサイエンティスト"],
        "search_job_postings",
    )
    assert _get_active_agent_name(svc) == "CareerAdvisor"


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_init_session_falls_back_when_current_search_filter_lookup_fails(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    svc._position_service.current_search_filter = AsyncMock(
        side_effect=RuntimeError("filter lookup failed")
    )

    status, is_new_session = await chat_svc.init_session("gpt-4o")

    assert status == ChatSessionStatus.CHATTING
    assert is_new_session is True
    svc._llm_svc.clone_agents.assert_called_once_with("gpt-4o")


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_init_session_ignores_invalid_current_filter_shapes(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    invalid_filters = [
        {"ToolName": 123},
        {"ToolName": "search_job_postings", "SearchFilters": []},
        {"ToolName": "search_job_postings", "SearchFilters": {"Jobtypes": None}},
        {"ToolName": "search_job_postings", "SearchFilters": {"Jobtypes": []}},
        {
            "ToolName": "search_job_postings",
            "SearchFilters": {
                "Jobtypes": {
                    "group": [
                        123,
                        {"Value": 5, "Selected": True},
                        {"Value": "  ", "Selected": True},
                    ]
                }
            },
        },
    ]

    for current_filter in invalid_filters:
        svc._llm_svc.clone_agents.reset_mock()
        svc._llm_svc.clone_agents.return_value = {
            "CareerAdvisor": (default_agent, True)
        }
        svc._position_service.current_search_filter = AsyncMock(
            return_value=current_filter
        )

        status, is_new_session = await chat_svc.init_session("gpt-4o")

        assert status == ChatSessionStatus.CHATTING
        assert is_new_session is True
        if isinstance(current_filter.get("ToolName"), str):
            svc._llm_svc.clone_agents.assert_called_once_with(
                "gpt-4o",
                [],
                "search_job_postings",
            )
        else:
            svc._llm_svc.clone_agents.assert_called_once_with("gpt-4o")


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_init_session_generates_new_session_id_when_repository_reports_exists(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    set_session_id("before-init-session-id")

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    svc._chat_repository.init_chat_session.return_value = (None, True)

    status, is_new_session = await chat_svc.init_session("gpt-4o")

    assert status == ChatSessionStatus.CHATTING
    assert is_new_session is True
    assert get_session_id() != "before-init-session-id"


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_init_session_returns_error_when_resume_history_has_only_position_guide(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {
        "CareerAdvisor": (default_agent, True),
        AgentName.POSITION_GUIDE: (default_agent, False),
    }
    histories = [
        _make_history(
            active_agent=AgentName.POSITION_GUIDE,
            role=LLMMessageRole.USER,
            content="ポジション詳細の会話だけが残っています",
        )
    ]
    svc._chat_repository.init_chat_session.return_value = (
        SimpleNamespace(
            session_id=_SESSION_ID,
            status=ChatSessionStatus.CHATTING,
            histories=histories,
        ),
        True,
    )

    status, is_new_session = await chat_svc.init_session("gpt-4o")

    assert status == ChatSessionStatus.ERROR
    assert is_new_session is False


@pytest.mark.rollback_di
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_init_session_restores_position_and_tool_histories_into_chat_input(
    variant, chat_service_container
):
    fixture = _load_json_fixture("history_mapping.json")
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    position_guide = MagicMock()
    position_guide.name = AgentName.POSITION_GUIDE
    position_guide.tool_use_behavior = {}
    position_agent = MagicMock()
    position_agent.name = AgentName.POSITION_GUIDE
    position_agent.tool_use_behavior = {}
    position_guide.clone.return_value = position_agent
    svc._llm_svc.clone_agents.return_value = {
        "CareerAdvisor": (default_agent, True),
        AgentName.POSITION_GUIDE: (position_guide, False),
    }

    position_id = 101
    _set_position_id(svc, str(position_id))
    histories = [
        _make_history(
            position_id=position_id,
            active_agent=AgentName.POSITION_GUIDE,
            message_id="pos-tool-empty",
            role=LLMMessageRole.TOOL,
            content="",
            tool_call_id="call-empty",
            tool_name="save_user_preference",
            tool_input={"Keyword": "empty"},
        ),
        _make_history(
            position_id=position_id,
            active_agent=AgentName.POSITION_GUIDE,
            message_id="pos-tool-position",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"AllPositionIds": ["p1", "p2"]}, ensure_ascii=False),
            tool_call_id="call-position",
            tool_name="search_job_postings",
            tool_input={"Keyword": "engineer"},
        ),
        _make_history(
            message_id="jobtype-tool",
            role=LLMMessageRole.TOOL,
            content=json.dumps(
                {"職種": [{"職種名": "SE", "職種説明": "システムエンジニア"}]},
                ensure_ascii=False,
            ),
            tool_call_id="call-jobtype",
            tool_name="search_occupations_by_sentence",
            tool_input={"Keyword": "engineer"},
        ),
        _make_history(
            message_id="reasoning-item",
            role=LLMMessageRole.REASONING,
            content="should be ignored",
        ),
        _make_history(
            message_id="unsupported-item",
            role="unsupported-role",
            content="unsupported",
        ),
        _make_history(
            message_id="main-user-message",
            role=LLMMessageRole.USER,
            content="こんにちは",
        ),
    ]
    svc._chat_repository.init_chat_session.return_value = (
        SimpleNamespace(
            session_id=_SESSION_ID,
            status=ChatSessionStatus.CHATTING,
            histories=histories,
        ),
        True,
    )
    svc._chat_repository.get_main_chat_histories.return_value = [
        h for h in histories if h.position_id is None
    ]

    captured_inputs = []

    if variant == "legacy":

        def _capture_run(**kwargs):
            captured_inputs.append(copy.deepcopy(kwargs["input"]))
            return _FakeRunResult([])

        svc._run_streamed = MagicMock(side_effect=_capture_run)
    else:
        # real-refactored uses _llm_runner.run_streamed.
        # _inner(chat_svc) returns chat_svc itself for these variants (no _legacy_chat_service).
        def _capture_refactored(starting_agent, input, **kwargs):
            captured_inputs.append(copy.deepcopy(input))
            return _FakeRunStream([])

        chat_svc._llm_runner.run_streamed = MagicMock(side_effect=_capture_refactored)

    status, is_new_session = await chat_svc.init_session("gpt-4o")
    assert status == ChatSessionStatus.CHATTING
    assert is_new_session is False

    async for _ in chat_svc.chat(_make_chat_request(), "127.0.0.1"):
        pass

    # legacy uses services.chat_service.decrypt; real-refactored uses
    # services.chat_service_refactored.decrypt — patch both so the test
    # works uniformly across variants.
    with (
        patch("services.chat_service.decrypt", return_value=str(position_id)),
        patch(
            "services.chat_service_refactored.decrypt",
            return_value=str(position_id),
        ),
    ):
        async for _ in chat_svc.chat(
            _make_chat_request(
                current_page=PageName.POSITION_DETAIL,
                position_id="encrypted-position-id",
                message="求人の詳細を教えてください",
            ),
            "127.0.0.1",
        ):
            pass

    main_conversation_input = captured_inputs[0]
    position_conversation_input = captured_inputs[1]
    position_guide.clone.assert_called_once()
    assert any(
        item.get("type") == "function_call_output"
        and item.get("call_id") == "call-empty"
        and item.get("output") == "ツール実行結果がまだありません。"
        for item in position_conversation_input
        if isinstance(item, dict)
    )
    assert any(
        item.get("type") == "function_call_output"
        and item.get("call_id") == "call-position"
        and item.get("output")
        == "2件の求人が見つかりました。ユーザーには別の手段で求人の検索結果を見せていますが、ユーザーから条件変更や再度見たいとの要望があれば、検索条件の差異に関わらず、再度このツールを実行してください。"
        for item in position_conversation_input
        if isinstance(item, dict)
    )
    assert any(
        item.get("type") == "function_call_output"
        and item.get("call_id") == "call-jobtype"
        and "###職種一覧" in item.get("output", "")
        and '"ID": "SE"' in item.get("output", "")
        and "システムエンジニア" in item.get("output", "")
        for item in main_conversation_input
        if isinstance(item, dict)
    )
    assert not any(
        isinstance(item, dict)
        and item.get("type") == "message"
        and item.get("content") == "should be ignored"
        for item in main_conversation_input + position_conversation_input
    )
    assert fixture["history_scenarios"]["residual_init_session"]["_expected_keys"] == [
        "current_search_filter",
        "restored_histories",
        "previous_history_contract",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_init_session_uses_generic_fake_result_when_position_output_is_invalid(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    histories = [
        _make_history(
            message_id="broken-position-output",
            role=LLMMessageRole.TOOL,
            content="{not-json}",
            tool_call_id="call-broken-position",
            tool_name="search_job_postings",
            tool_input={"Keyword": "engineer"},
        ),
        _make_history(
            message_id="main-user-message",
            role=LLMMessageRole.USER,
            content="こんにちは",
        ),
    ]
    svc._chat_repository.init_chat_session.return_value = (
        SimpleNamespace(
            session_id=_SESSION_ID,
            status=ChatSessionStatus.CHATTING,
            histories=histories,
        ),
        True,
    )
    svc._chat_repository.get_main_chat_histories.return_value = histories

    if variant == "legacy":
        captured = {}

        def _capture_legacy(**kwargs):
            captured["input"] = copy.deepcopy(kwargs.get("input", []))
            return _FakeRunResult([])

        svc._run_streamed = MagicMock(side_effect=_capture_legacy)
    else:
        # real-refactored routes through
        # _llm_runner.run_streamed. Capture the `input` positional argument.
        captured = {}

        def _capture_refactored(starting_agent, input, **kwargs):
            captured["input"] = copy.deepcopy(input)
            return _FakeRunStream([])

        chat_svc._llm_runner.run_streamed = MagicMock(side_effect=_capture_refactored)

    await chat_svc.init_session("gpt-4o")
    async for _ in chat_svc.chat(_make_chat_request(), "127.0.0.1"):
        pass

    conversation_input = captured["input"]
    assert any(
        item.get("type") == "function_call_output"
        and item.get("call_id") == "call-broken-position"
        and item.get("output")
        == "0件の求人が見つかりました。ユーザーには別の手段で求人の検索結果を見せていますが、ユーザーから条件変更や再度見たいとの要望があれば、検索条件の差異に関わらず、再度このツールを実行してください。"
        for item in conversation_input
        if isinstance(item, dict)
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_init_session_restores_existing_session_without_histories(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    svc._chat_repository.init_chat_session.return_value = (
        SimpleNamespace(
            session_id=_SESSION_ID,
            status=ChatSessionStatus.APPLYING,
            histories=[],
        ),
        True,
    )

    status, is_new_session = await chat_svc.init_session("gpt-4o")

    assert status == ChatSessionStatus.APPLYING
    assert is_new_session is True
    assert _get_conversation(svc)["MAIN"] == [svc._toolcall_trace_message]


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_init_session_falls_back_when_restored_tool_outputs_raise(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    svc._llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    histories = [
        _make_history(
            message_id="user-before-tools",
            role=LLMMessageRole.USER,
            content="前の会話があります",
        ),
        _make_history(
            message_id="position-tool-explodes",
            role=LLMMessageRole.TOOL,
            content=_ExplodingDict({"AllPositionIds": ["p1"]}),
            tool_call_id="call-position-explodes",
            tool_name="search_job_postings",
            tool_input={"Keyword": "engineer"},
        ),
        _make_history(
            message_id="jobtype-tool-explodes",
            role=LLMMessageRole.TOOL,
            content=json.dumps(
                {"職種": [{"職種名": "SE", "職種説明": "システムエンジニア"}]},
                ensure_ascii=False,
            ),
            tool_call_id="call-jobtype-explodes",
            tool_name="search_occupations_by_sentence",
            tool_input={"Keyword": "engineer"},
        ),
    ]
    svc._chat_repository.init_chat_session.return_value = (
        SimpleNamespace(
            session_id=_SESSION_ID,
            status=ChatSessionStatus.CHATTING,
            histories=histories,
        ),
        True,
    )
    svc._chat_repository.get_main_chat_histories.return_value = histories

    _patch_target = svc._history_mapper if hasattr(svc, "_history_mapper") else svc
    _patch_method = (
        "process_jobtype_search_result"
        if hasattr(svc, "_history_mapper")
        else "_process_jobtype_search_result"
    )
    with patch.object(
        _patch_target, _patch_method, side_effect=RuntimeError("jobtype-boom")
    ):
        status, is_new_session = await chat_svc.init_session("gpt-4o")

    assert status == ChatSessionStatus.CHATTING
    assert is_new_session is False
    assert any(
        item.get("type") == "function_call_output"
        and item.get("call_id") == "call-position-explodes"
        and item.get("output") == POSITION_SEARCH_FAKE_RESULT
        for item in _get_conversation(svc)["MAIN"]
        if isinstance(item, dict)
    )
    assert any(
        item.get("type") == "function_call_output"
        and item.get("call_id") == "call-jobtype-explodes"
        and "###職種一覧" in item.get("output", "")
        and "\n[]\n" in item.get("output", "")
        for item in _get_conversation(svc)["MAIN"]
        if isinstance(item, dict)
    )
