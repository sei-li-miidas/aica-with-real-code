from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.session_id"))
    position_id = Column(Integer, nullable=True)
    active_agent = Column(String)
    message_id = Column(String)
    role = Column(String)
    content = Column(String)
    tool_call_id = Column(String, nullable=True)
    tool_name = Column(String, nullable=True)
    tool_input = Column(JSONB, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_voice = Column(Boolean, nullable=True)
