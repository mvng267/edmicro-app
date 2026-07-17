"""Seed dữ liệu dev: 1 tenant 'bright' + 1 tài khoản owner (owner/owner123).

Chạy: just seed  (hoặc: cd backend && uv run python ../scripts/seed.py)
"""

import asyncio
import uuid

from sqlalchemy import text

from app.core.security import hash_password
from app.db import SessionLocal, set_tenant

TENANT_ID = uuid.uuid4()


async def main() -> None:
    async with SessionLocal() as s:
        async with s.begin():
            # Nếu tenant đã tồn tại, dùng id sẵn có để set context
            existing = (
                await s.execute(text("SELECT id FROM tenants WHERE slug = 'bright'"))
            ).scalar_one_or_none()
            tid = str(existing) if existing else str(TENANT_ID)
            await set_tenant(s, tid)
            if not existing:
                await s.execute(
                    text(
                        "INSERT INTO tenants (id, slug, name, status, settings) "
                        "VALUES (:id, 'bright', 'Anh ngữ Bright', 'active', '{}')"
                    ),
                    {"id": tid},
                )
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, password_hash, role, full_name, "
                    "status, must_change_password) "
                    "VALUES (:id, :t, 'owner', :ph, 'owner', 'Chủ trung tâm', 'active', false) "
                    "ON CONFLICT ON CONSTRAINT uq_users_tenant_username DO NOTHING"
                ),
                {"id": str(uuid.uuid4()), "t": tid, "ph": hash_password("owner123")},
            )
    print("Seeded: tenant 'bright' + owner/owner123")


if __name__ == "__main__":
    asyncio.run(main())
