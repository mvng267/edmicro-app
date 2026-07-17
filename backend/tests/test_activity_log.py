import uuid

import pytest
from sqlalchemy import text

from app.core.activity_log import log_activity
from app.db import set_tenant

TID = str(uuid.uuid4())


@pytest.mark.asyncio
async def test_log_activity_redacts_sensitive(session_factory):
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            await log_activity(
                s,
                tenant_id=TID,
                actor_id=str(uuid.uuid4()),
                actor_role="it_admin",
                action="update",
                module="ORG",
                entity_type="user",
                entity_id=str(uuid.uuid4()),
                diff={"full_name": "A->B", "password_hash": "secret"},
            )
        async with s.begin():
            await set_tenant(s, TID)
            row = (
                await s.execute(
                    text("SELECT diff FROM activity_logs WHERE tenant_id = :t"), {"t": TID}
                )
            ).scalar_one()
    assert row["password_hash"] == "***"
    assert row["full_name"] == "A->B"
