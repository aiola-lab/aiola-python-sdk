import asyncio
import os
import time
import logging
import colorlog
from aiola_stt.client import AiolaSttClient
from aiola_stt.config import AiolaConfig, AiolaQueryParams, VadConfig
from aiola_stt.errors import AiolaError
import sys

# Set up logger with colors
logger = logging.getLogger('aiola_stt')
logger.setLevel(logging.INFO)

# Remove all existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
    
# Create console handler with colors
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))
logger.addHandler(handler)


logger.setLevel(logging.INFO)
logger.info("Starting Aiola STT transcription example")
for handler in logger.handlers:
    handler.flush()
    
# Configure specific loggers
for logger_name in ["tts-custom-audio-stream", "asyncio"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # Add our colored handler
    logger.addHandler(handler)
    # Prevent propagation to root logger
    logger.propagate = False

start_time = None

def on_file_transcript(file_path):
    global start_time
    end_time = time.time()
    duration = end_time - start_time
    logger.info("Transcription completed in %.2f seconds", duration)
    logger.info("Transcription written to: %s", file_path)

def on_error(error: AiolaError):
    logger.error("Error: %s", error)

async def main():
    global start_time
    logger.info("Starting main function")
    sys.stdout.flush()
    # Replace with your actual API key and execution_id
    execution_id = "1t2e3m4p" # example execution id, please replace with your own generated one
    api_key = "jgDq2p1zLkY3kLWpU76jSK7KmxcODni46thGUboORJQk" #Playground token - Limited usage!!
    
    # Get file path from user input
    file_path = input("Please enter the path to your audio file (wav, mp3, or mp4): ").strip()
    if not os.path.exists(file_path):
        logger.error("Error: File '%s' does not exist", file_path)
        return
        
    output_transcript_file_path = "example_output/transcript.txt"
    config = AiolaConfig(
        api_key=api_key,
        query_params=AiolaQueryParams(execution_id=execution_id, flow_id = "8c301855-0ad3-4292-a2fa-847084dfca25"),
        events={
            "on_error": on_error,
            "on_file_transcript": on_file_transcript
        },
        vad_config=VadConfig(
            vad_threshold=0.5,
            min_silence_duration_ms=400
        )
    )
    client = AiolaSttClient(config)
    logger.info("Creating AiolaSttClient instance")
    await client.set_keywords(['Shmulik', 'Kipod'])
    start_time = time.time()
    logger.info("Starting transcription...")
    for i in range(13):
        logger.info("Starting transcription iteration %d/13", i + 1)
        await client.transcribe_file(file_path, output_transcript_file_path+f"_{i}.txt")
        logger.info("Completed transcription iteration %d/13", i + 1)

if __name__ == "__main__":
    asyncio.run(main()) 