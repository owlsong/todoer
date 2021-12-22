from todoer_api import __version__, __service_name__
from todoer_api.model import Task
from fastapi.testclient import TestClient
from main import app
import datetime as dt


client = TestClient(app)
BAD_ID = -123
BAD_DATA = {"what": "this is a random dict that doe snot match the schema"}

# test plan
# ---------
# test - using base test id (avoid having to assume empty)???
# test - using inmem db
# test - setup suite as per EG


def _create_test_task(task_id: int):
    # created=dt.datetime.now(),
    return Task(
        id=task_id,
        summary=f"Auto-generated test task {task_id}",
        description=f"Description for task {task_id}",
        status="Backlog",
        assignee="tester",
    )


def _post_new_task(task_id: int):
    new_task = _create_test_task(task_id)
    response = client.post(f"/api/v1/tasks", json=new_task.dict())
    assert response.status_code == 201
    return Task(**response.json())


def _put_update_task(upd_task: Task):
    # use body method to remove fields that cannot be serialised by requests
    response = client.put(f"/api/v1/tasks/{upd_task.id}", json=upd_task.body())
    assert response.status_code == 200
    return Task(**response.json())


def _compare_tasks(task1: Task, task2: Task):
    return task1.body() == task2.body()


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


def test_version():
    assert __version__ == "0.3.0"


def test_ping():
    """Test the simple ping service and check response time."""
    pre_time = dt.datetime.now()
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    body = response.json()
    ping_str = body.get("ping", None)
    assert ping_str is not None
    # "2021-12-19 10:53:51" -> "%Y-%m-%d %H:%M%S"
    post_time = dt.datetime.strptime(ping_str, "%Y-%m-%d %H:%M:%S")
    dur_secs = (post_time - pre_time).total_seconds()
    assert dur_secs < 0.5


def test_read_info():
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    body = response.json()
    # assert response.json() == {"msg": "Hello World"}
    assert body["service"] == __service_name__
    assert body["data_source"] == "mongo"
    assert body["version"] == __version__


def test_initial_state():
    _check_tasks_len(0)


def test_add_del_empty():
    # initial -> empty
    _check_tasks_len(0)
    # create task
    new_task = _post_new_task(0)
    _check_tasks_len(1)
    # del task -> OK
    resp_del = client.delete(f"/api/v1/tasks/{new_task.id}")
    assert resp_del.status_code == 204
    # get tasks -> empty
    _check_tasks_len(0)


def test_get():
    new_id = 0
    # initial -> empty
    _check_tasks_len(0)
    # create task
    rslt_new = _post_new_task(new_id)
    _check_tasks_len(1)
    # get/compare task
    get_task = _get_task(rslt_new.id)
    assert get_task.dict() == rslt_new.dict()

    # clean-up
    resp_del = client.delete(f"/api/v1/tasks/{rslt_new.id}")
    assert resp_del.status_code == 204
    _check_tasks_len(0)


def test_gets():
    num_tasks = 3
    # initial -> empty
    _check_tasks_len(0)
    # create tasks
    new_tasks = {}
    for id in range(num_tasks):
        new_tasks[id] = _post_new_task(id)
    _check_tasks_len(num_tasks)
    # get/compare task
    response_tasks = _get_all_tasks()
    assert len(response_tasks) == num_tasks
    for i in range(len(response_tasks)):
        response_task = response_tasks[i]
        assert response_task.dict() == new_tasks[response_task.id].dict()

    # clean-up
    for task in response_tasks:
        resp_del = client.delete(f"/api/v1/tasks/{task.id}")
        assert resp_del.status_code == 204
    _check_tasks_len(0)


def test_update():
    new_id = 0
    # initial -> empty
    _check_tasks_len(0)
    # create task
    rslt_new = _post_new_task(new_id)
    _check_tasks_len(1)
    # get/compare task
    get_task = _get_task(rslt_new.id)
    assert get_task.dict() == rslt_new.dict()
    # update
    upd_task = rslt_new.copy(deep=True)
    upd_task.description = "modified description"
    rslt_upd = _put_update_task(upd_task)
    _compare_tasks(upd_task, rslt_upd)

    # clean-up
    resp_del = client.delete(f"/api/v1/tasks/{rslt_new.id}")
    assert resp_del.status_code == 204
    _check_tasks_len(0)


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
    global BAD_DATA
    # initial -> empty
    new_id = 0
    _check_tasks_len(0)
    # create task
    rslt_new = _post_new_task(new_id)
    _check_tasks_len(1)

    # update
    response = client.put(f"/api/v1/tasks/{new_id}", json=BAD_DATA)
    assert response.status_code == 422

    # clean-up
    resp_del = client.delete(f"/api/v1/tasks/{new_id}")
    assert resp_del.status_code == 204
    _check_tasks_len(0)
