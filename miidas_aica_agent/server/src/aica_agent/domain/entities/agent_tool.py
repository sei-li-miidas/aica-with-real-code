from sqlalchemy import Boolean, Column, ForeignKey, Integer, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class AgentTool(Base):
    __tablename__ = "agent_tools"

    id = Column(Integer, primary_key=True, autoincrement=False)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"))
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    return_direct = Column(Boolean)
    deleted_at = Column(DateTime, nullable=True)
