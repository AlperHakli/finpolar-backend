from sqlmodel import SQLModel , create_engine , Session
from settings import settings


# engine = create_engine(url=settings.DATABASE_URL)
engine = create_engine(url="postgresql://admin:admin@localhost:5432/finpolar")

def create_db_table():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session