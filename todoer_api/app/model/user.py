""" Defines the pydantic models. """

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from .base import MongoBaseModel


class UserBase(BaseModel):
    username: str
    email: EmailStr
    organisation: str
    status: str
    projects: List[str] = Field(default_factory=list)


class UserPartialUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    organisation: Optional[str] = None
    status: Optional[str] = None
    projects: Optional[List[str]] = None


class UserUpdate(UserBase):
    pass


class UserCreate(UserBase):
    project: str


class UserDB(UserCreate, MongoBaseModel):
    created: datetime = Field(default_factory=datetime.now)
    updated: datetime = Field(default_factory=datetime.now)


class User(UserDB):
    pass
