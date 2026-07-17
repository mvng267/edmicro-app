from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.activity_log import log_activity
from app.core.audit import log_audit
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.modules.org import users_service as us
from app.modules.org.schemas import CredentialOut, ParentCreate, ScopeSet, UserCreate, UserOut

router = APIRouter(prefix="/api/v1/org", tags=["org-users"])

_MANAGE = {"owner", "manager", "it_admin"}


@router.post("/users", response_model=CredentialOut, status_code=201)
async def create_user(
    body: UserCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE:
        raise HTTPException(403, "forbidden_role")
    try:
        cred = await us.create_user(s, current.tenant_id, current.role, body.model_dump())
    except us.Forbidden as e:
        raise HTTPException(403, str(e)) from None
    except us.Duplicate as e:
        raise HTTPException(409, str(e)) from None
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="create",
        module="ORG",
        entity_type="user",
        entity_id=cred["id"],
        diff={"role": body.role, "username": cred["username"]},
    )
    return cred


@router.get("/users", response_model=list[UserOut])
async def list_users(
    q: str | None = None,
    role: str | None = None,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE:
        raise HTTPException(403, "forbidden_role")
    sql = "SELECT id, username, full_name, role, status FROM users WHERE 1=1"
    params: dict = {}
    if q:
        sql += " AND (username ILIKE :q OR full_name ILIKE :q)"
        params["q"] = f"%{q}%"
    if role:
        sql += " AND role = :r"
        params["r"] = role
    sql += " ORDER BY created_at DESC LIMIT 200"
    rows = (await s.execute(text(sql), params)).mappings().all()
    return [{**r, "id": str(r["id"])} for r in rows]


@router.post("/users/{user_id}/reset-password", response_model=dict)
async def reset_password(
    user_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE:
        raise HTTPException(403, "forbidden_role")
    target = await us.get_role(s, user_id)
    if target is None:
        raise HTTPException(404, "not_found")
    if target in us.MANAGEMENT_ROLES and current.role != "owner":
        raise HTTPException(403, "only_owner_for_management")
    password = await us.reset_password(s, user_id)
    await log_audit(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="reset_password",
        target_type="user",
        target_id=user_id,
    )
    return {"password": password}


@router.post("/users/{user_id}/lock", status_code=200)
async def lock_user(
    user_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE:
        raise HTTPException(403, "forbidden_role")
    target = await us.get_role(s, user_id)
    if target is None:
        raise HTTPException(404, "not_found")
    if target in us.MANAGEMENT_ROLES and current.role != "owner":
        raise HTTPException(403, "only_owner_for_management")
    await us.set_locked(s, user_id, True)
    await log_audit(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="lock_user",
        target_type="user",
        target_id=user_id,
    )
    return {"ok": True}


@router.put("/users/{user_id}/role", status_code=200)
async def change_role(
    user_id: str,
    body: dict,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "owner":
        raise HTTPException(403, "only_owner")
    new_role = body.get("role")
    if new_role not in us.TENANT_ROLES:
        raise HTTPException(422, "invalid_role")
    old = await us.get_role(s, user_id)
    if old is None:
        raise HTTPException(404, "not_found")
    await s.execute(
        text("UPDATE users SET role = :r WHERE id = :id"), {"r": new_role, "id": user_id}
    )
    await log_audit(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="change_role",
        target_type="user",
        target_id=user_id,
        before={"role": old},
        after={"role": new_role},
    )
    return {"ok": True}


@router.post("/parents", response_model=CredentialOut, status_code=201)
async def create_parent(
    body: ParentCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role not in _MANAGE:
        raise HTTPException(403, "forbidden_role")
    cred = await us.create_user(
        s,
        current.tenant_id,
        current.role,
        {"full_name": body.full_name, "role": "parent", "parent_phone": body.parent_phone},
    )
    for sid in body.student_ids:
        await us.link_parent(s, current.tenant_id, cred["id"], sid, current.user_id)
    await log_activity(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="create",
        module="ORG",
        entity_type="parent",
        entity_id=cred["id"],
        diff={"children": len(body.student_ids)},
    )
    return cred


@router.put("/users/{user_id}/scopes", status_code=200)
async def set_scopes(
    user_id: str,
    body: ScopeSet,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if current.role != "owner":
        raise HTTPException(403, "only_owner")
    await us.set_scopes(s, current.tenant_id, user_id, body.branch_ids)
    await log_audit(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="set_scopes",
        target_type="user",
        target_id=user_id,
        after={"branch_ids": body.branch_ids},
    )
    return {"ok": True}
