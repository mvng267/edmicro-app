"""Activity log — tầng log rộng: mọi thao tác ghi trên mọi module.

M0: ghi trực tiếp trong transaction hiện tại (đơn giản, an toàn).
M8: chuyển sang queue async theo FR-LOG-03 khi có arq worker.
Xem docs/18-quan-tri-log/srs-quan-tri-log.md.
"""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_SENSITIVE = {"password", "password_hash", "token", "totp_secret", "parent_phone"}


def _redact(diff: dict) -> dict:
    return {k: ("***" if k in _SENSITIVE else v) for k, v in diff.items()}


async def log_activity(
    session: AsyncSession,
    *,
    tenant_id: str | None,
    actor_id: str | None,
    actor_role: str,
    action: str,
    module: str,
    entity_type: str,
    entity_id: str,
    entity_label: str = "",
    diff: dict | None = None,
) -> None:
    await session.execute(
        text(
            "INSERT INTO activity_logs "
            "(tenant_id, actor_id, actor_role, action, module, entity_type, entity_id, "
            "entity_label, diff) "
            "VALUES (:t, :a, :r, :act, :m, :et, :eid, :el, CAST(:d AS jsonb))"
        ),
        {
            "t": tenant_id,
            "a": actor_id,
            "r": actor_role,
            "act": action,
            "m": module,
            "et": entity_type,
            "eid": entity_id,
            "el": entity_label,
            "d": json.dumps(_redact(diff or {}), ensure_ascii=False),
        },
    )
