from typing import Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from typing import List
from .audio import AudioConfig
from .callbacks import Callbacks

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
    transports: str = Field(default="polling")

    use_buildin_mic: bool=Field(default=False)
    
    # Nested configurations
    audio: AudioConfig = Field(default_factory=AudioConfig)
    callbacks: Callbacks = Field(default_factory=Callbacks)

    class Config:
        arbitrary_types_allowed = True 