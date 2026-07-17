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

        me = await client.get(
            "/api/v1/authz/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me.status_code == 200
        assert me.json()["role"] == "owner"

        bad = await client.post(
            "/api/v1/authz/login",
            json={"username": "owner1", "password": "x"},
            headers={"X-Tenant-Slug": SLUG},
        )
        assert bad.status_code == 401
    app.dependency_overrides.clear()
