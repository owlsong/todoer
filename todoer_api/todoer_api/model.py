from typing import List, Optional  # Dict,
from pydantic import BaseModel
import datetime as dt


class TodoerInfo(BaseModel):
    timestamp: str
    service = "Todoer"
    version = "0.1.0"


class Task(BaseModel):
    id: int
    summary: str
    description: str
    status: str
    # assignee: str
    created: Optional[dt.datetime] = None
    tags: List[str] = []
    # model_parameters: dict = {}
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "summary": "Example do laundry",
                "description": "Wask dry and fold them",
                "status": "WIP",
                "created": dt.datetime(2020, 5, 23, 7, 53, 34, 305),
                "tags": [],
            }
        }


class APIResponse(BaseModel):
    status: str
    description: Optional[str] = None
    errors: Optional[List[str]] = None
