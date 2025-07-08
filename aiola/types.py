from __future__ import annotations

from dataclasses import dataclass

from .constants import DEFAULT_AUTH_BASE_URL, DEFAULT_BASE_URL, DEFAULT_WORKFLOW_ID


@dataclass
class AiolaClientOptions:
    """Configuration options for Aiola clients."""

    base_url: str | None = DEFAULT_BASE_URL
    auth_base_url: str | None = DEFAULT_AUTH_BASE_URL
    api_key: str | None = None
    access_token: str | None = None
    workflow_id: str = DEFAULT_WORKFLOW_ID

    def __post_init__(self) -> None:
        """Validate options after initialization."""
        if not self.api_key and not self.access_token:
            raise ValueError("Either api_key or access_token must be provided")

        if self.api_key is not None and not isinstance(self.api_key, str):
            raise TypeError("API key must be a string")

        if self.access_token is not None and not isinstance(self.access_token, str):
            raise TypeError("Access token must be a string")

        if self.base_url is not None and not isinstance(self.base_url, str):
            raise TypeError("Base URL must be a string")

        if self.auth_base_url is not None and not isinstance(self.auth_base_url, str):
            raise TypeError("Auth base URL must be a string")

        if not isinstance(self.workflow_id, str):
            raise TypeError("Workflow ID must be a string")
