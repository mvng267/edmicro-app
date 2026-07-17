# Milestone 0 — Nền tảng (Foundation) Implementation Plan

**Trạng thái thực thi:** ✅ HOÀN TẤT 2026-07-17 — backend 7 test + E2E 2 test PASS; login owner chạy thật tại bright.localhost. Khác biệt so plan: port dev 5433/6380/8010/3001 (tránh xung đột edmicro-tools); HeroUI v3 (compound components); CORS middleware bổ sung; pyright hoãn sang M1 (chạy ruff+import-linter trong CI).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dựng bộ khung monorepo chạy được với 1 lát cắt dọc: đăng nhập bằng tài khoản `owner` đã seed trên subdomain tenant, JWT + refresh, và **RLS chứng minh chặn rò rỉ chéo tenant** — cùng CI, activity-log core, và trang login Next.js/HeroUI.

**Architecture:** Modular monolith. Backend FastAPI (async SQLAlchemy 2.0 + asyncpg) kết nối Postgres bằng role **không bypass RLS**; mỗi request đặt `app.tenant_id` qua `set_config(...)` để RLS lọc. Migration chạy bằng role owner (đủ quyền DDL). Frontend Next.js App Router resolve tenant từ subdomain ở middleware, gọi API qua client sinh từ OpenAPI. Test integration chạy trên **Postgres thật** qua testcontainers.

**Tech Stack:** uv · FastAPI · SQLAlchemy 2.0 async · asyncpg · Alembic · argon2-cffi · PyJWT · pydantic-settings · pytest + testcontainers · Next.js 15 + HeroUI + pnpm + Biome · @hey-api/openapi-ts · Docker Compose · just · GitHub Actions.

---

## File Structure (M0 tạo ra)

```
edmicro-app/
├── .gitignore
├── justfile
├── docker-compose.yml
├── infra/postgres/init/00-app-role.sql       # tạo role app_user NOBYPASSRLS
├── backend/
│   ├── pyproject.toml                          # uv + ruff + pyright + import-linter + pytest
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py                             # FastAPI app, mount routers, middleware
│   │   ├── config.py                           # Settings (pydantic-settings)
│   │   ├── db.py                               # async engine, session, tenant context
│   │   ├── core/
│   │   │   ├── security.py                     # argon2 hash + JWT
│   │   │   ├── tenant.py                        # middleware set app.tenant_id
│   │   │   ├── audit.py                         # audit_logs writer
│   │   │   └── activity_log.py                 # interceptor activity log (async)
│   │   └── modules/
│   │       ├── health/router.py
│   │       ├── authz/{router,service,repository,schemas,models}.py
│   │       └── org/models.py                    # tenants, users (M0 chỉ models + migration)
│   ├── alembic/versions/0001_initial.py
│   └── tests/
│       ├── conftest.py                          # testcontainers Postgres fixture
│       ├── test_health.py
│       ├── test_rls_isolation.py                # ★ test cách ly tenant
│       ├── test_security.py
│       └── test_auth_login.py
├── frontend/
│   ├── package.json  biome.json  next.config.ts  middleware.ts
│   └── app/(auth)/login/page.tsx
├── packages/api-client/                        # sinh từ OpenAPI
├── scripts/seed.py                             # 1 tenant + 1 owner
└── .github/workflows/ci.yml
```

---

## Task 1: Khởi tạo repo + gitignore + git

**Files:**
- Create: `.gitignore`, `README.md`

- [ ] **Step 1: Khởi tạo git + cấu trúc thư mục**

```bash
cd /home/mvng/edmicro-app
git init -b main
mkdir -p backend/app/core backend/app/modules infra/postgres/init frontend packages scripts .github/workflows
```

- [ ] **Step 2: Tạo `.gitignore`**

```gitignore
# Python
__pycache__/
*.pyc
.venv/
.pytest_cache/
.ruff_cache/
# Node
node_modules/
.next/
.turbo/
# Env & secrets
.env
.env.*
!.env.example
# Data
pgdata/
minio-data/
```

- [ ] **Step 3: README trỏ về docs**

```markdown
# Edmicro App

LMS B2B đa ngôn ngữ cho trung tâm ngoại ngữ. Tài liệu: [docs/README.md](docs/README.md). Kế hoạch: [docs/superpowers/plans/2026-07-17-roadmap.md](docs/superpowers/plans/2026-07-17-roadmap.md).

Chạy dev: `just dev`. Test: `just test`.
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore README.md
git commit -m "chore: init repo skeleton"
```

---

## Task 2: Hạ tầng dev — docker-compose + justfile + postgres role

**Files:**
- Create: `docker-compose.yml`, `justfile`, `infra/postgres/init/00-app-role.sql`, `.env.example`

- [ ] **Step 1: `.env.example`**

