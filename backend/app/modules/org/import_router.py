from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.org import import_service as imp

router = APIRouter(prefix="/api/v1/org", tags=["org-import"])

_MANAGE = {"owner", "manager", "it_admin"}


@router.post("/users/import")
async def import_validate(
    file: UploadFile = File(...),
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE:
        raise HTTPException(403, "forbidden_role")
    content = await file.read()
    try:
        result = await imp.validate_file(
            s, current.tenant_id, file.filename or "import.xlsx", content, current.user_id
        )
    except imp.TooManyRows:
        raise HTTPException(413, "too_many_rows") from None
    except Exception:
        raise HTTPException(422, "cannot_parse_file") from None
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="import_validate",
        module="ORG",
        entity_type="import_job",
        entity_id=result["job_id"],
        diff=result["summary"],
    )
    return result


@router.post("/users/import/{job_id}/commit")
async def import_commit(
    job_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE:
        raise HTTPException(403, "forbidden_role")
    try:
        creds = await imp.commit_job(s, current.tenant_id, job_id, current.role)
    except KeyError:
        raise HTTPException(404, "job_not_found") from None
    except ValueError:
        raise HTTPException(409, "already_committed") from None
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="import_commit",
        module="ORG",
        entity_type="import_job",
        entity_id=job_id,
        diff={"created": len(creds)},
    )
    return {"created": len(creds), "credentials": creds}
