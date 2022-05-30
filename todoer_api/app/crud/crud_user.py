from typing import Optional
from app.crud.base import CRUDMongoBase, MongoCollection
from app.model.user import UserCreate, UserUpdate, User


class CRUDUser(CRUDMongoBase[User, UserCreate, UserUpdate]):
    ...
