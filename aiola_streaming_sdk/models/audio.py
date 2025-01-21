from pydantic import BaseModel, Field

class AudioConfig(BaseModel):
    sample_rate: int = Field(default=16000, description="Sample rate in Hz")
    channels: int = Field(default=1, description="Number of audio channels")
    chunk_size: int = Field(default=4096, description="Size of each audio chunk")
    dtype: str = Field(default="int16", description="Data type for audio samples") 