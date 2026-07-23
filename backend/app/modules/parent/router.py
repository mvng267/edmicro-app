"""API cổng phụ huynh. Xem SRS REPORT §5.4."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.game import service as game
from app.modules.parent import service as svc
from app.modules.report import service as report

router = APIRouter(prefix="/api/v1", tags=["parent"])

_LINK_ROLES = {"owner", "manager", "it_admin"}


@router.post("/org/parents/{parent_id}/children/{student_id}", status_code=201)
async def link_child(
    parent_id: str,
    student_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _LINK_ROLES:
        raise HTTPException(403, "forbidden_role")
    await svc.link_child(s, current.tenant_id, parent_id, student_id, current.user_id)
    return {"linked": True}


@router.get("/me/children")
async def my_children(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "parent":
        raise HTTPException(403, "parents_only")
    return await svc.list_children(s, current.user_id)


async def _ensure_own_child(s: AsyncSession, current: CurrentUser, student_id: str) -> None:
    if current.role != "parent":
        raise HTTPException(403, "parents_only")
    if not await svc.is_parent_of(s, current.user_id, student_id):
        raise HTTPException(403, "not_your_child")


@router.get("/me/children/{student_id}/report")
async def child_report(
    student_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    await _ensure_own_child(s, current, student_id)
    return await report.student_report(s, student_id)


@router.get("/me/children/{student_id}/points")
async def child_points(
    student_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    await _ensure_own_child(s, current, student_id)
    return await game.points_summary(s, current.tenant_id, student_id)
