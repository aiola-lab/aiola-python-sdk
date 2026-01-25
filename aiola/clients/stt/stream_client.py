from collections.abc import Callable
from typing import Any

import socketio

from ...constants import DEFAULT_SOCKET_TIMEOUT
from ...errors import AiolaError, AiolaStreamingError, AiolaValidationError
from ...types import AiolaClientOptions, LiveEvents


class StreamConnection:
    """Real-time audio streaming connection for transcription.
    
    Manages a Socket.IO connection for bidirectional communication with the Aiola
    streaming service. Handles automatic reconnection and provides event-based
    communication for real-time transcription.
    
    Audio must be sent as 16-bit PCM format at 16kHz sample rate, mono channel.
    
    Examples:
        >>> # Create and use a streaming connection
        >>> stream = client.stt.stream(lang_code='en')
        >>> 
        >>> # Register event handlers
        >>> @stream.on(LiveEvents.Transcript)
        >>> def on_transcript(data):
        >>>     print(f"Transcript: {data['transcript']}")
        >>> 
        >>> # Or using direct registration
        >>> stream.on(LiveEvents.Connect, lambda: print("Connected"))
        >>> 
        >>> # Connect and start streaming
        >>> stream.connect()
        >>> stream.send(audio_data)
        >>> 
        >>> # Clean up
        >>> stream.disconnect()
    """

    def __init__(
        self,
        options: AiolaClientOptions,
        url: str,
        headers: dict[str, str],
        socketio_path: str,
        namespace: str = "/events",
    ):
        self._options = options
        self._url = url
        self._headers = headers
        self._socketio_path = socketio_path
        self._namespace = namespace
        self._sio: socketio.Client = socketio.Client(
            reconnection=True,
            reconnection_attempts=3,
            reconnection_delay=1,
            request_timeout=DEFAULT_SOCKET_TIMEOUT,
        )

    def connect(self) -> None:
        """Establish the Socket.IO connection to the streaming service.
        
        Creates a WebSocket connection for real-time audio streaming. The connection
        automatically uses the URL, headers, and parameters configured during
        initialization. Supports automatic reconnection up to 3 attempts.
        
        If already connected, this method returns without creating a new connection.
        
        Raises:
            AiolaStreamingError: If connection fails.
        
        Examples:
            >>> stream.on(LiveEvents.Connect, lambda: print("Connected!"))
            >>> stream.connect()
        """
        if self._sio.connected:
            return  # Already connected

        try:
            self._sio.connect(
                url=self._url,
                headers=self._headers,
                socketio_path=self._socketio_path,
                namespaces=[self._namespace],
                wait=True,
                transports=["polling", "websocket"],
            )
        except Exception as exc:
            raise AiolaStreamingError("Failed to connect to Streaming service") from exc

    def on(self, event: LiveEvents, handler: Callable[..., Any] | None = None) -> Callable[..., Any]:
        """Register an event handler."""
        if not isinstance(event, LiveEvents) or not event:
            raise AiolaValidationError("Event name must be a non-empty string")

        try:
            if handler is None:
                # Decorator usage: @connection.on(LiveEvents.Transcript)
                def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                    if not callable(func):
                        raise AiolaValidationError("Event handler must be callable")
                    self._sio.on(event, func, namespace=self._namespace)
                    return func

                return decorator
            else:
                # Direct usage: connection.on(LiveEvents.Transcript, lambda x: print(x))
                if not callable(handler):
                    raise AiolaValidationError("Event handler must be callable")
                self._sio.on(event, handler, namespace=self._namespace)
                return handler
        except (AiolaError, AiolaValidationError):
            raise
        except Exception as exc:
            raise AiolaStreamingError(f"Failed to register event handler for '{event}'") from exc

    def send(self, data: bytes) -> None:
        """Send audio data to the streaming service.
        
        Audio must be in 16-bit PCM format at 16kHz sample rate, mono channel.
        Send audio in chunks as it becomes available (typically 100-1000ms chunks).
        
        Args:
            data: Audio data in bytes (16-bit PCM, 16kHz, mono).
        
        Raises:
            AiolaError: If connection is not established.
            AiolaValidationError: If data is not bytes.
            AiolaStreamingError: If sending data fails.
        
        Examples:
            >>> # Send audio chunk
            >>> stream.send(audio_bytes)
            
            >>> # Stream from microphone
            >>> while recording:
            >>>     chunk = microphone.read()
            >>>     stream.send(chunk)
        """
        if not self.connected:
            raise AiolaError("Connection not established")

        if not isinstance(data, bytes):
            raise AiolaValidationError("Data must be bytes")

        try:
            self._sio.emit("binary_data", data, namespace=self._namespace)
        except Exception as exc:
            raise AiolaStreamingError("Failed to send audio data") from exc

    def set_keywords(self, keywords: dict[str, str]) -> None:
        """Set or update keywords for recognition boosting.
        
        Keywords are used to improve recognition accuracy for specific terms or phrases.
        The dictionary maps spoken phrases to their written forms.
        
        Args:
            keywords: Dictionary mapping spoken phrases to written forms.
                Example: {'eye ola': 'Aiola', 'open AI': 'OpenAI'}
        
        Raises:
            AiolaValidationError: If keywords is not a dict or values are not strings.
            AiolaStreamingError: If sending keywords fails.
        
        Examples:
            >>> stream.set_keywords({
            >>>     'aiola': 'Aiola',
            >>>     'API': 'API',
            >>>     'docker': 'Docker'
            >>> })
        """
        if not isinstance(keywords, dict):
            raise AiolaValidationError("Keywords must be a dict")

        if not all(isinstance(value, str) for value in keywords.values()):
            raise AiolaValidationError("All keywords must be strings")

        try:
            self._sio.emit("set_keywords", keywords, namespace=self._namespace)
        except Exception as exc:
            raise AiolaStreamingError("Failed to send keywords") from exc

    def disconnect(self) -> None:
        """Close the Socket.IO connection to the streaming service.
        
        Gracefully terminates the connection. Always disconnect when finished to
        free up server resources. If not connected, this method returns without error.
        
        Raises:
            AiolaStreamingError: If disconnection fails.
        
        Examples:
            >>> stream.disconnect()
            >>> print("Disconnected from streaming service")
        """
        if self._sio.connected:
            try:
                self._sio.disconnect()
            except Exception as exc:
                raise AiolaStreamingError("Failed to disconnect cleanly") from exc

    @property
    def connected(self) -> bool:
        """Check if the connection is active."""
        return self._sio.connected


