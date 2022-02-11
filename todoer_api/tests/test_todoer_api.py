from typing import Optional
from pydantic.tools import parse_obj_as
from todoer_api import service_version, service_name

# from todoer_api.model import Task
from app.schemas import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskSearchResults,
)  #  todoer_api.model import Task

# import todoer_api.data_layer as dl
from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
from app.main import app
import datetime as dt

# from config import get_logger
from app.core.config import get_logger


logger = get_logger("todoer")
client = TestClient(app)
BAD_ID = -123
BAD_DATA = {"what": "this is a random dict that does not match the schema"}

# test plan
# ---------
# test - using base test id (avoid having to assume empty)???
# test - using inmem db
# test - setup suite as per EG


def get_route(suffix: str, route_type: Optional[str] = "api") -> str:
    """The route based o nthe route type such as: api, admin."""
    return f"/todoer/{route_type}/v1/{suffix}"


def task_to_json_deprecated(task: Task, exclude_fields: list[str] = []):
    """Return a dict representing the JSON that is REST friendly."""
    # currently just exclude datetime fields
    # exclude_fields = ["created", "updated"]
    # if not include_id:
    #     exclude_fields.append("id")
    # TODO use jsonable_encoder -> converts things like datetime to strs tpo be JSON compatible
    json_dict = task.dict()
    return {
        key: value for (key, value) in json_dict.items() if key not in exclude_fields
    }


def _create_new_task_object() -> Task:
    return TaskCreate(
        project="test_project",
        summary=f"Auto-generated test task",
        description=f"Description for test task",
        status="Backlog",
        assignee_id=1,
        tags="test",
    )


def _post_new_task_to_db() -> Task:
    # new_task = TaskCreate(
    #     project="test_project",
    #     summary=f"Auto-generated test task",
    #     description=f"Description for test task",
    #     status="Backlog",
    #     assignee_id=1,
    #     tags="test",
    # )
    new_task = _create_new_task_object()
    response = client.post(get_route("tasks"), json=jsonable_encoder(new_task))
    assert response.status_code == 201
    return Task(**response.json())


def _put_update_task(upd_task: Task):
    exclude_fields = ["created", "updated"]
    response = client.put(
        get_route(f"tasks/{upd_task.id}"),
        json=task_to_json_deprecated(upd_task, exclude_fields),
    )
    assert response.status_code == 200
    return Task(**response.json())


def _compare_tasks(task1: Task, task2: Task):
    # exclude_fields = ["created", "updated"]
    exclude_fields = []
    return task_to_json_deprecated(task1, exclude_fields) == task_to_json_deprecated(
        task2, exclude_fields
    )


def _check_tasks_len(expected_len: int = None):
    # get tasks -> empty
    response = client.get(get_route("tasks"))
    assert response.status_code == 200
    rslts = TaskSearchResults(**response.json())
    num = len(rslts.results)
    if expected_len is not None:
        assert num == expected_len
    return num


def _get_task(task_id: int):
    """get task for given task_id"""
    # dict -> model     Task(**task)
    # model -> dict     task.dict()
    response = client.get(get_route(f"tasks/{task_id}"))
    assert response.status_code == 200
    return Task(**response.json())


def _get_all_tasks():
    """get all tasks"""
    # dict -> model     Task(**task)
    # model -> dict     task.dict()
    response = client.get(get_route("tasks"))
    assert response.status_code == 200
    return TaskSearchResults(**response.json()).results


def _setup_test():
    """Delete all tasks to ensure clean for runnning test."""
    url = get_route("tasks", "admin")
    resp_del = client.delete(get_route("tasks", "admin"))
    assert resp_del.status_code == 204
    # initial -> empty
    _check_tasks_len(0)


def _cleanup_test(task_id: int = None):
    """Delete all tasks (or task if id supplied) to ensure clean after test."""
    if task_id is None:
        resp_del = client.delete(get_route("tasks", "admin"))
        assert resp_del.status_code == 204
    else:
        resp_del = client.delete(get_route(f"tasks/{task_id}"))
        assert resp_del.status_code == 200
    _check_tasks_len(0)


