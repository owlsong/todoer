""" Defines the pydantic models. """

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .base import MongoBaseModel


def _get_task_key(project: str, seq: int) -> str:
    return f"{project.upper()}-{seq}"


class TaskBase(BaseModel):
    summary: str
    description: str
    status: str
    # assignee: str
    tags: List[str] = Field(default_factory=list)

    def get_dict_inc_seq(self, seq: int) -> dict:
        vals = self.dict()
        vals["seq"] = seq
        vals["key"] = _get_task_key(self.project, seq)
        return vals


class TaskPartialUpdate(TaskBase):
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class TaskUpdate(TaskBase):
    pass


class TaskCreate(TaskBase):
    project: str


class TaskDB(TaskCreate, MongoBaseModel):
    def get_task_key(self):
        return _get_task_key(self.project, self.seq)

    seq: int
    key: str
    created: datetime = Field(default_factory=datetime.now)
    updated: datetime = Field(default_factory=datetime.now)


class Task(TaskDB):
    pass
