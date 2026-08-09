from contextlib import contextmanager
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from domain.entities.agent import Agent
from domain.entities.agent_tool import AgentTool
from domain.entities.workflow import Workflow
from repositories.agent_repo import AgentRepository
from utils.log_utils import clear_session_id, set_session_id


@pytest.fixture(autouse=True)
def session_scope():
    """全テストでセッションIDをセットアップする。"""
    set_session_id("test-session-id")
    yield
    clear_session_id()


@pytest.fixture
def repository():
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(
            bind=engine,
            tables=[Agent.__table__, AgentTool.__table__, Workflow.__table__],
        )
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        @contextmanager
        def db_session():
            session = session_factory()
            try:
                yield session
                session.commit()
            finally:
                session.close()

        yield AgentRepository(session_factory=db_session), db_session
    finally:
        engine.dispose()


def test_get_agents_excludes_soft_deleted_related_records(repository):
    repo, db_session = repository
    deleted_at = datetime(2026, 3, 16, 12, 0, 0)

    with db_session() as session:
        session.add_all(
            [
                Agent(
                    id=1,
                    name="Agent1",
                    description="active source",
                    default_agent=True,
                    deleted_at=None,
                ),
                Agent(
                    id=2,
                    name="Agent2",
                    description="active destination",
                    default_agent=False,
                    deleted_at=None,
                ),
                Agent(
                    id=3,
                    name="DeletedAgent",
                    description="deleted destination",
                    default_agent=False,
                    deleted_at=deleted_at,
                ),
            ]
        )
        session.add_all(
            [
                AgentTool(
                    id=10,
                    agent_id=1,
                    tool_name="active_tool",
                    return_direct=False,
                    deleted_at=None,
                ),
                AgentTool(
                    id=11,
                    agent_id=1,
                    tool_name="deleted_tool",
                    return_direct=False,
                    deleted_at=deleted_at,
                ),
            ]
        )
        session.add_all(
            [
                Workflow(
                    id=20,
                    src_agent_id=1,
                    dest_agent_id=2,
                    description="active handoff",
                    deleted_at=None,
                ),
                Workflow(
                    id=21,
                    src_agent_id=1,
                    dest_agent_id=2,
                    description="deleted handoff",
                    deleted_at=deleted_at,
                ),
                Workflow(
                    id=22,
                    src_agent_id=1,
                    dest_agent_id=3,
                    description="handoff to deleted agent",
                    deleted_at=None,
                ),
            ]
        )

    agents = repo.get_agents()

    assert [agent.name for agent in agents] == ["Agent1", "Agent2"]

    agent1 = next(agent for agent in agents if agent.name == "Agent1")
    assert [tool.tool_name for tool in agent1.tools] == ["active_tool"]
    assert len(agent1.next_agents) == 1
    assert agent1.next_agents[0].dest_agent.name == "Agent2"
