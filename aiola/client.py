from __future__ import annotations

from .clients.auth.client import AsyncAuthClient, AuthClient
from .clients.stt.client import AsyncSttClient, SttClient
from .clients.tts.client import AsyncTtsClient, TtsClient
from .constants import DEFAULT_AUTH_BASE_URL, DEFAULT_BASE_URL, DEFAULT_HTTP_TIMEOUT, DEFAULT_WORKFLOW_ID
from .errors import AiolaError, AiolaValidationError
from .types import AiolaClientOptions, GrantTokenResponse, SessionCloseResponse


class AiolaClient:
    """Aiola SDK."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        access_token: str | None = None,
        base_url: str | None = None,
        auth_base_url: str | None = None,
        workflow_id: str = DEFAULT_WORKFLOW_ID,
        timeout: int = DEFAULT_HTTP_TIMEOUT,
    ):
        # Initialize lazy-loaded clients
        self._stt: SttClient | None = None
        self._tts: TtsClient | None = None
        self._auth: AuthClient | None = None

        try:
            self._options = AiolaClientOptions(
                base_url=base_url or DEFAULT_BASE_URL,
                auth_base_url=auth_base_url or DEFAULT_AUTH_BASE_URL,
                api_key=api_key,
                access_token=access_token,
                workflow_id=workflow_id,
                timeout=timeout,
            )
        except (ValueError, TypeError) as exc:
            raise AiolaValidationError(str(exc)) from exc
        except Exception as exc:
            raise AiolaError("Failed to initialize client options") from exc

    @property
    def options(self) -> AiolaClientOptions:
        return self._options

    @property
    def stt(self) -> SttClient:
        if self._stt is None:
            try:
                self._stt = SttClient(self._options, self.auth)
            except Exception as exc:
                raise AiolaError("Failed to initialize STT client") from exc
        return self._stt

    @property
    def tts(self) -> TtsClient:
        if self._tts is None:
            try:
                self._tts = TtsClient(self._options, self.auth)
            except Exception as exc:
                raise AiolaError("Failed to initialize TTS client") from exc
        return self._tts

    @property
    def auth(self) -> AuthClient:
        if self._auth is None:
            try:
                self._auth = AuthClient(options=self._options)
            except Exception as exc:
                raise AiolaError("Failed to initialize Auth client") from exc
        return self._auth

    @staticmethod
    def grant_token(
        api_key: str, auth_base_url: str = DEFAULT_AUTH_BASE_URL, workflow_id: str = DEFAULT_WORKFLOW_ID
    ) -> GrantTokenResponse:
        """
        Generate an access token from an API key.
        This is the recommended way to generate tokens in backend services.

        Args:
            api_key: The API key to use for token generation
            auth_base_url: Optional base URL for the API
            workflow_id: Optional workflow ID for the API

        Returns:
            The generated access token and session ID

        Example:
            ```python
            result = AiolaClient.grant_token('your-api-key')
            client = AiolaClient(access_token=result.access_token)
            ```
        """
        return AuthClient.grant_token(api_key=api_key, auth_base_url=auth_base_url, workflow_id=workflow_id)

    @staticmethod
    def close_session(access_token: str, auth_base_url: str = DEFAULT_AUTH_BASE_URL) -> SessionCloseResponse:
        """
        Close a session and free up concurrency slots.
        This is useful for cleaning up resources when done with a session.

        Args:
            access_token: The access token to close the session for
            auth_base_url: Optional base URL for the API

        Returns:
            The session close response

        Example:
            ```python
            result = AiolaClient.close_session('your-access-token')
            print(f"Session closed: {result.status}")
            ```
        """
        return AuthClient.close_session(access_token=access_token, auth_base_url=auth_base_url)


class AsyncAiolaClient:
    """Asynchronous Aiola SDK."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        access_token: str | None = None,
        base_url: str | None = None,
        auth_base_url: str | None = None,
        workflow_id: str = DEFAULT_WORKFLOW_ID,
    ):
        # Initialize lazy-loaded clients
        self._stt: AsyncSttClient | None = None
        self._tts: AsyncTtsClient | None = None
        self._auth: AsyncAuthClient | None = None

        try:
            self._options = AiolaClientOptions(
                base_url=base_url or DEFAULT_BASE_URL,
                auth_base_url=auth_base_url or DEFAULT_AUTH_BASE_URL,
                api_key=api_key,
                access_token=access_token,
                workflow_id=workflow_id,
            )
        except (ValueError, TypeError) as exc:
            raise AiolaValidationError(str(exc)) from exc
        except Exception as exc:
            raise AiolaError("Failed to initialize client options") from exc

    @property
    def options(self) -> AiolaClientOptions:
        return self._options

    @property
    def stt(self) -> AsyncSttClient:
        if self._stt is None:
            try:
                self._stt = AsyncSttClient(self._options, self.auth)
            except Exception as exc:
                raise AiolaError("Failed to initialize async STT client") from exc
        return self._stt

    @property
    def tts(self) -> AsyncTtsClient:
        if self._tts is None:
            try:
                self._tts = AsyncTtsClient(self._options, self.auth)
            except Exception as exc:
                raise AiolaError("Failed to initialize async TTS client") from exc
        return self._tts

    @property
    def auth(self) -> AsyncAuthClient:
        if self._auth is None:
            try:
                self._auth = AsyncAuthClient(options=self._options)
            except Exception as exc:
                raise AiolaError("Failed to initialize async Auth client") from exc
        return self._auth

    @staticmethod
    async def grant_token(
        api_key: str, auth_base_url: str = DEFAULT_AUTH_BASE_URL, workflow_id: str = DEFAULT_WORKFLOW_ID
    ) -> GrantTokenResponse:
        """
        Generate an access token from an API key.
        This is the recommended way to generate tokens in backend services.

        Args:
            api_key: The API key to use for token generation
            auth_base_url: Optional base URL for the API
            workflow_id: Optional workflow ID for the API

        Returns:
            The generated access token and session ID

        Example:
            ```python
            result = await AsyncAiolaClient.grant_token('your-api-key')
            client = AsyncAiolaClient(access_token=result.access_token)
            ```
        """
        return await AsyncAuthClient.async_grant_token(
            api_key=api_key, auth_base_url=auth_base_url, workflow_id=workflow_id
        )

    @staticmethod
    async def close_session(access_token: str, auth_base_url: str = DEFAULT_AUTH_BASE_URL) -> SessionCloseResponse:
        """
        Close a session and free up concurrency slots.
        This is useful for cleaning up resources when done with a session.

        Args:
            access_token: The access token to close the session for
            auth_base_url: Optional base URL for the API

        Returns:
            The session close response

        Example:
            ```python
            result = await AsyncAiolaClient.close_session('your-access-token')
            print(f"Session closed: {result.status}")
            ```
        """
        return await AsyncAuthClient.close_session(access_token=access_token, auth_base_url=auth_base_url)
