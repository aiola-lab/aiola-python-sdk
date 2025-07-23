import os
from aiola import AiolaClient

def stream_tts():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )
        
        # Step 2: Create client
        client = AiolaClient(
            access_token=result['accessToken']
        )
        
        # Step 3: Stream audio
        stream = client.tts.stream(
            text='Hello, how can I help you today?',
            voice='jess',
            language='en'
        )

        audio_chunks = []
        for chunk in stream:
            audio_chunks.append(chunk)
        
        print('Audio chunks received:', len(audio_chunks))
        
    except Exception as error:
        print('Error streaming TTS:', error)

if __name__ == "__main__":
    stream_tts()
