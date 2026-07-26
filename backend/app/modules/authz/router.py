from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.core.security import decode_token, hash_password, verify_password
from app.db import get_session, set_tenant
from app.modules.authz import service
from app.modules.authz.schemas import LoginRequest, LoginResponse, MeResponse

router = APIRouter(prefix="/api/v1/authz", tags=["auth"])

# ── Rate-limit đăng nhập (chống dò mật khẩu) ─────────────────────────────
# In-memory theo (IP + username): quá _MAX_FAILS lần sai trong _WINDOW giây → 429.
# Đủ cho 1 tiến trình uvicorn; scale nhiều worker thì chuyển sang Redis (đã có sẵn hạ tầng).
_LOGIN_FAILS: dict[str, list[float]] = {}
_MAX_FAILS = 5
_WINDOW_SECONDS = 300.0


def _client_ip(request: Request) -> str:
    # Sau Cloudflare tunnel + Next proxy: IP thật nằm ở header
    return (
        request.headers.get("cf-connecting-ip")
        or (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


def _throttle_check(key: str) -> None:
    import time

    now = time.monotonic()
    fails = [t for t in _LOGIN_FAILS.get(key, []) if now - t < _WINDOW_SECONDS]
    _LOGIN_FAILS[key] = fails
    if len(fails) >= _MAX_FAILS:
        raise HTTPException(status_code=429, detail="too_many_attempts")


def _throttle_fail(key: str) -> None:
    import time

    _LOGIN_FAILS.setdefault(key, []).append(time.monotonic())


async def _tenant_id_from_slug(session: AsyncSession, slug: str) -> str:
    row = (
        await session.execute(
            text("SELECT id FROM tenants WHERE slug = :s AND status = 'active'"), {"s": slug}
        )
    ).scalar_one_or_none()
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
    throttle_key = f"{_client_ip(request)}|{slug}|{body.username.lower()}"
    _throttle_check(throttle_key)
    tenant_id = await _tenant_id_from_slug(session, slug)
    await set_tenant(session, tenant_id)
    try:
        result = await service.login(session, body.username, body.password)
    except service.InvalidCredentials:
        _throttle_fail(throttle_key)
        raise HTTPException(status_code=401, detail="invalid_credentials") from None
    _LOGIN_FAILS.pop(throttle_key, None)  # đăng nhập đúng → xóa đếm
    return result


@router.get("/tenant-info")
async def tenant_info(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Tên trung tâm theo subdomain — cho màn đăng nhập (public, không lộ gì thêm)."""
    slug = request.scope.get("state", {}).get("tenant_slug")
    if not slug:
        raise HTTPException(status_code=400, detail="missing_tenant")
    name = (
        await session.execute(
            text("SELECT name FROM tenants WHERE slug = :s AND status = 'active'"), {"s": slug}
        )
    ).scalar_one_or_none()
    if name is None:
        raise HTTPException(status_code=404, detail="tenant_not_found")
    return {"slug": slug, "name": name}


class ChangePasswordBody(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


@router.post("/change-password")
async def change_password(
    body: ChangePasswordBody,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    """Đổi mật khẩu của chính mình; xóa cờ must_change_password (đăng nhập lần đầu)."""
    row = (
        await s.execute(
            text("SELECT password_hash FROM users WHERE id = :id"), {"id": current.user_id}
        )
    ).scalar_one_or_none()
    if row is None or not verify_password(body.old_password, row):
        raise HTTPException(status_code=401, detail="wrong_old_password")
    await s.execute(
        text(
            "UPDATE users SET password_hash = :ph, must_change_password = false, "
            "updated_at = now() WHERE id = :id"
        ),
        {"ph": hash_password(body.new_password), "id": current.user_id},
    )
    return {"changed": True}


@router.get("/me", response_model=MeResponse)
async def me(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_token")
    claims = decode_token(authorization.removeprefix("Bearer "))
    return MeResponse(user_id=claims["sub"], tenant_id=claims["tenant_id"], role=claims["role"])
