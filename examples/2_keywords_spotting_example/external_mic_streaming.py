import asyncio
import signal
import json
from threading import Event
from aiola_streaming_sdk.client import AiolaStreamingClient
from aiola_streaming_sdk.models.config import StreamingConfig
from recorder_app import RecorderApp

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
    namespace= "/events"
    bearer_token = '< your-bearer-token >'

    config = StreamingConfig(
        endpoint="< your-api-base-url >",
        auth_type="Bearer",
        auth_credentials={"token": bearer_token},
        flow_id="<your-flow-id>",
        namespace= "/events",
        transports='polling',
        execution_id="<your-execution-id>",
        use_buildin_mic=False,
        lang_code="en_US",
        time_zone="UTC",
        callbacks=dict(
            on_transcript=on_transcript,
            on_error=on_error,
            on_events=on_events,
            on_connect=lambda: on_connect(client, namespace),
            on_disconnect=on_disconnect
        )
    )

    # Create SDK client
    client = AiolaStreamingClient(config)

    await client.start_streaming()

    # Define a recording application
    recorder_app = RecorderApp(client, on_stream_error)

    # Start the recorder asynchronously
    recorder_app.start_streaming()

    print("Application is running. Press Ctrl+C to exit.")

    # Handle SIGINT to gracefully close resources
    loop = asyncio.get_event_loop()

    def signal_handler():
        print("\nStopping recording")
        recorder_app.close_audio_streaming()
        print("Closing real-time transcript connection")
        loop.stop()

    # Register signal handler
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Keep the event loop running until stopped
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())