from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
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


@router.get("/me", response_model=MeResponse)
async def me(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_token")
    claims = decode_token(authorization.removeprefix("Bearer "))
    return MeResponse(user_id=claims["sub"], tenant_id=claims["tenant_id"], role=claims["role"])
