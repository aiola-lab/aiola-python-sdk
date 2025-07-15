import os
import pyaudio # pip install pyaudio for mic stream
from aiola import AiolaClient
from aiola.types import LiveEvents

def live_streaming():
    try:
        # Step 1: Generate access token, save it
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY') or 'YOUR_API_KEY'
        )
        
        # Step 2: Create client using the access token
        client = AiolaClient(
            access_token=result['accessToken']
        )
        
        # Step 3: Start streaming
        connection = client.stt.stream(
            lang_code='en'
        )

        @connection.on(LiveEvents.Transcript)
        def on_transcript(data):
            print('Transcript:', data.get('transcript', data))

        @connection.on(LiveEvents.Connect)
        def on_connect():
            print('Connected to streaming service')

        @connection.on(LiveEvents.Disconnect)
        def on_disconnect():
            print('Disconnected from streaming service')

        @connection.on(LiveEvents.Error)
        def on_error(error):
            print('Streaming error:', error)

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

            while True:
                audio_data = stream.read(4096)
                connection.send(audio_data)
                
        except KeyboardInterrupt:
            print('Keyboard interrupt')
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            connection.disconnect()
        
    except Exception as error:
        print('Error:', error)

if __name__ == "__main__":
    live_streaming()
