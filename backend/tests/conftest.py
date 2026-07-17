import os
from pathlib import Path

import psycopg2
import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from alembic import command

_BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def pg_dsn():
    """Dựng Postgres 1 lần/session; tạo role app_user (NOBYPASSRLS) rồi chạy
    Alembic migration thật (schema test == production). Trả DSN cho app_user."""
    with PostgresContainer(
        "postgres:16", username="edmicro_owner", password="devpass", dbname="edmicro"
    ) as pg:
        owner_url = pg.get_connection_url()  # postgresql+psycopg2://...
        owner_raw = owner_url.replace("postgresql+psycopg2://", "postgresql://")

        conn = psycopg2.connect(owner_raw)
        conn.autocommit = True
        conn.cursor().execute(
            "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='app_user') "
            "THEN CREATE ROLE app_user LOGIN PASSWORD 'appdevpass' NOBYPASSRLS; END IF; END $$;"
        )
        conn.close()

        # Chạy migration bằng role owner (env.py đọc MIGRATION_DATABASE_URL)
        os.environ["MIGRATION_DATABASE_URL"] = owner_raw
        cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
        command.upgrade(cfg, "head")

        yield owner_raw.replace("edmicro_owner:devpass", "app_user:appdevpass")


@pytest_asyncio.fixture
async def app_engine(pg_dsn):
    engine = create_async_engine(pg_dsn.replace("postgresql://", "postgresql+asyncpg://"))
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(app_engine):
    return async_sessionmaker(app_engine, expire_on_commit=False)
