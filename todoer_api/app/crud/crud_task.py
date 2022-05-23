from typing import Optional
from app.crud.base import CRUDMongoBase, MongoCollection
from app.model.task import TaskCreate, TaskUpdate, Task
from app.data_layer.id_generator import TaskIdGenerator
from fastapi.encoders import jsonable_encoder

# from app.schemas.task import TaskCreate, TaskUpdate  # Pydantic models/schemas


class CRUDTask(CRUDMongoBase[Task, TaskCreate, TaskUpdate]):
    def __init__(self, model: Task, db: MongoCollection, id_gen: TaskIdGenerator):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `db`: A connetionc to the DB for persistence
        * `id_gen`: ID generator needed for the seq and key.
        """
        super.__init__(model, db)
        self.id_gen = id_gen

    async def add(self, *, obj_in: TaskCreate) -> Task:
        new_id = await self.id_gen.get_next_id(obj_in.project)
        new_data = obj_in.get_dict_inc_seq(new_id)
        new_task = Task(**new_data)
        new_key = new_task.key

        if await self.get_by_key(key=new_key) is not None:
            raise ValueError(
                f"Error in creating task the key {new_key} already exists!"
            )

        result = await self.tasks.insert_one(new_task.dict(by_alias=True))
        return await self.get(result.inserted_id)
