"""Tạo & quản lý tài khoản trong tenant: sinh username/mật khẩu, RBAC theo vai trò
người tạo, consent cho HS <16 tuổi, liên kết phụ huynh. Xem SRS ORG FR-08..17, 22.
"""

import re
import secrets
import unicodedata
import uuid
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password

TENANT_ROLES = {
    "owner",
    "manager",
    "academic_head",
    "it_admin",
    "teacher",
    "assistant",
    "student",
    "parent",
}
MANAGEMENT_ROLES = {"owner", "manager", "academic_head", "it_admin"}
# Ai được tạo vai trò nào
_CREATE_MATRIX = {
    "owner": TENANT_ROLES,
    "manager": {"teacher", "assistant", "student", "parent"},
    "it_admin": {"teacher", "assistant", "student", "parent"},
}


class Forbidden(Exception):
    pass


class Duplicate(Exception):
    pass


def can_create(creator_role: str, target_role: str) -> bool:
    return target_role in _CREATE_MATRIX.get(creator_role, set())


def _slugify(name: str) -> str:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    n = re.sub(r"[^a-zA-Z0-9]+", ".", n.strip().lower()).strip(".")
    return n or "user"


def _gen_password() -> str:
    return secrets.token_urlsafe(9)


def _is_minor(dob: date | None) -> bool:
    if dob is None:
        return False
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age < 16


async def _unique_username(s: AsyncSession, base: str) -> str:
    candidate = base
    i = 1
    while (
        await s.execute(text("SELECT 1 FROM users WHERE username = :u"), {"u": candidate})
    ).scalar_one_or_none() is not None:
        i += 1
        candidate = f"{base}{i}"
    return candidate


async def create_user(s: AsyncSession, tenant_id: str, creator_role: str, data: dict) -> dict:
    target_role = data["role"]
    if target_role not in TENANT_ROLES:
        raise Forbidden("invalid_role")
    if not can_create(creator_role, target_role):
        raise Forbidden("role_not_allowed")

    username = data.get("username") or await _unique_username(s, _slugify(data["full_name"]))
    if (
        await s.execute(text("SELECT 1 FROM users WHERE username = :u"), {"u": username})
    ).scalar_one_or_none() is not None:
        raise Duplicate("username_taken")

    password = _gen_password()
    uid = str(uuid.uuid4())
    dob = data.get("dob")
    if isinstance(dob, str):
        dob = date.fromisoformat(dob)
    await s.execute(
        text(
            "INSERT INTO users (id, tenant_id, username, password_hash, role, full_name, dob, "
            "parent_phone, must_change_password) "
            "VALUES (:id, :t, :u, :ph, :r, :fn, :dob, :pp, true)"
        ),
        {
            "id": uid,
            "t": tenant_id,
            "u": username,
            "ph": hash_password(password),
            "r": target_role,
            "fn": data["full_name"],
            "dob": dob,
            "pp": data.get("parent_phone"),
        },
    )
    # gán vào lớp nếu là học sinh + có class_id
    if target_role == "student" and data.get("class_id"):
        await s.execute(
            text("INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"),
            {"t": tenant_id, "c": data["class_id"], "u": uid},
        )
    # consent pending cho HS <16
    if target_role == "student" and _is_minor(dob):
        await s.execute(
            text("INSERT INTO consents (tenant_id, user_id, status) VALUES (:t, :u, 'pending')"),
            {"t": tenant_id, "u": uid},
        )
    return {"id": uid, "username": username, "password": password, "full_name": data["full_name"]}


async def reset_password(s: AsyncSession, user_id: str) -> str:
    password = _gen_password()
    await s.execute(
        text("UPDATE users SET password_hash = :ph, must_change_password = true WHERE id = :id"),
        {"ph": hash_password(password), "id": user_id},
    )
    return password


async def set_locked(s: AsyncSession, user_id: str, locked: bool) -> None:
    await s.execute(
        text("UPDATE users SET status = :st WHERE id = :id"),
        {"st": "locked" if locked else "active", "id": user_id},
    )


async def get_role(s: AsyncSession, user_id: str) -> str | None:
    return (
        await s.execute(text("SELECT role FROM users WHERE id = :id"), {"id": user_id})
    ).scalar_one_or_none()


async def link_parent(
    s: AsyncSession, tenant_id: str, parent_id: str, student_id: str, by: str
) -> None:
    await s.execute(
        text(
            "INSERT INTO parent_students (tenant_id, parent_user_id, student_user_id, linked_by) "
            "VALUES (:t, :p, :st, :by) ON CONFLICT DO NOTHING"
        ),
        {"t": tenant_id, "p": parent_id, "st": student_id, "by": by},
    )


async def set_scopes(s: AsyncSession, tenant_id: str, user_id: str, branch_ids: list[str]) -> None:
    await s.execute(text("DELETE FROM user_scopes WHERE user_id = :u"), {"u": user_id})
    for bid in branch_ids:
        await s.execute(
            text("INSERT INTO user_scopes (tenant_id, user_id, branch_id) VALUES (:t, :u, :b)"),
            {"t": tenant_id, "u": user_id, "b": bid},
        )
