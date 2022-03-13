from inspect import unwrap
from webbrowser import get
from pydantic.tools import parse_obj_as
from todoer_api import __version__, __service_name__
from todoer_api.model import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskPartialUpdate,
)  # , ObjectId, PyObjectId
import todoer_api.data_layer as dl
from app.main import app

from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
import datetime as dt
import json

# from config import get_logger
from app.core.config import get_logger


logger = get_logger("todoer")
client = TestClient(app)
BAD_ID = -123
BAD_DATA = {"what": "this is a random dict that doe snot match the schema"}

# test plan
# ---------
# test - using base test id (avoid having to assume empty)???
# test - using inmem db
# test - setup suite as per EG


def task_to_json_deprecated(task: Task, exclude_fields: list[str] = []):
    """Return a dict representing the JSON that is REST friendly."""
    # currently just exclude datetime fields
    # exclude_fields = ["created", "updated"]
    # if not include_id:
    #     exclude_fields.append("id")
    json_dict = task.dict()
    return {
        key: value for (key, value) in json_dict.items() if key not in exclude_fields
    }


def model_to_json(model_instance):
    """Return a dict representing the JSON that is REST friendly."""
    # return json.loads(model_instance.json())
    return jsonable_encoder(model_instance)


def _post_new_task() -> Task:
    #    owner="test_user",
    #    assignee="test_user",
    new_task = TaskCreate(
        project="test_project",
        summary=f"Auto-generated test task",
        description=f"Description for test task",
        status="Backlog",
        tags=[],
    )

    # json.loads(new_task.json())
    response = client.post(f"/todoer/api/v1/tasks", json=model_to_json(new_task))

    assert response.status_code == 201
    json_data = response.json()
    return Task(**json_data)


def _put_update_task(upd_task_in: TaskUpdate, key):
    # upd_task = TaskUpdate(**upd_task_in.dict())
    upd_task = upd_task_in
    logger.info(f"model sent to update {model_to_json(upd_task)}")
    response = client.put(
        f"/todoer/api/v1/tasks/{key}",
        json=model_to_json(upd_task),
    )
    assert response.status_code == 200
    return Task(**response.json())


def _compare_tasks(task1: Task, task2: Task):
    exclude_fields = ["created", "updated"]
    return task_to_json_deprecated(task1, exclude_fields) == task_to_json_deprecated(
        task2, exclude_fields
    )


def _check_tasks_len(expected_len: int = None):
    # get tasks -> empty
    response = client.get("/todoer/api/v1/tasks")
    assert response.status_code == 200
    num = len(response.json())
    if expected_len is not None:
        if num != expected_len:
            logger.info(f"THC check len response", response.json())
        assert num == expected_len
    return num


def _get_task(task_key: str) -> Task:
    """get task for given task_id"""
    # dict -> model     Task(**task)
    # model -> dict     task.dict()
    response = client.get(f"/todoer/api/v1/tasks/{task_key}")
    assert response.status_code == 200
    return Task(**response.json())


def _get_all_tasks():
    """get all tasks"""
    # dict -> model     Task(**task)
    # model -> dict     task.dict()
    response = client.get(f"/todoer/api/v1/tasks")
    assert response.status_code == 200
    rslts = []
    rsp_json = response.json()
    for tsk in rsp_json:
        rslts.append(Task(**tsk))
    return rslts


def _setup_test():
    resp_del = client.delete(f"/todoer/admin/v1/tasks")
    assert resp_del.status_code == 204
    # initial -> empty
    _check_tasks_len(0)


def _cleanup_test(task_key: str = None):
    if task_key is None:
        resp_del = client.delete(f"/todoer/admin/v1/tasks")
    else:
        resp_del = client.delete(f"/todoer/api/v1/tasks/{task_key}")
    assert resp_del.status_code == 204
    _check_tasks_len(0)


def test_version():
    assert __version__ == "0.3.0"


