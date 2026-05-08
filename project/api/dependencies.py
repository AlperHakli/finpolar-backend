from project.api.database import async_session_factory
from project.api.redis_client import RedisClient

from fastapi import Depends
from typing import AsyncIterator , Annotated
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

async def get_postresql_db() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency automatically connects postresql db and closes the connection
    """

    async with async_session_factory() as session:
        yield session

get_postresql_db_ctx = asynccontextmanager(get_postresql_db)


async def get_redis_db(request: Request) -> RedisClient:
    """
    FastAPI dependency return state.redis
    """
    return request.app.state.redis

PostreSqlDbDep = Annotated[AsyncIterator[AsyncSession] , Depends(get_postresql_db)]

RedisDbDep = Annotated[RedisClient , Depends(get_redis_db)]