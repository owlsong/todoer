""" Generic class for CRUD operations for data persistence in a Mongo DB. """
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
import datetime as dt
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from app.model.base import ObjectId
from app.data_layer.mongo_connection import MongoCollection
from re import S

# from httpcore import ReadTimeout


ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDMongoBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic class to manage data obejct of type ModelType, with special types for create/update."""

    def __init__(self, model: Type[ModelType], collection: MongoCollection):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        self.db_collection = collection
        self._collection = self.db_collection.get_collection()

    async def get(self, id: ObjectId) -> Optional[ModelType]:
        """Returns an object given its ID or `None` if it does not exist.
        **Parameters**
        * `id`: The ID of the object to get
        **Returns**
        * `obj`: The object or `None` if it does not exist
        """
        raw_obj = await self._collection.find_one({"_id": id})
        return self.model(**raw_obj) if raw_obj is not None else None

    async def get_by_key(self, key_name: str, key_value: Any) -> Optional[ModelType]:
        """Returns an object given key value or `None` if it does not exist (assuming the key is unique).
        **Parameters**
        * `id`: The ID of the object to get
        **Returns**
        * `obj`: The object or `None` if it does not exist
        """
        raw_obj = await self._collection.find_one({key_name: key_value})
        return self.model(**raw_obj) if raw_obj is not None else None

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = None,
        sort_ascending: bool = True
    ) -> List[ModelType]:
        return await self.filter_multi(
            {},
            skip=skip,
            limit=limit,
            sort_field=sort_field,
            sort_ascending=sort_ascending,
        )

    async def filter_one(self, filter: Dict) -> Optional[ModelType]:
        """Returns an object given a filter or `None` if it does not exist.
        **Parameters**
        * `filter`: The filter to apply to find one object
        * `id`: The ID of the object to get
        **Returns**
        * `obj`: The object or `None` if it does not exist
        """
        # CHECK: new method

        raw_obj = await self._collection.find_one(filter)
        return self.model(**raw_obj) if raw_obj is not None else None

    async def filter_multi(
        self,
        filter: Dict,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = None,
        sort_ascending: bool = True
    ) -> List[ModelType]:
        # 1 = ascending, -1 = descending
        query = self._collection.find(filter, skip=skip, limit=limit)
        if sort_field is not None:
            query = query.sort(sort_field, 1 if sort_ascending else -1)
        return [self.model(**raw_obj) async for raw_obj in query]
        # query = (
        #     self.db_collection.get_collection()
        #     .find(filter, skip=skip, limit=limit)
        #     .sort("key", 1)
        # )
        # results = [self.model(**raw_object) async for raw_object in query]
        # return results

    async def add(self, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)

        # datetimes not needed as done by model defaults
        db_obj = self.model(**obj_in_data)  # type: ignore

        result = await self._collection.insert_one(db_obj.dict(by_alias=True))
        # logger.info(f"Inserted task id {str(result.inserted_id)} key {new_key}")
        return await self.get(result.inserted_id)

    async def update(
        self,
        *,
        obj_original: ModelType,
        obj_update: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(obj_original)
        # convert obj_in -> dict as update_data
        if isinstance(obj_update, dict):
            update_data = obj_update
        else:
            update_data = obj_update.dict(exclude_unset=True)

        # ensure update set to now and do not allow created to be modified
        update_data["updated"] = dt.datetime.now()
        if "created" in update_data:
            del update_data["created"]

        for field in obj_data:
            if field in update_data:
                setattr(obj_original, field, update_data[field])

        await self._collection.update_one(
            {"_id": obj_original.id},
            {"$set": obj_original.dict(by_alias=True, exclude_unset=True)},
        )
        return await self.get(obj_original.id)

    async def delete(self, *, id: Any) -> ModelType:
        obj = self.get(id)
        await self._collection.delete_one({"_id": id})
        return obj

    async def delete_all(self) -> None:
        await self._collection.delete_many({})
