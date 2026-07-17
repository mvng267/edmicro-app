import uuid
from contextlib import asynccontextmanager

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app

TID = str(uuid.uuid4())


async def _seed_user(session_factory, role: str) -> str:
    uid = str(uuid.uuid4())
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                    "VALUES (:id, :t, :un, 'x', :r)"
                ),
                {"id": uid, "t": TID, "un": f"{role}-{uid[:8]}", "r": role},
            )
    return uid


@pytest.fixture
async def client(session_factory):
    # tenant bright tồn tại
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            await s.execute(
                text(
                    "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'Bright') "
                    "ON CONFLICT (slug) DO NOTHING"
                ),
                {"id": TID, "sl": f"bright-{TID[:8]}"},
            )

    @asynccontextmanager
    async def _sess():
        async with session_factory() as s:
            async with s.begin():
                await set_tenant(s, TID)
                yield s

    async def _override_session():
        async with _sess() as s:
            yield s

    app.dependency_overrides[get_tenant_session] = _override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def _as(role: str, uid: str | None = None):
    uid = uid or str(uuid.uuid4())
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(uid, TID, role)


@pytest.mark.asyncio
async def test_owner_creates_branch_manager_forbidden(client):
    _as("owner")
    r = await client.post("/api/v1/org/branches", json={"name": "Chi nhánh Q7"})
    assert r.status_code == 201, r.text
    branch_id = r.json()["id"]

    _as("manager")
    r2 = await client.post("/api/v1/org/branches", json={"name": "Chi nhánh Q1"})
    assert r2.status_code == 403

    # danh sách chỉ có 1 chi nhánh
    _as("owner")
    lst = await client.get("/api/v1/org/branches")
    assert any(b["id"] == branch_id for b in lst.json())


@pytest.mark.asyncio
async def test_class_lifecycle_and_rules(client, session_factory):
    _as("owner")
    branch_id = (await client.post("/api/v1/org/branches", json={"name": "CN chính"})).json()["id"]

    # tạo lớp
    c = await client.post(
        "/api/v1/org/classes", json={"branch_id": branch_id, "name": "IELTS 6.5", "language": "en"}
    )
    assert c.status_code == 201, c.text
    class_id = c.json()["id"]

    # gán teacher OK, gán student làm staff -> 422
    teacher = await _seed_user(session_factory, "teacher")
    student = await _seed_user(session_factory, "student")
    ok = await client.post(
        f"/api/v1/org/classes/{class_id}/staff", json={"user_id": teacher, "role": "teacher"}
    )
    assert ok.status_code == 201
    bad = await client.post(
        f"/api/v1/org/classes/{class_id}/staff", json={"user_id": student, "role": "teacher"}
    )
    assert bad.status_code == 422

    # thêm học sinh vào lớp
    add = await client.post(f"/api/v1/org/classes/{class_id}/students", json={"user_id": student})
    assert add.status_code == 201

    # xóa chi nhánh còn lớp active -> 409
    _as("owner")
    dele = await client.delete(f"/api/v1/org/branches/{branch_id}")
    assert dele.status_code == 409


@pytest.mark.asyncio
async def test_activity_log_written_on_branch_create(client, session_factory):
    _as("owner", uid=str(uuid.uuid4()))
    await client.post("/api/v1/org/branches", json={"name": "CN log"})
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            n = (
                await s.execute(
                    text(
                        "SELECT count(*) FROM activity_logs "
                        "WHERE module='ORG' AND action='create' AND entity_type='branch'"
                    )
                )
            ).scalar_one()
    assert n >= 1
