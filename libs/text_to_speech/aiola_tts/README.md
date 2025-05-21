# aiOla Text-to-Speech SDK

Python SDK for aiOla's Text-to-Speech API.

## Features

- Text-to-speech synthesis
- Multiple voice options
- Streaming support
- Support for different audio formats

## Installation

```bash
pip install aiola-tts
```

## Usage

```python
from aiola_tts import AiolaTtsClient, AudioFormat

client = AiolaTtsClient(
    bearer_token="YOUR_TOKEN",
    audio_format=AudioFormat.LINEAR16
)
audio = client.synthesize("Hello world", voice="af_bella")
with open("output.wav", "wb") as f:
    f.write(audio)
```

## Configuration

- `bearer_token`: Your API token
- `audio_format`: LINEAR16 or PCM
- `base_url`: (optional) API endpoint

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

## Advanced Usage

- Streaming synthesis
- Voice options

## Error Handling

```python
try:
    client.synthesize("Hello world")
except Exception as e:
    print(e)
```

## License

MIT License