# Speech-to-Text (STT) Examples

This directory contains examples demonstrating how to use the aiOla SDK for speech-to-text functionality.

## Quick start

<!--snippet;stt;quickstart-->
```python
import os
from aiola import AiolaClient
from aiola.types import LiveEvents

AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")

client = AiolaClient(api_key=AIOLA_API_KEY)

file_path = os.path.join(os.path.dirname(__file__), "audio.wav")

# Transcribe an audio file to text
def transcribe_file():
    with open(file_path, "rb") as audio_file:
        transcript = client.stt.transcribe_file(
            file=audio_file,
            language="en"
        )
    
    print(transcript)

# Stream audio in real-time for live transcription
def live_streaming():
    connection = client.stt.stream(lang_code="en")

    @connection.on(LiveEvents.Transcript)
    def on_transcript(data):
        print("Transcript:", data.get("transcript"))

    @connection.on(LiveEvents.Error)
    def on_error(error):
        print("Streaming error:", error)

    @connection.on(LiveEvents.Disconnect)
    def on_disconnect():
        print("Disconnected from streaming service")

    connection.connect()
    print("Connected to streaming service")

    with open(file_path, "rb") as audio_file:
        try:
            while True:
                chunk = audio_file.read(4096)
                if not chunk:
                    break
                connection.send(chunk)
        except Exception as error:
            print("File read error:", error)
        finally:
            connection.disconnect()
```
