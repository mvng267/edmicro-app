"""Truy vấn nhật ký hoạt động cho UI quản trị log. Xem SRS LOG §5.
activity_logs KHÔNG bật RLS (tenant_id nullable) → LỌC tenant_id tường minh để tránh lộ chéo.
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def list_activity(
    s: AsyncSession, tenant_id: str, filters: dict[str, Any], limit: int = 100
) -> list[dict]:
    sql = (
        "SELECT id, actor_id, actor_role, action, module, entity_type, entity_id, "
        "entity_label, diff, at FROM activity_logs WHERE tenant_id = :tenant"
    )
    p: dict[str, Any] = {"tenant": tenant_id, "lim": min(limit, 500)}
    for col in ("module", "actor_role", "entity_type"):
        if filters.get(col):
            sql += f" AND {col} = :{col}"
            p[col] = filters[col]
    if filters.get("actor_id"):
        sql += " AND actor_id = :actor_id"
        p["actor_id"] = filters["actor_id"]
    sql += " ORDER BY at DESC LIMIT :lim"
    rows = (await s.execute(text(sql), p)).mappings().all()
    return [
        {
            "id": str(r["id"]),
            "actor_id": str(r["actor_id"]) if r["actor_id"] else None,
            "actor_role": r["actor_role"],
            "action": r["action"],
            "module": r["module"],
            "entity_type": r["entity_type"],
            "entity_id": str(r["entity_id"]) if r["entity_id"] else None,
            "entity_label": r["entity_label"],
            "diff": r["diff"],
            "at": r["at"].isoformat(),
        }
        for r in rows
    ]
