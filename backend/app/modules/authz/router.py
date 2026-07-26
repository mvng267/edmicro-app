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
    tenant_id = await _tenant_id_from_slug(session, slug)
    await set_tenant(session, tenant_id)
    try:
        return await service.login(session, body.username, body.password)
    except service.InvalidCredentials:
        raise HTTPException(status_code=401, detail="invalid_credentials") from None


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
