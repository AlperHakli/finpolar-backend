# from sqlmodel import SQLModel , create_engine , Session
# from settings import settings
#
#
# # engine = create_engine(url=settings.DATABASE_URL)
# engine = create_engine(url="postgresql://postgres:admin@localhost:5432/finpolar")
#
# def create_db_table():
#     SQLModel.metadata.create_all(engine)
#
#
# def get_session():
#     with Session(engine) as session:
#         yield session

from sqlalchemy.ext.asyncio import create_async_engine , AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

engine = create_async_engine(url="postgresql+asyncpg://postgres:admin@localhost:5432/finpolar")

async def create_db_table():
    async with engine.begin() as conn:

        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncSession:
    """
    async database generator
    """
    async_session_factory = sessionmaker(engine , class_=AsyncSession , expire_on_commit=False)

    async with async_session_factory() as session:
        yield session

# TODO jobları ve endpointleri yeni async backgroundjobscheduler e göre (AsyncIOScheduler) ayarla