```bash
# Postgres — migration dùng owner, app dùng app_user (không bypass RLS)
POSTGRES_DB=edmicro
POSTGRES_USER=edmicro_owner
POSTGRES_PASSWORD=devpass
APP_DB_USER=app_user
APP_DB_PASSWORD=appdevpass
# DSN app dùng (async)
DATABASE_URL=postgresql+asyncpg://app_user:appdevpass@localhost:5432/edmicro
# DSN migration (sync, quyền DDL)
MIGRATION_DATABASE_URL=postgresql://edmicro_owner:devpass@localhost:5432/edmicro
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=dev-secret-change-me
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=2592000
```

- [ ] **Step 2: Postgres init — tạo app_user NOBYPASSRLS**

Create `infra/postgres/init/00-app-role.sql` (chạy tự động lần đầu khởi tạo volume):

```sql
-- app_user: role ứng dụng dùng runtime; KHÔNG bypass RLS
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user LOGIN PASSWORD 'appdevpass' NOBYPASSRLS;
  END IF;
END $$;
GRANT CONNECT ON DATABASE edmicro TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
-- Quyền bảng cấp sau migration (Task 5 step cuối)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
```

- [ ] **Step 3: `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports: ["5432:5432"]
    volumes:
      - ./pgdata:/var/lib/postgresql/data
      - ./infra/postgres/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10
  redis:
    image: redis:7
    ports: ["6379:6379"]
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports: ["9000:9000", "9001:9001"]
    volumes: ["./minio-data:/data"]
```

- [ ] **Step 4: `justfile`**

```make
set dotenv-load

up:
    docker compose up -d postgres redis minio

dev: up
    cd backend && uv run uvicorn app.main:app --reload --port 8000

migrate:
    cd backend && uv run alembic upgrade head

test:
    cd backend && uv run pytest -q

lint:
    cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports

seed:
    cd backend && uv run python ../scripts/seed.py

gen-api:
    cd frontend && pnpm gen-api
```

- [ ] **Step 5: Khởi động hạ tầng, xác minh Postgres**

```bash
cp .env.example .env
docker compose up -d postgres redis minio
docker compose exec postgres pg_isready -U edmicro_owner -d edmicro
```
Expected: `... accepting connections`

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml justfile infra .env.example
git commit -m "chore(infra): docker-compose (postgres/redis/minio) + app_user role + justfile"
```

---

## Task 3: Backend uv project + config + health endpoint (TDD)

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/config.py`, `backend/app/main.py`, `backend/app/modules/health/router.py`, `backend/tests/test_health.py`

- [ ] **Step 1: Khởi tạo uv project + deps**

```bash
cd backend
uv init --name edmicro-backend --python 3.12 --no-workspace
uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]>=2.0" asyncpg alembic pydantic-settings argon2-cffi pyjwt
uv add --dev pytest pytest-asyncio httpx testcontainers ruff pyright import-linter
```

- [ ] **Step 2: Cấu hình ruff + pyright + import-linter trong `pyproject.toml`**

Thêm vào cuối `backend/pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pyright]
include = ["app"]
typeCheckingMode = "standard"

[tool.pytest.ini_options]
asyncio_mode = "auto"

[tool.importlinter]
root_package = "app"
[[tool.importlinter.contracts]]
name = "Modules không import chéo repository/models"
type = "forbidden"
source_modules = ["app.modules"]
forbidden_modules = ["app.modules.*.repository", "app.modules.*.models"]
# Ngoại lệ: service của chính module (cưỡng chế chi tiết bổ sung khi có nhiều module — M1)
```

- [ ] **Step 3: `app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str
    migration_database_url: str
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 2592000


settings = Settings()  # type: ignore[call-arg]
```

- [ ] **Step 4: Viết test health thất bại**

Create `backend/tests/test_health.py`:

```python
import httpx
import pytest
from app.main import app


@pytest.mark.asyncio
async def test_health_returns_ok():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 5: Chạy test — xác minh FAIL**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: app.main` (chưa có app).

- [ ] **Step 6: Tạo health router + app tối thiểu**

Create `backend/app/modules/health/router.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI

from app.modules.health.router import router as health_router

app = FastAPI(title="Edmicro App API", version="0.1.0")
app.include_router(health_router)
```

Tạo file rỗng `backend/app/__init__.py`, `backend/app/modules/__init__.py`, `backend/app/modules/health/__init__.py`, `backend/tests/__init__.py`.

