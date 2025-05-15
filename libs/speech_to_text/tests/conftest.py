import sys
from unittest.mock import AsyncMock, MagicMock
import importlib
import pytest

# Mock sounddevice
mock_sd = MagicMock()
mock_sd.RawInputStream = MagicMock()
sys.modules['sounddevice'] = mock_sd

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

mock_socketio = MagicMock()
mock_socketio.AsyncClient = mock_socketio_factory
sys.modules['socketio'] = mock_socketio

# Patch socketio before any test imports

def pytest_sessionstart(session):
    sys.modules['socketio'] = mock_socketio
    import aiola_stt.client
    importlib.reload(aiola_stt.client)

from aiola_stt.config import AiolaConfig, AiolaQueryParams
from aiola_stt.client import AiolaSttClient

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