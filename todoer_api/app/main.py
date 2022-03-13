from typing import List, Optional  # Dict,
from fastapi import FastAPI, HTTPException  # , Response
from fastapi.templating import Jinja2Templates
from pathlib import Path

# from fastapi import FastAPI, status
from fastapi import Request

# from fastapi.responses import JSONResponse

import datetime as dt

from app.core.config import get_logger

from pymongo.common import validate_server_api_or_none

from todoer_api.model import Task, TodoerInfo, TaskCreate, TaskUpdate, TaskPartialUpdate
from todoer_api.data_layer import (
    TaskDatabase,
    DataLayerException,
    get_db,
    CONNECTION_TYPE,
)
from todoer_api import __version__, __service_name__

logger = get_logger("todoer")
BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates"))


app = FastAPI()


@app.get("/todoer/v1/tasks", status_code=200)
def root(request: Request) -> dict:  # 2
    """
    GET tasks as html page
    """
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "tasks": get_db().get_all()},
    )


@app.get("/todoer/api/v1/ping")
async def model_ping():
    return {"ping": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@app.get("/todoer/api/v1/info", response_model=TodoerInfo)
async def model_info() -> TodoerInfo:
    logger.info(f"get info")
    db = get_db()  # init DB connection
    return TodoerInfo(
        timestamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        service=__service_name__,
        data_source=db.db_type,
        version=__version__,
    )


@app.get("/todoer/api/v1/tests/{test_id}")
async def test(test_id: int, qry: Optional[str] = None):
    logger.info(f"in test id={test_id} qry={qry}")
    return {"test_id": test_id, "q": qry}


@app.get("/todoer/api/v1/tasks", response_model=List[Task])
async def get_tasks() -> List[Task]:
    vals = get_db().get_all()
    logger.info(f"request to get all tasks num={len(vals)}")
    return vals


@app.get("/todoer/api/v1/tasks/{task_key}", response_model=Task)
async def get_task_id(task_key: str) -> Task:
    try:
        logger.info(f"request to get task: {task_key}")
        task = get_db().get(task_key)
        logger.info(f"response to get task key: {task.key}")
        return task
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_key} not found")


@app.post("/todoer/api/v1/tasks", status_code=201, response_model=Task)
async def create_task(task: TaskCreate) -> Task:
    try:
        logger.info(f"request to create task in project {task.project}")
        added_task = get_db().add(task)
        logger.info(f"created task: {added_task.key}")
        return added_task
    except DataLayerException:
        raise HTTPException(
            status_code=409, detail=f"Add task {task.id} already exists"
        )


@app.put("/todoer/api/v1/tasks/{task_key}", response_model=Task)
async def update_task(task_key: str, task: TaskUpdate) -> Task:
    try:
        logger.info(f"request to update task: {task_key}")
        udp_task = get_db().update(task_key, task)
        logger.info(f"updated task: {udp_task.key}")
        return udp_task
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_key} not found")


@app.patch("/todoer/api/v1/tasks/{task_key}", response_model=Task)
async def patch_task(task_key: str, task: TaskPartialUpdate) -> Task:
    try:
        logger.info(f"request to patch task: {task_key}")
        return get_db().update(task_key, task)
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_key} not found")


@app.delete("/todoer/api/v1/tasks/{task_key}", status_code=204)
async def del_task(task_key: str) -> None:
    try:
        logger.info(f"request to delete task: {task_key}")
        get_db().delete(task_key)
        logger.info(f"deleted task: {task_key}")
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Delete task {task_key} not found")


@app.delete("/todoer/admin/v1/tasks", status_code=204)
async def del_all_task():
    try:
        get_db().delete_all()
        logger.info(f"deleted all tasks")
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Failed to delete all tasks")
