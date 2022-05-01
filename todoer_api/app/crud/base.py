""" Generic class for CRUD operations for data persistence in a Mongo DB. """

from re import S
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
import datetime as dt

from fastapi.encoders import jsonable_encoder
from httpcore import ReadTimeout
from pydantic import BaseModel

# this is the db connector replaced by connection
# from sqlalchemy.orm import Session
# this is the sqlalchemy base class - not needed
# from app.db.base_class import Base
from todoer_api.data_layer import MongoConnection

# ModelType = TypeVar("ModelType", bound=Base)
ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, db: MongoConnection, id: Any) -> Optional[ModelType]:
        """Returns an object given its ID or `None` if it does not exist.
        **Parameters**
        * `db`: The database connection
        * `id`: The ID of the object to get
        **Returns**
        * `obj`: The object or `None` if it does not exist
        """
        raw_obj = await db.get_collection().find_one({"id": id})
        return ModelType(**raw_obj) if raw_obj is not None else None
        # item_list = [Task(**raw_task) async for raw_task in query]
        # num = len(item_list)
        # if must_be_equal_to is not None and must_be_equal_to != num:
        #     raise DataLayerException(
        #         f"Error expected {must_be_equal_to} task(s) with ID {task_id} but had {num} occurance(s)"
        #     )
        # return item_list
        # return db.query(self.model).filter(self.model.id == id).first()

    async def filter_one(
        self, db: MongoConnection, filter: Dict
    ) -> Optional[ModelType]:
        """Returns an object given a filter or `None` if it does not exist.
        **Parameters**
        * `db`: The database connection
        * `filter`: The filter to apply to find one object
        * `id`: The ID of the object to get
        **Returns**
        * `obj`: The object or `None` if it does not exist
        """
        raw_obj = await db.get_collection().find_one(filter)
        return ModelType(**raw_obj) if raw_obj is not None else None

    async def filter_multi(
        self,
        db: MongoConnection,
        filter: Dict,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = None,
        sort_ascending: bool = True
    ) -> List[ModelType]:
        # 1 = ascending, -1 = descending
        query = db.get_collection().find(filter, skip=skip, limit=limit)
        if sort_field is not None:
            query = query.sort(sort_field, 1 if sort_ascending else -1)
        results = [ModelType(**raw_obj) async for raw_obj in query]
        return results
        # return db.query(self.model).offset(skip).limit(limit).all()

    async def get_multi(
        self,
        db: MongoConnection,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = None,
        sort_ascending: bool = True
    ) -> List[ModelType]:
        # 1 = ascending, -1 = descending
        # query = db.get_collection().find(
        #     {}, skip=skip, limit=limit
        # )  # .sort({"key": 1})
        # if sort_field is not None:
        #     query = query.sort({sort_field: 1})
        # results = [ModelType(**raw_obj) async for raw_obj in query]
        # return results
        return await self.filter_multi(
            db,
            {},
            skip=skip,
            limit=limit,
            sort_field=sort_field,
            sort_ascending=sort_ascending,
        )

    async def create(
        self, db: MongoConnection, *, obj_in: CreateSchemaType
    ) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)

        # not needed as done by model defaults
        # time_now = dt.datetime.now()
        # obj_in_data["updated"] = time_now
        # obj_in_data["created"] = time_now

        # TODO!!! add seq via kwargs
        # for k, v in kwargs.items():
        #     obj_in_data[k] = v

        db_obj = self.model(**obj_in_data)  # type: ignore

        result = await db.insert_one(db_obj.dict(by_alias=True))
        # logger.info(f"Inserted task id {str(result.inserted_id)} key {new_key}")
        return await self.get(db, db_obj.id)

    async def update(
        self,
        db: MongoConnection,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        # convert obj_in -> dict as update_data
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        # ensure update set to now and do not allow created to be modified
        update_data["updated"] = dt.datetime.now()
        if "created" in update_data:
            del update_data["created"]

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        await db.update_one(
            {"_id": db_obj.id},
            {"$set": db_obj.dict(by_alias=True, exclude_unset=True)},
        )
        return await self.get(db, db_obj.id)

    async def remove(self, db: MongoConnection, *, id: Any) -> ModelType:
        obj = self.get(db, id)
        await db.delete_one({"id": id})
        return obj

    async def remove_all(self, db: MongoConnection) -> None:
        await self.tasks.delete_many({})
