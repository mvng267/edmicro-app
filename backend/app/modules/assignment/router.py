from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.assignment import service as svc
from app.modules.grading import service as grading
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
    # NOTIF: báo HS được giao bài mới (in-app + email stub)
    from sqlalchemy import text

    from app.modules.notify import service as notify

    info = (
        (
            await s.execute(
                text(
                    "SELECT p.name, array_agg(aa.student_id::text) AS students "
                    "FROM assignment_assignees aa "
                    "JOIN assignments a ON a.id = aa.assignment_id "
                    "JOIN practices p ON p.id = a.content_id "
                    "WHERE aa.assignment_id = :aid GROUP BY p.name"
                ),
                {"aid": result["id"]},
            )
        )
        .mappings()
        .first()
    )
    if info and info["students"]:
        await notify.notify(
            s,
            current.tenant_id,
            info["students"],
            notify.EVT_ASSIGNMENT_CREATED,
            "Bài mới được giao",
            f"Bạn được giao bài “{info['name']}”.",
            entity_type="assignment",
            entity_id=result["id"],
            extra_channels=["email"],
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
    # đề thi: kèm đồng hồ server (hạn nộp + thời lượng) để client đếm ngược
    exam = (
        (
            await s.execute(
                _exam_clock_of_attempt(),
                {"att": attempt_id},
            )
        )
        .mappings()
        .first()
    )
    return {
        "attempt_id": attempt_id,
        "practice": practice,
        "deadline_at": exam["deadline_at"].isoformat() if exam and exam["deadline_at"] else None,
        "duration_minutes": exam["duration_minutes"] if exam else None,
    }


def _exam_clock_of_attempt():
    from sqlalchemy import text

    return text(
        "SELECT at.deadline_at, em.duration_minutes FROM attempts at "
        "JOIN assignment_assignees aa ON aa.id = at.assignee_id "
        "JOIN assignments a ON a.id = aa.assignment_id "
        "JOIN exam_meta em ON em.content_id = a.content_id "
        "WHERE at.id = :att"
    )


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
        result = await att.submit_attempt(s, current.tenant_id, attempt_id, current.user_id)
    except att.NotFound:
        raise HTTPException(404, "not_found") from None
    except att.Forbidden:
        raise HTTPException(403, "not_your_attempt") from None
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="auto_grade",
        module="GRADE",
        entity_type="attempt",
        entity_id=attempt_id,
        diff=result,
    )
    # GAME: cộng điểm khi nộp (lần đầu theo assignment) + điểm cao
    from app.modules.game import service as game

    await game.award_for_submission(s, current.tenant_id, attempt_id, float(result["score"]))
    return {"submitted": True, **result}


@router.get("/attempts/{attempt_id}/result")
async def get_result(
    attempt_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    # xác thực attempt thuộc student + đã nộp
    info = await att._attempt_owner_and_status(s, attempt_id)
    if info is None:
        raise HTTPException(404, "not_found")
    owner, status = info
    if owner != current.user_id:
        raise HTTPException(403, "not_your_attempt")
    if status != "submitted":
        raise HTTPException(409, "not_submitted")
    result = await grading.get_result(s, attempt_id)
    if result is None:
        raise HTTPException(404, "not_graded")
    return result
