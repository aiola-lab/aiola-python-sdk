"""
AiolaStreamingClient - Main client for handling audio streaming and Socket.IO connections.
"""

import asyncio
import json
import logging
import os
import tempfile
import time as pytime
import wave
from typing import AsyncGenerator, Dict, List, Optional
from urllib.parse import urlencode

import aiofiles
import av  # For mp4 extraction
import numpy as np
import sounddevice as sd
import soundfile as sf
from av.audio.resampler import AudioResampler
from scipy.signal import resample_poly

from .config import AiolaConfig
from .errors import AiolaError, AiolaErrorCode

# Constants
AUDIO_CHUNK_SIZE = 8192  # Maximum size of audio chunks in bytes
REQUIRED_SAMPLE_RATE = 16000  # Required sample rate in Hz for audio processing
SILENCE_DURATION_MS = 500  # Silence duration in milliseconds

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("aiola_streaming_sdk")
logger.setLevel("INFO")


class AiolaSttClient:
    """
    Client for streaming audio and handling real-time transcription.
    """

    def __init__(self, config: AiolaConfig, sio_client_factory=None):
        """
        Initialize the streaming client.

        Args:
            config (AiolaSocketConfig): Configuration for the streaming client
            sio_client_factory (optional): Factory function to create socketio client (for testing/mocking)
        """
        self.config = config
        self.config.events = config.events
        self.namespace = "/events"

        if sio_client_factory is None:
            import socketio  # noqa: F401

            self._sio_factory = lambda: socketio.AsyncClient()
        else:
            self._sio_factory = sio_client_factory
        self.sio = self._sio_factory()
        self.audio_stream: Optional[sd.RawInputStream] = None
        self.recording_in_progress: bool = False
        self.is_stopping_recording: bool = False
        self.active_keywords: List[str] = []
        self._streaming_task: Optional[asyncio.Task] = None
        self._setup_event_handlers()

    async def connect(
        self,
        auto_record: bool = False,
        custom_stream_generator: Optional[AsyncGenerator[bytes, None]] = None,
    ) -> None:
        """
        Connect to the aiOla streaming service.
        ```bash
        Args:
            auto_record (bool):  If True, automatically start recording/streaming after connection.
            custom_stream_generator (Optional[AsyncGenerator[bytes, None]]): Optional async generator for custom audio streaming.
                - The audio source must have the following format:
                    - sample_rate: 16000 Hz
                    - chunk_size: 4096 bytes MAX
                    - channels: 1 (mono)

                - Behavior:
                    - If auto_record is True:
                        - If provided: uses the custom generator for streaming.
                        - If None: uses the built-in microphone for recording.
        ```
        """
        # Re-initialize self.sio if it was cleaned up
        if self.sio is None:
            self.sio = self._sio_factory()
            self._setup_event_handlers()
        try:
            # Only cleanup if there's an existing connection
            if self.sio and self.sio.connected:
                await self._cleanup_socket()

            # Build connection URL and parameters
            base_url = self.config.base_url
            params = {
                **self.config.query_params.model_dump(),
            }
            if self.config.vad_config is not None:
                logger.debug("VAD config is set")
                params["vad_config"] = json.dumps(
                    {
                        "vad_threshold": self.config.vad_config.vad_threshold,
                        "min_silence_duration_ms": self.config.vad_config.min_silence_duration_ms,
                    }
                )
            else:
                print("VAD config is not set")
            logger.debug("Connection parameters: %s", params)

            # Encode parameters into URL
            url = f"{base_url}/?{urlencode(params)}"

            # Configure transports
            _transports = (
                ["polling"]
                if self.config.transports == "polling"
                else (
                    ["websocket", "polling"]
                    if self.config.transports == "websocket"
                    else ["websocket", "polling"]
                )
            )

            # Connect to the server
            await self.sio.connect(
                url=url,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                transports=_transports,
                socketio_path="/api/voice-streaming/socket.io",
                namespaces=[self.namespace],
            )

            if auto_record:
                self.start_recording(custom_stream_generator)

            # If there are active keywords, resend them on reconnection
            if self.active_keywords:
                await self.set_keywords(self.active_keywords)

        except Exception as e:
            self._handle_error(
                f"Failed to connect: {str(e)}",
                AiolaErrorCode.NETWORK_ERROR,
                {"original_error": str(e)},
            )
            await self._cleanup_socket()
            raise

    async def disconnect(self) -> None:
        """Disconnect from the server and clean up resources."""
        await self.stop_recording()
        await self._cleanup_socket()

    def start_recording(
        self, custom_stream_generator: Optional[AsyncGenerator[bytes, None]] = None
    ) -> None:
        """
        Start recording/streaming audio.
        ```bash
        Args:
            custom_stream_generator:  Optional async generator for custom audio streaming.
                - The audio source must have the following format:
                    - sample_rate: 16000 Hz
                    - chunk_size: 4096 bytes MAX
                    - channels: 1 (mono)

                - Behavior:
                    - If auto_record is True:
                        - If provided: uses the custom generator for streaming.
                        - If None: uses the built-in microphone for recording.
        ```
         Raises:
            AiolaError: With AiolaErrorCode.STREAMING_ERROR if:
                - Socket is not connected
                - Audio chunk size exceeds AUDIO_CHUNK_SIZE
                - Error occurs during streaming
        """
        if not self.sio or not self.sio.connected:
            logger.error("Cannot start recording: Socket is not connected")
            self._handle_error(
                "Socket is not connected. Please call connect first.",
                AiolaErrorCode.MIC_ERROR,
            )
            return

        if self.recording_in_progress:
            logger.warning("Recording is already in progress")
            self._handle_error(
                "Recording is already in progress. Please stop the current recording first.",
                AiolaErrorCode.MIC_ALREADY_IN_USE,
            )
            return

        try:
            self.recording_in_progress = True
            if self.config.events.get("on_start_record"):
                self.config.events["on_start_record"]()

            # Create the appropriate streaming task
            if custom_stream_generator:
                self._streaming_task = asyncio.create_task(
                    self._start_stream(custom_stream_generator)
                )
            else:
                # Create microphone generator without awaiting it
                mic_generator = self._create_mic_stream_generator()
                self._streaming_task = asyncio.create_task(
                    self._start_stream(mic_generator)
                )

        except Exception as e:
            self.recording_in_progress = False
            self.stop_recording()
            self._handle_error(
                f"Error starting recording: {str(e)}",
                AiolaErrorCode.MIC_ERROR,
                {"original_error": str(e)},
            )

    async def stop_recording(self) -> None:
        """Stop recording audio"""
        if self.is_stopping_recording:
            return

        try:
            self.is_stopping_recording = True
            if self.config.events.get("on_stop_record"):
                self.config.events["on_stop_record"]()

            if self._streaming_task:
                self._streaming_task.cancel()
                try:
                    await self._streaming_task
                except asyncio.CancelledError:
                    pass
                self._streaming_task = None

            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None

        except Exception as e:
            self._handle_error(
                f"Error stopping microphone recording: {str(e)}",
                AiolaErrorCode.MIC_ERROR,
                {"original_error": str(e)},
            )
        finally:
            self.recording_in_progress = False
            self.is_stopping_recording = False

    async def transcribe_file(
        self, file_path: str, output_transcript_file_path: str
    ) -> None:
        """
        Transcribe an audio file (wav, mp3, mp4). Extracts audio if mp4, checks sample rate, mono, and size, streams in 4096 byte chunks, buffers transcript, writes to file, and calls on_file_transcript.
        """
        logger.debug("<><><><>Starting transcription for file: %s", file_path)

        SUPPORTED_FORMATS = ("wav", "mp3", "mp4")
        MAX_SIZE_MB = 50
        CHUNK_SIZE = 4096
        transcript_buffer = []
        file_ext = os.path.splitext(file_path)[1][1:].lower()
        logger.debug(
            "Starting transcription for file: %s (type: %s)", file_path, file_ext
        )
        if file_ext not in SUPPORTED_FORMATS:
            logger.error("Unsupported file format: %s", file_ext)
            self._handle_error(
                f"Unsupported file format: {file_ext}",
                AiolaErrorCode.FILE_TRANSCRIPTION_ERROR,
                {"file_path": file_path},
            )
            return
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        logger.debug("Audio file size before conversion: %.2fMB", size_mb)

        # Convert to wav and downsample if needed
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        try:
            audio_path = self._convert_to_wav(
                file_path, temp_audio.name, REQUIRED_SAMPLE_RATE
            )
        except Exception as e:
            self._handle_error(
                f"Failed to convert audio to wav: {str(e)}",
                AiolaErrorCode.FILE_TRANSCRIPTION_ERROR,
                {"file_path": file_path, "original_error": str(e)},
            )
            os.unlink(temp_audio.name)
            return
        # Check file size
        size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        logger.debug("Audio file size after conversion: %.2fMB", size_mb)
        if size_mb > MAX_SIZE_MB:
            self._handle_error(
                f"File size {size_mb:.2f}MB exceeds {MAX_SIZE_MB}MB limit.",
                AiolaErrorCode.FILE_TRANSCRIPTION_ERROR,
                {"file_path": file_path, "size_mb": size_mb},
            )
            os.unlink(temp_audio.name)
            return
        # Open audio and read data
        try:
            with wave.open(audio_path, "rb") as wf:
                wf.rewind()
                audio_data = wf.readframes(wf.getnframes())
                # Apply silence padding to ensure proper chunking
                audio_data = self._silence_padding(
                    audio_data, wf.getframerate(), CHUNK_SIZE
                )

        except Exception as e:
            self._handle_error(
                f"Failed to read audio file: {str(e)}",
                AiolaErrorCode.FILE_TRANSCRIPTION_ERROR,
                {"file_path": file_path, "original_error": str(e)},
            )
            os.unlink(temp_audio.name)
            return
        # Prepare transcript buffer and override on_transcript
        last_transcript_time = pytime.time()
        transcript_event = asyncio.Event()

        async def wait_for_final_transcript():
            nonlocal last_transcript_time
            while True:
                await asyncio.sleep(1)
                if pytime.time() - last_transcript_time >= 5:
                    break
            # Write transcript to file here!
            logger.debug("Writing transcript to %s", output_transcript_file_path)
            try:
                os.makedirs(os.path.dirname(output_transcript_file_path), exist_ok=True)
                async with aiofiles.open(output_transcript_file_path, "w") as f:
                    full_transcript = " ".join(transcript_buffer)
                    await f.write(full_transcript + "\n")
            except Exception as e:
                logger.error("Failed to write transcript file: %s", e)
            logger.debug(
                "Calling on_file_transcript callback with %s",
                output_transcript_file_path,
            )
            if self.config.events.get("on_file_transcript"):
                self.config.events["on_file_transcript"](output_transcript_file_path)
            transcript_event.set()

        def buffer_transcript(data):
            nonlocal last_transcript_time
            last_transcript_time = pytime.time()
            # If data is a dict and has 'transcript', buffer only the transcript string
            if isinstance(data, dict) and "transcript" in data:
                transcript_buffer.append(str(data["transcript"]))
            else:
                transcript_buffer.append(str(data))
            logger.debug(
                "Buffering transcript - transcript_buffer: %s", transcript_buffer
            )

        self.config.events["on_transcript"] = buffer_transcript
        # Connect if not connected
        if not self.sio or not self.sio.connected:
            await self.connect(auto_record=False)
        # Stream audio in chunks
        logger.debug("Streaming audio in %d-byte chunks...", CHUNK_SIZE)
        try:
            for i in range(0, len(audio_data), CHUNK_SIZE):
                chunk = audio_data[i : i + CHUNK_SIZE]
                logger.debug(
                    "Streaming chunk %d / %d",
                    i // CHUNK_SIZE + 1,
                    len(audio_data) // CHUNK_SIZE + 1,
                )
                await self._stream_audio_data(chunk)
                # await asyncio.sleep(0.5)  # Sleep for 500 milliseconds
        except Exception as e:
            logger.error("Error streaming audio file: %s", e)
            self.config.events["on_transcript"] = buffer_transcript
            if temp_audio:
                os.unlink(temp_audio.name)
            return
        # Wait for transcript events
        logger.debug("Waiting for transcript events...")
        await asyncio.sleep(1)
        # Start background task to wait for final transcript
        asyncio.create_task(wait_for_final_transcript())
        await transcript_event.wait()
        # Clean up
        await self.disconnect()
        if temp_audio:
            logger.debug("Cleaning up temporary file: %s", temp_audio.name)
            os.unlink(temp_audio.name)

    def get_active_keywords(self) -> List[str]:
        """Get the currently active keywords"""
        return self.active_keywords.copy()

    async def set_keywords(self, keywords: List[str]) -> None:
        """
        Set keywords for speech recognition.

        Args:
        ```bash
            keywords (List[str]): List of keywords to spot in the audio stream
        ```
        Example:
            ```bash
            # Set keywords to spot in the audio stream
            await client.set_keywords(["hello", "world", "aiola"])

            # Clear keywords by passing an empty list
            await client.set_keywords([])
            ```
        """
        if not isinstance(keywords, list):
            raise AiolaError(
                "Keywords must be a valid list", AiolaErrorCode.KEYWORDS_ERROR
            )

        # Allow empty list to clear keywords
        if not keywords:
            self.active_keywords = []
            if self.sio and self.sio.connected:
                await self.sio.emit("set_keywords", "", namespace=self.namespace)
            return

        valid_keywords = [k.strip() for k in keywords if k.strip()]

        if not valid_keywords:
            raise AiolaError(
                "At least one valid keyword must be provided",
                AiolaErrorCode.KEYWORDS_ERROR,
            )

        self.active_keywords = valid_keywords

        if not self.sio or not self.sio.connected:
            return

        try:
            binary_data = json.dumps(valid_keywords).encode()
            await self.sio.emit("set_keywords", binary_data, namespace=self.namespace)
            if self.config.events.get("on_keyword_set"):
                self.config.events["on_keyword_set"](valid_keywords)

        except Exception as e:
            logger.error("Error setting keywords: %s", e)
            self._handle_error(
                f"Error setting keywords: {str(e)}",
                AiolaErrorCode.KEYWORDS_ERROR,
                {"original_error": str(e)},
            )
            raise

    async def _stream_audio_data(self, audio_data: bytes) -> None:
        """
        Stream custom audio data to the server.
        ```bash
        Args:
            audio_data (bytes): Raw audio data to stream. Should match the configured audio format
                              (sample_rate, channels, dtype as specified in mic_config)
        ```
        """
        if not self.sio or not self.sio.connected:
            logger.error("Cannot stream audio: Socket is not connected")
            self._handle_error(
                "Socket is not connected. Please call connect first.",
                AiolaErrorCode.STREAMING_ERROR,
            )
            return

        # Validate chunk size
        if len(audio_data) > AUDIO_CHUNK_SIZE:
            error_msg = (
                "Audio chunk size (%d bytes) exceeds maximum allowed size of %d bytes"
                % (len(audio_data) / 2, AUDIO_CHUNK_SIZE / 2)
            )
            logger.error(error_msg)
            self._handle_error(
                error_msg,
                AiolaErrorCode.STREAMING_ERROR,
                {"chunk_size": len(audio_data), "max_size": AUDIO_CHUNK_SIZE},
            )
            return

        try:
            await self.sio.emit("binary_data", audio_data, namespace=self.namespace)
        except Exception as e:
            logger.error("Error streaming audio data: %s", e)
            self._handle_error(
                f"Error streaming audio data: {str(e)}",
                AiolaErrorCode.STREAMING_ERROR,
                {"original_error": str(e)},
            )

    async def _start_stream(
        self, stream_generator: AsyncGenerator[bytes, None]
    ) -> None:
        """Start streaming audio from a stream generator
        ```bash
        Args:
            stream_generator: An async generator that yields audio data chunks in bytes format
        ```
        """
        chunk_count = 0

        try:
            async for audio_bytes in stream_generator:
                if not self.sio or not self.sio.connected:
                    break
                chunk_count += 1
                await self._stream_audio_data(audio_bytes)

        except Exception as e:
            self._handle_error(
                f"Error in audio streaming: {str(e)}",
                AiolaErrorCode.STREAMING_ERROR,
                {"original_error": str(e)},
            )
        finally:
            logger.debug("Audio streaming stopped. Total chunks sent: %d", chunk_count)
            self.recording_in_progress = False
            if self.config.events.get("on_stop_record"):
                self.config.events["on_stop_record"]()
            await self.stop_recording()

    async def _create_mic_stream_generator(self) -> AsyncGenerator[bytes, None]:
        """Create an async generator that yields audio data from the microphone"""
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def audio_callback(data, frames, time, status):
            """Handle audio data from the microphone"""
            if status:
                if self.config.events.get("on_error"):
                    self.config.events["on_error"](
                        AiolaError("Audio status: %s", status)
                    )

            if data is not None:
                loop.call_soon_threadsafe(queue.put_nowait, bytes(data))
            else:
                logger.warning("No audio data received in callback")

        # Create and start the audio stream
        self.audio_stream = sd.RawInputStream(
            samplerate=self.config.mic_config.sample_rate,
            channels=self.config.mic_config.channels,
            blocksize=self.config.mic_config.chunk_size,
            dtype=np.int16,
            callback=audio_callback,
        )
        self.audio_stream.start()

        try:
            while True:
                audio_bytes = await queue.get()
                yield audio_bytes
        finally:
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None

    # Internal methods below this line
    def _setup_event_handlers(self) -> None:
        """Set up Socket.IO event handlers"""
        if not self.sio:
            return

        @self.sio.event(namespace="/events")
        async def connect():
            """Handle connection event."""
            if self.config.events.get("on_connect"):
                transport = self.sio.transport
                self.config.events["on_connect"](transport or "unknown")

        @self.sio.event(namespace="/events")
        async def error(error):
            """Handle error events."""
            self._handle_error(
                f"Socket error: {str(error)}",
                AiolaErrorCode.GENERAL_ERROR,
                {"original_error": str(error)},
            )

        @self.sio.event(namespace="/events")
        async def connect_error(error):
            """Handle connection error events."""
            self._handle_error(
                f"Socket connection error: {str(error)}",
                AiolaErrorCode.NETWORK_ERROR,
                {"original_error": str(error)},
            )

        @self.sio.event(namespace="/events")
        async def disconnect():
            """Handle disconnection event."""
            if self.config.events.get("on_disconnect"):
                self.config.events["on_disconnect"]()

        @self.sio.event(namespace="/events")
        async def transcript(data, ack=None):
            """Handle transcript events."""
            if self.config.events.get("on_transcript"):
                self.config.events["on_transcript"](data)
            if ack:
                await ack({"status": "received"})

        @self.sio.event(namespace="/events")
        async def events(data, ack=None):
            """Handle general events."""
            if self.config.events.get("on_events"):
                self.config.events["on_events"](data)
            if ack:
                await ack({"status": "received"})

    def _handle_error(
        self,
        message: str,
        code: AiolaErrorCode = AiolaErrorCode.GENERAL_ERROR,
        details: Optional[Dict] = None,
    ) -> None:
        """Handle error by logging it and emitting the error event"""
        error = AiolaError(message, code, details)
        print(f"Error: {error}")
        if self.config.events.get("on_error"):
            self.config.events["on_error"](error)

    async def _cleanup_socket(self) -> None:
        """Clean up socket connection and resources"""
        if self.recording_in_progress:
            await self.stop_recording()

        if self.sio:
            try:
                if self.sio.connected:
                    await self.sio.disconnect()
            except Exception:
                pass  # Ignore disconnect errors during cleanup
            finally:
                self.sio = None

        if self.config.events.get("on_disconnect"):
            self.config.events["on_disconnect"]()

    def _convert_to_wav(self, input_path, output_path, target_sr=16000):
        """
        Convert an audio file (mp3/mp4/wav) to mono WAV at target_sr. Returns output_path.
        input_path: str - The path to the input audio file
        output_path: str - The path to the output WAV file
        target_sr: int - The sample rate to convert the audio to
        Raises an AiolaError if the sample rate is below the required rate.
        """
        logger.debug("Converting audio file to WAV: %s", input_path)
        file_ext = os.path.splitext(input_path)[1][1:].lower()
        if file_ext == "wav":
            # Check if conversion is needed
            with wave.open(input_path, "rb") as wf:
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                logger.debug(
                    "Audio properties: sample_rate=%d, channels=%d",
                    sample_rate,
                    channels,
                )
                if sample_rate < REQUIRED_SAMPLE_RATE:
                    raise AiolaError(
                        f"Sample rate {sample_rate}Hz is below required {REQUIRED_SAMPLE_RATE}Hz",
                        AiolaErrorCode.FILE_TRANSCRIPTION_ERROR,
                        {
                            "sample_rate": sample_rate,
                            "required_rate": REQUIRED_SAMPLE_RATE,
                        },
                    )
                if sample_rate == target_sr and channels == 1:
                    return input_path  # Already correct format
            # Otherwise, load and convert
            audio_np, sr = sf.read(input_path, dtype="int16", always_2d=True)
            if audio_np.shape[1] > 1:
                audio_np = np.mean(audio_np, axis=1)
            if sr != target_sr:
                audio_np = AiolaSttClient._downsample_audio(audio_np, sr, target_sr)
            sf.write(output_path, audio_np, target_sr, format="WAV", subtype="PCM_16")
            return output_path
        # For mp3/mp4
        container = av.open(input_path)
        audio_stream = next(s for s in container.streams if s.type == "audio")
        logger.debug(
            "Audio stream for non-WAV file properties: sample_rate=%d, channels=%d",
            audio_stream.sample_rate,
            audio_stream.channels,
        )
        if audio_stream.sample_rate < REQUIRED_SAMPLE_RATE:
            raise AiolaError(
                f"Sample rate {audio_stream.sample_rate}Hz is below required {REQUIRED_SAMPLE_RATE}Hz",
                AiolaErrorCode.FILE_TRANSCRIPTION_ERROR,
                {
                    "sample_rate": audio_stream.sample_rate,
                    "required_rate": REQUIRED_SAMPLE_RATE,
                },
            )
        resampler = AudioResampler(format="s16", layout="mono", rate=target_sr)
        out = av.open(output_path, mode="w", format="wav")
        out_stream = out.add_stream("pcm_s16le", rate=target_sr, layout="mono")
        for packet in container.demux(audio_stream):
            for frame in packet.decode():
                frame.pts = None
                if (
                    frame.format.name != "s16"
                    or frame.sample_rate != target_sr
                    or frame.layout.name != "mono"
                ):
                    resampled_frames = resampler.resample(frame)
                    if isinstance(resampled_frames, list):
                        for resampled_frame in resampled_frames:
                            if resampled_frame:
                                for packet in out_stream.encode(resampled_frame):
                                    out.mux(packet)
                    elif resampled_frames is not None:
                        for packet in out_stream.encode(resampled_frames):
                            out.mux(packet)
                else:
                    for packet in out_stream.encode(frame):
                        out.mux(packet)
        for packet in out_stream.encode(None):
            out.mux(packet)
        out.close()
        container.close()
        return output_path

    @staticmethod
    def _downsample_audio(audio_np, orig_sr, target_sr):
        """
        Downsample a numpy audio array from orig_sr to target_sr using polyphase filtering.
        """
        if orig_sr == target_sr:
            return audio_np
        return resample_poly(audio_np, target_sr, orig_sr).astype(np.int16)

    def _silence_padding(
        self, audio_data: bytes, sample_rate: int, chunk_size: int
    ) -> bytes:
        """
        Apply silence padding to audio data to ensure proper chunking.

        This method:
        1. Adds 500ms of silence to the end of the audio
        2. Ensures the total audio length is divisible by chunk_size by adding additional silence padding

        Args:
            audio_data (bytes): Raw audio data
            sample_rate (int): Sample rate of the audio in Hz
            chunk_size (int): Target chunk size in bytes (typically 4096)

        Returns:
            bytes: Audio data with silence padding applied
        """
        logger.debug(
            "Applying silence padding - original length: %d bytes", len(audio_data)
        )

        # Step 1: Add SILENCE_DURATION_MS of silence to the end of the audio
        silence_samples = int(SILENCE_DURATION_MS * sample_rate / 1000)
        # Each sample is 2 bytes (16-bit audio), so multiply by 2 for byte count
        silence_byte = b"\x00"
        silence_bytes = silence_samples * 2
        silence_data = silence_byte * silence_bytes
        audio_data += silence_data

        logger.debug("After 500ms silence padding: %d bytes", len(audio_data))

        # Step 2: Ensure the audio data length is divisible by chunk_size
        remainder = len(audio_data) % chunk_size
        if remainder != 0:
            # Calculate how many more bytes needed to make it divisible by chunk_size
            additional_padding_length = chunk_size - remainder
            additional_padding = silence_byte * additional_padding_length
            audio_data += additional_padding
            logger.debug(
                "Added %d bytes of additional padding for chunk alignment",
                additional_padding_length,
            )

        logger.debug(
            "Final audio length after padding: %d bytes (chunks: %d)",
            len(audio_data),
            len(audio_data) // chunk_size,
        )

        return audio_data
