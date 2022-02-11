from pydantic import BaseModel, ConstrainedStr  # HttpUrl, constr
from typing import List, Optional, Sequence  # Dict,
import datetime as dt

from sqlalchemy.sql.base import NO_ARG


class SmlStr(ConstrainedStr):
    min_length = 1
    max_length = 64


class MidStr(ConstrainedStr):
    min_length = 1
    max_length = 256


class LongStr(ConstrainedStr):
    min_length = 1
    max_length = 1024


class TodoerInfo(BaseModel):
    timestamp: str
    service: str
    data_source: str
    version: str
    api_version: str


class APIResponse(BaseModel):
    status: str
    description: Optional[str] = None
    errors: Optional[List[str]] = None


class TaskBase(BaseModel):
    # _id: Optional[str] = None
    # TODO-low project to become a id and relation
    # TODO-low tags: List[SmlStr]
    project: SmlStr
    summary: MidStr
    description: Optional[LongStr] = None
    status: SmlStr
    assignee_id: Optional[int] = None
    tags: Optional[MidStr] = None


class TaskCreate(TaskBase):
    """For creation of a task == TaskBase + submitter_id."""

    pass  # create == base


class TaskUpdate(TaskBase):
    """Things can modify in a task === TaskBase - project."""

    pass  # for now can update == base (including project)


# Properties shared by models stored in DB
class TaskInDBBase(TaskBase):
    id: int
    created: dt.datetime
    updated: dt.datetime

    class Config:
        orm_mode = True


# Properties to return to client
class Task(TaskInDBBase):
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "project": "HOME",
                "summary": "Example do laundry",
                "description": "Wash dry and fold them",
                "status": "WIP",
                "assignee_id": 1,
                "tags": "domestic, high",
                "created": "2022-02-06T09:18:29.345605",
                "updated": "2022-02-06T09:18:29.345605",
            }
        }


# Properties properties stored in DB
class TaskInDB(TaskInDBBase):
    pass


class TaskSearchResults(BaseModel):
    results: Sequence[Task]
