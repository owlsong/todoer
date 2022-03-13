# import imp
from .model import Task, TaskCreate, PyObjectId, ObjectId, TaskUpdate, TaskPartialUpdate
import datetime as dt
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Any, Union

# from app.core.config import get_logger
from app.core.config import get_logger

logger = get_logger("data layer")

# TODO! - 3 classes: DataLayer = [1]DB + [*]Model + [1]ID_generator
# DbInMem   CrudInMem(model clases, takes db as arg - then implments db specific cmds but data_model is generic)
# DbMongo   CrudMongo(model classes)
# abstract_factory that builds DB + ID_generator + Crud for each model
# get_db funct that uses USER = os.getenv('DB_TYPE') then calls  abstract_factory(db_type)


class DataLayerException(Exception):
    pass


class TaskIdGenerator:
    """Class to generate ids for tasks."""

    INIT_VALUE = 1

    def get_next_id(self, user: str, project: str) -> int:
        pass


class TaskDatabase:
    """Persists tasks internally whilst exposing the CRUD operations on Task objects."""

    def __init__(self) -> None:
        self.db_type = ""
        self.id_gen = None

    def get(self, task_id: int) -> Task:
        """Get a list of tasks with id=task_id, up to user to validate number of tasks."""
        raise NotImplementedError()

    def get_all(self) -> list[Task]:
        """Get all tasks as a list of tasks, empty if none."""
        raise NotImplementedError()

    def add(self, task: Task) -> Task:
        """Add a new task and return the created task, (fail if task.id already exists).

        invariant:  id's are unique
        pre:        task with id does not exist
        post:       task with id exists
        """
        raise NotImplementedError()

    def update(self, task_key: str, task: Task) -> Task:
        """Update a single task with id=task_id return updated task, (fail if task_id does not exist)."""
        raise NotImplementedError()

    def delete(self, task_id: int) -> None:
        """Delete a single task with id=task_id return nothing, (fail if task_id does not exist)."""
        raise NotImplementedError()

    def delete_all(self) -> None:
        """Delete all tasks return nothing, (do nothing if no tasks exist)."""
        raise NotImplementedError()


class TaskIdGeneratorMogo(TaskIdGenerator):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        # self.client = kwargs["client"]
        # self.db_name = kwargs["db_name"]
        self.collection_name = "id_generator"
        # self.db = self.client[self.db_name]
        self.db = kwargs["db"]
        self.id_collection = self.db[self.collection_name]
        # id indexed by: user: str, project: str

    def get_next_id(self, user: str, project: str) -> int:
        index_dict = {"user": user, "project": project}
        id_list = list(self.id_collection.find(index_dict))
        if len(id_list) == 0:
            # no IDs allocated yet -> current=0 next=1
            insert_dict = index_dict
            insert_dict["id"] = self.INIT_VALUE + 1
            self.id_collection.insert_one(insert_dict)
            return self.INIT_VALUE
        else:
            upd_dict = id_list[0]
            curr_id = upd_dict["id"]
            upd_dict["id"] = curr_id + 1
            self.id_collection.replace_one(index_dict, upd_dict)
            return curr_id


