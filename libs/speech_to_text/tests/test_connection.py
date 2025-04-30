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
    async def test_stop_recording(self, client, ):
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
    import pytest
    from pydantic import ValidationError
    # lang_code must be one of SupportedLang; 'xx_XX' is not valid
    with pytest.raises(ValidationError):
        AiolaQueryParams(execution_id="abcd1234", lang_code="xx_XX") 