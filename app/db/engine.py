import app.db.models
from sqlmodel import create_engine, SQLModel, Session

DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(
    DATABASE_URL,
    echo=False
)



def create_db_and_tables(engine_to_use = engine):
    SQLModel.metadata.create_all(engine_to_use)


def get_session(engine_to_use = engine):
    return Session(engine_to_use)
