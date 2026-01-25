from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING

import httpx

from ...errors import AiolaAuthenticationError, AiolaConnectionError, AiolaError, AiolaServerError, AiolaValidationError
from ...http_client import create_async_authenticated_client, create_authenticated_client
from ...types import AiolaClientOptions, VoiceId

if TYPE_CHECKING:
    from ...clients.auth.client import AsyncAuthClient, AuthClient


class BaseTts:
    def __init__(self, options: AiolaClientOptions, auth: AuthClient | AsyncAuthClient) -> None:
        self._options = options
        self._auth = auth

    @staticmethod
    def _make_headers() -> dict[str, str]:
        return {"Accept": "audio/*"}

    def _validate_tts_params(self, text: str, voice_id: VoiceId | str) -> None:
        """Validate TTS parameters."""
        if not text or not isinstance(text, str):
            raise AiolaValidationError("text must be a non-empty string")
        # VoiceId enum inherits from str, so isinstance check works for both
        if not voice_id or not isinstance(voice_id, str):
            raise AiolaValidationError("voice_id must be a non-empty string")


class TtsClient(BaseTts):
    """Text-to-Speech (TTS) client for converting text to spoken audio.
    
    Provides methods for both streaming and complete synthesis of text to speech.
    Audio is returned as an iterator of bytes for efficient handling of large audio files.
    """

    def __init__(self, options: AiolaClientOptions, auth: AuthClient):
        super().__init__(options, auth)
        self._auth: AuthClient = auth  # Type narrowing

    def stream(self, *, text: str, voice_id: VoiceId | str) -> Iterator[bytes]:
        """Synthesize text to speech with streaming delivery.
        
        Returns audio as it's generated, providing lower latency than the synthesize
        method. Ideal for real-time applications where you want to start playing audio
        as soon as the first chunks are available.
        
        Args:
            text: The text to convert to speech. Can include punctuation and
                formatting which may affect prosody and pauses.
            voice_id: Voice identifier for synthesis. Supported voices:
                - 'en_us_female', 'en_us_male' - English (US)
                - 'es_female', 'es_male' - Spanish
                - 'fr_female', 'fr_male' - French
                - 'de_female', 'de_male' - German
                - 'ja_female', 'ja_male' - Japanese
                - 'pt_female', 'pt_male' - Portuguese
        
        Yields:
            bytes: Audio data chunks as they are generated.
        
        Raises:
            AiolaValidationError: If text or voice_id is invalid.
            AiolaAuthenticationError: If authentication fails (401).
            AiolaServerError: If server error occurs (500+).
            AiolaConnectionError: If network error occurs.
            AiolaError: For other synthesis errors.
        
        Examples:
            >>> # Stream synthesis for real-time playback
            >>> for chunk in client.tts.stream(
            ...     text='Hello, welcome to Aiola!',
            ...     voice_id='en-US-JennyNeural'
            ... ):
            ...     audio_player.play(chunk)
            
            >>> # Save streamed audio to file
            >>> with open('output.wav', 'wb') as f:
            ...     for chunk in client.tts.stream(
            ...         text='This is a test',
            ...         voice_id='en-GB-RyanNeural'
            ...     ):
            ...         f.write(chunk)
        """
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

    def synthesize(self, *, text: str, voice_id: VoiceId | str) -> Iterator[bytes]:
        """Synthesize text to speech with complete generation.
        
        Waits for the complete audio to be generated before starting to return data.
        Use this when you need the complete audio file, or when you want to ensure
        the entire synthesis is successful before proceeding.
        
        Args:
            text: The text to convert to speech.
            voice_id: Voice identifier for synthesis. Supported voices:
                - 'en_us_female', 'en_us_male' - English (US)
                - 'es_female', 'es_male' - Spanish
                - 'fr_female', 'fr_male' - French
                - 'de_female', 'de_male' - German
                - 'ja_female', 'ja_male' - Japanese
                - 'pt_female', 'pt_male' - Portuguese
        
        Yields:
            bytes: Audio data chunks.
        
        Raises:
            AiolaValidationError: If text or voice_id is invalid.
            AiolaAuthenticationError: If authentication fails.
            AiolaServerError: If server error occurs.
            AiolaConnectionError: If network error occurs.
            AiolaError: For other synthesis errors.
        
        Examples:
            >>> # Synthesize complete audio
            >>> chunks = []
            >>> for chunk in client.tts.synthesize(
            ...     text='This is a longer text that will be fully synthesized.',
            ...     voice_id='en-US-JennyNeural'
            ... ):
            ...     chunks.append(chunk)
            >>> audio_data = b''.join(chunks)
            
            >>> # Save to file
            >>> with open('output.wav', 'wb') as f:
            ...     for chunk in client.tts.synthesize(text='Hello', voice_id='en-US-JennyNeural'):
            ...         f.write(chunk)
        """
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
    """Asynchronous Text-to-Speech (TTS) client for converting text to audio.
    
    Provides async/await access to speech synthesis services. Use this client in
    async applications for better performance and concurrency.
    """

    def __init__(self, options: AiolaClientOptions, auth: AsyncAuthClient):
        super().__init__(options, auth)
        self._auth: AsyncAuthClient = auth  # Type narrowing

    async def stream(self, *, text: str, voice_id: VoiceId | str) -> AsyncIterator[bytes]:
        """Asynchronously synthesize text to speech with streaming delivery.
        
        Returns audio as it's generated using async iteration. Provides lower latency
        for real-time applications.
        
        Args:
            text: The text to convert to speech.
            voice_id: Voice identifier for synthesis. Supported voices:
                - 'en_us_female', 'en_us_male' - English (US)
                - 'es_female', 'es_male' - Spanish
                - 'fr_female', 'fr_male' - French
                - 'de_female', 'de_male' - German
                - 'ja_female', 'ja_male' - Japanese
                - 'pt_female', 'pt_male' - Portuguese
        
        Yields:
            bytes: Audio data chunks as they are generated.
        
        Raises:
            AiolaValidationError: If parameters are invalid.
            AiolaAuthenticationError: If authentication fails.
            AiolaServerError: If server error occurs.
            AiolaConnectionError: If network error occurs.
            AiolaError: For other synthesis errors.
        
        Examples:
            >>> # Async stream synthesis
            >>> async for chunk in await client.tts.stream(
            ...     text='Hello, world!',
            ...     voice_id='en-US-JennyNeural'
            ... ):
            ...     await audio_player.play(chunk)
            
            >>> # Save to file asynchronously
            >>> async with aiofiles.open('output.wav', 'wb') as f:
            ...     async for chunk in await client.tts.stream(
            ...         text='Test audio',
            ...         voice_id='en-GB-RyanNeural'
            ...     ):
            ...         await f.write(chunk)
        """
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

    async def synthesize(self, *, text: str, voice_id: VoiceId | str) -> AsyncIterator[bytes]:
        """Asynchronously synthesize text to speech with complete generation.
        
        Waits for complete audio generation before streaming using async iteration.
        
        Args:
            text: The text to convert to speech.
            voice_id: Voice identifier for synthesis. Supported voices:
                - 'en_us_female', 'en_us_male' - English (US)
                - 'es_female', 'es_male' - Spanish
                - 'fr_female', 'fr_male' - French
                - 'de_female', 'de_male' - German
                - 'ja_female', 'ja_male' - Japanese
                - 'pt_female', 'pt_male' - Portuguese
        
        Yields:
            bytes: Audio data chunks.
        
        Raises:
            AiolaValidationError: If parameters are invalid.
            AiolaAuthenticationError: If authentication fails.
            AiolaServerError: If server error occurs.
            AiolaConnectionError: If network error occurs.
            AiolaError: For other synthesis errors.
        
        Examples:
            >>> # Async synthesis
            >>> chunks = []
            >>> async for chunk in await client.tts.synthesize(
            ...     text='Complete synthesis example',
            ...     voice_id='en-US-JennyNeural'
            ... ):
            ...     chunks.append(chunk)
            >>> audio_data = b''.join(chunks)
        """
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
