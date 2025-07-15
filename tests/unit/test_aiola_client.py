from unittest.mock import patch
import pytest

from aiola import AiolaClient, AsyncAiolaClient
from aiola.clients.auth.client import AuthClient, AsyncAuthClient
from aiola.constants import DEFAULT_AUTH_BASE_URL, DEFAULT_WORKFLOW_ID
from aiola.errors import AiolaValidationError


# ---------------------------------------------------------------------------
# Generic, user-facing client behaviour
# ---------------------------------------------------------------------------


def test_aiola_client_lazy_initialisation():
    """``AiolaClient`` should lazily instantiate sub-clients and cache them."""

    client = AiolaClient(api_key="test-key", base_url="https://example.com")

    # ``stt`` property
    stt_first = client.stt
    stt_second = client.stt
    assert stt_first is stt_second  # cached instance
    assert stt_first._options is client.options  # same options reference

    # ``tts`` property
    tts_first = client.tts
    tts_second = client.tts
    assert tts_first is tts_second
    assert tts_first._options is client.options

    # ``auth`` property
    auth_first = client.auth
    auth_second = client.auth
    assert auth_first is auth_second
    assert isinstance(auth_first, AuthClient)


def test_async_aiola_client_lazy_initialisation():
    """Async variant should follow the same lazy-instantiation pattern."""

    client = AsyncAiolaClient(api_key="test-key", base_url="https://example.com")

    stt_first = client.stt
    stt_second = client.stt
    assert stt_first is stt_second

    tts_first = client.tts
    tts_second = client.tts
    assert tts_first is tts_second

    auth_first = client.auth
    auth_second = client.auth
    assert auth_first is auth_second
    assert isinstance(auth_first, AsyncAuthClient)


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------


def test_aiola_client_constructor_with_api_key():
    """Test AiolaClient constructor with API key."""
    client = AiolaClient(api_key="test-key")
    assert client.options.api_key == "test-key"
    assert client.options.access_token is None


def test_aiola_client_constructor_with_access_token():
    """Test AiolaClient constructor with access token."""
    client = AiolaClient(access_token="test-token")
    assert client.options.access_token == "test-token"
    assert client.options.api_key is None


def test_aiola_client_constructor_with_both_credentials():
    """Test AiolaClient constructor with both API key and access token."""
    client = AiolaClient(api_key="test-key", access_token="test-token")
    assert client.options.api_key == "test-key"
    assert client.options.access_token == "test-token"


def test_aiola_client_constructor_with_base_url():
    """Test AiolaClient constructor with custom base URL."""
    client = AiolaClient(api_key="test-key", base_url="https://custom.api.com")
    assert client.options.base_url == "https://custom.api.com"


def test_aiola_client_constructor_no_credentials():
    """Test AiolaClient constructor with no credentials raises error."""
    with pytest.raises(AiolaValidationError, match="Either api_key or access_token must be provided"):
        AiolaClient()


def test_aiola_client_constructor_invalid_api_key():
    """Test AiolaClient constructor with invalid API key type."""
    with pytest.raises(AiolaValidationError, match="API key must be a string"):
        AiolaClient(api_key=123)


def test_aiola_client_constructor_invalid_access_token():
    """Test AiolaClient constructor with invalid access token type."""
    with pytest.raises(AiolaValidationError, match="Access token must be a string"):
        AiolaClient(access_token=123)


def test_aiola_client_constructor_invalid_base_url():
    """Test AiolaClient constructor with invalid base URL type."""
    with pytest.raises(AiolaValidationError, match="Base URL must be a string"):
        AiolaClient(api_key="test-key", base_url=123)


# ---------------------------------------------------------------------------
# Static grant_token method tests
# ---------------------------------------------------------------------------


