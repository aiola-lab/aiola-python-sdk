```python
from aiola_tts import AiolaTtsClient, AudioFormat

client = AiolaTtsClient(
    bearer_token="<API-KEY>",
    audio_format=AudioFormat.LINEAR16
)
audio = client.synthesize("Hello world", voice="af_bella")
with open("output.wav", "wb") as f:
    f.write(audio)
```