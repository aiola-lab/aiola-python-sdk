from collections.abc import Callable
from typing import Any

import socketio

from ...errors import AiolaError, AiolaStreamingError, AiolaValidationError
from ...types import AiolaClientOptions, LiveEvents


class StreamConnection:
    """Stream connection for the STT client."""

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
        )

    def connect(self) -> None:
        """Establish the socket connection using stored parameters."""
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
        """Send binary audio data."""
        if not self.connected:
            raise AiolaError("Connection not established")

        if not isinstance(data, bytes):
            raise AiolaValidationError("Data must be bytes")

        try:
            self._sio.emit("binary_data", data, namespace=self._namespace)
        except Exception as exc:
            raise AiolaStreamingError("Failed to send audio data") from exc

    def set_keywords(self, keywords: dict[str, str]) -> None:
        """Send keywords list to the server."""
        if not isinstance(keywords, dict):
            raise AiolaValidationError("Keywords must be a dict")

        if not all(isinstance(value, str) for value in keywords.values()):
            raise AiolaValidationError("All keywords must be strings")

        try:
            self._sio.emit("set_keywords", keywords, namespace=self._namespace)
        except Exception as exc:
            raise AiolaStreamingError("Failed to send keywords") from exc

    def disconnect(self) -> None:
        """Disconnect the socket connection."""
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
    """Async stream connection for the STT client."""

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
        )

    async def connect(self) -> None:
        """Establish the socket connection using stored parameters."""
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

    async def send(self, data: bytes) -> None:
        """Send binary audio data."""
        if not self.connected:
            raise AiolaError("Connection not established")

        if not isinstance(data, bytes):
            raise AiolaValidationError("Data must be bytes")

        try:
            await self._sio.emit("binary_data", data, namespace=self._namespace)
        except Exception as exc:
            raise AiolaStreamingError("Failed to send audio data") from exc

    async def set_keywords(self, keywords: dict[str, str]) -> None:
        """Send keywords list to the server."""
        if not isinstance(keywords, dict):
            raise AiolaValidationError("Keywords must be a dict")

        if not all(isinstance(value, str) for value in keywords.values()):
            raise AiolaValidationError("All keywords must be strings")

        try:
            await self._sio.emit("set_keywords", keywords, namespace=self._namespace)
        except Exception as exc:
            raise AiolaStreamingError("Failed to send keywords") from exc

    async def disconnect(self) -> None:
        """Disconnect the socket connection."""
        if self._sio.connected:
            try:
                await self._sio.disconnect()
            except Exception as exc:
                raise AiolaStreamingError("Failed to disconnect") from exc

    @property
    def connected(self) -> bool:
        """Check if the connection is active."""
        return self._sio.connected
