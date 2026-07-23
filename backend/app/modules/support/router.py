"""API hỗ trợ: ticket + impersonation (audit). Xem SRS SUPPORT FR-SUPPORT."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import log_audit
from app.core.authn import CurrentUser, get_current_user, get_tenant_session
from app.core.security import create_access_token
from app.modules.support import service as svc

router = APIRouter(prefix="/api/v1/support", tags=["support"])

_IMPERSONATE_ROLES = {"support_agent", "owner", "admin"}


class TicketCreate(BaseModel):
    subject: str
    body: str = ""


class CommentCreate(BaseModel):
    body: str


def _is_staff(role: str) -> bool:
    return role in svc.STAFF_ROLES


async def _can_view(s: AsyncSession, current: CurrentUser, ticket_id: str) -> bool:
    if _is_staff(current.role):
        return True
    return await svc.ticket_owner(s, ticket_id) == current.user_id


@router.post("/tickets", status_code=201)
async def create_ticket(
    body: TicketCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    tid = await svc.create_ticket(s, current.tenant_id, current.user_id, body.subject, body.body)
    return {"id": tid}


@router.get("/tickets")
async def list_tickets(
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    return await svc.list_tickets(s, current.user_id, _is_staff(current.role))


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if not await _can_view(s, current, ticket_id):
        raise HTTPException(403, "not_your_ticket")
    t = await svc.get_ticket(s, ticket_id)
    if t is None:
        raise HTTPException(404, "not_found")
    return t


@router.post("/tickets/{ticket_id}/comments", status_code=201)
async def add_comment(
    ticket_id: str,
    body: CommentCreate,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if not await _can_view(s, current, ticket_id):
        raise HTTPException(403, "not_your_ticket")
    cid = await svc.add_comment(s, current.tenant_id, ticket_id, current.user_id, body.body)
    return {"id": cid}


@router.post("/tickets/{ticket_id}/close")
async def close_ticket(
    ticket_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    if not _is_staff(current.role):
        raise HTTPException(403, "forbidden_role")
    await svc.close_ticket(s, ticket_id)
    return {"closed": True}


@router.post("/impersonate/{user_id}")
async def impersonate(
    user_id: str,
    current: CurrentUser = Depends(get_current_user),
    s: AsyncSession = Depends(get_tenant_session),
):
    """Đăng nhập thay 1 user cùng tenant — LUÔN ghi audit. Trả access token của user đích."""
    if current.role not in _IMPERSONATE_ROLES:
        raise HTTPException(403, "forbidden_role")
    role = await svc.user_role(s, user_id)  # RLS đảm bảo cùng tenant
    if role is None:
        raise HTTPException(404, "user_not_found")
    await log_audit(
        s,
        tenant_id=current.tenant_id,
        actor_id=current.user_id,
        actor_role=current.role,
        action="impersonate",
        target_type="user",
        target_id=user_id,
        after={"as_role": role},
    )
    token = create_access_token(user_id=user_id, tenant_id=current.tenant_id, role=role)
    return {"access_token": token, "as_role": role}
