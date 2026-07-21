"""API thông báo in-app cho người dùng hiện tại. Xem SRS NOTIF FR-NOTIF."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.notify import service as svc

router = APIRouter(prefix="/api/v1", tags=["notify"])


@router.get("/me/notifications")
async def my_notifications(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    return await svc.list_for_user(s, current.user_id)


@router.get("/me/notifications/unread-count")
async def unread_count(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    return {"count": await svc.unread_count(s, current.user_id)}


@router.post("/notifications/{notif_id}/read")
async def read_one(
    notif_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if not await svc.mark_read(s, current.user_id, notif_id):
        raise HTTPException(404, "not_found")
    return {"read": True}


@router.post("/notifications/read-all")
async def read_all(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    return {"marked": await svc.mark_all_read(s, current.user_id)}
