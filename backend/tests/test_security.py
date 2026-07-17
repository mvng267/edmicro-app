from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    h = hash_password("s3cret!")
    assert h != "s3cret!"
    assert verify_password("s3cret!", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_roundtrip():
    token = create_access_token(user_id="u1", tenant_id="t1", role="owner")
    claims = decode_token(token)
    assert claims["sub"] == "u1"
    assert claims["tenant_id"] == "t1"
    assert claims["role"] == "owner"
    assert claims["type"] == "access"
