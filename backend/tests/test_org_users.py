import uuid
from datetime import date

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import get_session, set_tenant
from app.main import app

TID = str(uuid.uuid4())
SLUG = f"acme-{TID[:8]}"


@pytest.fixture
async def client(session_factory):
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            await s.execute(
                text(
                    "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'Acme') "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {"id": TID, "sl": SLUG},
            )

    async def _override_session():
        async with session_factory() as s:
            async with s.begin():
                await set_tenant(s, TID)
                yield s

    app.dependency_overrides[get_tenant_session] = _override_session
    app.dependency_overrides[get_session] = _override_session  # cho login dùng chung DB test
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def _as(role: str):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(str(uuid.uuid4()), TID, role)


@pytest.mark.asyncio
async def test_create_role_matrix(client):
    _as("manager")
    # manager tạo student OK
    r = await client.post("/api/v1/org/users", json={"full_name": "Nguyễn Minh", "role": "student"})
    assert r.status_code == 201, r.text
    assert r.json()["username"] and r.json()["password"]
    # manager tạo manager -> 403
    r2 = await client.post("/api/v1/org/users", json={"full_name": "X", "role": "manager"})
    assert r2.status_code == 403

    _as("it_admin")
    r3 = await client.post("/api/v1/org/users", json={"full_name": "Y", "role": "owner"})
    assert r3.status_code == 403


@pytest.mark.asyncio
async def test_minor_gets_consent_pending(client, session_factory):
    _as("owner")
    r = await client.post(
        "/api/v1/org/users",
        json={"full_name": "Bé An", "role": "student", "dob": str(date(2015, 5, 1))},
    )
    uid = r.json()["id"]
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            st = (
                await s.execute(text("SELECT status FROM consents WHERE user_id = :u"), {"u": uid})
            ).scalar_one_or_none()
    assert st == "pending"


@pytest.mark.asyncio
async def test_created_student_can_login(client):
    _as("owner")
    cred = (
        await client.post(
            "/api/v1/org/users", json={"full_name": "Học Sinh Login", "role": "student"}
        )
    ).json()
    # đăng nhập bằng credentials vừa cấp (login đọc get_session đã override)
    del app.dependency_overrides[get_current_user]  # login không cần current user
    login = await client.post(
        "/api/v1/authz/login",
        json={"username": cred["username"], "password": cred["password"]},
        headers={"X-Tenant-Slug": SLUG},
    )
    assert login.status_code == 200, login.text
    assert login.json()["must_change_password"] is True


@pytest.mark.asyncio
async def test_reset_password_changes_login(client):
    _as("owner")
    cred = (
        await client.post("/api/v1/org/users", json={"full_name": "Reset Me", "role": "teacher"})
    ).json()
    _as("owner")
    new = await client.post(f"/api/v1/org/users/{cred['id']}/reset-password")
    assert new.status_code == 200
    new_pw = new.json()["password"]
    assert new_pw != cred["password"]
    del app.dependency_overrides[get_current_user]
    ok = await client.post(
        "/api/v1/authz/login",
        json={"username": cred["username"], "password": new_pw},
        headers={"X-Tenant-Slug": SLUG},
    )
    assert ok.status_code == 200
