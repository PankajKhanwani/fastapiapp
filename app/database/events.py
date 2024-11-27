import logging

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core import settings
from app.core.settings.app import AppSettings

logger = logging.getLogger(__name__)

db_client: AsyncIOMotorClient = None


# engine = create_async_engine(url=str(settings.db_url), pool_size=50, max_overflow=0, echo=True, future=True)
#     async_session_factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=True)
#     app.state.pool = async_session_factory


class MongoAPI(object):
    settings: AppSettings

    def __init__(self, conn_str: str = None, db_name: str = None):
        # Initialize client and DB
        MONGO_DB_URL = f'mongodb://{settings.db_username}:' \
                       f'{settings.db_password}@{settings.db_host}:' \
                       f'{settings.db_port}'

        conn_str = conn_str if conn_str else MONGO_DB_URL
        db_name = db_name if db_name else settings.db_name

        self.conn_str = conn_str
        self._client = AsyncIOMotorClient(self.conn_str)
        self._db = self._client[db_name]

    @property
    def db(self):
        if self._db is None:
            self._db = self._client[settings.db_name]
        return self._db

    @property
    def client(self):
        if not self._client:
            self._client = AsyncIOMotorClient(
                self._conn_str)
        return self._client

    async def create_capped_collection(self, collection_name, max_size_bytes, max_count):
        collection_names = await self._db.list_collection_names()
        if collection_name in collection_names:
            logging.info(f"Collection {collection_name} detected")
            return
        await self._db.create_collection(collection_name, size=max_size_bytes, capped=True, max=max_count)


async def get_db() -> AsyncIOMotorClient:
    db_name = settings.db_name
    return db_client[db_name]


async def connect_to_db(app: FastAPI, settings: AppSettings) -> None:
    global db_client
    try:
        db_client = AsyncIOMotorClient(
            settings.db_url,
            username=settings.db_username,
            password=settings.db_password,
            maxPoolSize=settings.db_max_connections,
            minPoolSize=settings.db_mix_connections,
            uuidRepresentation="standard",
        )
        logging.info('Connected to mongo.')
    except Exception as e:
        logging.exception(f'Could not connect to mongo: {e}')
        raise


async def close_db_connection(app: FastAPI) -> None:
    global db_client
    if db_client is None:
        logging.warning('Connection is None, nothing to close.')
        return
    db_client.close()
    db_client = None
    logging.info('Mongo connection closed.')
