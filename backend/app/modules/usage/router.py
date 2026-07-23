"""API mức dùng & quota. Xem SRS PLAN. owner/manager/it_admin xem usage tenant mình."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.usage import service as svc

router = APIRouter(prefix="/api/v1", tags=["usage"])

_USAGE_ROLES = {"owner", "manager", "it_admin"}


@router.get("/usage")
async def usage(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _USAGE_ROLES:
        raise HTTPException(403, "forbidden_role")
    return await svc.tenant_usage(s, current.tenant_id)
