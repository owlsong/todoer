from typing import Any
from app.crud.base import CRUDMongoBase
from app.crud import Task, User
from .mongo_connection import MongoCollection
from .id_generator import TaskIdGenerator
from app.crud.crud_task import CRUDTask
from app.crud.crud_user import CRUDUser


class DataObjectManager:
    """Class responsible for managing a specific persistent data object collection.

    The types defiend in DataObject (based on pydantic.BaseModel)
        ModelType, CreateSchemaType, UpdateSchemaType
    """

    def __init__(self, collection: MongoCollection, id_gen: TaskIdGenerator) -> None:
        super().__init__()
        self.collection = collection
        self.id_gen = id_gen
        # TODO!!! removme collection name from MongoConnection
        task = CRUDTask(Task, self.collection, self.id_gen)
        user = CRUDUser(User, self.collection)
        self._factory = {"Task": task, Task: task, "User": user, User: user}

    def get_object_manager(self, object_type: Any) -> CRUDMongoBase:
        return self._factory[object_type]
