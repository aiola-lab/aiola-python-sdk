from unittest.mock import AsyncMock, MagicMock
import pytest
import sounddevice

from aiola_stt import AiolaConfig, AiolaQueryParams
from aiola_stt.client import AiolaSttClient
# Factory for mock socketio.AsyncClient
def mock_socketio_factory():
    mock_client = AsyncMock()
    mock_client.connected = False
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.emit = AsyncMock()
    mock_client.call = AsyncMock()
    mock_client.event = lambda *args, **kwargs: lambda f: f
    return mock_client

@pytest.fixture
def mock_socketio_fixture():
    return mock_socketio_factory

@pytest.fixture
def config():
    return AiolaConfig(
        api_key="test_token",
        query_params=AiolaQueryParams(
            flow_id="test_flow_id",
            execution_id="test123"
        )
    )

@pytest.fixture
def client(config, mock_socketio_fixture):
    return AiolaSttClient(config, sio_client_factory=mock_socketio_fixture)

@pytest.fixture(autouse=True)
def mock_sounddevice(monkeypatch):
    mock_stream = MagicMock()
    monkeypatch.setattr(sounddevice, "InputStream", lambda *a, **kw: mock_stream)
    monkeypatch.setattr(sounddevice, "RawInputStream", lambda *a, **kw: mock_stream)