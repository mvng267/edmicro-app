import uuid

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app

TID = str(uuid.uuid4())


@pytest.fixture
async def client(session_factory):
    async def _override_session():
        async with session_factory() as s:
            async with s.begin():
                await set_tenant(s, TID)
                yield s

    app.dependency_overrides[get_tenant_session] = _override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def _as(role: str):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(str(uuid.uuid4()), TID, role)


_MCQ = {
    "type": "mcq_single",
    "language": "en",
    "skill": "reading",
    "content": {"prompt": "Capital of VN?", "options": ["Hanoi", "HCMC"]},
    "answer_key": {"correct_index": 0},
}


@pytest.mark.asyncio
async def test_teacher_creates_student_forbidden(client):
    _as("teacher")
    r = await client.post("/api/v1/content/questions", json=_MCQ)
    assert r.status_code == 201, r.text
    qid = r.json()["id"]

    _as("student")
    bad = await client.post("/api/v1/content/questions", json=_MCQ)
    assert bad.status_code == 403

    # invalid content -> 422
    _as("teacher")
    inv = await client.post(
        "/api/v1/content/questions",
        json={**_MCQ, "answer_key": {"correct_index": 9}},
    )
    assert inv.status_code == 422

    # publish + list lọc theo skill
    await client.post(f"/api/v1/content/questions/{qid}/publish")
    lst = await client.get("/api/v1/content/questions?skill=reading&status=published")
    assert any(q["id"] == qid for q in lst.json())


@pytest.mark.asyncio
async def test_activity_log_on_create(client, session_factory):
    _as("owner")
    await client.post("/api/v1/content/questions", json=_MCQ)
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            n = (
                await s.execute(
                    text(
                        "SELECT count(*) FROM activity_logs "
                        "WHERE module='CONTENT' AND action='create'"
                    )
                )
            ).scalar_one()
    assert n >= 1
