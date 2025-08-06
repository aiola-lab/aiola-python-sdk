# Speech-to-Text (STT) Examples

This directory contains examples demonstrating how to use the aiOla SDK for speech-to-text functionality.

## Quick start

<!--snippet;stt;quickstart-->
```python
# pip install aiola
from aiola import AiolaClient

# Step 1: Set up authentication
result = AiolaClient.grant_token(api_key='your-api-key-here')
access_token = result.access_token

# Step 2: Create a client
client = AiolaClient(access_token=access_token)

# Step 3: Transcribe audio from a file
try:
    with open('path/to/your/audio.wav', 'rb') as audio_file:
        transcript = client.stt.transcribe_file(
            file=audio_file,
            language='en',
            keywords={
                "postgres": "PostgreSQL",
                "k eight s": "Kubernetes"
            }
        )

    print("Transcription:", transcript)

except Exception as e:
    print(f"Error: {e}")
```