class MongoDatabase(TaskDatabase):
    """Stores tasks in a mongo database public API refers to Task objects (internal as dicts)."""

    def __init__(self) -> None:
        super().__init__()
        self.username = "localdev"
        self.password = "localdev"
        self.host = "mongo"
        self.url = f"mongodb://{self.username}:{self.password}@{self.host}:27017/"
        self.db_name = "taskdb"
        self.collection_name = "tasks"
        # mongodb://root:example@mongo:27017/
        # mongodb://localhost:27017/
        # TODO-HIGH !!! inject this dependnecy
        self.client = AsyncIOMotorClient(self.url)
        self.db = self.client[self.db_name]
        self.tasks = self.db[self.collection_name]
        self.id_gen = TaskIdGeneratorMogo(db=self.db)

    def _get_by_id(self, task_id, must_be_equal_to=None) -> list[dict]:
        """Get tasks that match the id, specifying must_be_equal_to adds a check of number or tasks."""
        item_list = list(self.tasks.find({"id": task_id}))
        num = len(item_list)
        if must_be_equal_to is not None and must_be_equal_to != num:
            raise DataLayerException(
                f"Error expected {must_be_equal_to} task(s) with ID {task_id} but had {num} occurance(s)"
            )
        return item_list

    def get(self, task_id: int) -> Task:
        # return self._get_by_id(task_id)
        return Task(**self._get_by_id(task_id, must_be_equal_to=1)[0])

    def get_all(self) -> list[Task]:
        task_list = self.tasks.find()
        return [Task(**task) for task in task_list]

    def add(self, task: Task) -> Task:
        # set admin info incl;duiiong the new id
        task.id = self.id_gen.get_next_id(task.owner, task.project)
        task.created = dt.datetime.now()
        task.updated = task.created

        # ensure task.id not pre-exist
        try:
            self._get_by_id(task.id, 0)
        except DataLayerException:
            raise DataLayerException(
                f"Error attempted to add task with ID {task.id} but already exists"
            )

        result = self.tasks.insert_one(task.dict())
        logger.info(f"Inserted task id {str(result.inserted_id)}")
        # return get as the db truncates the datetime so the actual object is different
        return self.get(task.id)

    def update(self, task_key: str, task: Task) -> Task:
        try:
            orig_task = self.get(task.id)
            task.updated = dt.datetime.now()
            task.created = orig_task.created
        except DataLayerException:
            raise DataLayerException(
                f"Error attempted to update a task with ID {task.id} but does not exist"
            )
        self.tasks.replace_one({"id": task.id}, task.dict())
        return self.get(task.id)

    def delete(self, task_id: int) -> None:
        try:
            self._get_by_id(task_id, 1)
        except DataLayerException:
            raise DataLayerException(
                f"Error attempted to delete task with ID {task_id} but does not exist"
            )
        self.tasks.delete_one({"id": task_id})

    def delete_all(self) -> None:
        self.tasks.delete_many({})


class TaskIdGeneratorInmem(TaskIdGenerator):
    def __init__(self) -> None:
        super().__init__()
        # id indexed by: user: str, project: str
        self.ids = {}

    def get_next_id(self, index: Any) -> int:
        # # index = (user, project)
        # index = project
        try:
            rslt = self.ids[index]
            self.ids[index] = rslt + 1
            return rslt
        except KeyError:
            self.ids[index] = self.INIT_VALUE + 1
            return self.INIT_VALUE


class InMemDatabase(TaskDatabase):
    def __init__(self):
        super().__init__()
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

    def get(self, id: Any) -> Task:
        """Gets a task by id(ObjectId) or key(str) and raises Error if does not exist."""
        try:
            if isinstance(id, ObjectId):
                return self.data[id]
            # raise DataLayerException("THC tmp")
            return self.data_index[id]
        except KeyError:
            raise DataLayerException(f"Task with seq {id} could not be found")

    def get_all(self) -> list[Task]:
        return list(self.data.values())

    def add(self, task_in: TaskCreate) -> Task:
        new_data = task_in.get_full_dict(self.seq_gen.get_next_id(task_in.project))
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

    def update(
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

    def delete(self, key: str) -> None:
        try:
            # ensure in indexes before delete
            del_task = self.data_index[key]
            del_task2 = self.data[del_task.id]
            del self.data_index[key]
            del self.data[del_task2.id]
        except KeyError:
            raise DataLayerException(f"Delete task with key {key} could not be found")

    def delete_all(self) -> None:
        self.data.clear()
        self.data_index.clear()


_DB_CON_FACTORY = {
    "in_memory": InMemDatabase(),
    "mongo": MongoDatabase(),
}
CONNECTION_TYPE = None
_DB_CON = None


def _get_db_con(db_type: str) -> TaskDatabase:
    # logger.info(f"geting db conn of type {db_type}")
    global _DB_CON, CONNECTION_TYPE, _DB_CON_FACTORY

    if _DB_CON is None or CONNECTION_TYPE != db_type:
        CONNECTION_TYPE = db_type
        _DB_CON = _DB_CON_FACTORY[CONNECTION_TYPE]
        _DB_CON.db_type = CONNECTION_TYPE
    return _DB_CON


def get_db() -> TaskDatabase:
    # TODO dynamic config the db type
    return _get_db_con("in_memory")
