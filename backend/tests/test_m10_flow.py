import uuid

import httpx
import pytest
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.core.security import decode_token
from app.db import set_tenant
from app.main import app

TID = str(uuid.uuid4())
OTHER_TID = str(uuid.uuid4())


async def _seed(session_factory):
    """Lớp + 1 HS; 2 activity_logs của tenant + 1 của tenant khác (kiểm tra cách ly)."""
    class_id = str(uuid.uuid4())
    student = str(uuid.uuid4())
    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        await s.execute(
            text(
                "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'M10') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": TID, "sl": f"m10-{TID[:8]}"},
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
        # 2 log của tenant này
        for module in ("ASSIGN", "GRADE"):
            await s.execute(
                text(
                    "INSERT INTO activity_logs (tenant_id, actor_id, actor_role, action, module) "
                    "VALUES (:t, :a, 'teacher', 'create', :m)"
                ),
                {"t": TID, "a": str(uuid.uuid4()), "m": module},
            )

    # 1 log của TENANT KHÁC — phải ghi bằng session của chính nó, vì RLS (migration 0012)
    # chặn ghi chéo tenant. Dùng để chứng minh /admin/logs không đọc thấy log tenant khác.
    async with session_factory() as s2, s2.begin():
        await set_tenant(s2, OTHER_TID)
        await s2.execute(
            text(
                "INSERT INTO activity_logs (tenant_id, actor_id, actor_role, action, module) "
                "VALUES (:t, :a, 'teacher', 'create', 'ASSIGN')"
            ),
            {"t": OTHER_TID, "a": str(uuid.uuid4())},
        )
    return class_id, student


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
async def test_log_admin_and_usage(client, session_factory):
    _class_id, student = await _seed(session_factory)

    # student KHÔNG xem log/usage
    _as("student", student)
    assert (await client.get("/api/v1/admin/logs")).status_code == 403
    assert (await client.get("/api/v1/usage")).status_code == 403

    # owner: log CHỈ của tenant mình (2), không thấy tenant khác
    _as("owner", str(uuid.uuid4()))
    logs = (await client.get("/api/v1/admin/logs")).json()
    assert len(logs) == 2
    assert {r["module"] for r in logs} == {"ASSIGN", "GRADE"}
    # lọc theo module
    only = (await client.get("/api/v1/admin/logs?module=ASSIGN")).json()
    assert len(only) == 1 and only[0]["module"] == "ASSIGN"

    # usage: counts + quota
    u = (await client.get("/api/v1/usage")).json()
    assert u["students"] >= 1 and u["classes"] >= 1
    assert "ai_writing" in u and "limit" in u["ai_writing"]


@pytest.mark.asyncio
async def test_tickets_and_impersonation(client, session_factory):
    _class_id, student = await _seed(session_factory)
    other_student = str(uuid.uuid4())

    # HS tạo ticket
    _as("student", student)
    tid = (
        await client.post(
            "/api/v1/support/tickets", json={"subject": "Không vào được bài", "body": "Lỗi 500"}
        )
    ).json()["id"]
    mine = (await client.get("/api/v1/support/tickets")).json()
    assert any(t["id"] == tid for t in mine)

    # HS khác không xem được ticket này
    _as("student", other_student)
    assert (await client.get(f"/api/v1/support/tickets/{tid}")).status_code == 403

    # owner (staff) xem + comment + đóng
    _as("owner", str(uuid.uuid4()))
    det = (await client.get(f"/api/v1/support/tickets/{tid}")).json()
    assert det["subject"] == "Không vào được bài"
    await client.post(f"/api/v1/support/tickets/{tid}/comments", json={"body": "Đang kiểm tra"})
    assert (await client.post(f"/api/v1/support/tickets/{tid}/close")).status_code == 200
    det2 = (await client.get(f"/api/v1/support/tickets/{tid}")).json()
    assert det2["status"] == "closed"
    assert len(det2["comments"]) == 1

    # impersonation: owner đăng nhập thay HS -> token của HS + ghi audit
    imp = await client.post(f"/api/v1/support/impersonate/{student}")
    assert imp.status_code == 200
    body = imp.json()
    assert body["as_role"] == "student"
    claims = decode_token(body["access_token"])
    assert claims["sub"] == student and claims["role"] == "student"

    async with session_factory() as s, s.begin():
        await set_tenant(s, TID)
        n = (
            await s.execute(
                text(
                    "SELECT count(*) FROM audit_logs WHERE action = 'impersonate' "
                    "AND target_id = :u"
                ),
                {"u": student},
            )
        ).scalar_one()
        assert n == 1

    # student KHÔNG impersonate được
    _as("student", student)
    assert (await client.post(f"/api/v1/support/impersonate/{other_student}")).status_code == 403


@pytest.mark.asyncio
async def test_rls_chan_ghi_log_cheo_tenant(session_factory):
    """Bằng chứng migration 0012: DB tự chặn ghi activity/audit log sang tenant khác.

    Trước khi bật RLS, 2 bảng log không có policy nên chỉ cần quên lọc tenant ở query
    là lộ log tenant khác — nay Postgres chặn ở tầng dữ liệu.
    """
    from sqlalchemy.exc import ProgrammingError

    for table, cols in (
        ("activity_logs", "(tenant_id, action, module) VALUES (:t, 'create', 'ORG')"),
        ("audit_logs", "(tenant_id, action, target_type) VALUES (:t, 'delete', 'user')"),
    ):
        async with session_factory() as s:
            await set_tenant(s, TID)  # autobegin transaction
            with pytest.raises(ProgrammingError, match="row-level security"):
                await s.execute(text(f"INSERT INTO {table} {cols}"), {"t": OTHER_TID})
            await s.rollback()
