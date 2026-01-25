# aiOla Python SDK

The official Python SDK for the [aiOla](https://aiola.com) API, designed to work seamlessly in both synchronous and asynchronous environments.

## Documentation

Learn more about the aiOla API and how to use the SDK in our [documentation](https://docs.aiola.ai).

## Installation

### Basic Installation

```bash
pip install aiola
# or
uv add aiola
```

### With Microphone Support

For microphone streaming functionality, install with the mic extra:

```bash
pip install 'aiola[mic]'
# or
uv add 'aiola[mic]'
```

## Usage

### Authentication

The aiOla SDK uses a **two-step authentication process**:

1. **Generate Access Token**: Use your API key to create a temporary access token, save it for later use
2. **Create Client**: Use the access token to instantiate the client

#### Step 1: Generate Access Token

```python
from aiola import AiolaClient

result = AiolaClient.grant_token(
    api_key='your-api-key'
)

access_token = result.access_token
session_id = result.session_id
```

#### Step 2: Create Client

```python
client = AiolaClient(
    access_token=access_token
)
```

#### Complete Example

```python
import os
from aiola import AiolaClient

def example():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        # Step 2: Create client
        client = AiolaClient(
            access_token=result.access_token
        )

        # Step 3: Use client for API calls
        with open('path/to/your/audio.wav', 'rb') as audio_file:
            transcript = client.stt.transcribe_file(
                file=audio_file,
                language='en'
            )

        print('Transcript:', transcript)

    except Exception as error:
        print('Error:', error)
```

#### Session Management

**Close Session:**
```python
# Terminates the session
result = AiolaClient.close_session(access_token)
print(f"Session closed at: {result.deleted_at}")
```

#### Custom base URL (enterprises)

```python
result = AiolaClient.grant_token(
    api_key='your-api-key',
    auth_base_url='https://mycompany.auth.aiola.ai'
)

client = AiolaClient(
    access_token=result.access_token,
    base_url='https://mycompany.api.aiola.ai'
)
```

### Speech-to-Text – transcribe file

```python
import os
from aiola import AiolaClient

def transcribe_file():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        # Step 2: Create client
        client = AiolaClient(
            access_token=result.access_token
        )

        # Step 3: Transcribe file
        with open('path/to/your/audio.wav', 'rb') as audio_file:
            transcript = client.stt.transcribe_file(
                file=audio_file,
                language="e" # supported lan: en,de,fr,es,pr,zh,ja,it
            )

        print(transcript)
    except Exception as error:
        print('Error transcribing file:', error)
```

### Speech-to-Text – live streaming

```python
import os
from aiola import AiolaClient, MicrophoneStream
from aiola.types import LiveEvents

def live_streaming():
    try:
        # Step 1: Generate access token, save it
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY') or 'YOUR_API_KEY'
        )

        # Step 2: Create client using the access token
        client = AiolaClient(
            access_token=result.access_token
        )

        # Step 3: Start streaming
        connection = client.stt.stream(
            lang_code='en'
        )

        @connection.on(LiveEvents.Transcript)
        def on_transcript(data):
            print('Transcript:', data.get('transcript', data))

        @connection.on(LiveEvents.Connect)
        def on_connect():
            print('Connected to streaming service')

        @connection.on(LiveEvents.Disconnect)
        def on_disconnect():
            print('Disconnected from streaming service')

        @connection.on(LiveEvents.Error)
        def on_error(error):
            print('Streaming error:', error)

        connection.connect()

        try:
            # Capture audio from microphone using the SDK's MicrophoneStream
            with MicrophoneStream(
                channels=1,
                samplerate=16000,
                blocksize=4096,
            ) as mic:
                mic.stream_to(connection)

                # Keep the main thread alive
                while True:
                    try:
                        import time
                        time.sleep(0.1)
                    except KeyboardInterrupt:
                        print('Keyboard interrupt')
                        break

        except KeyboardInterrupt:
            print('Keyboard interrupt')

    except Exception as error:
        print('Error:', error)
    finally:
        connection.disconnect()

if __name__ == "__main__":
    live_streaming()
```

### Text-to-Speech

```python
import os
from aiola import AiolaClient, VoiceId

def create_file():
    try:
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        client = AiolaClient(
            access_token=result.access_token
        )

        audio = client.tts.synthesize(
            text='Hello, how can I help you today?',
            voice_id=VoiceId.EnglishUSMale  # Type-safe enum
        )

        with open('./audio.wav', 'wb') as f:
            for chunk in audio:
                f.write(chunk)

        print('Audio file created successfully')
    except Exception as error:
        print('Error creating audio file:', error)

create_file()
```

### Text-to-Speech – streaming

```python
import os
from aiola import AiolaClient, VoiceId

def stream_tts():
    try:
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        client = AiolaClient(
            access_token=result.access_token
        )

        stream = client.tts.stream(
            text='Hello, how can I help you today?',
            voice_id=VoiceId.EnglishUSMale  # Type-safe enum
        )

        audio_chunks = []
        for chunk in stream:
            audio_chunks.append(chunk)

        print('Audio chunks received:', len(audio_chunks))
    except Exception as error:
        print('Error streaming TTS:', error)
```

## Async Client

For asynchronous operations, use the `AsyncAiolaClient`:

### Async Speech-to-Text – file transcription

```python
import asyncio
import os
from aiola import AsyncAiolaClient

async def transcribe_file():
    try:
        result = await AsyncAiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        client = AsyncAiolaClient(
            access_token=result.access_token
        )

        with open('path/to/your/audio.wav', 'rb') as audio_file:
            transcript = await client.stt.transcribe_file(
                file=audio_file,
                language="e" # supported lan: en,de,fr,es,pr,zh,ja,it
            )

        print(transcript)
    except Exception as error:
        print('Error transcribing file:', error)

if __name__ == "__main__":
    asyncio.run(transcribe_file())
```

### Async Text-to-Speech

```python
import asyncio
import os
from aiola import AsyncAiolaClient, VoiceId

async def create_audio_file():
    try:
        result = await AsyncAiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        client = AsyncAiolaClient(
            access_token=result.access_token
        )

        audio = client.tts.synthesize(
            text='Hello, how can I help you today?',
            voice_id=VoiceId.EnglishUSMale  # Type-safe enum
        )

        with open('./audio.wav', 'wb') as f:
            async for chunk in audio:
                f.write(chunk)

        print('Audio file created successfully')
    except Exception as error:
        print('Error creating audio file:', error)

if __name__ == "__main__":
    asyncio.run(create_audio_file())
```

### Async Text-to-Speech – streaming

```python
import asyncio
import os
from aiola import AsyncAiolaClient, VoiceId

async def stream_tts():
    try:
        result = await AsyncAiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        client = AsyncAiolaClient(
            access_token=result.access_token
        )

        stream = client.tts.stream(
            text='Hello, how can I help you today?',
            voice_id=VoiceId.EnglishUSMale  # Type-safe enum
        )

        audio_chunks = []
        async for chunk in stream:
            audio_chunks.append(chunk)

        print('Audio chunks received:', len(audio_chunks))
    except Exception as error:
        print('Error streaming TTS:', error)

if __name__ == "__main__":
    asyncio.run(stream_tts())
```

## Requirements

- Python 3.10+
- For microphone streaming functionality: Install with `pip install 'aiola[mic]'`

## Examples

The SDK includes several example scripts in the `examples/` directory.

---

## API Reference

### AiolaClient

Main client for interacting with the Aiola API (synchronous).

#### Static Methods

##### `AiolaClient.grant_token(api_key, auth_base_url=None, workflow_id=None)`

Generates an access token from an API key.

**Parameters:**
- `api_key` (str, required): Your Aiola API key
- `auth_base_url` (str, optional): Custom authentication base URL
- `workflow_id` (str, optional): Custom workflow ID

**Returns:** `GrantTokenResponse`
- `access_token` (str): JWT access token for API authentication
- `session_id` (str): Unique session identifier

##### `AiolaClient.close_session(access_token, auth_base_url=None)`

Closes a session on the server and frees up concurrency slots.

**Parameters:**
- `access_token` (str, required): The access token for the session
- `auth_base_url` (str, optional): Custom authentication base URL

**Returns:** `SessionCloseResponse`

#### Constructor

##### `AiolaClient(api_key=None, access_token=None, base_url=None, auth_base_url=None, workflow_id=None, timeout=30)`

Creates a new AiolaClient instance. Either `api_key` or `access_token` must be provided.

**Parameters:**
- `api_key` (str, optional): Your Aiola API key for automatic token management
- `access_token` (str, optional): Pre-generated access token from `grant_token()`
- `base_url` (str, optional): Custom API base URL
- `auth_base_url` (str, optional): Custom authentication base URL
- `workflow_id` (str, optional): Custom workflow ID
- `timeout` (int, optional): HTTP request timeout in seconds (default: 30)

#### Properties

##### `client.stt`

Gets the Speech-to-Text (STT) client.

**Type:** `SttClient`

##### `client.tts`

Gets the Text-to-Speech (TTS) client.

**Type:** `TtsClient`

##### `client.auth`

Gets the authentication client (internal use).

**Type:** `AuthClient`

##### `client.options`

Gets the client configuration options.

**Type:** `AiolaClientOptions`

---

### AsyncAiolaClient

Main client for interacting with the Aiola API (asynchronous). Same API as `AiolaClient` but with async/await support.

---

### STT Client

Speech-to-Text client for audio transcription.

#### Methods

##### `client.stt.transcribe_file(file, language=None, keywords=None, vad_config=None)`

Transcribes an audio file to text.

**Parameters:**
- `file` (File, required): Audio file (file path, file object, or bytes). Formats: WAV, MP3, M4A, OGG, FLAC
- `language` (str, optional): Language code (e.g., 'en', 'es', 'fr')
- `keywords` (dict, optional): Keywords map for boosting recognition
- `vad_config` (VadConfig, optional): Voice Activity Detection configuration

**Returns:** `TranscriptionResponse`
- `transcript` (str): Complete transcription with formatting
- `raw_transcript` (str): Raw transcription without post-processing
- `segments` (list[Segment]): Time segments where speech was detected
- `metadata` (TranscriptionMetadata): File metadata and transcription info

##### `client.stt.stream(workflow_id=None, execution_id=None, lang_code=None, time_zone=None, keywords=None, tasks_config=None, vad_config=None)`

Creates a real-time streaming connection for audio transcription.

**Parameters:**
- `lang_code` (str, optional): Language code (e.g., 'en', 'es', 'fr')
- `workflow_id` (str, optional): Custom workflow ID
- `execution_id` (str, optional): Execution ID for tracking (auto-generated if not provided)
- `time_zone` (str, optional): Timezone for timestamps (default: 'UTC')
- `keywords` (dict, optional): Keywords map for boosting recognition
- `tasks_config` (TasksConfig, optional): AI tasks configuration
- `vad_config` (VadConfig, optional): Voice Activity Detection configuration

**Returns:** `StreamConnection`

**Audio format requirements:** 16-bit PCM, 16kHz sample rate, mono channel

---

### StreamConnection

Real-time audio streaming connection for transcription.

#### Methods

##### `stream.connect()`

Establishes the Socket.IO connection.

##### `stream.disconnect()`

Closes the Socket.IO connection.

##### `stream.send(data)`

Sends audio data to the streaming service.

**Parameters:**
- `data` (bytes, required): Audio data (16-bit PCM, 16kHz, mono)

##### `stream.on(event, handler=None)`

Registers an event listener. Can be used as a decorator.

**Available events:**
- `LiveEvents.Transcript`: Real-time transcription results
- `LiveEvents.Structured`: Structured data extraction results
- `LiveEvents.Translation`: Translation results (if enabled)
- `LiveEvents.Connect`: Connection established
- `LiveEvents.Disconnect`: Connection closed
- `LiveEvents.Error`: Error occurred

##### `stream.set_keywords(keywords)`

Sets or updates keywords for recognition boosting.

**Parameters:**
- `keywords` (dict, required): Map of spoken phrases to written forms

#### Properties

##### `stream.connected`

Indicates whether the client is currently connected.

**Type:** `bool`

---

### TTS Client

Text-to-Speech client for converting text to spoken audio.

#### Methods

##### `client.tts.synthesize(text, voice_id)`

Synthesizes text to speech with complete generation.

**Parameters:**
- `text` (str, required): Text to convert to speech
- `voice_id` (VoiceId | str, required): Voice identifier

**Supported voice IDs (VoiceId enum):**

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `VoiceId.EnglishUSFemale` | `'en_us_female'` | English (US) Female |
| `VoiceId.EnglishUSMale` | `'en_us_male'` | English (US) Male |
| `VoiceId.SpanishFemale` | `'es_female'` | Spanish Female |
| `VoiceId.SpanishMale` | `'es_male'` | Spanish Male |
| `VoiceId.FrenchFemale` | `'fr_female'` | French Female |
| `VoiceId.FrenchMale` | `'fr_male'` | French Male |
| `VoiceId.GermanFemale` | `'de_female'` | German Female |
| `VoiceId.GermanMale` | `'de_male'` | German Male |
| `VoiceId.JapaneseFemale` | `'ja_female'` | Japanese Female |
| `VoiceId.JapaneseMale` | `'ja_male'` | Japanese Male |
| `VoiceId.PortugueseFemale` | `'pt_female'` | Portuguese Female |
| `VoiceId.PortugueseMale` | `'pt_male'` | Portuguese Male |

**Returns:** `Iterator[bytes]`

**Example:**
```python
from aiola import VoiceId

# Using enum (recommended - type-safe with autocomplete)
audio = client.tts.synthesize(
    text='Hello, world!',
    voice_id=VoiceId.EnglishUSFemale
)

# Or using string
audio = client.tts.synthesize(
    text='Hello, world!',
    voice_id='en_us_female'
)
```

##### `client.tts.stream(text, voice_id)`

Synthesizes text to speech with streaming delivery (lower latency).

**Parameters:**
- `text` (str, required): Text to convert to speech
- `voice_id` (VoiceId | str, required): Voice identifier (see supported voices above)

**Returns:** `Iterator[bytes]`

---

### MicrophoneStream

Utility for streaming audio from the microphone (requires `aiola[mic]` extra).

#### Constructor

##### `MicrophoneStream(channels=1, samplerate=16000, blocksize=4096, device=None)`

**Parameters:**
- `channels` (int, optional): Number of audio channels (default: 1)
- `samplerate` (int, optional): Sample rate in Hz (default: 16000)
- `blocksize` (int, optional): Audio block size (default: 4096)
- `device` (int/str, optional): Audio device to use

#### Methods

##### `mic.start()`

Starts recording from the microphone.

##### `mic.stop()`

Stops recording.

##### `mic.read(timeout=None)`

Reads audio data from the microphone.

**Returns:** `bytes`

##### `mic.stream_to(connection)`

Streams microphone audio to a StreamConnection.

##### `mic.stream_with_callback(callback)`

Streams microphone audio with a callback function.

##### `mic.list_devices()` (classmethod)

Lists available audio devices.

**Returns:** List of audio devices

#### Properties

##### `mic.is_recording`

Indicates whether currently recording.

**Type:** `bool`

---

### Streaming Events Reference

#### `LiveEvents.Transcript`

Emitted when new transcription text is available.

**Payload:**
```python
{
    'transcript': str  # The transcribed text
}
```

#### `LiveEvents.Structured`

Emitted when structured data is extracted (requires FORM_FILLING task).

**Payload:**
```python
{
    'results': dict  # Structured data extracted
}
```

#### `LiveEvents.Translation`

Emitted when translation is available (requires TRANSLATION task).

**Payload:**
```python
{
    'translation': str  # The translated text
}
```

#### Connection Events

- `LiveEvents.Connect`: Fired when Socket.IO connection is established
- `LiveEvents.Disconnect`: Fired when Socket.IO connection is closed
- `LiveEvents.Error`: Fired when an error occurs (receives error object)

---

### Error Handling

All errors thrown by the SDK inherit from `AiolaError`.

#### Error Classes

| Error Class | Description | When Raised |
|-------------|-------------|-------------|
| `AiolaError` | Base error class | Base for all SDK errors |
| `AiolaConnectionError` | Network connectivity issues | Network errors, timeouts, DNS failures |
| `AiolaAuthenticationError` | Authentication failures | Invalid API key, expired token (401) |
| `AiolaValidationError` | Invalid parameters | Missing required fields, wrong types |
| `AiolaStreamingError` | Streaming issues | WebSocket connection problems |
| `AiolaFileError` | File operation failures | Invalid file format, file not found |
| `AiolaRateLimitError` | Rate limit exceeded | Too many requests (429) |
| `AiolaServerError` | Server-side errors | Internal server errors (5xx) |

#### Error Attributes

All error classes have these attributes:
- `message` (str): Human-readable error description
- `reason` (str): Detailed explanation from server
- `status` (int): HTTP status code
- `code` (str): Machine-readable error code
- `details` (Any): Additional diagnostic information

#### Common Error Codes

| Code | Description | How to Handle |
|------|-------------|---------------|
| `TOKEN_EXPIRED` | Access token has expired | Generate a new token |
| `INVALID_TOKEN` | Access token is invalid | Verify API key and generate new token |
| `MAX_CONCURRENCY_REACHED` | Too many concurrent sessions | Close existing sessions or wait |
| `INVALID_AUDIO_FORMAT` | Unsupported audio format | Use WAV, MP3, M4A, OGG, or FLAC |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Implement exponential backoff |
| `WORKFLOW_NOT_FOUND` | Workflow ID doesn't exist | Verify workflow ID |
| `UNAUTHORIZED` | Invalid API key | Check API key and permissions |
| `VALIDATION_ERROR` | Invalid parameters | Check parameter types and values |

#### Error Handling Examples

```python
from aiola import AiolaClient, AiolaAuthenticationError, AiolaRateLimitError
import time

# Handle specific errors
try:
    result = client.stt.transcribe_file('audio.wav')
except AiolaAuthenticationError as e:
    if e.code == 'TOKEN_EXPIRED':
        # Refresh token and retry
        token = AiolaClient.grant_token(api_key='your-key')
        client = AiolaClient(access_token=token.access_token)
        result = client.stt.transcribe_file('audio.wav')
except AiolaRateLimitError as e:
    # Wait and retry
    time.sleep(60)
    result = client.stt.transcribe_file('audio.wav')

# General error handling
try:
    result = client.stt.transcribe_file('audio.wav')
except AiolaError as e:
    print(f"Error: {e.message}")
    print(f"Code: {e.code}")
    print(f"Status: {e.status}")
    print(f"Reason: {e.reason}")
```

---

### Audio Format Requirements

#### File Transcription

**Supported formats:** WAV, MP3, M4A, OGG, FLAC

**Recommended specifications:**
- Sample rate: 16kHz or higher
- Channels: Mono or stereo
- Bit depth: 16-bit

#### Streaming Audio

**Required specifications:**
- Format: 16-bit PCM (raw audio)
- Sample rate: 16kHz
- Channels: Mono (1 channel)
- Encoding: Little-endian

**Chunk size recommendations:**
- Minimum: 100ms of audio (~3,200 bytes)
- Recommended: 100-500ms chunks
- Maximum: 1000ms per chunk

---

### Voice Activity Detection (VAD)

Configure how speech and silence are detected in audio streams.

**Configuration options:**

```python
from aiola.types import VadConfig

vad_config = VadConfig(
    threshold=0.6,          # Detection threshold (0.0-1.0, default: ~0.5)
    min_speech_ms=300,      # Minimum speech duration (default: ~250ms)
    min_silence_ms=700,     # Minimum silence to split segments (default: ~500ms)
    max_segment_ms=15000    # Maximum segment duration (default: ~30000ms)
)
```

---

### AI Tasks Configuration

Enable AI-powered analysis tasks during transcription.

**Example:**

```python
from aiola.types import TasksConfig, TranslationPayload

tasks_config = TasksConfig(
    TRANSLATION=TranslationPayload(
        src_lang_code='en',
        dst_lang_code='es'
    )
)

stream = client.stt.stream(
    lang_code='en',
    tasks_config=tasks_config
)
```

---

### Sync vs Async Usage

#### When to Use Sync (`AiolaClient`)

- Simple scripts and applications
- Blocking I/O is acceptable
- Working with synchronous libraries
- Traditional Python development

#### When to Use Async (`AsyncAiolaClient`)

- High-concurrency applications
- Web servers (FastAPI, aiohttp)
- Multiple concurrent API calls
- Need for non-blocking I/O
- Integration with async libraries

**Example: Concurrent Transcriptions**

```python
import asyncio
from aiola import AsyncAiolaClient

async def transcribe_multiple_files():
    token = await AsyncAiolaClient.grant_token(api_key='your-key')
    client = AsyncAiolaClient(access_token=token.access_token)
    
    files = ['audio1.wav', 'audio2.wav', 'audio3.wav']
    
    # Transcribe all files concurrently
    tasks = [
        client.stt.transcribe_file(file, language='en')
        for file in files
    ]
    
    results = await asyncio.gather(*tasks)
    return results

# Run async function
results = asyncio.run(transcribe_multiple_files())
```

---

## Troubleshooting

### Connection Issues

**Problem:** Connection errors or timeouts

**Solutions:**
- Verify network connection
- Check firewall settings for WebSocket connections
- Ensure you're using a valid access token
- Try increasing timeout parameter

### Audio Quality Issues

**Problem:** Poor transcription accuracy

**Solutions:**
- Ensure audio is in correct format (16-bit PCM, 16kHz, mono for streaming)
- Remove background noise
- Use `keywords` parameter for domain-specific terms
- Adjust VAD configuration
- Verify correct language code

### Token Expiration

**Problem:** `TOKEN_EXPIRED` errors

**Solutions:**
- Generate a new token when needed
- Implement automatic token refresh
- Tokens have a 5-minute expiration buffer

### Concurrency Limits

**Problem:** `MAX_CONCURRENCY_REACHED` errors

**Solutions:**
- Close unused sessions using `close_session()`
- Wait for existing sessions to expire
- Upgrade plan for higher limits
- Implement session pooling

### Microphone Issues

**Problem:** Microphone not working

**Solutions:**
- Install with mic extra: `pip install 'aiola[mic]'`
- Check microphone permissions
- List devices with `MicrophoneStream.list_devices()`
- Verify device index is correct
- Check microphone is not in use by another application

### Import Errors

**Problem:** `ImportError` when importing SDK

**Solutions:**
- Ensure Python 3.10+ is installed
- Reinstall package: `pip install --upgrade aiola`
- For mic support: `pip install 'aiola[mic]'`
- Check virtual environment is activated

### File Upload Errors

**Problem:** Errors when uploading files

**Solutions:**
- Verify file format is supported
- Check file exists and is readable
- Ensure file permissions are correct
- Verify file is not corrupted

### Getting Help

If you encounter issues not covered here:

1. Check the [documentation](https://docs.aiola.ai)
2. Review the [examples](./examples) directory
3. Contact Aiola support with:
   - Error messages and codes
   - SDK version
   - Python version
   - Minimal code to reproduce the issue

---

## License

MIT License - see [LICENSE](LICENSE) file for details.
