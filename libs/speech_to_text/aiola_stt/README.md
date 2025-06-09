# aiOla Speech-to-Text SDK

Python SDK for aiOla's Speech-to-Text API.

## Features

- Real-time audio streaming
- File transcription
- Keyword spotting
- Voice Activity Detection (VAD)

## Installation

```bash
pip install aiola-stt
```

## Usage
<!--snippet;quickstart-->
```python
from aiola_stt import AiolaSttClient, AiolaConfig, AiolaQueryParams

config = AiolaConfig(
    api_key="YOUR_KEY",
    query_params=AiolaQueryParams(execution_id="YOUR_GENERATED_ID")
)
client = AiolaSttClient(config)
await client.connect(auto_record=True)
```

## Configuration
```python
AiolaConfig:{
    api_key: str
    query_params: AiolaQueryParams
    base_url: Optional[str] = 'https://api.aiola.ai'
    mic_config: Optional[MicConfig] = field(default_factory=MicConfig)
    vad_config: Optional[VadConfig] = field(default_factory=VadConfig)
    events: Optional[AiolaEvents] = field(default_factory=dict)
    transports: Literal["polling", "websocket", "all"] = "all"
}
```

**api_key** (str): Authentication key for the aiOla service

**Query Parameters**

The `query_params` argument is required in the configuration and controls session and recognition behavior. It must be an instance of `AiolaQueryParams`:

- **execution_id** (`str`, required): Unique identifier for the session/context. Must be 4 to 24 characters long and contain only letters and numbers.
- **flow_id** (`str`, optional): Identifier for a specific flow. Defaults to the playground flow (ASR only, no LLM tasks).
- **lang_code** (`str`, optional): Language code for speech recognition. Supported values: `en_US`, `es_ES`, `fr_FR`, `de_DE`, `pt_PT`, `ja_JP`, `it_IT`, `zh_CN`. Defaults to `en_US`.
- **time_zone** (`str`, optional): IANA timezone identifier (e.g., `UTC`, `America/New_York`). Must be a valid IANA timezone. Defaults to `UTC`.

Example:

```python
from aiola_stt import AiolaSttClient, AiolaConfig, AiolaQueryParams

config = AiolaConfig(
    api_key="your-api-key",
    query_params=AiolaQueryParams(
        execution_id="abcd1234",  # Required
        flow_id="custom-flow-id", # Optional
        lang_code="en_US",        # Optional
        time_zone="America/New_York" # Optional
    )
)
client = AiolaSttClient(config)
```

Validation:

- `execution_id` must be 4-24 alphanumeric characters.
- `time_zone` must be a valid IANA timezone (see [IANA Time Zone Database](https://www.iana.org/time-zones)).
- `lang_code` must be one of the supported language codes.

See the [examples](../../examples/stt/) for more advanced usage.

### Event Handling

```python
from aiola_stt import AiolaSocketEvents

# Define event handlers
events = AiolaSocketEvents(
    on_transcript=lambda data: print(f"Transcript: {data}"),
    on_connect=lambda transport: print(f"Connected via {transport}"),
    on_disconnect=lambda: print("Disconnected"),
    on_error=lambda error: print(f"Error: {error}"),
    on_start_record=lambda: print("Recording started"),
    on_stop_record=lambda: print("Recording stopped")
)

# Add events to config
config = AiolaSocketConfig(
    base_url="your-base-url", # i.e https://api.aiola.ai
    namespace=AiolaSocketNamespace.EVENTS,
    api_key="your-api-key",
    query_params={},
    events=events
)
```

### Keyword Spotting

```python
# Set keywords to spot in the audio stream
await client.set_keywords(["hello", "world"])

# Get currently active keywords
active_keywords = client.get_active_keywords()
```

### Custom Audio Streaming

```python
async def custom_audio_generator():
    # Your custom audio streaming logic here
    while True:
        audio_data = await get_audio_data()  # Your audio data source
        yield audio_data

# Use custom audio generator
await client.connect(auto_record=True, custom_stream_generator=custom_audio_generator())
```

#### Media File Upload

```python
from aiola_stt.client import AiolaSttClient
from aiola_stt.config import AiolaSocketConfig

def on_file_transcript(file_path):
    <your code here...>

# Configure client
config = AiolaSocketConfig(
    base_url="your-base-url",
    api_key="your-api-key",
    query_params=AiolaQueryParams(execution_id='<Generate your own execution id>'), # Required field, 4 to 24 characters long and contains only letters and numbers
    events={
            "on_error": on_error,
            "on_file_transcript": on_file_transcript
        },
)

# Initialize client
client = AiolaSttClient(config)

# Connect and start recording
await client.connect(auto_record=True)
await client.transcribe_file(file_path, output_transcript_file_path)

```

### Microphone Configuration

```python
from aiola_stt import MicConfig

mic_config = MicConfig(
    sample_rate=16000,  # Hz
    chunk_size=4096,    # Samples per chunk
    channels=1          # Mono audio
)
```

### Voice Activity Detection Configuration

```python
from aiola_stt import VadConfig

vad_config = VadConfig(
    vad_threshold=0.5,              # VAD threshold (0.0 to 1.0)
    min_silence_duration_ms=250     # Minimum silence duration
)
```

## Error Handling

The SDK provides comprehensive error handling through the `AiolaSocketError` class:

```python
from aiola_stt import AiolaSocketError, AiolaSocketErrorCode

try:
    await client.connect()
except AiolaSocketError as e:
    print(f"Error: {e.message}")
    print(f"Error code: {e.code}")
    print(f"Details: {e.details}")
```

## License

MIT License
