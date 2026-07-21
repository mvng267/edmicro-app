import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app
from app.modules.content import service as content_svc
from app.modules.grading import service as grading

TID = str(uuid.uuid4())
ESSAY = (
    "My city is a vibrant place full of energy. Every morning people rush to work "
    "while students head to school across many different neighborhoods and districts."
)


async def _seed(session_factory):
    """Lớp + 1 HS + 1 câu đóng (mcq đúng=0) + 1 câu writing.

    Trả (class_id, student, [closed_qid, writing_qid]).
    """
    class_id = str(uuid.uuid4())
    student = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'A6') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"a6-{TID[:8]}"},
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
        await s.execute(
            text(
                "INSERT INTO users (id, tenant_id, username, full_name, password_hash, role) "
                "VALUES (:id, :t, :un, 'HS', 'x', 'student')"
            ),
            {"id": student, "t": TID, "un": f"hs-{student[:8]}"},
        )
        await s.execute(
            text("INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"),
            {"t": TID, "c": class_id, "u": student},
        )
        closed = await content_svc.create_question(
            s,
            TID,
            str(uuid.uuid4()),
            {
                "type": "mcq_single",
                "language": "en",
                "skill": "reading",
                "content": {"prompt": "Pick A", "options": ["a", "b"]},
                "answer_key": {"correct_index": 0},
            },
        )
        await content_svc.publish_question(s, closed)
        writing = await content_svc.create_question(
            s,
            TID,
            str(uuid.uuid4()),
            {
                "type": "writing",
                "language": "en",
                "skill": "writing",
                "content": {"prompt": "Describe your city", "rubric": "IELTS Task 2"},
                "answer_key": {},
            },
        )
        await content_svc.publish_question(s, writing)
    return class_id, student, [closed, writing]


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


async def _assign_and_submit(client, class_id, qids, student):
    teacher = str(uuid.uuid4())
    _as("teacher", teacher)
    pid = (
        await client.post(
            "/api/v1/practices",
            json={"name": "Bài viết", "skill": "writing", "question_ids": qids},
        )
    ).json()["id"]
    due = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    await client.post(
        "/api/v1/assignments", json={"content_id": pid, "class_id": class_id, "due_at": due}
    )
    _as("student", student)
    aid = (await client.get("/api/v1/me/assignments")).json()[0]["assignee_id"]
    start = (await client.post(f"/api/v1/assignments/{aid}/start")).json()
    attempt_id = start["attempt_id"]
    for q in start["practice"]["questions"]:
        payload = {"selected": 0} if q["type"] == "mcq_single" else {"text": ESSAY}
        await client.put(
            f"/api/v1/attempts/{attempt_id}/answers",
            json={"question_version_id": q["question_version_id"], "payload": payload},
        )
    sub = await client.post(f"/api/v1/attempts/{attempt_id}/submit")
    return attempt_id, sub.json()


async def _svc(session_factory):
    s = session_factory()
    await s.__aenter__()
    await set_tenant(s, TID)
    return s


async def _writing_answer(s, attempt_id):
    return (
        (
            await s.execute(
                text(
                    "SELECT ans.grade_status, ans.ai_score, ans.final_score, "
                    "gj.status AS job_status "
                    "FROM answers ans "
                    "JOIN question_versions v ON v.id = ans.question_version_id "
                    "JOIN questions q ON q.id = v.question_id "
                    "LEFT JOIN grading_jobs gj ON gj.answer_id = ans.id "
                    "WHERE ans.attempt_id = :att AND q.type = 'writing' LIMIT 1"
                ),
                {"att": attempt_id},
            )
        )
        .mappings()
        .first()
    )


@pytest.mark.asyncio
async def test_submit_writing_queues_and_ai_grades(client, session_factory):
    class_id, student, qids = await _seed(session_factory)
    attempt_id, result = await _assign_and_submit(client, class_id, qids, student)

    # còn câu mở chờ GV -> submission provisional
    assert result["status"] == "provisional"
    assert result["total_count"] == 2

    s = await _svc(session_factory)
    try:
        w = await _writing_answer(s, attempt_id)
        assert w["grade_status"] == "ai_graded"  # FakeGrader đã chấm
        assert w["ai_score"] is not None
        assert w["job_status"] == "ai_graded"
    finally:
        await s.__aexit__(None, None, None)

    # get_result: câu mở hiện trạng thái chấm, CHƯA lộ nhận xét (chờ GV chốt)
    res = await client.get(f"/api/v1/attempts/{attempt_id}/result")
    body = res.json()
    assert body["status"] == "provisional"
    witem = next(r for r in body["review"] if r["type"] == "writing")
    assert witem["grade_status"] == "ai_graded"
    assert witem["ai_feedback"] is None


@pytest.mark.asyncio
async def test_finalize_open_answer_makes_final(client, session_factory):
    class_id, student, qids = await _seed(session_factory)
    attempt_id, _ = await _assign_and_submit(client, class_id, qids, student)

    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        ans_id = (
            await s.execute(
                text(
                    "SELECT ans.id FROM answers ans "
                    "JOIN question_versions v ON v.id = ans.question_version_id "
                    "JOIN questions q ON q.id = v.question_id "
                    "WHERE ans.attempt_id = :att AND q.type = 'writing'"
                ),
                {"att": attempt_id},
            )
        ).scalar_one()
        out = await grading.finalize_open_answer(
            s, TID, str(ans_id), 0.8, "Tốt, cần mở bài rõ hơn."
        )
    # điểm = (closed 1 + writing 0.8) / 2 * 100 = 90
    assert out["status"] == "final"
    assert out["score"] == 90.0

    # sau chốt: get_result lộ nhận xét + final
    body = (await client.get(f"/api/v1/attempts/{attempt_id}/result")).json()
    assert body["status"] == "final"
    witem = next(r for r in body["review"] if r["type"] == "writing")
    assert witem["grade_status"] == "finalized"
    assert witem["ai_feedback"] == "Tốt, cần mở bài rõ hơn."
    assert witem["final_score"] == 0.8


@pytest.mark.asyncio
async def test_quota_exceeded_degrades_to_manual(client, session_factory):
    class_id, student, qids = await _seed(session_factory)
    # đặt hạn mức writing = 0 cho kỳ hiện tại -> vượt ngay
    period = grading._period()
    async with session_factory() as s0, s0.begin():
        await set_tenant(s0, TID)
        await s0.execute(
            text(
                "INSERT INTO tenant_ai_quota (tenant_id, period, writing_limit, writing_used) "
                "VALUES (:t, :p, 0, 0) ON CONFLICT (tenant_id, period) "
                "DO UPDATE SET writing_limit = 0"
            ),
            {"t": TID, "p": period},
        )

    attempt_id, _ = await _assign_and_submit(client, class_id, qids, student)

    s = await _svc(session_factory)
    try:
        w = await _writing_answer(s, attempt_id)
        assert w["grade_status"] == "needs_manual"  # degrade vì vượt quota
        assert w["ai_score"] is None
        assert w["job_status"] == "needs_manual"
    finally:
        await s.__aexit__(None, None, None)
