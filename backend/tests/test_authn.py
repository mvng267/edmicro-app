import httpx
import pytest
from fastapi import Depends, FastAPI

from app.core.authn import CurrentUser, get_current_user, require_roles
from app.core.security import create_access_token, create_refresh_token

_app = FastAPI()


@_app.get("/whoami")
async def whoami(current: CurrentUser = Depends(get_current_user)):
    return {"role": current.role}


@_app.get("/owner-only")
async def owner_only(current: CurrentUser = Depends(require_roles("owner"))):
    return {"ok": True}


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=_app), base_url="http://t")


@pytest.mark.asyncio
async def test_missing_token_401():
    async with _client() as c:
        r = await c.get("/whoami")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rejected_on_access_endpoint():
    tok = create_refresh_token(user_id="u", tenant_id="t", role="owner")
    async with _client() as c:
        r = await c.get("/whoami", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_role_forbidden_403():
    tok = create_access_token(user_id="u", tenant_id="t", role="manager")
    async with _client() as c:
        r = await c.get("/owner-only", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_role_allowed_200():
    tok = create_access_token(user_id="u", tenant_id="t", role="owner")
    async with _client() as c:
        r = await c.get("/owner-only", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
