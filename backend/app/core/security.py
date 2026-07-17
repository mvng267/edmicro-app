from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

_ph = PasswordHasher()


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def _create_token(*, sub: str, tenant_id: str | None, role: str, ttl: int, ttype: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "role": role,
        "type": ttype,
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_access_token(*, user_id: str, tenant_id: str | None, role: str) -> str:
    return _create_token(
        sub=user_id,
        tenant_id=tenant_id,
        role=role,
        ttl=settings.jwt_access_ttl_seconds,
        ttype="access",
    )


def create_refresh_token(*, user_id: str, tenant_id: str | None, role: str) -> str:
    return _create_token(
        sub=user_id,
        tenant_id=tenant_id,
        role=role,
        ttl=settings.jwt_refresh_ttl_seconds,
        ttype="refresh",
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
