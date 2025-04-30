# flake8: noqa: D100,D101,D102,D103,D104,D105,D106,D107
# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring
import pytest  # noqa
from aiola_tts.client import AiolaTtsClient, VoiceOptions

class TestAiolaTtsClientValidation:
    def test_init_valid_params(self):
        client = AiolaTtsClient(
            base_url="https://api.example.com",
            bearer_token="test_token",
            audio_format="LINEAR16"
        )
        assert client.base_url == "https://api.example.com"
        assert client.bearer_token == "test_token"
        assert client.audio_converter.target_format == "LINEAR16"

    def test_init_invalid_bearer_token(self):
        with pytest.raises(ValueError, match="The bearer_token parameter is required."):
            AiolaTtsClient(base_url="https://api.example.com", bearer_token="")
        
        with pytest.raises(ValueError, match="The bearer_token parameter is required."):
            AiolaTtsClient(base_url="https://api.example.com", bearer_token=None)

    def test_init_invalid_audio_format(self):
        with pytest.raises(ValueError, match="audio_format must be one of: LINEAR16, PCM"):
            AiolaTtsClient(
                base_url="https://api.example.com",
                bearer_token="test_token",
                audio_format="INVALID"
            )

    def test_base_url_can_be_overridden(self):
        custom_url = "https://custom.example.com"
        client = AiolaTtsClient(bearer_token="test_token", base_url=custom_url)
        assert client.base_url == custom_url 