from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.content import ai_service
from app.modules.content import service as svc
from app.modules.content.schemas import (
    QuestionCreate,
    QuestionDetail,
    QuestionRow,
    QuestionUpdate,
)

router = APIRouter(prefix="/api/v1/content", tags=["content"])

_AUTHOR_ROLES = {"owner", "manager", "academic_head", "teacher"}


def _require_author(current: CurrentUser) -> None:
    if current.role not in _AUTHOR_ROLES:
        raise HTTPException(403, "forbidden_role")


async def _log(s, current, action, qid, diff=None):
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action=action,
        module="CONTENT",
        entity_type="question",
        entity_id=qid,
        diff=diff or {},
    )


@router.post("/questions", status_code=201)
async def create_question(
    body: QuestionCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    try:
        qid = await svc.create_question(s, current.tenant_id, current.user_id, body.model_dump())
    except svc.InvalidContent as e:
        raise HTTPException(422, str(e)) from None
    await _log(s, current, "create", qid, {"type": body.type})
    return {"id": qid}


@router.get("/questions", response_model=list[QuestionRow])
async def list_questions(
    language: str | None = None,
    skill: str | None = None,
    level: str | None = None,
    status: str | None = None,
    exam_tag: str | None = None,
    topic: str | None = None,
    folder_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    return await svc.list_questions(
        s,
        {
            "language": language,
            "skill": skill,
            "level": level,
            "status": status,
            "exam_tag": exam_tag,
            "topic": topic,
            "folder_id": folder_id,
        },
        limit=limit,
        offset=offset,
    )


class FolderCreate(BaseModel):
    name: str
    parent_id: str | None = None


class FolderRename(BaseModel):
    name: str


class QuestionMove(BaseModel):
    folder_id: str | None = None


class AIGenerateBody(BaseModel):
    topic: str
    skill: str = "reading"
    qtype: str = "mcq_single"
    count: int = 5
    language: str = "en"
    folder_id: str | None = None


@router.get("/folders")
async def list_folders(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    return await svc.list_folders(s)


@router.post("/folders", status_code=201)
async def create_folder(
    body: FolderCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    fid = await svc.create_folder(s, current.tenant_id, body.name, body.parent_id)
    return {"id": fid}


@router.patch("/folders/{folder_id}")
async def rename_folder(
    folder_id: str,
    body: FolderRename,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    try:
        await svc.rename_folder(s, folder_id, body.name)
    except KeyError:
        raise HTTPException(404, "not_found") from None
    return {"ok": True}


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    try:
        await svc.delete_folder(s, folder_id)
    except svc.FolderNotEmpty as e:
        raise HTTPException(409, str(e)) from None
    except KeyError:
        raise HTTPException(404, "not_found") from None
    return {"deleted": True}


@router.patch("/questions/{qid}/folder")
async def move_question(
    qid: str,
    body: QuestionMove,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    try:
        await svc.move_question(s, qid, body.folder_id)
    except KeyError:
        raise HTTPException(404, "not_found") from None
    return {"ok": True}


@router.post("/ai-generate", status_code=201)
async def ai_generate(
    body: AIGenerateBody,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    """AI sinh câu hỏi (draft) vào kho/thư mục — GV duyệt rồi xuất bản tay."""
    _require_author(current)
    try:
        ids = await ai_service.generate_questions(
            s,
            current.tenant_id,
            current.user_id,
            topic=body.topic,
            skill=body.skill,
            qtype=body.qtype,
            count=body.count,
            language=body.language,
            folder_id=body.folder_id,
        )
    except ai_service.AIUnavailable:
        raise HTTPException(503, "ai_not_configured") from None
    except ai_service.AIGenerateFailed as e:
        raise HTTPException(502, str(e)) from None
    await _log(s, current, "ai_generate", ids[0], {"count": len(ids), "topic": body.topic})
    return {"created": len(ids), "question_ids": ids}


@router.post("/questions/{qid}/archive", status_code=200)
async def archive_question(
    qid: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    """Lưu trữ câu hỏi: ẩn khỏi kho, không giao mới; bài đã giao giữ nguyên version cũ."""
    _require_author(current)
    try:
        await svc.archive_question(s, qid)
    except KeyError:
        raise HTTPException(404, "not_found") from None
    await _log(s, current, "archive", qid, {})
    return {"archived": True}


@router.get("/questions/{qid}", response_model=QuestionDetail)
async def get_question(
    qid: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    q = await svc.get_question(s, qid)
    if q is None:
        raise HTTPException(404, "not_found")
    return q


@router.patch("/questions/{qid}", status_code=200)
async def update_question(
    qid: str,
    body: QuestionUpdate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    try:
        version_no = await svc.update_question(
            s, current.tenant_id, qid, current.user_id, body.model_dump()
        )
    except KeyError:
        raise HTTPException(404, "not_found") from None
    except svc.InvalidContent as e:
        raise HTTPException(422, str(e)) from None
    await _log(s, current, "update", qid, {"version_no": version_no})
    return {"version_no": version_no}


@router.post("/questions/{qid}/publish", status_code=200)
async def publish_question(
    qid: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    _require_author(current)
    try:
        await svc.publish_question(s, qid)
    except KeyError:
        raise HTTPException(404, "not_found") from None
    await _log(s, current, "publish", qid)
    return {"ok": True}
