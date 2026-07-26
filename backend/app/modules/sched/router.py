"""API lịch học + điểm danh. Xem SRS SCHED FR-SCHED."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.sched import service as svc

router = APIRouter(prefix="/api/v1", tags=["sched"])

_STAFF_ROLES = {"owner", "manager", "academic_head", "teacher", "assistant"}
_TENANT_WIDE = {"owner", "manager", "academic_head"}


class SessionCreate(BaseModel):
    class_id: str
    starts_at: datetime
    ends_at: datetime
    topic: str = ""
    online_link: str | None = None


class RecurringCreate(BaseModel):
    class_id: str
    weekdays: list[int]  # 0=Thứ 2 … 6=Chủ nhật
    start_time: str  # "18:00"
    duration_minutes: int
    from_date: str  # "YYYY-MM-DD"
    to_date: str
    topic: str = ""
    online_link: str | None = None


class AttendanceRecord(BaseModel):
    student_id: str
    status: str = "present"
    note: str | None = None


class AttendanceMark(BaseModel):
    records: list[AttendanceRecord]


async def _staff_of_class(s: AsyncSession, user_id: str, class_id: str) -> bool:
    return (
        await s.execute(
            text("SELECT 1 FROM class_staff WHERE class_id = :c AND user_id = :u LIMIT 1"),
            {"c": class_id, "u": user_id},
        )
    ).first() is not None


async def _ensure_class(s: AsyncSession, current: CurrentUser, class_id: str | None) -> None:
    if current.role not in _STAFF_ROLES:
        raise HTTPException(403, "forbidden_role")
    if class_id is None:
        raise HTTPException(404, "not_found")
    if current.role not in _TENANT_WIDE and not await _staff_of_class(s, current.user_id, class_id):
        raise HTTPException(403, "not_your_class")


@router.post("/sessions", status_code=201)
async def create_session(
    body: SessionCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    await _ensure_class(s, current, body.class_id)
    sid = await svc.create_session(s, current.tenant_id, body.model_dump())
    return {"id": sid}


@router.post("/sessions/recurring", status_code=201)
async def create_recurring(
    body: RecurringCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    """Sinh buổi học lặp hằng tuần trong khoảng ngày (giờ Việt Nam)."""
    await _ensure_class(s, current, body.class_id)
    try:
        return await svc.create_recurring(s, current.tenant_id, body.model_dump())
    except ValueError as e:
        raise HTTPException(422, str(e)) from None


@router.get("/sessions")
async def list_sessions(
    class_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    await _ensure_class(s, current, class_id)
    return await svc.list_class_sessions(s, class_id)


@router.get("/me/sessions")
async def my_sessions(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    return await svc.list_student_sessions(s, current.user_id)


@router.post("/sessions/{session_id}/attendance")
async def mark_attendance(
    session_id: str,
    body: AttendanceMark,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    class_id = await svc._session_class(s, session_id)
    await _ensure_class(s, current, str(class_id) if class_id else None)
    try:
        return await svc.mark_attendance(
            s, current.tenant_id, session_id, [r.model_dump() for r in body.records]
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from None


@router.delete("/sessions/{session_id}", status_code=200)
async def delete_session(
    session_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    class_id = await svc._session_class(s, session_id)
    await _ensure_class(s, current, str(class_id) if class_id else None)
    try:
        await svc.delete_session(s, session_id)
    except KeyError:
        raise HTTPException(404, "not_found") from None
    return {"deleted": True}


@router.get("/sessions/{session_id}/attendance")
async def get_attendance(
    session_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    class_id = await svc._session_class(s, session_id)
    await _ensure_class(s, current, str(class_id) if class_id else None)
    return await svc.session_attendance(s, session_id)
