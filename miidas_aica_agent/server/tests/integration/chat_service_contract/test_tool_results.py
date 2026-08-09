"""
Tool result response shape 完全な振る舞いアサーション (Phase 3, feature-3, task-2)。

テスト対象公開インターフェース:
- ChatService.init_session(model_name: str) -> tuple[ChatSessionStatus, bool]
- ChatService.chat(input: ChatRequestModel, client_ip: str) -> AsyncGenerator[ChatStreamResponseModel, None]

Runner が tool call イベントを emit したとき、chat() が yield する ChatStreamResponseModel の
JSON shape が tool_results.json の各 _expected_keys と一致することを検証する。

テストケース一覧:
- test_position_search_tool_result_response_shape
    対象: Runner が position search ToolCallItem → ToolCallOutputItem を emit したとき、
    chat() が response_type=POSITION_SEARCH_RESULT の ChatStreamResponseModel を yield し、
    その model_dump() のキーが tool_results.json の position_search._expected_keys と一致すること。

- test_job_type_search_tool_result_response_shape
    対象: Runner が job type search ToolCallItem → ToolCallOutputItem を emit したとき、
    chat() が response_type=JOBTYPE_SEARCH_RESULT の ChatStreamResponseModel を yield し、
    その model_dump() のキーが tool_results.json の job_type_search._expected_keys と一致すること。

- test_workflow_start_tool_result_response_shape
    対象: Runner が start_workflow ToolCallItem → ToolCallOutputItem を emit したとき、
    chat() が response_type=WORKFLOW の ChatStreamResponseModel を yield し、
    その model_dump() のキーが tool_results.json の workflow_start._expected_keys と一致すること。

- test_chat_yields_end_response_when_session_init_fails
    対象: chat() 実行時に ChatService.init_session() が失敗したとき、
    chat() が終了用の ChatStreamResponseModel を yield すること。

マーカー:
- rollback_runner: Runner tool results は legacy shape を保持することを保証
- pre_extraction_parity: Tool result shape は pre-extraction parity gate の一部
"""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agents import ToolCallItem, ToolCallOutputItem
from .chat_service_contract_helpers import (
    _FakeRunResult,
    _FakeRunStream,
    _inner,
    _make_run_item_event,
    _state,
    _setup_existing_session,
)
from domain.entities.chat_session import ChatSessionStatus
from domain.entities.workflow_definition import (
    DisplayType,
    SelectionType,
    WorkflowDefinition,
    WorkflowOptionItem,
    WorkflowStep,
)
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.chat_response import ChatResponseType, ChatStreamResponseModel
from utils.const import MAIN_CHAT_KEY
from utils.enum import PageName
from utils.log_utils import set_session_id

FIXTURES_DIR = Path(__file__).with_name("fixtures")

_SESSION_ID = "test-session-tool-results"


def _load_json_fixture(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _make_chat_request(message: str = "検索してください") -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        message=message,
        current_message_id="msg-tool-test",
    )


def _make_default_agent_mock() -> MagicMock:
    """CareerAdvisor 名で最小限のアジェントモックを返す。"""
    agent_mock = MagicMock()
    agent_mock.name = "CareerAdvisor"
    agent_mock.tool_use_behavior = {}
    return agent_mock


async def _collect_tool_responses(
    chat_svc, response_type, request
) -> list[ChatStreamResponseModel]:
    """指定した response_type の ChatStreamResponseModel を chat() から収集する。

    ChatStreamResponse は self._model を mutate しながら同じオブジェクトを yield する設計のため、
    model_copy(deep=True) でスナップショットを取得してから収集する。
    """
    responses = []
    async for response in chat_svc.chat(request, "127.0.0.1"):
        if response.response_type == response_type:
            responses.append(response.model_copy(deep=True))
    return responses


def _assert_response_shape_matches(
    actual_response, expected_keys: list, tool_name: str
) -> None:
    """tool result response の model_dump() キーセットが期待値と一致することをアサートする。"""
    actual_keys = sorted(actual_response.model_dump().keys())
    assert sorted(expected_keys) == actual_keys, (
        f"{tool_name} response shape mismatch. "
        f"Expected keys: {sorted(expected_keys)}, "
        f"Actual keys: {actual_keys}"
    )


def _assert_message_payload_shape_matches(
    actual_response, expected_keys: list, tool_name: str
) -> None:
    """tool result response.message を JSON パースし、ペイロードのトップレベルキーセットが期待値と一致することをアサートする。"""
    payload = json.loads(actual_response.message)
    actual_keys = sorted(payload.keys())
    assert sorted(expected_keys) == actual_keys, (
        f"{tool_name} message payload shape mismatch. "
        f"Expected keys: {sorted(expected_keys)}, "
        f"Actual keys: {actual_keys}"
    )


