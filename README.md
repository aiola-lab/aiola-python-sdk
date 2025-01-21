# aiOla Python SDKs

Welcome to the **aiOla Python SDKs** repository. This repository contains examples and documentation for various SDKs that integrate with aiOla's Text-to-Speech (TTS) and streaming services.

---

## Examples Overview

### aiOla Streaming SDK

#### 1. [Transcript and Events Example](https://github.com/aiola-lab/aiola-python-sdk/blob/dev/examples/1_transcript_events_example/README.md)
This example demonstrates how to use the aiOla Streaming SDK to capture live transcripts and handle backend-triggered events.

- **Key Features**:
  - Real-time transcription.
  - Event-driven callbacks.
  - Internal / External Microphone.

#### 2.[Keyword Spotting Example](https://github.com/aiola-lab/aiola-python-sdk/blob/dev/examples/2_keywords_spotting_example/README.md)

This example shows how to set up keyword spotting using the aiOla Streaming SDK.

- **Key Features**:
  - Spot predefined keywords in live streams.
  - Event-driven keyword matching.
 
#### 3. Supported Languages 
 en-EN, de-DE, fr-FR, zh-ZH, es-ES, pt-PT

---

### aiOla TTS SDK

#### 3. [Synthesize Speech Example](https://github.com/aiola-lab/aiola-python-sdk/blob/dev/examples/3_synthesizeSpeech_example/README.md)
This example demonstrates how to convert text into speech and download the resulting audio file using the aiOla TTS SDK.

- **Key Features**:
  - Converts text into `.wav` audio files.
  - Supports voice selection.

#### 4. [Stream Speech Example](https://github.com/aiola-lab/aiola-python-sdk/blob/dev/examples/4_streamSpeech_example/README.md)
This example shows how to stream text-to-speech in real-time, enabling audio playback before the entire text is processed.

- **Key Features**:
  - Real-time TTS streaming.
  - Immediate audio playback.

---

## Get Started

1. Clone the repository:
   ```bash
   git clone https://github.com/aiola-lab/aiola-python-sdk.git
   cd aiola-python-sdk
   ```
2.	Follow the instructions in the individual example directories for specific use cases.

---

## Installation

To install the SDK, run the following command:

```bash
pip install aiola-python-sdk
```

or locally install the package from the root directory:

create virtual environment:

```bash
python -m venv .venv
```

activate virtual environment:

```bash
source .venv/bin/activate
```

install development dependencies:

```bash
pip install wheel build setuptools
```

Build the package:

```bash
python -m build
```

Install the package:

```bash
pip install -e .
```

---
