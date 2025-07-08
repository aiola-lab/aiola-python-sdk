from __future__ import annotations

from typing import Any

import httpx


class AiolaError(Exception):
    """Base error raised by aiola-python SDK.

    All errors thrown by this SDK inherit from :class:`AiolaError` so that callers
    can rely on a single error type for predictable error handling.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        code: str | None = None,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message  # Keep an explicit attribute – ``Exception`` drops it under ``__str__``
        self.status: int | None = status
        self.code: str | None = code
        self.details: Any | None = details

    @classmethod
    def from_response(cls, response: httpx.Response) -> AiolaError:
        """Build an :class:`AiolaError` from an *unsuccessful* ``httpx.Response``.

        The method reads the body trying to extract a JSON payload in the shape::

            {"error": {"message": "...", "code": "...", "details": {...}}}

        and falls back to plain text otherwise.
        """

        message: str = f"Request failed with status {response.status_code}"
        code: str | None = None
        details: Any | None = None

        try:
            payload = response.json()
            if isinstance(payload, dict):
                err_payload = payload.get("error", payload)
                if isinstance(err_payload, dict):
                    message = err_payload.get("message", message)
                    code = err_payload.get("code")
                    details = err_payload.get("details", err_payload)
        except ValueError:
            # Not JSON – try plain text
            text = response.text
            if text:
                message = text

        return cls(message, status=response.status_code, code=code, details=details)

    def __str__(self) -> str:
        return self.message


class AiolaConnectionError(AiolaError):
    """Raised when there are connectivity issues with the Aiola API."""

    pass


class AiolaAuthenticationError(AiolaError):
    """Raised when authentication fails (invalid API key, expired token, etc.)."""

    pass


class AiolaValidationError(AiolaError):
    """Raised when input validation fails (invalid parameters, missing required fields, etc.)."""

    pass


class AiolaStreamingError(AiolaError):
    """Raised when streaming operations fail (WebSocket connection issues, etc.)."""

    pass


class AiolaFileError(AiolaError):
    """Raised when file operations fail (invalid file format, file too large, etc.)."""

    pass


class AiolaRateLimitError(AiolaError):
    """Raised when API rate limits are exceeded."""

    pass


class AiolaServerError(AiolaError):
    """Raised when the Aiola API returns a server error (5xx status codes)."""

    pass
