"""API khóa học. Xem SRS COURSE FR-COURSE."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.course import service as svc

router = APIRouter(prefix="/api/v1", tags=["course"])

_AUTHOR_ROLES = {"owner", "manager", "academic_head", "teacher", "content_editor"}


class CourseCreate(BaseModel):
    name: str
    language: str = "en"


class LessonCreate(BaseModel):
    title: str
    kind: str = "text"
    body: str = ""
    content_ref: str | None = None


class AssignCourse(BaseModel):
    class_id: str


def _require_author(current: CurrentUser) -> None:
    if current.role not in _AUTHOR_ROLES:
        raise HTTPException(403, "forbidden_role")


@router.post("/courses", status_code=201)
async def create_course(
    body: CourseCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    cid = await svc.create_course(s, current.tenant_id, current.user_id, body.model_dump())
    return {"id": cid}


@router.post("/courses/{course_id}/lessons", status_code=201)
async def add_lesson(
    course_id: str,
    body: LessonCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    try:
        lid = await svc.add_lesson(s, current.tenant_id, course_id, body.model_dump())
    except svc.InvalidLesson as e:
        raise HTTPException(422, str(e)) from None
    return {"id": lid}


@router.post("/courses/{course_id}/assign", status_code=201)
async def assign_course(
    course_id: str,
    body: AssignCourse,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    await svc.assign_to_class(s, current.tenant_id, course_id, body.class_id)
    return {"assigned": True}


@router.get("/courses")
async def list_courses(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    return await svc.list_courses(s)


@router.get("/courses/{course_id}")
async def get_course(
    course_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    c = await svc.get_course(s, course_id)
    if c is None:
        raise HTTPException(404, "not_found")
    return c


@router.get("/me/courses")
async def my_courses(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    return await svc.list_student_courses(s, current.user_id)


@router.get("/me/courses/{course_id}")
async def my_course_detail(
    course_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    c = await svc.get_course(s, course_id, student_id=current.user_id)
    if c is None:
        raise HTTPException(404, "not_found")
    return c


@router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(
    lesson_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "student":
        raise HTTPException(403, "students_only")
    try:
        return await svc.complete_lesson(s, current.tenant_id, current.user_id, lesson_id)
    except PermissionError:
        raise HTTPException(403, "not_your_course") from None
