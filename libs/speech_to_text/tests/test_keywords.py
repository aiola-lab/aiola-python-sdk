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