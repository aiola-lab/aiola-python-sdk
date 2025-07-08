import pytest

from aiola import AiolaClient, AsyncAiolaClient, AiolaError

from tests._helpers import DummyHTTPClient, DummyAsyncHTTPClient


# ---------------------------------------------------------------------------
# Synchronous client
# ---------------------------------------------------------------------------


def test_tts_stream_makes_expected_http_request(dummy_http):
    """``TtsClient.stream`` should send POST /synthesize/stream and yield audio chunks."""

    client = AiolaClient(api_key="k", base_url="https://tts.example")
    chunks = list(client.tts.stream(text="Hello", voice="voiceA"))

    assert chunks == [b"chunk1", b"chunk2"]

    recorded = dummy_http.stream_calls.pop()
    assert recorded["method"] == "POST"
    assert recorded["path"] == "/api/tts/stream"
    assert recorded["json"] == {"text": "Hello", "voice": "voiceA", "language": None}


def test_tts_synthesize_makes_expected_http_request(dummy_http):
    """``TtsClient.synthesize`` must hit POST /synthesize (non-stream variant)."""

    client = AiolaClient(api_key="k")
    list(client.tts.synthesize(text="Hi", voice="B"))  # exhaust generator

    recorded = dummy_http.stream_calls.pop()
    assert recorded["path"] == "/api/tts/synthesize"


# ---------------------------------------------------------------------------
# Asynchronous client
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_async_tts_stream(dummy_async_http):
    """``AsyncTtsClient.stream`` should work similarly using awaitables."""

    client = AsyncAiolaClient(api_key="k")
    chunks = [c async for c in client.tts.stream(text="Async", voice="v")]  # exhaust

    assert chunks == [b"chunk1", b"chunk2"]

    recorded = dummy_async_http.stream_calls.pop()
    assert recorded["path"] == "/api/tts/stream"


@pytest.mark.anyio
async def test_async_tts_synthesize(dummy_async_http):
    """``AsyncTtsClient.synthesize`` POSTs to /synthesize endpoint."""

    client = AsyncAiolaClient(api_key="k")
    _ = [c async for c in client.tts.synthesize(text="Async", voice="v")]

    recorded = dummy_async_http.stream_calls.pop()
    assert recorded["path"] == "/api/tts/synthesize"


# ---------------------------------------------------------------------------
# Error propagation – ensure exceptions bubble up as AiolaError
# ---------------------------------------------------------------------------


def test_tts_stream_propagates_http_errors(monkeypatch):
    """If the underlying HTTP call fails, the exception should be wrapped in AiolaError."""

    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.tts.client

    # Mock auth client methods first
    def mock_get_access_token(self, options):
        return "fake_access_token"
    
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_get_access_token)

    class FailingHTTP(DummyHTTPClient):
        def stream(self, *a, **k):
            raise RuntimeError("http boom")

    def mock_create_authenticated_client(*args, **kwargs):
        return FailingHTTP()

    # Patch in the TTS client module where it's imported
    monkeypatch.setattr(aiola.clients.tts.client, "create_authenticated_client", mock_create_authenticated_client)

    client = AiolaClient(api_key="k")

    # Now wrapped in AiolaError instead of raw RuntimeError
    with pytest.raises(AiolaError, match="TTS streaming failed"):
        list(client.tts.stream(text="x", voice="v"))


@pytest.mark.anyio
async def test_async_tts_propagates_http_errors(monkeypatch):
    """Async variant must wrap HTTP errors in AiolaError."""

    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.tts.client

    # Mock auth client methods first
    def mock_get_access_token(self, options):
        return "fake_access_token"
    
    async def mock_async_get_access_token(self, options):
        return "fake_access_token"
    
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    class FailingAsyncHTTP(DummyAsyncHTTPClient):
        def stream(self, *a, **k):
            raise RuntimeError("async http boom")

    async def mock_create_async_authenticated_client(*args, **kwargs):
        return FailingAsyncHTTP()

    # Patch in the TTS client module where it's imported
    monkeypatch.setattr(aiola.clients.tts.client, "create_async_authenticated_client", mock_create_async_authenticated_client)

    client = AsyncAiolaClient(api_key="k")

    # Now wrapped in AiolaError instead of raw RuntimeError
    with pytest.raises(AiolaError, match="Async TTS streaming failed"):
        async for _ in client.tts.stream(text="fail", voice="v"):
            pass
