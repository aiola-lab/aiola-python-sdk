from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import IO, Any, Union

from .constants import DEFAULT_AUTH_BASE_URL, DEFAULT_BASE_URL, DEFAULT_HTTP_TIMEOUT, DEFAULT_WORKFLOW_ID


@dataclass
class AiolaClientOptions:
    """Configuration options for Aiola clients."""

    base_url: str | None = DEFAULT_BASE_URL
    auth_base_url: str | None = DEFAULT_AUTH_BASE_URL
    api_key: str | None = None
    access_token: str | None = None
    workflow_id: str = DEFAULT_WORKFLOW_ID
    timeout: float | None = DEFAULT_HTTP_TIMEOUT

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

        if self.timeout is not None and not isinstance(self.timeout, (int | float)):
            raise TypeError("Timeout must be a number")


class LiveEvents(str, enum.Enum):
    Transcript = "transcript"
    Translation = "translation"
    Structured = "structured"
    Error = "error"
    Disconnect = "disconnect"
    Connect = "connect"


@dataclass
class Segment:
    start: float
    end: float


@dataclass
class TranscriptionMetadata:
    """Metadata for transcription results."""

    file_duration: float | None = None
    language: str | None = None
    sample_rate: int | None = None
    num_channels: int | None = None
    timestamp_utc: str | None = None
    segments_count: int | None = None
    total_speech_duration: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> TranscriptionMetadata:
        """Create TranscriptionMetadata from dict, filtering unknown fields."""
        from dataclasses import fields

        known_fields = {field.name for field in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)


@dataclass
class TranscriptionResponse:
    """Response from file transcription API."""

    transcript: str
    raw_transcript: str
    segments: list[Segment]
    metadata: TranscriptionMetadata

    @classmethod
    def from_dict(cls, data: dict) -> TranscriptionResponse:
        """Create TranscriptionResponse from dict, properly handling segments and metadata."""
        segments_data = data.get("segments", [])
        segments = [Segment(start=seg["start"], end=seg["end"]) for seg in segments_data]

        metadata_data = data.get("metadata", {})
        metadata = TranscriptionMetadata.from_dict(metadata_data)

        return cls(
            transcript=data["transcript"],
            raw_transcript=data["raw_transcript"],
            segments=segments,
            metadata=metadata,
        )


@dataclass
class StructuredResponse:
    """Response from structured API."""

    results: dict[str, Any]


@dataclass
class SessionCloseResponse:
    """Response from session close API."""

    status: str
    deleted_at: str


@dataclass
class GrantTokenResponse:
    """Response from grant token API."""

    access_token: str
    session_id: str


@dataclass
class TranslationPayload:
    src_lang_code: str
    dst_lang_code: str


@dataclass
class TasksConfig:
    TRANSLATION: TranslationPayload | None = None


@dataclass
class VadConfig:
    threshold: float | None = None
    min_speech_ms: float | None = None
    min_silence_ms: float | None = None
    max_segment_ms: float | None = None


FileContent = Union[IO[bytes], bytes, str]
File = Union[
    # file (or bytes)
    FileContent,
    # (filename, file (or bytes))
    tuple[str | None, FileContent],
    # (filename, file (or bytes), content_type)
    tuple[str | None, FileContent, str | None],
    # (filename, file (or bytes), content_type, headers)
    tuple[
        str | None,
        FileContent,
        str | None,
        Mapping[str, str],
    ],
]
