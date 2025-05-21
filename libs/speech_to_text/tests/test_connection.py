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

@pytest.fixture(autouse=True)
def clear_connect_side_effect(client):
    client.sio.connect.side_effect = None

async def connect_and_set_connected(client):
    await client.connect()
    client.sio.connected = True

class TestAiolaSttClientConnection:
    @pytest.mark.asyncio
    async def test_connect_success(self, client):
        await client.connect()
        assert client.sio.connect.called

    @pytest.mark.asyncio
    async def test_connect_error(self, client):
        client.sio.connect.side_effect = Exception("Connection failed")
        with pytest.raises(Exception, match="Connection failed"):
            await client.connect()

    @pytest.mark.asyncio
    async def test_start_recording(self, client):
        await connect_and_set_connected(client)
        client.start_recording()
        assert client.recording_in_progress

    @pytest.mark.asyncio
    async def test_stop_recording(self, client):
        await connect_and_set_connected(client)
        await client.stop_recording()
        assert not client.recording_in_progress

    @pytest.mark.asyncio
    async def test_connect_with_auto_record(self, client):
        async def connect_side_effect(*args, **kwargs):
            client.sio.connected = True
        client.sio.connect.side_effect = connect_side_effect

        await client.connect(auto_record=True)
        assert client.sio.connect.called
        assert client.recording_in_progress

def test_query_params_flow_id_default():
    params = AiolaQueryParams(execution_id="abcd1234")
    assert params.flow_id == "C5f2da54-6150-47f7-9f36-e7b5dc384859"

def test_query_params_flow_id_override():
    params = AiolaQueryParams(execution_id="abcd1234", flow_id="custom_flow_id")
    assert params.flow_id == "custom_flow_id"

def test_query_params_invalid_lang_code():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AiolaQueryParams(execution_id="abcd1234", lang_code="xx_XX") 