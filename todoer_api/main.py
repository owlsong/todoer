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
from todoer_api.data_layer import (
    TaskDatabase,
    DataLayerException,
    get_db_con,
    CONNECTION_TYPE,
)
from todoer_api import __version__, __service_name__

# dictConfig(LogConfig().dict())
# logger = logging.getLogger("todoer")
logger = get_logger("todoer")


def get_db() -> TaskDatabase:
    # TODO make this a variable so don't reconnect each time
    # db_type = "mongo"
    db_type = "in_memory"
    return get_db_con(db_type)


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
        service=__service_name__,
        data_source=db.db_type,
        version=__version__,
    )


@app.get("/api/v1/tests/{test_id}")
async def test(test_id: int, qry: Optional[str] = None):
    logger.info(f"in test id={test_id} qry={qry}")
    return {"test_id": test_id, "q": qry}


@app.get("/api/v1/tasks", response_model=List[Task])
async def get_tasks():
    # TODO why does list[Task] work
    return get_db().get_all()


@app.get("/api/v1/tasks/{task_id}", response_model=Task)
async def get_task_id(task_id: int):
    try:
        rslt = get_db().get(task_id)
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return rslt.dict()


@app.post("/api/v1/tasks", status_code=201, response_model=Task)
async def create_task(task: Task):
    try:
        return get_db().add(task).dict()
    except DataLayerException:
        raise HTTPException(
            status_code=409, detail=f"Add task {task.id} already exists"
        )


@app.put("/api/v1/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task: Task):
    try:
        return get_db().update(task).dict()
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/api/v1/tasks/{task_id}", status_code=204)
async def del_task(task_id: int):
    try:
        get_db().delete(task_id)
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Delete task {task_id} not found")


@app.delete("/admin/v1/tasks", status_code=204)
async def del_task():
    try:
        get_db().delete_all()
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Failed to delete all tasks")
