from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import IO, TypedDict, Union

from .constants import DEFAULT_AUTH_BASE_URL, DEFAULT_BASE_URL, DEFAULT_WORKFLOW_ID


@dataclass
class AiolaClientOptions:
    """Configuration options for Aiola clients."""

    base_url: str | None = DEFAULT_BASE_URL
    auth_base_url: str | None = DEFAULT_AUTH_BASE_URL
    api_key: str | None = None
    access_token: str | None = None
    workflow_id: str = DEFAULT_WORKFLOW_ID

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


class Segment(TypedDict):
    start: float
    end: float
    text: str


class TranscriptionMetadata(TypedDict):
    """Metadata for transcription results."""

    duration: float
    language: str
    sample_rate: int
    num_channels: int
    timestamp_utc: str
    model_version: str


class TranscriptionResponse(TypedDict):
    """Response from file transcription API."""

    transcript: str
    itn_transcript: str
    segments: list[Segment]
    metadata: TranscriptionMetadata


class SessionCloseResponse(TypedDict):
    """Response from session close API."""

    status: str
    deletedAt: str


class GrantTokenResponse(TypedDict):
    """Response from grant token API."""

    accessToken: str
    sessionId: str


class TranslationPayload(TypedDict):
    src_lang_code: str
    dst_lang_code: str


class EntityDetectionFromListPayload(TypedDict):
    entity_list: list[str]


class _EmptyPayload(TypedDict):
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


class TasksConfig(TypedDict, total=False):
    FORM_FILLING: FormFillingPayload
    TRANSLATION: TranslationPayload
    ENTITY_DETECTION: EntityDetectionPayload
    ENTITY_DETECTION_FROM_LIST: EntityDetectionFromListPayload
    KEY_PHRASES: KeyPhrasesPayload
    PII_REDACTION: PiiRedactionPayload
    SENTIMENT_ANALYSIS: SentimentAnalysisPayload
    SUMMARIZATION: SummarizationPayload
    TOPIC_DETECTION: TopicDetectionPayload
    CONTENT_MODERATION: ContentModerationPayload
    AUTO_CHAPTERS: AutoChaptersPayload


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
