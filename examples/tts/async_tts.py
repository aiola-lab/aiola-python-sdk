import asyncio
import os
from aiola import AsyncAiolaClient

async def create_audio_file():
    try:
        # Step 1: Generate access token
        result = await AsyncAiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        # Step 2: Create client
        client = AsyncAiolaClient(
            access_token=result.access_token
        )

        # Step 3: Generate audio
        audio = client.tts.synthesize(
            text='Hello, how can I help you today?',
            voice='jess',
            language='en'
        )

        file_path = os.path.join(os.path.dirname(__file__), "async_audio.wav")

        with open(file_path, 'wb') as f:
            async for chunk in audio:
                f.write(chunk)

        print('Audio file created successfully')
        print(f"✅ Audio file saved: {file_path}")

    except Exception as error:
        print('Error creating audio file:', error)

async def stream_tts():
    try:
        # Step 1: Generate access token
        result = await AsyncAiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )

        # Step 2: Create client
        client = AsyncAiolaClient(
            access_token=result.access_token
        )

        # Step 3: Stream audio
        stream = client.tts.stream(
            text='Hello, how can I help you today?',
            voice='jess',
            language='en'
        )

        audio_chunks = []
        async for chunk in stream:
            audio_chunks.append(chunk)

        print('Audio chunks received:', len(audio_chunks))

    except Exception as error:
        print('Error streaming TTS:', error)

async def main():
    print("=== Async TTS Examples ===")

    await create_audio_file()
    print()
    await stream_tts()

    print("\n=== Examples Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
