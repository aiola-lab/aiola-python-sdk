from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import IO, Any, Union

from .constants import DEFAULT_AUTH_BASE_URL, DEFAULT_BASE_URL, DEFAULT_HTTP_TIMEOUT, DEFAULT_WORKFLOW_ID


@dataclass
class AiolaClientOptions:
    """Configuration options for Aiola clients.
    
    Contains all configuration parameters needed to initialize and configure
    an Aiola client. Either api_key or access_token must be provided.
    
    Attributes:
        base_url: API base URL. Defaults to production Aiola API endpoint.
        auth_base_url: Authentication service base URL. Defaults to production
            authentication endpoint.
        api_key: Your Aiola API key. Used for automatic token management. Either
            this or access_token must be provided.
        access_token: Pre-generated access token from grant_token(). Either this
            or api_key must be provided.
        workflow_id: Workflow ID defining the AI processing pipeline. Defaults
            to the standard workflow.
        timeout: HTTP request timeout in seconds. Defaults to 30 seconds.
    """

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
    """Events that can be received during live audio streaming.
    
    These events provide real-time feedback and results from the streaming
    transcription service.
    
    Attributes:
        Transcript: Real-time transcription results emitted for each detected
            speech segment.
        Translation: Translation results (only if TRANSLATION task is enabled).
        Structured: Structured data extraction results (only if FORM_FILLING
            task is enabled).
        Error: Error events indicating issues during streaming.
        Disconnect: Connection closed event.
        Connect: Connection established event.
    """
    Transcript = "transcript"
    Translation = "translation"
    Structured = "structured"
    Error = "error"
    Disconnect = "disconnect"
    Connect = "connect"


class VoiceId(str, enum.Enum):
    """Supported voice identifiers for text-to-speech synthesis.
    
    Use these enum values for type safety and autocomplete when specifying voices.
    
    Attributes:
        EnglishUSFemale: English (US) - Female voice ('en_us_female')
        EnglishUSMale: English (US) - Male voice ('en_us_male')
        SpanishFemale: Spanish - Female voice ('es_female')
        SpanishMale: Spanish - Male voice ('es_male')
        FrenchFemale: French - Female voice ('fr_female')
        FrenchMale: French - Male voice ('fr_male')
        GermanFemale: German - Female voice ('de_female')
        GermanMale: German - Male voice ('de_male')
        JapaneseFemale: Japanese - Female voice ('ja_female')
        JapaneseMale: Japanese - Male voice ('ja_male')
        PortugueseFemale: Portuguese - Female voice ('pt_female')
        PortugueseMale: Portuguese - Male voice ('pt_male')
    
    Examples:
        >>> from aiola import AiolaClient, VoiceId
        >>> client = AiolaClient(access_token='your-token')
        >>> audio = client.tts.synthesize(
        ...     text='Hello, world!',
        ...     voice_id=VoiceId.EnglishUSFemale
        ... )
    """
    EnglishUSFemale = "en_us_female"
    EnglishUSMale = "en_us_male"
    SpanishFemale = "es_female"
    SpanishMale = "es_male"
    FrenchFemale = "fr_female"
    FrenchMale = "fr_male"
    GermanFemale = "de_female"
    GermanMale = "de_male"
    JapaneseFemale = "ja_female"
    JapaneseMale = "ja_male"
    PortugueseFemale = "pt_female"
    PortugueseMale = "pt_male"


@dataclass
class Segment:
    """Time segment representing a portion of audio.
    
    Indicates where speech was detected in the audio file.
    
    Attributes:
        start: Start time of the segment in seconds.
        end: End time of the segment in seconds.
    """
    start: float
    end: float


