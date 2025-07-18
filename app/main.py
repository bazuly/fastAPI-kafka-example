"""
    The provided code snippet sets up connections to Redis and Kafka with retry logic and initializes
    FastAPI with routers for different application components.
    
    :param app: The `app` parameter in the code snippet refers to an instance of the FastAPI class. It
    is used to create a FastAPI application that will serve as the main application for the project. The
    `lifespan` function is a context manager that handles the initialization and cleanup tasks for
    connecting to
    :type app: FastAPI
"""
import asyncio

import logging
from contextlib import asynccontextmanager

from aiokafka.errors import KafkaConnectionError
from redis import RedisError

from fastapi import FastAPI

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio.connection import ConnectionPool
from redis import asyncio as redis

from app.applications.handlers import router as applications_router
from app.broker.consumer import KafkaConsumer
from app.image_upload.handlers import router as image_upload_router
from app.infrastructure.database.mongo_db.accessor import (
    startup_db_client as startup_mongo_db_client,
    shutdown_db_client as shutdown_mongo_db_client,
)
from app.users.auth.handlers import router as users_router
from app.settings import get_settings

logger = logging.getLogger(__name__)
consumer = KafkaConsumer()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # redis lifespan
    retries = 10
    delay = 2

    for attempt in range(retries):
        try:
            logger.info("Attempting to connect to Redis...")
            pool = ConnectionPool.from_url(url=settings.REDIS_URL)
            r = redis.Redis(connection_pool=pool)
            await r.ping()
            FastAPICache.init(
                RedisBackend(r),
                prefix="fastapi-cache:",
                expire=60,
            )
            logger.info(
                "Successfully connected to Redis and initialized cache")
            break
        except RedisError as e:
            logger.error(
                f"Redis connection attempt {attempt + 1}/{retries} failed: {str(e)}"
            )
            if attempt == retries - 1:
                raise RuntimeError(
                    "Failed to connect to Redis after multiple attempts"
                ) from e
            await asyncio.sleep(delay)

    # kafka lifespan
    for attempt in range(retries):
        try:
            await consumer.start()
            break
        except KafkaConnectionError as e:
            print(
                f"Connection attempt {attempt + 1}/{retries} failed: {str(e)}")
            if attempt == retries - 1:
                raise RuntimeError(
                    "Failed to connect to Kafka after multiple attempts"
                ) from e
            await asyncio.sleep(delay)
            await consumer.stop()

    # mongo connection lifespan
    for attempt in range(retries):
        try:
            await startup_mongo_db_client(app)
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            if attempt == retries - 1:
                raise RuntimeError(
                    "Failed to connect to MongoDB after multiple attempts"
                ) from e
            await asyncio.sleep(delay)
            await shutdown_mongo_db_client(app)

    yield


app = FastAPI(
    lifespan=lifespan
)

app.include_router(applications_router)
app.include_router(image_upload_router)
app.include_router(users_router)
