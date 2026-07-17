from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.authn import CurrentUser, get_current_user, get_tenant_session, scope_branch_ids
from app.modules.org import repository as repo
from app.modules.org.schemas import (
    BranchCreate,
    BranchOut,
    BranchUpdate,
    ClassCreate,
    ClassOut,
    StaffAdd,
    StudentAdd,
)

router = APIRouter(prefix="/api/v1/org", tags=["org"])

_MANAGE_ROLES = {"owner", "manager", "it_admin"}


async def _log(s, current: CurrentUser, action, entity_type, entity_id, diff=None):
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action=action,
        module="ORG",
        entity_type=entity_type,
        entity_id=entity_id,
        diff=diff or {},
    )


# ---------------- Branches ----------------
@router.get("/branches", response_model=list[BranchOut])
async def list_branches(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    return await repo.list_branches(s)


@router.post("/branches", response_model=BranchOut, status_code=201)
async def create_branch(
    body: BranchCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "owner":
        raise HTTPException(403, "only_owner")
    b = await repo.create_branch(s, current.tenant_id, body.name, body.address)
    await _log(s, current, "create", "branch", b["id"], {"name": body.name})
    return b


@router.patch("/branches/{branch_id}", response_model=BranchOut)
async def update_branch(
    branch_id: str,
    body: BranchUpdate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "owner":
        raise HTTPException(403, "only_owner")
    if not await repo.branch_exists(s, branch_id):
        raise HTTPException(404, "not_found")
    fields = body.model_dump(exclude_none=True)
    await repo.update_branch(s, branch_id, fields)
    await _log(s, current, "update", "branch", branch_id, fields)
    branches = {b["id"]: b for b in await repo.list_branches(s)}
    return branches[branch_id]


@router.delete("/branches/{branch_id}", status_code=204)
async def delete_branch(
    branch_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "owner":
        raise HTTPException(403, "only_owner")
    if not await repo.branch_exists(s, branch_id):
        raise HTTPException(404, "not_found")
    if await repo.branch_active_class_count(s, branch_id) > 0:
        raise HTTPException(409, "branch_has_active_classes")
    await repo.delete_branch(s, branch_id)
    await _log(s, current, "delete", "branch", branch_id)


# ---------------- Classes ----------------
@router.get("/classes", response_model=list[ClassOut])
async def list_classes(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    branch_ids = await scope_branch_ids(s, current)
    return await repo.list_classes(s, branch_ids)


@router.post("/classes", response_model=ClassOut, status_code=201)
async def create_class(
    body: ClassCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE_ROLES:
        raise HTTPException(403, "forbidden_role")
    if not await repo.branch_exists(s, body.branch_id):
        raise HTTPException(404, "branch_not_found")
    scope = await scope_branch_ids(s, current)
    if scope is not None and body.branch_id not in scope:
        raise HTTPException(403, "branch_out_of_scope")
    c = await repo.create_class(s, current.tenant_id, body.model_dump())
    await _log(s, current, "create", "class", c["id"], {"name": body.name})
    return c


@router.post("/classes/{class_id}/staff", status_code=201)
async def add_staff(
    class_id: str,
    body: StaffAdd,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE_ROLES:
        raise HTTPException(403, "forbidden_role")
    if await repo.get_class_branch(s, class_id) is None:
        raise HTTPException(404, "class_not_found")
    role = await repo.user_role(s, body.user_id)
    if role not in ("teacher", "assistant"):
        raise HTTPException(422, "user_not_teacher_or_assistant")
    await repo.add_staff(s, current.tenant_id, class_id, body.user_id, body.role)
    await _log(s, current, "add_staff", "class", class_id, {"user_id": body.user_id})
    return {"ok": True}


@router.post("/classes/{class_id}/students", status_code=201)
async def add_student(
    class_id: str,
    body: StudentAdd,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE_ROLES:
        raise HTTPException(403, "forbidden_role")
    if await repo.get_class_branch(s, class_id) is None:
        raise HTTPException(404, "class_not_found")
    if await repo.user_role(s, body.user_id) != "student":
        raise HTTPException(422, "user_not_student")
    await repo.add_student(s, current.tenant_id, class_id, body.user_id)
    await _log(s, current, "add_student", "class", class_id, {"user_id": body.user_id})
    return {"ok": True}


@router.post("/classes/{class_id}/students/{user_id}/transfer/{to_class_id}", status_code=201)
async def transfer_student(
    class_id: str,
    user_id: str,
    to_class_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE_ROLES:
        raise HTTPException(403, "forbidden_role")
    if await repo.get_class_branch(s, to_class_id) is None:
        raise HTTPException(404, "target_class_not_found")
    await repo.remove_student(s, class_id, user_id)
    await repo.add_student(s, current.tenant_id, to_class_id, user_id)
    await _log(
        s,
        current,
        "transfer_student",
        "class",
        to_class_id,
        {"user_id": user_id, "from": class_id},
    )
    return {"ok": True}