@dataclass
class TranscriptionMetadata:
    """Metadata about the transcribed audio file and transcription process.
    
    Contains information about the audio file characteristics and transcription results.
    
    Attributes:
        file_duration: Total duration of the audio file in seconds.
        language: Detected or specified language code (e.g., 'en', 'es', 'fr').
        sample_rate: Sample rate of the audio file in Hz (e.g., 16000, 44100).
        num_channels: Number of audio channels (1 for mono, 2 for stereo).
        timestamp_utc: ISO 8601 timestamp when transcription was processed.
        segments_count: Number of speech segments detected in the audio.
        total_speech_duration: Total duration of detected speech in seconds
            (excludes silence).
    """

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
    """Response from the file transcription API.
    
    Contains the complete transcription results including processed text,
    time segments, and metadata.
    
    Attributes:
        transcript: The complete transcription text with formatting and punctuation.
            This is the processed, production-ready transcript.
        raw_transcript: The raw transcription text without post-processing.
            Useful for debugging or custom post-processing pipelines.
        segments: List of time segments indicating where speech was detected.
            Useful for creating captions or navigating through the audio.
        metadata: Metadata about the transcription and source audio file.
    """

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
    """Response from structured data extraction API.
    
    Attributes:
        results: Dictionary containing extracted structured data. The structure
            depends on the form/schema configuration used.
    """

    results: dict[str, Any]


@dataclass
class SessionCloseResponse:
    """Response from the session close API.
    
    Attributes:
        status: Status of the session closure operation.
        deleted_at: ISO 8601 timestamp when the session was deleted.
    """

    status: str
    deleted_at: str


@dataclass
class GrantTokenResponse:
    """Response from the access token generation API.
    
    Attributes:
        access_token: JWT access token for API authentication. This token has
            an expiration time and should be validated before use.
        session_id: Unique session identifier. Can be used to track and close
            sessions.
    """

    access_token: str
    session_id: str


@dataclass
class TranslationPayload:
    """Configuration for translation task.
    
    Attributes:
        src_lang_code: Source language code (e.g., 'en', 'es', 'fr').
        dst_lang_code: Destination language code (e.g., 'es', 'fr', 'de').
    """
    src_lang_code: str
    dst_lang_code: str


@dataclass
class TasksConfig:
    """Configuration for AI tasks to run during transcription.
    
    Specify which AI-powered analysis tasks should be applied to the audio.
    Each task can have its own configuration payload.
    
    Attributes:
        TRANSLATION: Optional translation configuration. If provided, translates
            transcribed text from source to destination language.
    
    Examples:
        >>> config = TasksConfig(
        ...     TRANSLATION=TranslationPayload(
        ...         src_lang_code='en',
        ...         dst_lang_code='es'
        ...     )
        ... )
    """
    TRANSLATION: TranslationPayload | None = None


@dataclass
class VadConfig:
    """Voice Activity Detection (VAD) configuration.
    
    Controls how the system detects speech and silence in audio streams,
    affecting when transcription events are emitted and how audio is segmented.
    
    Attributes:
        threshold: Probability threshold for speech detection (0.0 to 1.0).
            Higher values make detection more conservative (less likely to
            detect speech). Default is typically around 0.5.
        min_speech_ms: Minimum duration of speech in milliseconds to trigger
            detection. Speech shorter than this will be ignored, reducing
            false positives. Default is typically 250ms.
        min_silence_ms: Minimum duration of silence in milliseconds to split
            speech segments. Pauses shorter than this won't split the segment.
            Default is typically 500ms.
        max_segment_ms: Maximum duration of a speech segment in milliseconds.
            Prevents extremely long segments. Default is typically 30000ms
            (30 seconds).
    
    Examples:
        >>> # More conservative detection with longer segments
        >>> vad = VadConfig(
        ...     threshold=0.6,
        ...     min_speech_ms=300,
        ...     min_silence_ms=700,
        ...     max_segment_ms=15000
        ... )
    """
    threshold: float | None = None
    min_speech_ms: float | None = None
    min_silence_ms: float | None = None
    max_segment_ms: float | None = None


"""Type alias for file content that can be uploaded."""
FileContent = Union[IO[bytes], bytes, str]

"""Type alias for file input supporting various formats.

Supports:
- FileContent: Direct file object, bytes, or file path string
- (filename, FileContent): Tuple with optional filename and content
- (filename, FileContent, content_type): Tuple with filename, content, and MIME type
- (filename, FileContent, content_type, headers): Complete tuple with all metadata

Examples:
    >>> # File path (string)
    >>> file = 'audio.wav'
    
    >>> # File object
    >>> file = open('audio.wav', 'rb')
    
    >>> # Bytes
    >>> file = audio_bytes
    
    >>> # With filename
    >>> file = ('myfile.wav', audio_bytes)
    
    >>> # With content type
    >>> file = ('myfile.wav', audio_bytes, 'audio/wav')
"""
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
