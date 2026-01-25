from __future__ import annotations

from .clients.auth.client import AsyncAuthClient, AuthClient
from .clients.stt.client import AsyncSttClient, SttClient
from .clients.tts.client import AsyncTtsClient, TtsClient
from .constants import DEFAULT_AUTH_BASE_URL, DEFAULT_BASE_URL, DEFAULT_HTTP_TIMEOUT, DEFAULT_WORKFLOW_ID
from .errors import AiolaError, AiolaValidationError
from .types import AiolaClientOptions, GrantTokenResponse, SessionCloseResponse


class AiolaClient:
    """Main client for interacting with the Aiola API (synchronous).

    Provides access to Speech-to-Text (STT), Text-to-Speech (TTS), and authentication services.
    The client uses lazy initialization for service clients, creating them only when first accessed.

    You can initialize the client with either an API key (for automatic token management) or
    a pre-generated access token.

    Examples:
        Using API key (recommended for backend services):
        >>> client = AiolaClient(api_key='your-api-key')
        >>> transcription = client.stt.transcribe_file('audio.wav')

        Using access token:
        >>> token_response = AiolaClient.grant_token(api_key='your-api-key')
        >>> client = AiolaClient(access_token=token_response.access_token)
        >>> transcription = client.stt.transcribe_file('audio.wav')

        Custom configuration:
        >>> client = AiolaClient(
        ...     api_key='your-api-key',
        ...     base_url='https://custom-api.aiola.com',
        ...     timeout=60
        ... )
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        access_token: str | None = None,
        base_url: str | None = None,
        auth_base_url: str | None = None,
        workflow_id: str | None = DEFAULT_WORKFLOW_ID,
        timeout: int | None = DEFAULT_HTTP_TIMEOUT,
    ):
        """Initialize the Aiola client.

        Either api_key or access_token must be provided. If both are provided,
        access_token takes precedence.

        Args:
            api_key: Your Aiola API key. If provided, the client will automatically
                manage access tokens.
            access_token: A pre-generated access token from grant_token(). Use this
                for more control over token lifecycle.
            base_url: Optional custom API base URL. Defaults to production endpoint.
            auth_base_url: Optional custom authentication base URL. Defaults to
                production authentication endpoint.
            workflow_id: Optional custom workflow ID. Workflows define the AI
                processing pipeline. Defaults to the standard workflow.
            timeout: HTTP request timeout in seconds. Defaults to 150 seconds.

        Raises:
            AiolaValidationError: If neither api_key nor access_token is provided,
                or if parameters are invalid.
            AiolaError: If client initialization fails.

        Examples:
            >>> # Using API key
            >>> client = AiolaClient(api_key='your-api-key')

            >>> # Using access token
            >>> token = AiolaClient.grant_token('your-api-key')
            >>> client = AiolaClient(access_token=token.access_token)

            >>> # With custom configuration
            >>> client = AiolaClient(
            ...     api_key='your-api-key',
            ...     base_url='https://custom.aiola.com',
            ...     timeout=60
            ... )
        """
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
        """Get the client configuration options.

        Returns the resolved configuration including default values for any
        options that were not explicitly provided during construction.

        Returns:
            AiolaClientOptions: The client configuration.
        """
        return self._options

    @property
    def stt(self) -> SttClient:
        """Get the Speech-to-Text (STT) client.

        Provides access to transcription services including file transcription
        and real-time streaming. The client is lazily initialized on first access.

        Returns:
            SttClient: The STT client instance.

        Raises:
            AiolaError: If STT client initialization fails.

        Examples:
            >>> # Transcribe a file
            >>> result = client.stt.transcribe_file('audio.wav', language='en')

            >>> # Start a streaming session
            >>> stream = client.stt.stream(lang_code='en')
        """
        if self._stt is None:
            try:
                self._stt = SttClient(self._options, self.auth)
            except Exception as exc:
                raise AiolaError("Failed to initialize STT client") from exc
        return self._stt

    @property
    def tts(self) -> TtsClient:
        """Get the Text-to-Speech (TTS) client.

        Provides access to speech synthesis services. The client is lazily
        initialized on first access.

        Returns:
            TtsClient: The TTS client instance.

        Raises:
            AiolaError: If TTS client initialization fails.

        Examples:
            >>> # Synthesize text to speech
            >>> audio_data = client.tts.synthesize(
            ...     text='Hello world',
            ...     voice_id='en-US-JennyNeural'
            ... )
        """
        if self._tts is None:
            try:
                self._tts = TtsClient(self._options, self.auth)
            except Exception as exc:
                raise AiolaError("Failed to initialize TTS client") from exc
        return self._tts

    @property
    def auth(self) -> AuthClient:
        """Get the authentication client.

        Used internally for token management and validation. The client is lazily
        initialized on first access. Most users will not need to access this directly.

        Returns:
            AuthClient: The authentication client instance.

        Raises:
            AiolaError: If Auth client initialization fails.
        """
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
    """Main client for interacting with the Aiola API (asynchronous).

    Provides async/await access to Speech-to-Text (STT), Text-to-Speech (TTS), and
    authentication services. Use this client in async applications for better
    performance and concurrency.

    The client uses lazy initialization for service clients, creating them only when
    first accessed.

    You can initialize the client with either an API key (for automatic token management)
    or a pre-generated access token.

    Examples:
        Using API key (recommended for backend services):
        >>> client = AsyncAiolaClient(api_key='your-api-key')
        >>> transcription = await client.stt.transcribe_file('audio.wav')

        Using access token:
        >>> token_response = await AsyncAiolaClient.grant_token(api_key='your-api-key')
        >>> client = AsyncAiolaClient(access_token=token_response.access_token)
        >>> transcription = await client.stt.transcribe_file('audio.wav')

        Custom configuration:
        >>> client = AsyncAiolaClient(
        ...     api_key='your-api-key',
        ...     base_url='https://custom-api.aiola.com'
        ... )
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        access_token: str | None = None,
        base_url: str | None = None,
        auth_base_url: str | None = None,
        workflow_id: str = DEFAULT_WORKFLOW_ID,
    ):
        """Initialize the async Aiola client.

        Either api_key or access_token must be provided. If both are provided,
        access_token takes precedence.

        Args:
            api_key: Your Aiola API key. If provided, the client will automatically
                manage access tokens.
            access_token: A pre-generated access token from grant_token(). Use this
                for more control over token lifecycle.
            base_url: Optional custom API base URL. Defaults to production endpoint.
            auth_base_url: Optional custom authentication base URL. Defaults to
                production authentication endpoint.
            workflow_id: Optional custom workflow ID. Workflows define the AI
                processing pipeline. Defaults to the standard workflow.

        Raises:
            AiolaValidationError: If neither api_key nor access_token is provided,
                or if parameters are invalid.
            AiolaError: If client initialization fails.

        Examples:
            >>> # Using API key
            >>> client = AsyncAiolaClient(api_key='your-api-key')

            >>> # Using access token
            >>> token = await AsyncAiolaClient.grant_token('your-api-key')
            >>> client = AsyncAiolaClient(access_token=token.access_token)

            >>> # With custom configuration
            >>> client = AsyncAiolaClient(
            ...     api_key='your-api-key',
            ...     base_url='https://custom.aiola.com'
            ... )
        """
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
        """Get the client configuration options.

        Returns the resolved configuration including default values for any
        options that were not explicitly provided during construction.

        Returns:
            AiolaClientOptions: The client configuration.
        """
        return self._options

    @property
    def stt(self) -> AsyncSttClient:
        """Get the Speech-to-Text (STT) client.

        Provides async access to transcription services including file transcription
        and real-time streaming. The client is lazily initialized on first access.

        Returns:
            AsyncSttClient: The async STT client instance.

        Raises:
            AiolaError: If STT client initialization fails.

        Examples:
            >>> # Transcribe a file
            >>> result = await client.stt.transcribe_file('audio.wav', language='en')

            >>> # Start a streaming session
            >>> stream = await client.stt.stream(lang_code='en')
        """
        if self._stt is None:
            try:
                self._stt = AsyncSttClient(self._options, self.auth)
            except Exception as exc:
                raise AiolaError("Failed to initialize async STT client") from exc
        return self._stt

    @property
    def tts(self) -> AsyncTtsClient:
        """Get the Text-to-Speech (TTS) client.

        Provides async access to speech synthesis services. The client is lazily
        initialized on first access.

        Returns:
            AsyncTtsClient: The async TTS client instance.

        Raises:
            AiolaError: If TTS client initialization fails.

        Examples:
            >>> # Synthesize text to speech
            >>> async for chunk in client.tts.synthesize(
            ...     text='Hello world',
            ...     voice_id='en-US-JennyNeural'
            ... ):
            ...     # Process audio chunk
            ...     pass
        """
        if self._tts is None:
            try:
                self._tts = AsyncTtsClient(self._options, self.auth)
            except Exception as exc:
                raise AiolaError("Failed to initialize async TTS client") from exc
        return self._tts

    @property
    def auth(self) -> AsyncAuthClient:
        """Get the authentication client.

        Used internally for token management and validation. The client is lazily
        initialized on first access. Most users will not need to access this directly.

        Returns:
            AsyncAuthClient: The async authentication client instance.

        Raises:
            AiolaError: If Auth client initialization fails.
        """
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