def _assert_list_entry_shape_matches(
    entries: list, expected_keys: list, context: str
) -> None:
    """リスト型ペイロードの各エントリのキーセットが期待値と一致することをアサートする。

    空リストは vacuous success を防ぐためアサートエラーとする。
    """
    assert entries, f"{context} must not be empty"
    for i, entry in enumerate(entries):
        actual_keys = sorted(entry.keys())
        assert sorted(expected_keys) == actual_keys, (
            f"{context}[{i}] shape mismatch. "
            f"Expected keys: {sorted(expected_keys)}, "
            f"Actual keys: {actual_keys}"
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


def _make_workflow_definition(
    workflow_id: str = "test-workflow-001",
    name: str = "テストワークフロー",
    display_type: DisplayType = DisplayType.MODAL,
) -> WorkflowDefinition:
    """テスト用の最小限 WorkflowDefinition を生成する。

    chat_service.py 内で `definition.model_dump(by_alias=True)` が呼ばれるため、
    MagicMock ではなく Pydantic の real instance が必要。
    """
    return WorkflowDefinition(
        id=workflow_id,
        name=name,
        displayType=display_type,
        steps=[
            WorkflowStep(
                id=1,
                question="どの職種に興味がありますか？",
                questionPrompt="どの職種に興味がありますか？",
                selectionType=SelectionType.SINGLE,
                options=[
                    WorkflowOptionItem(
                        label="エンジニア",
                        value=1,
                        allowFreeText=False,
                    )
                ],
            )
        ],
    )


pytestmark = pytest.mark.pre_extraction_parity


@pytest.mark.rollback_runner
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_position_search_tool_result_response_shape(
    variant, chat_service_container_tool_results
):
    """Runner が position search tool call を emit したとき、response shape が legacy contract と一致する。

    不変条件: _run_streamed が ToolCallItem(search_job_postings) →
    ToolCallOutputItem の順にイベントを yield すると、chat() が
    response_type=POSITION_SEARCH_RESULT の ChatStreamResponseModel を yield し、
    その model_dump() のキーが tool_results.json の position_search._expected_keys に一致する。
    """
    chat_svc = chat_service_container_tool_results
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    agent_mock = _make_default_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)

    # position_repository.process_position_search_result をスタブ
    position_repo_mock = MagicMock()
    position_repo_mock.process_position_search_result.return_value = {
        "SearchConditions": {"Keywords": ["エンジニア"]},
        "AllPositionIds": ["pos-001", "pos-002"],
        "PositionCount": 2,
    }
    svc._position_repository = position_repo_mock

    # ToolCallItem: search_job_postings
    tool_call_raw = SimpleNamespace(
        id="tc-pos-001",
        call_id="call-pos-001",
        name="search_job_postings",
        arguments=json.dumps(
            {
                "SessionID": _SESSION_ID,
                "RequestID": "req-001",
                "Keywords": ["エンジニア"],
            }
        ),
    )
    tool_item = ToolCallItem(agent=agent_mock, raw_item=tool_call_raw)

    # ToolCallOutputItem: position search result
    position_output = json.dumps(
        {
            "AllPositionIds": ["pos-001", "pos-002"],
            "SearchConditions": {"Keywords": ["エンジニア"]},
        }
    )
    output_item = ToolCallOutputItem(
        agent=agent_mock,
        raw_item={
            "call_id": "call-pos-001",
            "output": position_output,
            "type": "function_call_output",
        },
        output=position_output,
    )

    events = [_make_run_item_event(tool_item), _make_run_item_event(output_item)]
    _setup_runner_mock(variant, chat_svc, svc, events)

    # Act: chat() を消費して tool result イベントを収集する
    tool_result_responses = await _collect_tool_responses(
        chat_svc, ChatResponseType.POSITION_SEARCH_RESULT, _make_chat_request()
    )

    # Assert: tool result response が yield されること
    assert tool_result_responses, (
        "Expected at least one POSITION_SEARCH_RESULT response from chat(); got none"
    )

    # Assert: response shape が fixture の _expected_keys と一致すること
    fixture = _load_json_fixture("tool_results.json")
    expected_keys = fixture["tool_results"]["position_search"]["_expected_keys"]
    _assert_response_shape_matches(
        tool_result_responses[0], expected_keys, "Position search"
    )

    # Assert: message payload shape が fixture の _expected_message_keys と一致すること
    expected_message_keys = fixture["tool_results"]["position_search"][
        "_expected_message_keys"
    ]
    _assert_message_payload_shape_matches(
        tool_result_responses[0], expected_message_keys, "Position search"
    )

    # Assert: response_type が fixture の contract と一致すること
    assert tool_result_responses[0].response_type == ChatResponseType(
        fixture["tool_results"]["position_search"]["response_type"]
    )


