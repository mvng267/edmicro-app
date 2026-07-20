import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app
from app.modules.content import service as content_svc

TID = str(uuid.uuid4())


async def _seed(session_factory):
    """Tạo lớp + 2 HS trong lớp + 2 câu đã publish. Trả (class_id, students, qids)."""
    class_id = str(uuid.uuid4())
    students = [str(uuid.uuid4()), str(uuid.uuid4())]
    qids = []
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            await s.execute(
                text(
                    "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'M3') "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {"id": TID, "sl": f"m3-{TID[:8]}"},
            )
            bid = str(uuid.uuid4())
            await s.execute(
                text("INSERT INTO branches (id, tenant_id, name) VALUES (:b, :t, 'CN')"),
                {"b": bid, "t": TID},
            )
            await s.execute(
                text(
                    "INSERT INTO classes (id, tenant_id, branch_id, name) "
                    "VALUES (:c, :t, :b, 'Lop A')"
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
                        "INSERT INTO class_students (tenant_id, class_id, user_id) "
                        "VALUES (:t, :c, :u)"
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
        async with session_factory() as s:
            async with s.begin():
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
async def test_full_assign_do_submit(client, session_factory):
    class_id, students, qids = await _seed(session_factory)
    teacher = str(uuid.uuid4())
    s1, s2 = students

    # teacher tạo practice
    _as("teacher", teacher)
    pr = await client.post(
        "/api/v1/practices",
        json={"name": "Bài 1", "skill": "reading", "question_ids": qids},
    )
    assert pr.status_code == 201, pr.text
    practice_id = pr.json()["id"]

    # thêm câu chưa publish -> 422
    async with session_factory() as sess:
        async with sess.begin():
            await set_tenant(sess, TID)
            draft = await content_svc.create_question(
                sess,
                TID,
                teacher,
                {
                    "type": "mcq_single",
                    "language": "en",
                    "content": {"prompt": "draft", "options": ["a", "b"]},
                    "answer_key": {"correct_index": 0},
                },
            )
    bad = await client.post("/api/v1/practices", json={"name": "X", "question_ids": [draft]})
    assert bad.status_code == 422

    # giao cho lớp -> 2 assignee
    due = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    asg = await client.post(
        "/api/v1/assignments",
        json={"content_id": practice_id, "class_id": class_id, "due_at": due},
    )
    assert asg.status_code == 201, asg.text
    assert asg.json()["assignee_count"] == 2

    # student1 xem việc cần làm
    _as("student", s1)
    todo = await client.get("/api/v1/me/assignments")
    assert todo.status_code == 200
    assert len(todo.json()) == 1
    assignee_id = todo.json()[0]["assignee_id"]

    # start -> attempt + practice ẩn đáp án
    start = await client.post(f"/api/v1/assignments/{assignee_id}/start")
    assert start.status_code == 200, start.text
    attempt_id = start.json()["attempt_id"]
    first_q = start.json()["practice"]["questions"][0]
    assert "answer_key" not in first_q  # ẩn đáp án

    # autosave 2 lần cùng câu -> upsert (không tạo trùng)
    qv = first_q["question_version_id"]
    await client.put(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_version_id": qv, "payload": {"selected": 0}},
    )
    await client.put(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_version_id": qv, "payload": {"selected": 1}},
    )
    async with session_factory() as sess:
        async with sess.begin():
            await set_tenant(sess, TID)
            n = (
                await sess.execute(
                    text("SELECT count(*) FROM answers WHERE attempt_id = :a"),
                    {"a": attempt_id},
                )
            ).scalar_one()
    assert n == 1

    # student2 KHÔNG truy cập attempt của student1
    _as("student", s2)
    forbidden = await client.put(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_version_id": qv, "payload": {"selected": 0}},
    )
    assert forbidden.status_code == 403

    # student1 nộp bài
    _as("student", s1)
    sub = await client.post(f"/api/v1/attempts/{attempt_id}/submit")
    assert sub.status_code == 200
    todo2 = await client.get("/api/v1/me/assignments")
    assert todo2.json()[0]["status"] == "submitted"


@pytest.mark.asyncio
async def test_enroll_backfill_late_join(client, session_factory):
    from app.modules.assignment import service as asvc

    class_id, students, qids = await _seed(session_factory)
    teacher = str(uuid.uuid4())
    _as("teacher", teacher)
    pid = (
        await client.post("/api/v1/practices", json={"name": "B2", "question_ids": qids})
    ).json()["id"]
    due = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    await client.post(
        "/api/v1/assignments", json={"content_id": pid, "class_id": class_id, "due_at": due}
    )

    # học sinh mới vào lớp muộn
    late = str(uuid.uuid4())
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                    "VALUES (:id, :t, :un, 'x', 'student')"
                ),
                {"id": late, "t": TID, "un": f"late-{late[:8]}"},
            )
            await s.execute(
                text(
                    "INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"
                ),
                {"t": TID, "c": class_id, "u": late},
            )
            n = await asvc.enroll_backfill(s, TID, class_id, late)
    assert n == 1

    _as("student", late)
    todo = await client.get("/api/v1/me/assignments")
    assert len(todo.json()) == 1


@pytest.mark.asyncio
async def test_auto_grade_and_result(client, session_factory):
    class_id, students, qids = await _seed(session_factory)
    teacher = str(uuid.uuid4())
    s1, s2 = students

    # practice 1 câu (q0: correct_index=0)
    _as("teacher", teacher)
    pid = (
        await client.post("/api/v1/practices", json={"name": "Chấm", "question_ids": [qids[0]]})
    ).json()["id"]
    due = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    await client.post(
        "/api/v1/assignments", json={"content_id": pid, "class_id": class_id, "due_at": due}
    )

    _as("student", s1)
    aid = (await client.get("/api/v1/me/assignments")).json()[0]["assignee_id"]
    start = (await client.post(f"/api/v1/assignments/{aid}/start")).json()
    attempt_id = start["attempt_id"]
    qv = start["practice"]["questions"][0]["question_version_id"]

    # chưa nộp -> result 409
    early = await client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert early.status_code == 409

    # trả lời đúng (selected=0) rồi nộp -> chấm 1/1
    await client.put(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_version_id": qv, "payload": {"selected": 0}},
    )
    sub = await client.post(f"/api/v1/attempts/{attempt_id}/submit")
    assert sub.status_code == 200
    assert sub.json()["correct_count"] == 1
    assert sub.json()["total_count"] == 1
    assert sub.json()["score"] == 100.0

    # danh sách việc: đã nộp + có attempt_id để mở trang kết quả
    todo = (await client.get("/api/v1/me/assignments")).json()[0]
    assert todo["status"] == "submitted"
    assert todo["attempt_id"] == attempt_id

    # xem kết quả: review lộ đáp án đúng
    res = await client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert res.status_code == 200
    body = res.json()
    assert body["score"] == 100.0
    assert body["review"][0]["is_correct"] is True
    assert body["review"][0]["answer_key"] == {"correct_index": 0}

    # student2 KHÔNG xem được kết quả của student1
    _as("student", s2)
    other = await client.get(f"/api/v1/attempts/{attempt_id}/result")
    assert other.status_code == 403
