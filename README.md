# aiOla Python SDK

The official Python SDK for the [aiOla](https://aiola.com) API, designed to work seamlessly in both synchronous and asynchronous environments.

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

access_token = result['accessToken'] 
session_id = result['sessionId']
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
            access_token=result['accessToken']
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

example()
```

#### Session Management

**Close Session:**
```python
# Terminates the session
result = AiolaClient.close_session(access_token)
print(f"Session closed at: {result['deletedAt']}")
```

#### Custom base URL (enterprises)

```python
result = AiolaClient.grant_token(
    api_key='your-api-key',
    auth_base_url='https://mycompany.auth.aiola.ai'
)

client = AiolaClient(
    access_token=result['accessToken'],
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
            access_token=result['accessToken']
        )
        
        # Step 3: Transcribe file
        with open('path/to/your/audio.wav', 'rb') as audio_file:
            transcript = client.stt.transcribe_file(
                file=audio_file,
                language="en"
            )

        print(transcript)
    except Exception as error:
        print('Error transcribing file:', error)

transcribe_file()
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
            access_token=result['accessToken']
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
        finally:
            connection.disconnect()
        
    except Exception as error:
        print('Error:', error)

if __name__ == "__main__":
    live_streaming()
```

### Text-to-Speech

```python
import os
from aiola import AiolaClient

def create_file():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )
        
        # Step 2: Create client
        client = AiolaClient(
            access_token=result['accessToken']
        )
        
        # Step 3: Generate audio
        audio = client.tts.synthesize(
            text='Hello, how can I help you today?',
            voice='jess',
            language='en'
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
from aiola import AiolaClient

def stream_tts():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )
        
        # Step 2: Create client
        client = AiolaClient(
            access_token=result['accessToken']
        )
        
        # Step 3: Stream audio
        stream = client.tts.stream(
            text='Hello, how can I help you today?',
            voice='jess',
            language='en'
        )

        audio_chunks = []
        for chunk in stream:
            audio_chunks.append(chunk)
        
        print('Audio chunks received:', len(audio_chunks))
    except Exception as error:
        print('Error streaming TTS:', error)

stream_tts()
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
        # Step 1: Generate access token
        result = await AsyncAiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )
        
        # Step 2: Create client
        client = AsyncAiolaClient(
            access_token=result['accessToken']
        )
        
        # Step 3: Transcribe file
        with open('path/to/your/audio.wav', 'rb') as audio_file:
            transcript = await client.stt.transcribe_file(
                file=audio_file,
                language="en"
            )

        print(transcript)
    except Exception as error:
        print('Error transcribing file:', error)

asyncio.run(transcribe_file())
```

### Async Text-to-Speech

```python
import asyncio
import os
from aiola import AsyncAiolaClient

async def create_audio_file():
    try:
        # Step 1: Generate access token
        result = await AsyncAiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )
        
        # Step 2: Create client
        client = AsyncAiolaClient(
            access_token=result['accessToken']
        )
        
        # Step 3: Generate audio
        audio = client.tts.synthesize(
            text='Hello, how can I help you today?',
            voice='jess',
            language='en'
        )

        with open('./audio.wav', 'wb') as f:
            async for chunk in audio:
                f.write(chunk)
        
        print('Audio file created successfully')
    except Exception as error:
        print('Error creating audio file:', error)

asyncio.run(create_audio_file())
```

### Async Text-to-Speech – streaming

```python
import asyncio
import os
from aiola import AsyncAiolaClient

async def stream_tts():
    try:
        # Step 1: Generate access token
        result = await AsyncAiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )
        
        # Step 2: Create client
        client = AsyncAiolaClient(
            access_token=result['accessToken']
        )
        
        # Step 3: Stream audio
        stream = client.tts.stream(
            text='Hello, how can I help you today?',
            voice='jess',
            language='en'
        )

        audio_chunks = []
        async for chunk in stream:
            audio_chunks.append(chunk)
        
        print('Audio chunks received:', len(audio_chunks))
    except Exception as error:
        print('Error streaming TTS:', error)

asyncio.run(stream_tts())
```

## Requirements

- Python 3.10+
- For microphone streaming functionality: Install with `pip install 'aiola[mic]'`

## Examples

The SDK includes several example scripts in the `examples/` directory.