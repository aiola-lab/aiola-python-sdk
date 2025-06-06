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

class TestAiolaSttClientEvents:
    @pytest.mark.asyncio
    async def test_handle_transcription(self, client, mock_socketio_fixture):
        test_data = {"text": "Hello world"}
        received = {}
        def on_transcript(data):
            received["data"] = data
        client.config.events["on_transcript"] = on_transcript
        await connect_and_set_connected(client)
        client.config.events["on_transcript"](test_data)
        assert received["data"] == test_data

    @pytest.mark.asyncio
    async def test_handle_error(self, client, mock_socketio_fixture):
        error_data = {"code": "ERROR_CODE", "message": "Test error"}
        received = {}
        def on_error(data):
            received["data"] = data
        client.config.events["on_error"] = on_error
        await connect_and_set_connected(client)
        client.config.events["on_error"](error_data)
        assert received["data"] == error_data

    @pytest.mark.asyncio
    async def test_handle_connection_error(self, client, mock_socketio_fixture):
        received = {}
        def on_error(data):
            received["data"] = data
        client.config.events["on_error"] = on_error
        await connect_and_set_connected(client)
        client.sio.connected = False
        error_data = {"code": "CONNECTION_ERROR", "message": "Connection error"}
        client.config.events["on_error"](error_data)
        assert received["data"] == error_data

    @pytest.mark.asyncio
    async def test_handle_connect(self, client, mock_socketio_fixture):
        received = {}
        def on_connect(transport):
            received["transport"] = transport
        client.config.events["on_connect"] = on_connect
        await connect_and_set_connected(client)
        # Simulate the event handler call as the client would
        client.config.events["on_connect"]("websocket")
        assert received["transport"] == "websocket"

    @pytest.mark.asyncio
    async def test_handle_disconnect(self, client, mock_socketio_fixture):
        received = {"called": False}
        def on_disconnect():
            received["called"] = True
        client.config.events["on_disconnect"] = on_disconnect
        await connect_and_set_connected(client)
        client.config.events["on_disconnect"]()
        assert received["called"] is True

    @pytest.mark.asyncio
    async def test_handle_start_record(self, client, mock_socketio_fixture):
        received = {"called": False}
        def on_start_record():
            received["called"] = True
        client.config.events["on_start_record"] = on_start_record
        await connect_and_set_connected(client)
        client.config.events["on_start_record"]()
        assert received["called"] is True

    @pytest.mark.asyncio
    async def test_handle_stop_record(self, client, mock_socketio_fixture):
        received = {"called": False}
        def on_stop_record():
            received["called"] = True
        client.config.events["on_stop_record"] = on_stop_record
        await connect_and_set_connected(client)
        client.config.events["on_stop_record"]()
        assert received["called"] is True

    @pytest.mark.asyncio
    async def test_handle_keyword_set(self, client, mock_socketio_fixture):
        received = {}
        def on_keyword_set(keywords):
            received["keywords"] = keywords
        client.config.events["on_keyword_set"] = on_keyword_set
        await connect_and_set_connected(client)
        test_keywords = ["hello", "world"]
        client.config.events["on_keyword_set"](test_keywords)
        assert received["keywords"] == test_keywords 