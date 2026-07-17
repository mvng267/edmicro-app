import uuid

import pytest
from sqlalchemy import text

from app.db import set_tenant

TENANT_A = str(uuid.uuid4())
TENANT_B = str(uuid.uuid4())


@pytest.mark.asyncio
async def test_rls_blocks_cross_tenant_read(session_factory):
    # Seed: mỗi tenant 1 user, dưới đúng tenant context
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TENANT_A)
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                    "VALUES (:id, :t, 'a', 'x', 'owner')"
                ),
                {"id": str(uuid.uuid4()), "t": TENANT_A},
            )
        async with s.begin():
            await set_tenant(s, TENANT_B)
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                    "VALUES (:id, :t, 'b', 'x', 'owner')"
                ),
                {"id": str(uuid.uuid4()), "t": TENANT_B},
            )

    # Đọc dưới context tenant A -> chỉ thấy user của A
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TENANT_A)
            rows = (await s.execute(text("SELECT username FROM users"))).scalars().all()
    assert rows == ["a"]  # KHÔNG được thấy 'b'


@pytest.mark.asyncio
async def test_rls_blocks_write_into_other_tenant(session_factory):
    # Set context A nhưng cố insert tenant_id B -> WITH CHECK của policy chặn
    async with session_factory() as s:
        with pytest.raises(Exception):
            async with s.begin():
                await set_tenant(s, TENANT_A)
                await s.execute(
                    text(
                        "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                        "VALUES (:id, :t, 'x', 'x', 'owner')"
                    ),
                    {"id": str(uuid.uuid4()), "t": TENANT_B},
                )
