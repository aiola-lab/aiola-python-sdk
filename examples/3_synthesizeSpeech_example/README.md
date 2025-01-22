# aiOla TTS Synthesize Speech Example

**Version**: `0.1.0`

This example demonstrates how to use the aiOla TTS SDK to convert text into speech and save the resulting audio as a `.wav` file.

---

## How It Works

- Converts text into a `.wav` audio file using the aiOla TTS `/synthesize` endpoint.
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
   ```

## Usage

1.	Run the example:
   ```bash
   python synthesize_speech_example/demo.py
   ```
2. The output will display:
	- Progress logs for the synthesis process.
	- A success message with the location of the saved .wav file.

## Code Highlights

### Initialize the TTS Client

```python
from aiola_tts_sdk import AiolaTTSClient

tts_url = "<your-api-base-url>/api/tts"
tts_client = AiolaTTSClient(tts_url)
```

### Synthesize Speech
```python
text = "Hello, this is a test of the aiOla TTS synthesis feature."
audio_data = tts_client.synthesize(text, voice="af_bella")
```

### Save Audio to File
```python
def save_audio_file(audio_data: bytes, filename: str):
    with open(filename, "wb") as f:
        f.write(audio_data)
    print(f"Audio saved as {filename}")

save_audio_file(audio_data, "synthesized_audio.wav")
```
