"""
FastAPI dependency injection helpers.

Usage in routes:
  - get_current_enterprise  → verifies token is an enterprise token
  - get_current_admin       → verifies token is an admin token
  - get_db                  → SQLAlchemy session (re-exported here for convenience)
"""

from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.core.security import decode_token, TOKEN_TYPE_ENTERPRISE, TOKEN_TYPE_ADMIN
from app.core.exceptions import NotLoginException, ForbiddenException
from app.core.database import get_db
from sqlalchemy.orm import Session

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_payload(
    credentials: HTTPAuthorizationCredentials | None,
    expected_type: str,
) -> dict[str, Any]:
    if credentials is None:
        raise NotLoginException()
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise NotLoginException("token 无效或已过期")

    if payload.get("token_type") != expected_type:
        raise ForbiddenException(f"该接口仅允许 {expected_type} 端访问")

    return payload


def get_current_enterprise(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    """Dependency: requires a valid enterprise-type JWT."""
    return _extract_payload(credentials, TOKEN_TYPE_ENTERPRISE)


def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    """Dependency: requires a valid admin-type JWT."""
    return _extract_payload(credentials, TOKEN_TYPE_ADMIN)


# Re-export for convenience
DbSession = Annotated[Session, Depends(get_db)]
CurrentEnterprise = Annotated[dict[str, Any], Depends(get_current_enterprise)]
CurrentAdmin = Annotated[dict[str, Any], Depends(get_current_admin)]
