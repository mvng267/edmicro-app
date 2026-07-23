"""Mức dùng & quota của tenant. Xem SRS PLAN §5 (metering). M10: counts + quota AI writing."""

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def tenant_usage(s: AsyncSession, tenant_id: str) -> dict:
    counts = (
        (
            await s.execute(
                text(
                    "SELECT "
                    "(SELECT count(*) FROM users WHERE role = 'student') AS students, "
                    "(SELECT count(*) FROM classes) AS classes, "
                    "(SELECT count(*) FROM submissions) AS submissions, "
                    "(SELECT count(*) FROM courses) AS courses"
                )
            )
        )
        .mappings()
        .one()
    )
    period = datetime.now(UTC).strftime("%Y-%m")
    quota = (
        (
            await s.execute(
                text(
                    "SELECT writing_limit, writing_used FROM tenant_ai_quota "
                    "WHERE tenant_id = :t AND period = :p"
                ),
                {"t": tenant_id, "p": period},
            )
        )
        .mappings()
        .first()
    )
    return {
        "students": counts["students"],
        "classes": counts["classes"],
        "submissions": counts["submissions"],
        "courses": counts["courses"],
        "period": period,
        "ai_writing": {
            "limit": quota["writing_limit"] if quota else 0,
            "used": quota["writing_used"] if quota else 0,
        },
    }
