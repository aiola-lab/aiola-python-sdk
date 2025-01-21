from typing import Optional, Callable
from pydantic import BaseModel, Field

class Callbacks(BaseModel):
    on_connect: Optional[Callable] = Field(default=None, description="Callback when connection is established")
    on_disconnect: Optional[Callable] = Field(default=None, description="Callback when connection is closed")
    on_transcript: Optional[Callable] = Field(default=None, description="Callback for transcript events")
    on_events: Optional[Callable] = Field(default=None, description="Callback for general events")
    on_error: Optional[Callable] = Field(default=None, description="Callback for error events")

    class Config:
        arbitrary_types_allowed = True 