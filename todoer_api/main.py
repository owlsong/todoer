from typing import List, Optional  # Dict,
from fastapi import FastAPI, HTTPException, Response

# from fastapi import FastAPI, status
# from fastapi import Request
# from fastapi.responses import JSONResponse
import datetime as dt
from logging.config import dictConfig
import logging
from config import LogConfig

# from todoer_api.model import APIResponse
from todoer_api.model import Task, TodoerInfo
from todoer_api.test_db import TestDatabase, TestDatabaseException

dictConfig(LogConfig().dict())
logger = logging.getLogger("todoer")


# class TodoerInfo(BaseModel):
#     timestamp: str
#     service = "Todoer"
#     version = "0.1.0"
# class Task(BaseModel):
#     id: int
#     summary: str
#     description: str
#     status: str
#     # assignee: str
#     created: Optional[dt.datetime] = None
#     tags: List[str] = []
#     # model_parameters: dict = {}
#     class Config:
#         schema_extra = {
#             "example": {
#                 "id": 1,
#                 "summary": "Example do laundry",
#                 "description": "Wask dry and fold them",
#                 "status": "WIP",
#                 "created": dt.datetime(2020, 5, 23, 7, 53, 34, 305),
#                 "tags": [],
#             }
#         }
# class APIResponse(BaseModel):
#     status: str
#     description: Optional[str] = None
#     errors: Optional[List[str]] = None


TEST_DATA = TestDatabase()
app = FastAPI()


def get_db():
    global TEST_DATA
    return TEST_DATA


# @app.exception_handler(HTTPException)
# async def random_model_exception_handler(request: Request, exc: HTTPException):
#     # convert error to a API response
#     response = APIResponse(
#         status="FAIL", description="Generic HTTP error", errors=exc.detail
#     )
#     # remove unset values
#     resp_dict = {key: val for key, val in response.dict().items() if val is not None}
#     return JSONResponse(
#         status_code=400,
#         content=resp_dict,
#     )


@app.get("/api/v1/ping")
async def model_ping():
    return {"ping": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@app.get("/api/v1/info", response_model=TodoerInfo)
async def model_ping():
    return TodoerInfo(timestamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@app.get("/api/v1/tests/{test_id}")
async def test(test_id: int, qry: Optional[str] = None):
    logger.info(f"in test id={test_id} qry={qry}")
    return {"test_id": test_id, "q": qry}


@app.get("/api/v1/tasks", response_model=List[Task])
async def tasks():
    logger.info(f"get all tasks")
    return get_db().data


@app.get("/api/v1/tasks/{task_id}", response_model=Task)
async def task_id(task_id: int):
    logger.info(f"get singular task id {task_id}")
    rslt = get_db().get(task_id)
    # logger.info(f"get singular num rslts {len(rslt)}")
    if len(rslt) == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if len(rslt) > 1:
        raise HTTPException(
            status_code=500, detail=f"Too many tasks found for IUD {task_id}"
        )
    return rslt[0]


@app.post("/api/v1/tasks")
async def create_task(task: Task, response: Response):
    task.created = dt.datetime.now()
    get_db().add(task)
    response.status_code = 201
    return task


@app.delete("/api/v1/tasks/{task_id}")
async def del_task(task_id: int, response: Response):
    try:
        get_db().delete(task_id)
    except TestDatabaseException:
        raise HTTPException(status_code=404, detail=f"Delete task {task_id} not found")
    response.status_code = 204


@app.put("/api/v1/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    task.created = dt.datetime.now()
    return get_db().update(task)
