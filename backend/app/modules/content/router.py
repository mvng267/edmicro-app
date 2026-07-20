from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
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
        },
    )


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
