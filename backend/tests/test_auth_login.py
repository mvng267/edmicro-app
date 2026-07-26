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
            await s.execute(
                text("INSERT INTO tenants (id, slug, name) VALUES (:id, :slug, 'Bright')"),
                {"id": TID, "slug": SLUG},
            )
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                    "VALUES (:id, :t, 'owner1', :ph, 'owner')"
                ),
                {"id": str(uuid.uuid4()), "t": TID, "ph": hash_password("pass123")},
            )

    async def _override_session():
        async with session_factory() as s:
            async with s.begin():
                yield s

    app.dependency_overrides[get_session] = _override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/authz/login",
            json={"username": "owner1", "password": "pass123"},
            headers={"X-Tenant-Slug": SLUG},
        )
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]

        me = await client.get("/api/v1/authz/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["role"] == "owner"

        bad = await client.post(
            "/api/v1/authz/login",
            json={"username": "owner1", "password": "x"},
            headers={"X-Tenant-Slug": SLUG},
        )
        assert bad.status_code == 401
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_change_password_first_login(session_factory):
    from app.core.authn import get_tenant_session

    slug = f"cp-{uuid.uuid4().hex[:8]}"
    tid = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, tid)
        await s.execute(
            text("INSERT INTO tenants (id, slug, name) VALUES (:id, :slug, 'CP')"),
            {"id": tid, "slug": slug},
        )
        await s.execute(
            text(
                "INSERT INTO users (id, tenant_id, username, password_hash, role, "
                "must_change_password) VALUES (:id, :t, 'hs-cp', :ph, 'student', true)"
            ),
            {"id": str(uuid.uuid4()), "t": tid, "ph": hash_password("tam12345")},
        )

    async def _override_session():
        async with session_factory() as s, s.begin():
            yield s

    async def _override_tenant_session():
        async with session_factory() as s, s.begin():
            await set_tenant(s, tid)
            yield s

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_tenant_session] = _override_tenant_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/authz/login",
            json={"username": "hs-cp", "password": "tam12345"},
            headers={"X-Tenant-Slug": slug},
        )
        assert r.json()["must_change_password"] is True
        token = r.json()["access_token"]
        auth = {"Authorization": f"Bearer {token}"}

        # sai mật khẩu cũ -> 401; mới quá ngắn -> 422
        bad = await client.post(
            "/api/v1/authz/change-password",
            json={"old_password": "sai", "new_password": "moi12345"},
            headers=auth,
        )
        assert bad.status_code == 401
        short = await client.post(
            "/api/v1/authz/change-password",
            json={"old_password": "tam12345", "new_password": "ngan"},
            headers=auth,
        )
        assert short.status_code == 422

        ok = await client.post(
            "/api/v1/authz/change-password",
            json={"old_password": "tam12345", "new_password": "moi12345"},
            headers=auth,
        )
        assert ok.status_code == 200, ok.text

        # đăng nhập lại bằng mật khẩu MỚI, cờ must_change đã tắt
        r2 = await client.post(
            "/api/v1/authz/login",
            json={"username": "hs-cp", "password": "moi12345"},
            headers={"X-Tenant-Slug": slug},
        )
        assert r2.status_code == 200
        assert r2.json()["must_change_password"] is False
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_rate_limit(session_factory):
    """Sai mật khẩu 5 lần → lần 6 bị 429 (kể cả đúng mật khẩu); user khác không bị vạ lây."""
    slug = f"rl-{uuid.uuid4().hex[:8]}"
    tid = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, tid)
        await s.execute(
            text("INSERT INTO tenants (id, slug, name) VALUES (:id, :slug, 'RL')"),
            {"id": tid, "slug": slug},
        )
        for un in ("rl-user", "rl-khac"):
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                    "VALUES (:id, :t, :un, :ph, 'student')"
                ),
                {"id": str(uuid.uuid4()), "t": tid, "un": un, "ph": hash_password("dung1234")},
            )

    async def _override_session():
        async with session_factory() as s, s.begin():
            yield s

    app.dependency_overrides[get_session] = _override_session
    transport = httpx.ASGITransport(app=app)
    headers = {"X-Tenant-Slug": slug}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            r = await client.post(
                "/api/v1/authz/login",
                json={"username": "rl-user", "password": "sai"},
                headers=headers,
            )
            assert r.status_code == 401
        # lần 6: dù ĐÚNG mật khẩu vẫn 429 (đang bị khóa tạm)
        blocked = await client.post(
            "/api/v1/authz/login",
            json={"username": "rl-user", "password": "dung1234"},
            headers=headers,
        )
        assert blocked.status_code == 429

        # user khác cùng IP vẫn đăng nhập bình thường
        other = await client.post(
            "/api/v1/authz/login",
            json={"username": "rl-khac", "password": "dung1234"},
            headers=headers,
        )
        assert other.status_code == 200
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_tenant_info_public(session_factory):
    slug = f"ti-{uuid.uuid4().hex[:8]}"
    tid = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, tid)
        await s.execute(
            text("INSERT INTO tenants (id, slug, name) VALUES (:id, :slug, 'Trung tâm TI')"),
            {"id": tid, "slug": slug},
        )

    async def _override_session():
        async with session_factory() as s, s.begin():
            yield s

    app.dependency_overrides[get_session] = _override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/authz/tenant-info", headers={"X-Tenant-Slug": slug})
        assert r.status_code == 200
        assert r.json()["name"] == "Trung tâm TI"
        bad = await client.get(
            "/api/v1/authz/tenant-info", headers={"X-Tenant-Slug": "khong-ton-tai"}
        )
        assert bad.status_code == 404
    app.dependency_overrides.clear()
