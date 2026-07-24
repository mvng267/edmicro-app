"""Seed dữ liệu dev: 1 tenant + 1 tài khoản owner.

Mặc định: tenant 'bright' (Anh ngữ Bright) + owner/owner123.
Chạy: just seed
Tenant khác:  cd backend && uv run python ../scripts/seed.py <slug> "<Tên trung tâm>" [mật khẩu]
  ví dụ:      uv run python ../scripts/seed.py b2b "Edmicro B2B Demo"
Slug phải khớp subdomain truy cập (vd b2b.dalianperfume.com → slug 'b2b').
"""

import asyncio
import sys
import uuid

from sqlalchemy import text

from app.core.security import hash_password
from app.db import SessionLocal, set_tenant


async def main(slug: str, name: str, password: str) -> None:
    async with SessionLocal() as s, s.begin():
        # Nếu tenant đã tồn tại, dùng id sẵn có để set context
        existing = (
            await s.execute(text("SELECT id FROM tenants WHERE slug = :sl"), {"sl": slug})
        ).scalar_one_or_none()
        tid = str(existing) if existing else str(uuid.uuid4())
        await set_tenant(s, tid)
        if not existing:
            await s.execute(
                text(
                    "INSERT INTO tenants (id, slug, name, status, settings) "
                    "VALUES (:id, :sl, :nm, 'active', '{}')"
                ),
                {"id": tid, "sl": slug, "nm": name},
            )
        await s.execute(
            text(
                "INSERT INTO users (id, tenant_id, username, password_hash, role, full_name, "
                "status, must_change_password) "
                "VALUES (:id, :t, 'owner', :ph, 'owner', 'Chủ trung tâm', 'active', false) "
                "ON CONFLICT ON CONSTRAINT uq_users_tenant_username DO NOTHING"
            ),
            {"id": str(uuid.uuid4()), "t": tid, "ph": hash_password(password)},
        )
    print(f"Seeded: tenant '{slug}' ({name}) + owner/{password}")


if __name__ == "__main__":
    _slug = sys.argv[1] if len(sys.argv) > 1 else "bright"
    _name = sys.argv[2] if len(sys.argv) > 2 else "Anh ngữ Bright"
    _pw = sys.argv[3] if len(sys.argv) > 3 else "owner123"
    asyncio.run(main(_slug, _name, _pw))
