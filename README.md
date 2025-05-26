# aiOla Python SDKs

This repository contains Python SDKs for aiOla's Text-to-Speech (TTS) and Speech-to-Text (STT) services.

## TL;DR - Demo

Want to try out the playground? Just clone and run:

`. ./scripts/build_examples.sh `

https://github.com/user-attachments/assets/45319b52-3748-4b61-8127-adcaed96a64d


## SDKs

- [aiola-tts](libs/text_to_speech/aiola_tts/README.md): Text-to-Speech SDK
- [aiola-stt](libs/speech_to_text/aiola_stt/README.md): Speech-to-Text SDK

## Installation

```bash
pip install aiola-tts
pip install aiola-stt
```

## Quick Examples

### Text-to-Speech

```python
    from aiola_tts import AiolaTtsClient
    client = AiolaTtsClient(bearer_token="YOUR_TOKEN")
    audio = client.synthesize("Hello world")
```

### Speech-to-Text

```python
    from aiola_stt import AiolaSttClient, AiolaConfig, AiolaQueryParams
    config = AiolaConfig(api_key="YOUR_KEY", query_params=AiolaQueryParams(execution_id="YOUR_GENERATED_ID"))
    client = AiolaSttClient(config)
    await client.connect(auto_record=True)
```

## Features

| Speech-to-Text (STT)                                      | Text-to-Speech (TTS)                                  |
|:----------------------------------------------------------|:------------------------------------------------------|
| Real-time speech transcription                            | Convert text to speech and save as WAV files          |
| File Transcription (mp4, mp3 & wav)                       | Real-time streaming of synthesized speech             |
| Keyword spotting                                          | Multiple voice options available                      |
| Voice Activity Detection (VAD)                            | Support for different audio formats (LINEAR16, PCM)   |
| Support for custom audio streams                          |                                                      |
| Event-driven architecture                                 |                                                      |
| Multiple language support (en-US, de-DE, fr-FR, zh-ZH, es-ES, pt-PT) |                                                      |


## License

MIT License
