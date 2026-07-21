"""Thông báo in-app theo catalog sự kiện. Xem SRS NOTIF §5.
In-app luôn ghi bản ghi bền vững; kênh email/ZNS/SMS chỉ log (stub) ở M8.
"""

from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notify import channels

# Mã sự kiện (catalog rút gọn M8) — xem bảng catalog trong SRS NOTIF §5.
EVT_ASSIGNMENT_CREATED = "assignment_created"
EVT_DEADLINE_REMINDER = "deadline_reminder"
EVT_GRADE_FINALIZED = "grade_finalized"
EVT_ATTENDANCE_ABSENT = "attendance_absent"


async def notify(
    s: AsyncSession,
    tenant_id: str,
    recipients: Iterable[str],
    event_code: str,
    title: str,
    body: str = "",
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    extra_channels: Iterable[str] = (),
) -> int:
    """Ghi thông báo in-app cho từng người nhận; kênh trả phí chỉ log (stub). Trả số bản ghi."""
    ids = list(dict.fromkeys(recipients))  # loại trùng, giữ thứ tự
    for uid in ids:
        await s.execute(
            text(
                "INSERT INTO notifications "
                "(tenant_id, user_id, event_code, title, body, entity_type, entity_id) "
                "VALUES (:t, :u, :ev, :ti, :bo, :et, :ei)"
            ),
            {
                "t": tenant_id,
                "u": uid,
                "ev": event_code,
                "ti": title,
                "bo": body,
                "et": entity_type,
                "ei": entity_id,
            },
        )
        for ch in extra_channels:
            if ch in channels.STUB_CHANNELS:
                channels.deliver_stub(ch, uid, title, body)
    return len(ids)


async def list_for_user(s: AsyncSession, user_id: str, limit: int = 50) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT id, event_code, title, body, entity_type, entity_id, read_at, "
                    "created_at FROM notifications WHERE user_id = :u "
                    "ORDER BY created_at DESC LIMIT :lim"
                ),
                {"u": user_id, "lim": limit},
            )
        )
        .mappings()
        .all()
    )
    return [
        {
            "id": str(r["id"]),
            "event_code": r["event_code"],
            "title": r["title"],
            "body": r["body"],
            "entity_type": r["entity_type"],
            "entity_id": str(r["entity_id"]) if r["entity_id"] else None,
            "read": r["read_at"] is not None,
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


async def unread_count(s: AsyncSession, user_id: str) -> int:
    return (
        await s.execute(
            text("SELECT count(*) FROM notifications WHERE user_id = :u AND read_at IS NULL"),
            {"u": user_id},
        )
    ).scalar_one()


async def mark_read(s: AsyncSession, user_id: str, notif_id: str) -> bool:
    r = (
        await s.execute(
            text(
                "UPDATE notifications SET read_at = now() "
                "WHERE id = :id AND user_id = :u AND read_at IS NULL RETURNING id"
            ),
            {"id": notif_id, "u": user_id},
        )
    ).first()
    return r is not None


async def mark_all_read(s: AsyncSession, user_id: str) -> int:
    r = await s.execute(
        text("UPDATE notifications SET read_at = now() WHERE user_id = :u AND read_at IS NULL"),
        {"u": user_id},
    )
    return r.rowcount


async def remind_due_assignments(s: AsyncSession, tenant_id: str, within_hours: int = 24) -> int:
    """Nhắc HS chưa nộp các bài sắp tới hạn (trong within_hours). Không nhắc trùng 1 bài/HS."""
    rows = (
        (
            await s.execute(
                text(
                    "SELECT aa.student_id, a.id AS assignment_id, p.name "
                    "FROM assignment_assignees aa "
                    "JOIN assignments a ON a.id = aa.assignment_id AND a.status = 'active' "
                    "JOIN practices p ON p.id = a.content_id "
                    "WHERE aa.derived_status <> 'submitted' "
                    "AND a.due_at IS NOT NULL "
                    "AND a.due_at BETWEEN now() AND now() + (:h * interval '1 hour') "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM notifications n WHERE n.user_id = aa.student_id "
                    "  AND n.event_code = :ev AND n.entity_id = a.id)"
                ),
                {"h": within_hours, "ev": EVT_DEADLINE_REMINDER},
            )
        )
        .mappings()
        .all()
    )
    count = 0
    for r in rows:
        count += await notify(
            s,
            tenant_id,
            [str(r["student_id"])],
            EVT_DEADLINE_REMINDER,
            "Sắp tới hạn nộp bài",
            f"Bài “{r['name']}” sắp tới hạn. Hãy hoàn thành và nộp trước hạn.",
            entity_type="assignment",
            entity_id=str(r["assignment_id"]),
            extra_channels=["zns"],
        )
    return count
