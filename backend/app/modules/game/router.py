"""API gamification: điểm/streak/badge của HS + bảng xếp hạng lớp. Xem SRS GAME FR-GAME."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.game import service as svc

router = APIRouter(prefix="/api/v1", tags=["game"])

_STAFF_ROLES = {"owner", "manager", "academic_head", "teacher", "assistant"}


@router.get("/me/points")
async def my_points(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    return await svc.points_summary(s, current.tenant_id, current.user_id)


@router.get("/classes/{class_id}/leaderboard")
async def leaderboard(
    class_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    # HS xem BXH lớp mình; staff xem lớp trong phạm vi (RLS đã lọc tenant).
    if current.role == "student":
        member = (
            await s.execute(
                text(
                    "SELECT 1 FROM class_students WHERE class_id = :c AND user_id = :u "
                    "AND left_at IS NULL LIMIT 1"
                ),
                {"c": class_id, "u": current.user_id},
            )
        ).first()
        if member is None:
            raise HTTPException(403, "not_your_class")
    elif current.role not in _STAFF_ROLES:
        raise HTTPException(403, "forbidden_role")
    return await svc.class_leaderboard(s, class_id)
