from app.crud.base import CRUDBase
from app.model.task import TaskCreate, TaskUpdate, Task

# from app.schemas.task import TaskCreate, TaskUpdate  # Pydantic models/schemas


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    ...


task = CRUDTask(Task)
