import uuid

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app

TID = str(uuid.uuid4())


async def _seed(session_factory):
    """1 HS + 2 phụ huynh. Trả (student, parent, parent2)."""
    student = str(uuid.uuid4())
    parent = str(uuid.uuid4())
    parent2 = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'P9') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"p9-{TID[:8]}"},
        )
        for uid, role, fn in (
            (student, "student", "Bé An"),
            (parent, "parent", "Phụ huynh 1"),
            (parent2, "parent", "Phụ huynh 2"),
        ):
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, full_name, password_hash, role) "
                    "VALUES (:id, :t, :un, :fn, 'x', :r)"
                ),
                {"id": uid, "t": TID, "un": f"u-{uid[:8]}", "fn": fn, "r": role},
            )
    return student, parent, parent2


@pytest.fixture
async def client(session_factory):
    async def _override_session():
        async with session_factory() as s, s.begin():
            await set_tenant(s, TID)
            yield s

    app.dependency_overrides[get_tenant_session] = _override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def _as(role: str, uid: str):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(uid, TID, role)


@pytest.mark.asyncio
async def test_parent_portal(client, session_factory):
    student, parent, parent2 = await _seed(session_factory)

    # teacher KHÔNG liên kết được phụ huynh–HS
    _as("teacher", str(uuid.uuid4()))
    assert (
        await client.post(f"/api/v1/org/parents/{parent}/children/{student}")
    ).status_code == 403

    # owner liên kết
    _as("owner", str(uuid.uuid4()))
    assert (
        await client.post(f"/api/v1/org/parents/{parent}/children/{student}")
    ).status_code == 201

    # phụ huynh thấy con + xem báo cáo + điểm
    _as("parent", parent)
    kids = (await client.get("/api/v1/me/children")).json()
    assert len(kids) == 1 and kids[0]["student_id"] == student
    rep = await client.get(f"/api/v1/me/children/{student}/report")
    assert rep.status_code == 200
    assert "summary" in rep.json()
    pts = await client.get(f"/api/v1/me/children/{student}/points")
    assert pts.status_code == 200
    assert "total" in pts.json()

    # phụ huynh KHÁC không xem được con người ta
    _as("parent", parent2)
    assert (await client.get("/api/v1/me/children")).json() == []
    assert (await client.get(f"/api/v1/me/children/{student}/report")).status_code == 403

    # HS không phải phụ huynh -> /me/children 403
    _as("student", student)
    assert (await client.get("/api/v1/me/children")).status_code == 403
