from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_database_url, sql_echo_enabled

database_url = get_database_url()

connect_args = {}
if database_url.get_backend_name() == "mysql":
    connect_args["connect_timeout"] = 5
elif database_url.get_backend_name() == "sqlite":
    connect_args["check_same_thread"] = False

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=sql_echo_enabled(),
    connect_args=connect_args,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
