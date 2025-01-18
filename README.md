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
npm install aiola-python-sdk
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

## Example 1: Built-in Microphone Streaming
This example demonstrates how to stream audio from the **built-in microphone** to the Aiola service. The application connects to the Aiola API, streams audio data, and receives real-time transcripts and events.

```python
import asyncio
import signal
from aiola_streaming_sdk import AiolaStreamingClient, StreamingConfig

def on_connect():
    print(f"Connection established")

def on_disconnect():
    print(f"Connection closed")

def on_transcript(data):
    print(f"Transcript received: {data.get('transcript')}")

def on_events(data):
    print(f"Events received: {data}")

def on_error(data):
    print(f"Error occurred: {data}")

async def main():

    # 
    config = StreamingConfig(
        endpoint=`<endpoint>`,    # The URL of the Aiola server
        auth_type="x-api-key",    # Supported authentication for the API
        auth_credentials={"api_key": `<your_api_key_here>`}, # API key, obtained upon registration with Aiola },
        flow_id=`<flow_id_here>`, # One of the IDs from the flows created for the user
        namespace= "/events",     # Namespace for subscription: /transcript (for transcription) or /events (for transcription + LLM solution)
        transports=['polling'],   # Communication method: ['websocket'] for L4 or ['polling'] for L7
        execution_id="1",         # Unique identifier to trace execution
        use_buildin_mic=True,     # Indicate to use the SDK mic
        callbacks=dict(
            on_transcript=on_transcript, # Callback for transcript data
            on_error=on_error,           # Callback for handling errors
            on_events=on_events,         # Callback for event-related data
            on_connect=on_connect,       # Callback for connection establishment
            on_disconnect=on_disconnect  # Callback for connection termination
        )
    )

    # Create a SDK client
    client = AiolaStreamingClient(config)
    
    # Start the SDK streaming
    await client.start_streaming()

    ...
```

## Example 2: External Microphone Streaming
This example demonstrates how to stream audio from an **external microphone**. The configuration may require selecting a specific audio device depending on the system setup.

```python
import asyncio
import signal
from aiola_streaming_sdk import AiolaStreamingClient, StreamingConfig

def on_connect():
    print(f"Connection established")

def on_disconnect():
    print(f"Connection closed")

def on_transcript(data):
    print(f"Transcript received: {data.get('transcript')}")

def on_events(data):
    print(f"Events received: {data}")

def on_error(data):
    print(f"Error occurred: {data}")

async def main():

    # 
    config = StreamingConfig(
        endpoint=`<endpoint>`,    # The URL of the Aiola server
        auth_type="x-api-key",    # Supported authentication for the API
        auth_credentials={"api_key": `<your_api_key_here>`}, # API key, obtained upon registration with Aiola },
        flow_id=`<flow_id_here>`, # One of the IDs from the flows created for the user
        namespace= "/events",     # Namespace for subscription: /transcript (for transcription) or /events (for transcription + LLM solution)
        transports=['polling'],   # Communication method: ['websocket'] for L4 or ['polling'] for L7
        execution_id="1",         # Unique identifier to trace execution
        use_buildin_mic=True,     # Indicate to use the SDK mic
        callbacks=dict(
            on_transcript=on_transcript, # Callback for transcript data
            on_error=on_error,           # Callback for handling errors
            on_events=on_events,         # Callback for event-related data
            on_connect=on_connect,       # Callback for connection establishment
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
| `authType`	              | `string`     | The authentication type, currently supporting "x-api-key".                                                                           |
| `authCredentials` 	      | `object`     | An object containing credentials required for authentication.                                                                        |
| `authCredentials.api_key`   |	`string`     | The API key, obtained during registration with Aiola.                                                                                |
| `flowId`	                  |	`string`     | A unique identifier for the specific flow created for the user.                                                                      |
| `namespace`	              |	`string`     | The namespace to subscribe to. Use /transcript for transcription or /events for transcription + LLM integration.                     |
| `transports`	              |	`string[]`   | The communication method. Use ['websocket'] for Layer 4 (faster, low-level) or ['polling'] for Layer 7 (supports HTTP2, WAF, etc.).  |
| `executionId`	              |	`string`     | A unique identifier to trace the execution of the session. Defaults to "1".                                                          |
| `useBuildinMic`             | `bool`       | Indicate if to use the built-in mic listner inside the SDK or to use external one. (by default: `False` )                            |
| `langCode`	              |	`string`	 | The language code for transcription. For example, "en_US" for US English.                                                            |
| `timeZone`	              |	`string`	 | The time zone for aligning timestamps. Use "UTC" or any valid IANA time zone identifier.                                             |
| `callbacks`	              |	`object`	 | An object containing the event handlers (callbacks) for managing real-time data and connection states                                |

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
    -	The SDK uses x-api-key for authentication. The API key must be obtained during registration with Aiola.
3.	Namespace:
    -	Determines the type of data you want to subscribe to:
    -	`/transcript`: For transcription data only.
    -	`/events`: For transcription combined with LLM solution events.
4.	Transport Methods:
    -	Choose between:
        -	`['websocket']`: For **Layer 4** communication with lower latency.
        -	`['polling']`: For **Layer 7** communication, useful for environments with firewalls or HTTP2 support.
5.	Callbacks:
    -	These are functions provided by the user to handle various types of events or data received during the streaming session.
6.	Execution ID:
    -	Useful for tracing specific execution flows or debugging sessions.
7.	Language Code and Time Zone:
    -	Ensure the transcription aligns with the required language and time zone.