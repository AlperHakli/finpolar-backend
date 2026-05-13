from sqlalchemy.ext.asyncio import create_async_engine , AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from contextlib import asynccontextmanager
from settings import settings



engine = create_async_engine(url=settings.DATABASE_URL)

async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_db_table():
    async with engine.begin() as conn:

        await conn.run_sync(SQLModel.metadata.create_all)


# @asynccontextmanager
# async def get_postresql_session() -> AsyncSession:
#     """
#     async database session context manager for cron jobs
#     """
#
#
#     async with async_session_factory() as session:
#         yield session


