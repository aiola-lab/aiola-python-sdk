import os
from aiola_tts import AiolaTtsClient

def save_audio_file(audio_data: bytes, filename: str):
    output_dir = "example_output"
    os.makedirs(output_dir, exist_ok=True)
    completed_file = os.path.join(output_dir, filename)
    with open(completed_file, "wb") as f:
        f.write(audio_data)
    print(f"Audio saved as {completed_file}")

def main():
   # Playground token - Limited usage!
    bearer_token = "qLDczk3BESZt2vcU1Tqqb1sSJ9DjsKYGygKdRPhLSg0p"
    tts_client = AiolaTtsClient(bearer_token=bearer_token)

    try:
        # Stream Speech Example
        print("Streaming speech...")
        stream_data = tts_client.synthesize_stream("Streaming aiOla speech", voice="af_bella")
        save_audio_file(stream_data, "streamed_audio.wav")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()