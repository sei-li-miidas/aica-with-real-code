from sqlalchemy import Column, Integer, String
from database import Base


class JobTypeSmall(Base):
    __tablename__ = "job_type_small"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