class AsyncStreamConnection:
    """Asynchronous real-time audio streaming connection for transcription.
    
    Manages an async Socket.IO connection for bidirectional communication with the
    Aiola streaming service. Use this in async applications for better performance
    and concurrency.
    
    Audio must be sent as 16-bit PCM format at 16kHz sample rate, mono channel.
    
    Examples:
        >>> # Create and use an async streaming connection
        >>> stream = await client.stt.stream(lang_code='en')
        >>> 
        >>> # Register event handlers
        >>> @stream.on(LiveEvents.Transcript)
        >>> def on_transcript(data):
        >>>     print(f"Transcript: {data['transcript']}")
        >>> 
        >>> # Connect and start streaming
        >>> await stream.connect()
        >>> await stream.send(audio_data)
        >>> 
        >>> # Clean up
        >>> await stream.disconnect()
    """

    def __init__(
        self,
        options: AiolaClientOptions,
        url: str,
        headers: dict[str, str],
        socketio_path: str,
        namespace: str = "/events",
    ):
        self._options = options
        self._url = url
        self._headers = headers
        self._socketio_path = socketio_path
        self._namespace = namespace
        self._sio: socketio.AsyncClient = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=3,
            reconnection_delay=1,
            request_timeout=DEFAULT_SOCKET_TIMEOUT,
        )

    async def connect(self) -> None:
        """Asynchronously establish the Socket.IO connection.
        
        Creates a WebSocket connection for real-time audio streaming using async/await.
        Supports automatic reconnection up to 3 attempts.
        
        Raises:
            AiolaStreamingError: If connection fails.
        
        Examples:
            >>> stream.on(LiveEvents.Connect, lambda: print("Connected!"))
            >>> await stream.connect()
        """
        if self._sio.connected:
            return  # Already connected

        try:
            await self._sio.connect(
                url=self._url,
                headers=self._headers,
                socketio_path=self._socketio_path,
                namespaces=[self._namespace],
                wait=True,
                transports=["polling", "websocket"],
            )
        except Exception as exc:
            raise AiolaStreamingError("Failed to connect to Streaming service") from exc

    def on(self, event: LiveEvents, handler: Callable[..., Any] | None = None) -> Callable[..., Any]:
        """Register an event handler for async streaming events.
        
        Can be used as a decorator or called directly. Handlers can be regular
        functions or async functions.
        
        Args:
            event: The event to listen for (from LiveEvents enum).
            handler: Optional event handler function.
        
        Returns:
            The registered handler function (or decorator if handler is None).
        
        Raises:
            AiolaValidationError: If event or handler is invalid.
            AiolaStreamingError: If registration fails.
        
        Examples:
            >>> # Decorator usage
            >>> @stream.on(LiveEvents.Transcript)
            >>> async def handle_transcript(data):
            >>>     await process_transcript(data['transcript'])
            
            >>> # Direct usage
            >>> stream.on(LiveEvents.Connect, lambda: print("Connected"))
        """
        if not isinstance(event, LiveEvents) or not event:
            raise AiolaValidationError("Event name must be a non-empty string")

        try:
            if handler is None:
                # Decorator usage: @connection.on(LiveEvents.Transcript)
                def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                    if not callable(func):
                        raise AiolaValidationError("Event handler must be callable")
                    self._sio.on(event, func, namespace=self._namespace)
                    return func

                return decorator
            else:
                # Direct usage: connection.on(LiveEvents.Transcript, lambda x: print(x))
                if not callable(handler):
                    raise AiolaValidationError("Event handler must be callable")
                self._sio.on(event, handler, namespace=self._namespace)
                return handler
        except (AiolaError, AiolaValidationError):
            raise
        except Exception as exc:
            raise AiolaStreamingError(f"Failed to register event handler for '{event}'") from exc

    async def send(self, data: bytes) -> None:
        """Asynchronously send audio data to the streaming service.
        
        Audio must be in 16-bit PCM format at 16kHz sample rate, mono channel.
        
        Args:
            data: Audio data in bytes (16-bit PCM, 16kHz, mono).
        
        Raises:
            AiolaError: If connection is not established.
            AiolaValidationError: If data is not bytes.
            AiolaStreamingError: If sending data fails.
        
        Examples:
            >>> await stream.send(audio_bytes)
        """
        if not self.connected:
            raise AiolaError("Connection not established")

        if not isinstance(data, bytes):
            raise AiolaValidationError("Data must be bytes")

        try:
            await self._sio.emit("binary_data", data, namespace=self._namespace)
        except Exception as exc:
            raise AiolaStreamingError("Failed to send audio data") from exc

    async def set_keywords(self, keywords: dict[str, str]) -> None:
        """Asynchronously set or update keywords for recognition boosting.
        
        Args:
            keywords: Dictionary mapping spoken phrases to written forms.
        
        Raises:
            AiolaValidationError: If keywords format is invalid.
            AiolaStreamingError: If sending keywords fails.
        
        Examples:
            >>> await stream.set_keywords({'aiola': 'Aiola', 'API': 'API'})
        """
        if not isinstance(keywords, dict):
            raise AiolaValidationError("Keywords must be a dict")

        if not all(isinstance(value, str) for value in keywords.values()):
            raise AiolaValidationError("All keywords must be strings")

        try:
            await self._sio.emit("set_keywords", keywords, namespace=self._namespace)
        except Exception as exc:
            raise AiolaStreamingError("Failed to send keywords") from exc

    async def disconnect(self) -> None:
        """Asynchronously close the Socket.IO connection.
        
        Gracefully terminates the connection using async/await.
        
        Raises:
            AiolaStreamingError: If disconnection fails.
        
        Examples:
            >>> await stream.disconnect()
        """
        if self._sio.connected:
            try:
                await self._sio.disconnect()
            except Exception as exc:
                raise AiolaStreamingError("Failed to disconnect") from exc

    @property
    def connected(self) -> bool:
        """Check if the connection is active."""
        return self._sio.connected
