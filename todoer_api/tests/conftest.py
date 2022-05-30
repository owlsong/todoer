import asyncio
import httpx
import pytest_asyncio
from asgi_lifespan import LifespanManager
from app.main import app, get_database
from app.model.task import TaskCreate
from app.data_layer import database as db
from typing import Optional, Any
from app.data_layer import data_obj_mgr as dom


# region global vars

old_test_task_db: db.TaskDatabase = db.database_factory(
    "mongo", db_name="test_taskdb", id_db_name="test_taskdb_id"
)
test_object_mgr: dom.DataObjectManager = db.database_factory(
    "mongo-data-obj-mgr", db_name="test_taskdb", id_db_name="test_taskdb_id"
)

test_task_db = test_object_mgr

NUM_INIT_TASKS = 2


async def get_test_database() -> db.TaskDatabase:
    return test_task_db


# endregion global vars

# region helpers


def get_url(sub_directory_struct) -> str:
    api_ver = 1
    return f"/api/v{api_ver}/{sub_directory_struct}"


def new_test_task(i: Optional[int] = None, desc: Optional[str] = None) -> TaskCreate:
    return TaskCreate(
        summary="Init Test Task" if i is None else f"Init Test Task {i}",
        description="Initial Test Task" if desc is None else f"Test Task: {desc}",
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

# scope (from low to high)
# function: the default scope, the fixture is destroyed at the end of the test.
# class: the fixture is destroyed during teardown of the last test in the class.
# module: the fixture is destroyed during teardown of the last test in the module.
# package: the fixture is destroyed during teardown of the last test in the package.
# session: the fixture is destroyed at the end of the test session.


@pytest_asyncio.fixture(scope="session")
def event_loop():
    # automatically requested by pytest-asyncio before executing asynchronous tests.
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_database():
    # when adding params to tests it looks for fixtures
    # CARGO - not sure why no async
    global test_task_db
    yield test_task_db
    # this is needed to enable the db conn to be released and the tests to end
    del test_task_db


@pytest_asyncio.fixture
async def test_client():
    # an async client for use in tests
    # CARGO
    app.dependency_overrides[get_database] = get_test_database
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            app=app, base_url="http://127.0.0.1:8000/todoer"
        ) as client:
            yield client


@pytest_asyncio.fixture(autouse=True, scope="module")
async def initial_tasks():
    # autouse - means does not need otb eexplicitly called as a param
    # CARGO

    # PROB! - any await call to task_mgr prevents from closing!
    global test_task_db
    task_mgr = test_task_db.get_object_manager("Task")
    initial_tasks = [new_test_task() for i in range(NUM_INIT_TASKS)]
    for task in initial_tasks:
        await task_mgr.add(obj_in=task)

    yield initial_tasks
    await test_task_db.drop_database()
