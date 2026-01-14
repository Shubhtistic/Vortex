# Engine-> The always-open connection pool to Postgres
# Session -> A temporary workspace for a single request, When a user asks for data, we open a session.
# When the request is done, we closw it

from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings


engine = create_engine(settings.DATABASE_URL)


def get_session():
    #our db session after yield it closes
    with Session(engine) as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
