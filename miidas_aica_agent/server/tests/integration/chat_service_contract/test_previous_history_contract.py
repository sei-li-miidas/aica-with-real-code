"""
Previous history contract テスト。

テストケース一覧:
- test_check_if_previous_chat_histories_exist_uses_decrypted_position_id
    対象: encrypted position_id を decrypt して
    has_position_chat_histories 判定へ渡すこと。
- test_load_previous_chat_histories_reconstructs_tool_results_and_greeting_tail
    対象: 既存履歴から tool result 復元と greeting tail 補完を行うこと。
- test_load_previous_chat_histories_handles_empty_and_position_detail_paths
    対象: 履歴なしケースと position_detail 導線の
    初期化分岐を正しく処理すること。
- test_load_previous_chat_histories_covers_residual_tool_and_paging_branches
    対象: 残余 tool 分岐と paging 分岐を通して
    退行を防ぐこと。
- test_load_previous_chat_histories_returns_empty_when_limit_is_zero
    対象: limit=0 指定時に履歴を返さず空配列にすること。
- test_load_previous_chat_histories_appends_greeting_tail_when_only_greeting_remains
    対象: greeting のみ残る境界ケースで
    tail 追記ルールを維持すること。
"""

import json
from contextlib import contextmanager, ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from .chat_service_contract_helpers import _inner
from domain.entities.chat_history import ChatHistory
from utils.const import SESSION_START_MESSAGE
from utils.chat_response import ChatResponseType
from utils.enum import LLMMessageRole, LocationType


FIXTURES_DIR = Path(__file__).with_name("fixtures")
_VARIANTS = [
    "legacy",
    "real-refactored",
]
_SESSION_ID = "test-session-previous-history"


@contextmanager
def _patch_decrypt(variant: str, return_value):
    """variant に応じて正しいモジュールの decrypt をパッチする。

    - legacy: services.chat_service.decrypt（legacy path が使用）
    - real-refactored: services.chat_service_refactored.decrypt
    """
    if variant == "legacy":
        with patch("services.chat_service.decrypt", return_value=return_value) as m:
            yield m
    else:
        with ExitStack() as stack:
            m = stack.enter_context(
                patch(
                    "services.chat_service_refactored.decrypt",
                    return_value=return_value,
                )
            )
            yield m


