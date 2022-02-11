from typing import Optional
from pydantic import BaseModel, EmailStr
import datetime as dt


class UserBase(BaseModel):
    first_name: Optional[str]
    surname: Optional[str]
    email: Optional[EmailStr] = None
    is_superuser: bool = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    """To create a User the email is mandatory."""

    email: EmailStr


# Properties to receive via API on update
class UserUpdate(UserBase):
    ...


class UserInDBBase(UserBase):
    id: int
    created: dt.datetime
    updated: dt.datetime

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass
