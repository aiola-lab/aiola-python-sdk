import json
import urllib.parse
from io import BytesIO

import pytest
import httpx

from aiola import AiolaClient, AsyncAiolaClient, AiolaError
from aiola.types import TasksConfig, LiveEvents, TranscriptionResponse
from aiola.clients.stt.client import StreamConnection, AsyncStreamConnection

from tests._helpers import (
    DummySocketClient,
    DummyAsyncSocketClient,
    DummyResponse,
)

from aiola.constants import DEFAULT_WORKFLOW_ID


# ---------------------------------------------------------------------------
# Success paths
# ---------------------------------------------------------------------------


def test_stt_stream_creates_connection_without_connecting(patch_dummy_socket, monkeypatch):
    """``SttClient.stream`` must create a connection object without connecting immediately."""

    # Mock the auth client to return the API key directly instead of making HTTP requests
    def mock_get_access_token(self, access_token, api_key, workflow_id):
        return api_key or "secret-key"

    from aiola.clients.auth.client import AuthClient
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    connection = client.stt.stream(workflow_id="flow-123", lang_code="fr", time_zone="Europe/Paris")

    assert isinstance(connection, StreamConnection)
    assert connection.connected is False  # Should not be connected yet

    # Connection should be established when calling connect()
    connection.connect()
    assert connection.connected is True

    # Access the underlying socket to validate connection parameters
    sio = connection._sio
    assert isinstance(sio, DummySocketClient)

    # ---------------------------------------------------------------------
    # Validate URL + query parameters
    # ---------------------------------------------------------------------
    kwargs = sio.connect_kwargs  # All args are passed by keyword in our SDK
    url = kwargs["url"]

    parsed = urllib.parse.urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "speech.example"

    query = urllib.parse.parse_qs(parsed.query)
    assert query["flow_id"] == ["flow-123"]
    assert query["lang_code"] == ["fr"]
    assert query["time_zone"] == ["Europe/Paris"]

    # Auth propagated
    assert kwargs["headers"]["Authorization"] == "Bearer secret-key"


def test_stt_transcribe_file_makes_expected_http_request(dummy_stt_http):
    """``SttClient.transcribe_file`` should send POST /api/speech-to-text/file with file."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    # Create a mock audio file
    audio_file = BytesIO(b"fake audio data")

    result = client.stt.transcribe_file(
        file=audio_file,
        language="en",
    )

    # Check the response
    assert isinstance(result, TranscriptionResponse)
    assert result.transcript == "Hello, this is a test transcription."
    assert result.raw_transcript == "Hello, this is a test transcription."
    assert len(result.segments) == 2
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 2.5
    assert result.metadata.language == "en"
    assert result.metadata.file_duration == 5.0

    # Check the HTTP request
    assert len(dummy_stt_http.post_calls) == 1
    recorded = dummy_stt_http.post_calls[0]
    assert recorded["path"] == "/api/speech-to-text/file"
    assert recorded["files"]["file"] == audio_file
    assert recorded["data"]["language"] == "en"

    # Verify empty keywords JSON is sent (since keywords defaults to empty dict)
    keywords_json = recorded["data"]["keywords"]
    parsed_keywords = json.loads(keywords_json)
    assert parsed_keywords == {}


def test_stt_transcribe_file_with_keywords(dummy_stt_http):
    """``SttClient.transcribe_file`` properly serializes keywords."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    # Create a mock audio file
    audio_file = BytesIO(b"fake audio data")

    keywords = {"hello": "greeting", "world": "place"}

    result = client.stt.transcribe_file(
        file=audio_file,
        language="fr",
        keywords=keywords,
    )

    # Check the response
    assert result.transcript == "Hello, this is a test transcription."

    # Check the HTTP request
    assert len(dummy_stt_http.post_calls) == 1
    recorded = dummy_stt_http.post_calls[0]
    assert recorded["path"] == "/api/speech-to-text/file"
    assert recorded["files"]["file"] == audio_file
    assert recorded["data"]["language"] == "fr"

    # Verify keywords was properly serialized
    keywords_json = recorded["data"]["keywords"]
    parsed_keywords = json.loads(keywords_json)
    assert parsed_keywords["hello"] == "greeting"
    assert parsed_keywords["world"] == "place"


def test_stt_transcribe_file_with_default_parameters(dummy_stt_http):
    """``SttClient.transcribe_file`` uses default values when parameters are not provided."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    # Create a mock audio file
    audio_file = BytesIO(b"fake audio data")

    # Call without optional parameters
    result = client.stt.transcribe_file(file=audio_file)

    # Check the response
    assert isinstance(result, TranscriptionResponse)
    assert result.transcript == "Hello, this is a test transcription."

    # Check the HTTP request uses defaults
    assert len(dummy_stt_http.post_calls) == 1
    recorded = dummy_stt_http.post_calls[0]
    assert recorded["path"] == "/api/speech-to-text/file"
    assert recorded["files"]["file"] == audio_file
    assert recorded["data"]["language"] == "en"  # Default language

    # Verify empty keywords JSON is sent
    keywords_json = recorded["data"]["keywords"]
    parsed_keywords = json.loads(keywords_json)
    assert parsed_keywords == {}


def test_stt_transcribe_file_with_empty_keywords(dummy_stt_http):
    """``SttClient.transcribe_file`` handles empty keywords dict properly."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    # Create a mock audio file
    audio_file = BytesIO(b"fake audio data")

    result = client.stt.transcribe_file(
        file=audio_file,
        language="es",
        keywords={},
    )

    # Check the response
    assert result.transcript == "Hello, this is a test transcription."

    # Check the HTTP request
    assert len(dummy_stt_http.post_calls) == 1
    recorded = dummy_stt_http.post_calls[0]
    assert recorded["data"]["language"] == "es"

    # Verify empty keywords JSON
    keywords_json = recorded["data"]["keywords"]
    parsed_keywords = json.loads(keywords_json)
    assert parsed_keywords == {}


def test_stt_transcribe_file_with_different_file_types(dummy_stt_http):
    """``SttClient.transcribe_file`` works with different file input types."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    # Test with bytes
    audio_bytes = b"fake audio data as bytes"
    result = client.stt.transcribe_file(file=audio_bytes)
    assert result.transcript == "Hello, this is a test transcription."

    # Test with tuple (filename, file)
    audio_file_tuple = ("audio.wav", BytesIO(b"fake audio data"))
    result = client.stt.transcribe_file(file=audio_file_tuple)
    assert result.transcript == "Hello, this is a test transcription."

    # Verify both calls were made
    assert len(dummy_stt_http.post_calls) == 2


def test_stt_transcribe_file_with_complex_keywords(dummy_stt_http):
    """``SttClient.transcribe_file`` handles complex keyword structures."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    # Create a mock audio file
    audio_file = BytesIO(b"fake audio data")

    # Complex keywords with special characters and numbers
    keywords = {
        "API key": "authentication",
        "user@example.com": "email",
        "123-456-7890": "phone",
        "special!@#$%": "symbols",
    }

    result = client.stt.transcribe_file(
        file=audio_file,
        keywords=keywords,
    )

    # Check the response
    assert result.transcript == "Hello, this is a test transcription."

    # Check the HTTP request
    assert len(dummy_stt_http.post_calls) == 1
    recorded = dummy_stt_http.post_calls[0]

    # Verify complex keywords were properly serialized
    keywords_json = recorded["data"]["keywords"]
    parsed_keywords = json.loads(keywords_json)
    assert parsed_keywords["API key"] == "authentication"
    assert parsed_keywords["user@example.com"] == "email"
    assert parsed_keywords["123-456-7890"] == "phone"
    assert parsed_keywords["special!@#$%"] == "symbols"


