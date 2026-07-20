"""Giao bài: fan-out cho học sinh trong lớp; danh sách việc cần làm của học sinh.
Xem SRS ASSIGN. M3: content_kind='practice'.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def create_assignment(
    s: AsyncSession, tenant_id: str, creator: str, data: dict[str, Any]
) -> dict:
    aid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO assignments (id, tenant_id, content_kind, content_id, class_id, "
            "due_at, created_by) VALUES (:id, :t, 'practice', :c, :cl, :due, :by)"
        ),
        {
            "id": aid,
            "t": tenant_id,
            "c": data["content_id"],
            "cl": data["class_id"],
            "due": data.get("due_at"),
            "by": creator,
        },
    )
    # fan-out cho học sinh đang trong lớp (chưa rời)
    students = (
        (
            await s.execute(
                text("SELECT user_id FROM class_students WHERE class_id = :cl AND left_at IS NULL"),
                {"cl": data["class_id"]},
            )
        )
        .scalars()
        .all()
    )
    for sid in students:
        await s.execute(
            text(
                "INSERT INTO assignment_assignees (tenant_id, assignment_id, student_id) "
                "VALUES (:t, :a, :s) ON CONFLICT DO NOTHING"
            ),
            {"t": tenant_id, "a": aid, "s": str(sid)},
        )
    return {"id": aid, "assignee_count": len(students)}


async def enroll_backfill(s: AsyncSession, tenant_id: str, class_id: str, student_id: str) -> int:
    """Học sinh vào lớp muộn -> nhận các assignment active còn hạn của lớp."""
    now = datetime.now(UTC)
    rows = (
        (
            await s.execute(
                text(
                    "SELECT id FROM assignments WHERE class_id = :cl AND status = 'active' "
                    "AND (due_at IS NULL OR due_at > :now)"
                ),
                {"cl": class_id, "now": now},
            )
        )
        .scalars()
        .all()
    )
    for aid in rows:
        await s.execute(
            text(
                "INSERT INTO assignment_assignees (tenant_id, assignment_id, student_id) "
                "VALUES (:t, :a, :s) ON CONFLICT DO NOTHING"
            ),
            {"t": tenant_id, "a": str(aid), "s": student_id},
        )
    return len(rows)


async def list_student_assignments(s: AsyncSession, student_id: str) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT aa.id AS assignee_id, aa.derived_status, aa.submitted_at, "
                    "a.id AS assignment_id, a.due_at, p.name AS practice_name, "
                    "(SELECT at.id FROM attempts at WHERE at.assignee_id = aa.id "
                    "AND at.status = 'submitted' ORDER BY at.submitted_at DESC LIMIT 1"
                    ") AS attempt_id "
                    "FROM assignment_assignees aa "
                    "JOIN assignments a ON a.id = aa.assignment_id "
                    "JOIN practices p ON p.id = a.content_id "
                    "WHERE aa.student_id = :sid AND a.status = 'active' "
                    "ORDER BY a.due_at NULLS LAST, a.created_at DESC"
                ),
                {"sid": student_id},
            )
        )
        .mappings()
        .all()
    )
    now = datetime.now(UTC)
    out = []
    for r in rows:
        status = r["derived_status"]
        if status not in ("submitted",) and r["due_at"] is not None and r["due_at"] < now:
            status = "overdue"
        out.append(
            {
                "assignee_id": str(r["assignee_id"]),
                "assignment_id": str(r["assignment_id"]),
                "practice_name": r["practice_name"],
                "due_at": r["due_at"].isoformat() if r["due_at"] else None,
                "status": status,
                "attempt_id": str(r["attempt_id"]) if r["attempt_id"] else None,
            }
        )
    return out
