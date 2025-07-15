import asyncio
import os
from aiola import AsyncAiolaClient

async def transcribe_file():
    try:
        # Step 1: Generate access token
        result = await AsyncAiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )
        
        # Step 2: Create client
        client = AsyncAiolaClient(
            access_token=result['accessToken']
        )
        
        # Step 3: Transcribe file
        file_path = os.path.join(os.path.dirname(__file__), "..", "assets", "sample-en.wav")
        with open(file_path, "rb") as audio_file:
            transcript = await client.stt.transcribe_file(
                file=audio_file,
                language="en"
            )

        print('Transcript:', transcript)
        
    except Exception as error:
        print('Error transcribing file:', error)

if __name__ == "__main__":
    asyncio.run(transcribe_file()) 