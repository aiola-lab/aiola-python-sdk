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

    bearer_token = "< your-bearer-token >"
    config = StreamingConfig(
        endpoint="< your-api-base-url >",
        auth_type="Bearer",
        auth_credentials={"token": bearer_token},
        flow_id="<your-flow-id>",
        namespace="/events",
        transports="websocket",
        execution_id="<your-execution-id>",
        use_buildin_mic=True,
        callbacks=dict(
            on_transcript=on_transcript,
            on_error=on_error,
            on_events=on_events,
            on_connect=on_connect,
            on_disconnect=on_disconnect,
        ),
        vad_config=dict(vad_threshold=0.5, min_silence_duration_ms=250),
    )

    client = AiolaStreamingClient(config)

    await client.start_streaming()

    print("Application is running. Press Ctrl+C to exit.")

    # Handle SIGINT to gracefully close resources
    loop = asyncio.get_event_loop()

    def signal_handler():
        print("Closing real-time transcript connection")
        loop.stop()

    # Register signal handler
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Keep the event loop running until stopped
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
