from __future__ import annotations

import base64
import json
import time
from typing import Any

import httpx

from ...constants import DEFAULT_HEADERS, DEFAULT_HTTP_TIMEOUT
from ...errors import AiolaError
from ...types import AiolaClientOptions, GrantTokenResponse, SessionCloseResponse


class BaseAuthClient:
    """Base class containing shared logic for authentication clients."""

    def __init__(self, options: AiolaClientOptions) -> None:
        self._options = options
        self._access_token: str | None = None
        self._session_id: str | None = None

    def _is_session_valid(self, access_token: str) -> bool:
        """Check if the access token is valid and not expired."""
        try:
            payload = self._parse_jwt_payload(access_token)
            exp = payload.get("exp")
            if exp is None:
                return False

            # Add 5 minute buffer before expiration
            buffer_time = 5 * 60  # 5 minutes in seconds
            current_time = int(time.time())
            return exp > (current_time + buffer_time)
        except Exception:
            return False

    def clear_session(self) -> None:
        """Clear cached session data."""
        self._access_token = None
        self._session_id = None

    def _parse_jwt_payload(self, token: str) -> dict[str, Any]:
        """Parse JWT payload from token."""
        try:
            # Split the token into parts
            parts = token.split(".")
            if len(parts) != 3:
                raise AiolaError(message="Invalid JWT format", code="INVALID_TOKEN")

            # Decode the payload (second part)
            payload_part = parts[1]

            # Add padding if needed for base64 decoding
            padding = len(payload_part) % 4
            if padding:
                payload_part += "=" * (4 - padding)

            # Decode from base64
            payload_bytes = base64.urlsafe_b64decode(payload_part)
            payload = json.loads(payload_bytes.decode("utf-8"))

            return payload
        except Exception as error:
            raise AiolaError(
                message=f"Failed to parse JWT payload: {str(error)}", code="JWT_PARSE_ERROR", details=error
            ) from error

    @staticmethod
    def grant_token(api_key: str, auth_base_url: str, workflow_id: str) -> GrantTokenResponse:
        """
        Static method to generate an access token from an API key without creating an Auth instance.
        This is the recommended way to generate tokens in backend services.
        """
        if not api_key:
            raise AiolaError(message="API key is required to generate access token", code="MISSING_API_KEY")

        try:
            # Determine endpoints based on base_url
            auth_base_url = auth_base_url.rstrip("/")
            token_endpoint = f"{auth_base_url}/voip-auth/apiKey2Token"
            session_endpoint = f"{auth_base_url}/voip-auth/session"
            headers = {
                **DEFAULT_HEADERS,
                "Authorization": f"Bearer {api_key}",
            }
            # Generate temporary token
            with httpx.Client(timeout=DEFAULT_HTTP_TIMEOUT) as client:
                token_response = client.post(
                    token_endpoint,
                    headers=headers,
                )

                if not token_response.is_success:
                    raise AiolaError(
                        message=f"Token generation failed: {token_response.status_code}",
                        status=token_response.status_code,
                    )

                token_data = token_response.json()
                if not token_data.get("context", {}).get("token"):
                    raise AiolaError(
                        message="Invalid token response - no token found in data.context.token",
                        code="INVALID_TOKEN_RESPONSE",
                    )

                # Create session
                session_body = {"workflow_id": workflow_id}

                session_response = client.post(
                    session_endpoint,
                    headers={
                        **DEFAULT_HEADERS,
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token_data['context']['token']}",
                    },
                    json=session_body,
                )

                if not session_response.is_success:
                    raise AiolaError(
                        message=f"Session creation failed: {session_response.status_code}",
                        status=session_response.status_code,
                    )

                session_data = session_response.json()
                if not session_data.get("jwt"):
                    raise AiolaError(message="Invalid session response - no jwt found", code="INVALID_SESSION_RESPONSE")

                return GrantTokenResponse(
                    access_token=session_data["jwt"], session_id=session_data.get("sessionId", "")
                )

        except AiolaError:
            raise
        except Exception as error:
            raise AiolaError(
                message=f"Token generation failed: {str(error)}", code="TOKEN_GENERATION_ERROR", details=error
            ) from error

    @staticmethod
    async def async_grant_token(api_key: str, auth_base_url: str, workflow_id: str) -> GrantTokenResponse:
        """
        Static async method to generate an access token from an API key without creating an Auth instance.
        This is the recommended way to generate tokens in backend services.
        """
        if not api_key:
            raise AiolaError(message="API key is required to generate access token", code="MISSING_API_KEY")

        try:
            # Determine endpoints based on base_url
            auth_base_url = auth_base_url.rstrip("/")
            token_endpoint = f"{auth_base_url}/voip-auth/apiKey2Token"
            session_endpoint = f"{auth_base_url}/voip-auth/session"

            # Generate temporary token
            async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT) as client:
                token_response = await client.post(
                    token_endpoint, headers={**DEFAULT_HEADERS, "Authorization": f"Bearer {api_key}"}
                )

                if not token_response.is_success:
                    raise AiolaError(
                        message=f"Token generation failed: {token_response.status_code}",
                        status=token_response.status_code,
                    )

                token_data = token_response.json()
                if not token_data.get("context", {}).get("token"):
                    raise AiolaError(
                        message="Invalid token response - no token found in data.context.token",
                        code="INVALID_TOKEN_RESPONSE",
                    )

                # Create session
                session_body = {"workflow_id": workflow_id}

                session_response = await client.post(
                    session_endpoint,
                    headers={
                        **DEFAULT_HEADERS,
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token_data['context']['token']}",
                    },
                    json=session_body,
                )

                if not session_response.is_success:
                    raise AiolaError(
                        message=f"Session creation failed: {session_response.status_code}",
                        status=session_response.status_code,
                    )

                session_data = session_response.json()
                if not session_data.get("jwt"):
                    raise AiolaError(message="Invalid session response - no jwt found", code="INVALID_SESSION_RESPONSE")

                return GrantTokenResponse(
                    access_token=session_data["jwt"], session_id=session_data.get("sessionId", "")
                )

        except AiolaError:
            raise
        except Exception as error:
            raise AiolaError(
                message=f"Token generation failed: {str(error)}", code="TOKEN_GENERATION_ERROR", details=error
            ) from error

    @staticmethod
    async def async_close_session(access_token: str, auth_base_url: str) -> SessionCloseResponse:
        """
        Static async method to close a session and free up concurrency slots.
        """
        if not access_token:
            raise AiolaError(message="Access token is required to close session", code="MISSING_ACCESS_TOKEN")

        try:
            auth_base_url = auth_base_url.rstrip("/")
            session_endpoint = f"{auth_base_url}/voip-auth/session"

            async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT) as client:
                response = await client.delete(
                    session_endpoint,
                    headers={
                        **DEFAULT_HEADERS,
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}",
                    },
                )

                if not response.is_success:
                    raise AiolaError(
                        message=f"Session close failed: {response.status_code}",
                        status=response.status_code,
                    )

                data = response.json()
                return SessionCloseResponse(status=data["status"], deleted_at=data["deletedAt"])

        except AiolaError:
            raise
        except Exception as error:
            raise AiolaError(
                message=f"Session close failed: {str(error)}", code="SESSION_CLOSE_ERROR", details=error
            ) from error


