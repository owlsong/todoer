# import imp
# from sqlite3 import connect
import datetime as dt
from typing import Any, List, Union
from app.data_layer.data_obj_mgr import DataObjectManager
from black import TRANSFORMED_MAGICS

# from app.core.config import get_logger
# from motor.motor_asyncio import (
#     AsyncIOMotorClient,
#     AsyncIOMotorCollection,
# )
# from fastapi.encoders import jsonable_encoder
# from pymongo import ReturnDocument
from app.core.config import get_logger
from app.model.base import ObjectId
from app.model.task import Task, TaskCreate, TaskPartialUpdate, TaskUpdate
from .mongo_connection import MongoConnection, MongoCollection
from .dl_exception import DataLayerException
from .id_generator import TaskIdGeneratorInmem, TaskIdGeneratorMogo

logger = get_logger("data layer")

# TODO! - 3 classes: DataLayer = [1]DB + [*]Model + [1]ID_generator
# DbInMem   CrudInMem(model clases, takes db as arg - then implments db specific cmds but data_model is generic)
# DbMongo   CrudMongo(model classes)
# abstract_factory that builds DB + ID_generator + Crud for each model


# TODO! - remove these old DB classes
class TaskDatabase:
    """Persists tasks internally whilst exposing the CRUD operations on Task objects."""

    def __init__(self, db_type, id_gen) -> None:
        self.db_type = db_type
        self.id_gen = id_gen

    async def get(self, task_id: Any) -> Task:
        """Get a list of tasks with id=task_id, up to user to validate number of tasks."""
        raise NotImplementedError()

    async def get_all(self, skip=0, limit=10) -> list[Task]:
        """Get all tasks as a list of tasks, empty if none."""
        raise NotImplementedError()

    async def add(self, task: TaskCreate) -> Task:
        """Add a new task and return the created task, (fail if task.id already exists).

        invariant:  id's are unique
        pre:        task with id does not exist
        post:       task with id exists
        """
        raise NotImplementedError()

    async def update(
        self, task_key: str, task_in: Union[TaskUpdate, TaskPartialUpdate]
    ) -> Task:
        """Update a single task with id=task_id return updated task, (fail if task_id does not exist)."""
        raise NotImplementedError()

    async def delete(self, key: str) -> None:
        """Delete a single task with id=task_id return nothing, (fail if task_id does not exist)."""
        raise NotImplementedError()

    async def delete_all(self) -> None:
        """Delete all tasks return nothing, (do nothing if no tasks exist)."""
        raise NotImplementedError()

    async def drop_database(self) -> None:
        """Drop the database."""
        raise NotImplementedError()


# region MongoDB


class MongoDatabase(TaskDatabase):
    """Stores tasks in a mongo database public API refers to Task objects (internal as dicts)."""

    def __init__(
        self, task_collection: MongoCollection, id_gen: TaskIdGeneratorMogo
    ) -> None:
        super().__init__("mongo", id_gen)
        self._task_collection = task_collection
        self.tasks = self._task_collection.get_collection()

    def __del__(self):
        del self._task_collection

    async def _get_by_id(self, task_id, must_be_equal_to=None) -> list[dict]:
        """Get tasks that match the id, specifying must_be_equal_to adds a check of number or tasks."""
        query = self.tasks.find({"_id": task_id})
        item_list = [Task(**raw_task) async for raw_task in query]
        num = len(item_list)
        if must_be_equal_to is not None and must_be_equal_to != num:
            raise DataLayerException(
                f"Error expected {must_be_equal_to} task(s) with ID {task_id} but had {num} occurance(s)"
            )
        return item_list

    async def _get_by_key(self, task_key, must_be_equal_to=None) -> list[dict]:
        """Get tasks that match the id, specifying must_be_equal_to adds a check of number or tasks."""
        query = self.tasks.find({"key": task_key})
        item_list = [Task(**raw_task) async for raw_task in query]
        num = len(item_list)
        if must_be_equal_to is not None and must_be_equal_to != num:
            raise DataLayerException(
                f"Error expected {must_be_equal_to} task(s) with ID {task_key} but had {num} occurance(s)"
            )
        return item_list

    async def get(self, task_id: Any) -> Task:
        if isinstance(task_id, str):
            rslts = await self._get_by_key(task_id, must_be_equal_to=1)
        else:
            rslts = await self._get_by_id(task_id, must_be_equal_to=1)
        return rslts[0]

    async def get_all(self, skip=0, limit=10) -> list[Task]:
        # 1 = ascending, -1 = descending
        query = self.tasks.find({}, skip=skip, limit=limit).sort("key", 1)
        results = [Task(**raw_task) async for raw_task in query]
        return results

    async def add(self, task_in: TaskCreate) -> Task:
        new_id = await self.id_gen.get_next_id(task_in.project)
        new_data = task_in.get_dict_inc_seq(new_id)
        # TODO-low set seq, key in pydantic model logic
        new_task = Task(**new_data)
        new_key = new_task.key

        # ensure task.key does not pre-exist
        try:
            await self._get_by_key(new_key, 0)
        except DataLayerException:
            raise DataLayerException(
                f"Error attempted to add task with key {new_key} but already exists"
            )

        result = await self.tasks.insert_one(new_task.dict(by_alias=True))
        logger.info(f"Inserted task id {str(result.inserted_id)} key {new_key}")
        try:
            return await self.get(new_key)
        except DataLayerException:
            raise DataLayerException(f"Error failed to add task with key {new_key}")

    async def update(
        self, task_key: str, task_in: Union[TaskUpdate, TaskPartialUpdate]
    ) -> Task:
        try:
            stored_task: Task = await self.get(task_key)
        except DataLayerException:
            raise DataLayerException(
                f"Error attempted to update a task with key {task_key} but does not exist"
            )
        updated_task = stored_task.copy(update=task_in.dict(exclude_unset=True))
        updated_task.updated = dt.datetime.now()
        await self.tasks.update_one(
            {"_id": updated_task.id},
            {"$set": updated_task.dict(by_alias=True, exclude_unset=True)},
        )

        return await self.get(task_key)

    async def delete(self, key: str) -> None:
        try:
            await self._get_by_key(key, 1)
        except DataLayerException:
            raise DataLayerException(
                f"Error attempted to delete task with key {key} but does not exist"
            )
        await self.tasks.delete_one({"key": key})

    async def delete_all(self) -> None:
        await self.tasks.delete_many({})

    async def drop_database(self) -> None:
        await self._task_collection.drop_db()
        # await self._task_collection().drop_database(self.db_name)
        # self.db = None
        # self.tasks = self._task_collection.get_collection()


