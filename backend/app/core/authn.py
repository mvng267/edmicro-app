"""Xác thực + phân quyền dùng chung cho mọi endpoint sau đăng nhập.

- get_current_user: decode JWT access token -> CurrentUser
- get_tenant_session: mở session + set app.tenant_id theo token (RLS)
- require_roles: 403 nếu vai trò không thuộc danh sách
- scope_branch_ids: phạm vi chi nhánh của manager/it_admin (None = toàn tenant)
Xem docs/02-phan-quyen/srs-phan-quyen.md.
"""

from collections.abc import AsyncGenerator
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db import SessionLocal, set_tenant


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    tenant_id: str
    role: str


def get_current_user(authorization: str = Header(default="")) -> CurrentUser:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_token")
    try:
        claims = decode_token(authorization.removeprefix("Bearer "))
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid_token") from None
    if claims.get("type") != "access":
        raise HTTPException(status_code=401, detail="wrong_token_type")
    return CurrentUser(user_id=claims["sub"], tenant_id=claims["tenant_id"], role=claims["role"])


async def get_tenant_session(
    current: CurrentUser = Depends(get_current_user),
) -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        async with session.begin():
            await set_tenant(session, current.tenant_id)
            yield session


def require_roles(*roles: str):
    """Dependency factory: chặn 403 nếu vai trò không thuộc danh sách cho phép."""

    def _dep(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current.role not in roles:
            raise HTTPException(status_code=403, detail="forbidden_role")
        return current

    return _dep


async def scope_branch_ids(session: AsyncSession, current: CurrentUser) -> list[str] | None:
    """None = toàn tenant (owner, hoặc manager/it_admin không giới hạn chi nhánh).
    Danh sách = chỉ các chi nhánh được gán."""
    if current.role == "owner":
        return None
    if current.role not in ("manager", "it_admin"):
        return None
    rows = (
        (
            await session.execute(
                text(
                    "SELECT branch_id FROM user_scopes WHERE user_id = :u AND branch_id IS NOT NULL"
                ),
                {"u": current.user_id},
            )
        )
        .scalars()
        .all()
    )
    return [str(r) for r in rows] if rows else None
