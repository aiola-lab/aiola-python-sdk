from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

try:
    import numpy as np
    import sounddevice as sd
except (ImportError, OSError):
    # ImportError: sounddevice/numpy not installed
    # OSError: PortAudio library not found (common in CI environments)
    sd = None
    np = None

if TYPE_CHECKING:
    import numpy as np
    import sounddevice as sd

# Default values for microphone stream
CHANNELS = 1
SAMPLE_RATE = 16000
BLOCK_SIZE = 4096
DTYPE = "int16"


class MicrophoneStream:
    """
    A microphone stream class that handles audio capture from the microphone
    and provides a simple interface for streaming audio data.
    """

    def __init__(
        self,
        channels: int = CHANNELS,
        samplerate: int = SAMPLE_RATE,
        blocksize: int = BLOCK_SIZE,
        dtype: str = DTYPE,
        device: int | None = None,
    ):
        """
        Initialize the microphone stream.

        Args:
            channels: Number of audio channels (default: 1)
            samplerate: Sample rate in Hz (default: 16000)
            blocksize: Number of frames per buffer (default: 4096)
            dtype: Audio data type (default: "int16")
            device: Index of the input device to use (default: None for default device)
        """
        if sd is None or np is None:
            raise ImportError(
                "sounddevice and numpy are required for microphone functionality. "
                "Install them with: pip install 'aiola[mic]'\n"
                "Note: This also requires system PortAudio libraries."
            )

        self.channels = channels
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.dtype = dtype
        self.device = device

        self._stream: Any | None = None
        self._is_recording = False
        self._thread: threading.Thread | None = None
        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        self._on_audio_callback: Callable[[bytes], None] | None = None
        self._on_error_callback: Callable[[Exception], None] | None = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def _audio_callback(self, indata: Any, frames: int, time: Any, status: Any) -> None:
        """Internal callback for sounddevice stream."""
        if status and self._on_error_callback:
            self._on_error_callback(Exception(f"Audio callback status: {status}"))

        # Convert numpy array to bytes
        audio_bytes = indata.astype(self.dtype).tobytes()
        self._audio_queue.put(audio_bytes)

    def start(self) -> None:
        """Start the microphone stream."""
        if self._is_recording:
            return

        self._stream = sd.InputStream(
            device=self.device,
            channels=self.channels,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            dtype=self.dtype,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._is_recording = True

    def stop(self) -> None:
        """Stop the microphone stream."""
        if not self._is_recording:
            return

        self._is_recording = False

        if self._thread and self._thread.is_alive():
            self._thread.join()

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Clear the audio queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

    def read(self, timeout: float | None = None) -> bytes:
        """
        Read audio data from the microphone.

        Args:
            timeout: Timeout in seconds to wait for audio data (default: None for blocking)

        Returns:
            Audio data as bytes

        Raises:
            RuntimeError: If the stream is not started
            queue.Empty: If timeout is reached
        """
        if not self._is_recording or not self._stream:
            raise RuntimeError("Microphone stream is not started")

        return self._audio_queue.get(timeout=timeout)

    def stream_to(
        self,
        connection: Any,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """
        Stream audio data to a connection (e.g., STT streaming connection).

        Args:
            connection: The connection object to send audio data to
            on_error: Optional callback for handling errors

        Raises:
            RuntimeError: If the stream is not started
        """
        if not self._is_recording:
            raise RuntimeError("Microphone stream is not started")

        self._on_error_callback = on_error

        def _stream_worker():
            try:
                while self._is_recording:
                    try:
                        audio_data = self.read(timeout=0.1)
                        # Check if connection is still active before sending
                        if hasattr(connection, "connected") and not connection.connected:
                            break
                        connection.send(audio_data)
                    except queue.Empty:
                        continue
                    except Exception as e:
                        if self._on_error_callback:
                            self._on_error_callback(e)
                        else:
                            raise
            except Exception as e:
                if self._on_error_callback:
                    self._on_error_callback(e)
                else:
                    raise

        self._thread = threading.Thread(target=_stream_worker, daemon=True)
        self._thread.start()

    def stream_with_callback(
        self,
        callback: Callable[[bytes], None],
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """
        Stream audio data to a callback function.

        Args:
            callback: Function to call with audio data
            on_error: Optional callback for handling errors

        Raises:
            RuntimeError: If the stream is not started
        """
        if not self._is_recording:
            raise RuntimeError("Microphone stream is not started")

        self._on_audio_callback = callback
        self._on_error_callback = on_error

        def _stream_worker():
            try:
                while self._is_recording:
                    try:
                        audio_data = self.read(timeout=0.1)
                        if self._on_audio_callback:
                            self._on_audio_callback(audio_data)
                    except queue.Empty:
                        continue
                    except Exception as e:
                        if self._on_error_callback:
                            self._on_error_callback(e)
                        else:
                            raise
            except Exception as e:
                if self._on_error_callback:
                    self._on_error_callback(e)
                else:
                    raise

        self._thread = threading.Thread(target=_stream_worker, daemon=True)
        self._thread.start()

    @property
    def is_recording(self) -> bool:
        """Check if the microphone is currently recording."""
        return self._is_recording

    @classmethod
    def list_devices(cls) -> list[dict]:
        """
        List available audio input devices.

        Returns:
            List of dictionaries containing device information
        """
        if sd is None:
            raise ImportError(
                "sounddevice is required for microphone functionality. "
                "Install it with: pip install 'aiola[mic]'\n"
                "Note: This also requires system PortAudio libraries."
            )

        devices = []
        device_list = sd.query_devices()

        for i, device_info in enumerate(device_list):
            if device_info["max_input_channels"] > 0:
                devices.append(
                    {
                        "index": i,
                        "name": device_info["name"],
                        "channels": device_info["max_input_channels"],
                        "sample_rate": device_info["default_samplerate"],
                        "hostapi": device_info["hostapi"],
                    }
                )

        return devices
