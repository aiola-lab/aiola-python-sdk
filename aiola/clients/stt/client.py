from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx

from ...constants import DEFAULT_WORKFLOW_ID
from ...errors import (
    AiolaAuthenticationError,
    AiolaConnectionError,
    AiolaError,
    AiolaFileError,
    AiolaServerError,
    AiolaValidationError,
)
from ...http_client import create_async_authenticated_client, create_authenticated_client
from ...types import AiolaClientOptions, File, TasksConfig, TranscriptionResponse, VadConfig
from .stream_client import AsyncStreamConnection, StreamConnection

if TYPE_CHECKING:
    from ...clients.auth.client import AsyncAuthClient, AuthClient


class _BaseStt:
    def __init__(self, options: AiolaClientOptions, auth: AuthClient | AsyncAuthClient) -> None:
        self._options = options
        self._auth = auth
        self._path = "/api/voice-streaming/socket.io"
        self._namespace = "/events"

    def _build_url(self, query_params: dict[str, str]) -> str:
        """Return base URL with encoded query parameters."""
        try:
            return f"{self._options.base_url}?{urlencode(query_params)}"
        except Exception as exc:
            raise AiolaError("Failed to build streaming URL") from exc

    def _resolve_workflow_id(self, workflow_id: str | None) -> str:
        """Resolve workflow_id with proper precedence: method param > client options > default."""
        if workflow_id is not None:
            return workflow_id
        if self._options.workflow_id:
            return self._options.workflow_id
        return DEFAULT_WORKFLOW_ID

    def _build_query_and_headers(
        self,
        workflow_id: str | None,
        execution_id: str | None,
        lang_code: str | None,
        time_zone: str | None,
        keywords: dict[str, str] | None,
        tasks_config: TasksConfig | None,
        vad_config: VadConfig | None,
        access_token: str,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Build query parameters and headers for streaming requests."""
        execution_id = execution_id or str(uuid.uuid4())
        resolved_workflow_id = self._resolve_workflow_id(workflow_id)

        query = {
            "execution_id": execution_id,
            "flow_id": resolved_workflow_id,
            "time_zone": time_zone or "UTC",
            "x-aiola-api-token": access_token,
        }

        if lang_code is not None:
            query["lang_code"] = lang_code
        if keywords is not None:
            query["keywords"] = json.dumps(keywords)
        if tasks_config is not None:
            query["tasks_config"] = json.dumps(tasks_config)
        if vad_config is not None:
            query["vad_config"] = json.dumps(vad_config)

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        return query, headers

    def _validate_stream_params(
        self,
        flow_id: str | None,
        execution_id: str | None,
        lang_code: str | None,
        time_zone: str | None,
        keywords: dict[str, str] | None,
        tasks_config: TasksConfig | None,
        vad_config: VadConfig | None,
    ) -> None:
        """Validate streaming parameters."""
        if flow_id is not None and not isinstance(flow_id, str):
            raise AiolaValidationError("flow_id must be a string")
        if execution_id is not None and not isinstance(execution_id, str):
            raise AiolaValidationError("execution_id must be a string")
        if lang_code is not None and not isinstance(lang_code, str):
            raise AiolaValidationError("lang_code must be a string")
        if time_zone is not None and not isinstance(time_zone, str):
            raise AiolaValidationError("time_zone must be a string")
        if keywords is not None and not isinstance(keywords, dict):
            raise AiolaValidationError("keywords must be a dictionary")
        if tasks_config is not None and not isinstance(tasks_config, dict | TasksConfig):
            raise AiolaValidationError("tasks_config must be a dictionary or a TasksConfig object")
        if vad_config is not None and not isinstance(vad_config, dict | VadConfig):
            raise AiolaValidationError("vad_config must be a dictionary or a VadConfig object")


class SttClient(_BaseStt):
    """Speech-to-Text (STT) client for audio transcription services.
    
    Provides both file-based transcription and real-time streaming capabilities.
    Supports multiple audio formats and various AI-powered tasks.
    """

    def __init__(self, options: AiolaClientOptions, auth: AuthClient) -> None:
        super().__init__(options, auth)
        self._auth: AuthClient = auth  # Type narrowing

    def stream(
        self,
        workflow_id: str | None = None,
        execution_id: str | None = None,
        lang_code: str | None = None,
        time_zone: str | None = None,
        keywords: dict[str, str] | None = None,
        tasks_config: TasksConfig | None = None,
        vad_config: VadConfig | None = None,
    ) -> StreamConnection:
        """Create a real-time streaming connection for audio transcription.
        
        Returns a connection object that can be used to send audio data and receive
        transcription events in real-time. Audio should be sent as 16-bit PCM at
        16kHz sample rate, mono channel.

        Args:
            workflow_id: Optional workflow ID. If not provided, uses the client's
                workflow_id from initialization, or falls back to the default workflow.
                Workflows define the AI processing pipeline.
            execution_id: Optional execution ID for tracking this session. If not
                provided, a UUID will be automatically generated. Useful for
                correlating logs and events.
            lang_code: Optional language code for transcription (e.g., 'en', 'es', 'fr').
                If not specified, the service will attempt to auto-detect.
            time_zone: Optional timezone for timestamps in events. Defaults to 'UTC'.
                Use IANA timezone format (e.g., 'America/New_York', 'Europe/London').
            keywords: Optional dictionary mapping spoken phrases to written forms
                for boosting recognition accuracy. Format: {'spoken': 'written'}.
            tasks_config: Optional AI tasks configuration. Specify which AI-powered
                analysis tasks should run (e.g., translation, sentiment analysis).
            vad_config: Optional Voice Activity Detection configuration. Controls
                how speech segments are detected and when events are emitted.

        Returns:
            StreamConnection: A connection object for real-time streaming.
        
        Raises:
            AiolaValidationError: If parameters are invalid.
            AiolaError: If connection creation fails.
        
        Examples:
            >>> # Basic streaming
            >>> stream = client.stt.stream(lang_code='en')
            >>> stream.on('transcript', lambda data: print(data['transcript']))
            >>> stream.connect()
            >>> stream.send(audio_data)
            
            >>> # With keywords and VAD config
            >>> stream = client.stt.stream(
            ...     lang_code='en',
            ...     keywords={'aiola': 'Aiola', 'AI': 'AI'},
            ...     vad_config={'min_speech_ms': 300, 'min_silence_ms': 700}
            ... )
        """
        try:
            self._validate_stream_params(
                workflow_id, execution_id, lang_code, time_zone, keywords, tasks_config, vad_config
            )

            # Resolve workflow_id with proper precedence
            resolved_workflow_id = self._resolve_workflow_id(workflow_id)

            # Get access token for streaming connection using resolved workflow_id
            access_token = self._auth.get_access_token(
                access_token=self._options.access_token or "",
                api_key=self._options.api_key or "",
                workflow_id=resolved_workflow_id,
            )

            # Build query parameters and headers
            query, headers = self._build_query_and_headers(
                workflow_id, execution_id, lang_code, time_zone, keywords, tasks_config, vad_config, access_token
            )

            url = self._build_url(query)

            return StreamConnection(
                options=self._options, url=url, headers=headers, socketio_path=self._path, namespace=self._namespace
            )
        except (AiolaError, AiolaValidationError):
            raise
        except Exception as exc:
            raise AiolaError("Failed to create streaming connection") from exc

    def transcribe_file(
        self,
        file: File,
        *,
        language: str | None = None,
        keywords: dict[str, str] | None = None,
        vad_config: VadConfig | None = None,
    ) -> TranscriptionResponse:
        """Transcribe an audio file to text.
        
        Uploads and processes an audio file on the server, returning the complete
        transcription once processing is finished. Supports multiple audio formats
        including WAV, MP3, M4A, OGG, and FLAC.

        Args:
            file: Audio file to transcribe. Can be a file path (str), file object,
                or bytes. Supported formats: WAV, MP3, M4A, OGG, FLAC.
            language: Optional language code (e.g., 'en', 'es', 'fr'). If not
                specified, the service will attempt to auto-detect the language.
            keywords: Optional dictionary mapping spoken phrases to written forms
                for boosting recognition accuracy. Format: {'spoken': 'written'}.
            vad_config: Optional Voice Activity Detection configuration. Controls
                how speech segments are detected in the audio.

        Returns:
            TranscriptionResponse: Complete transcription result including:
                - transcript: The processed transcription text
                - raw_transcript: Unprocessed transcription
                - segments: Time segments where speech was detected
                - metadata: File metadata and transcription information

        Raises:
            AiolaFileError: If file parameter is missing or invalid.
            AiolaValidationError: If parameters are invalid.
            AiolaAuthenticationError: If authentication fails (401).
            AiolaServerError: If server error occurs (500+).
            AiolaConnectionError: If network error occurs.
            AiolaError: For other transcription errors.

        Examples:
            >>> # Transcribe from file path
            >>> result = client.stt.transcribe_file('audio.wav', language='en')
            >>> print(result.transcript)
            
            >>> # Transcribe with keywords
            >>> result = client.stt.transcribe_file(
            ...     'audio.wav',
            ...     language='en',
            ...     keywords={'aiola': 'Aiola', 'API': 'API'}
            ... )
            
            >>> # Transcribe with VAD config
            >>> result = client.stt.transcribe_file(
            ...     'audio.wav',
            ...     vad_config={'min_speech_ms': 300, 'threshold': 0.6}
            ... )
        """

        if file is None:
            raise AiolaFileError("File parameter is required")

        if language is not None and not isinstance(language, str):
            raise AiolaValidationError("language must be a string")

        if keywords is not None and not isinstance(keywords, dict):
            raise AiolaValidationError("keywords must be a dictionary")

        if vad_config is not None and not isinstance(vad_config, dict | VadConfig):
            raise AiolaValidationError("vad_config must be a dictionary or a VadConfig object")

        try:
            # Prepare the form data
            files = {"file": file}
            data = {
                "language": language or "en",
                "keywords": json.dumps(keywords or {}),
                "vad_config": json.dumps(vad_config or {}),
            }

            # Create authenticated HTTP client and make request
            with create_authenticated_client(self._options, self._auth) as client:
                response = client.post(
                    "/api/speech-to-text/file",
                    files=files,
                    data=data,
                )
                return TranscriptionResponse.from_dict(response.json())

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
            raise AiolaConnectionError(f"Network error during transcription: {str(exc)}") from exc
        except (ValueError, TypeError) as exc:
            raise AiolaError(f"Invalid response format from transcription service: {str(exc)}") from exc
        except Exception as exc:
            raise AiolaError(f"Transcription failed: {str(exc)}") from exc


class AsyncSttClient(_BaseStt):
    """Asynchronous Speech-to-Text (STT) client for audio transcription.
    
    Provides async/await access to file-based transcription and real-time streaming.
    Use this client in async applications for better performance and concurrency.
    """

    def __init__(self, options: AiolaClientOptions, auth: AsyncAuthClient) -> None:
        super().__init__(options, auth)
        self._auth: AsyncAuthClient = auth  # Type narrowing

    async def stream(
        self,
        workflow_id: str | None = None,
        execution_id: str | None = None,
        lang_code: str | None = None,
        time_zone: str | None = None,
        keywords: dict[str, str] | None = None,
        tasks_config: TasksConfig | None = None,
        vad_config: VadConfig | None = None,
    ) -> AsyncStreamConnection:
        """Create a real-time async streaming connection for audio transcription.
        
        Returns a connection object that can be used to send audio data and receive
        transcription events in real-time using async/await. Audio should be sent as
        16-bit PCM at 16kHz sample rate, mono channel.

        Args:
            workflow_id: Optional workflow ID. If not provided, uses the client's
                workflow_id from initialization, or falls back to the default workflow.
            execution_id: Optional execution ID for tracking. Auto-generated if not provided.
            lang_code: Optional language code (e.g., 'en', 'es', 'fr').
            time_zone: Optional timezone for timestamps (default: 'UTC').
            keywords: Optional keywords dictionary for boosting recognition.
            tasks_config: Optional AI tasks configuration.
            vad_config: Optional Voice Activity Detection configuration.

        Returns:
            AsyncStreamConnection: An async connection object for real-time streaming.

        Raises:
            AiolaValidationError: If parameters are invalid.
            AiolaError: If connection creation fails.

        Examples:
            >>> # Basic async streaming
            >>> stream = await client.stt.stream(lang_code='en')
            >>> stream.on('transcript', lambda data: print(data['transcript']))
            >>> await stream.connect()
            >>> await stream.send(audio_data)
            
            >>> # With AI tasks
            >>> stream = await client.stt.stream(
            ...     lang_code='en',
            ...     tasks_config={'TRANSLATION': {'src_lang_code': 'en', 'dst_lang_code': 'es'}}
            ... )
        """
        try:
            self._validate_stream_params(
                workflow_id, execution_id, lang_code, time_zone, keywords, tasks_config, vad_config
            )

            # Resolve workflow_id with proper precedence
            resolved_workflow_id = self._resolve_workflow_id(workflow_id)

            # Get access token for streaming connection using resolved workflow_id
            access_token = await self._auth.get_access_token(
                self._options.access_token or "",
                self._options.api_key or "",
                resolved_workflow_id,
            )

            # Build query parameters and headers
            query, headers = self._build_query_and_headers(
                workflow_id, execution_id, lang_code, time_zone, keywords, tasks_config, vad_config, access_token
            )

            url = self._build_url(query)

            return AsyncStreamConnection(
                options=self._options, url=url, headers=headers, socketio_path=self._path, namespace=self._namespace
            )
        except (AiolaError, AiolaValidationError):
            raise
        except Exception as exc:
            raise AiolaError("Failed to create async streaming connection") from exc

    async def transcribe_file(
        self,
        file: File,
        *,
        language: str | None = None,
        keywords: dict[str, str] | None = None,
        vad_config: VadConfig | None = None,
    ) -> TranscriptionResponse:
        """Asynchronously transcribe an audio file to text.
        
        Uploads and processes an audio file on the server, returning the complete
        transcription once processing is finished. Supports multiple audio formats.

        Args:
            file: Audio file to transcribe. Can be a file path, file object, or bytes.
                Supported formats: WAV, MP3, M4A, OGG, FLAC.
            language: Optional language code (e.g., 'en', 'es', 'fr').
            keywords: Optional keywords dictionary for boosting recognition.
            vad_config: Optional Voice Activity Detection configuration.

        Returns:
            TranscriptionResponse: Complete transcription result with text, segments,
                and metadata.

        Raises:
            AiolaFileError: If file parameter is missing or invalid.
            AiolaValidationError: If parameters are invalid.
            AiolaAuthenticationError: If authentication fails.
            AiolaServerError: If server error occurs.
            AiolaConnectionError: If network error occurs.
            AiolaError: For other transcription errors.

        Examples:
            >>> # Async transcription
            >>> result = await client.stt.transcribe_file('audio.wav', language='en')
            >>> print(result.transcript)
            
            >>> # With keywords
            >>> result = await client.stt.transcribe_file(
            ...     'audio.wav',
            ...     language='en',
            ...     keywords={'company': 'CompanyName'}
            ... )
        """

        if file is None:
            raise AiolaFileError("File parameter is required")

        if language is not None and not isinstance(language, str):
            raise AiolaValidationError("language must be a string")

        if keywords is not None and not isinstance(keywords, dict):
            raise AiolaValidationError("keywords must be a dictionary")

        if vad_config is not None and not isinstance(vad_config, dict | VadConfig):
            raise AiolaValidationError("vad_config must be a dictionary or a VadConfig object")

        try:
            # Prepare the form data
            files = {"file": file}
            data = {
                "language": language or "en",
                "keywords": json.dumps(keywords or {}),
                "vad_config": json.dumps(vad_config or {}),
            }

            # Create authenticated HTTP client and make request
            client = await create_async_authenticated_client(self._options, self._auth)
            async with client as http_client:
                response = await http_client.post(
                    "/api/speech-to-text/file",
                    files=files,
                    data=data,
                )
                return TranscriptionResponse.from_dict(response.json())

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
            raise AiolaConnectionError(f"Network error during async transcription: {str(exc)}") from exc
        except (ValueError, TypeError) as exc:
            raise AiolaError(f"Invalid response format from transcription service: {str(exc)}") from exc
        except Exception as exc:
            raise AiolaError(f"Async transcription failed: {str(exc)}") from exc