def test_ping():
    """Test the simple ping service and check response time."""
    pre_time = dt.datetime.now()
    response = client.get("/todoer/api/v1/ping")
    assert response.status_code == 200
    response_body = response.json()
    ping_str = response_body.get("ping", None)
    assert ping_str is not None
    # "2021-12-19 10:53:51" -> "%Y-%m-%d %H:%M%S"
    post_time = dt.datetime.strptime(ping_str, "%Y-%m-%d %H:%M:%S")
    dur_secs = (post_time - pre_time).total_seconds()
    assert dur_secs < 0.5


def test_read_info():
    response = client.get("/todoer/api/v1/info")
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["service"] == __service_name__
    assert response_body["data_source"] == dl.CONNECTION_TYPE
    assert response_body["version"] == __version__


def test_setup_test():
    _setup_test()
    _check_tasks_len(0)


def test_add_del_empty():
    _setup_test()

    # create task
    new_task = _post_new_task()
    _check_tasks_len(1)

    _cleanup_test(new_task.key)


def test_get():
    _setup_test()

    # create task
    rslt_new = _post_new_task()
    _check_tasks_len(1)

    # get/compare task
    get_task = _get_task(rslt_new.key)
    _compare_tasks(get_task, rslt_new)
    _cleanup_test(rslt_new.key)


def test_gets():
    _setup_test()

    # create tasks
    num_tasks = 3
    new_tasks = {}
    for id in range(num_tasks):
        new_task = _post_new_task()
        new_tasks[new_task.key] = new_task

    _check_tasks_len(num_tasks)
    # get/compare task
    response_tasks = _get_all_tasks()
    assert len(response_tasks) == num_tasks
    for i in range(len(response_tasks)):
        response_task = response_tasks[i]
        _compare_tasks(response_task, new_tasks[response_task.key])

    _cleanup_test()


def test_update():
    _setup_test()

    # create task
    rslt_new = _post_new_task()
    _check_tasks_len(1)
    logger.info(f"test_update created task {rslt_new.key}")
    logger.info(f"test_update created task {rslt_new.dict()}")
    # get/compare task
    get_task = _get_task(rslt_new.key)
    assert _compare_tasks(get_task, rslt_new)
    key = get_task.get_task_key()

    # update
    upd_dict = get_task.dict()
    wanted_fields = ["summary", "description", "status"]
    unwanted_fields = [x for x in upd_dict.keys() if x not in wanted_fields]
    for k in unwanted_fields:
        del upd_dict[k]
    upd_dict["summary"] = "updated summary"
    upd_task = TaskUpdate(**upd_dict)
    # upd_task = rslt_new.copy(deep=True)
    rslt_upd = _put_update_task(upd_task, key)
    logger.info(f"test_update orig task {get_task.dict()}")
    logger.info(f"test_update upd  task {upd_task.dict()}")
    logger.info(f"test_update rslt task {rslt_upd.dict()}")
    _check_tasks_len(1)
    _compare_tasks(upd_task, rslt_upd)

    _cleanup_test(rslt_upd.key)


def test_bad_id_get():
    global BAD_ID
    response = client.get(f"/api/v1/tasks/{BAD_ID}")
    assert response.status_code == 404


def test_bad_id_del():
    global BAD_ID
    response = client.delete(f"/api/v1/tasks/{BAD_ID}")
    assert response.status_code == 404


def test_bad_id_update():
    global BAD_ID
    response = client.delete(f"/api/v1/tasks/{BAD_ID}")
    assert response.status_code == 404


def test_bad_data_create():
    global BAD_DATA
    response = client.post(f"/todoer/api/v1/tasks", json=BAD_DATA)
    assert response.status_code == 422


def test_bad_data_update():
    _setup_test()
    global BAD_DATA

    # create task
    rslt_new = _post_new_task()
    _check_tasks_len(1)

    # update
    response = client.put(f"/todoer/api/v1/tasks/{rslt_new.key}", json=BAD_DATA)
    assert response.status_code == 422

    _cleanup_test(rslt_new.key)
