import os
from aiola import AiolaClient

AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")

def main():
    client = AiolaClient(api_key=AIOLA_API_KEY)

    file_path = os.path.join(os.path.dirname(__file__), "..", "assets", "sample-en.wav")
    
    # Transcribe an audio file
    with open(file_path, "rb") as audio_file:
        result = client.stt.transcribe_file(
            file=audio_file,
            language="en",
        )

    print(result)


if __name__ == "__main__":
    main() 