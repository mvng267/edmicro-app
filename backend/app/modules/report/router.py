from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.report import pdf as pdf_mod
from app.modules.report import service as svc

router = APIRouter(prefix="/api/v1", tags=["report"])

# Vai trò được xem báo cáo lớp/học sinh của tenant.
_VIEWER_ROLES = {"owner", "manager", "academic_head", "teacher", "assistant"}
# Xem toàn tenant, không giới hạn theo lớp được gán.
_TENANT_WIDE = {"owner", "manager", "academic_head"}


async def _staff_of_class(s: AsyncSession, user_id: str, class_id: str) -> bool:
    return (
        await s.execute(
            text("SELECT 1 FROM class_staff WHERE class_id = :c AND user_id = :u LIMIT 1"),
            {"c": class_id, "u": user_id},
        )
    ).first() is not None


async def _shares_class(s: AsyncSession, staff_id: str, student_id: str) -> bool:
    """teacher/assistant có cùng lớp với học sinh không (class_staff ∩ class_students)."""
    return (
        await s.execute(
            text(
                "SELECT 1 FROM class_staff cst "
                "JOIN class_students cs ON cs.class_id = cst.class_id AND cs.left_at IS NULL "
                "WHERE cst.user_id = :st AND cs.user_id = :hs LIMIT 1"
            ),
            {"st": staff_id, "hs": student_id},
        )
    ).first() is not None


@router.get("/me/report")
async def my_report(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    return await svc.student_report(s, current.user_id)


@router.get("/reports/classes/{class_id}")
async def class_report(
    class_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _VIEWER_ROLES:
        raise HTTPException(403, "forbidden_role")
    if current.role not in _TENANT_WIDE and not await _staff_of_class(s, current.user_id, class_id):
        raise HTTPException(403, "not_your_class")
    return await svc.class_report(s, class_id)


@router.get("/reports/students/{student_id}")
async def student_report(
    student_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _VIEWER_ROLES:
        raise HTTPException(403, "forbidden_role")
    if current.role not in _TENANT_WIDE and not await _shares_class(s, current.user_id, student_id):
        raise HTTPException(403, "not_your_student")
    return await svc.student_report(s, student_id)


# ── PDF báo cáo học tập (SRS REPORT §5.4) ──────────────────────


async def render_student_pdf(s: AsyncSession, student_id: str) -> Response:
    """Dựng PDF cho 1 HS (tên + tenant + báo cáo + chuyên cần gần đây)."""
    info = (
        (
            await s.execute(
                text(
                    "SELECT COALESCE(NULLIF(u.full_name, ''), u.username) AS name, t.name AS tname "
                    "FROM users u JOIN tenants t ON t.id = u.tenant_id WHERE u.id = :id"
                ),
                {"id": student_id},
            )
        )
        .mappings()
        .first()
    )
    if info is None:
        raise HTTPException(404, "student_not_found")
    report = await svc.student_report(s, student_id)
    attendance = (
        (
            await s.execute(
                text(
                    "SELECT cs.topic, cs.starts_at, a.status FROM attendance a "
                    "JOIN class_sessions cs ON cs.id = a.session_id "
                    "WHERE a.student_id = :id ORDER BY cs.starts_at DESC LIMIT 10"
                ),
                {"id": student_id},
            )
        )
        .mappings()
        .all()
    )
    data = pdf_mod.build_student_report_pdf(
        tenant_name=info["tname"],
        student_name=info["name"],
        report=report,
        attendance=[
            {"topic": a["topic"], "starts_at": a["starts_at"].isoformat(), "status": a["status"]}
            for a in attendance
        ],
    )
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="bao-cao-hoc-tap.pdf"'},
    )


@router.get("/me/report/pdf")
async def my_report_pdf(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    return await render_student_pdf(s, current.user_id)


@router.get("/reports/students/{student_id}/pdf")
async def student_report_pdf(
    student_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _VIEWER_ROLES:
        raise HTTPException(403, "forbidden_role")
    if current.role not in _TENANT_WIDE and not await _shares_class(s, current.user_id, student_id):
        raise HTTPException(403, "not_your_student")
    return await render_student_pdf(s, student_id)
