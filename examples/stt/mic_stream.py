import os
from aiola import AiolaClient, MicrophoneStream
from aiola.types import LiveEvents

def live_streaming():
    try:
        # Step 1: Generate access token, save it
        result = AiolaClient.grant_token(
            api_key=os.getenv('AIOLA_API_KEY') or 'YOUR_API_KEY'
        )

        # Step 2: Create client using the access token
        client = AiolaClient(
            access_token=result.accessToken
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
            # Capture audio from microphone using the SDK's MicrophoneStream
            with MicrophoneStream(
                channels=1,
                samplerate=16000,
                blocksize=4096,
            ) as mic:
                mic.stream_to(connection)

                # Keep the main thread alive
                while True:
                    try:
                        import time
                        time.sleep(0.1)
                    except KeyboardInterrupt:
                        print('Keyboard interrupt')
                        break

        except KeyboardInterrupt:
            print('Keyboard interrupt')

    except Exception as error:
        print('Error:', error)
    finally:
        connection.disconnect()

if __name__ == "__main__":
    live_streaming()
