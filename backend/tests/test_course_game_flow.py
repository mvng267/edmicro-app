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
    """Lớp + 1 HS trong lớp + 1 HS ngoài lớp + 1 câu mcq (đúng=0).

    Trả (class, hs_in, hs_out, qid).
    """
    class_id = str(uuid.uuid4())
    hs_in = str(uuid.uuid4())
    hs_out = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'C9') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"c9-{TID[:8]}"},
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
        for sid, in_class in ((hs_in, True), (hs_out, False)):
            await s.execute(
                text(
                    "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                    "VALUES (:id, :t, :un, 'x', 'student')"
                ),
                {"id": sid, "t": TID, "un": f"hs-{sid[:8]}"},
            )
            if in_class:
                await s.execute(
                    text(
                        "INSERT INTO class_students (tenant_id, class_id, user_id) "
                        "VALUES (:t, :c, :u)"
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
    return class_id, hs_in, hs_out, qid


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
async def test_course_progress_points_badges(client, session_factory):
    class_id, hs_in, hs_out, _qid = await _seed(session_factory)

    # student KHÔNG tạo được khóa học
    _as("student", hs_in)
    assert (await client.post("/api/v1/courses", json={"name": "X"})).status_code == 403

    # teacher tạo khóa + 2 bài + giao lớp
    _as("teacher", str(uuid.uuid4()))
    cid = (await client.post("/api/v1/courses", json={"name": "Khóa 1"})).json()["id"]
    l1 = (
        await client.post(
            f"/api/v1/courses/{cid}/lessons", json={"title": "Bài 1", "kind": "text", "body": "Hi"}
        )
    ).json()["id"]
    await client.post(f"/api/v1/courses/{cid}/lessons", json={"title": "Bài 2", "kind": "text"})
    assert (
        await client.post(f"/api/v1/courses/{cid}/assign", json={"class_id": class_id})
    ).status_code == 201

    # HS trong lớp thấy khóa, tiến độ 0
    _as("student", hs_in)
    mine = (await client.get("/api/v1/me/courses")).json()
    assert len(mine) == 1
    assert mine[0]["total"] == 2 and mine[0]["progress"] == 0.0

    # hoàn thành bài 1 -> tiến độ 50%, +5 điểm
    prog = (await client.post(f"/api/v1/lessons/{l1}/complete")).json()
    assert prog["progress"] == 50.0
    pts = (await client.get("/api/v1/me/points")).json()
    assert pts["total"] == 5
    assert pts["streak"] == 1

    # hoàn thành lại bài 1 -> không cộng trùng
    await client.post(f"/api/v1/lessons/{l1}/complete")
    assert (await client.get("/api/v1/me/points")).json()["total"] == 5

    # HS NGOÀI lớp không hoàn thành được bài của khóa
    _as("student", hs_out)
    assert (await client.post(f"/api/v1/lessons/{l1}/complete")).status_code == 403


@pytest.mark.asyncio
async def test_submission_points_and_leaderboard(client, session_factory):
    class_id, hs_in, _hs_out, qid = await _seed(session_factory)
    _as("teacher", str(uuid.uuid4()))
    pid = (
        await client.post("/api/v1/practices", json={"name": "P", "question_ids": [qid]})
    ).json()["id"]
    due = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    await client.post(
        "/api/v1/assignments", json={"content_id": pid, "class_id": class_id, "due_at": due}
    )

    # HS làm đúng -> nộp -> +10 (nộp) +5 (điểm cao) = 15; badge first_submission
    _as("student", hs_in)
    aid = (await client.get("/api/v1/me/assignments")).json()[0]["assignee_id"]
    start = (await client.post(f"/api/v1/assignments/{aid}/start")).json()
    qv = start["practice"]["questions"][0]["question_version_id"]
    await client.put(
        f"/api/v1/attempts/{start['attempt_id']}/answers",
        json={"question_version_id": qv, "payload": {"selected": 0}},
    )
    await client.post(f"/api/v1/attempts/{start['attempt_id']}/submit")

    pts = (await client.get("/api/v1/me/points")).json()
    assert pts["total"] == 15
    assert any(b["code"] == "first_submission" for b in pts["badges"])

    # bảng xếp hạng lớp: HS có 15 điểm, hạng 1
    lb = (await client.get(f"/api/v1/classes/{class_id}/leaderboard")).json()
    me = next(x for x in lb if x["student_id"] == hs_in)
    assert me["points"] == 15
    assert me["rank"] == 1
