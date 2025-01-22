from aiola_tts_sdk import AiolaTTSClient

def save_audio_file(audio_data: bytes, filename: str):
    with open(filename, "wb") as f:
        f.write(audio_data)
    print(f"Audio saved as {filename}")

def main():
    tts_url = "< your-api-base-url >/tts"   # Replace with your API base URL
    tts_client = AiolaTTSClient(tts_url)

    try:

        # Stream Speech Example
        print("Streaming speech...")
        stream_data = tts_client.synthesize_stream("Streaming aiOla speech", voice="af_bella")
        save_audio_file(stream_data, "streamed_audio.wav")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()