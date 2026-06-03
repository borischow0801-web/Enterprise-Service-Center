"""
Unified Identity Auth Adapter
==============================
Extension point for integrating a real unified identity platform
(e.g. provincial e-government SSO, enterprise WeChat Work, etc.).

To enable real auth:
1. Implement a subclass of BaseAuthAdapter.
2. Swap the adapter in get_auth_adapter().
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAuthAdapter(ABC):
    """Abstract interface for identity provider integration."""

    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> dict[str, Any]:
        """
        Validate credentials against the identity provider.
        Returns a normalized user info dict on success.
        Raises ThirdPartyAuthException on failure.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Fetch user info from the identity provider using its own token."""
        raise NotImplementedError


class MockAuthAdapter(BaseAuthAdapter):
    """Pass-through adapter used in development / mock mode."""

    async def authenticate(self, credentials: dict[str, Any]) -> dict[str, Any]:
        # In mock mode, trust whatever the caller provides
        return credentials

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        return {}


def get_auth_adapter() -> BaseAuthAdapter:
    """
    Factory. Swap MockAuthAdapter for a real implementation when ready.
    Could also read APP_AUTH_ADAPTER env var to select adapter dynamically.
    """
    return MockAuthAdapter()
