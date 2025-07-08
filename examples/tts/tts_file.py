import os
from aiola import AiolaClient

AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")


def main():
    client = AiolaClient(api_key=AIOLA_API_KEY)

    response = client.tts.synthesize(
        text="Hello, how can I help you today?", voice="jess", language="en"
    )

    with open("audio.wav", "wb") as f:
        for chunk in response:
            f.write(chunk)


if __name__ == "__main__":
    main()
