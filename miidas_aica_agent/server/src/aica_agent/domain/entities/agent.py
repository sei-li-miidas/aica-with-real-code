from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.orm import Mapped, relationship

from database import Base

from .agent_tool import AgentTool
from .workflow import Workflow


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String)
    description = Column(String)
    default_agent = Column(Boolean)
    can_search_position = Column(Boolean)
    deleted_at = Column(DateTime, nullable=True)

    tools: Mapped[list[AgentTool]] = relationship(
        primaryjoin="and_(Agent.id == AgentTool.agent_id, AgentTool.deleted_at.is_(None))"
    )
    next_agents: Mapped[list[Workflow]] = relationship(
        primaryjoin="and_(Agent.id == Workflow.src_agent_id, Workflow.deleted_at.is_(None))"
    )
