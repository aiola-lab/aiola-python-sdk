from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

import httpx

from .constants import DEFAULT_BASE_URL, DEFAULT_HEADERS
from .errors import AiolaError

if TYPE_CHECKING:
    from .clients.auth.client import AsyncAuthClient, AuthClient
    from .types import AiolaClientOptions


def _merge_headers(base: Mapping[str, str], extra: Mapping[str, str] | None = None) -> dict[str, str]:
    try:
        merged: dict[str, str] = dict(base)
        if extra:
            merged.update(extra)
        return merged
    except Exception as exc:
        raise AiolaError("Failed to merge headers") from exc


def create_authenticated_client(options: AiolaClientOptions, auth: AuthClient) -> httpx.Client:
    """Create an authenticated httpx.Client with proper headers."""
    try:
        # Get access token
        access_token = auth.get_access_token(options.access_token or "", options.api_key or "", options.workflow_id)

        # Prepare headers
        headers = _merge_headers(DEFAULT_HEADERS, {"Authorization": f"Bearer {access_token}"})

        # Create client with base URL and headers
        full_base_url = (options.base_url or DEFAULT_BASE_URL).rstrip("/")
        timeout = options.timeout

        return httpx.Client(base_url=full_base_url, headers=headers, timeout=timeout)
    except Exception as exc:
        raise AiolaError("Failed to create authenticated HTTP client") from exc


async def create_async_authenticated_client(options: AiolaClientOptions, auth: AsyncAuthClient) -> httpx.AsyncClient:
    """Create an authenticated httpx.AsyncClient with proper headers."""
    try:
        # Get access token
        access_token = await auth.get_access_token(
            options.access_token or "", options.api_key or "", options.workflow_id
        )

        # Prepare headers
        headers = _merge_headers(DEFAULT_HEADERS, {"Authorization": f"Bearer {access_token}"})

        # Create client with base URL and headers
        full_base_url = (options.base_url or DEFAULT_BASE_URL).rstrip("/")
        timeout = options.timeout

        return httpx.AsyncClient(base_url=full_base_url, headers=headers, timeout=timeout)
    except Exception as exc:
        raise AiolaError("Failed to create authenticated async HTTP client") from exc
