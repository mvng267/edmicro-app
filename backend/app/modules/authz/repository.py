from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def find_user_by_username(session: AsyncSession, username: str) -> dict | None:
    row = (
        await session.execute(
            text(
                "SELECT id, tenant_id, password_hash, role, must_change_password "
                "FROM users WHERE username = :u AND status = 'active'"
            ),
            {"u": username},
        )
    ).mappings().first()
    return dict(row) if row else None
