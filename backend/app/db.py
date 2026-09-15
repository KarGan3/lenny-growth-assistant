from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Creates tables if they don't exist. For a real production rollout
    # you'd use Alembic migrations instead; kept simple here to match the
    # "one-command startup" requirement.
    from app import models  # noqa: F401  (ensures models are registered on Base)
    Base.metadata.create_all(bind=engine)
    # Additive migration for existing demo databases; preserve saved conversations.
    with engine.begin() as conn:
        columns = {c['name'] for c in inspect(conn).get_columns('chat_messages')}
        for name in ('artifacts', 'warnings'):
            if name not in columns:
                conn.execute(text(f"ALTER TABLE chat_messages ADD COLUMN {name} JSON NOT NULL DEFAULT '[]'"))