@pytest.mark.rollback_runner
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_job_type_search_tool_result_response_shape(
    variant, chat_service_container_tool_results
):
    """Runner が job type search tool call を emit したとき、response shape が legacy contract と一致する。

    不変条件: _run_streamed が ToolCallItem(search_occupations_by_sentence) →
    ToolCallOutputItem の順にイベントを yield すると、chat() が
    response_type=JOBTYPE_SEARCH_RESULT の ChatStreamResponseModel を yield し、
    その model_dump() のキーが tool_results.json の job_type_search._expected_keys に一致する。
    """
    chat_svc = chat_service_container_tool_results
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    agent_mock = _make_default_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)

    # ToolCallItem: search_occupations_by_sentence
    tool_call_raw = SimpleNamespace(
        id="tc-jt-001",
        call_id="call-jt-001",
        name="search_occupations_by_sentence",
        arguments=json.dumps(
            {"SessionID": _SESSION_ID, "RequestID": "req-002", "Keyword": "エンジニア"}
        ),
    )
    tool_item = ToolCallItem(agent=agent_mock, raw_item=tool_call_raw)

    # ToolCallOutputItem: job type search result with 職種 list
    jobtype_output = json.dumps(
        {
            "職種": [
                {"職種名": "SE", "職種説明": "システムエンジニア"},
                {"職種名": "PG", "職種説明": "プログラマー"},
            ],
            "Keyword": "エンジニア",
        }
    )
    output_item = ToolCallOutputItem(
        agent=agent_mock,
        raw_item={
            "call_id": "call-jt-001",
            "output": jobtype_output,
            "type": "function_call_output",
        },
        output=jobtype_output,
    )

    events = [_make_run_item_event(tool_item), _make_run_item_event(output_item)]
    _setup_runner_mock(variant, chat_svc, svc, events)

    # Act: chat() を消費して tool result イベントを収集する
    tool_result_responses = await _collect_tool_responses(
        chat_svc, ChatResponseType.JOBTYPE_SEARCH_RESULT, _make_chat_request()
    )

    # Assert: tool result response が yield されること
    assert tool_result_responses, (
        "Expected at least one JOBTYPE_SEARCH_RESULT response from chat(); got none"
    )

    # Assert: response shape が fixture の _expected_keys と一致すること
    fixture = _load_json_fixture("tool_results.json")
    expected_keys = fixture["tool_results"]["job_type_search"]["_expected_keys"]
    _assert_response_shape_matches(
        tool_result_responses[0], expected_keys, "Job type search"
    )

    # Assert: message payload shape が fixture の _expected_message_keys と一致すること
    expected_message_keys = fixture["tool_results"]["job_type_search"][
        "_expected_message_keys"
    ]
    _assert_message_payload_shape_matches(
        tool_result_responses[0], expected_message_keys, "Job type search"
    )

    # Assert: Jobtypes エントリの shape が fixture の _expected_jobtypes_entry_keys と一致すること
    expected_jobtypes_entry_keys = fixture["tool_results"]["job_type_search"][
        "_expected_jobtypes_entry_keys"
    ]
    payload = json.loads(tool_result_responses[0].message)
    _assert_list_entry_shape_matches(
        payload["Jobtypes"], expected_jobtypes_entry_keys, "Job type search Jobtypes"
    )

    # Assert: response_type が fixture の contract と一致すること
    assert tool_result_responses[0].response_type == ChatResponseType(
        fixture["tool_results"]["job_type_search"]["response_type"]
    )


