# aiOla Text-to-Speech SDK

The aiOla Text-to-Speech SDK provides Python bindings for aiOla's text-to-speech services, enabling high-quality voice synthesis with multiple voice options.

## Features

- Text-to-speech synthesis
- Multiple voice options
- Streaming support
- Customizable audio formats
- Error handling and logging

## Installation

```bash
pip install aiola-tts
```

## Usage

### Basic Usage

```python
from aiola_tts import AiolaTtsClient, AudioFormat

# Initialize client
client = AiolaTtsClient(
    base_url="your-base-url",  # i.e https://api.aiola.ai
    bearer_token="your-bearer-token",
    audio_format=AudioFormat.LINEAR16  # or AudioFormat.PCM
)

# Synthesize text to speech
audio_data = client.synthesize(
    text="Hello, world!",
    voice="af_bella"  # Optional, defaults to "af_bella"
)

# Save the audio data to a file
with open("output.wav", "wb") as f:
    f.write(audio_data)
```

### Streaming Support

```python
# Stream text-to-speech audio
streamed_audio = client.synthesize_stream(
    text="Hello, world!",
    voice="af_bella"  # Optional, defaults to "af_bella"
)

# Process the streamed audio data
with open("streamed_output.wav", "wb") as f:
    f.write(streamed_audio)
```

### Available Voices

The SDK supports multiple voice options:

```python
# Female voices
"af_bella"    # Default voice
"af_nicole"
"af_sarah"
"af_sky"

# Male voices
"am_adam"
"am_michael"
"bf_emma"
"bf_isabella"
"bm_george"
"bm_lewis"
```

### Audio Format Configuration

The SDK supports two audio formats:

```python
from aiola_tts import AudioFormat

# LINEAR16 format (default)
client = AiolaTtsClient(
    base_url="your-base-url",
    bearer_token="your-bearer-token",
    audio_format=AudioFormat.LINEAR16
)

# PCM format
client = AiolaTtsClient(
    base_url="your-base-url",
    bearer_token="your-bearer-token",
    audio_format=AudioFormat.PCM
)
```

## Development

To install development dependencies:

```bash
pip install -e ".[dev]"
```

## Error Handling

The SDK provides comprehensive error handling:

```python
try:
    audio_data = client.synthesize("Hello, world!")
except requests.exceptions.RequestException as e:
    print(f"Error: {str(e)}")
```

## License

MIT License
