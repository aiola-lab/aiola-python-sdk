# Text-to-Speech (TTS) Examples

This directory contains examples demonstrating how to use the aiOla SDK for text-to-speech functionality.

## Quick start

<!--snippet;tts;quickstart-->
```python
# pip install aiola
from aiola import AiolaClient

def synthesize_to_file():
    try:
        # Step 1: Set up authentication
        result = AiolaClient.grant_token(api_key='your-api-key-here')
        access_token = result.access_token

        # Step 2: Create a client
        client = AiolaClient(access_token=access_token)

        # Step 3: Synthesize audio to a file
        audio_stream = client.tts.synthesize(
            text="Hello, how can I help you today?",
            voice="jess",
            language="en"
        )

        # Step 4: Save to file
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

def main():
    # Example with session management
    result = AiolaClient.grant_token(api_key=os.getenv("AIOLA_API_KEY"))
    client = AiolaClient(access_token=result.access_token)
    print(f"Session ID: {result.session_id}")

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
        close_result = AiolaClient.close_session(result.access_token)
        print(f"Session closed at: {close_result.deleted_at}")
    except Exception as e:
        print(f"Session close failed: {e}")

if __name__ == "__main__":
    main()
```

## Async Examples

For async usage, use `AsyncAiolaClient`:

```python
import asyncio
import os
from aiola import AsyncAiolaClient

async def async_tts_example():
    result = await AsyncAiolaClient.grant_token(api_key=os.getenv("AIOLA_API_KEY"))
    client = AsyncAiolaClient(access_token=result.access_token)

    response = await client.tts.synthesize(text="Hello world", voice="jess", language="en")

    async for chunk in response:
        # Process audio chunk
        pass

    await AsyncAiolaClient.close_session(result.access_token)


if __name__ == "__main__":
    asyncio.run(async_tts_example())
```
