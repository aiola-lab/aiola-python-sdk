from __future__ import annotations

from typing import Any

import httpx


class AiolaError(Exception):
    """Base error raised by aiola-python SDK.

    All errors thrown by this SDK inherit from :class:`AiolaError` so that callers
    can rely on a single error type for predictable error handling.
    
    Attributes:
        message: Human-readable description of the error.
        reason: Detailed explanation from the server (if available).
        status: HTTP status code when the error originates from an HTTP response.
        code: Machine-readable error code for programmatic handling.
        details: Additional diagnostic information that may help debug the problem.
    
    Common error codes:
        - TOKEN_EXPIRED: Access token has expired and needs to be refreshed
        - INVALID_TOKEN: Access token is malformed or invalid
        - MAX_CONCURRENCY_REACHED: Too many concurrent sessions for your account
        - INVALID_AUDIO_FORMAT: The audio format is not supported
        - RATE_LIMIT_EXCEEDED: Too many requests in a short period
        - WORKFLOW_NOT_FOUND: The specified workflow ID does not exist
        - UNAUTHORIZED: Invalid API key or insufficient permissions
        - VALIDATION_ERROR: Request parameters are invalid
    
    Examples:
        >>> try:
        ...     result = client.stt.transcribe_file('audio.wav')
        ... except AiolaError as e:
        ...     print(f"Error: {e.message}")
        ...     print(f"Code: {e.code}")
        ...     print(f"Status: {e.status}")
        ...     if e.code == 'TOKEN_EXPIRED':
        ...         # Refresh token and retry
        ...         pass
    """

    def __init__(
        self,
        message: str,
        *,
        reason: str | None = None,
        status: int | None = None,
        code: str | None = None,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message  # Keep an explicit attribute – ``Exception`` drops it under ``__str__``
        self.reason: str | None = reason
        self.status: int | None = status
        self.code: str | None = code
        self.details: Any | None = details

    @classmethod
    def from_response(cls, response: httpx.Response) -> AiolaError:
        """Build an :class:`AiolaError` from an *unsuccessful* ``httpx.Response``.

        The method reads the body trying to extract a JSON payload in the shape::

            {"error": {"message": "...", "code": "...", "details": {...}}}

        and falls back to plain text otherwise.
        """

        message: str = f"Request failed with status {response.status_code}"
        reason: str | None = None
        code: str | None = None
        details: Any | None = None

        try:
            payload = response.json()
            if isinstance(payload, dict):
                reason = payload.get("message")
                code = payload.get("code")
                details = payload.get("details", payload)
        except ValueError:
            # Not JSON – try plain text
            reason = response.text

        return cls(message, reason=reason, status=response.status_code, code=code, details=details)

    def __str__(self) -> str:
        parts = [self.message]
        
        if self.reason is not None:
            parts.append(f"Reason: {self.reason}")
        
        return " | ".join(parts)


class AiolaConnectionError(AiolaError):
    """Raised when there are connectivity issues with the Aiola API.
    
    This error indicates network-level problems such as:
    - DNS resolution failures
    - Connection timeouts
    - Network unreachable errors
    - SSL/TLS handshake failures
    
    When raised:
        - During any HTTP request if network connection fails
        - When the API endpoint is unreachable
        - When network errors occur during file upload or streaming
    
    How to handle:
        - Check network connectivity
        - Verify firewall settings
        - Retry with exponential backoff
        - Check if the API endpoint URL is correct
    """

    pass


class AiolaAuthenticationError(AiolaError):
    """Raised when authentication fails.
    
    This error indicates authentication-related issues such as:
    - Invalid API key
    - Expired access token
    - Malformed access token
    - Missing authentication credentials
    - Unauthorized access to resources
    
    When raised:
        - When API key is invalid or missing
        - When access token has expired (typically after some time)
        - When access token is malformed or corrupted
        - When trying to access resources without proper permissions
        - HTTP 401 responses from the API
    
    How to handle:
        - Verify your API key is correct
        - Generate a new access token using grant_token()
        - Check that you're using a valid, non-expired token
        - Ensure your account has the necessary permissions
    
    Examples:
        >>> try:
        ...     result = client.stt.transcribe_file('audio.wav')
        ... except AiolaAuthenticationError as e:
        ...     if e.code == 'TOKEN_EXPIRED':
        ...         # Generate new token
        ...         token = AiolaClient.grant_token(api_key='your-key')
        ...         new_client = AiolaClient(access_token=token.access_token)
        ...         result = new_client.stt.transcribe_file('audio.wav')
    """

    pass


class AiolaValidationError(AiolaError):
    """Raised when input validation fails.
    
    This error indicates problems with the parameters provided to SDK methods:
    - Missing required parameters
    - Invalid parameter types
    - Invalid parameter values
    - Parameters out of acceptable range
    
    When raised:
        - When required parameters are missing (e.g., file, text, api_key)
        - When parameter types are incorrect (e.g., string expected but int provided)
        - When parameter values are invalid (e.g., empty string, negative numbers)
        - Before making API requests (client-side validation)
        - When API returns 400 Bad Request for invalid input
    
    How to handle:
        - Check the error message for specific validation failure
        - Verify all required parameters are provided
        - Ensure parameter types match expected types
        - Validate parameter values are within acceptable ranges
    
    Examples:
        >>> try:
        ...     stream = client.stt.stream(lang_code=123)  # Should be string
        ... except AiolaValidationError as e:
        ...     print(f"Validation error: {e.message}")
        ...     # Fix: stream = client.stt.stream(lang_code='en')
    """

    pass


class AiolaStreamingError(AiolaError):
    """Raised when streaming operations fail.
    
    This error indicates issues specific to real-time streaming:
    - WebSocket connection failures
    - Socket.IO connection issues
    - Connection drops during streaming
    - Failures to send or receive streaming data
    - Event handler registration failures
    
    When raised:
        - When failing to establish WebSocket connection
        - When connection drops unexpectedly during streaming
        - When unable to send audio data to the streaming service
        - When event handler registration fails
        - When disconnection fails
    
    How to handle:
        - Check network stability
        - Verify WebSocket connections are not blocked by firewall
        - Implement reconnection logic with exponential backoff
        - Listen to disconnect events and handle reconnection
        - Validate audio format meets requirements (16-bit PCM, 16kHz, mono)
    
    Examples:
        >>> try:
        ...     stream = client.stt.stream(lang_code='en')
        ...     stream.connect()
        ...     stream.send(audio_data)
        ... except AiolaStreamingError as e:
        ...     print(f"Streaming error: {e.message}")
        ...     # Attempt reconnection
        ...     stream.disconnect()
        ...     stream.connect()
    """

    pass


class AiolaFileError(AiolaError):
    """Raised when file operations fail.
    
    This error indicates issues with file handling:
    - Invalid or unsupported file format
    - File not found
    - File too large
    - File read/write errors
    - Corrupted file
    
    When raised:
        - When file parameter is None or missing
        - When file format is not supported (must be WAV, MP3, M4A, OGG, or FLAC)
        - When file path doesn't exist or is inaccessible
        - When file exceeds size limits
        - When file is corrupted or unreadable
    
    How to handle:
        - Verify file exists and is accessible
        - Check file format is supported
        - Ensure file is not corrupted
        - Check file size is within limits
        - Verify file permissions for reading
    
    Examples:
        >>> try:
        ...     result = client.stt.transcribe_file(None)
        ... except AiolaFileError as e:
        ...     print(f"File error: {e.message}")
        ...     # Fix: Provide valid file
        ...     result = client.stt.transcribe_file('audio.wav')
    """

    pass


class AiolaRateLimitError(AiolaError):
    """Raised when API rate limits are exceeded.
    
    This error indicates you've made too many requests in a short period:
    - Too many requests per second/minute/hour
    - Concurrent request limit exceeded
    - Quota exhausted
    
    When raised:
        - When HTTP 429 (Too Many Requests) is returned
        - When making requests too rapidly
        - When exceeding concurrent session limits
        - When account quota is exhausted
    
    How to handle:
        - Implement exponential backoff and retry logic
        - Reduce request rate
        - Close unused sessions
        - Check rate limit headers if available
        - Consider upgrading plan for higher limits
    
    Examples:
        >>> import time
        >>> try:
        ...     for i in range(100):
        ...         result = client.stt.transcribe_file(f'audio{i}.wav')
        ... except AiolaRateLimitError as e:
        ...     print(f"Rate limit exceeded: {e.message}")
        ...     time.sleep(60)  # Wait before retrying
    """

    pass


class AiolaServerError(AiolaError):
    """Raised when the Aiola API returns a server error (5xx status codes).
    
    This error indicates issues on the server side:
    - Internal server errors (500)
    - Service unavailable (503)
    - Gateway timeout (504)
    - Other server-side problems
    
    When raised:
        - When HTTP 500 (Internal Server Error) is returned
        - When HTTP 503 (Service Unavailable) is returned
        - When HTTP 504 (Gateway Timeout) is returned
        - When any other 5xx status code is returned
    
    How to handle:
        - Retry the request after a delay
        - Implement exponential backoff
        - Check service status page if available
        - Contact support if error persists
        - These are typically temporary issues
    
    Examples:
        >>> import time
        >>> max_retries = 3
        >>> for attempt in range(max_retries):
        ...     try:
        ...         result = client.stt.transcribe_file('audio.wav')
        ...         break
        ...     except AiolaServerError as e:
        ...         if attempt < max_retries - 1:
        ...             time.sleep(2 ** attempt)  # Exponential backoff
        ...         else:
        ...             raise
    """

    pass