@pytest.mark.rollback_runner
@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_workflow_start_tool_result_response_shape(
    variant, chat_service_container_tool_results
):
    """Runner が start_workflow tool call を emit したとき、response shape が legacy contract と一致する。

    不変条件: _run_streamed が ToolCallItem(start_workflow) →
    ToolCallOutputItem の順にイベントを yield すると、chat() が
    response_type=WORKFLOW の ChatStreamResponseModel を yield し、
    その model_dump() のキーが tool_results.json の workflow_start._expected_keys に一致する。
    """
    chat_svc = chat_service_container_tool_results
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    agent_mock = _make_default_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)

    # workflow_definition_repository をスタブ: 最小限の WorkflowDefinition を返す。
    # モック方針: WorkflowService はリアルインスタンス、リポジトリ層のみモックする。
    svc._workflow_service._workflow_definition_repository.get_definition.return_value = _make_workflow_definition(
        "test-workflow-001"
    )

    # ToolCallItem: start_workflow
    tool_call_raw = SimpleNamespace(
        id="tc-wf-001",
        call_id="call-wf-001",
        name="start_workflow",
        arguments=json.dumps(
            {
                "SessionID": _SESSION_ID,
                "RequestID": "req-003",
                "WorkflowID": "test-workflow-001",
            }
        ),
    )
    tool_item = ToolCallItem(agent=agent_mock, raw_item=tool_call_raw)

    # ToolCallOutputItem: workflow start result
    workflow_output = json.dumps({"WorkflowID": "test-workflow-001"})
    output_item = ToolCallOutputItem(
        agent=agent_mock,
        raw_item={
            "call_id": "call-wf-001",
            "output": workflow_output,
            "type": "function_call_output",
        },
        output=workflow_output,
    )

    events = [_make_run_item_event(tool_item), _make_run_item_event(output_item)]
    _setup_runner_mock(variant, chat_svc, svc, events)

    # Act: chat() を消費して tool result イベントを収集する
    tool_result_responses = await _collect_tool_responses(
        chat_svc, ChatResponseType.WORKFLOW, _make_chat_request()
    )

    # Assert: tool result response が yield されること
    assert tool_result_responses, (
        "Expected at least one WORKFLOW response from chat(); got none"
    )

    # Assert: response shape が fixture の _expected_keys と一致すること
    fixture = _load_json_fixture("tool_results.json")
    expected_keys = fixture["tool_results"]["workflow_start"]["_expected_keys"]
    _assert_response_shape_matches(
        tool_result_responses[0], expected_keys, "Workflow start"
    )

    # Assert: message payload shape が fixture の _expected_message_keys と一致すること
    expected_message_keys = fixture["tool_results"]["workflow_start"][
        "_expected_message_keys"
    ]
    _assert_message_payload_shape_matches(
        tool_result_responses[0], expected_message_keys, "Workflow start"
    )

    # Assert: steps エントリの shape が fixture の _expected_step_keys と一致すること
    expected_step_keys = fixture["tool_results"]["workflow_start"][
        "_expected_step_keys"
    ]
    payload = json.loads(tool_result_responses[0].message)
    _assert_list_entry_shape_matches(
        payload["steps"], expected_step_keys, "Workflow start steps"
    )

    # Assert: response_type が fixture の contract と一致すること
    assert tool_result_responses[0].response_type == ChatResponseType(
        fixture["tool_results"]["workflow_start"]["response_type"]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["legacy", "real-refactored"])
async def test_chat_yields_end_response_when_session_init_fails(
    variant, chat_service_container_tool_results
):
    """init_session が失敗したとき、chat() は END レスポンスを yield し tool result は yield しない。

    不変条件: init_chat_session が例外を発生させて init_session が (ERROR, False) を返すとき、
    chat() が END レスポンスを yield し、POSITION_SEARCH_RESULT / JOBTYPE_SEARCH_RESULT /
    WORKFLOW の各 response_type は yield されない。
    これは _conversation が未初期化（空の dict）のまま残るため、chat() が
    `MAIN_CHAT_KEY not in self._conv_state.conversation` を検知して END を返す動作を保証する。
    """
    chat_svc = chat_service_container_tool_results
    svc = _inner(chat_svc)
    set_session_id(_SESSION_ID)

    # init_chat_session で例外を発生させてセッション初期化を失敗させる
    svc._chat_repository.init_chat_session.side_effect = Exception(
        "DB connection failed"
    )

    status, is_new = await chat_svc.init_session("gpt-4o")
    assert status == ChatSessionStatus.ERROR, (
        f"Expected ERROR status after init_session failure, got {status}"
    )
    assert is_new is False

    # init_session が失敗したため _conversation は未初期化のまま。
    # MAIN_CHAT_KEY の previous-state を設定し build_summary_context を
    # スキップさせることで、chat() が END ガードを検知できるようにする。
    if variant == "legacy":
        chat_svc._previous_response_ids[MAIN_CHAT_KEY] = "init-failed"
    else:
        _state(chat_svc).previous_continuation_states[MAIN_CHAT_KEY] = "init-failed"

    # Act: セッション未初期化状態で chat() を呼ぶ
    all_responses = []
    async for response in chat_svc.chat(_make_chat_request(), "127.0.0.1"):
        all_responses.append(response.model_copy(deep=True))

    # Assert: END レスポンスが yield されること（_conversation が未初期化のため）
    assert any(r.response_type == ChatResponseType.END for r in all_responses), (
        f"Expected END response after session init failure; got {[r.response_type for r in all_responses]}"
    )

    # Assert: tool result レスポンスは yield されないこと
    _tool_result_types = {
        ChatResponseType.POSITION_SEARCH_RESULT,
        ChatResponseType.JOBTYPE_SEARCH_RESULT,
        ChatResponseType.WORKFLOW,
    }
    assert not any(r.response_type in _tool_result_types for r in all_responses), (
        f"Expected no tool result responses when session init failed; got {[r.response_type for r in all_responses]}"
    )
