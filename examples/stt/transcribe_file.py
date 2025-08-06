import os
from aiola import AiolaClient

def transcribe_file():
    try:
        # Step 1: Generate access token
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY') or "YOUR_API_KEY"
        )

        # Step 2: Create client
        client = AiolaClient(
            access_token=result.access_token
        )

        # Step 3: Transcribe file
        file_path = os.path.join(os.path.dirname(__file__), "..", "assets", "tales-of-shmulik-kipod-22050-stereo.mp3")
        print("file_path", file_path)

        with open(file_path, "rb") as audio_file:
            transcript = client.stt.transcribe_file(
                file=audio_file,
                language="en",
                keywords={'shmu lik':'shmulik', 'khipod':'kipod'}
            )

        print('Transcript:', transcript)

    except Exception as error:
        print('Error transcribing file:', error)

if __name__ == "__main__":
    transcribe_file()
