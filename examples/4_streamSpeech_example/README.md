# aiOla TTS Stream Speech Example

**Version**: `0.1.0`

This example demonstrates how to use the aiOla TTS SDK to convert text into speech and save the resulting audio as a `.wav` file.

---

## How It Works

- Streams text-to-speech audio using the aiOla TTS `/synthesize/stream` endpoint.
- Allows voice selection for speech synthesis.
- Saves the synthesized audio locally for playback or further processing.

---

## Prerequisites

- **Python**: Version 3.7 or higher.
- **aiOla TTS SDK**: Ensure the SDK is installed and properly configured.

---

## Setup

1.	Clone the repository and navigate to the example directory.
2.	Update the baseUrl and ensure the API endpoint is correct:
   ```javascript
   tts_url = "<your-api-base-url>/api/tts" // Replace with your API base URL
   bearer_token = "<your-bearer-token>"  // Replace with your Bearer token
   ```

## Usage

1.	Run the example:
   ```bash
   python stream_speech_example/demo.py
   ```
2. The output will display:
	- Progress logs for the synthesis process.
	- A success message with the location of the saved .wav file.

## Code Highlights

### Initialize the TTS Client

```python
from aiola_tts_sdk import AiolaTTSClient

tts_url = "<your-api-base-url>/api/tts"
bearer_token = "<your-bearer-token>"
tts_client = AiolaTTSClient(base_url=tts_url, bearer_token=bearer_token)
```

# Audio Format Options

The SDK supports multiple audio formats for the synthesized speech. You can specify the format when initializing the client:

```python
tts_client = AiolaTTSClient(base_url=tts_url, bearer_token=bearer_token, audio_format="LINEAR16")
```

Supported formats:
- LINEAR16
- PCM
- MULAW

### Stream Speech
```python
stream_data = tts_client.synthesize_stream("Streaming aiOla speech", voice="af_bella")
```

### Save Audio to File
```python
def save_audio_file(audio_data: bytes, filename: str):
    with open(filename, "wb") as f:
        f.write(audio_data)
    print(f"Audio saved as {filename}")

save_audio_file(stream_data, "streamed_audio.wav")
```
