""" Defines the TodoerInfo pydantic models. """

from pydantic import BaseModel


class TodoerInfo(BaseModel):
    timestamp: str
    service: str
    data_source: str
    version: str
