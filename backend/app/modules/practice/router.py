from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.practice import service as svc

router = APIRouter(prefix="/api/v1/practices", tags=["practice"])

_AUTHOR_ROLES = {"owner", "manager", "academic_head", "teacher"}


class PracticeCreate(BaseModel):
    name: str
    skill: str | None = None
    language: str = "en"
    question_ids: list[str]


@router.post("", status_code=201)
async def create_practice(
    body: PracticeCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _AUTHOR_ROLES:
        raise HTTPException(403, "forbidden_role")
    try:
        pid = await svc.create_practice(s, current.tenant_id, current.user_id, body.model_dump())
    except svc.InvalidQuestion as e:
        raise HTTPException(422, str(e)) from None
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="create",
        module="PRACTICE",
        entity_type="practice",
        entity_id=pid,
        diff={"name": body.name, "n_q": len(body.question_ids)},
    )
    return {"id": pid}


@router.get("")
async def list_practices(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _AUTHOR_ROLES:
        raise HTTPException(403, "forbidden_role")
    return await svc.list_practices(s)


@router.get("/{practice_id}")
async def get_practice(
    practice_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _AUTHOR_ROLES:
        raise HTTPException(403, "forbidden_role")
    p = await svc.get_practice(s, practice_id, for_attempt=False)
    if p is None:
        raise HTTPException(404, "not_found")
    return p
