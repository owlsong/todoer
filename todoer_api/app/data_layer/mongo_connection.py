from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
)


class MongoConnection:
    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        set_client: bool = True,
        db_name: str = None,
        collection_name: str = None,
    ) -> None:
        self._username = username
        self._password = password
        self._host = host
        self.db_name = db_name
        self.collection_name = collection_name
        self._url = f"mongodb://{self._username}:{self._password}@{self._host}:27017/"
        self._client: AsyncIOMotorClient = (
            AsyncIOMotorClient(self._url) if set_client else None
        )

    def __call__(self) -> AsyncIOMotorClient:
        return self._client

    def __del__(self) -> None:
        if self._client is not None:
            self._client.close()

    def get_collection(self) -> AsyncIOMotorCollection:
        return self.client[self.db_name][self.collection]

    @property
    def url(self) -> str:
        return self._url

    @property
    def client(self) -> AsyncIOMotorClient:
        return self._client

    @client.setter
    def client(self, newValue: AsyncIOMotorClient) -> None:
        self._client = newValue
