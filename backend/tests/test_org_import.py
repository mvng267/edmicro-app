import io
import uuid

import httpx
import pytest
from openpyxl import Workbook
from sqlalchemy import text

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.db import get_session, set_tenant
from app.main import app

TID = str(uuid.uuid4())
SLUG = f"imp-{TID[:8]}"


def _xlsx(rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["Họ tên", "Ngày sinh", "Giới tính", "Email", "SĐT phụ huynh", "Mã lớp", "Ghi chú"])
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
async def client(session_factory):
    async with session_factory() as s:
        async with s.begin():
            await set_tenant(s, TID)
            await s.execute(
                text(
                    "INSERT INTO tenants (id, slug, name) VALUES (:id, :sl, 'Imp') "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {"id": TID, "sl": SLUG},
            )
            bid = str(uuid.uuid4())
            await s.execute(
                text("INSERT INTO branches (id, tenant_id, name) VALUES (:b, :t, 'CN')"),
                {"b": bid, "t": TID},
            )
            await s.execute(
                text(
                    "INSERT INTO classes (id, tenant_id, branch_id, name) "
                    "VALUES (gen_random_uuid(), :t, :b, 'IELTS-1')"
                ),
                {"t": TID, "b": bid},
            )

    async def _override_session():
        async with session_factory() as s:
            async with s.begin():
                await set_tenant(s, TID)
                yield s

    app.dependency_overrides[get_tenant_session] = _override_session
    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        str(uuid.uuid4()), TID, "it_admin"
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_import_validate_then_commit_and_login(client):
    content = _xlsx(
        [
            ["Nguyễn A", "01/05/2015", "Nam", "", "0900000001", "IELTS-1", ""],
            ["Trần B", "10/10/2014", "Nữ", "", "0900000002", "IELTS-1", ""],
            ["Lê C", "2013-03-03", "Nam", "", "", "IELTS-1", ""],
            ["Phạm D", "01/05/2015", "Nam", "", "", "LỚP-SAI", ""],  # lỗi lớp
            ["", "01/01/2015", "", "", "", "IELTS-1", ""],  # thiếu tên
        ]
    )
    files = {"file": ("hs.xlsx", content, "application/vnd.openxmlformats")}
    r = await client.post("/api/v1/org/users/import", files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"] == {"total": 5, "valid": 3, "errors": 2}
    job_id = body["job_id"]

    # commit -> tạo 3 học sinh
    c = await client.post(f"/api/v1/org/users/import/{job_id}/commit")
    assert c.status_code == 200, c.text
    creds = c.json()["credentials"]
    assert len(creds) == 3

    # commit lại -> 409
    again = await client.post(f"/api/v1/org/users/import/{job_id}/commit")
    assert again.status_code == 409

    # học sinh import login được
    del app.dependency_overrides[get_current_user]
    login = await client.post(
        "/api/v1/authz/login",
        json={"username": creds[0]["username"], "password": creds[0]["password"]},
        headers={"X-Tenant-Slug": SLUG},
    )
    assert login.status_code == 200, login.text
