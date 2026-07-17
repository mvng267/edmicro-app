from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.modules.authz import repository


class InvalidCredentials(Exception):
    pass


async def login(session: AsyncSession, username: str, password: str) -> dict:
    user = await repository.find_user_by_username(session, username)
    if user is None or not verify_password(password, user["password_hash"]):
        raise InvalidCredentials
    uid, tid, role = str(user["id"]), str(user["tenant_id"]), user["role"]
    return {
        "access_token": create_access_token(user_id=uid, tenant_id=tid, role=role),
        "refresh_token": create_refresh_token(user_id=uid, tenant_id=tid, role=role),
        "must_change_password": user["must_change_password"],
    }
