import os
from aiola import AiolaClient

def create_file():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY')
        )
        
        # Step 2: Create client
        client = AiolaClient(
            access_token=result['accessToken']
        )
        
        print(f"Session ID: {result['sessionId']}")
        
        # Step 3: Generate audio
        audio = client.tts.synthesize(
            text='Hello, how can I help you today?',
            voice='jess',
            language='en'
        )

        output_path = os.path.join(os.path.dirname(__file__), "output_audio.wav")
        
        with open(output_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
        
        print('Audio file created successfully')
        print(f"✅ Audio file saved: {output_path}")
        
        # Clean up session
        AiolaClient.close_session(result['accessToken'])
        
    except Exception as error:
        print('Error creating audio file:', error)

if __name__ == "__main__":
    create_file()
