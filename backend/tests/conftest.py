import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

# Schema tối thiểu cho test integration (khớp migration 0001 + activity_logs).
_SCHEMA_DDL = [
    "CREATE TABLE tenants (id uuid PRIMARY KEY, slug text UNIQUE, name text, "
    "status text DEFAULT 'active')",
    "CREATE TABLE users (id uuid PRIMARY KEY, tenant_id uuid NOT NULL, username text, "
    "password_hash text, role text, status text DEFAULT 'active', "
    "must_change_password boolean DEFAULT true)",
    "ALTER TABLE users ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE users FORCE ROW LEVEL SECURITY",
    "CREATE POLICY tenant_isolation ON users "
    "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
    "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)",
    "CREATE TABLE activity_logs ("
    "id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid, actor_id uuid, "
    "actor_role text, action text, module text, entity_type text, entity_id uuid, "
    "entity_label text, diff jsonb, at timestamptz DEFAULT now())",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON users, tenants TO app_user",
    "GRANT SELECT, INSERT ON activity_logs TO app_user",
]


@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer(
        "postgres:16", username="edmicro_owner", password="devpass", dbname="edmicro"
    ) as pg:
        yield pg


@pytest_asyncio.fixture(scope="session")
async def app_engine(pg_container):
    owner_dsn = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    owner_engine = create_async_engine(owner_dsn)
    async with owner_engine.begin() as conn:
        await conn.execute(
            text(
                "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='app_user') "
                "THEN CREATE ROLE app_user LOGIN PASSWORD 'appdevpass' NOBYPASSRLS; END IF; END $$;"
            )
        )
        for stmt in _SCHEMA_DDL:
            await conn.execute(text(stmt))
    await owner_engine.dispose()

    app_dsn = owner_dsn.replace("edmicro_owner:devpass", "app_user:appdevpass")
    engine = create_async_engine(app_dsn)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(app_engine):
    return async_sessionmaker(app_engine, expire_on_commit=False)
