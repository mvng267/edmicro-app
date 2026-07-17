import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ---------- Branches ----------
async def create_branch(s: AsyncSession, tenant_id: str, name: str, address: str | None) -> dict:
    bid = str(uuid.uuid4())
    await s.execute(
        text("INSERT INTO branches (id, tenant_id, name, address) VALUES (:id, :t, :n, :a)"),
        {"id": bid, "t": tenant_id, "n": name, "a": address},
    )
    return {"id": bid, "name": name, "address": address, "status": "active"}


async def list_branches(s: AsyncSession) -> list[dict]:
    rows = (
        (
            await s.execute(
                text("SELECT id, name, address, status FROM branches ORDER BY created_at")
            )
        )
        .mappings()
        .all()
    )
    return [{**r, "id": str(r["id"])} for r in rows]


async def update_branch(s: AsyncSession, branch_id: str, fields: dict) -> None:
    if not fields:
        return
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    await s.execute(
        text(f"UPDATE branches SET {sets}, updated_at = now() WHERE id = :id"),
        {**fields, "id": branch_id},
    )


async def branch_active_class_count(s: AsyncSession, branch_id: str) -> int:
    return (
        await s.execute(
            text("SELECT count(*) FROM classes WHERE branch_id = :b AND status = 'active'"),
            {"b": branch_id},
        )
    ).scalar_one()


async def delete_branch(s: AsyncSession, branch_id: str) -> None:
    await s.execute(text("DELETE FROM branches WHERE id = :id"), {"id": branch_id})


async def branch_exists(s: AsyncSession, branch_id: str) -> bool:
    return (
        await s.execute(text("SELECT 1 FROM branches WHERE id = :id"), {"id": branch_id})
    ).scalar_one_or_none() is not None


# ---------- Classes ----------
async def create_class(s: AsyncSession, tenant_id: str, data: dict) -> dict:
    cid = str(uuid.uuid4())
    await s.execute(
        text(
            "INSERT INTO classes (id, tenant_id, branch_id, name, language, level, capacity, "
            "start_date, end_date) VALUES (:id, :t, :b, :n, :lang, :lvl, :cap, :sd, :ed)"
        ),
        {
            "id": cid,
            "t": tenant_id,
            "b": data["branch_id"],
            "n": data["name"],
            "lang": data["language"],
            "lvl": data.get("level"),
            "cap": data.get("capacity"),
            "sd": data.get("start_date"),
            "ed": data.get("end_date"),
        },
    )
    return {
        "id": cid,
        "branch_id": data["branch_id"],
        "name": data["name"],
        "language": data["language"],
        "level": data.get("level"),
        "status": "active",
    }


async def list_classes(s: AsyncSession, branch_ids: list[str] | None) -> list[dict]:
    if branch_ids is None:
        rows = (
            (
                await s.execute(
                    text(
                        "SELECT id, branch_id, name, language, level, status FROM classes "
                        "ORDER BY created_at"
                    )
                )
            )
            .mappings()
            .all()
        )
    else:
        rows = (
            (
                await s.execute(
                    text(
                        "SELECT id, branch_id, name, language, level, status FROM classes "
                        "WHERE branch_id = ANY(:b) ORDER BY created_at"
                    ),
                    {"b": branch_ids},
                )
            )
            .mappings()
            .all()
        )
    return [{**r, "id": str(r["id"]), "branch_id": str(r["branch_id"])} for r in rows]


async def get_class_branch(s: AsyncSession, class_id: str) -> str | None:
    r = (
        await s.execute(text("SELECT branch_id FROM classes WHERE id = :id"), {"id": class_id})
    ).scalar_one_or_none()
    return str(r) if r else None


async def add_staff(
    s: AsyncSession, tenant_id: str, class_id: str, user_id: str, role: str
) -> None:
    await s.execute(
        text(
            "INSERT INTO class_staff (tenant_id, class_id, user_id, role) VALUES (:t, :c, :u, :r)"
        ),
        {"t": tenant_id, "c": class_id, "u": user_id, "r": role},
    )


async def add_student(s: AsyncSession, tenant_id: str, class_id: str, user_id: str) -> None:
    await s.execute(
        text("INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"),
        {"t": tenant_id, "c": class_id, "u": user_id},
    )


async def remove_student(s: AsyncSession, class_id: str, user_id: str) -> None:
    await s.execute(
        text(
            "UPDATE class_students SET left_at = now() "
            "WHERE class_id = :c AND user_id = :u AND left_at IS NULL"
        ),
        {"c": class_id, "u": user_id},
    )


async def user_role(s: AsyncSession, user_id: str) -> str | None:
    return (
        await s.execute(text("SELECT role FROM users WHERE id = :id"), {"id": user_id})
    ).scalar_one_or_none()
