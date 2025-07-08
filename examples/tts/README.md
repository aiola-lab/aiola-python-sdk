# Text-to-Speech (TTS) Examples

This directory contains examples demonstrating how to use the aiOla SDK for text-to-speech functionality.

## Quick start

<!--snippet;tts;quickstart-->
```python
import os
from aiola import AiolaClient

AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")

client = AiolaClient(api_key=AIOLA_API_KEY)

def synthesize_to_file():
    audio_stream = client.tts.synthesize(
        text="Hello, how can I help you today?",
        voice="jess",
        language="en",
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
        language="en",
    )
    
    # Collect audio chunks
    audio_chunks = []
    for chunk in stream:
        audio_chunks.append(chunk)
    
    # Process chunks as needed (e.g., play audio, save to buffer, etc.)
    print(f"Collected {len(audio_chunks)} audio chunks")
``` 