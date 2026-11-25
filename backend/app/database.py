"""Database connection.

DATABASE_URL comes from the environment (.env locally, dashboard env vars in
production). If it is not set we fall back to a local SQLite file, so the app
runs with zero setup on a laptop. In production it points to PostgreSQL (Neon),
which keeps data safe across server restarts.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


def _normalise_url(url: str) -> str:
    # Neon/Render give "postgres://" or "postgresql://" URLs; SQLAlchemy needs
    # the driver name, and we use psycopg (v3).
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


DATABASE_URL = _normalise_url(os.getenv("DATABASE_URL") or "sqlite:///./patients.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping re-checks connections before use (Neon closes idle connections).
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: one DB session per request, always closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
