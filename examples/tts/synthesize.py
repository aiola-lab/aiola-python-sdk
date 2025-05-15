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
        # Synthesize Speech Example
        print("Synthesizing speech...")

        text = 'Hello, this is a test of the aiOla TTS synthesis feature. You can download the audio after processing.'
        audio_data = tts_client.synthesize(text, voice="af_bella")
        save_audio_file(audio_data, "synthesized_audio.wav")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()