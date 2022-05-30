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
        self.db_type = "Data-object-manager-mongo"
        self.collection = collection
        self.id_gen = id_gen
        task = CRUDTask(Task, self.collection, self.id_gen)
        user = None  # cannot use same collection user = CRUDUser(User, self.collection)
        # self._factory = {"task": task, Task: task, "user": user, User: user}
        self._factory = {}
        self.add_manager("task", task)
        self.add_manager(Task, task)

    def add_manager(self, key: Any, obj_mgr: Any) -> None:
        self._factory[key] = obj_mgr

    def get_object_manager(self, object_type: Any) -> CRUDMongoBase:
        if isinstance(object_type, str):
            return self._factory[object_type.lower()]
        else:
            return self._factory[object_type]
