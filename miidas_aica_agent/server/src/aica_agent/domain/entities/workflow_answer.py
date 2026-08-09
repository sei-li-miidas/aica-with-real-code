from sqlalchemy import Column, String, JSON
from database import Base


class WorkflowAnswer(Base):
    __tablename__ = "workflow_answers"

    session_id = Column(String(255), primary_key=True)
    workflow_id = Column(String(255), primary_key=True)
    answers = Column(JSON, nullable=False)
