import io
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text

from app.core import storage
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import set_tenant
from app.main import app

TID = str(uuid.uuid4())
OTHER_TID = str(uuid.uuid4())
WAV = b"RIFF$\x00\x00\x00WAVEfmt " + b"\x00" * 100  # giả lập wav nhỏ


@pytest.fixture(autouse=True)
def _mem_storage():
    storage.use_memory_storage()


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


def _as(role: str, uid: str | None = None, tid: str = TID):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        uid or str(uuid.uuid4()), tid, role
    )


@pytest.mark.asyncio
async def test_upload_and_fetch_media(client):
    # student KHÔNG upload được
    _as("student")
    r = await client.post(
        "/api/v1/media", files={"file": ("beep.wav", io.BytesIO(WAV), "audio/wav")}
    )
    assert r.status_code == 403

    # teacher upload OK; loại file lạ bị 422
    _as("teacher")
    bad = await client.post(
        "/api/v1/media", files={"file": ("x.exe", io.BytesIO(b"MZ"), "application/x-msdownload")}
    )
    assert bad.status_code == 422
    up = await client.post(
        "/api/v1/media", files={"file": ("beep.wav", io.BytesIO(WAV), "audio/wav")}
    )
    assert up.status_code == 201, up.text
    key = up.json()["key"]
    assert key.startswith(f"{TID}/")

    # cùng tenant (student) nghe được — round-trip đúng bytes
    _as("student", tid=TID)
    got = await client.get(f"/api/v1/media/{key}")
    assert got.status_code == 200
    assert got.content == WAV
    assert got.headers["content-type"].startswith("audio/wav")

    # TENANT KHÁC bị chặn dù biết key
    _as("teacher", tid=OTHER_TID)
    assert (await client.get(f"/api/v1/media/{key}")).status_code == 403


@pytest.mark.asyncio
async def test_listening_question_carries_audio(client, session_factory):
    """Câu nghe có audio_key → HS thấy audio_key khi làm bài (ẩn answer_key)."""
    class_id = str(uuid.uuid4())
    hs = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'MD') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"md-{TID[:8]}"},
        )
        bid = str(uuid.uuid4())
        await s.execute(
            text("INSERT INTO branches (id, tenant_id, name) VALUES (:b, :t, 'CN')"),
            {"b": bid, "t": TID},
        )
        await s.execute(
            text("INSERT INTO classes (id, tenant_id, branch_id, name) VALUES (:c, :t, :b, 'L')"),
            {"c": class_id, "t": TID, "b": bid},
        )
        await s.execute(
            text(
                "INSERT INTO users (id, tenant_id, username, password_hash, role) "
                "VALUES (:id, :t, :un, 'x', 'student')"
            ),
            {"id": hs, "t": TID, "un": f"hs-{hs[:8]}"},
        )
        await s.execute(
            text("INSERT INTO class_students (tenant_id, class_id, user_id) VALUES (:t, :c, :u)"),
            {"t": TID, "c": class_id, "u": hs},
        )

    # teacher: upload audio + tạo câu nghe + practice + giao
    _as("teacher")
    key = (
        await client.post(
            "/api/v1/media", files={"file": ("listen.wav", io.BytesIO(WAV), "audio/wav")}
        )
    ).json()["key"]
    q = await client.post(
        "/api/v1/content/questions",
        json={
            "type": "mcq_single",
            "language": "en",
            "skill": "listening",
            "content": {"prompt": "Nghe và chọn:", "options": ["cat", "cut"], "audio_key": key},
            "answer_key": {"correct_index": 0},
        },
    )
    qid = q.json()["id"]
    await client.post(f"/api/v1/content/questions/{qid}/publish")
    pid = (
        await client.post("/api/v1/practices", json={"name": "Nghe 1", "question_ids": [qid]})
    ).json()["id"]
    due = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    await client.post(
        "/api/v1/assignments", json={"content_id": pid, "class_id": class_id, "due_at": due}
    )

    # HS start: câu có audio_key, KHÔNG lộ answer_key
    _as("student", hs)
    aid = (await client.get("/api/v1/me/assignments")).json()[0]["assignee_id"]
    start = (await client.post(f"/api/v1/assignments/{aid}/start")).json()
    qq = start["practice"]["questions"][0]
    assert qq["content"]["audio_key"] == key
    assert "answer_key" not in qq
    # HS tải audio bằng chính key đó
    assert (await client.get(f"/api/v1/media/{key}")).status_code == 200
