import os
from aiola import AiolaClient
from io import BytesIO

AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")


def main():
    client = AiolaClient(api_key=AIOLA_API_KEY)

    response = client.tts.stream(text="Hello, world!", voice="jess", language="en")

    audio = BytesIO()

    for chunk in response:
        audio.write(chunk)


if __name__ == "__main__":
    main()
