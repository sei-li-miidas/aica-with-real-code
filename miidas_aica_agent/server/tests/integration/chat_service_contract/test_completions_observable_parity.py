"""
Observable parity テスト: responses vs completions api_style の chat() 出力が同一であることを検証する。

テストケース一覧:
- test_response_shape_parity_responses_vs_completions
    対象: LLMRawResponseEvent テキストデルタを両 api_style に注入したとき、
    MESSAGE / END レスポンスの response_type と message が一致すること。

- test_stream_chunk_ordering_parity
    対象: 複数 LLMRawResponseEvent チャンクを注入したとき、MESSAGE チャンクが
    同じ順序で yield され、END が最後であること。

- test_tool_result_parity_responses_vs_completions
    対象: ToolCallItem + ToolCallOutputItem を注入したとき、両 api_style が
    同じ response_type シーケンスの POSITION_SEARCH_RESULT を yield すること。

- test_end_behavior_parity_empty_stream
    対象: 空のイベントストリームで両 api_style が END だけを yield すること。

マーカー:
- completions_contract: Gate B completions config / contract matrix
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from services.chat.llm_runner import LLMRawResponseEvent
from utils.chat_response import ChatResponseType
from utils.log_utils import clear_session_id, set_session_id

from .chat_service_contract_helpers import (
    _FakeRunStream,
    build_parity_container,
    make_agent_mock,
    make_chat_request,
    _make_run_item_event,
    _setup_existing_session,
)

pytestmark = pytest.mark.completions_contract

_SESSION_ID = "test-parity-observable"


@pytest.fixture(autouse=True)
def _session_scope():
    set_session_id(_SESSION_ID)
    yield
    clear_session_id()


async def _run_chat_and_collect(chat_svc, events: list) -> list:
    """指定イベントを注入して chat() を実行し、レスポンスのスナップショットリストを返す。"""
    chat_svc._llm_runner.run_streamed.return_value = _FakeRunStream(events)

    agent_mock = make_agent_mock()
    await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)

    responses = []
    async for response in chat_svc.chat(
        make_chat_request(message_id="msg-parity-test"),
        "127.0.0.1",
    ):
        responses.append(response.model_copy(deep=True))
    return responses


@pytest.mark.asyncio
async def test_response_shape_parity_responses_vs_completions(tmp_path):
    """LLMRawResponseEvent テキストデルタを注入したとき、両 api_style の MESSAGE/END 出力が同一であること。

    不変条件: 同一の raw_response_event を注入した場合、
    api_style=responses と api_style=completions は同じ response_type / message を yield する。
    """
    events = [
        LLMRawResponseEvent(item_id="msg-item-1", delta="こんにちは"),
    ]

    container_r, _ = build_parity_container("responses", str(tmp_path))
    chat_svc_r = container_r.chat_svc()

    container_c, _ = build_parity_container("completions", str(tmp_path))
    chat_svc_c = container_c.chat_svc()

    responses_r = await _run_chat_and_collect(chat_svc_r, events)
    responses_c = await _run_chat_and_collect(chat_svc_c, events)

    # MESSAGE レスポンスが存在する
    msg_r = [r for r in responses_r if r.response_type == ChatResponseType.MESSAGE]
    msg_c = [r for r in responses_c if r.response_type == ChatResponseType.MESSAGE]
    assert msg_r, "responses style: MESSAGE レスポンスが存在すること"
    assert msg_c, "completions style: MESSAGE レスポンスが存在すること"

    # response_type が一致する
    assert msg_r[0].response_type == msg_c[0].response_type

    # message 本文が一致する
    assert msg_r[0].message == msg_c[0].message

    # END が存在する
    assert any(r.response_type == ChatResponseType.END for r in responses_r), (
        "responses style: END レスポンスが存在すること"
    )
    assert any(r.response_type == ChatResponseType.END for r in responses_c), (
        "completions style: END レスポンスが存在すること"
    )


@pytest.mark.asyncio
async def test_stream_chunk_ordering_parity(tmp_path):
    """複数 LLMRawResponseEvent を注入したとき、両 api_style の MESSAGE チャンク順序が同一であること。

    不変条件: 複数の raw_response_event を同順に注入した場合、
    api_style=responses と api_style=completions は同じ順序で MESSAGE を yield し、
    END が最後に来る。
    """
    events = [
        LLMRawResponseEvent(item_id="msg-item-1", delta="最初"),
        LLMRawResponseEvent(item_id="msg-item-2", delta="次"),
        LLMRawResponseEvent(item_id="msg-item-3", delta="最後"),
    ]

    container_r, _ = build_parity_container("responses", str(tmp_path))
    chat_svc_r = container_r.chat_svc()

    container_c, _ = build_parity_container("completions", str(tmp_path))
    chat_svc_c = container_c.chat_svc()

    responses_r = await _run_chat_and_collect(chat_svc_r, events)
    responses_c = await _run_chat_and_collect(chat_svc_c, events)

    types_r = [r.response_type for r in responses_r]
    types_c = [r.response_type for r in responses_c]

    # 最後が END であること
    assert types_r[-1] == ChatResponseType.END, (
        f"responses style: 最後のレスポンスが END であること。実際: {types_r}"
    )
    assert types_c[-1] == ChatResponseType.END, (
        f"completions style: 最後のレスポンスが END であること。実際: {types_c}"
    )

    # MESSAGE チャンクを抽出
    msg_r = [r for r in responses_r if r.response_type == ChatResponseType.MESSAGE]
    msg_c = [r for r in responses_c if r.response_type == ChatResponseType.MESSAGE]

    # チャンク数が一致する
    assert len(msg_r) == len(msg_c), (
        f"MESSAGE チャンク数が一致すること。responses={len(msg_r)}, completions={len(msg_c)}"
    )

    # 各チャンクの message が一致する
    for i, (r_resp, c_resp) in enumerate(zip(msg_r, msg_c)):
        assert r_resp.message == c_resp.message, (
            f"チャンク[{i}] message が一致すること: responses={r_resp.message!r}, completions={c_resp.message!r}"
        )


@pytest.mark.asyncio
async def test_tool_result_parity_responses_vs_completions(tmp_path):
    """ToolCallItem + ToolCallOutputItem を注入したとき、両 api_style の POSITION_SEARCH_RESULT が同一であること。

    不変条件: search_job_postings の ToolCallItem → ToolCallOutputItem を注入した場合、
    api_style=responses と api_style=completions は同じ response_type=POSITION_SEARCH_RESULT を yield する。
    """
    from agents import ToolCallItem, ToolCallOutputItem

    agent_mock = make_agent_mock()

    tool_call_raw = SimpleNamespace(
        id="tc-pos-parity-001",
        call_id="call-pos-parity-001",
        name="search_job_postings",
        arguments=json.dumps(
            {
                "SessionID": _SESSION_ID,
                "RequestID": "req-parity-001",
                "Keywords": ["エンジニア"],
            }
        ),
    )
    tool_item = ToolCallItem(agent=agent_mock, raw_item=tool_call_raw)

    position_output = json.dumps(
        {
            "AllPositionIds": ["pos-001", "pos-002"],
            "SearchConditions": {"Keywords": ["エンジニア"]},
        }
    )
    output_item = ToolCallOutputItem(
        agent=agent_mock,
        raw_item={
            "call_id": "call-pos-parity-001",
            "output": position_output,
            "type": "function_call_output",
        },
        output=position_output,
    )

    events = [_make_run_item_event(tool_item), _make_run_item_event(output_item)]

    position_repo_mock = MagicMock()
    position_repo_mock.process_position_search_result.return_value = {
        "SearchConditions": {"Keywords": ["エンジニア"]},
        "AllPositionIds": ["pos-001", "pos-002"],
        "PositionCount": 2,
    }

    async def _collect_with_position_repo(api_style: str) -> list:
        container, _ = build_parity_container(api_style, str(tmp_path))
        chat_svc = container.chat_svc()
        # position_repository をスタブに差し替える
        chat_svc._position_repository = position_repo_mock
        chat_svc._llm_runner.run_streamed.return_value = _FakeRunStream(events)
        _agent = make_agent_mock()
        await _setup_existing_session(chat_svc, _agent, _SESSION_ID)
        responses = []
        async for response in chat_svc.chat(
            make_chat_request(message_id="msg-parity-test"),
            "127.0.0.1",
        ):
            responses.append(response.model_copy(deep=True))
        return responses

    responses_r = await _collect_with_position_repo("responses")
    responses_c = await _collect_with_position_repo("completions")

    pos_r = [
        r
        for r in responses_r
        if r.response_type == ChatResponseType.POSITION_SEARCH_RESULT
    ]
    pos_c = [
        r
        for r in responses_c
        if r.response_type == ChatResponseType.POSITION_SEARCH_RESULT
    ]

    assert pos_r, "responses style: POSITION_SEARCH_RESULT が存在すること"
    assert pos_c, "completions style: POSITION_SEARCH_RESULT が存在すること"

    # response_type が一致する
    assert pos_r[0].response_type == pos_c[0].response_type

    # model_dump() の payload 全体（キー・値とも）が一致する。
    # キーセットだけでなく値まで比較することで、片方の style だけ field が
    # 欠ける/増える/値が変わるといった observable payload 差分も検知する。
    assert pos_r[0].model_dump() == pos_c[0].model_dump(), (
        "POSITION_SEARCH_RESULT の model_dump() payload 全体が一致すること"
    )


@pytest.mark.asyncio
async def test_end_behavior_parity_empty_stream(tmp_path):
    """空のイベントストリームを注入したとき、両 api_style が END だけを yield すること。

    不変条件: イベントが一件もない場合、
    api_style=responses と api_style=completions は END レスポンスのみを yield し、
    MESSAGE は yield しない。
    """
    events: list = []

    container_r, _ = build_parity_container("responses", str(tmp_path))
    chat_svc_r = container_r.chat_svc()

    container_c, _ = build_parity_container("completions", str(tmp_path))
    chat_svc_c = container_c.chat_svc()

    responses_r = await _run_chat_and_collect(chat_svc_r, events)
    responses_c = await _run_chat_and_collect(chat_svc_c, events)

    types_r = [r.response_type for r in responses_r]
    types_c = [r.response_type for r in responses_c]

    # END が存在する
    assert ChatResponseType.END in types_r, (
        f"responses style: END が存在すること。実際: {types_r}"
    )
    assert ChatResponseType.END in types_c, (
        f"completions style: END が存在すること。実際: {types_c}"
    )

    # MESSAGE は存在しない（空ストリームのため）
    assert ChatResponseType.MESSAGE not in types_r, (
        f"responses style: 空ストリームでは MESSAGE が存在しないこと。実際: {types_r}"
    )
    assert ChatResponseType.MESSAGE not in types_c, (
        f"completions style: 空ストリームでは MESSAGE が存在しないこと。実際: {types_c}"
    )
