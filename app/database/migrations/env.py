import asyncio
import pathlib
import sys
from copy import copy
from logging.config import fileConfig

import sqlalchemy as sa
from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy_utils import database_exists
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy_utils.functions import quote

from app.core.config import get_app_settings

from app.models.rwmodel import RWModel

# User

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

SETTINGS = get_app_settings()
DATABASE_URL = SETTINGS.db_url

config = context.config

fileConfig(config.config_file_name)

target_metadata = RWModel.metadata


print(target_metadata, 'this is  target metadata')

config.set_main_option("sqlalchemy.url", str(DATABASE_URL))


async def create_database_if_not_exists(url: str):
    # Check if database exists
    print(url, 'this is url')
    url = make_url(url)
    database = url.database
    print(database, 'this is database')
    url = url.set(database=None)  # Connect without specifying the database
    print(url, 'hu url')
    url = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=None  # Connect without specifying a database
    )
    # Create an async engine
    engine = create_async_engine(str(url))

    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
            {"database_name": database}
        )
        database_exists = result.scalar() is not None

    if not database_exists:
        print(f"Database {database} does not exist. Creating...")

        # Switch to `template1` to create the database
        url.set(database="template1")
        template = "template0"
        encoding = "utf-8"

        engine = create_async_engine(str(url), isolation_level="AUTOCOMMIT")
        async with engine.connect() as conn:
            await conn.execute(
                text(f"CREATE DATABASE {database} ENCODING '{encoding}' TEMPLATE {template}")
            )
        print(f"Database {database} created successfully.")

    else:
        print(f"Database {database} already exists.")


# Example usage
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


asyncio.run(create_database_if_not_exists(str(DATABASE_URL)))

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
