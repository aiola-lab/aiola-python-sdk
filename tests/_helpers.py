from typing import AsyncIterator, Iterator


class DummySocketClient:
    """Sync stub mimicking :class:`socketio.Client`."""

    def __init__(self, *args, **kwargs):
        self.init_args = args
        self.init_kwargs = kwargs
        self.connected = False
        self.connect_args: tuple = ()
        self.connect_kwargs: dict | None = None
        self.event_handlers: dict = {}
        self.emit_calls: list = []

    def connect(self, *args, **kwargs):
        """Pretend to establish a connection and record parameters."""
        self.connect_args = args
        self.connect_kwargs = kwargs
        self.connected = True

    def on(self, event: str, handler, namespace: str = None):
        """Register an event handler."""
        key = f"{event}:{namespace}" if namespace else event
        self.event_handlers[key] = handler

    def emit(self, event: str, data, namespace: str = None):
        """Record emit calls for testing."""
        self.emit_calls.append({
            "event": event,
            "data": data,
            "namespace": namespace
        })

    def disconnect(self):
        """Disconnect the socket."""
        self.connected = False

    def __repr__(self):
        return f"<DummySocketClient connected={self.connected}>"


class DummyAsyncSocketClient(DummySocketClient):
    async def connect(self, *args, **kwargs):
        super().connect(*args, **kwargs)

    async def emit(self, event: str, data, namespace: str = None):
        """Record emit calls for testing (async version)."""
        self.emit_calls.append({
            "event": event,
            "data": data,
            "namespace": namespace
        })

    async def disconnect(self):
        """Disconnect the socket (async version)."""
        self.connected = False


class DummyResponse:
    """Emulates :pyclass:`httpx.Response` for streaming tests (sync)."""

    def __init__(self, chunks: list[bytes], json_data: dict | None = None):
        self._chunks = chunks
        self._json_data = json_data or {}

    # Synchronous iterator – mirrors *iter_bytes* API
    def iter_bytes(self) -> Iterator[bytes]:
        yield from self._chunks

    def json(self) -> dict:
        """Return JSON data for non-streaming responses."""
        return self._json_data

    def raise_for_status(self) -> None:
        """Mock raise_for_status - does nothing for successful responses."""
        pass

    # Context-manager helpers -------------------------------------------------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Do *not* suppress exceptions.
        return False


class DummyAsyncResponse(DummyResponse):
    async def aiter_bytes(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            yield chunk

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class DummyHTTPClient:
    """Collects calls made through *stream* and *post* for assertion convenience (sync)."""

    def __init__(self):
        self.stream_calls: list[dict] = []
        self.post_calls: list[dict] = []

    def stream(self, method, path, *, headers, json):
        self.stream_calls.append(
            {
                "method": method,
                "path": path,
                "headers": headers,
                "json": json,
            }
        )
        return DummyResponse([b"chunk1", b"chunk2"])

    def post(self, path, *, files=None, data=None, json=None):
        """Mock POST request for file uploads."""
        self.post_calls.append(
            {
                "path": path,
                "files": files,
                "data": data,
                "json": json,
            }
        )
        # Return a mock transcription response
        return DummyResponse(
            chunks=[],
            json_data={
                "transcript": "Hello, this is a test transcription.",
                "confidence": 0.95,
                "language": "en"
            }
        )

    # Context manager support for httpx.Client compatibility
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class DummyAsyncHTTPClient(DummyHTTPClient):
    def stream(self, method, path, *, headers, json):
        """Return an async-compatible context manager mimicking httpx.stream.

        Although the *real* httpx ``stream`` is a *sync* method that returns an
        *async* context manager (when using ``AsyncClient``), keeping this
        function synchronous means our production code can directly use
        ``async with client.stream(...)`` without needing an intermediate
        ``await`` call. The returned :class:`DummyAsyncResponse` implements the
        asynchronous context-manager protocol, so everything fits together.
        """

        self.stream_calls.append(
            {
                "method": method,
                "path": path,
                "headers": headers,
                "json": json,
            }
        )
        return DummyAsyncResponse([b"chunk1", b"chunk2"])

    async def post(self, path, *, files=None, data=None, json=None):
        """Mock async POST request for file uploads."""
        self.post_calls.append(
            {
                "path": path,
                "files": files,
                "data": data,
                "json": json,
            }
        )
        # Return a mock transcription response
        return DummyResponse(
            chunks=[],
            json_data={
                "transcript": "Hello, this is a test transcription.",
                "confidence": 0.95,
                "language": "en"
            }
        )

    # Async context manager support for httpx.AsyncClient compatibility
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False
