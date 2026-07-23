"""API quản trị log (đọc). Xem SRS LOG. Chỉ owner/it_admin/admin xem nhật ký tenant."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.logadmin import service as svc

router = APIRouter(prefix="/api/v1/admin", tags=["logadmin"])

_LOG_ROLES = {"owner", "it_admin", "admin"}


@router.get("/logs")
async def list_logs(
    module: str | None = None,
    actor_role: str | None = None,
    entity_type: str | None = None,
    actor_id: str | None = None,
    limit: int = 100,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _LOG_ROLES:
        raise HTTPException(403, "forbidden_role")
    return await svc.list_activity(
        s,
        current.tenant_id,
        {
            "module": module,
            "actor_role": actor_role,
            "entity_type": entity_type,
            "actor_id": actor_id,
        },
        limit=limit,
    )
