import base64
import json
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock

import pytest
import httpx

from aiola.clients.auth.client import AuthClient, AsyncAuthClient, BaseAuthClient
from aiola.constants import DEFAULT_AUTH_BASE_URL, DEFAULT_WORKFLOW_ID
from aiola.errors import AiolaError
from aiola.types import AiolaClientOptions, GrantTokenResponse


class TestAuthClient:
    """Test suite for AuthClient."""

    def setup_method(self):
        """Setup method called before each test."""
        self.mock_api_key = "test_api_key_123"
        self.mock_temp_token = "temp_token_456"
        self.mock_access_token = "access_token_789"
        self.auth = AuthClient(AiolaClientOptions(
            auth_base_url="https://test.example.com",
            api_key="test_key",
            workflow_id=DEFAULT_WORKFLOW_ID
        ))

    @patch('httpx.Client')
    def test_static_grant_token_success(self, mock_client_class):
        """Test successful token generation using static method."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock responses for token and session endpoints
        token_response = Mock()
        token_response.is_success = True
        token_response.json.return_value = {
            "context": {"token": self.mock_temp_token}
        }

        session_response = Mock()
        session_response.is_success = True
        session_response.json.return_value = {
            "jwt": self.mock_access_token,
            "sessionId": "session_789"
        }

        mock_client.post.side_effect = [token_response, session_response]

        # Test the static method
        result = BaseAuthClient.grant_token(
            self.mock_api_key,
            DEFAULT_AUTH_BASE_URL,
            DEFAULT_WORKFLOW_ID
        )

        assert result.accessToken == self.mock_access_token
        assert result.sessionId == "session_789"
        assert mock_client.post.call_count == 2

    @patch('httpx.Client')
    def test_static_grant_token_with_custom_base_url(self, mock_client_class):
        """Test token generation with custom base URL."""
        custom_base_url = "https://custom.api.com"

        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock responses
        token_response = Mock()
        token_response.is_success = True
        token_response.json.return_value = {
            "context": {"token": self.mock_temp_token}
        }

        session_response = Mock()
        session_response.is_success = True
        session_response.json.return_value = {
            "jwt": self.mock_access_token,
            "sessionId": "session_789"
        }

        mock_client.post.side_effect = [token_response, session_response]

        result = BaseAuthClient.grant_token(
            self.mock_api_key,
            custom_base_url,
            DEFAULT_WORKFLOW_ID
        )

        assert result.accessToken == self.mock_access_token
        assert result.sessionId == "session_789"
        # Verify the custom base URL was used in the endpoint calls
        calls = mock_client.post.call_args_list
        assert custom_base_url in calls[0][0][0]  # First call (token endpoint)
        assert custom_base_url in calls[1][0][0]  # Second call (session endpoint)

    @patch('httpx.Client')
    def test_static_grant_token_with_custom_workflow_id(self, mock_client_class):
        """Test token generation with custom workflow ID."""
        custom_workflow_id = "custom_workflow_123"

        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock responses
        token_response = Mock()
        token_response.is_success = True
        token_response.json.return_value = {
            "context": {"token": self.mock_temp_token}
        }

        session_response = Mock()
        session_response.is_success = True
        session_response.json.return_value = {
            "jwt": self.mock_access_token,
            "sessionId": "session_789"
        }

        mock_client.post.side_effect = [token_response, session_response]

        result = BaseAuthClient.grant_token(
            self.mock_api_key,
            DEFAULT_AUTH_BASE_URL,
            custom_workflow_id
        )

        assert result.accessToken == self.mock_access_token
        assert result.sessionId == "session_789"
        # Check that the workflow ID was included in the session request
        session_call = mock_client.post.call_args_list[1]
        session_body = session_call[1]["json"]
        assert session_body["workflow_id"] == custom_workflow_id

    def test_static_grant_token_empty_api_key(self):
        """Test error when API key is not provided."""
        with pytest.raises(AiolaError, match="API key is required"):
            BaseAuthClient.grant_token("", DEFAULT_AUTH_BASE_URL, DEFAULT_WORKFLOW_ID)

    @patch('httpx.Client')
    def test_static_grant_token_token_failure(self, mock_client_class):
        """Test error when token generation fails."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock failed token response
        token_response = Mock()
        token_response.is_success = False
        token_response.status_code = 401

        mock_client.post.return_value = token_response

        with pytest.raises(AiolaError):
            BaseAuthClient.grant_token(self.mock_api_key, DEFAULT_AUTH_BASE_URL, DEFAULT_WORKFLOW_ID)

    def test_instance_grant_token_delegates_to_static(self):
        """Test that instance method delegates to static method."""
        with patch.object(BaseAuthClient, 'grant_token') as mock_static:
            mock_static.return_value = GrantTokenResponse(accessToken=self.mock_access_token, sessionId="session_789")

            result = self.auth.grant_token(self.mock_api_key, "https://test.example.com", DEFAULT_WORKFLOW_ID)

            assert result.accessToken == self.mock_access_token
        assert result.sessionId == "session_789"
        mock_static.assert_called_once_with(
                api_key=self.mock_api_key,
                auth_base_url="https://test.example.com",
                workflow_id=DEFAULT_WORKFLOW_ID
            )

    def test_instance_grant_token_with_custom_workflow_id(self):
        """Test instance method with custom workflow ID."""
        custom_workflow_id = "custom_workflow_123"

        with patch.object(BaseAuthClient, 'grant_token') as mock_static:
            mock_static.return_value = GrantTokenResponse(accessToken=self.mock_access_token, sessionId="session_789")

            result = self.auth.grant_token(self.mock_api_key, "https://test.example.com", custom_workflow_id)

            assert result.accessToken == self.mock_access_token
        assert result.sessionId == "session_789"
        mock_static.assert_called_once_with(
                api_key=self.mock_api_key,
                auth_base_url="https://test.example.com",
                workflow_id=custom_workflow_id
            )

    def test_instance_grant_token_empty_api_key(self):
        """Test error when API key is not provided to instance method."""
        with pytest.raises(AiolaError, match="API key is required"):
            self.auth.grant_token("", "https://test.example.com", DEFAULT_WORKFLOW_ID)

    def test_get_access_token_with_valid_access_token(self):
        """Test returning provided access token when valid."""
        # Create a valid JWT token (expires in 1 hour)
        future_exp = int(time.time()) + 3600  # 1 hour from now
        payload = {"exp": future_exp, "iat": int(time.time())}
        encoded_payload = base64.b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=').replace('+', '-').replace('/', '_')
        valid_access_token = f"header.{encoded_payload}.signature"

        result = self.auth.get_access_token(valid_access_token, "", DEFAULT_WORKFLOW_ID)

        assert result == valid_access_token

    def test_get_access_token_with_expired_access_token(self):
        """Test error when access token is expired."""
        # Create an expired JWT token (expired 1 hour ago)
        past_exp = int(time.time()) - 3600  # 1 hour ago
        payload = {"exp": past_exp, "iat": int(time.time()) - 7200}
        encoded_payload = base64.b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=').replace('+', '-').replace('/', '_')
        expired_access_token = f"header.{encoded_payload}.signature"

        with pytest.raises(AiolaError, match="Provided access token is expired"):
            self.auth.get_access_token(expired_access_token, "", DEFAULT_WORKFLOW_ID)

    def test_get_access_token_no_credentials(self):
        """Test error when neither apiKey nor accessToken is provided."""
        with pytest.raises(AiolaError, match="No valid credentials provided"):
            self.auth.get_access_token("", "", DEFAULT_WORKFLOW_ID)

    def test_parse_jwt_payload_valid_token(self):
        """Test JWT payload parsing with valid token."""
        payload = {"exp": 1234567890, "iat": 1234567000}
        encoded_payload = base64.b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=').replace('+', '-').replace('/', '_')
        token = f"header.{encoded_payload}.signature"

        result = self.auth._parse_jwt_payload(token)

        assert result["exp"] == 1234567890
        assert result["iat"] == 1234567000

    def test_parse_jwt_payload_invalid_format(self):
        """Test JWT payload parsing with invalid format."""
        invalid_token = "invalid.token"

        with pytest.raises(AiolaError, match="Failed to parse JWT payload"):
            self.auth._parse_jwt_payload(invalid_token)

    def test_clear_session(self):
        """Test clearing session cache."""
        # Set some cached values
        self.auth._access_token = "cached_token"
        self.auth._session_id = "cached_session"

        self.auth.clear_session()

        assert self.auth._access_token is None
        assert self.auth._session_id is None


