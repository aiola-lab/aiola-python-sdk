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
from ...types import AiolaClientOptions, File, TasksConfig, TranscriptionResponse
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

    def _build_query_and_headers(
        self,
        workflow_id: str | None,
        execution_id: str | None,
        lang_code: str | None,
        time_zone: str | None,
        keywords: dict[str, str] | None,
        tasks_config: TasksConfig | None,
        access_token: str,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Build query parameters and headers for streaming requests."""
        execution_id = execution_id or str(uuid.uuid4())

        query = {
            "execution_id": execution_id,
            "flow_id": workflow_id or DEFAULT_WORKFLOW_ID,
            "lang_code": lang_code or "en",
            "time_zone": time_zone or "UTC",
            "keywords": json.dumps(keywords or {}),
            "tasks_config": json.dumps(tasks_config or {}),
            "x-aiola-api-token": access_token,
        }

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
        if tasks_config is not None and not isinstance(tasks_config, dict):
            raise AiolaValidationError("tasks_config must be a dictionary")


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
    ) -> StreamConnection:
        """Create a streaming connection for real-time transcription."""
        try:
            self._validate_stream_params(workflow_id, execution_id, lang_code, time_zone, keywords, tasks_config)

            # Get access token for streaming connection
            access_token = self._auth.get_access_token(
                access_token=self._options.access_token or "",
                api_key=self._options.api_key or "",
                workflow_id=self._options.workflow_id,
            )

            # Build query parameters and headers
            query, headers = self._build_query_and_headers(
                workflow_id, execution_id, lang_code, time_zone, keywords, tasks_config, access_token
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
    ) -> TranscriptionResponse:
        """Transcribe an audio file and return the transcription result."""

        if file is None:
            raise AiolaFileError("File parameter is required")

        if language is not None and not isinstance(language, str):
            raise AiolaValidationError("language must be a string")

        if keywords is not None and not isinstance(keywords, dict):
            raise AiolaValidationError("keywords must be a dictionary")

        try:
            # Prepare the form data
            files = {"file": file}
            data = {
                "language": language or "en",
                "keywords": json.dumps(keywords or {}),
            }

            # Create authenticated HTTP client and make request
            with create_authenticated_client(self._options, self._auth) as client:
                response = client.post(
                    "/api/speech-to-text/file",
                    files=files,
                    data=data,
                )
                return response.json()

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
    ) -> AsyncStreamConnection:
        """Create an async streaming connection for real-time transcription."""
        try:
            self._validate_stream_params(workflow_id, execution_id, lang_code, time_zone, keywords, tasks_config)
            # Get access token for streaming connection
            access_token = await self._auth.get_access_token(
                self._options.access_token or "",
                self._options.api_key or "",
                self._options.workflow_id,
            )

            # Build query parameters and headers
            query, headers = self._build_query_and_headers(
                workflow_id, execution_id, lang_code, time_zone, keywords, tasks_config, access_token
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
    ) -> TranscriptionResponse:
        """Transcribe an audio file and return the transcription result."""

        if file is None:
            raise AiolaFileError("File parameter is required")

        if language is not None and not isinstance(language, str):
            raise AiolaValidationError("language must be a string")

        if keywords is not None and not isinstance(keywords, dict):
            raise AiolaValidationError("keywords must be a dictionary")

        try:
            # Prepare the form data
            files = {"file": file}
            data = {
                "language": language or "en",
                "keywords": json.dumps(keywords or {}),
            }

            # Create authenticated HTTP client and make request
            client = await create_async_authenticated_client(self._options, self._auth)
            async with client as http_client:
                response = await http_client.post(
                    "/api/speech-to-text/file",
                    files=files,
                    data=data,
                )
                return response.json()

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
