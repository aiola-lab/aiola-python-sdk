import os
import pyaudio
from aiola import AiolaClient
from aiola.clients.stt.types import LiveEvents


AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")

# Audio parameters
FORMAT = pyaudio.paInt16  # 16-bit integers
CHANNELS = 1  # Mono audio
RATE = 16000  # Sample rate (samples per second)
CHUNK = 4096  # Number of frames per buffer


def main():
    client = AiolaClient(api_key=AIOLA_API_KEY)

    connection = client.stt.stream(
        lang_code="en",
        keywords={
            "aiola": "aiOla",
        }
    )

    connection.connect()

    @connection.on(LiveEvents.Transcript)
    def on_transcript(data):
        print("transcript", data)

    @connection.on(LiveEvents.Error)
    def on_error(data):
        print("error", data)

    @connection.on(LiveEvents.Disconnect)
    def on_disconnect():
        print("disconnected")

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    try:
        while True:
            audio_data = stream.read(CHUNK)
            connection.send(audio_data)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


if __name__ == "__main__":
    main()
