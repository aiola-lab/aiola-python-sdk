# Text-to-Speech (TTS) Examples

This directory contains examples demonstrating how to use the aiOla SDK for text-to-speech functionality.

## Quick start

<!--snippet;tts;quickstart-->
```python
import os
from aiola import AiolaClient

def synthesize_to_file():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv("AIOLA_API_KEY") or "YOUR_API_KEY"
        )
        
        # Step 2: Create client
        client = AiolaClient(access_token=result["accessToken"])
        
        audio_stream = client.tts.synthesize(
            text="Hello, how can I help you today?",
            voice="jess",
            language="en"
        )

        # Save to file
        with open("./output.wav", "wb") as file_stream:
            for chunk in audio_stream:
                file_stream.write(chunk)

        print("Audio file saved successfully!")
    except Exception as error:
        print("Error saving file:", error)

if __name__ == "__main__":
    synthesize_to_file()
```

## Available Examples

- `tts_file.py` - Basic text-to-speech synthesis to file
- `tts_stream.py` - Streaming TTS with session management  
- `async_tts.py` - Asynchronous TTS examples

## Session Management

The examples demonstrate proper session management:

1. **Token Generation**: Use `AiolaClient.grant_token()` to get both access token and session ID
2. **Client Creation**: Create client with the access token
3. **Session Cleanup**: Close sessions with `AiolaClient.close_session()` to free resources

## Complete Example with Session Management

```python
import os
from aiola import AiolaClient

# Example with session management
result = AiolaClient.grant_token(api_key=os.getenv("AIOLA_API_KEY"))
client = AiolaClient(access_token=result['accessToken'])
print(f"Session ID: {result['sessionId']}")

def synthesize_to_file():
    audio_stream = client.tts.synthesize(
        text="Hello, how can I help you today?",
        voice="jess",
        language="en"
    )

    # Save to file
    try:
        with open("./output.wav", "wb") as file_stream:
            for chunk in audio_stream:
                file_stream.write(chunk)
        print("Audio file saved successfully!")
    except Exception as error:
        print("Error saving file:", error)

def stream_tts():
    stream = client.tts.stream(
        text="Hello, this is a streaming example of text-to-speech synthesis.",
        voice="jess",
        language="en"
    )
    
    # Collect audio chunks
    audio_chunks = []
    for chunk in stream:
        audio_chunks.append(chunk)
    
    # Process chunks as needed (e.g., play audio, save to buffer, etc.)
    print(f"Collected {len(audio_chunks)} audio chunks")

synthesize_to_file()
stream_tts()

# Clean up session when done
try:
    close_result = AiolaClient.close_session(result['accessToken'])
    print(f"Session closed at: {close_result['deletedAt']}")
except Exception as e:
    print(f"Session close failed: {e}")
```

## Async Examples

For async usage, use `AsyncAiolaClient`:

```python
import asyncio
import os
from aiola import AsyncAiolaClient

async def async_tts_example():
    result = await AsyncAiolaClient.grant_token(api_key=os.getenv("AIOLA_API_KEY"))
    client = AsyncAiolaClient(access_token=result['accessToken'])
    
    response = client.tts.synthesize(text="Hello world", voice="jess", language="en")
    
    async for chunk in response:
        # Process audio chunk
        pass
    
    await AsyncAiolaClient.close_session(result['accessToken'])

asyncio.run(async_tts_example())
```