from __future__ import annotations

import pytest

from tests._helpers import (
    DummySocketClient,
    DummyAsyncSocketClient,
    DummyHTTPClient,
    DummyAsyncHTTPClient,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def patch_dummy_socket(monkeypatch):
    """Replace *socketio.Client* with a synchronous dummy implementation.

    This avoids external network calls during tests and lets us easily introspect
    the parameters passed to ``connect``.
    """
    import aiola.clients.stt.stream_client as stream_module
    from aiola.clients.auth.client import AuthClient, AsyncAuthClient

    # Mock socket client
    monkeypatch.setattr(stream_module.socketio, "Client", DummySocketClient)
    
    # Mock auth client methods to prevent real HTTP requests
    def mock_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_get_access_token)
    
    yield  # ``monkeypatch`` automatically restores the original attribute.


@pytest.fixture
def patch_dummy_async_socket(monkeypatch):
    """Patch *socketio.AsyncClient* with an async dummy implementation."""
    import aiola.clients.stt.stream_client as stream_module
    from aiola.clients.auth.client import AuthClient, AsyncAuthClient

    # Mock socket client
    monkeypatch.setattr(stream_module.socketio, "AsyncClient", DummyAsyncSocketClient)
    
    # Mock auth client methods to prevent real HTTP requests
    def mock_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    async def mock_async_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)
    
    yield


@pytest.fixture
def dummy_http(monkeypatch):
    """Provide a patched HTTP client factory returning :class:`DummyHTTPClient`."""
    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.tts.client
    import aiola.clients.stt.client

    # Mock auth client methods
    def mock_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    async def mock_async_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    # Mock HTTP client factory
    client = DummyHTTPClient()
    
    def mock_create_authenticated_client(*args, **kwargs):
        return client
    
    # Patch in all the places where it's imported
    monkeypatch.setattr(aiola.clients.tts.client, "create_authenticated_client", mock_create_authenticated_client)
    monkeypatch.setattr(aiola.clients.stt.client, "create_authenticated_client", mock_create_authenticated_client)
    return client


@pytest.fixture
def dummy_async_http(monkeypatch):
    """Provide a patched async HTTP client factory returning :class:`DummyAsyncHTTPClient`."""
    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.tts.client
    import aiola.clients.stt.client

    # Mock auth client methods
    def mock_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    async def mock_async_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    # Mock HTTP client factory
    client = DummyAsyncHTTPClient()
    
    async def mock_create_async_authenticated_client(*args, **kwargs):
        return client
    
    # Patch in all the places where it's imported
    monkeypatch.setattr(aiola.clients.tts.client, "create_async_authenticated_client", mock_create_async_authenticated_client)
    monkeypatch.setattr(aiola.clients.stt.client, "create_async_authenticated_client", mock_create_async_authenticated_client)
    return client


@pytest.fixture
def dummy_stt_http(monkeypatch):
    """Provide a patched HTTP client factory for STT client returning :class:`DummyHTTPClient`."""
    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.stt.client

    # Mock auth client methods
    def mock_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    async def mock_async_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    # Mock HTTP client factory
    client = DummyHTTPClient()
    
    def mock_create_authenticated_client(*args, **kwargs):
        return client
    
    monkeypatch.setattr(aiola.clients.stt.client, "create_authenticated_client", mock_create_authenticated_client)
    return client


@pytest.fixture
def dummy_async_stt_http(monkeypatch):
    """Provide a patched async HTTP client factory for STT client returning :class:`DummyAsyncHTTPClient`."""
    from aiola.clients.auth.client import AuthClient, AsyncAuthClient
    import aiola.clients.stt.client

    # Mock auth client methods
    def mock_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    async def mock_async_get_access_token(self, access_token, api_key, workflow_id):
        return "fake_access_token"
    
    monkeypatch.setattr(AuthClient, "get_access_token", mock_get_access_token)
    monkeypatch.setattr(AsyncAuthClient, "get_access_token", mock_async_get_access_token)

    # Mock HTTP client factory
    client = DummyAsyncHTTPClient()
    
    async def mock_create_async_authenticated_client(*args, **kwargs):
        return client
    
    monkeypatch.setattr(aiola.clients.stt.client, "create_async_authenticated_client", mock_create_async_authenticated_client)
    return client
