# flake8: noqa: D100,D101,D102,D103,D104,D105,D106,D107
# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring
import pytest
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from aiola_stt.config import AiolaConfig, AiolaQueryParams

@pytest.fixture
def config():
    return AiolaConfig(
        api_key="test_token",
        query_params=AiolaQueryParams(
            flow_id="test_flow_id",
            execution_id="test123"
        )
    )

def mock_socketio_factory():
    mock_sio_client = MagicMock()
    mock_sio_client.connected = False
    mock_sio_client.connect = AsyncMock()
    mock_sio_client.disconnect = AsyncMock()
    mock_sio_client.emit = AsyncMock()
    mock_sio_client.call = AsyncMock()
    # Mock the event decorator to simply return the function
    mock_sio_client.event = lambda *args, **kwargs: lambda f: f
    return mock_sio_client

@pytest.fixture
def client(config):
    # Create the mock modules
    mock_socketio = MagicMock()
    mock_socketio.AsyncClient = MagicMock()
    
    mock_sd = MagicMock()
    mock_sd.RawInputStream = MagicMock()
    
    # Patch the modules in sys.modules
    with patch.dict('sys.modules', {'socketio': mock_socketio, 'sounddevice': mock_sd}):
        # Now import AiolaSttClient after patching
        from aiola_stt.client import AiolaSttClient
        client_instance = AiolaSttClient(config, sio_client_factory=mock_socketio_factory)
        yield client_instance

@pytest.fixture
def mock_socketio_fixture():
    return mock_socketio_factory

async def connect_and_set_connected(client):
    await client.connect()
    client.sio.connected = True

class TestAiolaSttClientKeywords:
    @pytest.mark.asyncio
    async def test_set_keywords(self, client, mock_socketio_fixture):
        await connect_and_set_connected(client)
        keywords = ["hello", "world"]
        await client.set_keywords(keywords)
        assert client.active_keywords == keywords 

    @pytest.mark.asyncio
    async def test_clear_keywords(self, client, mock_socketio_fixture):
        await connect_and_set_connected(client)
        await client.set_keywords([])
        assert client.active_keywords == [] 