"""Lượt làm bài: start (1 attempt/assignee), autosave answer (upsert), submit.
Xem SRS PRACTICE §5, SRS GRADE (chấm ở M4). M3 chỉ lưu câu trả lời.
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.grading import service as grading


class Forbidden(Exception):
    pass


class NotFound(Exception):
    pass


class NotEditable(Exception):
    pass


async def _assignee_owner(s: AsyncSession, assignee_id: str) -> str | None:
    return (
        await s.execute(
            text("SELECT student_id FROM assignment_assignees WHERE id = :id"),
            {"id": assignee_id},
        )
    ).scalar_one_or_none()


async def start_attempt(s: AsyncSession, tenant_id: str, assignee_id: str, student_id: str) -> str:
    owner = await _assignee_owner(s, assignee_id)
    if owner is None:
        raise NotFound("assignee_not_found")
    if str(owner) != student_id:
        raise Forbidden("not_your_assignment")

    existing = (
        await s.execute(
            text(
                "SELECT id FROM attempts WHERE assignee_id = :a AND status = 'in_progress' "
                "ORDER BY started_at DESC LIMIT 1"
            ),
            {"a": assignee_id},
        )
    ).scalar_one_or_none()
    if existing is not None:
        return str(existing)

    aid = str(uuid.uuid4())
    await s.execute(
        text("INSERT INTO attempts (id, tenant_id, assignee_id) VALUES (:id, :t, :a)"),
        {"id": aid, "t": tenant_id, "a": assignee_id},
    )
    await s.execute(
        text(
            "UPDATE assignment_assignees SET derived_status = 'in_progress' "
            "WHERE id = :a AND derived_status = 'not_opened'"
        ),
        {"a": assignee_id},
    )
    return aid


async def _attempt_owner_and_status(s: AsyncSession, attempt_id: str) -> tuple[str, str] | None:
    row = (
        await s.execute(
            text(
                "SELECT aa.student_id, at.status FROM attempts at "
                "JOIN assignment_assignees aa ON aa.id = at.assignee_id "
                "WHERE at.id = :id"
            ),
            {"id": attempt_id},
        )
    ).first()
    return (str(row[0]), row[1]) if row else None


async def save_answer(
    s: AsyncSession,
    tenant_id: str,
    attempt_id: str,
    student_id: str,
    question_version_id: str,
    payload: dict[str, Any],
) -> None:
    info = await _attempt_owner_and_status(s, attempt_id)
    if info is None:
        raise NotFound("attempt_not_found")
    owner, status = info
    if owner != student_id:
        raise Forbidden("not_your_attempt")
    if status != "in_progress":
        raise NotEditable("attempt_submitted")
    await s.execute(
        text(
            "INSERT INTO answers (tenant_id, attempt_id, question_version_id, payload) "
            "VALUES (:t, :at, :q, CAST(:p AS jsonb)) "
            "ON CONFLICT (attempt_id, question_version_id) "
            "DO UPDATE SET payload = EXCLUDED.payload, saved_at = now()"
        ),
        {
            "t": tenant_id,
            "at": attempt_id,
            "q": question_version_id,
            "p": json.dumps(payload, ensure_ascii=False),
        },
    )


async def submit_attempt(s: AsyncSession, tenant_id: str, attempt_id: str, student_id: str) -> dict:
    info = await _attempt_owner_and_status(s, attempt_id)
    if info is None:
        raise NotFound("attempt_not_found")
    owner, status = info
    if owner != student_id:
        raise Forbidden("not_your_attempt")
    now = datetime.now(UTC)
    await s.execute(
        text("UPDATE attempts SET status = 'submitted', submitted_at = :now WHERE id = :id"),
        {"now": now, "id": attempt_id},
    )
    # cập nhật assignee: submitted + is_late nếu quá hạn
    await s.execute(
        text(
            "UPDATE assignment_assignees aa "
            "SET derived_status = 'submitted', submitted_at = :now, "
            "is_late = COALESCE("
            "(SELECT a.due_at < :now FROM assignments a WHERE a.id = aa.assignment_id), false) "
            "FROM attempts at WHERE at.id = :att AND aa.id = at.assignee_id"
        ),
        {"now": now, "att": attempt_id},
    )
    # chấm tự động câu đóng ngay khi nộp (M4)
    return await grading.grade_attempt(s, tenant_id, attempt_id)
