from app.models import task
from fastapi import (
    FastAPI,
    APIRouter,
    HTTPException,
    Request,
    Depends,
    Query,
)  # , Response
from fastapi.templating import Jinja2Templates

from typing import Dict, List, Optional, Any  # Dict,
from pathlib import Path
from sqlalchemy.orm import Session

from app.schemas.task import TaskSearchResults, Task, TaskCreate, TaskUpdate
from app.schemas.task import TodoerInfo
from app import deps
from app import crud


# ------------------------------------------------------------------------------
# >>> extras
from fastapi import Request

# from fastapi.responses import JSONResponse
# from fastapi.responses import JSONResponse
import datetime as dt
from app.core.config import get_logger

# from pymongo.common import validate_server_api_or_none
# from app.models import Task, TodoerInfo
# from todoer_api.data_layer import (
#     TaskDatabase,
#     DataLayerException,
#     get_db_con,
#     CONNECTION_TYPE,
# )
from todoer_api import service_version, service_name, data_source, api_version


logger = get_logger("todoer")
# <<< extras

BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates"))

# ------------------------------------------------------------------------------

# def get_db() -> TaskDatabase:
#     # TODO make this a variable so don't reconnect each time
#     db_type = "mongo"
#     # db_type = "in_memory"
#     return get_db_con(db_type)


app = FastAPI(title=f"{service_name} API")
api_prefix = f"/{service_name.lower()}/api/v{api_version}"
api_router = APIRouter(prefix=api_prefix)


# @api_router.get("/tasks", status_code=200)
# def get_tasks_page(
#     request: Request,
#     db: Session = Depends(deps.get_db),
# ) -> dict:  # 2
#     """
#     GET tasks as html page
#     """
#     logger.info(f"get tasks html page")
#     tasks = crud.tasks.get_multi(db=db, limit=10)
#     return TEMPLATES.TemplateResponse(
#         "index.html",
#         {"request": request, "tasks": tasks},
#     )


@api_router.get("/ping", status_code=200)
async def model_ping() -> dict:
    logger.info(f"get ping")
    return {"ping": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@api_router.get("/info", status_code=200, response_model=TodoerInfo)
async def model_info():
    logger.info(f"get info")
    return TodoerInfo(
        timestamp=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        service=service_name,
        data_source=data_source,
        version=service_version,
        api_version=api_version,
    )


@api_router.get("/tests/{test_id}", status_code=200)
async def test(test_id: int, qry: Optional[str] = None):
    logger.info(f"in test id={test_id} qry={qry}")
    return {"test_id": test_id, "q": qry}


@api_router.get("/tasks/{task_id}", status_code=200, response_model=Task)
async def get_task_by_id(
    *,
    task_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch a single task by ID
    """
    result = crud.task.get(db=db, id=task_id)
    if not result:
        # the exception is raised, not returned - you will get a validation
        # error otherwise.
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

    return result


@api_router.get("/tasks", status_code=200, response_model=TaskSearchResults)
async def get_tasks(
    *,
    keyword: Optional[str] = Query(None, min_length=3, example="shopping"),
    max_results: Optional[int] = 10,
    db: Session = Depends(deps.get_db),
) -> dict:
    tasks = crud.task.get_multi(db=db, limit=max_results)
    if not keyword:
        return {"results": tasks[:max_results]}
    results = filter(lambda task: keyword.lower() in task.summary.lower(), tasks)
    return {"results": list(results)[:max_results]}
    # TODO seperate search from get all


@api_router.post("/tasks", status_code=201, response_model=Task)
async def create_task(
    *, task_in: TaskCreate, db: Session = Depends(deps.get_db)
) -> dict:
    """
    Create a new task in the database.
    """
    task = crud.task.create(db=db, obj_in=task_in)
    return task


@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    *, task_id: int, updated_task: TaskUpdate, db: Session = Depends(deps.get_db)
):
    curr_task = crud.task.get(db=db, id=task_id)
    if not curr_task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

    updated_task = crud.task.update(db=db, db_obj=curr_task, obj_in=updated_task)
    return updated_task


@api_router.delete("/tasks/{task_id}", status_code=200, response_model=Task)
async def del_task(*, task_id: int, db: Session = Depends(deps.get_db)) -> dict:
    curr_task = crud.task.get(db=db, id=task_id)
    if not curr_task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    del_task = crud.task.remove(db, id=task_id)
    return del_task


admin_router = APIRouter(
    prefix=f"/{service_name.lower()}/admin/v{api_version}", tags=["admin"]
)


@admin_router.delete("/tasks", status_code=204)
async def del_all_tasks(*, db: Session = Depends(deps.get_db)) -> None:
    crud.task.remove_all(db)


app.include_router(api_router)
app.include_router(admin_router)
