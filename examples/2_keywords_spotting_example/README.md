# Aiola Streaming SDK

**Version**: `0.1.0`  
**Description**: A Python SDK for interacting with the Aiola Streaming Service, enabling real-time audio streaming and processing.

---

## Features

- **Real-Time Audio Streaming**: Stream audio to the Aiola service with configurable settings.
- **Built-in and External Microphone Support**: Choose between built-in and external microphones for streaming.
- **Customizable Audio Configuration**: Define sample rate, channels, and chunk size for your audio streams.
- **Type Safety**: Developed in TypeScript with type definitions for all core components.

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

## Requirements

- **Python**: Version 3.8 or higher
- **Dependencies**:
  - `pydantic`
  - `python-socketio`
  - `aiohttp`

---

## What in the Project

- **`aiola_streaming_sdk`**: Core SDK logic for connecting and interacting with Aiola’s API.
- **`recorder_app`**: Handles audio streaming configuration and recording logic.

### Examples

- **`buildin_mic_streaming.py`**: Example of streaming audio from a built-in microphone.
- **`external_mic_streaming.py`**: Example of streaming audio from an external microphone.
---

## Audio Configuration

The `recorder_app` uses a configurable schema defined as follows:

| Property     | Type    | Default  | Description                              |
|--------------|---------|----------|------------------------------------------|
| `sample_rate` | `number`| `16000`  | Sample rate in Hz                        |
| `channels`   | `number`| `1`      | Number of audio channels (Mono = 1)      |
| `chunk_size`  | `number`| `4096`   | Size of each audio chunk in bytes        |
| `dtype`      | `string`| `'int16'`| Data type for audio samples              |

---

<br><br>


# Example Application: Using the SDK and RecorderApp

## External Microphone Streaming with Keyword Spotting:
This example demonstrates how to stream audio from an **external microphone** and leverage **keyword spotting**. The configuration may require selecting a specific audio device depending on the system setup.

```python
import asyncio
import signal
import json
from threading import Event
from aiola_streaming_sdk import AiolaStreamingClient, StreamingConfig

def on_connect(client, namespace):
    print("Connection established")

    kws_list = ["aiola", "ngnix"]
    binary_data = json.dumps(kws_list).encode('utf-8')
    print(f'kws_list: {kws_list}')

    client.sio.emit("set_keywords", binary_data, namespace=namespace)

def on_disconnect(duration, total_audio):
    print(f"Connection closed. Duration: {duration}ms, Total audio: {total_audio}ms")

def on_transcript(data):
    print(f"Transcript received: {data.get('transcript')}")

def on_events(data):
    print(f"Events received: {json.dumps(data, indent=2)}")

def on_error(data):
    print("Error occurred:", data)

def on_stream_error(data):
    print("Stream Error received:", data)

# Create an event to keep the application running
exit_event = Event()

async def main():
    # Define the SDK configurations
    bearer_token = '< your-bearer-token >'
    namespace= "/events"

    config = StreamingConfig(
        endpoint=`<endpoint>`,    # The URL of the Aiola server
        auth_type="Bearer",    # Supported authentication for the API
        auth_credentials={"token": `<your_bearer_token_here>`}, # The Bearer token, obtained upon registration with Aiola },
        flow_id=`<flow_id_here>`, # One of the IDs from the flows created for the user
        namespace= "/events",     # Namespace for subscription: /transcript (for transcription) or /events (for transcription + LLM solution)
        transports='polling',   # Communication method: ['websocket'] for L4 or ['polling'] for L7
        execution_id="1",         # Unique identifier to trace execution
        use_buildin_mic=False,     # Indicate to use the SDK mic
        lang_code="en_US",
        time_zone="UTC",
        callbacks=dict(
            on_transcript=on_transcript, # Callback for transcript data
            on_error=on_error,           # Callback for handling errors
            on_events=on_events,         # Callback for event-related data
            on_connect=lambda: on_connect(client, namespace),       # Callback for connection establishment
            on_disconnect=on_disconnect  # Callback for connection termination
        )
    )

    # Create SDK client
    client = AiolaStreamingClient(config)

    # Start the SDK streaming
    await client.start_streaming()

    # Define a recording application
    recorder_app = RecorderApp(client, on_stream_error)

    # Start the recorder asynchronously
    recorder_app.start_streaming()

    ...
```


