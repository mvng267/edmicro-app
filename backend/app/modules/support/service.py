"""Ticket hỗ trợ trong tenant + impersonation có audit. Xem SRS SUPPORT §5, FR-SUPPORT.
Impersonation ("đăng nhập thay") LUÔN ghi audit_logs — yêu cầu bảo mật.
"""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Vai trò xử lý ticket của tenant (thấy mọi ticket, đóng, comment).
STAFF_ROLES = {"owner", "manager", "support_agent", "it_admin"}


async def create_ticket(
    s: AsyncSession, tenant_id: str, creator: str, subject: str, body: str
) -> str:
    tid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO tickets (id, tenant_id, subject, body, created_by) "
            "VALUES (:id, :t, :sub, :bo, :by)"
        ),
        {"id": tid, "t": tenant_id, "sub": subject, "bo": body, "by": creator},
    )
    return tid


async def list_tickets(s: AsyncSession, user_id: str, is_staff: bool) -> list[dict]:
    sql = "SELECT id, subject, status, created_by, created_at FROM tickets "
    p = {}
    if not is_staff:
        sql += "WHERE created_by = :u "
        p["u"] = user_id
    sql += "ORDER BY created_at DESC LIMIT 200"
    rows = (await s.execute(text(sql), p)).mappings().all()
    return [
        {
            "id": str(r["id"]),
            "subject": r["subject"],
            "status": r["status"],
            "created_by": str(r["created_by"]),
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


async def ticket_owner(s: AsyncSession, ticket_id: str) -> str | None:
    r = (
        await s.execute(text("SELECT created_by FROM tickets WHERE id = :id"), {"id": ticket_id})
    ).scalar_one_or_none()
    return str(r) if r else None


async def get_ticket(s: AsyncSession, ticket_id: str) -> dict | None:
    t = (
        (
            await s.execute(
                text(
                    "SELECT id, subject, body, status, created_by, created_at "
                    "FROM tickets WHERE id = :id"
                ),
                {"id": ticket_id},
            )
        )
        .mappings()
        .first()
    )
    if t is None:
        return None
    comments = (
        (
            await s.execute(
                text(
                    "SELECT id, author_id, body, created_at FROM ticket_comments "
                    "WHERE ticket_id = :id ORDER BY created_at"
                ),
                {"id": ticket_id},
            )
        )
        .mappings()
        .all()
    )
    return {
        "id": str(t["id"]),
        "subject": t["subject"],
        "body": t["body"],
        "status": t["status"],
        "created_by": str(t["created_by"]),
        "created_at": t["created_at"].isoformat(),
        "comments": [
            {
                "id": str(c["id"]),
                "author_id": str(c["author_id"]),
                "body": c["body"],
                "created_at": c["created_at"].isoformat(),
            }
            for c in comments
        ],
    }


async def add_comment(
    s: AsyncSession, tenant_id: str, ticket_id: str, author: str, body: str
) -> str:
    cid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO ticket_comments (id, tenant_id, ticket_id, author_id, body) "
            "VALUES (:id, :t, :tk, :au, :bo)"
        ),
        {"id": cid, "t": tenant_id, "tk": ticket_id, "au": author, "bo": body},
    )
    await s.execute(text("UPDATE tickets SET updated_at = now() WHERE id = :id"), {"id": ticket_id})
    return cid


async def close_ticket(s: AsyncSession, ticket_id: str) -> None:
    await s.execute(
        text("UPDATE tickets SET status = 'closed', updated_at = now() WHERE id = :id"),
        {"id": ticket_id},
    )


async def user_role(s: AsyncSession, user_id: str) -> str | None:
    return (
        await s.execute(text("SELECT role FROM users WHERE id = :id"), {"id": user_id})
    ).scalar_one_or_none()
