import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app
from app.modules.content import service as content_svc
from app.modules.exam import service as exam_svc

TID = str(uuid.uuid4())
SCALE = [{"min": 0, "band": "5.0"}, {"min": 50, "band": "6.0"}, {"min": 80, "band": "7.0"}]


def test_band_for_edges():
    assert exam_svc.band_for(SCALE, 90) == "7.0"
    assert exam_svc.band_for(SCALE, 50) == "6.0"
    assert exam_svc.band_for(SCALE, 49.9) == "5.0"
    assert exam_svc.band_for(SCALE, 0) == "5.0"
    assert exam_svc.band_for([], 100) is None
    assert exam_svc.band_for(None, 100) is None


async def _seed_exam(session_factory):
    """Lớp + 1 HS + đề thi 2 câu đóng (q0 đúng=0, q1 đúng=1), 60 phút.

    Trả (class_id, hs, exam_id).
    """
    class_id = str(uuid.uuid4())
    hs = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'E7') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"e7-{TID[:8]}"},
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
            {"id": hs, "t": TID, "un": f"hs-{hs[:8]}"},
        )
        await s.execute(
            text("INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"),
            {"t": TID, "c": class_id, "u": hs},
        )
        qids = []
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
        exam_id = await exam_svc.create_exam(
            s,
            TID,
            str(uuid.uuid4()),
            {
                "name": "Đề thi thử",
                "question_ids": qids,
                "duration_minutes": 60,
                "band_scale": SCALE,
            },
        )
    return class_id, hs, exam_id


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


async def _publish_two(session_factory):
    qids = []
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'E7') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"e7-{TID[:8]}"},
        )
        for i in range(2):
            qid = await content_svc.create_question(
                s,
                TID,
                str(uuid.uuid4()),
                {
                    "type": "mcq_single",
                    "language": "en",
                    "content": {"prompt": f"E{i}?", "options": ["a", "b"]},
                    "answer_key": {"correct_index": 0},
                },
            )
            await content_svc.publish_question(s, qid)
            qids.append(qid)
    return qids


@pytest.mark.asyncio
async def test_create_exam_api_rbac(client, session_factory):
    qids = await _publish_two(session_factory)
    body = {
        "name": f"Đề {uuid.uuid4().hex[:6]}",
        "question_ids": qids,
        "duration_minutes": 30,
        "band_scale": SCALE,
    }
    # student KHÔNG được tạo đề
    _as("student", str(uuid.uuid4()))
    assert (await client.post("/api/v1/exams", json=body)).status_code == 403

    # teacher tạo đề -> 201; xuất hiện trong danh sách
    _as("teacher", str(uuid.uuid4()))
    r = await client.post("/api/v1/exams", json=body)
    assert r.status_code == 201, r.text
    eid = r.json()["id"]
    exams = (await client.get("/api/v1/exams")).json()
    assert any(e["id"] == eid and e["duration_minutes"] == 30 for e in exams)


@pytest.mark.asyncio
async def test_exam_clock_and_band(client, session_factory):
    class_id, hs, exam_id = await _seed_exam(session_factory)

    # GV giao đề cho lớp (dùng chung endpoint assignment)
    _as("teacher", str(uuid.uuid4()))
    due = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    asg = await client.post(
        "/api/v1/assignments", json={"content_id": exam_id, "class_id": class_id, "due_at": due}
    )
    assert asg.status_code == 201, asg.text

    # HS bắt đầu thi -> start trả deadline (đồng hồ server)
    _as("student", hs)
    aid = (await client.get("/api/v1/me/assignments")).json()[0]["assignee_id"]
    start = (await client.post(f"/api/v1/assignments/{aid}/start")).json()
    attempt_id = start["attempt_id"]
    assert start["deadline_at"] is not None
    assert start["duration_minutes"] == 60

    qs = start["practice"]["questions"]
    # trả lời q0 đúng (0), q1 sai (0) -> 1/2 = 50%
    await client.put(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_version_id": qs[0]["question_version_id"], "payload": {"selected": 0}},
    )
    await client.put(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_version_id": qs[1]["question_version_id"], "payload": {"selected": 0}},
    )

    # hết giờ (đẩy deadline về quá khứ) -> khóa lưu
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text("UPDATE attempts SET deadline_at = now() - interval '1 minute' WHERE id = :id"),
            {"id": attempt_id},
        )
    late = await client.put(
        f"/api/v1/attempts/{attempt_id}/answers",
        json={"question_version_id": qs[0]["question_version_id"], "payload": {"selected": 1}},
    )
    assert late.status_code == 409

    # nộp (tự nộp khi hết giờ) -> chấm; kết quả có band quy đổi 50% -> 6.0
    sub = await client.post(f"/api/v1/attempts/{attempt_id}/submit")
    assert sub.status_code == 200
    res = (await client.get(f"/api/v1/attempts/{attempt_id}/result")).json()
    assert res["score"] == 50.0
    assert res["is_exam"] is True
    assert res["band"] == "6.0"
    assert res["duration_minutes"] == 60
