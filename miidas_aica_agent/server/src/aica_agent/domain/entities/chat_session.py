from datetime import datetime
from enum import IntEnum
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, relationship

from database import Base

from .chat_history import ChatHistory
from .user_profile import UserProfile


class ChatSessionStatus(IntEnum):
    # エラー
    ERROR = -1
    # 会話中
    CHATTING = 10
    # 会員登録中
    REGISTERING = 100
    # 面談応募中
    APPLYING = 110
    # 会員登録済み
    REGISTERED = 200
    # 面談応募済み
    APPLIED = 210


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True)
    summary = Column(String, nullable=True)
    status = Column(Integer, default=ChatSessionStatus.CHATTING)
    miidas_user_id = Column(Integer, nullable=True)
    is_blocked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    deleted_at = Column(DateTime, nullable=True)

    histories: Mapped[list[ChatHistory]] = relationship(
        primaryjoin="ChatSession.session_id == ChatHistory.session_id"
    )
    user_profile: Mapped[UserProfile] = relationship(
        primaryjoin="ChatSession.session_id == UserProfile.session_id"
    )
