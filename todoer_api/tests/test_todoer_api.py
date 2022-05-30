import httpx
import pytest
from fastapi import status
from fastapi.encoders import jsonable_encoder
import datetime as dt
from todoer_api import __version__, __service_name__
from app.data_layer import database as db
from .conftest import compare_models, new_test_task, get_url
from app.model.task import Task, TaskUpdate, TaskPartialUpdate
from typing import Union
from app.data_layer.data_obj_mgr import DataObjectManager, CRUDMongoBase
from app.core.config import get_logger

logger = get_logger("todoer")


async def get_first_task(test_client: httpx.AsyncClient):
    # get 1st task from get all
    response = await test_client.get(get_url("tasks"))
    assert response.status_code == status.HTTP_200_OK
    response_body = response.json()
    assert len(response_body) > 0
    return Task(**(response_body[0]))


async def get_tasks_via_api(test_client: httpx.AsyncClient, task_key: str):
    response = await test_client.get(get_url(f"tasks/{task_key}"))
    assert response.status_code == status.HTTP_200_OK
    response_body = response.json()
    # assert len(response_body) > 0
    return Task(**response_body)


@pytest.mark.asyncio
class TestInfo:
    async def test_version(self, caplog):
        assert __version__ == "0.3.0"

    async def test_ping(self, test_client: httpx.AsyncClient):
        pre_time = dt.datetime.now()
        response = await test_client.get(get_url("ping"))
        assert response.status_code == status.HTTP_200_OK

        response_body = response.json()
        ping_str = response_body.get("ping", None)
        assert ping_str is not None
        # "2021-12-19 10:53:51" -> "%Y-%m-%d %H:%M%S"
        post_time = dt.datetime.strptime(ping_str, "%Y-%m-%d %H:%M:%S")
        dur_secs = (post_time - pre_time).total_seconds()
        assert dur_secs < 0.5

    async def test_read_info(self, test_client: httpx.AsyncClient):
        response = await test_client.get(get_url("info"))
        assert response.status_code == status.HTTP_200_OK
        response_body = response.json()
        assert response_body["service"] == __service_name__
        assert response_body["version"] == __version__


@pytest.mark.asyncio
class TestTasksGet:
    BAD_KEY = "bad_id"

    async def test_get_not_existing(
        self, test_client: httpx.AsyncClient, initial_tasks
    ):
        # confirm not in db
        exists_lst = [x for x in initial_tasks if x.key == self.BAD_KEY]
        assert len(exists_lst) == 0
        # # now check for correct REST code
        response = await test_client.get(get_url(f"tasks/{self.BAD_KEY}"))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_init_num(
        self,
        test_client: httpx.AsyncClient,
        initial_tasks,
    ):
        response = await test_client.get(get_url("tasks"))
        assert response.status_code == status.HTTP_200_OK
        response_body = response.json()
        assert len(response_body) == len(initial_tasks)

    async def test_init_tasks_get_all(
        self, test_client: httpx.AsyncClient, initial_tasks
    ):
        response = await test_client.get(get_url("tasks"))
        assert response.status_code == status.HTTP_200_OK
        response_body = response.json()

        initial_dict = {task.key: task for task in initial_tasks}
        for tsk_json in response_body:
            task_api = Task(**tsk_json)
            task_init = initial_dict[task_api.key]
            assert compare_models(task_api, task_init)

    async def test_init_tasks_get(self, test_client: httpx.AsyncClient, initial_tasks):
        for task_orig in initial_tasks:
            task_key = task_orig.key
            # get specific task and db - compare
            task_get = await get_tasks_via_api(test_client, task_key)
            assert compare_models(task_orig, task_get)


@pytest.mark.asyncio
class TestTasksModify:
    BAD_KEY = "bad_id"

    async def test_task_add_del(self, test_client: httpx.AsyncClient):
        # add task
        new_task_in = new_test_task(desc="new task")
        pay_load = jsonable_encoder(new_task_in)
        response = await test_client.post(get_url("tasks"), json=pay_load)
        assert response.status_code == status.HTTP_201_CREATED

        # get task from response and DB - compare
        response_body = response.json()
        task = Task(**response_body)
        task_get = await get_tasks_via_api(test_client, task.key)
        assert compare_models(task, task_get)

        # delete new task
        response = await test_client.delete(get_url(f"tasks/{task.key}"))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    async def test_task_add_bad_task(self, test_client: httpx.AsyncClient):
        bad_task_in = {"project bad name": "this wont work"}
        response = await test_client.post(get_url("tasks"), json=bad_task_in)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_task_del_bad_task(self, test_client: httpx.AsyncClient):
        bad_key = self.BAD_KEY
        response = await test_client.delete(get_url(f"tasks/{bad_key}"))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def task_update(
        self,
        test_client: httpx.AsyncClient,
        task_key: str,
        task_in: Union[TaskUpdate, TaskPartialUpdate],
    ):
        response = await test_client.put(
            get_url(f"tasks/{task_key}"), json=jsonable_encoder(task_in)
        )
        assert response.status_code == status.HTTP_200_OK
        return response

    async def test_task_update(
        self,
        test_client: httpx.AsyncClient,
        initial_tasks,
        test_database: DataObjectManager,
    ):
        # get existing task
        task_orig = initial_tasks[0]
        # task_orig = await get_first_task(test_client)
        task_key = task_orig.key

        # modify task & compare wth DB
        task_updated = task_orig.copy()
        task_updated.status = "Updated"
        response = await self.task_update(
            test_client, task_key, TaskUpdate(**task_updated.dict())
        )
        task_upd_rsp = Task(**(response.json()))

        # conapre to DB to capture update time
        task_mgr: CRUDMongoBase = test_database.get_object_manager("Task")
        task_db = await task_mgr.get_by_key("key", task_orig.key)
        assert compare_models(task_db, task_upd_rsp)

        # revert tasks task & compare wth DB
        response = await self.task_update(
            test_client, task_key, TaskUpdate(**task_orig.dict())
        )
        task_revert_rsp = Task(**(response.json()))
        task_revert_db = await task_mgr.get_by_key("key", task_orig.key)
        assert compare_models(task_revert_db, task_revert_rsp)

    async def test_task_update_bad_id(
        self, test_client: httpx.AsyncClient, initial_tasks
    ):
        # get existing task
        task_orig = initial_tasks[0]

        # modify task with bad ID
        task_updated = task_orig.copy()
        task_updated.status = "Updated"
        response = await test_client.put(
            get_url(f"tasks/{self.BAD_KEY}"), json=jsonable_encoder(task_updated)
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_task_update_bad_task(
        self, test_client: httpx.AsyncClient, initial_tasks
    ):
        # get existing task
        task_orig = initial_tasks[0]

        bad_task_in = {"project bad name": "this wont work"}
        response = await test_client.put(
            get_url(f"tasks/{task_orig.key}"), json=bad_task_in
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
