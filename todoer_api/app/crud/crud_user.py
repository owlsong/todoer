from typing import Optional
from app.crud.base import CRUDBase, MongoConnection
from app.model.user import UserCreate, UserUpdate, User


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: MongoConnection, *, email: str) -> Optional[User]:
        return self.filter_one(db, {"email": email})


user = CRUDUser(User)