- [ ] **Step 7: Chạy test — xác minh PASS**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend
git commit -m "feat(backend): uv project, config, health endpoint"
```

---

## Task 4: Async engine + session + tenant context

**Files:**
- Create: `backend/app/db.py`, `backend/app/core/__init__.py`

- [ ] **Step 1: `app/db.py` — engine, session factory, hàm đặt tenant context**

```python
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def set_tenant(session: AsyncSession, tenant_id: str | None) -> None:
    """Đặt app.tenant_id cho transaction hiện tại — RLS dùng để lọc.

    Dùng set_config(..., true) (LOCAL) để chỉ áp trong transaction.
    tenant_id=None (vai trò platform) → đặt chuỗi rỗng, RLS coi như không khớp tenant nào.
    """
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"),
        {"tid": tenant_id or ""},
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        async with session.begin():
            yield session
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/db.py backend/app/core/__init__.py
git commit -m "feat(backend): async engine + tenant context (set_config app.tenant_id)"
```

---

## Task 5: Migration đầu tiên — tenants, platform_users, users + RLS

**Files:**
- Create: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_initial.py`, `backend/app/modules/org/models.py`, `backend/app/modules/authz/models.py`

- [ ] **Step 1: Khởi tạo Alembic**

```bash
cd backend && uv run alembic init alembic
```

- [ ] **Step 2: Cấu hình `alembic/env.py` dùng MIGRATION_DATABASE_URL (sync, role owner)**

Sửa `alembic/env.py`, phần config URL:

```python
import os
from app.db import Base
import app.modules.org.models  # noqa: F401  (đăng ký bảng)
import app.modules.authz.models  # noqa: F401

config.set_main_option("sqlalchemy.url", os.environ["MIGRATION_DATABASE_URL"])
target_metadata = Base.metadata
```

- [ ] **Step 3: Models — tenants + users**

Create `backend/app/modules/org/models.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    must_change_password: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Create `backend/app/modules/authz/models.py` (platform_users — không tenant_id, không RLS):

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PlatformUser(Base):
    __tablename__ = "platform_users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # admin|content_editor|support_agent
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Tạo `backend/app/modules/org/__init__.py` và `backend/app/modules/authz/__init__.py` rỗng.

- [ ] **Step 4: Sinh migration + thêm RLS thủ công**

```bash
cd backend && uv run alembic revision --autogenerate -m "initial tenants users platform_users"
```
Sau khi autogenerate, **thêm** vào cuối hàm `upgrade()` của file version vừa tạo (bật RLS + policy + UNIQUE username per tenant + grant cho app_user):

```python
    op.create_unique_constraint("uq_users_tenant_username", "users", ["tenant_id", "username"])
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON users "
        "USING (tenant_id = current_setting('app.tenant_id', true)::uuid)"
    )
    # app_user thao tác dữ liệu; owner (migration) sở hữu bảng
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON users, tenants, platform_users TO app_user")
```

Và đầu `downgrade()`:

```python
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON users")
```

- [ ] **Step 5: Chạy migration + kiểm tra bảng tồn tại**

```bash
just migrate
docker compose exec postgres psql -U edmicro_owner -d edmicro -c "\dt"
```
Expected: liệt kê `tenants`, `users`, `platform_users`, `alembic_version`.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic backend/app/modules backend/alembic.ini
git commit -m "feat(db): initial migration tenants/users/platform_users + RLS policy"
```

---

## Task 6: ★ Test cách ly tenant (RLS) — rủi ro số 1

**Files:**
- Create: `backend/tests/conftest.py`, `backend/tests/test_rls_isolation.py`

- [ ] **Step 1: Fixture testcontainers Postgres (áp migration + app_user)**

Create `backend/tests/conftest.py`:

```python
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16", username="edmicro_owner", password="devpass",
                           dbname="edmicro") as pg:
        yield pg


@pytest_asyncio.fixture(scope="session")
async def app_engine(pg_container):
    # DSN owner để tạo schema + role app_user; app kết nối lại bằng app_user
    owner_dsn = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    owner_engine = create_async_engine(owner_dsn)
    async with owner_engine.begin() as conn:
        await conn.execute(text(
            "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='app_user') "
            "THEN CREATE ROLE app_user LOGIN PASSWORD 'appdevpass' NOBYPASSRLS; END IF; END $$;"))
        await conn.execute(text(
            "CREATE TABLE tenants (id uuid PRIMARY KEY, slug text UNIQUE, name text, "
            "status text DEFAULT 'active')"))
        await conn.execute(text(
            "CREATE TABLE users (id uuid PRIMARY KEY, tenant_id uuid NOT NULL, username text, "
            "password_hash text, role text, status text DEFAULT 'active')"))
        await conn.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY"))
        await conn.execute(text("ALTER TABLE users FORCE ROW LEVEL SECURITY"))
        await conn.execute(text(
            "CREATE POLICY tenant_isolation ON users "
            "USING (tenant_id = current_setting('app.tenant_id', true)::uuid)"))
        await conn.execute(text("GRANT SELECT, INSERT, UPDATE, DELETE ON users, tenants TO app_user"))
    await owner_engine.dispose()

    app_dsn = owner_dsn.replace("edmicro_owner:devpass", "app_user:appdevpass")
    engine = create_async_engine(app_dsn)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(app_engine):
    return async_sessionmaker(app_engine, expire_on_commit=False)
```

