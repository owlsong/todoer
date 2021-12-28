from typing import List, Optional  # Dict,
from pydantic import BaseModel
import datetime as dt


class TodoerInfo(BaseModel):
    timestamp: str
    service: str
    data_source: str
    version: str


class Task(BaseModel):
    _id: Optional[str] = None
    id: int
    owner: str
    project: str
    summary: str
    description: Optional[str] = ""
    status: str
    # assignee: str
    created: Optional[dt.datetime] = None
    updated: Optional[dt.datetime] = None
    tags: List[str] = []
    # model_parameters: dict = {}
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "owner": "anne",
                "project": "HOME",
                "summary": "Example do laundry",
                "description": "Wask dry and fold them",
                "status": "WIP",
                "created": dt.datetime(2020, 5, 23, 7, 53, 34, 305),
                "tags": [],
            }
        }

    def body(self, include_id=False):
        """Return a dict representing the JSON that is REST friendly."""
        # currently just exclude datetime fields
        exclude_fields = ["created", "updated"]
        if not include_id:
            exclude_fields.append("id")
        json_dict = self.dict()
        return {
            key: value
            for (key, value) in json_dict.items()
            if key not in exclude_fields
        }


class APIResponse(BaseModel):
    status: str
    description: Optional[str] = None
    errors: Optional[List[str]] = None
