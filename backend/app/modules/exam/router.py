"""Tạo/liệt kê đề thi. Xem SRS EXAM FR-EXAM-02/03. Giao đề dùng chung endpoint assignment."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.exam import service as svc
from app.modules.practice import service as psvc

router = APIRouter(prefix="/api/v1/exams", tags=["exam"])

_AUTHOR_ROLES = {"owner", "manager", "academic_head", "teacher", "content_editor"}


class BandRow(BaseModel):
    min: float
    band: str


class ExamCreate(BaseModel):
    name: str
    skill: str | None = None
    language: str = "en"
    question_ids: list[str]
    duration_minutes: int
    band_scale: list[BandRow] = []
    review_allowed: bool = True


@router.post("", status_code=201)
async def create_exam(
    body: ExamCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _AUTHOR_ROLES:
        raise HTTPException(403, "forbidden_role")
    try:
        eid = await svc.create_exam(s, current.tenant_id, current.user_id, body.model_dump())
    except psvc.InvalidQuestion as e:
        raise HTTPException(422, str(e)) from None
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="create",
        module="EXAM",
        entity_type="exam",
        entity_id=eid,
        diff={"name": body.name, "n_q": len(body.question_ids), "mins": body.duration_minutes},
    )
    return {"id": eid}


@router.get("")
async def list_exams(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _AUTHOR_ROLES:
        raise HTTPException(403, "forbidden_role")
    return await svc.list_exams(s)