- [ ] **Step 2: Viết test cách ly — xác minh FAIL trước khi seed dữ liệu đúng**

Create `backend/tests/test_rls_isolation.py`:

```python
import uuid

import pytest
from sqlalchemy import text

from app.db import set_tenant

TENANT_A = str(uuid.uuid4())
TENANT_B = str(uuid.uuid4())


@pytest.mark.asyncio
async def test_rls_blocks_cross_tenant_read(session_factory):
    # Seed: mỗi tenant 1 user (owner insert bằng cách set đúng tenant context)
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TENANT_A)
            await s.execute(text("INSERT INTO users (id, tenant_id, username, password_hash, role) "
                                 "VALUES (:id, :t, 'a', 'x', 'owner')"),
                            {"id": str(uuid.uuid4()), "t": TENANT_A})
        async with s.begin():
            await set_tenant(s, TENANT_B)
            await s.execute(text("INSERT INTO users (id, tenant_id, username, password_hash, role) "
                                 "VALUES (:id, :t, 'b', 'x', 'owner')"),
                            {"id": str(uuid.uuid4()), "t": TENANT_B})

    # Đọc dưới context tenant A → chỉ thấy user của A
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TENANT_A)
            rows = (await s.execute(text("SELECT username FROM users"))).scalars().all()
    assert rows == ["a"]  # KHÔNG được thấy 'b'


@pytest.mark.asyncio
async def test_rls_blocks_write_into_other_tenant(session_factory):
    # Set context A nhưng cố insert tenant_id B → RLS chặn (0 dòng thấy được / vi phạm policy)
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TENANT_A)
            with pytest.raises(Exception):
                await s.execute(text("INSERT INTO users (id, tenant_id, username, password_hash, role) "
                                     "VALUES (:id, :t, 'x', 'x', 'owner')"),
                                {"id": str(uuid.uuid4()), "t": TENANT_B})
```

- [ ] **Step 3: Chạy — xác minh test PASS (RLS thật sự chặn)**

Run: `cd backend && uv run pytest tests/test_rls_isolation.py -v`
Expected: cả 2 PASS. Nếu `test_rls_blocks_cross_tenant_read` thấy `['a','b']` → RLS chưa hiệu lực (app_user đang bypass) → kiểm tra role NOBYPASSRLS + FORCE RLS.

