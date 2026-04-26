from sqlmodel import SQLModel , create_engine , Session
import os


engine = create_engine(url=os.getenv("database_url"))

def create_db_table():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session