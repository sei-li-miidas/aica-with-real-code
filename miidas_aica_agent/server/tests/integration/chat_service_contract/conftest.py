"""チャットサービスコントラクトテスト用フィクスチャ。"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from dependency_injector import providers

from containers import Container
from domain.entities.chat_session import ChatSessionStatus
from services.conversation_summary_service import ConversationSummaryService
from repositories.api_repo import AICAAPIRepository
from repositories.chat_repo import ChatRepository
from repositories.position_repo import PositionRepository
from repositories.rate_limit_repo import BaseRateLimitRepository
from repositories.user_repo import UserRepository
from repositories.workflow_definition_repo import WorkflowDefinitionRepository
from repositories.summary_repo import SummaryRepository
from repositories.workflow_repo import WorkflowRepository
from .chat_service_contract_helpers import (
    _FakeRunStream,
    _attach_run_with_retry_passthrough,
)
from services import chat_service, chat_service_refactored
from services.position_service import PositionService
from services.rate_limit_service import RateLimitService
from services.summary_service import SummaryService
from services.workflow_service import WorkflowService


def _resolve_variant(request: pytest.FixtureRequest, fixture_name: str) -> str:
    """variant を request.param → callspec.params → fail の順で解決する。

    - indirect parametrization: request.param で取得済み。
    - direct @pytest.mark.parametrize("variant", ...): callspec.params["variant"] で取得する。
      getfixturevalue("variant") はテストパラメータをフィクスチャとして解決しようとするため
      pytest バージョンにより FixtureLookupError を起こすか誤った値を返す可能性がある。
    """
    variant = getattr(request, "param", None)
    if variant is None:
        callspec = getattr(request.node, "callspec", None)
        if callspec is not None:
            variant = callspec.params.get("variant")
    if variant is None:
        pytest.fail(
            f"{fixture_name} requires either indirect parametrization "
            "or @pytest.mark.parametrize('variant', ...) on the test function."
        )
    return variant


def _build_variant_container(service_variant: str, workflow_dir: str) -> Container:
    container = Container()
    stub = providers.Object(SimpleNamespace())

    # Mock(spec=ChatRepository) を使用する。MagicMock ではなく Mock を選ぶ理由は、
    # spec により存在しないメソッドへのアクセスで AttributeError が発生し、
    # テストが誤って存在しない呼び出しを見逃さないようにするため。
    # return_value の設定と call_args の検査は
    # chat_svc._chat_repository.<method>.return_value 経由で行う。
    chat_repository = Mock(spec=ChatRepository)
    chat_repository.init_chat_session.return_value = (None, False)
    chat_repository.session_status.return_value = ChatSessionStatus.CHATTING
    chat_repository.is_session_blocked.return_value = False
    chat_repository.get_main_chat_histories.return_value = []
    chat_repository.get_main_chat_histories_after_by_session.return_value = []
    chat_repository.count_user_messages_by_session.return_value = 0

    # MCP サーバー初期化をトリガーせずに clone_agents() を設定できるよう
    # llm_svc に MagicMock を使用する。
    llm_svc = MagicMock()
    llm_svc.clone_agents.return_value = {}

    # insert() が無音で呼び出せるよう action_log_repository に MagicMock を使用する。
    action_log_repository = MagicMock()

    # モック方針: PositionService はリアルインスタンスを使い、リポジトリ層のみモックする。
    # aica_api_repository.get を AsyncMock(return_value=(None, None)) にして
    # current_search_filter() が None を返すようにする。
    # これにより init_session() の try/except が正常パスを通り、clone_agents() が確定して呼ばれる。
    aica_api_repository = MagicMock(spec=AICAAPIRepository)
    aica_api_repository.get = AsyncMock(return_value=(None, None))
    position_svc = PositionService(
        position_repository=Mock(spec=PositionRepository),
        aica_api_repository=aica_api_repository,
        chat_repository=chat_repository,
        user_repository=Mock(spec=UserRepository),
        action_log_repository=action_log_repository,
    )

    container.db.override(providers.Object(SimpleNamespace(session=SimpleNamespace())))
    container.config.override(
        providers.Object(
            {
                "db": {"url": "not-used://db"},
                "agent_runtime": {"service_variant": service_variant},
                "workflows": {"dir": workflow_dir},
                "model_list": [
                    {
                        "model": "gpt-4o",
                        "use_for": ["agent"],
                        "model_settings": {},
                    },
                    {
                        "model": "gpt-4o-mini",
                        "use_for": ["summary"],
                        "model_settings": {},
                    },
                ],
            }
        )
    )
    container.position_svc.override(providers.Object(position_svc))
    container.llm_svc.override(providers.Object(llm_svc))
    # モック方針: WorkflowService はリアルインスタンスを使い、リポジトリ層のみモックする。
    # workflow_definition_repository は tests からアクセス可能なようモックを保持しておく。
    workflow_definition_repository = Mock(spec=WorkflowDefinitionRepository)
    workflow_svc = WorkflowService(
        aica_api_repository=Mock(spec=AICAAPIRepository),
        workflow_repository=Mock(spec=WorkflowRepository),
        workflow_definition_repository=workflow_definition_repository,
        position_change_analyze_summary_svc=Mock(),
    )
    container.workflow_svc.override(providers.Object(workflow_svc))
    container.chat_repository.override(providers.Object(chat_repository))
    container.position_repository.override(stub)
    container.user_repository.override(stub)
    container.action_log_repository.override(providers.Object(action_log_repository))
    # モック方針: RateLimitService はリアルインスタンスを使い、リポジトリ層のみモックする。
    # rate_limit config を空にすることで全チェックが即 True を返す（ルール未設定時の動作）。
    rate_limit_svc = RateLimitService(
        rate_limit_repository=Mock(spec=BaseRateLimitRepository),
        rate_limit={
            "chat_request": {},
            "position_detail": {},
            "position_search": {},
            "load_more_positions": {},
        },
    )
    container.rate_limit_svc.override(providers.Object(rate_limit_svc))
    with patch("services.conversation_summary_service.AsyncOpenAI"):
        conversation_summary_svc = ConversationSummaryService(
            model_list=[
                {"model": "gpt-4o-mini", "use_for": ["summary"], "model_settings": {}}
            ]
        )
    conversation_summary_svc._openai_client = SimpleNamespace(
        responses=SimpleNamespace(create=AsyncMock())
    )
    container.conversation_summary_svc.override(
        providers.Object(conversation_summary_svc)
    )
    summary_repository = Mock(spec=SummaryRepository)
    summary_repository.get_latest_completed.return_value = None
    summary_svc = SummaryService(
        summary_repository=summary_repository,
        chat_repository=chat_repository,
        conversation_summary_service=conversation_summary_svc,
    )
    container.summary_svc.override(providers.Object(summary_svc))
    # refactored_llm_runner は ResponsesAgentRunner（実 OpenAI SDK）を呼ぶため、
    # テストで呼ばれないよう run_streamed/run_with_retry 双方を備えた mock で上書きする。
    # 特定のストリームイベントが必要なテストは個別に chat_svc._llm_runner.run_streamed
    # を差し替える。
    mock_llm_runner = MagicMock()
    mock_llm_runner.run_streamed.return_value = _FakeRunStream([])
    _attach_run_with_retry_passthrough(
        mock_llm_runner,
        action_log_repository=action_log_repository,
    )
    container.refactored_llm_runner.override(providers.Object(mock_llm_runner))
    return container


@pytest.fixture(scope="function")
def chat_service_container(request, tmp_path):
    """legacy / real-refactored 特性化テスト用のチャットサービスを解決する。"""
    variant = _resolve_variant(request, "chat_service_container")

    if variant == "legacy":
        service_variant = "legacy"
        expected_module = chat_service.__name__
    elif variant == "real-refactored":
        service_variant = "refactored"
        expected_module = chat_service_refactored.__name__
    else:
        pytest.fail(f"Unsupported chat service test variant: {variant}")

    container = _build_variant_container(service_variant, str(tmp_path))
    chat_svc = container.chat_svc()

    # false-green なバリアント特性化を避けるためフィクスチャ配線をアサートする。
    assert chat_svc.__class__.__module__ == expected_module
    return chat_svc


@pytest.fixture(scope="function")
def chat_service_container_history_parity(request, tmp_path):
    """history mapping parity テスト専用: legacy / real-refactored を解決する。

    Phase 4 task-2-history-mapper により real-refactored evidence が確立した後、
    history mapping の 2 variant テストを実行するために使用する。
    """
    variant = _resolve_variant(request, "chat_service_container_history_parity")

    if variant == "legacy":
        service_variant = "legacy"
        expected_module = chat_service.__name__
    elif variant == "real-refactored":
        service_variant = "refactored"
        expected_module = chat_service_refactored.__name__
    else:
        pytest.fail(f"Unsupported chat service test variant: {variant}")

    container = _build_variant_container(service_variant, str(tmp_path))
    chat_svc = container.chat_svc()

    assert chat_svc.__class__.__module__ == expected_module
    return chat_svc


@pytest.fixture(scope="function")
def real_refactored_chat_service_container(tmp_path):
    """Phase 4 bootstrap 用に real-refactored variant を明示的に解決する。"""
    container = _build_variant_container("refactored", str(tmp_path))
    chat_svc = container.chat_svc()

    assert chat_svc.__class__.__module__ == chat_service_refactored.__name__
    return chat_svc


@pytest.fixture(scope="function")
def real_refactored_setup(tmp_path):
    """Phase 4 behavioral proof 用に real-refactored variant と依存 mock を返す。

    container の provider 経由で llm_svc / chat_repository を公開する。
    """
    container = _build_variant_container("refactored", str(tmp_path))
    chat_svc = container.chat_svc()
    assert chat_svc.__class__.__module__ == chat_service_refactored.__name__
    return SimpleNamespace(
        chat_svc=chat_svc,
        llm_svc=container.llm_svc(),
        chat_repository=container.chat_repository(),
    )


@pytest.fixture(scope="function")
def chat_service_container_tool_results(request, tmp_path):
    """Tool result response shape テスト専用: legacy / real-refactored を解決する。

    Phase 4 task-2-tool-event-handler で real-refactored evidence が確立した後、
    tool result response shape の 2 variant テストを実行するために使用する。
    """
    variant = _resolve_variant(request, "chat_service_container_tool_results")

    if variant == "legacy":
        service_variant = "legacy"
        expected_module = chat_service.__name__
    elif variant == "real-refactored":
        service_variant = "refactored"
        expected_module = chat_service_refactored.__name__
    else:
        pytest.fail(f"Unsupported chat service test variant: {variant}")

    container = _build_variant_container(service_variant, str(tmp_path))
    chat_svc = container.chat_svc()
    assert chat_svc.__class__.__module__ == expected_module
    return chat_svc


@pytest.fixture(scope="function")
def chat_service_container_db_side_effects(request, tmp_path):
    """DB 副作用テスト専用: legacy / real-refactored を解決する。

    Phase 4 task-1-chat-persistence で real-refactored evidence が確立した後、
    DB 副作用の 2 variant テストを実行するために使用する。
    """
    variant = _resolve_variant(request, "chat_service_container_db_side_effects")

    if variant == "legacy":
        service_variant = "legacy"
        expected_module = chat_service.__name__
    elif variant == "real-refactored":
        service_variant = "refactored"
        expected_module = chat_service_refactored.__name__
    else:
        pytest.fail(f"Unsupported chat service test variant: {variant}")

    container = _build_variant_container(service_variant, str(tmp_path))
    chat_svc = container.chat_svc()
    assert chat_svc.__class__.__module__ == expected_module
    return chat_svc


@pytest.fixture(scope="function")
def chat_service_container_security(request, tmp_path):
    """セキュリティクリーンアップテスト専用: legacy / real-refactored を解決する。

    Phase 4 task-3-stream-guard-security で real-refactored evidence が確立した後、
    セキュリティブロック・クリーンアップの 2 variant テストを実行するために使用する。
    """
    variant = _resolve_variant(request, "chat_service_container_security")

    if variant == "legacy":
        service_variant = "legacy"
        expected_module = chat_service.__name__
    elif variant == "real-refactored":
        service_variant = "refactored"
        expected_module = chat_service_refactored.__name__
    else:
        pytest.fail(f"Unsupported chat service test variant: {variant}")

    container = _build_variant_container(service_variant, str(tmp_path))
    chat_svc = container.chat_svc()
    assert chat_svc.__class__.__module__ == expected_module
    return chat_svc


@pytest.fixture(scope="function")
def chat_service_container_workflow(request, tmp_path):
    """ワークフロー副作用テスト専用: legacy / real-refactored を解決する。

    Phase 4 task-4-workflow-chat-handler で real-refactored evidence が確立した後、
    ワークフロー副作用の 2 variant テストを実行するために使用する。
    """
    variant = _resolve_variant(request, "chat_service_container_workflow")

    if variant == "legacy":
        service_variant = "legacy"
        expected_module = chat_service.__name__
    elif variant == "real-refactored":
        service_variant = "refactored"
        expected_module = chat_service_refactored.__name__
    else:
        pytest.fail(f"Unsupported chat service test variant: {variant}")

    container = _build_variant_container(service_variant, str(tmp_path))
    chat_svc = container.chat_svc()
    assert chat_svc.__class__.__module__ == expected_module
    return chat_svc
