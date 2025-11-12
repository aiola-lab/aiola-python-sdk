from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING

import httpx

from ...errors import AiolaAuthenticationError, AiolaConnectionError, AiolaError, AiolaServerError, AiolaValidationError
from ...http_client import create_async_authenticated_client, create_authenticated_client
from ...types import AiolaClientOptions

if TYPE_CHECKING:
    from ...clients.auth.client import AsyncAuthClient, AuthClient


class BaseTts:
    def __init__(self, options: AiolaClientOptions, auth: AuthClient | AsyncAuthClient) -> None:
        self._options = options
        self._auth = auth

    @staticmethod
    def _make_headers() -> dict[str, str]:
        return {"Accept": "audio/*"}

    def _validate_tts_params(self, text: str, voice_id: str) -> None:
        """Validate TTS parameters."""
        if not text or not isinstance(text, str):
            raise AiolaValidationError("text must be a non-empty string")
        if not voice_id or not isinstance(voice_id, str):
            raise AiolaValidationError("voice_id must be a non-empty string")


class TtsClient(BaseTts):
    """TTS client."""

    def __init__(self, options: AiolaClientOptions, auth: AuthClient):
        super().__init__(options, auth)
        self._auth: AuthClient = auth  # Type narrowing

    def stream(self, *, text: str, voice_id: str) -> Iterator[bytes]:
        """Stream synthesized audio in real-time."""
        self._validate_tts_params(text, voice_id)

        try:
            # Create authenticated HTTP client and make the streaming request
            with (
                create_authenticated_client(self._options, self._auth) as client,
                client.stream(
                    "POST",
                    "/api/tts/stream",
                    json={
                        "text": text,
                        "voice_id": voice_id,
                    },
                    headers=self._make_headers(),
                ) as response,
            ):
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError:
                    response.read()
                    raise

                yield from response.iter_bytes()

        except AiolaError:
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise AiolaAuthenticationError.from_response(exc.response) from exc
            elif exc.response.status_code >= 500:
                raise AiolaServerError.from_response(exc.response) from exc
            else:
                raise AiolaError.from_response(exc.response) from exc
        except httpx.RequestError as exc:
            raise AiolaConnectionError(f"Network error during TTS streaming: {str(exc)}") from exc
        except Exception as exc:
            raise AiolaError(f"TTS streaming failed: {str(exc)}") from exc

    def synthesize(self, *, text: str, voice_id: str) -> Iterator[bytes]:
        """Synthesize audio and return as iterator of bytes."""
        self._validate_tts_params(text, voice_id)

        try:
            # Create authenticated HTTP client and make the streaming request
            with (
                create_authenticated_client(self._options, self._auth) as client,
                client.stream(
                    "POST",
                    "/api/tts/synthesize",
                    json={
                        "text": text,
                        "voice_id": voice_id,
                    },
                    headers=self._make_headers(),
                ) as response,
            ):
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError:
                    response.read()
                    raise

                yield from response.iter_bytes()

        except AiolaError:
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise AiolaAuthenticationError.from_response(exc.response) from exc
            elif exc.response.status_code >= 500:
                raise AiolaServerError.from_response(exc.response) from exc
            else:
                raise AiolaError.from_response(exc.response) from exc
        except httpx.RequestError as exc:
            raise AiolaConnectionError(f"Network error during TTS synthesis: {str(exc)}") from exc
        except Exception as exc:
            raise AiolaError(f"TTS synthesis failed: {str(exc)}") from exc


class AsyncTtsClient(BaseTts):
    """Asynchronous TTS client."""

    def __init__(self, options: AiolaClientOptions, auth: AsyncAuthClient):
        super().__init__(options, auth)
        self._auth: AsyncAuthClient = auth  # Type narrowing

    async def stream(self, *, text: str, voice_id: str) -> AsyncIterator[bytes]:
        """Stream synthesized audio in real-time (async)."""
        self._validate_tts_params(text, voice_id)

        try:
            # Create authenticated HTTP client and make the streaming request
            client = await create_async_authenticated_client(self._options, self._auth)
            async with (
                client as http_client,
                http_client.stream(
                    "POST",
                    "/api/tts/stream",
                    json={
                        "text": text,
                        "voice_id": voice_id,
                    },
                    headers=self._make_headers(),
                ) as response,
            ):
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError:
                    await response.aread()
                    raise

                async for chunk in response.aiter_bytes():
                    yield chunk

        except AiolaError:
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise AiolaAuthenticationError.from_response(exc.response) from exc
            elif exc.response.status_code >= 500:
                raise AiolaServerError.from_response(exc.response) from exc
            else:
                raise AiolaError.from_response(exc.response) from exc
        except httpx.RequestError as exc:
            raise AiolaConnectionError(f"Network error during async TTS streaming: {str(exc)}") from exc
        except Exception as exc:
            raise AiolaError(f"Async TTS streaming failed: {str(exc)}") from exc

    async def synthesize(self, *, text: str, voice_id: str) -> AsyncIterator[bytes]:
        """Synthesize audio and return as async iterator of bytes."""
        self._validate_tts_params(text, voice_id)

        try:
            # Create authenticated HTTP client and make the streaming request
            client = await create_async_authenticated_client(self._options, self._auth)
            async with (
                client as http_client,
                http_client.stream(
                    "POST",
                    "/api/tts/synthesize",
                    json={
                        "text": text,
                        "voice_id": voice_id,
                    },
                    headers=self._make_headers(),
                ) as response,
            ):
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError:
                    await response.aread()
                    raise

                async for chunk in response.aiter_bytes():
                    yield chunk

        except AiolaError:
            raise
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise AiolaAuthenticationError.from_response(exc.response) from exc
            elif exc.response.status_code >= 500:
                raise AiolaServerError.from_response(exc.response) from exc
            else:
                raise AiolaError.from_response(exc.response) from exc
        except httpx.RequestError as exc:
            raise AiolaConnectionError(f"Network error during async TTS synthesis: {str(exc)}") from exc
        except Exception as exc:
            raise AiolaError(f"Async TTS synthesis failed: {str(exc)}") from exc
