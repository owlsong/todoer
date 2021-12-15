from typing import List, Optional  # Dict,
from fastapi import FastAPI, HTTPException, Response

# from fastapi import FastAPI, status
# from fastapi import Request
# from fastapi.responses import JSONResponse

import datetime as dt

# from logging.config import dictConfig
# import logging
# from config import LogConfig
from config import get_logger
from pymongo.common import validate_server_api_or_none

# from todoer_api.model import APIResponse
from todoer_api.model import Task, TodoerInfo
from todoer_api.test_db import (
    TaskDatabase,
    TestDatabase,
    DataLayerException,
    get_db_con,
    CONNECTION_TYPE,
)
from todoer_api import __version__

# dictConfig(LogConfig().dict())
# logger = logging.getLogger("todoer")
logger = get_logger("todoer")


def get_db() -> TaskDatabase:
    # global TEST_DATA
    # return TEST_DATA
    return get_db_con("mongo")


# TEST_DATA = TestDatabase()
app = FastAPI()


@app.get("/api/v1/ping")
async def model_ping():
    return {"ping": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@app.get("/api/v1/info", response_model=TodoerInfo)
async def model_info():
    logger.info(f"get info")
    db = get_db()  # init DB connection
    return TodoerInfo(
        timestamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data_source=db.db_type,
        version=__version__,
    )


@app.get("/api/v1/tests/{test_id}")
async def test(test_id: int, qry: Optional[str] = None):
    logger.info(f"in test id={test_id} qry={qry}")
    return {"test_id": test_id, "q": qry}


@app.get("/api/v1/tasks", response_model=List[Task])
async def tasks():
    logger.info(f"get all tasks")
    return get_db().get_all()


@app.get("/api/v1/tasks/{task_id}", response_model=Task)
async def task_id(task_id: int):
    rslt = get_db().get(task_id)
    if len(rslt) == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if len(rslt) > 1:
        raise HTTPException(
            status_code=500, detail=f"Too many tasks found for ID {task_id}"
        )
    return rslt[0]


@app.post("/api/v1/tasks")
async def create_task(task: Task, response: Response):
    task.created = dt.datetime.now()
    try:
        rslt = get_db().add(task)
    except DataLayerException:
        raise HTTPException(
            status_code=409, detail=f"Add task {task.id} already exists"
        )
    response.status_code = 201
    return rslt


@app.delete("/api/v1/tasks/{task_id}")
async def del_task(task_id: int, response: Response):
    try:
        get_db().delete(task_id)
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Delete task {task_id} not found")
    response.status_code = 204


@app.put("/api/v1/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    task.created = dt.datetime.now()
    task.id = task_id
    try:
        return get_db().update(task)
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
