"""
Legacy dependency 再導入防止テスト。

Real refactored 実装が使用中であることを検証:
- chat_service_refactored.ChatService.chat() が LLMRunner.run_streamed() に到達
- Phase 2 delegating adapter へのロールバックはテスト失敗を引き起こす
- Real 実装が使用中であることの振る舞い証明

マーカー:
- pre_extraction_bootstrap: Phase 4 bootstrap 用マーカー
- pre_extraction_parity: Pre-extraction parity matrix の一部

注記: このテストは Phase 4 bootstrap 振る舞い証明に重要。
Phase 3 task-2 が legacy characterization を作成。
Phase 4 bootstrap task が real-refactored 実行証拠を追加。

テストケース一覧:
- test_real_refactored_reaches_llm_runner
    対象: real-refactored の chat() 実行が LLMRunner.run_streamed へ
    到達すること。
- test_real_refactored_vs_delegating_adapter_difference
    対象: delegating adapter 経路との差分が残り、
    互換委譲へ戻していないことを示すこと。
- test_real_refactored_execution_identity
    対象: 実行 identity が real-refactored として記録されること。
- test_chat_service_refactored_has_no_delegate_chat_path
    対象: refactored 実装ソースに delegate_chat 経路が存在しないこと。
"""

from unittest.mock import MagicMock, create_autospec

import pytest

from .chat_service_contract_helpers import _attach_run_with_retry_passthrough
from services.chat.llm_runner import LLMRunner
from utils.chat_request import ChatRequestModel, ChatRequestType
from utils.enum import PageName
from utils.log_utils import clear_session_id, set_session_id


pytestmark = [pytest.mark.pre_extraction_bootstrap, pytest.mark.pre_extraction_parity]

_SESSION_ID = "phase4-bootstrap-behavioral-proof"


@pytest.fixture(autouse=True)
def set_test_session_id():
    set_session_id(_SESSION_ID)
    yield
    clear_session_id()


class _FakeRunStream:
    """Behavioral proof 用の最小 run stream fake。"""

    def __init__(self):
        self.continuation_state = None
        self.agent_state = None
        self.replay_items = []
        self.usage = None

    async def stream_events(self):
        return
        yield  # noqa: unreachable - makes this an async generator

    async def aclose(self):
        pass


def _make_request() -> ChatRequestModel:
    return ChatRequestModel(
        request_type=ChatRequestType.CHAT,
        current_page=PageName.CHAT,
        position_id=None,
        message="テスト",
        current_message_id="msg-behavioral-proof",
    )


async def _init_chat_session(setup, monkeypatch) -> None:
    """Behavioral proof テスト用のセッション初期化。

    container の public provider 経由で llm_svc mock を設定する。
    """
    monkeypatch.setattr(
        "services.chat_service_refactored.is_local_or_dev", lambda: False
    )
    default_agent = MagicMock()
    default_agent.name = "CareerAdvisor"
    default_agent.tool_use_behavior = {}
    setup.llm_svc.clone_agents.return_value = {"CareerAdvisor": (default_agent, True)}
    await setup.chat_svc.init_session("gpt-4o")


@pytest.mark.asyncio
async def test_real_refactored_reaches_llm_runner(
    real_refactored_setup,
    monkeypatch,
):
    """Real refactored 実装が LLMRunner.run_streamed() に到達することを証明する。

    implementation_identity=real-refactored
    """
    await _init_chat_session(real_refactored_setup, monkeypatch)
    chat_svc = real_refactored_setup.chat_svc

    chat_svc._llm_runner = create_autospec(LLMRunner, instance=True)
    chat_svc._llm_runner.run_streamed.return_value = _FakeRunStream()
    _attach_run_with_retry_passthrough(chat_svc._llm_runner)

    async for _ in chat_svc.chat(_make_request(), "127.0.0.1"):
        pass

    assert chat_svc._llm_runner.run_streamed.call_count == 1, (
        f"implementation_identity=real-refactored: "
        f"LLMRunner.run_streamed() expected 1 call, got {chat_svc._llm_runner.run_streamed.call_count}"
    )


@pytest.mark.asyncio
async def test_real_refactored_vs_delegating_adapter_difference(
    real_refactored_setup,
    monkeypatch,
):
    """task-5 以降: delegating adapter は削除済み。_delegate_chat が存在しないことを証明する。

    task-5-legacy-dependency-removal により _delegate_chat フラグと
    if self._delegate_chat: ブロックは完全に削除された。
    このテストはその静的・実行時の両面を検証する再導入防止ガード。
    implementation_identity=real-refactored (post-task-5 verification)
    """
    await _init_chat_session(real_refactored_setup, monkeypatch)
    chat_svc = real_refactored_setup.chat_svc

    # _delegate_chat 属性が存在しないことを証明する（task-5 で削除済み）。
    assert not hasattr(chat_svc, "_delegate_chat"), (
        "implementation_identity: _delegate_chat must not exist after task-5 removal"
    )

    chat_svc._llm_runner = create_autospec(LLMRunner, instance=True)
    chat_svc._llm_runner.run_streamed.return_value = _FakeRunStream()
    _attach_run_with_retry_passthrough(chat_svc._llm_runner)

    async for _ in chat_svc.chat(_make_request(), "127.0.0.1"):
        pass

    # Real-refactored は常に _llm_runner.run_streamed() に到達する（委譲パスなし）。
    assert chat_svc._llm_runner.run_streamed.call_count == 1, (
        f"implementation_identity=real-refactored: "
        f"LLMRunner.run_streamed() expected 1 call, got {chat_svc._llm_runner.run_streamed.call_count}"
    )


@pytest.mark.asyncio
async def test_real_refactored_execution_identity(
    real_refactored_chat_service_container,
):
    """実行 identity が real-refactored であり legacy ではないことを証明する。

    implementation_identity=real-refactored
    """
    chat_svc = real_refactored_chat_service_container

    assert chat_svc.__class__.__module__ == "services.chat_service_refactored", (
        f"implementation_identity: expected services.chat_service_refactored, "
        f"got {chat_svc.__class__.__module__}"
    )
    assert not hasattr(chat_svc, "_delegate_chat"), (
        "implementation_identity=real-refactored: _delegate_chat must not exist (task-5 removed it)"
    )
    assert chat_svc._llm_runner is not None, (
        "implementation_identity=real-refactored: _llm_runner must be injected"
    )


def test_chat_service_refactored_has_no_delegate_chat_path():
    """chat_service_refactored.py が legacy chat() 委譲コードを含まないことを静的に検証する。

    task-5-legacy-dependency-removal の再導入防止ガード。
    """
    import inspect
    import services.chat_service_refactored as module

    full_source = inspect.getsource(module)
    assert "_legacy_chat_service.chat(" not in full_source, (
        "chat_service_refactored.py contains '_legacy_chat_service.chat(' call. "
        "LegacyChatService.chat() delegation must not exist (task-5 removed it)."
    )
    assert "_delegate_chat" not in full_source, (
        "chat_service_refactored.py contains '_delegate_chat'. "
        "This delegation flag was removed in task-5."
    )
