from pydantic.tools import parse_obj_as
from todoer_api import __version__, __service_name__
from todoer_api.model import Task
import todoer_api.data_layer as dl
from fastapi.testclient import TestClient
from main import app
import datetime as dt
from config import get_logger


logger = get_logger("todoer")
client = TestClient(app)
BAD_ID = -123
BAD_DATA = {"what": "this is a random dict that doe snot match the schema"}

# test plan
# ---------
# test - using base test id (avoid having to assume empty)???
# test - using inmem db
# test - setup suite as per EG


def task_to_json(task: Task, exclude_fields: list[str] = []):
    """Return a dict representing the JSON that is REST friendly."""
    # currently just exclude datetime fields
    # exclude_fields = ["created", "updated"]
    # if not include_id:
    #     exclude_fields.append("id")
    json_dict = task.dict()
    return {
        key: value for (key, value) in json_dict.items() if key not in exclude_fields
    }


def _post_new_task() -> Task:
    new_task = Task(
        id=0,
        owner="test_user",
        project="test_project",
        summary=f"Auto-generated test task",
        description=f"Description for test task",
        status="Backlog",
        assignee="test_user",
    )
    response = client.post(f"/api/v1/tasks", json=new_task.dict())
    assert response.status_code == 201
    return Task(**response.json())


def _put_update_task(upd_task: Task):
    exclude_fields = ["created", "updated"]
    response = client.put(
        f"/api/v1/tasks/{upd_task.id}", json=task_to_json(upd_task, exclude_fields)
    )
    assert response.status_code == 200
    return Task(**response.json())


def _compare_tasks(task1: Task, task2: Task):
    exclude_fields = ["created", "updated"]
    return task_to_json(task1, exclude_fields) == task_to_json(task2, exclude_fields)


def _check_tasks_len(expected_len: int = None):
    # get tasks -> empty
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    num = len(response.json())
    if expected_len is not None:
        assert num == expected_len
    return num


def _get_task(task_id: int):
    """get task for given task_id"""
    # dict -> model     Task(**task)
    # model -> dict     task.dict()
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    return Task(**response.json())


def _get_all_tasks():
    """get all tasks"""
    # dict -> model     Task(**task)
    # model -> dict     task.dict()
    response = client.get(f"/api/v1/tasks")
    assert response.status_code == 200
    rslts = []
    rsp_json = response.json()
    for tsk in rsp_json:
        rslts.append(Task(**tsk))
    return rslts


def _setup_test():
    resp_del = client.delete(f"/admin/v1/tasks")
    assert resp_del.status_code == 204
    # initial -> empty
    _check_tasks_len(0)


def _cleanup_test(task_id: int = None):
    if task_id is None:
        resp_del = client.delete(f"/admin/v1/tasks")
        pass
    else:
        resp_del = client.delete(f"/api/v1/tasks/{task_id}")
    assert resp_del.status_code == 204
    _check_tasks_len(0)


def test_version():
    assert __version__ == "0.3.0"


def test_ping():
    """Test the simple ping service and check response time."""
    pre_time = dt.datetime.now()
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    response_body = response.json()
    ping_str = response_body.get("ping", None)
    assert ping_str is not None
    # "2021-12-19 10:53:51" -> "%Y-%m-%d %H:%M%S"
    post_time = dt.datetime.strptime(ping_str, "%Y-%m-%d %H:%M:%S")
    dur_secs = (post_time - pre_time).total_seconds()
    assert dur_secs < 0.5


def test_read_info():
    response = client.get("/api/v1/info")
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

    _cleanup_test(new_task.id)


def test_get():
    _setup_test()

    # create task
    rslt_new = _post_new_task()
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
        new_task = _post_new_task()
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
    rslt_new = _post_new_task()
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
    response = client.post(f"/api/v1/tasks", json=BAD_DATA)
    assert response.status_code == 422


def test_bad_data_update():
    _setup_test()
    global BAD_DATA

    # create task
    rslt_new = _post_new_task()
    _check_tasks_len(1)

    # update
    response = client.put(f"/api/v1/tasks/{rslt_new.id}", json=BAD_DATA)
    assert response.status_code == 422

    _cleanup_test(rslt_new.id)
