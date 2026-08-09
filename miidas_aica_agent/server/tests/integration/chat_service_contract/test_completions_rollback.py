"""
Rollback safety テスト: config-only のキー変更でランナー/サービスが正しく切り替わることを検証する。

テストケース一覧:
- test_rollback_api_style_completions_to_responses_wires_responses_runner
    対象: api_style=completions → responses のフリップで ResponsesAgentRunner に戻ること。

- test_rollback_api_style_completions_chat_service_behavior_matches_responses
    対象: 同一のフェイクイベントを注入したとき、completions と responses の
    chat() response_type シーケンスが一致すること。

- test_rollback_service_variant_refactored_to_legacy_wires_legacy_service
    対象: service_variant=refactored → legacy のフリップで legacy ChatService に戻ること。

マーカー:
- rollback_api_style: Gate B api_style rollback subset
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from dependency_injector import providers

from containers import Container
from services import chat_service, chat_service_refactored
from services.chat.llm_runner import (
    CompletionsAgentRunner,
    LLMRawResponseEvent,
    ResponsesAgentRunner,
)
from utils.chat_response import ChatResponseType
from utils.log_utils import clear_session_id, set_session_id

from .chat_service_contract_helpers import (
    _FakeRunStream,
    build_parity_container,
    make_agent_mock,
    make_chat_request,
    _setup_existing_session,
)

pytestmark = pytest.mark.rollback_api_style

_SESSION_ID = "test-rollback-api-style"


@pytest.fixture(autouse=True)
def _session_scope():
    set_session_id(_SESSION_ID)
    yield
    clear_session_id()


def _build_lightweight_container(
    service_variant: str, api_style: str, workflow_dir: str
) -> Container:
    """ランナー配線確認専用の軽量コンテナ。外部境界はすべてスタブ。"""
    container = Container()
    stub = providers.Object(SimpleNamespace())
    container.db.override(providers.Object(SimpleNamespace(session=SimpleNamespace())))
    container.config.override(
        providers.Object(
            {
                "db": {"url": "not-used://db"},
                "agent_runtime": {
                    "service_variant": service_variant,
                    "api_style": api_style,
                },
                "workflows": {"dir": workflow_dir},
                "model_list": [
                    {"model": "gpt-4o", "use_for": ["agent"], "model_settings": {}},
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


def test_rollback_api_style_completions_to_responses_wires_responses_runner(tmp_path):
    """api_style=completions → responses へのフリップで ResponsesAgentRunner に戻ることを確認する。

    不変条件:
    - api_style=completions の場合、container.refactored_llm_runner() は CompletionsAgentRunner であること。
    - api_style=responses の場合、container.refactored_llm_runner() は ResponsesAgentRunner であること。

    これにより config-only の rollback でランナーが切り替わることを保証する。
    """
    # Gate B: completions → CompletionsAgentRunner
    container_c = _build_lightweight_container(
        "refactored", "completions", str(tmp_path)
    )
    runner_c = container_c.refactored_llm_runner()
    assert isinstance(runner_c, CompletionsAgentRunner), (
        f"api_style=completions のとき CompletionsAgentRunner が配線されること。実際: {type(runner_c).__name__}"
    )

    # Rollback: responses → ResponsesAgentRunner
    container_r = _build_lightweight_container("refactored", "responses", str(tmp_path))
    runner_r = container_r.refactored_llm_runner()
    assert isinstance(runner_r, ResponsesAgentRunner), (
        f"api_style=responses のとき ResponsesAgentRunner が配線されること。実際: {type(runner_r).__name__}"
    )

    # CompletionsAgentRunner は ResponsesAgentRunner のサブクラスのため、
    # responses style が strict に ResponsesAgentRunner (非 Completions) であることも検証する。
    assert not isinstance(runner_r, CompletionsAgentRunner), (
        "api_style=responses のランナーが CompletionsAgentRunner でないこと"
    )


@pytest.mark.asyncio
async def test_rollback_api_style_completions_chat_service_behavior_matches_responses(
    tmp_path,
):
    """同一の fake イベントで completions と responses の chat() 観測出力が一致することを確認する。

    不変条件: api_style=completions と api_style=responses に同じ LLMRawResponseEvent を注入したとき、
    chat() から yield される (ChatResponseType, message) のシーケンスが完全に一致すること。
    response_type だけでなく MESSAGE 本文まで比較することで、ロールバック時に
    観測可能な振る舞い（本文を含む）が変わらないことを保証する。
    """
    events = [
        LLMRawResponseEvent(item_id="msg-rollback-1", delta="ロールバック"),
    ]

    container_c, _ = build_parity_container("completions", str(tmp_path))
    chat_svc_c = container_c.chat_svc()

    container_r, _ = build_parity_container("responses", str(tmp_path))
    chat_svc_r = container_r.chat_svc()

    async def collect(chat_svc) -> list[tuple[ChatResponseType, str | None]]:
        chat_svc._llm_runner.run_streamed.return_value = _FakeRunStream(events)
        agent_mock = make_agent_mock()
        await _setup_existing_session(chat_svc, agent_mock, _SESSION_ID)
        observed = []
        async for response in chat_svc.chat(
            make_chat_request(message_id="msg-rollback-test"),
            "127.0.0.1",
        ):
            observed.append((response.response_type, response.message))
        return observed

    observed_c = await collect(chat_svc_c)
    observed_r = await collect(chat_svc_r)

    assert observed_c == observed_r, (
        f"completions と responses の (response_type, message) シーケンスが一致すること。"
        f"completions={observed_c}, responses={observed_r}"
    )


def test_rollback_service_variant_refactored_to_legacy_wires_legacy_service(tmp_path):
    """service_variant=refactored → legacy のフリップで legacy ChatService に戻ることを確認する。

    不変条件:
    - service_variant=refactored の場合、container.chat_svc() は services.chat_service_refactored モジュールであること。
    - service_variant=legacy の場合、container.chat_svc() は services.chat_service モジュールであること。

    これにより config-only の rollback でサービス実装が切り替わることを保証する。
    """
    # refactored → refactored ChatService
    container_r = _build_lightweight_container("refactored", "responses", str(tmp_path))
    chat_svc_r = container_r.chat_svc()
    assert chat_svc_r.__class__.__module__ == chat_service_refactored.__name__, (
        f"service_variant=refactored のとき chat_service_refactored が配線されること。"
        f"実際モジュール: {chat_svc_r.__class__.__module__}"
    )

    # Rollback: legacy → legacy ChatService
    # legacy ChatService は全スタブを受け入れるため lightweight container で確認できる。
    container_l = _build_lightweight_container("legacy", "responses", str(tmp_path))
    chat_svc_l = container_l.chat_svc()
    assert chat_svc_l.__class__.__module__ == chat_service.__name__, (
        f"service_variant=legacy のとき chat_service が配線されること。"
        f"実際モジュール: {chat_svc_l.__class__.__module__}"
    )
