import enum
from collections.abc import Mapping
from typing import IO, TypedDict, Union


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
