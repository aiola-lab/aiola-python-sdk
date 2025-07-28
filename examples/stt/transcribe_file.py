import os
from aiola import AiolaClient

def transcribe_file():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key="ak_d7715b8690531b83f0e03c56c50503465ef7bcf9156991d286c156746e4db110"
        )
        
        # Step 2: Create client
        client = AiolaClient(
            access_token=result['accessToken'],
            timeout=1000
        )
        
        # Step 3: Transcribe file
        file_path = os.path.join(os.path.dirname(__file__), "..", "assets", "sample-en.wav")
        with open(file_path, "rb") as audio_file:
            transcript = client.stt.transcribe_file(
                file=audio_file,
                language="en"
            )

        print('Transcript:', transcript)
        
    except Exception as error:
        print('Error transcribing file:', error)

if __name__ == "__main__":
    transcribe_file() 