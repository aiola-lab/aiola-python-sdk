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

def test_synthesize_invalid_text(client):
    with pytest.raises(ValueError, match="The 'text' parameter is required."):
        client.synthesize("")
    with pytest.raises(ValueError, match="The 'text' parameter is required."):
        client.synthesize(None)

@patch('requests.post')
def test_synthesize_invalid_voice(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "Invalid voice"}
    mock_post.return_value = mock_response
    with pytest.raises(requests.exceptions.RequestException) as exc_info:
        client.synthesize("Hello", voice="invalid_voice")
    assert "Invalid voice" in str(exc_info.value)

@patch('requests.post')
def test_synthesize_success(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "audio/wav"}
    mock_response.content = create_mock_wav()
    mock_post.return_value = mock_response
    result = client.synthesize("Hello, world!")
    mock_post.assert_called_once()
    assert result is not None

@patch('requests.post')
def test_api_error_handling(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "Invalid request"}
    mock_post.return_value = mock_response
    with pytest.raises(requests.exceptions.RequestException) as exc_info:
        client.synthesize("Hello, world!")
    assert "Error 400" in str(exc_info.value)
    assert "Invalid request" in str(exc_info.value)

@patch('requests.post')
def test_unknown_error_handling(mock_post, client):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.side_effect = ValueError()
    mock_post.return_value = mock_response
    with pytest.raises(requests.exceptions.RequestException) as exc_info:
        client.synthesize("Hello, world!")
    assert "Error 500" in str(exc_info.value)
    assert "Unknown error occurred" in str(exc_info.value) 