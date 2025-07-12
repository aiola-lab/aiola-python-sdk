# Speech-to-Text (STT) Examples

This directory contains examples demonstrating how to use the aiOla SDK for speech-to-text functionality.

## Quick start

<!--snippet;stt;quickstart-->
```python
import os
import pyaudio # pip install pyaudio, for mic stream
from aiola import AiolaClient
from aiola.types import LiveEvents

AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")

client = AiolaClient(api_key=AIOLA_API_KEY)

# Transcribe an audio file to text
def transcribe_file():
    with open("path/to/your/audio.wav", "rb") as audio_file:
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
        print("transcript", data)

    @connection.on(LiveEvents.Error)
    def on_error(data):
        print("error", data)

    @connection.on(LiveEvents.Disconnect)
    def on_disconnect():
        print("disconnected")

    @connection.on(LiveEvents.Connect)
    def on_connect():
        print("Connected to streaming service")

    connection.connect()

    try:
        # Capture audio from microphone
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096,
        )

        # Send audio data to streaming service, wait until finished
        while True:
            audio_data = stream.read(4096)
            connection.send(audio_data)
    except KeyboardInterrupt:
        print("Stopping audio capture...")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        connection.disconnect()

if __name__ == "__main__":
    transcribe_file()
    # live_streaming()
```