# endregion


class InMemDatabase(TaskDatabase):
    def __init__(self):
        super().__init__("in-memory")
        self.data = {}  # Dict[id] -> Task
        self.data_index = {}  # Dict[key] -> Task
        self.id_gen = TaskIdGeneratorInmem()
        self.seq_gen = TaskIdGeneratorInmem()
        # self.next_id = 0

    def _get_task_by_index(self, key: str) -> Task:
        """Gets a task using key and returns None if does not exist."""
        try:
            return self.data_index[key]
        except KeyError:
            return None

    def _get_task(self, id: ObjectId) -> Task:
        """Gets a task using a id(ObjectId) and returns None if does not exist."""
        try:
            return self.data[id]
        except KeyError:
            return None

    async def get(self, id: Any) -> Task:
        """Gets a task by id(ObjectId) or key(str) and raises Error if does not exist."""
        try:
            if isinstance(id, ObjectId):
                return self.data[id]
            return self.data_index[id]
        except KeyError:
            raise DataLayerException(f"Task with seq {id} could not be found")

    async def get_all(self, skip=0, limit=10) -> list[Task]:
        data_items = self.data.items()
        sorted_data = sorted(data_items)
        sorted_data = sorted_data[skip : skip + limit]
        return [task for _, task in sorted_data]

    async def add(self, task_in: TaskCreate) -> Task:
        new_data = task_in.get_dict_inc_seq(self.seq_gen.get_next_id(task_in.project))
        # TODO - set seq, key in pydantic model logic
        new_task = Task(**new_data)
        # task should auto create: id, created, updated
        new_key = new_task.key
        if self._get_task_by_index(new_key) is None:
            self.data_index[new_key] = new_task
            self.data[new_task.id] = new_task
        else:
            raise DataLayerException(
                f"Error attempting to add Task {task_in.get_task_key()} already exists"
            )
        return self._get_task_by_index(new_key)

    async def update(
        self, task_key: str, task_in: Union[TaskUpdate, TaskPartialUpdate]
    ) -> Task:
        stored_task = self._get_task_by_index(task_key)
        if stored_task is None:
            raise DataLayerException(
                f"Error attempting to update Task {task_key} does not exist"
            )

        update_data = task_in.dict(exclude_unset=True)
        updated_task = stored_task.copy(update=update_data)
        updated_task.updated = dt.datetime.now()
        self.data_index[task_key] = updated_task
        self.data[updated_task.id] = updated_task

        return updated_task

    async def delete(self, key: str) -> None:
        try:
            # ensure in indexes before delete
            del_task = self.data_index[key]
            del_task2 = self.data[del_task.id]
            del self.data_index[key]
            del self.data[del_task2.id]
        except KeyError:
            raise DataLayerException(f"Delete task with key {key} could not be found")

    async def delete_all(self) -> None:
        self.data.clear()
        self.data_index.clear()

    async def drop_database(self) -> None:
        self.data = {}
        self.data_index = {}
        self.id_gen = TaskIdGeneratorInmem()
        self.seq_gen = TaskIdGeneratorInmem()


# endregion


def get_database_types() -> List[str]:
    return [
        "mongo",
        "in-memory",
    ]


def database_factory(db_type: str, **kwargs) -> TaskDatabase:
    db_name = kwargs.get("db_name", "taskdb")
    task_collection_name = kwargs.get("task_collection_name", "tasks")
    id_db_name = kwargs.get("id_db_name", "taskdb_id")
    id_collection_name = kwargs.get("id_collection_name", "tasks")
    logger.info(f"DB-factory type={db_type} DB={db_name} Table={task_collection_name}")
    if db_type == "mongo":
        mongo_conn = MongoConnection("localdev", "localdev", "mongo")
        mongo_coll = MongoCollection(mongo_conn, db_name, task_collection_name)
        mongo_id_coll = MongoCollection(mongo_conn, id_db_name, id_collection_name)
        return MongoDatabase(mongo_coll, TaskIdGeneratorMogo(mongo_id_coll))
    elif db_type == "mongo-data-obj-mgr":
        mongo_conn = MongoConnection("localdev", "localdev", "mongo")
        mongo_coll = MongoCollection(mongo_conn, db_name, task_collection_name)
        mongo_id_coll = MongoCollection(mongo_conn, id_db_name, id_collection_name)
        id_gen = TaskIdGeneratorMogo(mongo_id_coll)
        return DataObjectManager(mongo_coll, id_gen)
    elif db_type == "in-memory":
        return InMemDatabase(**kwargs)
    else:
        raise DataLayerException(f"Unknown database type {db_type}")
