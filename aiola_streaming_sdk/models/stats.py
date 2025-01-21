from typing import Optional
from pydantic import BaseModel

class StreamingStats(BaseModel):
    total_audio_sent_duration: float = 0.0
    connection_start_time: Optional[float] = None 