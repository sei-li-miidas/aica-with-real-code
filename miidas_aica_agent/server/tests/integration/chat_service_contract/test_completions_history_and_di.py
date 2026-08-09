from __future__ import annotations

from types import SimpleNamespace

import pytest
from dependency_injector import providers

from containers import Container
from services.chat.chat_persistence import ChatPersistence
from services.chat.history_mapper import HistoryMapper
from services.chat.llm_runner import CompletionsAgentRunner, ResponsesAgentRunner
from services.chat.turn_preparer import TurnPreparer


pytestmark = pytest.mark.completions_contract


def _build_container(api_style: str, workflow_dir: str) -> Container:
    container = Container()
    stub = providers.Object(SimpleNamespace())

    container.db.override(providers.Object(SimpleNamespace(session=SimpleNamespace())))
    container.config.override(
        providers.Object(
            {
                "db": {"url": "not-used://db"},
                "agent_runtime": {
                    "service_variant": "refactored",
                    "api_style": api_style,
                },
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


@pytest.mark.parametrize(
    ("api_style", "runner_cls"),
    [
        ("responses", ResponsesAgentRunner),
        ("completions", CompletionsAgentRunner),
    ],
)
def test_container_injects_runner_by_api_style(api_style, runner_cls, tmp_path):
    container = _build_container(api_style, str(tmp_path))

    runner = container.refactored_llm_runner()

    assert isinstance(runner, runner_cls)


@pytest.mark.parametrize("api_style", ["responses", "completions"])
def test_refactored_history_and_persistence_components_remain_style_agnostic(
    api_style,
    tmp_path,
):
    container = _build_container(api_style, str(tmp_path))

    chat_svc = container.chat_svc()

    assert isinstance(chat_svc._history_mapper, HistoryMapper)
    assert isinstance(chat_svc._chat_persistence, ChatPersistence)
    assert isinstance(chat_svc._turn_preparer, TurnPreparer)
