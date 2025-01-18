from typing import Optional, Callable, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl

class AudioConfig(BaseModel):
    sample_rate: int = Field(default=16000, description="Sample rate in Hz")
    channels: int = Field(default=1, description="Number of audio channels")
    chunk_size: int = Field(default=4096, description="Size of each audio chunk")
    dtype: str = Field(default="int16", description="Data type for audio samples")

class Callbacks(BaseModel):
    on_connect: Optional[Callable] = Field(default=None, description="Callback when connection is established")
    on_disconnect: Optional[Callable] = Field(default=None, description="Callback when connection is closed")
    on_transcript: Optional[Callable] = Field(default=None, description="Callback for transcript events")
    on_events: Optional[Callable] = Field(default=None, description="Callback for general events")
    on_error: Optional[Callable] = Field(default=None, description="Callback for error events")

    class Config:
        arbitrary_types_allowed = True

class StreamingConfig(BaseModel):
    endpoint: HttpUrl
    auth_type: str = Field(..., description="Authentication type: 'Cookie', 'Bearer', or 'x-api-key'")
    auth_credentials: Dict[str, Any] = Field(..., description="Authentication credentials")
    
    # Stream parameters
    flow_id: str = Field(default="default_flow")
    execution_id: str = Field(default="1")
    lang_code: str = Field(default="en_US")
    time_zone: str = Field(default="UTC")
    namespace: str = Field(default="/events")
    transports: List[str] = Field(default=['polling'])
    
    # Nested configurations
    audio: AudioConfig = Field(default_factory=AudioConfig)
    callbacks: Callbacks = Field(default_factory=Callbacks)

    class Config:
        arbitrary_types_allowed = True 