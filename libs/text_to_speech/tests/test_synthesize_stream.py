# flake8: noqa: D100,D101,D102,D103,D104,D105,D106,D107
# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring
from unittest.mock import Mock, patch
import pytest
import requests
from aiola_tts.client import AiolaTtsClient
from .common import create_mock_wav

@pytest.fixture
def client():
    return AiolaTtsClient(
        base_url="https://api.example.com",
        bearer_token="test_token",
        audio_format="LINEAR16"
    )

def test_synthesize_stream_invalid_text(client):
    with pytest.raises(ValueError, match="The 'text' parameter is required."):
        client.synthesize_stream("")
    with pytest.raises(ValueError, match="The 'text' parameter is required."):
        client.synthesize_stream(None)

@patch('requests.post')
def test_synthesize_stream_invalid_voice(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "Invalid voice"}
    mock_post.return_value = mock_response
    with pytest.raises(requests.exceptions.RequestException) as exc_info:
        client.synthesize_stream("Hello", voice="invalid_voice")
    assert "Invalid voice" in str(exc_info.value)

@patch('requests.post')
def test_synthesize_stream_success(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "audio/wav"}
    mock_response.content = create_mock_wav()
    mock_post.return_value = mock_response
    result = client.synthesize_stream("Hello, world!")
    mock_post.assert_called_once()
    assert result is not None 