def _load_json_fixture(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _history(**kwargs) -> ChatHistory:
    defaults = {
        "session_id": _SESSION_ID,
        "position_id": None,
        "active_agent": "CareerAdvisor",
        "message_id": "msg",
        "role": LLMMessageRole.USER,
        "content": "history content",
        "tool_call_id": None,
        "tool_name": None,
        "tool_input": None,
    }
    defaults.update(kwargs)
    return ChatHistory(**defaults)


pytestmark = pytest.mark.pre_extraction_parity


@pytest.mark.asyncio
@pytest.mark.rollback_di
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_check_if_previous_chat_histories_exist_uses_decrypted_position_id(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    svc._chat_repository.has_position_chat_histories.return_value = True

    with _patch_decrypt(variant, 321) as decrypt_mock:
        result = await chat_svc.check_if_previous_chat_histories_exist(
            "encrypted-position"
        )

    assert result is True
    decrypt_mock.assert_called_once()
    svc._chat_repository.has_position_chat_histories.assert_called_once_with(321)


@pytest.mark.asyncio
@pytest.mark.rollback_di
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_load_previous_chat_histories_reconstructs_tool_results_and_greeting_tail(
    variant, chat_service_container
):
    fixture = _load_json_fixture("history_mapping.json")
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    histories = [
        _history(
            message_id="greeting-dev",
            role=LLMMessageRole.DEVELOPER,
            content=SESSION_START_MESSAGE,
        ),
        _history(
            message_id="greeting-asst",
            role=LLMMessageRole.ASSISTANT,
            content="こんにちは。転職相談を始めましょう。",
        ),
        _history(
            message_id="user-001",
            role=LLMMessageRole.USER,
            content="東京で年収700万円以上の求人はありますか？",
        ),
        _history(
            message_id="tool-pos-001",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"AllPositionIds": ["p1", "p2"]}, ensure_ascii=False),
            tool_call_id="call-pos-001",
            tool_name="search_job_postings",
            tool_input={
                "Salary": 700,
                "Locations": [
                    {
                        "LocationType": LocationType.RESIDENCE,
                        "PrefectureName": "東京都",
                        "CityName": "千代田区",
                    },
                    {
                        "LocationType": LocationType.WORK_LOCATION,
                        "PrefectureName": "東京都",
                        "CityName": "港区",
                    },
                    {
                        "LocationType": LocationType.FULL_REMOTE,
                        "PrefectureName": "",
                        "CityName": "",
                    },
                ],
                "PositionKeyword": "バックエンド",
                "JobtypeNames": ["エンジニア"],
            },
        ),
        _history(
            message_id="assistant-duplicate-1",
            role=LLMMessageRole.ASSISTANT,
            content="まずは該当求人を確認します。",
        ),
        _history(
            message_id="assistant-duplicate-2",
            role=LLMMessageRole.ASSISTANT,
            content="このメッセージは previous history で重複排除されます。",
        ),
        _history(
            message_id="user-002",
            role=LLMMessageRole.USER,
            content="職種候補も見せてください。",
        ),
        _history(
            message_id="tool-jobtype-001",
            role=LLMMessageRole.TOOL,
            content=json.dumps(
                {
                    "職種": [{"職種名": "SE", "職種説明": "システムエンジニア"}],
                    "Keyword": "エンジニア",
                },
                ensure_ascii=False,
            ),
            tool_call_id="call-jobtype-001",
            tool_name="search_occupations_by_sentence",
            tool_input={"Keyword": "エンジニア"},
        ),
        _history(
            message_id="developer-selected-jobtype",
            role=LLMMessageRole.DEVELOPER,
            content="ユーザーが職種「システムエンジニア」を選択しました。",
        ),
        _history(
            message_id="assistant-jobtype",
            role=LLMMessageRole.ASSISTANT,
            content="職種候補はこちらです。",
        ),
    ]
    svc._chat_repository.get_main_chat_histories.return_value = histories

    result, no_more = await chat_svc.load_previous_chat_histories(
        limit=5,
        encrypted_position_id=None,
        before_id=None,
    )

    assert no_more is True
    position_entries = [
        entry
        for entry in result
        if entry["Type"] == ChatResponseType.POSITION_SEARCH_LINK
    ]
    assert len(position_entries) == 1
    assert position_entries[0]["Message"]["Salary"] == 700
    assert position_entries[0]["Message"]["Residence"] == "東京都千代田区"
    assert position_entries[0]["Message"]["WorkLocations"] == ["東京都港区"]
    assert position_entries[0]["Message"]["IsFullyRemoteWork"] is True
    assert position_entries[0]["Message"]["PositionKeyword"] == "バックエンド"
    assert position_entries[0]["Message"]["JobtypeNames"] == ["エンジニア"]

    jobtype_entries = [
        entry
        for entry in result
        if entry["Type"] == ChatResponseType.JOBTYPE_SEARCH_RESULT
    ]
    assert len(jobtype_entries) == 1
    assert jobtype_entries[0]["Message"]["SelectedJobtypeName"] == "システムエンジニア"

    assistant_entries = [
        entry for entry in result if entry["Role"] == LLMMessageRole.ASSISTANT
    ]
    assert (
        sum(
            entry["MessageID"].startswith("assistant-duplicate")
            for entry in assistant_entries
        )
        == 1
    )
    assert any(
        entry["MessageID"] == "greeting-asst"
        and entry["Type"] == ChatResponseType.MESSAGE
        for entry in assistant_entries
    )
    assert fixture["history_scenarios"]["previous_history_contract"][
        "_expected_keys"
    ] == [
        "position_detail_path",
        "tool_result_payloads",
        "session_greeting_tail",
    ]