def test_stt_stream_with_tasks_config(patch_dummy_socket):
    """``SttClient.stream`` properly serializes tasks_config as JSON."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    tasks_config: TasksConfig = {
        "TRANSLATION": {
            "src_lang_code": "en",
            "dst_lang_code": "es",
        },
        "SENTIMENT_ANALYSIS": {},
        "ENTITY_DETECTION_FROM_LIST": {
            "entity_list": ["person", "location", "organization"]
        },
    }

    connection = client.stt.stream(
        workflow_id="flow-123",
        tasks_config=tasks_config
    )

    assert isinstance(connection, StreamConnection)
    assert connection.connected is False

    connection.connect()
    assert connection.connected is True

    # Access the underlying socket to validate connection parameters
    sio = connection._sio
    assert isinstance(sio, DummySocketClient)

    # ---------------------------------------------------------------------
    # Validate tasks_config is properly serialized in query parameters
    # ---------------------------------------------------------------------
    kwargs = sio.connect_kwargs
    url = kwargs["url"]
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)

    # Extract and parse the tasks_config from the URL
    tasks_config_json = query["tasks_config"][0]
    parsed_tasks_config = json.loads(tasks_config_json)

    # Verify the tasks_config was properly serialized
    assert parsed_tasks_config["TRANSLATION"]["src_lang_code"] == "en"
    assert parsed_tasks_config["TRANSLATION"]["dst_lang_code"] == "es"
    assert parsed_tasks_config["SENTIMENT_ANALYSIS"] == {}
    assert parsed_tasks_config["ENTITY_DETECTION_FROM_LIST"]["entity_list"] == ["person", "location", "organization"]


def test_stt_stream_with_empty_tasks_config(patch_dummy_socket):
    """``SttClient.stream`` handles empty tasks_config properly."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    connection = client.stt.stream(workflow_id="flow-123", tasks_config={})

    assert isinstance(connection, StreamConnection)
    assert connection.connected is False

    connection.connect()
    assert connection.connected is True

    # Access the underlying socket to validate connection parameters
    sio = connection._sio

    # Verify empty tasks_config is serialized as empty JSON object
    kwargs = sio.connect_kwargs
    url = kwargs["url"]
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)

    tasks_config_json = query["tasks_config"][0]
    parsed_tasks_config = json.loads(tasks_config_json)
    assert parsed_tasks_config == {}


def test_stt_stream_with_no_tasks_config(patch_dummy_socket):
    """``SttClient.stream`` handles None tasks_config properly."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    connection = client.stt.stream(workflow_id="flow-123", tasks_config=None)

    assert isinstance(connection, StreamConnection)
    assert connection.connected is False

    connection.connect()
    assert connection.connected is True

    # Access the underlying socket to validate connection parameters
    sio = connection._sio

    # Verify None tasks_config is serialized as empty JSON object
    kwargs = sio.connect_kwargs
    url = kwargs["url"]
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)

    tasks_config_json = query["tasks_config"][0]
    parsed_tasks_config = json.loads(tasks_config_json)
    assert parsed_tasks_config == None


def test_stt_stream_with_all_tasks_config(patch_dummy_socket):
    """``SttClient.stream`` handles all possible task configurations."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")

    tasks_config: TasksConfig = {
        "FORM_FILLING": {},
        "TRANSLATION": {
            "src_lang_code": "english",
            "dst_lang_code": "spanish",
        },
        "SENTIMENT_ANALYSIS": {},
        "SUMMARIZATION": {},
        "TOPIC_DETECTION": {},
        "CONTENT_MODERATION": {},
        "AUTO_CHAPTERS": {},
        "ENTITY_DETECTION": {},
        "ENTITY_DETECTION_FROM_LIST": {
            "entity_list": ["animals", "fruits"],
        },
        "KEY_PHRASES": {},
        "PII_REDACTION": {},
    }

    connection = client.stt.stream(
        workflow_id="flow-123",
        tasks_config=tasks_config
    )

    assert isinstance(connection, StreamConnection)
    assert connection.connected is False

    connection.connect()
    assert connection.connected is True

    # Access the underlying socket to validate connection parameters
    sio = connection._sio

    # Verify all tasks are properly serialized
    kwargs = sio.connect_kwargs
    url = kwargs["url"]
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)

    tasks_config_json = query["tasks_config"][0]
    parsed_tasks_config = json.loads(tasks_config_json)

    # Check each task configuration
    assert "FORM_FILLING" in parsed_tasks_config
    assert "TRANSLATION" in parsed_tasks_config
    assert parsed_tasks_config["TRANSLATION"]["src_lang_code"] == "english"
    assert parsed_tasks_config["TRANSLATION"]["dst_lang_code"] == "spanish"
    assert "SENTIMENT_ANALYSIS" in parsed_tasks_config
    assert "SUMMARIZATION" in parsed_tasks_config
    assert "TOPIC_DETECTION" in parsed_tasks_config
    assert "CONTENT_MODERATION" in parsed_tasks_config
    assert "AUTO_CHAPTERS" in parsed_tasks_config
    assert "ENTITY_DETECTION" in parsed_tasks_config
    assert "ENTITY_DETECTION_FROM_LIST" in parsed_tasks_config
    assert parsed_tasks_config["ENTITY_DETECTION_FROM_LIST"]["entity_list"] == ["animals", "fruits"]
    assert "KEY_PHRASES" in parsed_tasks_config
    assert "PII_REDACTION" in parsed_tasks_config


