from .model import Task
import datetime as dt
import pymongo
from config import get_logger

logger = get_logger("data layer")


class DataLayerException(Exception):
    pass


class TaskDatabase:
    """Stores tasks in a mongo database publis API refers to Task objects (internal as dicts)."""

    def __init__(self) -> None:
        self.db_type = ""

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

    def update(self, task: Task) -> Task:
        """Update a single task with id=task_id return updated task, (fail if task_id does not exist)."""
        raise NotImplementedError()

    def delete(self, task_id: int) -> None:
        """Delete a single task with id=task_id return nothing, (fail if task_id does not exist)."""
        raise NotImplementedError()

    def delete_all(self) -> None:
        """Delete all tasks return nothing, (do nothing if no tasks exist)."""
        raise NotImplementedError()


class MongoDatabase(TaskDatabase):
    """Stores tasks in a mongo database public API refers to Task objects (internal as dicts)."""

    def __init__(self) -> None:
        super().__init__()
        self.username = "localdev"
        self.password = "localdev"
        self.host = "mongo"
        self.url = f"mongodb://{self.username}:{self.password}@{self.host}:27017/"
        # mongodb://root:example@mongo:27017/
        # mongodb://localhost:27017/
        self.client = pymongo.MongoClient(self.url)
        self.db = self.client["taskdb"]  # db
        self.tasks = self.db["tasks"]  # collection

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
        # TODO allocate new ID? return new task
        # ensure task.id not pre-exist
        task_id = task.id
        try:
            self._get_by_id(task_id, 0)
        except DataLayerException:
            raise DataLayerException(
                f"Error attempted to add task with ID {task_id} but already exists"
            )

        task.created = dt.datetime.now()
        task.updated = task.created

        result = self.tasks.insert_one(task.dict())
        logger.info(f"Inserted task id {str(result.inserted_id)}")
        # return get as the db truncates the datetime so the actual object is different
        return self.get(task_id)

    def update(self, task: Task) -> Task:
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


class InMemDatabase(TaskDatabase):
    def __init__(self):
        self.data = {}  # Dict[id] -> Task
        # self.next_id = 0

    def _get_task(self, task_id: int):
        try:
            return self.data[task_id]
        except KeyError:
            return None

    def get(self, task_id: int) -> Task:
        try:
            return self.data[task_id]
        except KeyError:
            raise DataLayerException(f"Task with ID {task_id} could not be found")

    def get_all(self) -> list[Task]:
        return list(self.data.values())

    def add(self, task: Task) -> Task:
        if self._get_task(task.id) is None:
            task.created = dt.datetime.now()
            task.updated = task.created
            self.data[task.id] = task
        else:
            raise DataLayerException(
                f"Error attempting to add Task {task.id} already exists"
            )
        return self.get(task.id)

    def update(self, task: Task) -> Task:
        orig_task = self._get_task(task.id)
        if orig_task is None:
            raise DataLayerException(
                f"Error attempting to update Task {task.id} does not exist"
            )
        else:
            task.updated = dt.datetime.now()
            task.created = orig_task.created
            self.data[task.id] = task
        return self.get(task.id)

    def delete(self, task_id: int) -> None:
        try:
            del self.data[task_id]
        except KeyError:
            raise DataLayerException(
                f"Delete task with ID {task_id} could not be found"
            )

    def delete_all(self) -> None:
        self.data.clear()


CONNECTION_TYPE = ""
_DB_CON = None


def get_db_con(db_type: str) -> TaskDatabase:
    dbs = {"in_memory": InMemDatabase(), "mongo": MongoDatabase()}
    # logger.info(f"geting db conn of type {db_type}")
    global _DB_CON, CONNECTION_TYPE

    if _DB_CON is None or CONNECTION_TYPE != db_type:
        CONNECTION_TYPE = db_type
        _DB_CON = dbs[CONNECTION_TYPE]
        _DB_CON.db_type = CONNECTION_TYPE
    return _DB_CON
