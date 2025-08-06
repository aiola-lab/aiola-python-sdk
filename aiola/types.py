from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import IO, Union

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
    SentimentAnalysis = "sentiment_analysis"
    Summarization = "summarization"
    TopicDetection = "topic_detection"
    ContentModeration = "content_moderation"
    AutoChapters = "auto_chapters"
    FormFilling = "form_filling"
    EntityDetection = "entity_detection"
    EntityDetectionFromList = "entity_detection_from_list"
    KeyPhrases = "key_phrases"
    PiiRedaction = "pii_redaction"
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

    file_duration: float
    language: str
    sample_rate: int
    num_channels: int
    timestamp_utc: str
    asr_model_version: str
    segments_count: int
    total_speech_duration: float


@dataclass
class TranscriptionResponse:
    """Response from file transcription API."""

    transcript: str
    raw_transcript: str
    segments: list[Segment]
    metadata: TranscriptionMetadata


@dataclass
class SessionCloseResponse:
    """Response from session close API."""

    status: str
    deletedAt: str


@dataclass
class GrantTokenResponse:
    """Response from grant token API."""

    accessToken: str
    sessionId: str


@dataclass
class TranslationPayload:
    src_lang_code: str
    dst_lang_code: str


@dataclass
class EntityDetectionFromListPayload:
    entity_list: list[str]


@dataclass
class _EmptyPayload:
    pass


EntityDetectionPayload = _EmptyPayload
KeyPhrasesPayload = _EmptyPayload
PiiRedactionPayload = _EmptyPayload
SentimentAnalysisPayload = _EmptyPayload
SummarizationPayload = _EmptyPayload
TopicDetectionPayload = _EmptyPayload
ContentModerationPayload = _EmptyPayload
AutoChaptersPayload = _EmptyPayload
FormFillingPayload = _EmptyPayload


@dataclass
class TasksConfig:
    FORM_FILLING: FormFillingPayload | None = None
    TRANSLATION: TranslationPayload | None = None
    ENTITY_DETECTION: EntityDetectionPayload | None = None
    ENTITY_DETECTION_FROM_LIST: EntityDetectionFromListPayload | None = None
    KEY_PHRASES: KeyPhrasesPayload | None = None
    PII_REDACTION: PiiRedactionPayload | None = None
    SENTIMENT_ANALYSIS: SentimentAnalysisPayload | None = None
    SUMMARIZATION: SummarizationPayload | None = None
    TOPIC_DETECTION: TopicDetectionPayload | None = None
    CONTENT_MODERATION: ContentModerationPayload | None = None
    AUTO_CHAPTERS: AutoChaptersPayload | None = None


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
