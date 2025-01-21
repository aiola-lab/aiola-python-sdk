
import sounddevice as sd
from .exceptions import AiolaStreamingError

from aiola_streaming_sdk.client import AiolaStreamingClient
from aiola_streaming_sdk.models.audio import AudioConfig


class RecorderApp:
    def __init__(self, sdk: AiolaStreamingClient, on_stream_error: callable):
        """
        Initializes the RecorderApp with the SDK client and error callback.

        :param sdk: Instance of AiolaStreamingClient
        :param on_stream_error: Callback function to handle stream errors
        """
        self._sdk = sdk
        self._on_stream_error = on_stream_error
        self.recording = None
        self.default_audio_config = AudioConfig()

    def start_streaming(self) -> None:
        """
        Starts the audio streaming process.
        """
        try:
            self._start_audio_streaming()
        except Exception as error:
            raise AiolaStreamingError(str(error))
        
    def close_audio_streaming(self) -> None:
        """
        Stops the audio streaming and cleans up the recording instance.
        """
        print("closeAudioStreaming")
        if self.recording:
            try:
                self.recording.stop()
                print("Recording stopped")
            except Exception as error:
                print(f"Error stopping the recording: {error}")
            finally:
                self.recording = None
        else:
            print("No active recording to stop")

    def _start_audio_streaming(self) -> None:
        """Start streaming audio from the microphone."""
        
        def audio_callback(data, frames, time, status):
            """Handle audio data from the microphone."""
            if not self._sdk.sio.connected:
                return
            
            if status and self._on_stream_error:
                self._on_stream_error({"audio_status": status})
            
            if data is not None:
                self._sdk.sio.emit("binary_data", bytes(data), namespace=self._sdk.config.namespace)

        with sd.RawInputStream(
            samplerate=self.default_audio_config.sample_rate,
            channels=self.default_audio_config.channels,
            blocksize=self.default_audio_config.chunk_size,
            dtype=self.default_audio_config.dtype,
            callback=audio_callback,
        ):self._sdk.sio.wait()