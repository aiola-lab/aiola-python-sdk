# aiOla Python SDKs

Welcome to the **aiOla Python SDKs** repository. This repository contains Python SDKs for integrating with aiOla's Text-to-Speech (TTS) and Speech-to-Text (STT) services.

## TL;DR - Demo

Want to try out the playground? Just clone and run:
```./build_and_play.sh ```

https://github.com/user-attachments/assets/6dbbb71d-9f70-46bb-8395-506d3d05abba


## Table of Contents

- [Text-to-Speech (TTS) SDK](#text-to-speech-tts-sdk)
- [Speech-to-Text (STT) SDK](#speech-to-text-stt-sdk)
- [Installation](#installation)
- [Getting Started](#getting-started)

## Text-to-Speech (TTS) SDK

The TTS SDK provides functionality to convert text into natural-sounding speech with various voice options.

### Features

- Convert text to speech and save as WAV files
- Real-time streaming of synthesized speech
- Multiple voice options available
- Support for different audio formats (LINEAR16, PCM)

### Voice Options

Available voices include:

- `af_bella` (default)
- `af_nicole`
- `af_sarah`
- `af_sky`
- `am_adam`
- `am_michael`
- `bf_emma`
- `bf_isabella`
- `bm_george`
- `bm_lewis`

### Code Examples

#### Basic Text-to-Speech Synthesis

```python
from aiola_tts.client import AiolaTtsClient

# Initialize client
tts_client = AiolaTtsClient(
    base_url="YOUR_API_URL",
    bearer_token="YOUR_BEARER_TOKEN"
)

# Synthesize speech
text = "Hello, this is a test of the aiOla TTS synthesis feature."
audio_data = tts_client.synthesize(text, voice="af_bella")

# Save to file
with open("output.wav", "wb") as f:
    f.write(audio_data)
```

#### Streaming Speech Synthesis

```python
from aiola_tts.client import AiolaTtsClient

# Initialize client
tts_client = AiolaTtsClient(
    base_url="YOUR_API_URL",
    bearer_token="YOUR_BEARER_TOKEN"
)

# Stream speech
stream_data = tts_client.synthesize_stream(
    "Streaming aiOla speech",
    voice="af_bella"
)
```

### Example Implementations

- [Basic Synthesis Example](examples/tts/synthesize.py)
- [Streaming Synthesis Example](examples/tts/synthesize_stream.py)

## Speech-to-Text (STT) SDK

The STT SDK enables real-time speech recognition with advanced features like keyword spotting and voice activity detection.

### Features

- Real-time speech transcription
- Keyword spotting
- Voice Activity Detection (VAD)
- Support for custom audio streams
- Event-driven architecture
- Multiple language support (en-US, de-DE, fr-FR, zh-ZH, es-ES, pt-PT)

### Code Examples

#### Basic Streaming with Built-in Microphone

```python
from aiola_stt.client import AiolaSttClient
from aiola_stt.config import AiolaSocketConfig, AiolaSocketNamespace

# Configure client
config = AiolaSocketConfig(
    base_url="YOUR_API_URL",
    api_key="YOUR_API_KEY",
    namespace=AiolaSocketNamespace.EVENTS,
    query_params={"flow_id": "YOUR_FLOW_ID"}
)

# Initialize client
client = AiolaSttClient(config)

# Connect and start recording
await client.connect(auto_record=True)
```

#### Custom Audio Stream

```python
async def audio_stream_handler():
    # Custom audio stream implementation
    with wave.open("input.wav", 'rb') as wav_file:
        while True:
            frames = wav_file.readframes(4096)
            if not frames:
                break
            yield frames

# Use custom stream
client.start_recording(custom_stream_generator=audio_stream_handler())
```

#### Keyword Spotting

```python
# Set keywords to spot and wait for transript

keywords = ["hello", "world", "aiola"]
await client.set_keywords(keywords)
```
### Example Implementations

- [Default Audio Stream with Auto-Record](examples/stt/deafult_audio_stream_auto_record.py)
- [Default Audio Stream with Lazy Record](examples/stt/deafult_audio_stream_lazy_record.py)
- [Custom Audio Stream](examples/stt/custom_audio_stream.py)

## Installation

### pypi
```bash
pip install aiola_stt
pip install aiola_tts

```
[aiola_tts](https://pypi.org/project/aiola-tts/) | [aiola_stt](https://pypi.org/project/aiola-stt/)

### local

1. Clone the repository:

   ```bash
   git clone https://github.com/aiola-lab/aiola-python-sdk.git
   cd aiola-python-sdk
   ```

2. setup development environment:
from the root
    ```bash
    . ./build_and_play.sh
    ```

3. Check out the example implementations in the`examples`directory:

   - TTS examples: [examples/tts/](libs/text_to_speech/aiola_tts/README.md)
   - STT examples: [examples/stt/](libs/speech_to_text/aiola_stt/README.md)

## License

MIT License
