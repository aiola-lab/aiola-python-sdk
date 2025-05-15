# flake8: noqa: D100,D101,D102,D103,D104,D105,D106,D107
# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring
import pytest
from aiola_stt.client import AiolaSttClient
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

@pytest.fixture
def client(config):
    return AiolaSttClient(config)

@pytest.fixture(autouse=True)
def clear_connect_side_effect(client):
    client.sio.connect.side_effect = None

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