def test_stream_connection_wrapper_functionality(patch_dummy_socket):
    """Test that StreamConnection wrapper provides the expected API."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")
    connection = client.stt.stream(workflow_id="flow-123")

    assert isinstance(connection, StreamConnection)
    assert connection.connected is False

    # Should be able to register event handlers before connecting
    @connection.on(LiveEvents.Transcript)
    def on_transcript(data):
        return data

    # But should raise error when trying to send data before connecting
    with pytest.raises(AiolaError, match="Connection not established"):
        connection.send(b"test_audio")

    # Connect first
    connection.connect()
    assert connection.connected is True

    # Now methods should work
    @connection.on(LiveEvents.Transcript)
    def on_transcript(data):
        return data

    # Test event handler registration (direct style)
    def on_error(data):
        return data
    connection.on(LiveEvents.Error, on_error)

    # Test sending audio data
    audio_data = b"test_audio_data"
    connection.send(audio_data)

    # Verify the underlying socket received the correct calls
    sio = connection._sio

    # Check that event handlers were registered with the correct namespace
    assert f"{LiveEvents.Transcript}:/events" in sio.event_handlers
    assert f"{LiveEvents.Error}:/events" in sio.event_handlers

    # Check that send() translates to emit() with correct parameters
    assert len(sio.emit_calls) == 1
    emit_call = sio.emit_calls[0]
    assert emit_call["event"] == "binary_data"
    assert emit_call["data"] == audio_data
    assert emit_call["namespace"] == "/events"


def test_connection_disconnect_resets_state(patch_dummy_socket):
    """Test that disconnect properly resets the connection state."""

    client = AiolaClient(api_key="secret-key", base_url="https://speech.example")
    connection = client.stt.stream(workflow_id="flow-123")

    # Connect and verify
    connection.connect()
    assert connection.connected is True

    # Disconnect and verify state is reset
    connection.disconnect()
    assert connection.connected is False

    # Should be able to connect again
    connection.connect()
    assert connection.connected is True


@pytest.mark.anyio
async def test_async_stt_stream(patch_dummy_async_socket):
    """Async version should behave identically while being awaitable."""

    client = AsyncAiolaClient(api_key="tok", base_url="https://speech.example")

    connection = await client.stt.stream(workflow_id="f1")

    assert isinstance(connection, AsyncStreamConnection)
    assert connection.connected is False

    await connection.connect()
    assert connection.connected is True

    # Access the underlying socket to validate connection parameters
    sio = connection._sio
    assert isinstance(sio, DummyAsyncSocketClient)

    url = sio.connect_kwargs["url"]
    assert "flow_id=f1" in url


@pytest.mark.anyio
async def test_async_stt_stream_with_tasks_config(patch_dummy_async_socket):
    """Async version properly handles tasks_config."""

    client = AsyncAiolaClient(api_key="tok", base_url="https://speech.example")

    tasks_config: TasksConfig = {
        "TRANSLATION": {
            "src_lang_code": "en",
            "dst_lang_code": "fr",
        },
        "SENTIMENT_ANALYSIS": {},
    }

    connection = await client.stt.stream(
        workflow_id="f1",
        tasks_config=tasks_config
    )

    assert isinstance(connection, AsyncStreamConnection)
    assert connection.connected is False

    await connection.connect()
    assert connection.connected is True

    # Access the underlying socket to validate connection parameters
    sio = connection._sio

    # Verify tasks_config is properly serialized
    kwargs = sio.connect_kwargs
    url = kwargs["url"]
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)

    tasks_config_json = query["tasks_config"][0]
    parsed_tasks_config = json.loads(tasks_config_json)

    assert parsed_tasks_config["TRANSLATION"]["src_lang_code"] == "en"
    assert parsed_tasks_config["TRANSLATION"]["dst_lang_code"] == "fr"
    assert parsed_tasks_config["SENTIMENT_ANALYSIS"] == {}


@pytest.mark.anyio
async def test_async_stt_transcribe_file_makes_expected_http_request(dummy_async_stt_http):
    """``AsyncSttClient.transcribe_file`` should send POST /api/speech-to-text/file with file."""

    client = AsyncAiolaClient(api_key="secret-key", base_url="https://speech.example")

    # Create a mock audio file
    audio_file = BytesIO(b"fake audio data")

    result = await client.stt.transcribe_file(
        file=audio_file,
        language="en",
    )

    # Check the response
    assert isinstance(result, TranscriptionResponse)
    assert result.transcript == "Hello, this is a test transcription."
    assert result.raw_transcript == "Hello, this is a test transcription."
    assert len(result.segments) == 2
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 2.5
    assert result.metadata.language == "en"
    assert result.metadata.file_duration == 5.0

    # Check the HTTP request
    assert len(dummy_async_stt_http.post_calls) == 1
    recorded = dummy_async_stt_http.post_calls[0]
    assert recorded["path"] == "/api/speech-to-text/file"
    assert recorded["files"]["file"] == audio_file
    assert recorded["data"]["language"] == "en"

    # Verify empty keywords JSON is sent (since keywords defaults to empty dict)
    keywords_json = recorded["data"]["keywords"]
    parsed_keywords = json.loads(keywords_json)
    assert parsed_keywords == {}


@pytest.mark.anyio
async def test_async_stt_transcribe_file_with_keywords(dummy_async_stt_http):
    """``AsyncSttClient.transcribe_file`` properly serializes keywords."""

    client = AsyncAiolaClient(api_key="secret-key", base_url="https://speech.example")

    # Create a mock audio file
    audio_file = BytesIO(b"fake audio data")

    keywords = {"hello": "greeting", "world": "place"}

    result = await client.stt.transcribe_file(
        file=audio_file,
        language="fr",
        keywords=keywords,
    )

    # Check the response
    assert result.transcript == "Hello, this is a test transcription."

    # Check the HTTP request
    assert len(dummy_async_stt_http.post_calls) == 1
    recorded = dummy_async_stt_http.post_calls[0]
    assert recorded["path"] == "/api/speech-to-text/file"
    assert recorded["files"]["file"] == audio_file
    assert recorded["data"]["language"] == "fr"

    # Verify keywords was properly serialized
    keywords_json = recorded["data"]["keywords"]
    parsed_keywords = json.loads(keywords_json)
    assert parsed_keywords["hello"] == "greeting"
    assert parsed_keywords["world"] == "place"


@pytest.mark.anyio
async def test_async_stt_transcribe_file_with_default_parameters(dummy_async_stt_http):
    """``AsyncSttClient.transcribe_file`` uses default values when parameters are not provided."""

    client = AsyncAiolaClient(api_key="secret-key", base_url="https://speech.example")

    # Create a mock audio file
    audio_file = BytesIO(b"fake audio data")

    # Call without optional parameters
    result = await client.stt.transcribe_file(file=audio_file)

    # Check the response
    assert isinstance(result, TranscriptionResponse)
    assert result.transcript == "Hello, this is a test transcription."

    # Check the HTTP request uses defaults
    assert len(dummy_async_stt_http.post_calls) == 1
    recorded = dummy_async_stt_http.post_calls[0]
    assert recorded["path"] == "/api/speech-to-text/file"
    assert recorded["files"]["file"] == audio_file
    assert recorded["data"]["language"] == "en"  # Default language

    # Verify empty keywords JSON is sent
    keywords_json = recorded["data"]["keywords"]
    parsed_keywords = json.loads(keywords_json)
    assert parsed_keywords == {}


@pytest.mark.anyio
async def test_async_stt_transcribe_file_handles_http_error(monkeypatch):
    """Async STT transcribe_file should handle HTTP errors gracefully."""

    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.stt.client

    # Mock auth client methods first
    def mock_get_access_token(self, options):
        return "fake_access_token"

    async def mock_async_get_access_token(self, options):
        return "fake_access_token"

    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    class AsyncFailingHTTPClient:
        async def post(self, path, *, files=None, data=None, json=None):
            # Simulate HTTP error response
            from httpx import Response, Request
            from aiola.errors import AiolaError
            request = Request("POST", "http://test.com")
            response = Response(400, request=request)
            response._content = b'{"error": "Bad request"}'
            raise AiolaError.from_response(response)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

    async def mock_create_async_authenticated_client(*args, **kwargs):
        return AsyncFailingHTTPClient()

    # Patch in the STT client module where it's imported
    monkeypatch.setattr(aiola.clients.stt.client, "create_async_authenticated_client", mock_create_async_authenticated_client)

    audio_file = BytesIO(b"fake_audio_data")
    client = AsyncAiolaClient(api_key="test-key")

    with pytest.raises(AiolaError, match="Request failed with status 400"):
        await client.stt.transcribe_file(file=audio_file)


@pytest.mark.anyio
async def test_async_stt_transcribe_file_handles_network_error(monkeypatch):
    """Async STT transcribe_file should handle network errors gracefully."""

    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.stt.client

    # Mock auth client methods first
    def mock_get_access_token(self, options):
        return "fake_access_token"

    async def mock_async_get_access_token(self, options):
        return "fake_access_token"

    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    class AsyncNetworkErrorHTTPClient:
        async def post(self, path, *, files=None, data=None, json=None):
            import httpx
            raise httpx.ConnectError("Network unreachable")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

    async def mock_create_async_authenticated_client(*args, **kwargs):
        return AsyncNetworkErrorHTTPClient()

    # Patch in the STT client module where it's imported
    monkeypatch.setattr(aiola.clients.stt.client, "create_async_authenticated_client", mock_create_async_authenticated_client)

    audio_file = BytesIO(b"fake_audio_data")
    client = AsyncAiolaClient(api_key="test-key")

    with pytest.raises(AiolaError, match="Network error during async transcription"):
        await client.stt.transcribe_file(file=audio_file)


# ---------------------------------------------------------------------------
# Error / exception paths
# ---------------------------------------------------------------------------


def test_stt_stream_connection_raises_aiola_error(monkeypatch):
    """When the underlying socket connection fails, an :class:`AiolaError` is raised."""

    from aiola.clients.stt import stream_client as stream_module
    from aiola.clients.auth.client import AuthClient, AsyncAuthClient

    # Mock auth client methods first
    def mock_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"

    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_get_access_token)

    class FailingSocket(DummySocketClient):
        def connect(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(stream_module.socketio, "Client", FailingSocket)

    client = AiolaClient(api_key="k")
    connection = client.stt.stream()

    with pytest.raises(AiolaError):
        connection.connect()


@pytest.mark.anyio
async def test_async_stt_stream_connection_raises_aiola_error(monkeypatch):
    """Async variant must wrap exceptions into :class:`AiolaError`."""

    from aiola.clients.stt import stream_client as stream_module
    from aiola.clients.auth.client import AuthClient, AsyncAuthClient

    # Mock auth client methods first
    def mock_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"

    async def mock_async_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"

    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    class AsyncFail(DummyAsyncSocketClient):
        async def connect(self, *args, **kwargs):
            raise RuntimeError("fail")

    monkeypatch.setattr(stream_module.socketio, "AsyncClient", AsyncFail)

    client = AsyncAiolaClient(api_key="k")
    connection = await client.stt.stream()

    with pytest.raises(AiolaError):
        await connection.connect()


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# workflow_id precedence tests
# ---------------------------------------------------------------------------


def test_workflow_id_precedence_method_param_overrides_client_default(patch_dummy_socket, monkeypatch):
    """Method-level workflow_id parameter should override client default."""

    def mock_get_access_token(self, access_token, api_key, workflow_id):
        # Track which workflow_id was passed to auth
        mock_get_access_token.called_with_workflow_id = workflow_id
        return "test-token"

    from aiola.clients.auth.client import AuthClient
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)

    client = AiolaClient(api_key="secret-key", workflow_id="client-workflow-123")
    connection = client.stt.stream(workflow_id="method-workflow-456")

    # Auth should have been called with method-level workflow_id
    assert mock_get_access_token.called_with_workflow_id == "method-workflow-456"

    # URL should contain method-level workflow_id
    parsed_url = urllib.parse.urlparse(connection._url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    assert query_params["flow_id"][0] == "method-workflow-456"


def test_workflow_id_precedence_client_default_when_method_param_none(patch_dummy_socket, monkeypatch):
    """Client-level workflow_id should be used when method parameter is None."""

    def mock_get_access_token(self, access_token, api_key, workflow_id):
        mock_get_access_token.called_with_workflow_id = workflow_id
        return "test-token"

    from aiola.clients.auth.client import AuthClient
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)

    client = AiolaClient(api_key="secret-key", workflow_id="client-workflow-123")
    connection = client.stt.stream(workflow_id=None)

    # Auth should have been called with client-level workflow_id
    assert mock_get_access_token.called_with_workflow_id == "client-workflow-123"

    # URL should contain client-level workflow_id
    parsed_url = urllib.parse.urlparse(connection._url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    assert query_params["flow_id"][0] == "client-workflow-123"


def test_workflow_id_precedence_default_fallback(patch_dummy_socket, monkeypatch):
    """Should fall back to DEFAULT_WORKFLOW_ID when neither client nor method provide it."""

    def mock_get_access_token(self, access_token, api_key, workflow_id):
        mock_get_access_token.called_with_workflow_id = workflow_id
        return "test-token"

    from aiola.clients.auth.client import AuthClient
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)

    client = AiolaClient(api_key="secret-key")  # No workflow_id provided
    connection = client.stt.stream()  # No workflow_id provided

    # Auth should have been called with DEFAULT_WORKFLOW_ID
    assert mock_get_access_token.called_with_workflow_id == DEFAULT_WORKFLOW_ID

    # URL should contain DEFAULT_WORKFLOW_ID
    parsed_url = urllib.parse.urlparse(connection._url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    assert query_params["flow_id"][0] == DEFAULT_WORKFLOW_ID


@pytest.mark.anyio
async def test_async_workflow_id_precedence_method_param_overrides_client_default(patch_dummy_async_socket, monkeypatch):
    """Async method-level workflow_id parameter should override client default."""

    async def mock_async_get_access_token(self, access_token, api_key, workflow_id):
        mock_async_get_access_token.called_with_workflow_id = workflow_id
        return "test-token"

    from aiola.clients.auth.client import AsyncAuthClient
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    client = AsyncAiolaClient(api_key="secret-key", workflow_id="client-workflow-123")
    connection = await client.stt.stream(workflow_id="method-workflow-456")

    # Auth should have been called with method-level workflow_id
    assert mock_async_get_access_token.called_with_workflow_id == "method-workflow-456"

    # URL should contain method-level workflow_id
    parsed_url = urllib.parse.urlparse(connection._url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    assert query_params["flow_id"][0] == "method-workflow-456"


@pytest.mark.anyio
async def test_async_workflow_id_precedence_client_default_when_method_param_none(patch_dummy_async_socket, monkeypatch):
    """Async client-level workflow_id should be used when method parameter is None."""

    async def mock_async_get_access_token(self, access_token, api_key, workflow_id):
        mock_async_get_access_token.called_with_workflow_id = workflow_id
        return "test-token"

    from aiola.clients.auth.client import AsyncAuthClient
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    client = AsyncAiolaClient(api_key="secret-key", workflow_id="client-workflow-123")
    connection = await client.stt.stream(workflow_id=None)

    # Auth should have been called with client-level workflow_id
    assert mock_async_get_access_token.called_with_workflow_id == "client-workflow-123"

    # URL should contain client-level workflow_id
    parsed_url = urllib.parse.urlparse(connection._url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    assert query_params["flow_id"][0] == "client-workflow-123"


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


def test_stt_transcribe_file_handles_http_error(monkeypatch):
    """STT transcribe_file should handle HTTP errors gracefully."""

    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.stt.client

    # Mock auth client methods first
    def mock_get_access_token(self, options):
        return "fake_access_token"

    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_get_access_token)

    class FailingHTTPClient:
        def post(self, path, *, files=None, data=None, json=None):
            # Simulate HTTP error response
            from httpx import Response, Request
            from aiola.errors import AiolaError
            request = Request("POST", "http://test.com")
            response = Response(400, request=request)
            response._content = b'{"error": "Bad request"}'
            raise AiolaError.from_response(response)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    def mock_create_authenticated_client(*args, **kwargs):
        return FailingHTTPClient()

    # Patch in the STT client module where it's imported
    monkeypatch.setattr(aiola.clients.stt.client, "create_authenticated_client", mock_create_authenticated_client)

    audio_file = BytesIO(b"fake_audio_data")
    client = AiolaClient(api_key="test-key")

    with pytest.raises(AiolaError, match="Request failed with status 400"):
        client.stt.transcribe_file(file=audio_file)


def test_stt_transcribe_file_handles_network_error(monkeypatch):
    """STT transcribe_file should handle network errors gracefully."""

    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.stt.client

    # Mock auth client methods first
    def mock_get_access_token(self, options):
        return "fake_access_token"

    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_get_access_token)

    class NetworkErrorHTTPClient:
        def post(self, path, *, files=None, data=None, json=None):
            import httpx
            raise httpx.ConnectError("Network unreachable")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    def mock_create_authenticated_client(*args, **kwargs):
        return NetworkErrorHTTPClient()

    # Patch in the STT client module where it's imported
    monkeypatch.setattr(aiola.clients.stt.client, "create_authenticated_client", mock_create_authenticated_client)

    audio_file = BytesIO(b"fake_audio_data")
    client = AiolaClient(api_key="test-key")

    with pytest.raises(AiolaError, match="Network error during transcription"):
        client.stt.transcribe_file(file=audio_file)


def test_stt_transcribe_file_handles_json_decode_error(monkeypatch):
    """STT transcribe_file should handle JSON decode errors gracefully."""

    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.stt.client

    # Mock auth client methods first
    def mock_get_access_token(self, options):
        return "fake_access_token"

    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_get_access_token)

    class InvalidJSONHTTPClient:
        def post(self, path, *, files=None, data=None, json=None):
            class MockResponse:
                def json(self):
                    import json
                    raise json.JSONDecodeError("Invalid JSON", "", 0)

                def raise_for_status(self):
                    pass

            return MockResponse()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    def mock_create_authenticated_client(*args, **kwargs):
        return InvalidJSONHTTPClient()

    # Patch in the STT client module where it's imported
    monkeypatch.setattr(aiola.clients.stt.client, "create_authenticated_client", mock_create_authenticated_client)

    audio_file = BytesIO(b"fake_audio_data")
    client = AiolaClient(api_key="test-key")

    with pytest.raises(AiolaError, match="Invalid response format from transcription service"):
        client.stt.transcribe_file(file=audio_file)


# ---------------------------------------------------------------------------
# Async stream connection tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_async_stream_connection_wrapper_functionality(patch_dummy_async_socket):
    """Test that AsyncStreamConnection wrapper provides the expected API."""

    client = AsyncAiolaClient(api_key="secret-key", base_url="https://speech.example")
    connection = await client.stt.stream(workflow_id="flow-123")

    assert isinstance(connection, AsyncStreamConnection)
    assert connection.connected is False

    # Should be able to register event handlers before connecting
    @connection.on(LiveEvents.Transcript)
    def on_transcript(data):
        return data

    # But should raise error when trying to send data before connecting
    with pytest.raises(AiolaError, match="Connection not established"):
        await connection.send(b"test_audio")

    # Connect first
    await connection.connect()
    assert connection.connected is True

    # Now methods should work
    @connection.on(LiveEvents.Transcript)
    def on_transcript(data):
        return data

    # Test event handler registration (direct style)
    def on_error(data):
        return data
    connection.on(LiveEvents.Error, on_error)

    # Test sending audio data
    audio_data = b"test_audio_data"
    await connection.send(audio_data)

    # Verify the underlying socket received the correct calls
    sio = connection._sio

    # Check that event handlers were registered with the correct namespace
    assert f"{LiveEvents.Transcript}:/events" in sio.event_handlers
    assert f"{LiveEvents.Error}:/events" in sio.event_handlers

    # Check that send() translates to emit() with correct parameters
    assert len(sio.emit_calls) == 1
    emit_call = sio.emit_calls[0]
    assert emit_call["event"] == "binary_data"
    assert emit_call["data"] == audio_data
    assert emit_call["namespace"] == "/events"


@pytest.mark.anyio
async def test_async_connection_disconnect_resets_state(patch_dummy_async_socket):
    """Test that async disconnect properly resets the connection state."""

    client = AsyncAiolaClient(api_key="secret-key", base_url="https://speech.example")
    connection = await client.stt.stream(workflow_id="flow-123")

    # Connect and verify
    await connection.connect()
    assert connection.connected is True

    # Disconnect and verify state is reset
    await connection.disconnect()
    assert connection.connected is False

    # Should be able to connect again
    await connection.connect()
    assert connection.connected is True
