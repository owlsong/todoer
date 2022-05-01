from app.crud.base import CRUDBase
from app.models.task import Task  # DB model
from app.schemas.task import TaskCreate, TaskUpdate  # Pydantic models/schemas


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    ...


task = CRUDTask(Task)
