from aiola_tts_sdk import AiolaTTSClient

def save_audio_file(audio_data: bytes, filename: str):
    with open(filename, "wb") as f:
        f.write(audio_data)
    print(f"Audio saved as {filename}")

def main():
    tts_url = "< your-api-base-url >/tts"  # Replace with your API base URL
    tts_client = AiolaTTSClient(tts_url)

    try:
        # Synthesize Speech Example
        print("Synthesizing speech...")

        text = 'Hello, this is a test of the aiOla TTS synthesis feature. You can download the audio after processing.'
        audio_data = tts_client.synthesize(text, voice="af_bella")
        save_audio_file(audio_data, "synthesized_audio.wav")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()