"""Hàng đợi review + chốt điểm câu mở cho GV. Xem SRS GRADE §5.3, FR-GRADE-06/07/08."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.grading import service as svc

router = APIRouter(prefix="/api/v1/grading", tags=["grading"])

_REVIEWER_ROLES = {"owner", "manager", "academic_head", "teacher", "assistant"}
_TENANT_WIDE = {"owner", "manager", "academic_head"}


class FinalizeBody(BaseModel):
    final_score: float = Field(ge=0.0, le=1.0)
    feedback: str | None = None


async def _staff_of_class(s: AsyncSession, user_id: str, class_id: str) -> bool:
    return (
        await s.execute(
            text("SELECT 1 FROM class_staff WHERE class_id = :c AND user_id = :u LIMIT 1"),
            {"c": class_id, "u": user_id},
        )
    ).first() is not None


async def _attempt_class(s: AsyncSession, attempt_id: str) -> str | None:
    return (
        await s.execute(
            text(
                "SELECT a.class_id FROM attempts at "
                "JOIN assignment_assignees aa ON aa.id = at.assignee_id "
                "JOIN assignments a ON a.id = aa.assignment_id "
                "WHERE at.id = :att"
            ),
            {"att": attempt_id},
        )
    ).scalar_one_or_none()


async def _attempt_student(s: AsyncSession, attempt_id: str) -> str | None:
    r = (
        await s.execute(
            text(
                "SELECT aa.student_id FROM attempts at "
                "JOIN assignment_assignees aa ON aa.id = at.assignee_id WHERE at.id = :att"
            ),
            {"att": attempt_id},
        )
    ).scalar_one_or_none()
    return str(r) if r else None


async def _answer_attempt(s: AsyncSession, answer_id: str) -> str | None:
    return (
        await s.execute(
            text("SELECT attempt_id FROM answers WHERE id = :id"),
            {"id": answer_id},
        )
    ).scalar_one_or_none()


async def _ensure_can_access(s: AsyncSession, current: CurrentUser, class_id: str | None) -> None:
    if current.role not in _REVIEWER_ROLES:
        raise HTTPException(403, "forbidden_role")
    if class_id is None:
        raise HTTPException(404, "not_found")
    if current.role not in _TENANT_WIDE and not await _staff_of_class(s, current.user_id, class_id):
        raise HTTPException(403, "not_your_class")


@router.get("/queue")
async def queue(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    """Hàng đợi câu mở chờ chốt, gộp theo lượt làm; ưu tiên needs_manual/độ tự tin thấp."""
    if current.role not in _REVIEWER_ROLES:
        raise HTTPException(403, "forbidden_role")
    scope = (
        ""
        if current.role in _TENANT_WIDE
        else ("AND a.class_id IN (SELECT class_id FROM class_staff WHERE user_id = :u) ")
    )
    rows = (
        (
            await s.execute(
                text(
                    "SELECT at.id AS attempt_id, aa.student_id, "
                    "COALESCE(NULLIF(u.full_name, ''), u.username) AS student_name, "
                    "a.class_id, c.name AS class_name, p.name AS practice_name, "
                    "count(*) AS pending_count, max(gj.priority) AS priority, "
                    "bool_or(gj.status = 'needs_manual') AS has_manual "
                    "FROM grading_jobs gj "
                    "JOIN attempts at ON at.id = gj.attempt_id "
                    "JOIN assignment_assignees aa ON aa.id = at.assignee_id "
                    "JOIN assignments a ON a.id = aa.assignment_id "
                    "JOIN classes c ON c.id = a.class_id "
                    "JOIN practices p ON p.id = a.content_id "
                    "JOIN users u ON u.id = aa.student_id "
                    "WHERE gj.status IN ('ai_graded', 'needs_manual') "
                    + scope
                    + "GROUP BY at.id, aa.student_id, u.full_name, u.username, "
                    "a.class_id, c.name, p.name "
                    "ORDER BY priority DESC, pending_count DESC"
                ),
                {"u": current.user_id},
            )
        )
        .mappings()
        .all()
    )
    return [
        {
            "attempt_id": str(r["attempt_id"]),
            "student_id": str(r["student_id"]),
            "student_name": r["student_name"],
            "class_id": str(r["class_id"]),
            "class_name": r["class_name"],
            "practice_name": r["practice_name"],
            "pending_count": r["pending_count"],
            "priority": r["priority"],
            "has_manual": r["has_manual"],
        }
        for r in rows
    ]


@router.get("/attempts/{attempt_id}")
async def review_detail(
    attempt_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    """Chi tiết review: từng câu mở + bài làm HS + điểm AI đề xuất."""
    class_id = await _attempt_class(s, attempt_id)
    await _ensure_can_access(s, current, str(class_id) if class_id else None)
    rows = (
        (
            await s.execute(
                text(
                    "SELECT pq.sort_order, v.content, ans.id AS answer_id, ans.payload, "
                    "ans.ai_score, ans.ai_feedback, ans.ai_confidence, ans.final_score, "
                    "ans.grade_status "
                    "FROM answers ans "
                    "JOIN question_versions v ON v.id = ans.question_version_id "
                    "JOIN questions q ON q.id = v.question_id "
                    "JOIN attempts at ON at.id = ans.attempt_id "
                    "JOIN assignment_assignees aa ON aa.id = at.assignee_id "
                    "JOIN assignments a ON a.id = aa.assignment_id "
                    "JOIN practice_questions pq ON pq.practice_id = a.content_id "
                    "AND pq.question_version_id = ans.question_version_id "
                    "WHERE ans.attempt_id = :att AND q.type = 'writing' "
                    "ORDER BY pq.sort_order"
                ),
                {"att": attempt_id},
            )
        )
        .mappings()
        .all()
    )

    def _num(v):
        return float(v) if v is not None else None

    return {
        "attempt_id": attempt_id,
        "items": [
            {
                "answer_id": str(r["answer_id"]),
                "sort_order": r["sort_order"],
                "prompt": (r["content"] or {}).get("prompt"),
                "rubric": (r["content"] or {}).get("rubric"),
                "your_answer": (r["payload"] or {}).get("text"),
                "ai_score": _num(r["ai_score"]),
                "ai_feedback": r["ai_feedback"],
                "ai_confidence": _num(r["ai_confidence"]),
                "final_score": _num(r["final_score"]),
                "grade_status": r["grade_status"],
            }
            for r in rows
        ],
    }


@router.post("/answers/{answer_id}/finalize")
async def finalize(
    answer_id: str,
    body: FinalizeBody,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    """GV chốt điểm 1 câu mở (0..1) + nhận xét. Tính lại điểm bài."""
    attempt_id = await _answer_attempt(s, answer_id)
    if attempt_id is None:
        raise HTTPException(404, "answer_not_found")
    class_id = await _attempt_class(s, str(attempt_id))
    await _ensure_can_access(s, current, str(class_id) if class_id else None)
    try:
        result = await svc.finalize_open_answer(
            s, current.tenant_id, answer_id, body.final_score, body.feedback
        )
    except ValueError:
        raise HTTPException(409, "not_reviewable") from None
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="finalize_grade",
        module="GRADE",
        entity_type="answer",
        entity_id=answer_id,
        diff={"final_score": body.final_score},
    )
    # NOTIF: báo HS đã có điểm chốt (chỉ khi bài đã final — hết câu chờ)
    if result.get("status") == "final":
        from app.modules.notify import service as notify

        student = await _attempt_student(s, str(attempt_id))
        if student:
            await notify.notify(
                s,
                current.tenant_id,
                [student],
                notify.EVT_GRADE_FINALIZED,
                "Đã có kết quả chấm",
                "Giáo viên đã chốt điểm bài của bạn. Xem kết quả và nhận xét.",
                entity_type="attempt",
                entity_id=str(attempt_id),
                extra_channels=["email"],
            )
    return result
