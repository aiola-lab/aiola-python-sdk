import asyncio
import signal
import json
from threading import Event
from aiola_streaming_sdk.client import AiolaStreamingClient
from aiola_streaming_sdk.models.config import StreamingConfig
from recorder_app import RecorderApp

def on_connect():
    print("Connection established")

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
    bearer_token = 'BdGVzbGFpbGFubXVzawodGVzbGFpbGFubXVzawo=pbGFubXVz'
    config = StreamingConfig(
        endpoint="https://tesla.internal.aiola.ai",
        auth_type="Bearer",
        auth_credentials={"token": bearer_token},
        flow_id="f38d5001-3b42-405f-b4e3-6caddce456c3",
        namespace= "/events",
        transports='polling',
        execution_id="19990",
        use_buildin_mic = False,
        lang_code="en_US",
        time_zone="UTC",
        callbacks=dict(
            on_transcript=on_transcript,
            on_error=on_error,
            on_events=on_events,
            on_connect=on_connect,
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