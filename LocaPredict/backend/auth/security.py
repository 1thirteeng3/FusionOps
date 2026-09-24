import hmac
import hashlib
import base64
import json
import time
import os
import secrets
import threading
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.core.config import settings
from backend.utils.logger import logger

security_bearer = HTTPBearer(auto_error=False)

# Demo User Roles
ROLES = {
    "admin": {"name": "Administrador AIOps", "role": "admin", "permissions": ["all"]},
    "operator": {"name": "Operador NOC / ITSM", "role": "operator", "permissions": ["triage", "assign", "escalate", "notify"]},
    "viewer": {"name": "Visualizador / Auditor", "role": "viewer", "permissions": ["read_only"]}
}

# --- Credential verification (T009/T036, Constitution VII, Gate 6) ---
# Role passphrases come from env (vault in production). Dev-only fallbacks exist
# solely outside production and are refused when ENV=production.
def _role_password(role: str) -> str:
    env_name = f"LOCAPREDICT_{role.upper()}_PASSWORD"
    secret = os.getenv(env_name, "")
    if secret:
        return secret
    if settings.ENV == "production":
        raise RuntimeError(f"{env_name} is required in production. Startup refused.")
    return f"dev-only-{role}-passphrase-change-me"


def verify_password(role: str, password: str) -> bool:
    """Constant-time passphrase verification for a role (T009)."""
    if not password or len(password) < 8:
        return False
    expected = _role_password(role)
    return hmac.compare_digest(expected.encode("utf-8"), password.encode("utf-8"))


# --- Token revocation (T009/T036) ---
_revoked_jti: set = set()
_revoke_lock = threading.Lock()


def revoke_token(token: str) -> bool:
    """Revoke a token by its jti claim. Returns True if revoked."""
    try:
        payload = json.loads(
            _base64url_decode(token.split(".")[1]).decode("utf-8"))
        jti = payload.get("jti")
        if not jti:
            return False
        with _revoke_lock:
            _revoked_jti.add(jti)
        return True
    except Exception:
        return False


def is_revoked(jti: Optional[str]) -> bool:
    if not jti:
        return False
    with _revoke_lock:
        return jti in _revoked_jti


# --- Login rate limiting (T009/T036) ---
_login_attempts: Dict[str, List[float]] = {}
_rate_lock = threading.Lock()
_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW_S = 60.0


def check_login_rate_limit(key: str) -> None:
    """Sliding-window rate limit hook; raises 429 when exceeded (T009)."""
    now = time.time()
    with _rate_lock:
        attempts = [t for t in _login_attempts.get(key, []) if now - t < _RATE_LIMIT_WINDOW_S]
        if len(attempts) >= _RATE_LIMIT_MAX:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas de login. Aguarde 60 segundos.")
        attempts.append(now)
        _login_attempts[key] = attempts


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(user_id: str, role: str, expires_delta_seconds: Optional[int] = None) -> str:
    """Creates a signed JWT token using HMAC-SHA256"""
    header = {"alg": "HS256", "typ": "JWT"}
    exp = int(time.time()) + (expires_delta_seconds or (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60))
    payload = {
        "sub": user_id,
        "role": role,
        "name": ROLES.get(role, {}).get("name", user_id),
        "exp": exp,
        "iat": int(time.time()),
        "jti": secrets.token_hex(16),
    }

    header_encoded = _base64url_encode(json.dumps(header).encode('utf-8'))
    payload_encoded = _base64url_encode(json.dumps(payload).encode('utf-8'))

    signature_input = f"{header_encoded}.{payload_encoded}".encode('utf-8')
    signature = hmac.new(settings.JWT_SECRET.encode('utf-8'), signature_input, hashlib.sha256).digest()
    signature_encoded = _base64url_encode(signature)

    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token (signature, expiry, revocation)"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Formato de token JWT inválido")

        header_encoded, payload_encoded, signature_encoded = parts
        signature_input = f"{header_encoded}.{payload_encoded}".encode('utf-8')
        expected_sig = hmac.new(settings.JWT_SECRET.encode('utf-8'), signature_input, hashlib.sha256).digest()
        actual_sig = _base64url_decode(signature_encoded)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Assinatura do token inválida")

        payload = json.loads(_base64url_decode(payload_encoded).decode('utf-8'))

        # Check expiration
        if payload.get("exp") and payload["exp"] < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")

        # Check revocation (T009)
        if is_revoked(payload.get("jti")):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revogado")

        return payload
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.warning(f"Token decoding error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de autenticação inválido ou expirado")

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> Dict[str, Any]:
    """Extracts and verifies the current authenticated user.

    Constitution VII (T009): no anonymous fallback. Missing credentials yield
    401 in every environment, including localhost development.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação exigida: forneça um Bearer token JWT.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    return decode_access_token(token)

def require_role(allowed_roles: List[str]):
    """Role-Based Access Control dependency factory"""
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role", "viewer")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado: Perfil '{user_role}' não possui permissão para esta operação. Requer: {allowed_roles}"
            )
        return user
    return role_checker
