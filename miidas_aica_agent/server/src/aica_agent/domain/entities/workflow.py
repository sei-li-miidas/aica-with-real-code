from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, relationship, mapped_column
from database import Base

if TYPE_CHECKING:
    from aica_agent.domain.entities.agent import Agent


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, autoincrement=False)
    src_agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    dest_agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    description = Column(String)
    deleted_at = Column(DateTime, nullable=True)

    # 循環参照になるので、TYPE_CHECKINGでインポートする
    dest_agent: Mapped[Agent] = relationship(
        primaryjoin="and_(Workflow.dest_agent_id == Agent.id, Agent.deleted_at.is_(None))"
    )
