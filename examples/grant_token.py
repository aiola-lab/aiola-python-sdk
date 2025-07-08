import os
import pathlib
from aiola import AiolaClient

def grant_token():
  api_key = os.getenv("AIOLA_API_KEY")

  try:
    # Generate a temporary token from an API key.
    access_token = AiolaClient.grant_token(api_key=api_key)
    
    print(f"Token: {access_token[:50]}...")

    # Create a client with the temporary token.
    client = AiolaClient(access_token=access_token)

    print("Client created successfully with access token")

    file_path = pathlib.Path(__file__).parent / "stt" / "audio.wav"
    with open(file_path, "rb") as file:
      result = client.stt.transcribe_file(file=file)
      print(result)

  except Exception as e:
    print(f"Error: {e}")


grant_token()