### Explanation of Configuration Parameters

| Parameter	                  | Type	     | Description                                                                                                                          |
|-----------------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------|
| `endpoint`	              | `string`     | The base URL of the Aiola server                                                                                                     |
| `authType`	              | `string`     | The authentication type, currently supporting "Bearer".                                                                           |
| `authCredentials` 	      | `object`     | An object containing credentials required for authentication.                                                                        |
| `authCredentials.token`   |	`string`     | The Bearer token, obtained during registration with Aiola.                                                                                |
| `flowId`	                  |	`string`     | A unique identifier for the specific flow created for the user.                                                                      |
| `namespace`	              |	`string`     | The namespace to subscribe to. Use /transcript for transcription or /events for transcription + LLM integration.                     |
| `transports`	              |	`string[]`   | The communication method. Use ['websocket'] for Layer 4 (faster, low-level) or ['polling'] for Layer 7 (supports HTTP2, WAF, etc.).  |
| `executionId`	              |	`string`     | A unique identifier to trace the execution of the session. Defaults to "1".                                                          |
| `useBuildinMic`             | `bool`       | Indicate if to use the built-in mic listner inside the SDK or to use external one. (by default: `False` )                            |
| `langCode`	              |	`string`	 | The language code for transcription. For example, "en_US" for US English.                                                            |
| `timeZone`	              |	`string`	 | The time zone for aligning timestamps. Use "UTC" or any valid IANA time zone identifier.                                             |
| `callbacks`	              |	`object`	 | An object containing the event handlers (callbacks) for managing real-time data and connection states                                |

<br>

### Keyword Spotting

This example introduces Keyword Spotting functionality:
-	**How It Works**:
    1.	During the on_connect event, keywords are set dynamically using client.sio.emit("set_keywords", ...). The connection must be open
    2.	These keywords trigger real-time detection when encountered in the streamed audio.
-	**Setting Keywords**:

    ```python
    kws_list = ["aiola", "ngnix"]
    binary_data = json.dumps(kws_list).encode('utf-8')
    client.sio.emit("set_keywords", binary_data, namespace=namespace)
    ```
---

<br>

### Supported Callbacks

| Callback	| Description |
|-----------|-------------|
|`onTranscript` |	Invoked when a transcript is received from the Aiola server. |
|`onError` |	Triggered when an error occurs during the streaming session. |
|`onEvents` |	Called when events (e.g., LLM responses or processing events) are received. |
|`onConnect` |	Fired when the connection to the Aiola server is successfully established. |
|`onDisconnect` |	Fired when the connection to the server is terminated. Includes session details such as duration and total audio streamed. |

---

### How It Works

1.	Endpoint:
    -	This is the base URL of the Aiola server where the client will connect.
2.	Authentication:
    -	The SDK uses Bearer for authentication. The Bearer token must be obtained during registration with Aiola.
3.	Namespace:
    -	Determines the type of data you want to subscribe to:
    -	`/transcript`: For transcription data only.
    -	`/events`: For transcription combined with LLM solution events.
4.	Transport Methods:
    -	Choose between:
        -	`'websocket'`: For **Layer 4** communication with lower latency.
        -	`'polling'`: For **Layer 7** communication, useful for environments with firewalls or HTTP2 support.
5.	Callbacks:
    -	These are functions provided by the user to handle various types of events or data received during the streaming session.
6.	Execution ID:
    -	Useful for tracing specific execution flows or debugging sessions.
7.	Language Code and Time Zone:
    -	Ensure the transcription aligns with the required language and time zone.