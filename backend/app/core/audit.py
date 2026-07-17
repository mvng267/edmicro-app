"""Audit log — tầng nhạy cảm (tập con nghiêm ngặt của activity log).

Ghi đồng bộ trong transaction nghiệp vụ. Xem docs/01-kien-truc/03-bao-mat.md §6.
"""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def log_audit(
    session: AsyncSession,
    *,
    tenant_id: str | None,
    actor_id: str | None,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    await session.execute(
        text(
            "INSERT INTO audit_logs "
            "(tenant_id, actor_id, actor_role, action, target_type, target_id, before, after) "
            "VALUES (:t, :a, :r, :act, :tt, :tid, CAST(:b AS jsonb), CAST(:af AS jsonb))"
        ),
        {
            "t": tenant_id,
            "a": actor_id,
            "r": actor_role,
            "act": action,
            "tt": target_type,
            "tid": target_id,
            "b": json.dumps(before or {}, ensure_ascii=False),
            "af": json.dumps(after or {}, ensure_ascii=False),
        },
    )
