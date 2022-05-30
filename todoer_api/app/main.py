from operator import ge
from typing import List, Optional, Tuple, Dict
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi import Request  # , Response
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import datetime as dt

from app.core.config import get_logger
from app.model.base import ObjectId
from app.model.todoerinfo import TodoerInfo
from app.model.task import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskPartialUpdate,
)
from app.data_layer.dl_exception import DataLayerException
from app.data_layer.database import (
    TaskDatabase,
    database_factory,
)
from app.data_layer.data_obj_mgr import DataObjectManager, CRUDMongoBase
from todoer_api import __version__, __service_name__

# from fastapi.encoders import jsonable_encoder
# from starlette.responses import JSONResponse

logger = get_logger("todoer")
BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates"))


# ------------------------------------------------------------------------------
# Globals
app = FastAPI()
# tehse are intiatied in the startup ans shutdown functions (must be async)
# task_db: TaskDatabase = database_factory("mongo")
# object_db: DataObjectManager = database_factory("mongo-data-obj-mgr")
task_db: TaskDatabase = None
object_db: DataObjectManager = None


# region dependencies

# async def build_database() -> TaskDatabase:
#     return database_factory("mongo")


async def get_database_v0() -> TaskDatabase:
    # !!! for some reason when trying to saccess the DB via the data layer
    # it creates an error: attached to a different loop
    # don't know why left it to a local variable in main
    return task_db


async def get_database_v2() -> DataObjectManager:
    return object_db


def pagination(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=0),
) -> Tuple[int, int]:
    capped_limit = min(100, limit)
    return (skip, capped_limit)


def pagination_dict(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=0),
) -> Dict[str, int]:
    capped_limit = min(100, limit)
    return {"skip": skip, "limit": capped_limit}


async def get_task_or_404_v0(task_key: str, database=Depends(get_database_v0)) -> Task:
    try:
        return await database.get(task_key)
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_key} not found")


async def get_task_or_404_v2(task_key: str, database=Depends(get_database_v2)) -> Task:
    task_mgr: CRUDMongoBase = database.get_object_manager("Task")
    task = await task_mgr.get_by_key("key", task_key)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_key} not found")
    return task


async def get_task_id_or_404_v0(
    task_id: str, database=Depends(get_database_v0)
) -> Task:
    try:
        return await database.get(ObjectId(task_id))
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


async def get_task_id_or_404_v2(
    task_id: str, database=Depends(get_database_v2)
) -> Task:
    task_mgr: CRUDMongoBase = database.get_object_manager("Task")
    task = await task_mgr.get(ObjectId(task_id))
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


# endregion dependencies

# region non-data


# database_builder=Depends(build_database)
@app.on_event("startup")
async def startup():
    global task_db, object_db
    task_db = database_factory("mongo")  #
    object_db = database_factory("mongo-data-obj-mgr")


@app.on_event("shutdown")
async def shutdown():
    global task_db, object_db
    del task_db
    task_db = None
    del object_db
    object_db = None


@app.get("/todoer/v1/tasks", status_code=200)
async def root(
    request: Request,
    database=Depends(get_database_v0),
    pagination: Tuple[int, int] = Depends(pagination),
) -> dict:  # 2
    """
    GET tasks as html page
    """
    tasks = await database.get_all(*pagination)
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "tasks": tasks},
    )


