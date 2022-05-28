import asyncio
import httpx
import pytest_asyncio
from asgi_lifespan import LifespanManager
from app.main import app, get_database_v0
from app.model.task import TaskCreate
from app.data_layer import database as db
from typing import Optional, Any
from app.data_layer import data_obj_mgr as dom

# region global vars

test_task_db: db.TaskDatabase = db.database_factory(
    "mongo", db_name="test_taskdb", id_db_name="test_taskdb_id"
)
test_object_db: dom.DataObjectManager = db.database_factory(
    "mongo-data-obj-mgr", db_name="test_taskdb", id_db_name="test_taskdb_id"
)

NUM_INIT_TASKS = 2


async def get_test_database() -> db.TaskDatabase:
    global test_task_db
    return test_task_db


# endregion global vars

# region helpers


def new_test_task(i: Optional[int] = None, desc: Optional[str] = None) -> TaskCreate:
    return TaskCreate(
        summary="Init Test Task" if i is None else f"Init Test Task {i}",
        description="Init Test Task" if desc is None else f"Test Task: {desc}",
        status="New",
        tags=["Test"],
        project="Test",
    )


def compare_models(task1: Any, task2: Any) -> bool:
    # exclude_fields = ["created", "updated"]
    # exclude=exclude_fields
    dict1 = task1.dict()
    dict2 = task2.dict()
    return dict1 == dict2


# endregion helpers


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
def test_database():
    global test_task_db
    yield test_task_db
    # this is needed to enable the db conn to be released and the tests to end
    del test_task_db


@pytest_asyncio.fixture
async def test_client():
    app.dependency_overrides[get_database_v0] = get_test_database
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            app=app, base_url="http://127.0.0.1:8000/todoer"
        ) as client:
            yield client


@pytest_asyncio.fixture(autouse=True, scope="module")
async def initial_tasks():
    initial_tasks = [new_test_task() for i in range(NUM_INIT_TASKS)]
    global test_task_db
    for task in initial_tasks:
        await test_task_db.add(task)

    yield initial_tasks

    await test_task_db.drop_database()
