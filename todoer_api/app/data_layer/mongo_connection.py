from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
)


class MongoConnection:
    def __init__(self, username: str, password: str, host: str) -> None:
        self._username = username
        self._password = password
        self._host = host
        self._url = f"mongodb://{self._username}:{self._password}@{self._host}:27017/"
        self._client: AsyncIOMotorClient = AsyncIOMotorClient(self._url)
        # note DONOT explicitly del self._client in dstructor - problems

    def __call__(self) -> AsyncIOMotorClient:
        return self._client

    @property
    def url(self) -> str:
        return self._url

    @property
    def client(self) -> AsyncIOMotorClient:
        return self._client

    def __str__(self) -> str:
        return f"MongoConnection:url={self._url}"


class MongoCollection:
    def __init__(
        self,
        mongo_conn: MongoConnection,
        db_name: str,
        collection_name: str,
    ) -> None:
        self._mongo_connection = mongo_conn
        self._db_name = db_name
        self._collection_name = collection_name

    def __call__(self) -> AsyncIOMotorCollection:
        return self.get_collection()

    def get_connection(self) -> MongoConnection:
        return self._mongo_connection

    def get_db(self) -> AsyncIOMotorDatabase:
        return self._mongo_connection.client[self._db_name]

    def get_collection(self) -> AsyncIOMotorCollection:
        return self._mongo_connection.client[self._db_name][self._collection_name]

    async def count_documents(self) -> int:
        return await self.get_collection().count_documents({})

    async def drop_db(self) -> None:
        await self._mongo_connection.client.drop_database(self._db_name)

    def __str__(self) -> str:
        return f"MongoCollection:db={self._db_name}, collection={self._collection_name}, mongo_connection={str(self._mongo_connection)}"