class TestAsyncAuthClient:
    """Test cases for AsyncAuthClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.auth = AsyncAuthClient(AiolaClientOptions(
            auth_base_url="https://test.example.com",
            api_key="test_key",
            workflow_id=DEFAULT_WORKFLOW_ID
        ))
        self.mock_api_key = "test_api_key_123"
        self.mock_temp_token = "temp_token_456"
        self.mock_access_token = "access_token_789"

    @patch('aiola.clients.auth.client.httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_static_grant_token_success(self, mock_client_class):
        """Test successful async token generation using static method."""
        # Mock responses for token and session endpoints
        token_response = Mock()
        token_response.is_success = True
        token_response.json.return_value = {
            "context": {"token": self.mock_temp_token}
        }

        session_response = Mock()
        session_response.is_success = True
        session_response.json.return_value = {
            "jwt": self.mock_access_token,
            "sessionId": "session_789"
        }

        # Create an async mock client
        mock_client = AsyncMock()
        mock_client.post.side_effect = [token_response, session_response]

        # Mock the AsyncClient context manager
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client_class.return_value.__aexit__.return_value = None

        # Test the static method
        result = await BaseAuthClient.async_grant_token(
            self.mock_api_key,
            DEFAULT_AUTH_BASE_URL,
            DEFAULT_WORKFLOW_ID
        )

        assert result.accessToken == self.mock_access_token
        assert result.sessionId == "session_789"
        # Verify that post was called twice (token then session)
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_instance_grant_token_delegates_to_static(self):
        """Test that async instance method delegates to static method."""
        with patch.object(BaseAuthClient, 'async_grant_token') as mock_static:
            mock_static.return_value = GrantTokenResponse(accessToken=self.mock_access_token, sessionId="session_789")

            result = await self.auth.grant_token(self.mock_api_key, "https://test.example.com", DEFAULT_WORKFLOW_ID)

            assert result.accessToken == self.mock_access_token
        assert result.sessionId == "session_789"
        mock_static.assert_called_once_with(
                self.mock_api_key,
                "https://test.example.com",
                DEFAULT_WORKFLOW_ID
            )

    @pytest.mark.asyncio
    async def test_get_access_token_with_valid_access_token(self):
        """Test async returning provided access token when valid."""
        # Create a valid JWT token (expires in 1 hour)
        future_exp = int(time.time()) + 3600  # 1 hour from now
        payload = {"exp": future_exp, "iat": int(time.time())}
        encoded_payload = base64.b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=').replace('+', '-').replace('/', '_')
        valid_access_token = f"header.{encoded_payload}.signature"

        result = await self.auth.get_access_token(valid_access_token, "", DEFAULT_WORKFLOW_ID)

        assert result == valid_access_token

    @pytest.mark.asyncio
    async def test_get_access_token_with_expired_access_token(self):
        """Test async error when access token is expired."""
        # Create an expired JWT token (expired 1 hour ago)
        past_exp = int(time.time()) - 3600  # 1 hour ago
        payload = {"exp": past_exp, "iat": int(time.time()) - 7200}
        encoded_payload = base64.b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=').replace('+', '-').replace('/', '_')
        expired_access_token = f"header.{encoded_payload}.signature"

        with pytest.raises(AiolaError, match="Provided access token is expired"):
            await self.auth.get_access_token(expired_access_token, "", DEFAULT_WORKFLOW_ID)

    @pytest.mark.asyncio
    async def test_get_access_token_no_credentials(self):
        """Test async error when neither apiKey nor accessToken is provided."""
        with pytest.raises(AiolaError, match="No valid credentials provided"):
            await self.auth.get_access_token("", "", DEFAULT_WORKFLOW_ID)

    def test_clear_session_async(self):
        """Test clearing async session cache."""
        # Set some cached values
        self.auth._access_token = "cached_token"
        self.auth._session_id = "cached_session"

        self.auth.clear_session()

        assert self.auth._access_token is None
        assert self.auth._session_id is None
