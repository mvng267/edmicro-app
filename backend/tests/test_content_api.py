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


@pytest.mark.asyncio
async def test_archive_and_pagination(client, session_factory):
    """Lưu trữ ẩn câu khỏi kho mặc định; pagination limit/offset hoạt động."""
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'AR') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"ar-{TID[:8]}"},
        )
    _as("teacher")
    tag = uuid.uuid4().hex[:6]
    ids = []
    for i in range(3):
        r = await client.post(
            "/api/v1/content/questions",
            json={
                "type": "mcq_single",
                "language": "en",
                "topic": f"pg-{tag}",
                "content": {"prompt": f"PG {tag} {i}?", "options": ["a", "b"]},
                "answer_key": {"correct_index": 0},
            },
        )
        ids.append(r.json()["id"])

    # pagination: limit=2 → 2 câu; offset=2 → 1 câu còn lại
    base = f"/api/v1/content/questions?topic=pg-{tag}"
    assert len((await client.get(f"{base}&limit=2")).json()) == 2
    assert len((await client.get(f"{base}&limit=2&offset=2")).json()) == 1

    # archive câu đầu → biến khỏi danh sách mặc định, chỉ hiện khi lọc status=archived
    assert (await client.post(f"/api/v1/content/questions/{ids[0]}/archive")).status_code == 200
    remain = (await client.get(base)).json()
    assert len(remain) == 2
    assert all(x["id"] != ids[0] for x in remain)
    archived = (await client.get(f"{base}&status=archived")).json()
    assert [x["id"] for x in archived] == [ids[0]]

    # student không archive được
    _as("student")
    assert (await client.post(f"/api/v1/content/questions/{ids[1]}/archive")).status_code == 403


@pytest.mark.asyncio
async def test_folder_tree_crud_and_move(client, session_factory):
    """Cây thư mục: tạo (cha/con) → đổi tên → gán câu vào → lọc → chặn xóa khi chưa rỗng."""
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'FD') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"fd-{TID[:8]}"},
        )
    _as("teacher")
    # tạo thư mục cha + con
    root = (await client.post("/api/v1/content/folders", json={"name": "IELTS"})).json()["id"]
    child = (
        await client.post("/api/v1/content/folders", json={"name": "Reading", "parent_id": root})
    ).json()["id"]
    # đổi tên
    assert (
        await client.patch(f"/api/v1/content/folders/{child}", json={"name": "Reading L1"})
    ).status_code == 200
    folders = (await client.get("/api/v1/content/folders")).json()
    by_id = {f["id"]: f for f in folders}
    assert by_id[child]["name"] == "Reading L1"
    assert by_id[child]["parent_id"] == root

    # tạo câu TRỰC TIẾP vào thư mục con
    q = await client.post(
        "/api/v1/content/questions",
        json={
            "type": "mcq_single",
            "language": "en",
            "folder_id": child,
            "content": {"prompt": "Trong thư mục?", "options": ["a", "b"]},
            "answer_key": {"correct_index": 0},
        },
    )
    qid = q.json()["id"]

    # lọc theo thư mục + đếm
    in_child = (await client.get(f"/api/v1/content/questions?folder_id={child}")).json()
    assert [x["id"] for x in in_child] == [qid]
    folders = (await client.get("/api/v1/content/folders")).json()
    assert {f["id"]: f["n_questions"] for f in folders}[child] == 1

    # xóa thư mục CHƯA rỗng → 409 (cả cha vì còn con)
    assert (await client.delete(f"/api/v1/content/folders/{child}")).status_code == 409
    assert (await client.delete(f"/api/v1/content/folders/{root}")).status_code == 409

    # chuyển câu về "chưa phân loại" → giờ con rỗng, xóa được; rồi xóa cha
    assert (
        await client.patch(f"/api/v1/content/questions/{qid}/folder", json={"folder_id": None})
    ).status_code == 200
    assert (await client.get("/api/v1/content/questions?folder_id=none")).json()[0]["id"] == qid
    assert (await client.delete(f"/api/v1/content/folders/{child}")).status_code == 200
    assert (await client.delete(f"/api/v1/content/folders/{root}")).status_code == 200

    # student không được đụng thư mục
    _as("student")
    assert (await client.post("/api/v1/content/folders", json={"name": "X"})).status_code == 403
