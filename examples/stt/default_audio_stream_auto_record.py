import asyncio
import signal
import logging
import colorlog
import sys

from aiola_stt import AiolaSttClient, AiolaConfig, AiolaQueryParams


# Configure root logger first
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove all existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Set up logging with colors
default_handler = colorlog.StreamHandler()
default_handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

# Custom formatter for transcript and events
transcript_handler = colorlog.StreamHandler()
transcript_handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(message)s',
    log_colors={
        'INFO': 'yellow',  # Yellow for transcript
    }
))

# Custom formatter for events
events_handler = colorlog.StreamHandler()
events_handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(message)s',
    log_colors={
        'INFO': 'blue',  # Blue for events
    }
))

# Add default handler to root logger
root_logger.addHandler(default_handler)

# Configure specific loggers
for logger_name in ["tts-builtin-mic-streaming", "asyncio"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # Add our colored handler
    logger.addHandler(default_handler)
    # Prevent propagation to root logger
    logger.propagate = False

# Get our main logger
logger = logging.getLogger("tts-builtin-mic-streaming")

# Create custom loggers for transcript and events
transcript_logger = logging.getLogger("transcript")
transcript_logger.setLevel(logging.INFO)
transcript_logger.addHandler(transcript_handler)
transcript_logger.propagate = False

events_logger = logging.getLogger("events")
events_logger.setLevel(logging.INFO)
events_logger.addHandler(events_handler)  # Use the blue handler
events_logger.propagate = False

def on_connect(transport):
    """Handle socket connection event."""
    if isinstance(transport, str):
        logger.info("Connection established with %s", transport)
    else:
        logger.info("Connection established")


def on_disconnect():
    """Handle socket disconnection event."""
    logger.info("Connection closed")


def on_transcript(data):
    """Handle transcript data event."""
    transcript_logger.info("Transcript: %s", data.get('transcript'))


def on_events(data):
    """Handle general events."""
    events_logger.info("Events: %s", data)


def on_error(error):
    """Handle error events."""
    logger.error("Error: %s", error)


async def main():
    """Main function to run the streaming example."""
    logger.info("Starting main application")
    
    # Prompt for keywords
    keywords_input = input("Enter keywords to spot (comma-separated): ")
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    
    execution_id_example = "1t2e3m4p" # example execution id, please replace with your own generated one
    api_key = "qLDczk3BESZt2vcU1Tqqb1sSJ9DjsKYGygKdRPhLSg0p" #Playground token - Limited usage!!
    config = AiolaConfig(
        api_key=api_key,
        query_params=AiolaQueryParams(
            execution_id=execution_id_example,  # Required field, 4 to 24 characters long and contains only letters and numbers
        ),
      
        events={
            "on_connect": on_connect,
            "on_disconnect": on_disconnect,
            "on_transcript": on_transcript,
            "on_events": on_events,
            "on_error": on_error
        }
    )

    logger.info("Creating AiolaSttClient instance")
    client = AiolaSttClient(config)

    # Create an event to signal when to stop
    stop_event = asyncio.Event()

    logger.info("Creating streaming task with auto_record=True")
    # Create a task for the streaming
    await client.connect(auto_record=True)
    
    # Set keywords after connection is established
    if keywords:
        logger.info("Setting keywords: %s", keywords)
        await client.set_keywords(keywords)

    logger.info("Application is running. Press Ctrl+C to exit.")

    # Handle SIGINT to gracefully close resources
    def signal_handler():
        logger.info("Signal handler triggered")
        logger.info("Stopping streaming...")
        # Create a task to handle the disconnect
        asyncio.create_task(handle_disconnect())

    async def handle_disconnect():
        logger.info("Handling disconnect")
        await client.disconnect()
        stop_event.set()
            
    # Register signal handler
    loop = asyncio.get_event_loop()
    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

    try:
        logger.info("Microphone is recording 🎤... (🛑Press Ctrl+C to exit)")
        # Wait for either the streaming task to complete or the stop event
        try:
            # Create a task that will run until the stop event is set
            await stop_event.wait()
            logger.info("Stop event received, cleaning up...")
        except asyncio.CancelledError:
            logger.info("Task was cancelled")
            # This is expected during shutdown
            pass

    except Exception as e:
        logger.error("Error during streaming: %s", e)
    finally:
        # Ensure we disconnect properly
        try:
            logger.info("Cleaning up socket in finally block")
            await client.disconnect()
        except Exception as e:
            logger.error("Error during disconnect: %s", e)


if __name__ == "__main__":
    logger.info("Starting application")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        # This is expected when user presses Ctrl+C
        pass
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise
