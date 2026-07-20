from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.assignment import service as svc
from app.modules.practice import attempt_service as att
from app.modules.practice import service as psvc

router = APIRouter(prefix="/api/v1", tags=["assignment"])

_AUTHOR_ROLES = {"owner", "manager", "academic_head", "teacher"}


class AssignmentCreate(BaseModel):
    content_id: str  # practice id
    class_id: str
    due_at: datetime | None = None


class AnswerSave(BaseModel):
    question_version_id: str
    payload: dict


@router.post("/assignments", status_code=201)
async def create_assignment(
    body: AssignmentCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _AUTHOR_ROLES:
        raise HTTPException(403, "forbidden_role")
    result = await svc.create_assignment(s, current.tenant_id, current.user_id, body.model_dump())
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="create",
        module="ASSIGN",
        entity_type="assignment",
        entity_id=result["id"],
        diff={"assignees": result["assignee_count"]},
    )
    return result


@router.get("/me/assignments")
async def my_assignments(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    return await svc.list_student_assignments(s, current.user_id)


@router.post("/assignments/{assignee_id}/start")
async def start(
    assignee_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    try:
        attempt_id = await att.start_attempt(s, current.tenant_id, assignee_id, current.user_id)
    except att.NotFound:
        raise HTTPException(404, "not_found") from None
    except att.Forbidden:
        raise HTTPException(403, "not_your_assignment") from None
    # trả câu hỏi (ẩn đáp án) của practice tương ứng
    practice_id = (
        await s.execute(
            _practice_of_assignee(),
            {"a": assignee_id},
        )
    ).scalar_one()
    practice = await psvc.get_practice(s, str(practice_id), for_attempt=True)
    return {"attempt_id": attempt_id, "practice": practice}


def _practice_of_assignee():
    from sqlalchemy import text

    return text(
        "SELECT a.content_id FROM assignment_assignees aa "
        "JOIN assignments a ON a.id = aa.assignment_id WHERE aa.id = :a"
    )


@router.put("/attempts/{attempt_id}/answers")
async def save_answer(
    attempt_id: str,
    body: AnswerSave,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    try:
        await att.save_answer(
            s,
            current.tenant_id,
            attempt_id,
            current.user_id,
            body.question_version_id,
            body.payload,
        )
    except att.NotFound:
        raise HTTPException(404, "not_found") from None
    except att.Forbidden:
        raise HTTPException(403, "not_your_attempt") from None
    except att.NotEditable:
        raise HTTPException(409, "attempt_submitted") from None
    return {"saved": True}


@router.post("/attempts/{attempt_id}/submit")
async def submit(
    attempt_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    try:
        await att.submit_attempt(s, attempt_id, current.user_id)
    except att.NotFound:
        raise HTTPException(404, "not_found") from None
    except att.Forbidden:
        raise HTTPException(403, "not_your_attempt") from None
    return {"submitted": True}