@app.get("/todoer/api/v1/ping")
async def model_ping():
    return {"ping": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@app.get("/todoer/api/v1/info", response_model=TodoerInfo)
async def model_info(database=Depends(get_database_v0)) -> TodoerInfo:
    logger.info(f"get info")
    return TodoerInfo(
        timestamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        service=__service_name__,
        data_source=database.db_type,
        version=__version__,
    )


@app.get("/todoer/api/v1/tests/{test_id}")
async def test(test_id: int, qry: Optional[str] = None):
    logger.info(f"in test id={test_id} qry={qry}")
    return {"test_id": test_id, "q": qry}


# endregion

# region tasks


@app.get("/todoer/api/v1/tasks")
async def get_tasks(
    pagination: Dict[str, int] = Depends(pagination_dict),
    database=Depends(get_database_v0),
) -> List[Task]:
    return await database.get_all(**pagination)


@app.get("/todoer/api/v2/tasks")
async def get_tasks_v2(
    pagination: Dict[str, int] = Depends(pagination_dict),
    database=Depends(get_database_v2),
) -> List[Task]:
    task_mgr = database.get_object_manager("Task")
    return await task_mgr.get_all(**pagination)


@app.get("/todoer/api/v1/tasks/{task_key}", response_model=Task)
async def get_task_key(task: Task = Depends(get_task_or_404_v0)) -> Task:
    # to return with id iso _id do the follwing but breaks tests
    # as rebuild from dict assume _id is present
    # retrun a JSONResponse to avoid casting back to Task which uses _id
    # tsk_dict = jsonable_encoder(task, by_alias=False)
    # return JSONResponse(content=tsk_dict)

    # to return with _id
    logger.info(f"get task by key {task.key} id = {task.id}")
    return task


@app.get("/todoer/api/v2/tasks/{task_key}", response_model=Task)
async def get_task_key_v2(task: Task = Depends(get_task_or_404_v2)) -> Task:
    # to return with id iso _id do the follwing but breaks tests
    # as rebuild from dict assume _id is present
    # retrun a JSONResponse to avoid casting back to Task which uses _id
    # tsk_dict = jsonable_encoder(task, by_alias=False)
    # return JSONResponse(content=tsk_dict)
    logger.info(f"get task by key {task.key} id = {task.id}")
    return task


@app.get("/todoer/api/v1/tasks/id/{task_id}", response_model=Task)
async def get_task_id(task: Task = Depends(get_task_id_or_404_v0)) -> Task:
    logger.info(f"get task by ID {task.id}")
    return task


@app.get("/todoer/api/v2/tasks/id/{task_id}", response_model=Task)
async def get_task_id(task: Task = Depends(get_task_id_or_404_v2)) -> Task:
    logger.info(f"get task by ID {task.id}")
    return task


@app.post("/todoer/api/v1/tasks", status_code=201, response_model=Task)
async def create_task(task: TaskCreate, database=Depends(get_database_v0)) -> Task:
    try:
        logger.info(f"request to create task in project {task.project}")
        added_task = await database.add(task)
        return added_task
    except DataLayerException:
        raise HTTPException(
            status_code=409, detail=f"Adding task key {task.key} failed, already exists"
        )


@app.post("/todoer/api/v2/tasks", status_code=201, response_model=Task)
async def create_task_v2(task: TaskCreate, database=Depends(get_database_v2)) -> Task:
    try:
        logger.info(f"request to create task in project {task.project}")
        task_mgr = database.get_object_manager("Task")
        added_task = await task_mgr.add(obj_in=task)
        return added_task
    except ValueError:
        raise HTTPException(
            status_code=409, detail=f"Adding task key {task.key} failed, already exists"
        )


@app.put("/todoer/api/v1/tasks/{task_key}", response_model=Task)
async def update_task(
    task_key: str, task: TaskUpdate, database=Depends(get_database_v0)
) -> Task:
    try:
        logger.info(f"request to update task: {task_key}")
        udp_task = await database.update(task_key, task)
        return udp_task
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_key} not found")


@app.put("/todoer/api/v2/tasks/{task_key}", response_model=Task)
async def update_task_v2(
    task_upd: TaskUpdate,
    task_orig: Task = Depends(get_task_or_404_v2),
    database=Depends(get_database_v2),
) -> Task:
    logger.info(f"request to update task: {task_orig.key}")
    task_mgr: CRUDMongoBase = database.get_object_manager("Task")
    task_new = await task_mgr.update(obj_original=task_orig, obj_update=task_upd)
    return task_new


@app.patch("/todoer/api/v1/tasks/{task_key}", response_model=Task)
async def patch_task(
    task_key: str, task: TaskPartialUpdate, database=Depends(get_database_v0)
) -> Task:
    try:
        logger.info(f"request to patch task: {task_key}")
        return await database.update(task_key, task)
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Task {task_key} not found")


@app.patch("/todoer/api/v2/tasks/{task_key}", response_model=Task)
async def patch_task_v2(
    task_upd: TaskPartialUpdate,
    task_orig: Task = Depends(get_task_or_404_v2),
    database=Depends(get_database_v2),
) -> Task:
    logger.info(f"request to patch task: {task_orig.key}")
    task_mgr: CRUDMongoBase = database.get_object_manager("Task")
    task_new = await task_mgr.update(obj_original=task_orig, obj_update=task_upd)
    return task_new


@app.delete("/todoer/api/v1/tasks/{task_key}", status_code=204)
async def del_task(task_key: str, database=Depends(get_database_v0)) -> None:
    try:
        logger.info(f"request to delete task: {task_key}")
        await database.delete(task_key)
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Delete task {task_key} not found")


@app.delete("/todoer/api/v2/tasks/{task_key}", status_code=204)
async def del_task(
    task: Task = Depends(get_task_or_404_v2), database=Depends(get_database_v2)
) -> None:
    logger.info(f"request to delete task: {task.key}")
    task_mgr: CRUDMongoBase = database.get_object_manager("Task")
    await task_mgr.delete(id=task.id)


@app.delete("/todoer/admin/v1/tasks", status_code=204)
async def del_all_task(database=Depends(get_database_v0)):
    try:
        logger.info("request to delete all tasks")
        await database.delete_all()
    except DataLayerException:
        raise HTTPException(status_code=404, detail=f"Failed to delete all tasks")


@app.delete("/todoer/admin/v2/tasks", status_code=204)
async def del_all_task(database=Depends(get_database_v2)):
    logger.info("request to delete all tasks")
    task_mgr: CRUDMongoBase = database.get_object_manager("Task")
    await task_mgr.delete_all()


# endregion
