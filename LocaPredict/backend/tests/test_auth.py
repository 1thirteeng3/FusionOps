import pytest
from fastapi import HTTPException
from backend.auth.security import (
    create_access_token, decode_access_token, revoke_token,
    verify_password, check_login_rate_limit, ROLES,
)
from backend.core.config import settings


def test_jwt_token_generation_and_decoding():
    token = create_access_token(user_id="test-operator", role="operator", expires_delta_seconds=3600)
    assert token is not None
    assert len(token.split('.')) == 3

    payload = decode_access_token(token)
    assert payload["sub"] == "test-operator"
    assert payload["role"] == "operator"
    assert "exp" in payload
    assert "jti" in payload

def test_jwt_admin_role():
    token = create_access_token(user_id="admin-user", role="admin")
    payload = decode_access_token(token)
    assert payload["role"] == "admin"
    assert payload["sub"] == "admin-user"

def test_jwt_invalid_token():
    with pytest.raises(Exception):
        decode_access_token("invalid.token.signature")

def test_passwordless_login_rejected_at_schema():
    from pydantic import ValidationError
    from backend.models.schemas import LoginRequest
    with pytest.raises(ValidationError):
        LoginRequest(username="someone", role="operator")

def test_password_verification_requires_match():
    assert verify_password("operator", "dev-only-operator-passphrase-change-me") is True
    assert verify_password("operator", "wrong-password-xyz") is False
    assert verify_password("operator", "short") is False

def test_no_committed_default_secret():
    assert settings.JWT_SECRET != "locapredict-super-secret-key-production-change-me-2026"

def test_token_revocation_enforced():
    token = create_access_token(user_id="revoked-user", role="viewer", expires_delta_seconds=3600)
    assert revoke_token(token) is True
    with pytest.raises(HTTPException) as exc:
        decode_access_token(token)
    assert exc.value.status_code == 401

def test_login_rate_limit_trips():
    key = "ratelimit-test-user"
    for _ in range(10):
        check_login_rate_limit(key)
    with pytest.raises(HTTPException) as exc:
        check_login_rate_limit(key)
    assert exc.value.status_code == 429

def test_rbac_matrix_viewer_cannot_mutate():
    import asyncio
    from backend.auth.security import require_role
    checker = require_role(["admin", "operator"])
    with pytest.raises(HTTPException) as exc:
        asyncio.run(checker({"sub": "v", "role": "viewer"}))
    assert exc.value.status_code == 403
    # admin passes
    out = asyncio.run(checker({"sub": "a", "role": "admin"}))
    assert out["role"] == "admin"
