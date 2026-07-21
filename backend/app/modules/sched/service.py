"""Lịch học (buổi) + điểm danh. Xem SRS SCHED §5, FR-SCHED.
M8: tạo buổi lẻ + điểm danh bulk ("tất cả có mặt rồi chỉnh lệch"); vắng → NOTIF attendance_absent.
"""

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notify import service as notify

VALID_STATUS = {"present", "absent", "late", "excused"}


async def create_session(s: AsyncSession, tenant_id: str, data: dict[str, Any]) -> str:
    sid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO class_sessions "
            "(id, tenant_id, class_id, starts_at, ends_at, topic, online_link) "
            "VALUES (:id, :t, :c, :st, :en, :tp, :ln)"
        ),
        {
            "id": sid,
            "t": tenant_id,
            "c": data["class_id"],
            "st": data["starts_at"],
            "en": data["ends_at"],
            "tp": data.get("topic", ""),
            "ln": data.get("online_link"),
        },
    )
    return sid


def _row(r) -> dict:
    return {
        "id": str(r["id"]),
        "class_id": str(r["class_id"]),
        "class_name": r.get("class_name"),
        "starts_at": r["starts_at"].isoformat(),
        "ends_at": r["ends_at"].isoformat(),
        "topic": r["topic"],
        "online_link": r["online_link"],
    }


async def list_class_sessions(s: AsyncSession, class_id: str) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT id, class_id, starts_at, ends_at, topic, online_link "
                    "FROM class_sessions WHERE class_id = :c ORDER BY starts_at DESC"
                ),
                {"c": class_id},
            )
        )
        .mappings()
        .all()
    )
    return [_row(r) for r in rows]


async def list_student_sessions(s: AsyncSession, student_id: str) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT cs.id, cs.class_id, c.name AS class_name, cs.starts_at, cs.ends_at, "
                    "cs.topic, cs.online_link FROM class_sessions cs "
                    "JOIN classes c ON c.id = cs.class_id "
                    "JOIN class_students st ON st.class_id = cs.class_id AND st.left_at IS NULL "
                    "WHERE st.user_id = :u ORDER BY cs.starts_at DESC"
                ),
                {"u": student_id},
            )
        )
        .mappings()
        .all()
    )
    return [_row(r) for r in rows]


async def _session_class(s: AsyncSession, session_id: str) -> str | None:
    return (
        await s.execute(
            text("SELECT class_id FROM class_sessions WHERE id = :id"),
            {"id": session_id},
        )
    ).scalar_one_or_none()


async def session_roster(s: AsyncSession, session_id: str) -> list[dict]:
    """Danh sách HS của lớp + trạng thái điểm danh hiện tại (mặc định chưa có = present khi lưu)."""
    rows = (
        (
            await s.execute(
                text(
                    "SELECT cst.user_id AS student_id, "
                    "COALESCE(NULLIF(u.full_name, ''), u.username) AS full_name, "
                    "a.status, a.note "
                    "FROM class_sessions cs "
                    "JOIN class_students cst "
                    "ON cst.class_id = cs.class_id AND cst.left_at IS NULL "
                    "JOIN users u ON u.id = cst.user_id "
                    "LEFT JOIN attendance a ON a.session_id = cs.id AND a.student_id = cst.user_id "
                    "WHERE cs.id = :sid ORDER BY u.full_name, u.username"
                ),
                {"sid": session_id},
            )
        )
        .mappings()
        .all()
    )
    return [
        {
            "student_id": str(r["student_id"]),
            "full_name": r["full_name"],
            "status": r["status"],
            "note": r["note"],
        }
        for r in rows
    ]


async def mark_attendance(
    s: AsyncSession, tenant_id: str, session_id: str, records: list[dict[str, Any]]
) -> dict:
    """Điểm danh bulk (upsert); HS vắng → thông báo attendance_absent. Trả {marked, absent}."""
    absent_ids: list[str] = []
    for rec in records:
        status = rec.get("status", "present")
        if status not in VALID_STATUS:
            raise ValueError(f"invalid_status:{status}")
        await s.execute(
            text(
                "INSERT INTO attendance (tenant_id, session_id, student_id, status, note) "
                "VALUES (:t, :s, :u, :st, :n) "
                "ON CONFLICT (session_id, student_id) "
                "DO UPDATE SET status = EXCLUDED.status, note = EXCLUDED.note, marked_at = now()"
            ),
            {
                "t": tenant_id,
                "s": session_id,
                "u": rec["student_id"],
                "st": status,
                "n": rec.get("note"),
            },
        )
        if status == "absent":
            absent_ids.append(str(rec["student_id"]))
    if absent_ids:
        await notify.notify(
            s,
            tenant_id,
            absent_ids,
            notify.EVT_ATTENDANCE_ABSENT,
            "Điểm danh: vắng mặt",
            "Bạn được ghi nhận vắng mặt trong buổi học. Liên hệ giáo viên nếu có nhầm lẫn.",
            entity_type="session",
            entity_id=session_id,
            extra_channels=["zns"],
        )
    return {"marked": len(records), "absent": len(absent_ids)}


async def session_attendance(s: AsyncSession, session_id: str) -> list[dict]:
    return await session_roster(s, session_id)