class AuthClient(BaseAuthClient):
    """Authentication client for managing API keys and access tokens."""

    def __init__(self, options: AiolaClientOptions) -> None:
        super().__init__(options)

    @staticmethod
    def grant_token(api_key: str, auth_base_url: str, workflow_id: str) -> GrantTokenResponse:
        """
        Instance method to generate an access token from an API key.
        Delegates to the static method with the current base_url.
        """
        return BaseAuthClient.grant_token(api_key=api_key, auth_base_url=auth_base_url, workflow_id=workflow_id)

    def get_access_token(self, access_token: str, api_key: str, workflow_id: str) -> str:
        """
        Get or create an access token based on provided credentials.
        Implements priority-based resolution: access_token > api_key
        """
        if access_token:
            if not self._is_session_valid(access_token):
                raise AiolaError(message="Provided access token is expired", code="TOKEN_EXPIRED")
            return access_token

        # Priority 2: API Key (requires token generation)
        if api_key:
            session = self._get_or_create_session(api_key, workflow_id)
            if session:
                self._access_token = session["access_token"]
                self._session_id = session["session_id"]
                return session["access_token"]

        raise AiolaError(
            message=(
                "No valid credentials provided. Please provide either api_key or access_token. "
                "You can generate an access_token using AuthClient.grant_token(api_key)."
            ),
            code="MISSING_CREDENTIALS",
        )

    def _api_key_to_token(self, api_key: str) -> str:
        """Generate a temporary JWT token from API key."""
        try:
            with httpx.Client(timeout=DEFAULT_HTTP_TIMEOUT) as client:
                response = client.post(
                    f"{self._options.auth_base_url}/voip-auth/apiKey2Token",
                    headers={**DEFAULT_HEADERS, "Authorization": f"Bearer {api_key}"},
                )

                if not response.is_success:
                    raise AiolaError(
                        message=f"Token generation failed: {response.status_code}", status=response.status_code
                    )

                data = response.json()
                if not data.get("context", {}).get("token"):
                    raise AiolaError(
                        message="Invalid token response - no token found in data.context.token",
                        code="INVALID_TOKEN_RESPONSE",
                    )

                return data["context"]["token"]

        except AiolaError:
            raise
        except Exception as error:
            raise AiolaError(
                message=f"Token generation failed: {str(error)}", code="TOKEN_GENERATION_ERROR", details=error
            ) from error

    def _create_session(self, token: str, workflow_id: str) -> dict[str, str]:
        """Create an access token (session JWT) using the temporary token."""
        try:
            body = {"workflow_id": workflow_id}
            headers = {**DEFAULT_HEADERS, "Content-Type": "application/json", "Authorization": f"Bearer {token}"}

            with httpx.Client(timeout=DEFAULT_HTTP_TIMEOUT) as client:
                response = client.post(
                    f"{self._options.auth_base_url}/voip-auth/session",
                    headers=headers,
                    json=body,
                )

                if not response.is_success:
                    raise AiolaError(
                        message=f"Session creation failed: {response.status_code}", status=response.status_code
                    )

                data = response.json()

                if not data.get("jwt"):
                    raise AiolaError(message="Invalid session response - no jwt found", code="INVALID_SESSION_RESPONSE")

                return {"access_token": data["jwt"], "session_id": data.get("sessionId", "")}

        except AiolaError:
            raise
        except Exception as error:
            raise AiolaError(
                message=f"Session creation failed: {str(error)}", code="SESSION_CREATION_ERROR", details=error
            ) from error

    def _get_or_create_session(self, api_key: str, workflow_id: str) -> dict[str, str] | None:
        """Get cached session or create new one."""
        # Check if cached session is still valid
        if self._access_token and self._is_session_valid(self._access_token):
            return {"access_token": self._access_token, "session_id": self._session_id or ""}

        # Create new session
        try:
            token = self._api_key_to_token(api_key)
            session = self._create_session(token, workflow_id)

            # Cache the session
            self._access_token = session["access_token"]
            self._session_id = session["session_id"]

            return session
        except Exception:
            # Clean up invalid cache entry
            self.clear_session()
            raise

    @staticmethod
    def close_session(access_token: str, auth_base_url: str) -> SessionCloseResponse:
        """
        Static method to close a session and free up concurrency slots.
        """
        if not access_token:
            raise AiolaError(message="Access token is required to close session", code="MISSING_ACCESS_TOKEN")

        try:
            auth_base_url = auth_base_url.rstrip("/")
            session_endpoint = f"{auth_base_url}/voip-auth/session"

            with httpx.Client(timeout=DEFAULT_HTTP_TIMEOUT) as client:
                response = client.delete(
                    session_endpoint,
                    headers={
                        **DEFAULT_HEADERS,
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}",
                    },
                )

                if not response.is_success:
                    raise AiolaError(
                        message=f"Session close failed: {response.status_code}",
                        status=response.status_code,
                    )

                data = response.json()
                return SessionCloseResponse(status=data["status"], deleted_at=data["deletedAt"])

        except AiolaError:
            raise
        except Exception as error:
            raise AiolaError(
                message=f"Session close failed: {str(error)}", code="SESSION_CLOSE_ERROR", details=error
            ) from error

    @staticmethod
    def is_token_valid(access_token: str) -> bool:
        """
        Static method to check if an access token is valid and not expired.
        """
        try:
            payload = AuthClient._parse_jwt_payload_static(access_token)
            exp = payload.get("exp")
            if exp is None:
                return False

            # Add 5 minute buffer before expiration
            buffer_time = 5 * 60  # 5 minutes in seconds
            current_time = int(time.time())
            return exp > (current_time + buffer_time)
        except Exception:
            return False

    @staticmethod
    def parse_jwt_payload(token: str) -> dict[str, Any]:
        """
        Static method to parse JWT payload from token.
        """
        return AuthClient._parse_jwt_payload_static(token)

    @staticmethod
    def _parse_jwt_payload_static(token: str) -> dict[str, Any]:
        """
        Static helper method to parse JWT payload from token.
        """
        try:
            # Split the token into parts
            parts = token.split(".")
            if len(parts) != 3:
                raise AiolaError(message="Invalid JWT format", code="INVALID_TOKEN")

            # Decode the payload (second part)
            payload_part = parts[1]

            # Add padding if needed for base64 decoding
            padding = len(payload_part) % 4
            if padding:
                payload_part += "=" * (4 - padding)

            # Decode from base64
            payload_bytes = base64.urlsafe_b64decode(payload_part)
            payload = json.loads(payload_bytes.decode("utf-8"))

            return payload
        except Exception as error:
            raise AiolaError(
                message=f"Failed to parse JWT token: {str(error)}", code="JWT_PARSE_ERROR", details=error
            ) from error

    def api_key_to_token(self, api_key: str) -> str:
        """
        Generate a temporary JWT token from API key.
        """
        return self._api_key_to_token(api_key)

    def create_session(self, token: str, workflow_id: str) -> dict[str, str]:
        """
        Create an access token (session JWT) using the temporary token.
        """
        return self._create_session(token, workflow_id)

    def is_session_valid(self, access_token: str) -> bool:
        """
        Check if the access token is valid and not expired.
        """
        return self._is_session_valid(access_token)


