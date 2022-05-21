from typing import Optional
from app.crud.base import CRUDMongoBase, MongoConnection
from app.model.task import TaskCreate, TaskUpdate, Task

# from app.schemas.task import TaskCreate, TaskUpdate  # Pydantic models/schemas


class CRUDTask(CRUDMongoBase[Task, TaskCreate, TaskUpdate]):
    def get_by_key(self, db: MongoConnection, *, key: str) -> Optional[Task]:
        return self.filter_one(db, {"key": key})


task = CRUDTask(Task)
