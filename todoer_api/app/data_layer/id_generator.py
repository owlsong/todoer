# import imp
# from sqlite3 import connect
import datetime as dt
from typing import Any, List, Union

# from app.core.config import get_logger
# from motor.motor_asyncio import (
#     AsyncIOMotorClient,
#     AsyncIOMotorCollection,
# )
# from fastapi.encoders import jsonable_encoder
from pymongo import ReturnDocument
from app.core.config import get_logger
from app.model.base import ObjectId
from app.model.task import Task, TaskCreate, TaskPartialUpdate, TaskUpdate
from .mongo_connection import MongoConnection
from .dl_exception import DataLayerException

logger = get_logger("data layer")


class TaskIdGenerator:
    """Class to generate ids for tasks."""

    INIT_VALUE = 1

    def get_next_id(self, index: Any) -> int:
        pass


class TaskIdGeneratorMogo(TaskIdGenerator):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        # self.client = kwargs["client"]
        # self.db_name = kwargs["db_name"]
        self.collection_name = "id_generator"
        # self.db = self.client[self.db_name]
        self.db = kwargs["db"]
        self.id_collection = self.db[self.collection_name]
        # each item of form: { "index": "project-x", "next_id": 23 }

    async def get_next_id(self, index: str) -> int:
        rslt = await self.id_collection.find_one_and_update(
            {"index": index},
            {"$inc": {"next_id": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return rslt["next_id"]

    async def get_next_id_deprecated(self, index: str) -> int:
        index_dict = {"index": index}
        id_list = list(self.id_collection.find(index_dict))

        indexed_dict = await self.id_collection.find_one(index_dict)

        if indexed_dict is None:
            # no IDs allocated yet -> current=0 next=1
            insert_dict = index_dict
            insert_dict["next_id"] = self.INIT_VALUE + 1
            self.id_collection.insert_one(insert_dict)
            return self.INIT_VALUE
        else:
            # upd_dict = indexed_dict
            curr_id = indexed_dict["next_id"]
            indexed_dict["next_id"] = curr_id + 1
            self.id_collection.replace_one(index_dict, indexed_dict)
            return curr_id


class TaskIdGeneratorInmem(TaskIdGenerator):
    def __init__(self) -> None:
        super().__init__()
        # id indexed by: user: str, project: str
        self.ids = {}

    def get_next_id(self, index: Any) -> int:
        # # index = (user, project)
        # index = project
        try:
            rslt = self.ids[index]
            self.ids[index] = rslt + 1
            return rslt
        except KeyError:
            self.ids[index] = self.INIT_VALUE + 1
            return self.INIT_VALUE