class AsyncAuthClient(BaseAuthClient):
    """Async authentication client for managing API keys and access tokens."""

    def __init__(self, options: AiolaClientOptions) -> None:
        super().__init__(options)

    @staticmethod
    async def grant_token(api_key: str, auth_base_url: str, workflow_id: str) -> GrantTokenResponse:
        """
        Instance method to generate an access token from an API key.
        Delegates to the static async method with the current base_url.
        """
        return await BaseAuthClient.async_grant_token(api_key, auth_base_url, workflow_id)

    async def get_access_token(self, access_token: str, api_key: str, workflow_id: str) -> str:
        """
        Get or create an access token based on provided credentials.
        Implements priority-based resolution: access_token > api_key
        """
        if access_token:
            if not self._is_session_valid(access_token):
                raise AiolaError(message="Provided access token is expired", code="TOKEN_EXPIRED")
            return access_token

        # Priority 2: API Key (requires token generation)
        if api_key:
            session = await self._get_or_create_session(api_key, workflow_id)
            if session:
                self._access_token = session["access_token"]
                self._session_id = session["session_id"]
                return session["access_token"]

        raise AiolaError(
            message=(
                "No valid credentials provided. Please provide either api_key or access_token. "
                "You can generate an access_token using AsyncAuthClient.async_grant_token(api_key)."
            ),
            code="MISSING_CREDENTIALS",
        )

    async def _api_key_to_token(self, api_key: str) -> str:
        """Generate a temporary JWT token from API key."""
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT) as client:
                response = await client.post(
                    f"{self._options.auth_base_url}/voip-auth/apiKey2Token",
                    headers={**DEFAULT_HEADERS, "Authorization": f"Bearer {api_key}"},
                )

                if not response.is_success:
                    raise AiolaError(
                        message=f"Token generation failed: {response.status_code}", status=response.status_code
                    )

                data = response.json()
                if not data.get("context", {}).get("token"):
                    raise AiolaError(
                        message="Invalid token response - no token found in data.context.token",
                        code="INVALID_TOKEN_RESPONSE",
                    )

                return data["context"]["token"]

        except AiolaError:
            raise
        except Exception as error:
            raise AiolaError(
                message=f"Token generation failed: {str(error)}", code="TOKEN_GENERATION_ERROR", details=error
            ) from error

    async def _create_session(self, token: str, workflow_id: str) -> dict[str, str]:
        """Create an access token (session JWT) using the temporary token."""
        try:
            body = {"workflow_id": workflow_id}

            async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT) as client:
                response = await client.post(
                    f"{self._options.auth_base_url}/voip-auth/session",
                    headers={**DEFAULT_HEADERS, "Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                    json=body,
                )

                if not response.is_success:
                    raise AiolaError(
                        message=f"Session creation failed: {response.status_code}", status=response.status_code
                    )

                data = response.json()

                if not data.get("jwt"):
                    raise AiolaError(message="Invalid session response - no jwt found", code="INVALID_SESSION_RESPONSE")

                return {"access_token": data["jwt"], "session_id": data.get("sessionId", "")}

        except AiolaError:
            raise
        except Exception as error:
            raise AiolaError(
                message=f"Session creation failed: {str(error)}", code="SESSION_CREATION_ERROR", details=error
            ) from error

    async def _get_or_create_session(self, api_key: str, workflow_id: str) -> dict[str, str] | None:
        """Get cached session or create new one."""
        # Check if cached session is still valid
        if self._access_token and self._is_session_valid(self._access_token):
            return {"access_token": self._access_token, "session_id": self._session_id or ""}

        # Create new session
        try:
            token = await self._api_key_to_token(api_key)
            session = await self._create_session(token, workflow_id)

            # Cache the session
            self._access_token = session["access_token"]
            self._session_id = session["session_id"]

            return session
        except Exception:
            # Clean up invalid cache entry
            self.clear_session()
            raise

    async def api_key_to_token(self, api_key: str) -> str:
        """
        Generate a temporary JWT token from API key.
        """
        return await self._api_key_to_token(api_key)

    async def create_session(self, token: str, workflow_id: str) -> dict[str, str]:
        """
        Create an access token (session JWT) using the temporary token.
        """
        return await self._create_session(token, workflow_id)

    def is_session_valid(self, access_token: str) -> bool:
        """
        Check if the access token is valid and not expired.
        """
        return self._is_session_valid(access_token)

    def parse_jwt_payload(self, token: str) -> dict[str, Any]:
        """
        Parse JWT payload from token.
        """
        return self._parse_jwt_payload(token)

    @staticmethod
    async def close_session(access_token: str, auth_base_url: str) -> SessionCloseResponse:
        """
        Static method to close a session and free up concurrency slots.
        """
        return await BaseAuthClient.async_close_session(access_token, auth_base_url)
