import requests
from typing import Union
from .audio_converter import AudioFormat, AudioConverter


class AiolaTTSClient:
    """
    A client for interacting with the aiOla Text-to-Speech API.
    """

    def __init__(self, base_url: str, bearer_token: str, audio_format: AudioFormat = "LINEAR16"):
        """
        Initializes the Aiola TTS Client.
        
        :param base_url: The base URL of the TTS API.
        :param bearer_token: The Bearer token for authentication.
        :param audio_format: The desired audio format (LINEAR16, MULAW, or PCM). Defaults to LINEAR16.
        """
        if not base_url:
            raise ValueError("The base_url parameter is required.")
        if not bearer_token:
            raise ValueError("The bearer_token parameter is required.")
        if audio_format not in ["LINEAR16", "MULAW", "PCM"]:
            raise ValueError("audio_format must be one of: LINEAR16, MULAW, PCM")
        
        self.base_url = base_url
        self.bearer_token = bearer_token
        self.audio_converter = AudioConverter(audio_format)

    def _post_request(self, endpoint: str, payload: dict) -> Union[bytes, dict]:
        """
        Internal method for making POST requests.

        :param endpoint: The API endpoint to call.
        :param payload: The data to send in the request.
        :return: The API response as raw bytes for audio data or a JSON response.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {self.bearer_token}"
        }

        response = requests.post(url, data=payload, headers=headers)

        if response.status_code == 200:
            if "audio/wav" in response.headers.get("Content-Type", ""):
                converted = self.audio_converter.convert(response.content)
                return converted
            return response.json()

        # Handle errors
        try:
            error_data = response.json()
        except ValueError:
            error_data = {"detail": "Unknown error occurred."}
        raise Exception(f"Error {response.status_code}: {error_data.get('detail')}")

    def synthesize(self, text: str, voice: str = "af_bella") -> bytes:
        """
        Converts text to speech and returns the audio file as bytes.

        :param text: The text to convert to speech.
        :param voice: The voice to use for synthesis (default is "af_bella").
        :return: The synthesized audio file as bytes.
        """
        if not text:
            raise ValueError("The 'text' parameter is required.")
        
        payload = {
            "text": text,
            "voice": voice,
        }
        return self._post_request("/synthesize", payload)

    def synthesize_stream(self, text: str, voice: str = "af_bella") -> bytes:
        """
        Streams text-to-speech audio data.

        :param text: The text to convert to speech.
        :param voice: The voice to use for synthesis (default is "af_bella").
        :return: The streamed audio file as bytes.
        """
        if not text:
            raise ValueError("The 'text' parameter is required.")
        
        payload = {
            "text": text,
            "voice": voice,
        }
        return self._post_request("/synthesize/stream", payload)