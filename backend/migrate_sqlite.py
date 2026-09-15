"""Copy existing SQLite chats into the configured database, keeping SQLite intact."""
from sqlalchemy import create_engine, select

from app.db import Base, engine, init_db
from app import models  # noqa: F401


def migrate():
    if engine.url.get_backend_name() != 'postgresql':
        raise SystemExit('Set DATABASE_URL to PostgreSQL before migrating.')
    source = create_engine('sqlite:///./data/app.db')
    init_db()
    copied = 0
    with source.connect() as old, engine.begin() as new:
        for table in Base.metadata.sorted_tables:
            for row in old.execute(select(table)).mappings():
                if not new.execute(select(table.c.id).where(table.c.id == row['id'])).first():
                    new.execute(table.insert().values(**dict(row)))
                    copied += 1
    print(f'Copied {copied} rows to PostgreSQL. SQLite remains intact.')


if __name__ == '__main__':
    migrate()