def test_version():
    assert service_version == "0.4.0"


def test_ping():
    """Test the simple ping service and check response time."""
    pre_time = dt.datetime.now()
    response = client.get(get_route("ping"))
    assert response.status_code == 200
    response_body = response.json()
    ping_str = response_body.get("ping", None)
    assert ping_str is not None
    # "2021-12-19 10:53:51" -> "%Y-%m-%d %H:%M%S"
    post_time = dt.datetime.strptime(ping_str, "%Y-%m-%d %H:%M:%S")
    dur_secs = (post_time - pre_time).total_seconds()
    assert dur_secs < 0.5


def test_read_info():
    response = client.get(get_route("info"))
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["service"] == service_name
    # assert response_body["data_source"] == "???"
    assert response_body["version"] == service_version


def test_setup_test():
    _setup_test()
    _check_tasks_len(0)


def test_add_del_empty():
    _setup_test()

    # create task
    new_task = _post_new_task_to_db()
    _check_tasks_len(1)

    _cleanup_test(new_task.id)


def test_get():
    _setup_test()

    # create task
    rslt_new = _post_new_task_to_db()
    _check_tasks_len(1)

    # get/compare task
    get_task = _get_task(rslt_new.id)
    _compare_tasks(get_task, rslt_new)
    _cleanup_test(rslt_new.id)


def test_gets():
    _setup_test()

    # create tasks
    num_tasks = 3
    new_tasks = {}
    for id in range(num_tasks):
        new_task = _post_new_task_to_db()
        new_tasks[new_task.id] = new_task

    _check_tasks_len(num_tasks)
    # get/compare task
    response_tasks = _get_all_tasks()
    assert len(response_tasks) == num_tasks
    for i in range(len(response_tasks)):
        response_task = response_tasks[i]
        _compare_tasks(response_task, new_tasks[response_task.id])

    _cleanup_test()


def test_update():
    _setup_test()

    # create task
    rslt_new = _post_new_task_to_db()
    _check_tasks_len(1)
    logger.info(f"test_update createred task {rslt_new.id}")
    # get/compare task
    get_task = _get_task(rslt_new.id)
    assert _compare_tasks(get_task, rslt_new)

    # update
    upd_task = rslt_new.copy(deep=True)
    upd_task.description = "modified description"
    rslt_upd = _put_update_task(upd_task)
    _compare_tasks(upd_task, rslt_upd)

    _cleanup_test(rslt_new.id)


def test_bad_id_get():
    _setup_test()
    global BAD_ID
    response = client.get(get_route(f"tasks/{BAD_ID}"))
    assert response.status_code == 404
    missing_id = 1  # setup ensures no tasks exist
    response = client.get(get_route(f"tasks/{missing_id}"))
    assert response.status_code == 404


def test_bad_id_del():
    _setup_test()
    global BAD_ID
    response = client.delete(get_route(f"tasks/{BAD_ID}"))
    assert response.status_code == 404
    missing_id = 1  # setup ensures no tasks exist
    response = client.get(get_route(f"tasks/{missing_id}"))
    assert response.status_code == 404


def test_bad_data_create():
    _setup_test()
    global BAD_DATA
    response = client.post(get_route(f"tasks"), json=BAD_DATA)
    assert response.status_code == 422


def test_bad_id_update():
    _setup_test()
    global BAD_ID

    # create task
    rslt_new = _post_new_task_to_db()
    _check_tasks_len(1)

    # update with the wrong id
    response = client.put(get_route(f"tasks/{BAD_ID}"), json=jsonable_encoder(rslt_new))
    assert response.status_code == 404
    _cleanup_test()


def test_bad_data_update():
    _setup_test()
    global BAD_DATA

    # create task
    rslt_new = _post_new_task_to_db()
    _check_tasks_len(1)

    # update with invalid data
    response = client.put(get_route(f"tasks/{rslt_new.id}"), json=BAD_DATA)
    assert response.status_code == 422

    _cleanup_test()
