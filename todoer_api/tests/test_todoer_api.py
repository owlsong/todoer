from todoer_api import __version__, __service_name__
from todoer_api.model import Task
from fastapi.testclient import TestClient
from main import app
import datetime as dt


client = TestClient(app)
BAD_ID = -123


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
    # create task
    new_task = _create_test_task(task_id)
    response = client.post(f"/api/v1/tasks", json=new_task.dict())
    assert response.status_code == 201
    return Task(**response.json())


def _put_update_task(upd_task: Task):
    # create task

    # remove created field as updated internally
    # and error when put request tries to convert datetime to json
    json_dict = upd_task.dict()
    created_name = "created"
    if created_name in json_dict:
        del json_dict[created_name]
    response = client.put(f"/api/v1/tasks/{upd_task.id}", json=json_dict)
    assert response.status_code == 200
    return Task(**response.json())


def _compare_tasks(task1: Task, task2: Task):
    dict1 = task1.dict()
    dict2 = task2.dict()

    def del_ignored_entries(dict_in):
        deleted_entry = "created"
        if deleted_entry in dict_in:
            del dict_in[deleted_entry]

    dict1 = del_ignored_entries(dict1)
    dict2 = del_ignored_entries(dict2)
    return dict1 == dict2


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
    # global BAD_ID
    # response = client.delete(f"/api/v1/tasks/{BAD_ID}")
    # assert response.status_code == 404
    pass


def test_bad_data_create():
    # global BAD_ID
    # response = client.delete(f"/api/v1/tasks/{BAD_ID}")
    # assert response.status_code == 404
    pass


def test_bad_data_update():
    # does this cover both PUT and POST
    # expect 422
    # global BAD_ID
    # response = client.delete(f"/api/v1/tasks/{BAD_ID}")
    # assert response.status_code == 404
    pass


def def_all_tests():
    # some @app.gets("/api/v1/tasks", response_model=List[Task])
    # OK   @app.get("/api/v1/tasks/{task_id}", response_model=Task)
    # some @app.post("/api/v1/tasks")
    # OK   @app.delete("/api/v1/tasks/{task_id}")
    #      @app.put("/api/v1/tasks/{task_id}")
    pass


def def_test_plan():
    # test plan
    # test - using base test id???
    # test - using inmem db
    # test - setup suite as per EG
    pass
