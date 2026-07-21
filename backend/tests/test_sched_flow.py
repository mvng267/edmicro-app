import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app

TID = str(uuid.uuid4())


async def _seed(session_factory):
    """Lớp + 2 HS + 1 GV chủ nhiệm (class_staff). Trả (class_id, [s1,s2], teacher)."""
    class_id = str(uuid.uuid4())
    students = [str(uuid.uuid4()), str(uuid.uuid4())]
    teacher = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'S8') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"s8-{TID[:8]}"},
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
        for i, sid in enumerate(students):
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, full_name, password_hash, role) "
                    "VALUES (:id, :t, :un, :fn, 'x', 'student')"
                ),
                {"id": sid, "t": TID, "un": f"hs-{sid[:8]}", "fn": f"HS {i}"},
            )
            await s.execute(
                text(
                    "INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"
                ),
                {"t": TID, "c": class_id, "u": sid},
            )
        await s.execute(
            text(
                "INSERT INTO class_staff (tenant_id, class_id, user_id, role) "
                "VALUES (:t, :c, :u, 'teacher')"
            ),
            {"t": TID, "c": class_id, "u": teacher},
        )
    return class_id, students, teacher


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
async def test_session_attendance_and_absent_notify(client, session_factory):
    class_id, (s1, s2), teacher = await _seed(session_factory)
    start = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    end = (datetime.now(UTC) + timedelta(days=1, hours=2)).isoformat()

    # student KHÔNG tạo được buổi
    _as("student", s1)
    assert (
        await client.post(
            "/api/v1/sessions",
            json={"class_id": class_id, "starts_at": start, "ends_at": end},
        )
    ).status_code == 403

    # teacher lớp tạo buổi
    _as("teacher", teacher)
    r = await client.post(
        "/api/v1/sessions",
        json={"class_id": class_id, "starts_at": start, "ends_at": end, "topic": "Unit 1"},
    )
    assert r.status_code == 201, r.text
    sid = r.json()["id"]
    assert any(
        x["id"] == sid for x in (await client.get(f"/api/v1/sessions?class_id={class_id}")).json()
    )

    # HS xem lịch mình
    _as("student", s1)
    assert any(x["id"] == sid for x in (await client.get("/api/v1/me/sessions")).json())

    # teacher điểm danh: s1 có mặt, s2 vắng
    _as("teacher", teacher)
    m = await client.post(
        f"/api/v1/sessions/{sid}/attendance",
        json={
            "records": [
                {"student_id": s1, "status": "present"},
                {"student_id": s2, "status": "absent", "note": "ốm"},
            ]
        },
    )
    assert m.status_code == 200
    assert m.json() == {"marked": 2, "absent": 1}

    roster = (await client.get(f"/api/v1/sessions/{sid}/attendance")).json()
    by_id = {x["student_id"]: x for x in roster}
    assert by_id[s1]["status"] == "present"
    assert by_id[s2]["status"] == "absent"

    # s2 nhận thông báo vắng; s1 thì không
    _as("student", s2)
    codes = [n["event_code"] for n in (await client.get("/api/v1/me/notifications")).json()]
    assert "attendance_absent" in codes
    _as("student", s1)
    codes1 = [n["event_code"] for n in (await client.get("/api/v1/me/notifications")).json()]
    assert "attendance_absent" not in codes1


@pytest.mark.asyncio
async def test_session_rbac_other_teacher(client, session_factory):
    class_id, _students, _teacher = await _seed(session_factory)
    start = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    end = (datetime.now(UTC) + timedelta(days=1, hours=2)).isoformat()
    # teacher KHÔNG dạy lớp -> 403
    _as("teacher", str(uuid.uuid4()))
    assert (
        await client.post(
            "/api/v1/sessions",
            json={"class_id": class_id, "starts_at": start, "ends_at": end},
        )
    ).status_code == 403
    # owner (tenant-wide) -> tạo được
    _as("owner", str(uuid.uuid4()))
    assert (
        await client.post(
            "/api/v1/sessions",
            json={"class_id": class_id, "starts_at": start, "ends_at": end},
        )
    ).status_code == 201