def test_aiola_client_static_grant_token():
    """Test AiolaClient static grant_token method."""
    with patch.object(AuthClient, 'grant_token') as mock_grant:
        mock_grant.return_value = {"accessToken": "test-access-token", "sessionId": "session_789"}
        
        result = AiolaClient.grant_token("test-api-key")
        
        assert result == {"accessToken": "test-access-token", "sessionId": "session_789"}
        mock_grant.assert_called_once_with(
            api_key="test-api-key", 
            auth_base_url=DEFAULT_AUTH_BASE_URL, 
            workflow_id=DEFAULT_WORKFLOW_ID
        )


def test_aiola_client_static_grant_token_with_options():
    """Test AiolaClient static grant_token method with options."""
    with patch.object(AuthClient, 'grant_token') as mock_grant:
        mock_grant.return_value = {"accessToken": "test-access-token", "sessionId": "session_789"}
        
        result = AiolaClient.grant_token(
            "test-api-key", 
            auth_base_url="https://custom.api.com", 
            workflow_id="custom-workflow"
        )
        
        assert result == {"accessToken": "test-access-token", "sessionId": "session_789"}
        mock_grant.assert_called_once_with(
            api_key="test-api-key", 
            auth_base_url="https://custom.api.com", 
            workflow_id="custom-workflow"
        )


def test_aiola_client_static_grant_token_propagates_errors():
    """Test AiolaClient static grant_token method propagates errors."""
    error = Exception("Token generation failed")
    
    with patch.object(AuthClient, 'grant_token') as mock_grant:
        mock_grant.side_effect = error
        
        with pytest.raises(Exception, match="Token generation failed"):
            AiolaClient.grant_token("test-api-key")


# ---------------------------------------------------------------------------
# Async constructor tests
# ---------------------------------------------------------------------------


def test_async_aiola_client_constructor_with_api_key():
    """Test AsyncAiolaClient constructor with API key."""
    client = AsyncAiolaClient(api_key="test-key")
    assert client.options.api_key == "test-key"
    assert client.options.access_token is None


def test_async_aiola_client_constructor_with_access_token():
    """Test AsyncAiolaClient constructor with access token."""
    client = AsyncAiolaClient(access_token="test-token")
    assert client.options.access_token == "test-token"
    assert client.options.api_key is None


def test_async_aiola_client_constructor_no_credentials():
    """Test AsyncAiolaClient constructor with no credentials raises error."""
    with pytest.raises(AiolaValidationError, match="Either api_key or access_token must be provided"):
        AsyncAiolaClient()


# ---------------------------------------------------------------------------
# Async static grant_token method tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_aiola_client_static_grant_token():
    """Test AsyncAiolaClient static grant_token method."""
    with patch.object(AsyncAuthClient, 'async_grant_token') as mock_grant:
        mock_grant.return_value = {"accessToken": "test-access-token", "sessionId": "session_789"}
        
        result = await AsyncAiolaClient.grant_token("test-api-key")
        
        assert result == {"accessToken": "test-access-token", "sessionId": "session_789"}
        mock_grant.assert_called_once_with(
            api_key="test-api-key", 
            auth_base_url=DEFAULT_AUTH_BASE_URL, 
            workflow_id=DEFAULT_WORKFLOW_ID
        )


@pytest.mark.asyncio
async def test_async_aiola_client_static_grant_token_with_options():
    """Test AsyncAiolaClient static grant_token method with options."""
    with patch.object(AsyncAuthClient, 'async_grant_token') as mock_grant:
        mock_grant.return_value = {"accessToken": "test-access-token", "sessionId": "session_789"}
        
        result = await AsyncAiolaClient.grant_token(
            "test-api-key", 
            auth_base_url="https://custom.api.com", 
            workflow_id="custom-workflow"
        )
        
        assert result == {"accessToken": "test-access-token", "sessionId": "session_789"}
        mock_grant.assert_called_once_with(
            api_key="test-api-key", 
            auth_base_url="https://custom.api.com", 
            workflow_id="custom-workflow"
        )
