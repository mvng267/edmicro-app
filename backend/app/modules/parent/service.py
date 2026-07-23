"""Cổng phụ huynh: liên kết phụ huynh–học sinh + truy cập dữ liệu của con.
Xem SRS REPORT §5.4. Dùng bảng parent_students (parent_user_id, student_user_id)."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def link_child(
    s: AsyncSession, tenant_id: str, parent_id: str, student_id: str, linked_by: str
) -> None:
    await s.execute(
        text(
            "INSERT INTO parent_students (tenant_id, parent_user_id, student_user_id, linked_by) "
            "SELECT :t, :p, :st, :by "
            "WHERE NOT EXISTS (SELECT 1 FROM parent_students "
            "  WHERE parent_user_id = :p AND student_user_id = :st)"
        ),
        {"t": tenant_id, "p": parent_id, "st": student_id, "by": linked_by},
    )


async def is_parent_of(s: AsyncSession, parent_id: str, student_id: str) -> bool:
    return (
        await s.execute(
            text(
                "SELECT 1 FROM parent_students "
                "WHERE parent_user_id = :p AND student_user_id = :st LIMIT 1"
            ),
            {"p": parent_id, "st": student_id},
        )
    ).first() is not None


async def list_children(s: AsyncSession, parent_id: str) -> list[dict]:
    rows = (
        (
            await s.execute(
                text(
                    "SELECT u.id AS student_id, "
                    "COALESCE(NULLIF(u.full_name, ''), u.username) AS full_name "
                    "FROM parent_students ps JOIN users u ON u.id = ps.student_user_id "
                    "WHERE ps.parent_user_id = :p ORDER BY full_name"
                ),
                {"p": parent_id},
            )
        )
        .mappings()
        .all()
    )
    return [{"student_id": str(r["student_id"]), "full_name": r["full_name"]} for r in rows]
