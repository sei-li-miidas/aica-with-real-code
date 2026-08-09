from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)

from database import Base


class ChatSummaryStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ChatSummary(Base):
    __tablename__ = "chat_summaries"

    summary_id = Column(BigInteger, primary_key=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False)
    summary_text = Column(Text, nullable=True)
    summary_until_history_id = Column(BigInteger, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed')",
            name="chat_summaries_status_check",
        ),
    )
