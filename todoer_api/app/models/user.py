from sqlalchemy import Integer, String, Column, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(256), nullable=False)
    surname = Column(String(256), nullable=True)
    email = Column(String, index=True, nullable=False)
    is_superuser = Column(Boolean, default=False)
    assigned_tasks = relationship(
        "Task",
        cascade="all,delete-orphan",
        back_populates="assignee",
        uselist=True,
    )
    # admin fields (does not use inheritance)
    created = Column(DateTime, nullable=False)
    updated = Column(DateTime, nullable=False)
