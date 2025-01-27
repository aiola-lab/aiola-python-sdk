"""
AiolaStreamingClient - Main client for handling audio streaming and Socket.IO connections.
"""

import socketio
import time
import sounddevice as sd
from typing import Dict
from urllib.parse import urlencode

from .models.config import StreamingConfig
from .models.stats import StreamingStats
from .services.auth import get_auth_headers

class CustomSocketIOClient(socketio.Client):
    def __init__(self, custom_headers=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_headers = custom_headers or {}

    def connect(self, *args, **kwargs):
        # Save a reference to the original method
        original_send_request = self.eio._send_request

        # Define a patched method that includes the custom headers
        def custom_send_request(method, url, headers=None, body=None, timeout=None):
            if headers is None:
                headers = {}
            headers.update(self.custom_headers)  # Inject custom headers
            return original_send_request(method, url, headers=headers, body=body, timeout=timeout)

        # Patch the method
        self.eio._send_request = custom_send_request

        # Call the original connect method
        super().connect(*args, **kwargs)


class AiolaStreamingClient:
    """
    Client for streaming audio and handling real-time transcription.

    Attributes:
        config (StreamingConfig): Configuration for the streaming client
        sio (socketio.Client): Socket.IO client instance
        stats (StreamingStats): Statistics about the streaming session
    """

    def __init__(self, config: StreamingConfig):
        """
        Initialize the streaming client.

        Args:
            config (StreamingConfig): Configuration for the streaming client
        """

        self.config = config
        auth_headers = get_auth_headers(
            auth_type=self.config.auth_type,
            auth_credentials=self.config.auth_credentials
        )
        self.sio = CustomSocketIOClient(auth_headers.headers)
        self.stats = StreamingStats()
        self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Set up Socket.IO event handlers for various events."""

        @self.sio.event(namespace=self.config.namespace)
        def connect() -> None:
            """Handle connection event."""
            self.stats.connection_start_time = time.time()
            if self.config.callbacks.on_connect:
                self.config.callbacks.on_connect()

        @self.sio.event(namespace=self.config.namespace)
        def disconnect() -> None:
            """Handle disconnection event."""
            if self.config.callbacks.on_disconnect:
                connection_duration = time.time() - (self.stats.connection_start_time or 0)
                self.config.callbacks.on_disconnect(
                    connection_duration,
                    self.stats.total_audio_sent_duration
                )

        @self.sio.event(namespace=self.config.namespace)
        def transcript(data: Dict, ack=None) -> None:
            """
            Handle transcript events.

            Args:
                data: Transcript data from the server
                ack: Acknowledgment callback
            """
            if self.config.callbacks.on_transcript:
                self.config.callbacks.on_transcript(data)
            if ack:
                ack({"status": "received"})

        @self.sio.event(namespace=self.config.namespace)
        def events(data: Dict, ack=None) -> None:
            """
            Handle general events.

            Args:
                data: Event data from the server
                ack: Acknowledgment callback
            """
            if self.config.callbacks.on_events:
                self.config.callbacks.on_events(data)
            if ack:
                ack({"status": "received"})

        @self.sio.event(namespace=self.config.namespace)
        def error(data: Dict) -> None:
            """
            Handle error events.

            Args:
                data: Error data from the server
            """
            if self.config.callbacks.on_error:
                self.config.callbacks.on_error(data)

    def _get_connection_params(self) -> Dict[str, str]:
        """
        Get connection parameters for the streaming URL.

        Returns:
            Dict[str, str]: URL parameters
        """
        return {
            'flow_id': self.config.flow_id,
            'execution_id': self.config.execution_id,
            'lang_code': self.config.lang_code,
            'time_zone': self.config.time_zone
        }

    def _start_audio_streaming(self) -> None:
        """Start streaming audio from the microphone."""

        def audio_callback(data, frames, time, status):
            """Handle audio data from the microphone."""
            if not self.sio.connected:
                return

            if status and self.config.callbacks.on_error:
                self.config.callbacks.on_error({"audio_status": status})

            if data is not None:
                self.sio.emit("binary_data", bytes(data), namespace=self.config.namespace)

        with sd.RawInputStream(
            samplerate=self.config.audio.sample_rate,
            channels=self.config.audio.channels,
            blocksize=self.config.audio.chunk_size,
            dtype=self.config.audio.dtype,
            callback=audio_callback,
        ):
            self.sio.wait()

    async def start_streaming(self, silent: bool = False) -> None:
        """
        Start streaming audio to the server asynchronously.

        Args:
            silent (bool): If True, don't stream audio from the microphone
        """
        try:
            # Get authentication headers
            auth_headers = get_auth_headers(
                auth_type=self.config.auth_type,
                auth_credentials=self.config.auth_credentials
            )

            # Build connection URL
            params = self._get_connection_params()
            url = f"{str(self.config.endpoint)}{str(self.config.namespace)}/?{urlencode(params)}"

            _transports = ['polling'] if self.config.transports == 'polling' else ['polling', 'websocket'] if self.config.transports == 'websocket' else ['polling', 'websocket']

            namespaces = [self.config.namespace]
            if self.config.namespace != '/':
                namespaces.append('/')

            # Connect to the server
            self.sio.connect(
                url=url,
                transports=_transports,
                headers=auth_headers.headers,
                socketio_path='/api/voice-streaming/socket.io',
                namespaces=namespaces
            )

            # Start streaming or wait
            if self.config.use_buildin_mic:
                if not silent:
                    self._start_audio_streaming()
                else:
                    self.sio.wait()

        except Exception as e:
            print(f"Streaming error: {e}")
            await self.sio.disconnect()


    def disconnect(self) -> None:
        """Disconnect from the streaming server."""
        if self.sio.connected:
            self.sio.disconnect()