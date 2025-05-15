"""
Configuration classes for the aiOla streaming service.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal, TypedDict, Callable
from zoneinfo import available_timezones
from pydantic import field_validator, BaseModel

from .errors import AiolaError


SupportedLang = Literal["en_US", "es_ES", "fr_FR", "de_DE", "pt_PT", "ja_JP", "it_IT", "zh_CN"]
@dataclass
class MicConfig:
    """Configuration for the microphone input.
    ```bash 
    EXPERIMENTAL - Don't touch if you are not sure
    
    Attributes:
        sample_rate (Optional[int]): The audio sample rate in Hz. Defaults to 16000.
        chunk_size (Optional[int]): The number of frames per buffer. Max to 4096.
        channels (Optional[int]): The number of audio channels. Defaults to 1 (mono).
    ```
    """
    sample_rate: Optional[int] = 16000
    chunk_size: Optional[int] = 4096
    channels: Optional[int] = 1

@dataclass
class VadConfig:
    """Configuration for voice activity detection.
    ```bash 
    EXPERIMENTAL - Don't touch if you are not sure
    
    Attributes:
        vad_threshold (Optional[float]): Voice activity detection threshold between 0 and 1. Defaults to 0.5.
        min_silence_duration_ms (Optional[int]): Minimum duration of silence in milliseconds before stopping recording. Defaults to 250.
    ```
    """
    vad_threshold: Optional[float] = 0.5
    min_silence_duration_ms: Optional[int] = 250

class AiolaEvents(TypedDict, total=False):
    """Callback for the aiOla streaming service functionalities."""
    on_transcript: Callable[[Dict], None]
    on_events: Callable[[Dict], None]
    on_connect: Callable[[Literal["polling", "websocket"]], None]
    on_disconnect: Callable[[], None]
    on_start_record: Callable[[], None]
    on_stop_record: Callable[[], None]
    on_keyword_set: Callable[[List[str]], None]
    on_error: Callable[[AiolaError], None]

class AiolaQueryParams(BaseModel):
    """Query parameters for the aiOla streaming service.
    Attributes:
        ```bash 
        execution_id (str): Required unique identifier for the session/context, 4 to 24 characters long and contains only letters and numbers
        flow_id (str, optional): Identifier for a specific flow. Defaults to "C5f2da54-6150-47f7-9f36-e7b5dc384859".
        lang_code (SupportedLang, optional): Language code for speech recognition. Must be one of: "en", "es", "fr", "de", "pt", "ja", "it", "zh". Defaults to "en".
        time_zone (str, optional): IANA timezone identifier (e.g., "UTC", "America/New_York"). Must be a valid IANA timezone. Defaults to "UTC".
        ```
    """
    execution_id: str
    flow_id: Optional[str] = "C5f2da54-6150-47f7-9f36-e7b5dc384859" #Default flow id for playground - ASR only with no LLM tasks
    lang_code: Optional[SupportedLang] = "en_US"
    time_zone: Optional[str] = "UTC"

    @field_validator("time_zone")
    @classmethod
    def check_iana_timezone(cls, value: Optional[str]) -> Optional[str]:
        """Validates that the timezone is a valid IANA timezone."""
        if value is not None and value not in available_timezones():
            raise ValueError(f"Invalid AiolaSttQueryParams:time_zone, Invalid IANA time zone: {value}")
        return value
    
    @field_validator("execution_id")
    @classmethod
    def check_execution_id(cls, value: str) -> str:
        """Validates that the execution_id is 24 characters long and contains only letters and numbers."""
        if not (4 <= len(value) <= 24 and value.isalnum()):
            raise ValueError("Invalid AiolaSttQueryParams:execution_id, must be 4 to 24 characters long and contain only letters and numbers.")
        return value

@dataclass
class AiolaConfig:
    """Configuration for the aiOla streaming service.
    ```bash 
    Args:
        api_key (str): Authentication key for the aiOla service
        query_params (AiolaSttQueryParams): Query parameters for the API request
        base_url (str, optional): Base URL for the API. Defaults to 'api.aiola.ai'
        mic_config (MicConfig, optional): Microphone configuration settings. Defaults to MicConfig()
        vad_config (VadConfig, optional): Voice activity detection settings. Defaults to VadConfig()
        events (AiolaEvents, optional): Callback functions for various events. Defaults to None
        transports (Literal["polling", "websocket", "all"]): Transport method for communication. Defaults to "all"
    """
    api_key: str
    query_params: AiolaQueryParams
    base_url: Optional[str] = 'https://api.aiola.ai'
    mic_config: Optional[MicConfig] = field(default_factory=MicConfig)
    vad_config: Optional[VadConfig] = field(default_factory=VadConfig)
    events: Optional[AiolaEvents] = field(default_factory=dict)
    transports: Literal["polling", "websocket", "all"] = "all" 