> Đây là test quan trọng nhất M0: chứng minh không rò rỉ chéo tenant ở tầng DB.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_rls_isolation.py
git commit -m "test(db): RLS chặn rò rỉ chéo tenant (testcontainers postgres thật)"
```

---

## Task 7: Bảo mật — argon2 hash + JWT (TDD)

**Files:**
- Create: `backend/app/core/security.py`, `backend/tests/test_security.py`

- [ ] **Step 1: Viết test security thất bại**

Create `backend/tests/test_security.py`:

```python
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    h = hash_password("s3cret!")
    assert h != "s3cret!"
    assert verify_password("s3cret!", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_roundtrip():
    token = create_access_token(user_id="u1", tenant_id="t1", role="owner")
    claims = decode_token(token)
    assert claims["sub"] == "u1"
    assert claims["tenant_id"] == "t1"
    assert claims["role"] == "owner"
    assert claims["type"] == "access"
```

- [ ] **Step 2: Chạy — xác minh FAIL**

Run: `cd backend && uv run pytest tests/test_security.py -v`
Expected: FAIL — `ModuleNotFoundError: app.core.security`.

- [ ] **Step 3: Cài đặt `app/core/security.py`**

```python
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

_ph = PasswordHasher()


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def _create_token(*, sub: str, tenant_id: str | None, role: str, ttl: int, ttype: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "role": role,
        "type": ttype,
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_access_token(*, user_id: str, tenant_id: str | None, role: str) -> str:
    return _create_token(sub=user_id, tenant_id=tenant_id, role=role,
                         ttl=settings.jwt_access_ttl_seconds, ttype="access")


def create_refresh_token(*, user_id: str, tenant_id: str | None, role: str) -> str:
    return _create_token(sub=user_id, tenant_id=tenant_id, role=role,
                         ttl=settings.jwt_refresh_ttl_seconds, ttype="refresh")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
```

- [ ] **Step 4: Chạy — xác minh PASS**

Run: `cd backend && uv run pytest tests/test_security.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py backend/tests/test_security.py
git commit -m "feat(auth): argon2 password hashing + JWT access/refresh"
```

---

## Task 8: Đăng nhập tenant — endpoint login + /authz/me (TDD)

**Files:**
- Create: `backend/app/modules/authz/{schemas,repository,service,router}.py`, `backend/app/core/tenant.py`, `backend/tests/test_auth_login.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Middleware resolve tenant từ header + đặt context**

Create `backend/app/core/tenant.py`:

```python
from starlette.types import ASGIApp, Receive, Scope, Send


class TenantMiddleware:
    """Đọc X-Tenant-Slug (frontend đặt từ subdomain) và gắn vào request state."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            slug = headers.get(b"x-tenant-slug", b"").decode() or None
            scope.setdefault("state", {})["tenant_slug"] = slug
        await self.app(scope, receive, send)
```

- [ ] **Step 2: Schemas + repository + service**

Create `backend/app/modules/authz/schemas.py`:

```python
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    must_change_password: bool


class MeResponse(BaseModel):
    user_id: str
    tenant_id: str
    role: str
```

Create `backend/app/modules/authz/repository.py`:

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def find_user_by_username(session: AsyncSession, username: str) -> dict | None:
    row = (await session.execute(
        text("SELECT id, tenant_id, password_hash, role, must_change_password "
             "FROM users WHERE username = :u AND status = 'active'"),
        {"u": username},
    )).mappings().first()
    return dict(row) if row else None
```

Create `backend/app/modules/authz/service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.modules.authz import repository


class InvalidCredentials(Exception):
    pass


async def login(session: AsyncSession, tenant_slug: str, username: str, password: str) -> dict:
    user = await repository.find_user_by_username(session, username)
    if user is None or not verify_password(password, user["password_hash"]):
        raise InvalidCredentials
    uid, tid, role = str(user["id"]), str(user["tenant_id"]), user["role"]
    return {
        "access_token": create_access_token(user_id=uid, tenant_id=tid, role=role),
        "refresh_token": create_refresh_token(user_id=uid, tenant_id=tid, role=role),
        "must_change_password": user["must_change_password"],
    }
```

- [ ] **Step 3: Router — login đặt tenant context theo slug (resolve slug→id qua bảng tenants)**

Create `backend/app/modules/authz/router.py`:

```python
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db import get_session, set_tenant
from app.modules.authz import service
from app.modules.authz.schemas import LoginRequest, LoginResponse, MeResponse

router = APIRouter(prefix="/api/v1/authz", tags=["auth"])


async def _tenant_id_from_slug(session: AsyncSession, slug: str) -> str:
    row = (await session.execute(
        text("SELECT id FROM tenants WHERE slug = :s AND status = 'active'"), {"s": slug}
    )).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="tenant_not_found")
    return str(row)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    slug = request.scope.get("state", {}).get("tenant_slug")
    if not slug:
        raise HTTPException(status_code=400, detail="missing_tenant")
    tenant_id = await _tenant_id_from_slug(session, slug)
    await set_tenant(session, tenant_id)
    try:
        return await service.login(session, slug, body.username, body.password)
    except service.InvalidCredentials:
        raise HTTPException(status_code=401, detail="invalid_credentials") from None


@router.get("/me", response_model=MeResponse)
async def me(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_token")
    claims = decode_token(authorization.removeprefix("Bearer "))
    return MeResponse(user_id=claims["sub"], tenant_id=claims["tenant_id"], role=claims["role"])
```

- [ ] **Step 4: Mount router + middleware trong `app/main.py`**

```python
from fastapi import FastAPI

from app.core.tenant import TenantMiddleware
from app.modules.authz.router import router as authz_router
from app.modules.health.router import router as health_router

app = FastAPI(title="Edmicro App API", version="0.1.0")
app.add_middleware(TenantMiddleware)
app.include_router(health_router)
app.include_router(authz_router)
```

- [ ] **Step 5: Test login end-to-end (dùng app_engine + override get_session)**

Create `backend/tests/test_auth_login.py`:

```python
import uuid

import httpx
import pytest
from sqlalchemy import text

from app.core.security import hash_password
from app.db import get_session, set_tenant
from app.main import app

TID = str(uuid.uuid4())
SLUG = "bright"


@pytest.mark.asyncio
async def test_login_success_and_me(session_factory):
    # Seed 1 tenant + 1 owner
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            await s.execute(text("INSERT INTO tenants (id, slug, name) VALUES (:id, :slug, 'Bright')"),
                            {"id": TID, "slug": SLUG})
            await s.execute(
                text("INSERT INTO users (id, tenant_id, username, password_hash, role) "
                     "VALUES (:id, :t, 'owner1', :ph, 'owner')"),
                {"id": str(uuid.uuid4()), "t": TID, "ph": hash_password("pass123")})

    async def _override_session():
        async with session_factory() as s:
            async with s.begin():
                yield s

    app.dependency_overrides[get_session] = _override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/authz/login", json={"username": "owner1", "password": "pass123"},
                              headers={"X-Tenant-Slug": SLUG})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        me = await client.get("/api/v1/authz/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["role"] == "owner"

        bad = await client.post("/api/v1/authz/login", json={"username": "owner1", "password": "x"},
                                headers={"X-Tenant-Slug": SLUG})
        assert bad.status_code == 401
    app.dependency_overrides.clear()
```

- [ ] **Step 6: Chạy toàn bộ test — xác minh PASS**

Run: `cd backend && uv run pytest -q`
Expected: tất cả PASS (health, security, rls_isolation, auth_login).

- [ ] **Step 7: Commit**

```bash
git add backend/app/modules/authz backend/app/core/tenant.py backend/app/main.py backend/tests/test_auth_login.py
git commit -m "feat(auth): tenant login (JWT) + /authz/me + tenant middleware"
```

---

## Task 9: Activity log core (log-by-design) — ghi async, append-only

**Files:**
- Create: `backend/app/core/activity_log.py`, `backend/app/core/audit.py`, migration `0002_activity_audit.py`, `backend/tests/test_activity_log.py`

- [ ] **Step 1: Migration bảng activity_logs + audit_logs (append-only)**

```bash
cd backend && uv run alembic revision -m "activity and audit logs"
```
Trong `upgrade()`:

```python
    op.execute("""
      CREATE TABLE activity_logs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid,
        actor_id uuid, actor_role text,
        action text NOT NULL, module text NOT NULL,
        entity_type text, entity_id uuid, entity_label text,
        diff jsonb, request_id text, ip text, user_agent text,
        at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_activity_tenant_entity ON activity_logs (tenant_id, entity_type, entity_id, at)")
    op.execute("""
      CREATE TABLE audit_logs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid, actor_id uuid, actor_role text,
        action text NOT NULL, target_type text, target_id uuid,
        before jsonb, after jsonb, ip text, user_agent text,
        at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("GRANT INSERT, SELECT ON activity_logs, audit_logs TO app_user")  # không UPDATE/DELETE
```

- [ ] **Step 2: `app/core/activity_log.py` — hàm ghi (M0: đồng bộ đơn giản; queue hóa ở M8)**

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_SENSITIVE = {"password", "password_hash", "token", "totp_secret", "parent_phone"}


def _redact(diff: dict) -> dict:
    return {k: ("***" if k in _SENSITIVE else v) for k, v in diff.items()}


async def log_activity(
    session: AsyncSession, *, tenant_id: str | None, actor_id: str | None, actor_role: str,
    action: str, module: str, entity_type: str, entity_id: str, entity_label: str = "",
    diff: dict | None = None,
) -> None:
    await session.execute(
        text("INSERT INTO activity_logs "
             "(tenant_id, actor_id, actor_role, action, module, entity_type, entity_id, entity_label, diff) "
             "VALUES (:t, :a, :r, :act, :m, :et, :eid, :el, :d)"),
        {"t": tenant_id, "a": actor_id, "r": actor_role, "act": action, "m": module,
         "et": entity_type, "eid": entity_id, "el": entity_label,
         "d": _redact(diff or {})},
    )
```

Create `backend/app/core/audit.py` tương tự (bảng `audit_logs`) — cùng khuôn, dành cho hành động nhạy cảm.

- [ ] **Step 3: Test — ghi log & không lộ trường nhạy cảm**

Create `backend/tests/test_activity_log.py`:

```python
import uuid

import pytest
from sqlalchemy import text

from app.core.activity_log import log_activity
from app.db import set_tenant

TID = str(uuid.uuid4())


@pytest.mark.asyncio
async def test_log_activity_redacts_sensitive(session_factory):
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            await log_activity(
                s, tenant_id=TID, actor_id=str(uuid.uuid4()), actor_role="it_admin",
                action="update", module="ORG", entity_type="user", entity_id=str(uuid.uuid4()),
                diff={"full_name": "A→B", "password_hash": "secret"})
        async with s.begin():
            await set_tenant(s, TID)
            row = (await s.execute(text("SELECT diff FROM activity_logs LIMIT 1"))).scalar_one()
    assert row["password_hash"] == "***"
    assert row["full_name"] == "A→B"
```

> Bổ sung DDL tương ứng vào `conftest.py` step tạo schema (thêm bảng `activity_logs` như migration).

- [ ] **Step 4: Chạy — PASS**

Run: `cd backend && uv run pytest tests/test_activity_log.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/activity_log.py backend/app/core/audit.py backend/alembic backend/tests/test_activity_log.py
git commit -m "feat(log): activity + audit log core, append-only, redact sensitive fields"
```

---

## Task 10: Seed script — 1 tenant + 1 owner

**Files:**
- Create: `scripts/seed.py`

- [ ] **Step 1: Viết seed script**

```python
import asyncio
import uuid

from sqlalchemy import text

from app.core.security import hash_password
from app.db import SessionLocal, set_tenant

TENANT_ID = uuid.uuid4()


async def main() -> None:
    async with SessionLocal() as s:
        async with s.begin():
            await set_tenant(s, str(TENANT_ID))
            await s.execute(
                text("INSERT INTO tenants (id, slug, name) VALUES (:id, 'bright', 'Anh ngữ Bright') "
                     "ON CONFLICT (slug) DO NOTHING"),
                {"id": str(TENANT_ID)})
            await s.execute(
                text("INSERT INTO users (id, tenant_id, username, password_hash, role, full_name) "
                     "VALUES (:id, :t, 'owner', :ph, 'owner', 'Chủ trung tâm') "
                     "ON CONFLICT (tenant_id, username) DO NOTHING"),
                {"id": str(uuid.uuid4()), "t": str(TENANT_ID), "ph": hash_password("owner123")})
    print(f"Seeded tenant 'bright' (slug) + owner/owner123")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Chạy seed trên DB dev + xác minh**

```bash
just migrate && just seed
docker compose exec postgres psql -U edmicro_owner -d edmicro -c "SELECT username, role FROM users"
```
Expected: 1 dòng `owner | owner`.

- [ ] **Step 3: Commit**

```bash
git add scripts/seed.py
git commit -m "chore(seed): 1 tenant bright + owner account"
```

---

## Task 11: CI — GitHub Actions (lint + typecheck + test + import-linter)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Workflow backend CI (Postgres không cần — testcontainers tự dựng)**

```yaml
name: CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Sync deps
        working-directory: backend
        run: uv sync --all-extras --dev
      - name: Lint
        working-directory: backend
        run: uv run ruff check . && uv run ruff format --check .
      - name: Type check
        working-directory: backend
        run: uv run pyright
      - name: Import boundaries
        working-directory: backend
        run: uv run lint-imports
      - name: Tests (testcontainers)
        working-directory: backend
        run: uv run pytest -q
```

- [ ] **Step 2: Chạy thử cục bộ chuỗi lệnh CI**

Run: `cd backend && uv run ruff check . && uv run pyright && uv run lint-imports && uv run pytest -q`
Expected: tất cả xanh.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: lint + typecheck + import-linter + pytest on push/PR"
```

---

## Task 12: Frontend — Next.js + HeroUI + tenant middleware + trang login

**Files:**
- Create: `frontend/` (scaffold), `frontend/middleware.ts`, `frontend/app/(auth)/login/page.tsx`, `frontend/lib/api.ts`, `frontend/biome.json`

- [ ] **Step 1: Scaffold Next.js + HeroUI + Biome**

```bash
cd /home/mvng/edmicro-app
pnpm create next-app@latest frontend --typescript --app --tailwind --eslint=false --src-dir=false --import-alias="@/*"
cd frontend
pnpm add @heroui/react framer-motion
pnpm add -D @biomejs/biome @hey-api/openapi-ts
pnpm dlx @biomejs/biome init
```
Cấu hình HeroUI theo docs (HeroUIProvider trong `app/providers.tsx`, thêm plugin vào `tailwind.config.ts`).

- [ ] **Step 2: Middleware resolve tenant từ subdomain → header cho API**

Create `frontend/middleware.ts`:

```typescript
import { NextRequest, NextResponse } from "next/server";

export function middleware(req: NextRequest) {
  const host = req.headers.get("host") ?? "";
  const sub = host.split(".")[0];
  const slug = sub && !["www", "localhost:3000", "ops"].includes(sub) ? sub : "";
  const res = NextResponse.next();
  res.headers.set("x-tenant-slug", slug);
  return res;
}

export const config = { matcher: ["/((?!_next|favicon.ico).*)"] };
```

- [ ] **Step 3: `lib/api.ts` — gắn X-Tenant-Slug vào mọi request**

```typescript
export async function apiLogin(slug: string, username: string, password: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/authz/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Tenant-Slug": slug },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("invalid_credentials");
  return res.json() as Promise<{ access_token: string; refresh_token: string; must_change_password: boolean }>;
}
```

- [ ] **Step 4: Trang login dùng HeroUI (map mockup `auth/dang-nhap.html`)**

Create `frontend/app/(auth)/login/page.tsx`:

```tsx
"use client";
import { Button, Card, CardBody, Input } from "@heroui/react";
import { useState } from "react";
import { apiLogin } from "@/lib/api";

export default function LoginPage() {
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState("");

  async function onSubmit() {
    try {
      const slug = window.location.host.split(".")[0];
      const r = await apiLogin(slug, username, password);
      localStorage.setItem("access_token", r.access_token);
      window.location.href = "/dashboard";
    } catch {
      setErr("Sai tên đăng nhập hoặc mật khẩu");
    }
  }

  return (
    <div className="min-h-screen grid place-items-center bg-default-50">
      <Card className="w-[420px]">
        <CardBody className="gap-4 p-6">
          <h1 className="text-lg font-semibold">Đăng nhập</h1>
          <Input label="Tên đăng nhập" value={username} onValueChange={setU} />
          <Input label="Mật khẩu" type="password" value={password} onValueChange={setP} />
          {err && <p className="text-danger text-sm">{err}</p>}
          <Button color="primary" size="lg" onPress={onSubmit}>Đăng nhập</Button>
        </CardBody>
      </Card>
    </div>
  );
}
```

- [ ] **Step 5: Sinh api-client từ OpenAPI (script)**

Thêm vào `frontend/package.json`:

```json
"scripts": { "gen-api": "openapi-ts -i http://localhost:8000/openapi.json -o ../packages/api-client" }
```
Chạy (backend phải đang chạy): `pnpm gen-api`.

- [ ] **Step 6: Chạy thủ công — xác minh luồng login**

```bash
just up && just migrate && just seed
just dev &            # backend :8000
cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev  # :3000
```
Mở `http://bright.localhost:3000/login`, đăng nhập `owner` / `owner123` → chuyển `/dashboard` (trang tạm), token lưu localStorage. Sai mật khẩu → hiện lỗi.

- [ ] **Step 7: Commit**

```bash
git add frontend packages
git commit -m "feat(frontend): Next.js + HeroUI scaffold, tenant middleware, login page + api-client"
```

---

## Task 13: E2E smoke (Playwright) — luồng login

**Files:**
- Create: `frontend/e2e/login.spec.ts`, `frontend/playwright.config.ts`

- [ ] **Step 1: Cài Playwright**

```bash
cd frontend && pnpm add -D @playwright/test && pnpm exec playwright install chromium
```

- [ ] **Step 2: Test E2E login**

Create `frontend/e2e/login.spec.ts`:

```typescript
import { expect, test } from "@playwright/test";

test("owner đăng nhập thành công", async ({ page }) => {
  await page.goto("http://bright.localhost:3000/login");
  await page.getByLabel("Tên đăng nhập").fill("owner");
  await page.getByLabel("Mật khẩu").fill("owner123");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
});

test("sai mật khẩu hiện lỗi", async ({ page }) => {
  await page.goto("http://bright.localhost:3000/login");
  await page.getByLabel("Tên đăng nhập").fill("owner");
  await page.getByLabel("Mật khẩu").fill("wrong");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page.getByText("Sai tên đăng nhập")).toBeVisible();
});
```

- [ ] **Step 3: Chạy E2E (backend + frontend đang chạy) — PASS**

Run: `cd frontend && pnpm exec playwright test`
Expected: 2 PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e frontend/playwright.config.ts
git commit -m "test(e2e): playwright login smoke (owner đăng nhập + sai mật khẩu)"
```

---

## Nghiệm thu Milestone 0 (Definition of Done)

- [ ] `just up && just migrate && just seed` chạy sạch; `just test` xanh (health, security, RLS isolation, auth login, activity log).
- [ ] **RLS chứng minh chặn chéo tenant** (`test_rls_isolation.py` PASS) — rủi ro #1 đã khóa.
- [ ] Đăng nhập được `owner`/`owner123` tại `bright.localhost:3000/login` → nhận JWT, `/authz/me` trả đúng vai trò.
- [ ] Mọi thao tác ghi có thể gọi `log_activity` (interceptor hoàn thiện ở M1 khi có service CRUD thật).
- [ ] CI xanh trên push/PR (lint + pyright + import-linter + pytest).
- [ ] E2E login PASS.

## Self-review (đã kiểm)

- **Spec coverage**: M0 phủ AUTH (login/JWT/hash — FR-AUTH-08/09), Multi-tenant (RLS §3), LOG core (FR-LOG-01/02/04/12), kiến trúc/toolchain (05-cau-truc-code). Các FR còn lại thuộc M1+.
- **Placeholder**: không có TBD; mọi step logic có code thật; scaffold step có lệnh chính xác.
- **Type consistency**: `set_tenant`, `hash_password/verify_password`, `create_access_token/decode_token`, `log_activity` — chữ ký dùng nhất quán giữa các task và test.
- **Lưu ý thực thi**: `test_activity_log.py` cần bảng `activity_logs` trong `conftest.py` — Task 9 Step 3 đã ghi chú thêm DDL vào fixture. `app_user` phải NOBYPASSRLS ở cả docker init lẫn testcontainers fixture (nếu không, RLS test sẽ sai).

## Lịch sử thay đổi

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-07-17 | Tạo plan M0 (nền tảng) — 13 task bite-sized TDD | Claude |
