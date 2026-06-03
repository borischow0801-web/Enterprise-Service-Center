"""
JWT utilities. Two token types are issued:
  - "enterprise": for the H5 enterprise portal  (/api/enterprise/*)
  - "admin":      for the PC management backend (/api/admin/*)

The `token_type` claim is embedded in the payload so that route
dependencies can reject tokens issued for the wrong audience.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

TOKEN_TYPE_ENTERPRISE = "enterprise"
TOKEN_TYPE_ADMIN = "admin"


def _create_token(payload: dict[str, Any], expire_minutes: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    data = {**payload, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(data, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def create_enterprise_token(enterprise_data: dict[str, Any]) -> str:
    payload = {"token_type": TOKEN_TYPE_ENTERPRISE, "sub_type": "enterprise", **enterprise_data}
    return _create_token(payload, settings.jwt_enterprise_expire_minutes)


def create_admin_token(admin_data: dict[str, Any]) -> str:
    payload = {"token_type": TOKEN_TYPE_ADMIN, "sub_type": "admin", **admin_data}
    return _create_token(payload, settings.jwt_admin_expire_minutes)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify token. Raises JWTError on failure."""
    return jwt.decode(token, settings.app_secret_key, algorithms=[settings.jwt_algorithm])
