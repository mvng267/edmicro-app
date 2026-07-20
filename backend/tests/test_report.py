import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app
from app.modules.content import service as content_svc
from app.modules.report import service as report

TID = str(uuid.uuid4())


async def _seed(session_factory):
    """Lớp + 2 HS + 2 câu (Q0 đúng=0, Q1 đúng=1). Trả (class_id, [s1,s2], qids)."""
    class_id = str(uuid.uuid4())
    students = [str(uuid.uuid4()), str(uuid.uuid4())]
    qids = []
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'R5') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"r5-{TID[:8]}"},
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
        for i in range(2):
            qid = await content_svc.create_question(
                s,
                TID,
                str(uuid.uuid4()),
                {
                    "type": "mcq_single",
                    "language": "en",
                    "skill": "reading",
                    "content": {"prompt": f"Q{i}?", "options": ["a", "b"]},
                    "answer_key": {"correct_index": i % 2},
                },
            )
            await content_svc.publish_question(s, qid)
            qids.append(qid)
    return class_id, students, qids


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


async def _do_full_correct(client, assignee_id):
    """HS làm assignee: trả lời đúng mọi câu rồi nộp."""
    start = (await client.post(f"/api/v1/assignments/{assignee_id}/start")).json()
    attempt_id = start["attempt_id"]
    for q in start["practice"]["questions"]:
        # Q{i}? -> đáp án đúng = i%2; suy từ prompt
        correct = int(q["content"]["prompt"][1]) % 2
        await client.put(
            f"/api/v1/attempts/{attempt_id}/answers",
            json={
                "question_version_id": q["question_version_id"],
                "payload": {"selected": correct},
            },
        )
    await client.post(f"/api/v1/attempts/{attempt_id}/submit")
    return attempt_id


@pytest.fixture
async def scenario(client, session_factory):
    """Giao 1 bài 2 câu cho lớp; s1 nộp đúng (100), s2 không làm."""
    class_id, (s1, s2), qids = await _seed(session_factory)
    teacher = str(uuid.uuid4())
    _as("teacher", teacher)
    pid = (
        await client.post(
            "/api/v1/practices",
            json={"name": "Bài R", "skill": "reading", "question_ids": qids},
        )
    ).json()["id"]
    due = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    await client.post(
        "/api/v1/assignments", json={"content_id": pid, "class_id": class_id, "due_at": due}
    )
    _as("student", s1)
    aid = (await client.get("/api/v1/me/assignments")).json()[0]["assignee_id"]
    await _do_full_correct(client, aid)
    return {"class_id": class_id, "s1": s1, "s2": s2, "teacher": teacher}


async def _svc_session(session_factory):
    s = session_factory()
    await s.__aenter__()
    await set_tenant(s, TID)
    return s


@pytest.mark.asyncio
async def test_student_report(scenario, session_factory):
    s = await _svc_session(session_factory)
    try:
        r1 = await report.student_report(s, scenario["s1"])
        assert r1["summary"] == {"assigned": 1, "submitted": 1, "avg_score": 100.0}
        assert len(r1["items"]) == 1
        assert r1["items"][0]["score"] == 100.0
        assert r1["items"][0]["total_count"] == 2
        assert r1["items"][0]["practice_name"] == "Bài R"

        r2 = await report.student_report(s, scenario["s2"])
        assert r2["summary"] == {"assigned": 1, "submitted": 0, "avg_score": None}
        assert r2["items"] == []
    finally:
        await s.__aexit__(None, None, None)


async def _add_class_staff(session_factory, class_id, user_id):
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO class_staff (tenant_id, class_id, user_id, role) "
                "VALUES (:t, :c, :u, 'teacher')"
            ),
            {"t": TID, "c": class_id, "u": user_id},
        )


@pytest.mark.asyncio
async def test_report_rbac_and_scope(scenario, session_factory, client):
    cid, s1 = scenario["class_id"], scenario["s1"]

    # student: /me/report OK, /reports/* bị chặn
    _as("student", s1)
    assert (await client.get("/api/v1/me/report")).status_code == 200
    assert (await client.get(f"/api/v1/reports/classes/{cid}")).status_code == 403

    # owner: xem mọi lớp + mọi HS
    _as("owner", str(uuid.uuid4()))
    assert (await client.get(f"/api/v1/reports/classes/{cid}")).status_code == 200
    assert (await client.get(f"/api/v1/reports/students/{s1}")).status_code == 200
    assert (await client.get("/api/v1/me/report")).status_code == 403  # owner không phải student

    # teacher KHÔNG dạy lớp -> 403
    outsider = str(uuid.uuid4())
    _as("teacher", outsider)
    assert (await client.get(f"/api/v1/reports/classes/{cid}")).status_code == 403
    assert (await client.get(f"/api/v1/reports/students/{s1}")).status_code == 403

    # teacher CÓ dạy lớp -> 200
    homeroom = str(uuid.uuid4())
    await _add_class_staff(session_factory, cid, homeroom)
    _as("teacher", homeroom)
    r = await client.get(f"/api/v1/reports/classes/{cid}")
    assert r.status_code == 200
    assert r.json()["summary"]["student_count"] == 2
    assert (await client.get(f"/api/v1/reports/students/{s1}")).status_code == 200


@pytest.mark.asyncio
async def test_class_report(scenario, session_factory):
    s = await _svc_session(session_factory)
    try:
        rc = await report.class_report(s, scenario["class_id"])
        assert rc["summary"]["student_count"] == 2
        assert rc["summary"]["submitted_total"] == 1
        assert rc["summary"]["assigned_total"] == 2
        assert rc["summary"]["completion_rate"] == 0.5
        assert rc["summary"]["class_avg"] == 100.0
        by_id = {x["student_id"]: x for x in rc["students"]}
        assert by_id[scenario["s1"]]["submitted"] == 1
        assert by_id[scenario["s1"]]["avg_score"] == 100.0
        assert by_id[scenario["s2"]]["submitted"] == 0
        assert by_id[scenario["s2"]]["avg_score"] is None
    finally:
        await s.__aexit__(None, None, None)
