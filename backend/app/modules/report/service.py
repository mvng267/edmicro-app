"""Báo cáo cấp 1–2 (học sinh / lớp) đọc trực tiếp từ điểm chốt. Xem SRS REPORT §5.1.
M5: realtime từ bảng nguồn (pilot nhỏ). Pre-aggregation nightly để v2.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _f(v) -> float | None:
    """Decimal/None → float làm tròn 2 (None giữ nguyên)."""
    return round(float(v), 2) if v is not None else None


async def student_report(s: AsyncSession, student_id: str) -> dict:
    """Tổng quan 1 học sinh: đã giao / đã nộp / điểm TB + danh sách bài đã nộp."""
    summary = (
        (
            await s.execute(
                text(
                    "SELECT count(DISTINCT aa.id) AS assigned, "
                    "count(DISTINCT aa.id) FILTER (WHERE aa.derived_status = 'submitted') "
                    "AS submitted, avg(sub.score) AS avg_score "
                    "FROM assignment_assignees aa "
                    "JOIN assignments a ON a.id = aa.assignment_id AND a.status = 'active' "
                    "LEFT JOIN attempts at ON at.assignee_id = aa.id AND at.status = 'submitted' "
                    "LEFT JOIN submissions sub ON sub.attempt_id = at.id "
                    "WHERE aa.student_id = :sid"
                ),
                {"sid": student_id},
            )
        )
        .mappings()
        .one()
    )
    items = (
        (
            await s.execute(
                text(
                    "SELECT p.name AS practice_name, sub.score, sub.correct_count, "
                    "sub.total_count, at.submitted_at, at.id AS attempt_id "
                    "FROM submissions sub "
                    "JOIN attempts at ON at.id = sub.attempt_id AND at.status = 'submitted' "
                    "JOIN assignment_assignees aa ON aa.id = at.assignee_id "
                    "JOIN assignments a ON a.id = aa.assignment_id "
                    "JOIN practices p ON p.id = a.content_id "
                    "WHERE aa.student_id = :sid "
                    "ORDER BY at.submitted_at DESC"
                ),
                {"sid": student_id},
            )
        )
        .mappings()
        .all()
    )
    return {
        "summary": {
            "assigned": summary["assigned"],
            "submitted": summary["submitted"],
            "avg_score": _f(summary["avg_score"]),
        },
        "items": [
            {
                "practice_name": r["practice_name"],
                "score": _f(r["score"]),
                "correct_count": r["correct_count"],
                "total_count": r["total_count"],
                "submitted_at": r["submitted_at"].isoformat() if r["submitted_at"] else None,
                "attempt_id": str(r["attempt_id"]),
            }
            for r in items
        ],
    }


async def class_report(s: AsyncSession, class_id: str) -> dict:
    """Báo cáo lớp: mỗi HS đã/chưa nộp + điểm TB; điểm TB lớp + tỉ lệ hoàn thành."""
    rows = (
        (
            await s.execute(
                text(
                    "SELECT cs.user_id AS student_id, u.full_name, u.username, "
                    "count(DISTINCT aa.id) AS assigned, "
                    "count(DISTINCT aa.id) FILTER (WHERE aa.derived_status = 'submitted') "
                    "AS submitted, avg(sub.score) AS avg_score "
                    "FROM class_students cs "
                    "JOIN users u ON u.id = cs.user_id "
                    "LEFT JOIN assignments a "
                    "ON a.class_id = cs.class_id AND a.status = 'active' "
                    "LEFT JOIN assignment_assignees aa "
                    "ON aa.assignment_id = a.id AND aa.student_id = cs.user_id "
                    "LEFT JOIN attempts at ON at.assignee_id = aa.id AND at.status = 'submitted' "
                    "LEFT JOIN submissions sub ON sub.attempt_id = at.id "
                    "WHERE cs.class_id = :cid AND cs.left_at IS NULL "
                    "GROUP BY cs.user_id, u.full_name, u.username "
                    "ORDER BY u.full_name, u.username"
                ),
                {"cid": class_id},
            )
        )
        .mappings()
        .all()
    )
    students = [
        {
            "student_id": str(r["student_id"]),
            "full_name": r["full_name"] or r["username"],
            "assigned": r["assigned"],
            "submitted": r["submitted"],
            "avg_score": _f(r["avg_score"]),
        }
        for r in rows
    ]
    assigned_total = sum(x["assigned"] for x in students)
    submitted_total = sum(x["submitted"] for x in students)
    # điểm TB lớp = trung bình có trọng số theo số bài đã nộp của mỗi HS
    weighted = sum(x["avg_score"] * x["submitted"] for x in students if x["avg_score"] is not None)
    class_avg = round(weighted / submitted_total, 2) if submitted_total else None
    completion_rate = round(submitted_total / assigned_total, 2) if assigned_total else None
    return {
        "summary": {
            "student_count": len(students),
            "assigned_total": assigned_total,
            "submitted_total": submitted_total,
            "class_avg": class_avg,
            "completion_rate": completion_rate,
        },
        "students": students,
    }
