# aiOla Python SDK

The official Python SDK for the [aiOla](https://aiola.com) API, designed to work seamlessly in both synchronous and asynchronous environments.

## Installation

```bash
pip install aiola-python
# or
uv add aiola-python
```

## Usage

### Instantiate the client

```python
import os
from aiola import AiolaClient

client = AiolaClient(
    api_key=os.getenv("AIOLA_API_KEY"),
)
```

#### Custom base URL (enterprises)

You can direct the SDK to use your own endpoint by providing the `base_url` option:

```python
client = AiolaClient(
    api_key=os.getenv("AIOLA_API_KEY"),
    base_url="https://api.mycompany.aiola.ai",
)
```

### Speech-to-Text – live streaming

```python
from aiola import AiolaClient
from aiola.clients.stt.types import LiveEvents

client = AiolaClient(api_key=os.getenv("AIOLA_API_KEY"))

connection = client.stt.stream(
    lang_code="en",
    keywords:{
        "Aiola": "aiOla"
    }
)

connection.connect()

@connection.on(LiveEvents.Transcript)
def on_transcript(data):
    print("📝 Transcript:", data)

connection.send(audio_data)
```

### Speech-to-Text – file transcription

```python
from aiola import AiolaClient

client = AiolaClient(api_key=os.getenv("AIOLA_API_KEY"))

# Transcribe an audio file
with open("audio.wav", "rb") as audio_file:
    result = client.stt.transcribe_file(
        file=audio_file,
        lang_code="en",
    )

```

### Text-to-Speech

```python
from aiola import AiolaClient

client = AiolaClient(api_key=os.getenv("AIOLA_API_KEY"))

response = client.tts.synthesize(
    text="Hello, how can I help you today?",
    voice="jess",
    language="en",
)

with open("audio.wav", "wb") as f:
    for chunk in response:
        f.write(chunk)
```

### Text-to-Speech – streaming

```python
from aiola import AiolaClient
from io import BytesIO

client = AiolaClient(api_key=os.getenv("AIOLA_API_KEY"))

response = client.tts.stream(
    text="Hello, how can I help you today?",
    voice="jess",
    language="en",
)

audio = BytesIO()
for chunk in response:
    audio.write(chunk)
```

## Async Client

For asynchronous operations, use the `AsyncAiolaClient`:

### Async Speech-to-Text – file transcription

```python
import asyncio
import os
from aiola import AsyncAiolaClient

async def transcribe_file():
    client = AsyncAiolaClient(api_key=os.getenv("AIOLA_API_KEY"))

    with open("audio.wav", "rb") as audio_file:
        result = await client.stt.transcribe_file(
            file=audio_file,
            lang_code="en",
            keywords={
                "aiola": "aiOla",
            },
        )

    print(result)

asyncio.run(transcribe_file())
```

### Async Text-to-Speech

```python
import asyncio
import os
from aiola import AsyncAiolaClient

async def create_audio_file():
    client = AsyncAiolaClient(api_key=os.getenv("AIOLA_API_KEY"))

    response = client.tts.synthesize(
        text="Hello, how can I help you today?",
        voice="jess",
        language="en",
    )

    with open("audio.wav", "wb") as f:
        async for chunk in response:
            f.write(chunk)

asyncio.run(create_audio_file())
```

### Async Text-to-Speech – streaming

```python
import asyncio
import os
from aiola import AsyncAiolaClient
from io import BytesIO

async def stream_tts():
    client = AsyncAiolaClient(api_key=os.getenv("AIOLA_API_KEY"))

    response = client.tts.stream(
        text="Hello, how can I help you today?",
        voice="jess",
        language="en",
    )

    audio = BytesIO()
    async for chunk in response:
        audio.write(chunk)

asyncio.run(stream_tts())
```

## Requirements

- Python 3.10+
- For microphone streaming examples: `pyaudio` (install separately)

## Examples

The SDK includes several example scripts in the `examples/` directory.