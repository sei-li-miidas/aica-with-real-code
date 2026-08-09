"""
Integration tests for AgentService — targeting 100% branch coverage.

Tests call the real service with mocked repositories.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from repositories.agent_repo import AgentRepository
from repositories.prompt_repo import PromptRepository
from services.agent_service import AgentService

pytestmark = pytest.mark.pre_extraction_parity


def _make_agent(agent_id: int, name: str, tools=None, next_agents=None):
    agent = SimpleNamespace(
        id=agent_id,
        name=name,
        tools=tools or [],
        next_agents=next_agents or [],
        default_agent=True,
        can_search_position=False,
        deleted_at=None,
    )
    return agent


def _make_svc_with_mocks(agents, prompts_dir: str) -> AgentService:
    agent_repo = Mock(spec=AgentRepository)
    agent_repo.get_agents.return_value = agents

    prompt_repo = PromptRepository(prompts_dir)

    return AgentService(
        agent_repository=agent_repo,
        prompt_repository=prompt_repo,
    )


def test_get_agents_with_prompts_returns_list_of_tuples(tmp_path):
    agent = _make_agent(2, "CareerAdvisor")

    prompt_file = tmp_path / "2_CareerAdvisor.txt"
    prompt_file.write_text("You are a helpful agent.", encoding="utf-8")

    svc = _make_svc_with_mocks([agent], str(tmp_path))
    result = svc.get_agents_with_prompts()

    assert len(result) == 1
    returned_agent, prompt = result[0]
    assert returned_agent is agent
    assert prompt == "You are a helpful agent."


def test_get_agents_with_prompts_multiple_agents(tmp_path):
    agents = [
        _make_agent(1, "AgentOne"),
        _make_agent(2, "AgentTwo"),
    ]

    (tmp_path / "1_AgentOne.txt").write_text("Prompt one", encoding="utf-8")
    (tmp_path / "2_AgentTwo.txt").write_text("Prompt two", encoding="utf-8")

    svc = _make_svc_with_mocks(agents, str(tmp_path))
    result = svc.get_agents_with_prompts()

    assert len(result) == 2
    names = [a.name for a, _ in result]
    assert "AgentOne" in names
    assert "AgentTwo" in names


def test_get_agents_with_prompts_raises_when_prompt_file_missing(tmp_path):
    agent = _make_agent(1, "AgentWithNoFile")

    svc = _make_svc_with_mocks([agent], str(tmp_path))

    with pytest.raises(FileNotFoundError):
        svc.get_agents_with_prompts()


def test_get_agents_with_prompts_empty_agent_list(tmp_path):
    svc = _make_svc_with_mocks([], str(tmp_path))
    result = svc.get_agents_with_prompts()
    assert result == []
