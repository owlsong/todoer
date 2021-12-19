from todoer_api import __version__, __service_name__
from todoer_api.model import Task
from fastapi.testclient import TestClient
from main import app
import datetime as dt


client = TestClient(app)
BAD_ID = -123


def _create_test_task(task_id: int):
    return Task(
        id=task_id,
        summary=f"Auto-generated test task {task_id}",
        description=f"Description for task {task_id}",
        status="Backlog",
        assignee="tester",
    )


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


def _check_tasks_len(expected_len: int = None):
    # get tasks -> empty
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    num = len(response.json())
    if expected_len is not None:
        assert num == expected_len
    return num


def test_initial_state():
    _check_tasks_len(0)


def test_add_del_empty():
    # initial -> empty
    _check_tasks_len(0)
    # create task -> OK
    tsk = _create_test_task(0)
    response = client.post(f"/api/v1/tasks", json=tsk.dict())
    assert response.status_code == 201
    _check_tasks_len(1)
    # del task -> OK
    resp_del = client.delete(f"/api/v1/tasks/{tsk.id}")
    assert resp_del.status_code == 204
    # get tasks -> empty
    _check_tasks_len(0)


def test_bad_get():
    global BAD_ID
    response = client.get(f"/api/v1/tasks/{BAD_ID}")
    assert response.status_code == 404


def test_bad_del():
    global BAD_ID
    response = client.delete(f"/api/v1/tasks/{BAD_ID}")
    assert response.status_code == 404


def test_bad_update():
    # global BAD_ID
    # response = client.delete(f"/api/v1/tasks/{BAD_ID}")
    # assert response.status_code == 404
    pass


def test_bad_create():
    # global BAD_ID
    # response = client.delete(f"/api/v1/tasks/{BAD_ID}")
    # assert response.status_code == 404
    pass


def test_bad_data():
    # does this cover both PUT and POST
    # expect 422
    # global BAD_ID
    # response = client.delete(f"/api/v1/tasks/{BAD_ID}")
    # assert response.status_code == 404
    pass


def test_get():
    # test initial
    # add task -> OK
    # get/compare task
    # clean-up
    pass


def test_gets():
    # test initial
    # add tasks -> OK
    # get/compare tasks
    # get/compare task for all ids
    # clean-up
    pass


def test_update():
    # test initial
    # add task -> OK
    # get/compare task
    # modify task -> put
    # get/compare task
    # clean-up
    pass


def def_all_tests():
    #       @app.gets("/api/v1/tasks", response_model=List[Task])
    #       @app.get("/api/v1/tasks/{task_id}", response_model=Task)
    # do_bad @app.post("/api/v1/tasks")
    # OK     @app.delete("/api/v1/tasks/{task_id}")
    #       @app.put("/api/v1/tasks/{task_id}")
    pass


def def_test_plan():
    # test plan
    # test - using base test id???
    # test - using inmem db
    # test - setup suite as per EG
    pass
