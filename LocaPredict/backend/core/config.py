import os
import logging
from typing import List
from pydantic import BaseModel

logger = logging.getLogger("locapredict.config")

_DEV_FALLBACK_SECRET = "locapredict-DEV-ONLY-secret-do-not-use-in-production"

def _resolve_jwt_secret() -> str:
    """Fail-closed JWT secret resolution (Constitution VII, Gate 6).

    Production (ENV=production) without JWT_SECRET raises at import time.
    Non-production without JWT_SECRET uses an explicit dev-only fallback and
    logs a warning. No committed secret is ever trusted in production.
    """
    env = os.getenv("ENV", "development").lower()
    secret = os.getenv("JWT_SECRET", "")
    if secret:
        return secret
    if env == "production":
        raise RuntimeError(
            "JWT_SECRET is required in production (ENV=production). "
            "Provide it via vault or environment; startup refused."
        )
    if os.getenv("LOCAPREDICT_ALLOW_DEV_SECRET", "1") != "1":
        raise RuntimeError(
            "JWT_SECRET is not set and dev fallback is disabled "
            "(LOCAPREDICT_ALLOW_DEV_SECRET!=1). Startup refused."
        )
    logger.warning("Using dev-only JWT fallback secret; never use in production.")
    return _DEV_FALLBACK_SECRET


_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


def _parse_origins() -> List[str]:
    """CORS whitelist: defaults plus comma-separated ALLOWED_ORIGINS env (F4).

    Wildcards are refused when credentials are used (fail-closed).
    """
    extra = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
    origins = list(_DEFAULT_ORIGINS)
    for origin in extra:
        if "*" in origin:
            raise RuntimeError(
                f"Wildcard origin refused with credentials support: {origin!r}. "
                "List explicit origins instead.")
        if origin not in origins:
            origins.append(origin)
    return origins

class Settings(BaseModel):
    PROJECT_NAME: str = "LocaPredict SLA Guard v3 — FusionOps Intelligence Platform"
    VERSION: str = "3.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Security & CORS
    JWT_SECRET: str = _resolve_jwt_secret()
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ENV: str = os.getenv("ENV", "development").lower()
    
    # Whitelist specific trusted origins (Strict CORS - No wildcard with credentials).
    # Single-service deploys are same-origin (no CORS triggered); extra public
    # origins (e.g. the *.onrender.com URL) come via ALLOWED_ORIGINS env (F4).
    ALLOWED_ORIGINS: List[str] = _parse_origins()
    
    # Persistence & ML Seed
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///locapredict.db")
    RANDOM_SEED: int = 42

settings = Settings()
