import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app
from app.modules.content import service as content_svc
from app.modules.notify import service as notify

TID = str(uuid.uuid4())


async def _seed(session_factory):
    class_id = str(uuid.uuid4())
    students = [str(uuid.uuid4()), str(uuid.uuid4())]
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'N8') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"n8-{TID[:8]}"},
        )
        bid = str(uuid.uuid4())
        await s.execute(
            text("INSERT INTO branches (id, tenant_id, name) VALUES (:b, :t, 'CN')"),
            {"b": bid, "t": TID},
        )
        await s.execute(
            text(
                "INSERT INTO classes (id, tenant_id, branch_id, name) VALUES (:c, :t, :b, 'Lop A')"
            ),
            {"c": class_id, "t": TID, "b": bid},
        )
        for sid in students:
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                    "VALUES (:id, :t, :un, 'x', 'student')"
                ),
                {"id": sid, "t": TID, "un": f"hs-{sid[:8]}"},
            )
            await s.execute(
                text(
                    "INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"
                ),
                {"t": TID, "c": class_id, "u": sid},
            )
        qid = await content_svc.create_question(
            s,
            TID,
            str(uuid.uuid4()),
            {
                "type": "mcq_single",
                "language": "en",
                "content": {"prompt": "Q?", "options": ["a", "b"]},
                "answer_key": {"correct_index": 0},
            },
        )
        await content_svc.publish_question(s, qid)
    return class_id, students, qid


@pytest.fixture
async def client(session_factory):
    async def _override_session():
        async with session_factory() as s, s.begin():
            await set_tenant(s, TID)
            yield s

    app.dependency_overrides[get_tenant_session] = _override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def _as(role: str, uid: str):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(uid, TID, role)


@pytest.mark.asyncio
async def test_assignment_created_notifies_students(client, session_factory):
    class_id, (s1, s2), qid = await _seed(session_factory)
    _as("teacher", str(uuid.uuid4()))
    pid = (
        await client.post("/api/v1/practices", json={"name": "Bài N", "question_ids": [qid]})
    ).json()["id"]
    due = (datetime.now(UTC) + timedelta(hours=12)).isoformat()
    await client.post(
        "/api/v1/assignments", json={"content_id": pid, "class_id": class_id, "due_at": due}
    )

    # s1 có 1 thông báo chưa đọc "Bài mới"
    _as("student", s1)
    lst = (await client.get("/api/v1/me/notifications")).json()
    assert len(lst) == 1
    assert lst[0]["event_code"] == "assignment_created"
    assert lst[0]["read"] is False
    assert (await client.get("/api/v1/me/notifications/unread-count")).json()["count"] == 1

    # đánh dấu đã đọc -> unread 0
    nid = lst[0]["id"]
    assert (await client.post(f"/api/v1/notifications/{nid}/read")).status_code == 200
    assert (await client.get("/api/v1/me/notifications/unread-count")).json()["count"] == 0

    # s2 chỉ thấy thông báo của mình (không thấy của s1)
    _as("student", s2)
    lst2 = (await client.get("/api/v1/me/notifications")).json()
    assert len(lst2) == 1
    assert lst2[0]["id"] != nid


@pytest.mark.asyncio
async def test_remind_due_no_duplicate(client, session_factory):
    class_id, (s1, s2), qid = await _seed(session_factory)
    _as("teacher", str(uuid.uuid4()))
    pid = (
        await client.post("/api/v1/practices", json={"name": "Bài D", "question_ids": [qid]})
    ).json()["id"]
    due = (datetime.now(UTC) + timedelta(hours=12)).isoformat()
    await client.post(
        "/api/v1/assignments", json={"content_id": pid, "class_id": class_id, "due_at": due}
    )

    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        n1 = await notify.remind_due_assignments(s, TID, within_hours=24)
        assert n1 >= 2  # ≥2 HS chưa nộp, bài sắp tới hạn (tenant có thể có bài khác)
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        n2 = await notify.remind_due_assignments(s, TID, within_hours=24)
        assert n2 == 0  # không nhắc trùng

    _as("student", s1)
    codes = [n["event_code"] for n in (await client.get("/api/v1/me/notifications")).json()]
    assert "deadline_reminder" in codes
