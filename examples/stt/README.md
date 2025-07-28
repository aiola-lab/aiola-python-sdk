# Speech-to-Text (STT) Examples

This directory contains examples demonstrating how to use the aiOla SDK for speech-to-text functionality.

## Installation

For microphone streaming functionality, install the SDK with the mic extra:

```bash
pip install 'aiola[mic]'
```

With uv:
```bash
uv add 'aiola[mic]'
# or for development
uv sync --group dev  # includes mic dependencies
```

Or if you prefer to use your own microphone implementation:

```bash
pip install 'aiola[mic]'
```

## Quick start

<!--snippet;stt;quickstart-->
```python
import os
import time
from aiola import AiolaClient, MicrophoneStream # pip install 'aiola[mic]'
from aiola.types import LiveEvents

def live_streaming():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv("AIOLA_API_KEY") or "YOUR_API_KEY"
        )
        
        # Step 2: Create client
        client = AiolaClient(access_token=result["accessToken"])
        
        # Step 3: Use the client
        connection = client.stt.stream(
            lang_code="en",
            keywords={"<word_to_catch>": "<word_transcribe>"}
            )

        @connection.on(LiveEvents.Transcript)
        def on_transcript(data):
            print("Transcript:", data.get("transcript", data))

        @connection.on(LiveEvents.Connect)
        def on_connect():
            print("Connected to streaming service")

        @connection.on(LiveEvents.Disconnect)
        def on_disconnect():
            print("Disconnected from streaming service")

        @connection.on(LiveEvents.Error)
        def on_error(error):
            print("Streaming error:", error)

        connection.connect()

        with MicrophoneStream(channels=1, samplerate=16000, blocksize=4096) as mic:
            mic.stream_to(connection)
            # Keep the main thread alive
            while True:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("Keyboard interrupt")
    except Exception as error:
        print("Error:", error)
    finally:
        connection.disconnect()

if __name__ == "__main__":
    live_streaming()
```

## Alternative: Using Custom Microphone Implementation

If you prefer to use your own microphone implementation (e.g., with pyaudio), you can install the basic SDK and handle audio capture yourself:

```bash
pip install aiola
pip install pyaudio  # or your preferred audio library
```

See [mic_stream_custom.py](mic_stream_custom.py) for an example of using pyaudio directly with the aiOla SDK.