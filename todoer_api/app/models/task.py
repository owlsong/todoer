from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# from sqlalchemy.dialects.postgresql import ARRAY
# from sqlalchemy.sql.sqltypes import DateTime


class Task(Base):
    id = Column(Integer, primary_key=True, index=True)
    project = Column(String(256), nullable=False)
    summary = Column(String(256), nullable=False)
    description = Column(String(256), nullable=True)
    status = Column(String(256), nullable=False)

    # list of tags is comma separated for now
    tags = Column(String(256), nullable=True)
    # tags = Column(ARRAY(String(255)))
    assignee_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    assignee = relationship("User", back_populates="assigned_tasks")

    # admin fields (does not use inheritance)
    created = Column(DateTime, nullable=False)
    updated = Column(DateTime, nullable=False)
