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
    """STT client."""

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
        """Create a streaming connection for real-time transcription.

        Args:
            workflow_id: Workflow ID to use for this stream. If not provided, uses the client's
                        workflow_id from initialization, or falls back to the default workflow.
            execution_id: Unique execution ID. If not provided, a UUID will be generated.
            lang_code: Language code for transcription (default: "en").
            time_zone: Time zone for timestamps (default: "UTC").
            keywords: Optional keywords dictionary for enhanced transcription.
            tasks_config: Optional configuration for additional AI tasks.

        Returns:
            StreamConnection: A connection object for real-time streaming.
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
        """Transcribe an audio file and return the transcription result."""

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
    """Asynchronous STT client."""

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
        """Create an async streaming connection for real-time transcription.

        Args:
            workflow_id: Workflow ID to use for this stream. If not provided, uses the client's
                        workflow_id from initialization, or falls back to the default workflow.
            execution_id: Unique execution ID. If not provided, a UUID will be generated.
            lang_code: Language code for transcription (default: "en").
            time_zone: Time zone for timestamps (default: "UTC").
            keywords: Optional keywords dictionary for enhanced transcription.
            tasks_config: Optional configuration for additional AI tasks.

        Returns:
            AsyncStreamConnection: A connection object for real-time async streaming.
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
        """Transcribe an audio file and return the transcription result."""

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