@pytest.mark.asyncio
@pytest.mark.rollback_di
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_load_previous_chat_histories_handles_empty_and_position_detail_paths(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    svc._chat_repository.get_position_detail_chat_histories.return_value = []

    with _patch_decrypt(variant, 555):
        result, no_more = await chat_svc.load_previous_chat_histories(
            limit=3,
            encrypted_position_id="encrypted-position-id",
            before_id="before-001",
        )

    assert result == []
    assert no_more is True
    svc._chat_repository.get_position_detail_chat_histories.assert_called_once_with(
        555,
        "before-001",
    )


@pytest.mark.asyncio
@pytest.mark.rollback_di
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_load_previous_chat_histories_covers_residual_tool_and_paging_branches(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)

    histories = [
        _history(
            message_id="prefix-assistant",
            role=LLMMessageRole.ASSISTANT,
            content="先頭の補助メッセージ",
        ),
        _history(
            message_id="prefix-developer",
            role=LLMMessageRole.DEVELOPER,
            content="greeting ではない developer",
        ),
        _history(
            message_id="user-empty",
            role=LLMMessageRole.USER,
            content="レスポンスのない質問",
        ),
        _history(
            message_id="unknown-tool",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"ignored": True}, ensure_ascii=False),
            tool_call_id="call-unknown-tool",
            tool_name="unknown_tool",
            tool_input={},
        ),
        _history(
            message_id="user-main",
            role=LLMMessageRole.USER,
            content="主な質問です",
        ),
        _history(
            message_id="position-message",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"Message": "tool failed"}, ensure_ascii=False),
            tool_call_id="call-position-message",
            tool_name="search_job_postings",
            tool_input={"Salary": 700, "Locations": []},
        ),
        _history(
            message_id="position-unknown-location",
            role=LLMMessageRole.TOOL,
            content=json.dumps({"AllPositionIds": ["p1"]}, ensure_ascii=False),
            tool_call_id="call-position-unknown-location",
            tool_name="search_job_postings",
            tool_input={
                "Salary": 700,
                "Locations": [
                    {
                        "LocationType": "mystery",
                        "PrefectureName": "東京都",
                        "CityName": "不明区",
                    }
                ],
                "PositionKeyword": "backend",
                "JobtypeNames": ["エンジニア"],
            },
        ),
        _history(
            message_id="jobtype-no-selection",
            role=LLMMessageRole.TOOL,
            content=json.dumps(
                {
                    "職種": [{"職種名": "SE", "職種説明": "システムエンジニア"}],
                    "Keyword": "engineer",
                },
                ensure_ascii=False,
            ),
            tool_call_id="call-jobtype-no-selection",
            tool_name="search_occupations_by_sentence",
            tool_input={"Keyword": "engineer"},
        ),
        _history(
            message_id="assistant-before-selection-search",
            role=LLMMessageRole.ASSISTANT,
            content="候補を確認します",
        ),
        _history(
            message_id="developer-empty",
            role=LLMMessageRole.DEVELOPER,
            content="",
        ),
        _history(
            message_id="developer-unmatched",
            role=LLMMessageRole.DEVELOPER,
            content="ユーザーはまだ決めていません。",
        ),
    ]
    svc._chat_repository.get_main_chat_histories.return_value = histories

    result, no_more = await chat_svc.load_previous_chat_histories(
        limit=2,
        encrypted_position_id=None,
        before_id=None,
    )

    assert no_more is True
    position_entries = [
        entry
        for entry in result
        if entry["Type"] == ChatResponseType.POSITION_SEARCH_LINK
    ]
    assert len(position_entries) == 1
    assert position_entries[0]["Message"]["Residence"] == ""
    assert position_entries[0]["Message"]["WorkLocations"] == []
    jobtype_entries = [
        entry
        for entry in result
        if entry["Type"] == ChatResponseType.JOBTYPE_SEARCH_RESULT
    ]
    assert len(jobtype_entries) == 1
    assert jobtype_entries[0]["Message"]["SelectedJobtypeName"] is None
    assert all(entry["MessageID"] != "user-empty" for entry in result)

    limited_result, no_more = await chat_svc.load_previous_chat_histories(
        limit=1,
        encrypted_position_id=None,
        before_id=None,
    )

    assert no_more is False
    assert any(entry["MessageID"] == "user-main" for entry in limited_result)
    assert all(entry["MessageID"] != "prefix-assistant" for entry in limited_result)


@pytest.mark.asyncio
@pytest.mark.rollback_di
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_load_previous_chat_histories_returns_empty_when_limit_is_zero(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    svc._chat_repository.get_main_chat_histories.return_value = [
        _history(message_id="user-001", role=LLMMessageRole.USER, content="こんにちは")
    ]

    result, no_more = await chat_svc.load_previous_chat_histories(
        limit=0,
        encrypted_position_id=None,
        before_id=None,
    )

    assert result == []
    assert no_more is False


@pytest.mark.asyncio
@pytest.mark.rollback_di
@pytest.mark.parametrize("variant", _VARIANTS)
async def test_load_previous_chat_histories_appends_greeting_tail_when_only_greeting_remains(
    variant, chat_service_container
):
    chat_svc = chat_service_container
    svc = _inner(chat_svc)
    svc._chat_repository.get_main_chat_histories.return_value = [
        _history(
            message_id="greeting-dev",
            role=LLMMessageRole.DEVELOPER,
            content=SESSION_START_MESSAGE,
        ),
        _history(
            message_id="greeting-asst",
            role=LLMMessageRole.ASSISTANT,
            content="ようこそ。まずは希望を教えてください。",
        ),
        _history(
            message_id="user-latest",
            role=LLMMessageRole.USER,
            content="求人を探したいです",
        ),
        _history(
            message_id="assistant-latest",
            role=LLMMessageRole.ASSISTANT,
            content="条件を確認します。",
        ),
    ]

    result, no_more = await chat_svc.load_previous_chat_histories(
        limit=1,
        encrypted_position_id=None,
        before_id=None,
    )

    assert no_more is True
    assert any(entry["MessageID"] == "greeting-asst" for entry in result)
