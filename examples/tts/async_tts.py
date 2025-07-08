import asyncio
import os
from aiola import AsyncAiolaClient
from io import BytesIO

AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")


async def create_audio_file():
    client = AsyncAiolaClient(api_key=AIOLA_API_KEY)

    response = client.tts.synthesize(
        text="Hello, how can I help you today?", voice="jess", language="en"
    )

    file_path = os.path.join(os.path.dirname(__file__), "audio.wav")
    with open(file_path, "wb") as f:
        async for chunk in response:
            f.write(chunk)


async def stream_tts():
    client = AsyncAiolaClient(api_key=AIOLA_API_KEY)

    response = client.tts.stream(
        text="Hello, how can I help you today?", voice="jess", language="en"
    )

    audio = BytesIO()
    async for chunk in response:
        audio.write(chunk)


if __name__ == "__main__":
    asyncio.run(create_audio_file())
    # asyncio.run(stream_tts())
