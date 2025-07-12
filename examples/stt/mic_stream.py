import os
import pyaudio # pip install pyaudio for mic stream
from aiola import AiolaClient
from aiola.types import LiveEvents


AIOLA_API_KEY = os.getenv("AIOLA_API_KEY")

def main():    
    client = AiolaClient(api_key=AIOLA_API_KEY)

    connection = client.stt.stream(lang_code="en")

    @connection.on(LiveEvents.Transcript)
    def on_transcript(data):
        print("transcript", data)

    @connection.on(LiveEvents.Error)
    def on_error(data):
        print("error", data)

    @connection.on(LiveEvents.Disconnect)
    def on_disconnect():
        print("disconnected")

    @connection.on(LiveEvents.Connect)
    def on_connect():
        print("Connected to streaming service")

    connection.connect()

    try:
        # Capture audio from microphone
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096,
        )

        # Send audio data to streaming service, wait until finished
        while True:
            audio_data = stream.read(4096)
            connection.send(audio_data)
    except KeyboardInterrupt:
        print("Stopping audio capture...")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        connection.disconnect()


if __name__ == "__main__":
    main()
