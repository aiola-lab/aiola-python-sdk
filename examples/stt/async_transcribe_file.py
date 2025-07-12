import asyncio
import os
from aiola import AsyncAiolaClient

AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")


async def main():
    client = AsyncAiolaClient(api_key=AIOLA_API_KEY)

    # Transcribe an audio file asynchronously
    file_path = os.path.join(os.path.dirname(__file__), "..", "assets", "sample-en.wav")
    with open(file_path, "rb") as audio_file:
        result = await client.stt.transcribe_file(
            file=audio_file,
            language="en"
        )

    print(result)


if __name__ == "__main__":
    asyncio.run(main()) 