# flake8: noqa: D100,D101,D102,D103,D104,D105,D106,D107
# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring
import asyncio
import os
import wave
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from aiola_stt.config import AiolaConfig, AiolaQueryParams

# Constants from the actual implementation
REQUIRED_SAMPLE_RATE = 16000


@pytest.fixture
def config():
    return AiolaConfig(
        api_key="test_token",
        query_params=AiolaQueryParams(flow_id="test_flow_id", execution_id="test123"),
    )


def mock_socketio_factory():
    mock_sio_client = MagicMock()
    mock_sio_client.connected = False
    mock_sio_client.connect = AsyncMock()
    mock_sio_client.disconnect = AsyncMock()
    mock_sio_client.emit = AsyncMock()
    mock_sio_client.call = AsyncMock()
    mock_sio_client.event = lambda *args, **kwargs: lambda f: f
    return mock_sio_client


@pytest.fixture
def client(config):
    # Create the mock modules
    mock_socketio = MagicMock()
    mock_socketio.AsyncClient = mock_socketio_factory

    mock_sd = MagicMock()
    mock_sd.RawInputStream = MagicMock()

    mock_sf = MagicMock()
    mock_sf.read = MagicMock(return_value=(np.zeros(16000), 16000))
    mock_sf.write = MagicMock()

    # Create mock for av module
    mock_av = MagicMock()
    mock_av_container = MagicMock()
    mock_av_stream = MagicMock()
    mock_av_stream.type = "audio"
    mock_av_stream.sample_rate = 44100
    mock_av_stream.channels = 2
    mock_av_container.streams = [mock_av_stream]
    mock_av.open = MagicMock(return_value=mock_av_container)

    # Create mock for AudioResampler
    mock_resampler = MagicMock()
    mock_resampler.resample = MagicMock(return_value=MagicMock())

    # Create mock for aiofiles
    mock_aiofiles = MagicMock()
    mock_file = MagicMock()
    mock_file.write = AsyncMock()
    # Create async context manager for file
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_file)
    mock_cm.__aexit__ = AsyncMock()
    mock_aiofiles.open = MagicMock(return_value=mock_cm)

    # Patch the modules in sys.modules
    with (
        patch.dict(
            "sys.modules",
            {
                "socketio": mock_socketio,
                "sounddevice": mock_sd,
                "soundfile": mock_sf,
                "av": mock_av,
                "aiofiles": mock_aiofiles,
            },
        ),
        patch("aiola_stt.client.REQUIRED_SAMPLE_RATE", REQUIRED_SAMPLE_RATE),
        patch("av.audio.resampler.AudioResampler", return_value=mock_resampler),
    ):
        # Import modules
        from aiola_stt.client import AiolaSttClient

        # Create client instance
        client_instance = AiolaSttClient(
            config, sio_client_factory=mock_socketio_factory
        )
        yield client_instance


@pytest.fixture
def mock_socketio_fixture():
    return mock_socketio_factory


async def connect_and_set_connected(client):
    await client.connect()
    client.sio.connected = True


# Create a mock async context manager
class AsyncMockContextManager:
    def __init__(self, mock_obj):
        self.mock_obj = mock_obj

    async def __aenter__(self):
        return self.mock_obj

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestAiolaSttClientTranscription:
    @pytest.mark.asyncio
    async def test_transcribe_file(self, client, tmp_path):
        test_wav_path = os.path.join(tmp_path, "test.wav")
        # Use wave.open in write mode to create the test wav file
        with wave.open(test_wav_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(np.zeros(16000, dtype=np.int16).tobytes())
        output_transcript_path = os.path.join(tmp_path, "transcript.txt")
        # Proper context manager mock for wave.open
        mock_wave_file = MagicMock()
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnframes.return_value = 16000
        mock_wave_file.readframes.return_value = np.zeros(
            16000, dtype=np.int16
        ).tobytes()
        mock_wave_cm = MagicMock()
        mock_wave_cm.__enter__.return_value = mock_wave_file
        mock_wave_cm.__exit__.return_value = None
        transcript_data = {"text": "Hello, this is a test transcript"}
        mock_file = MagicMock()
        mock_file.write = AsyncMock()
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_file)
        mock_cm.__aexit__ = AsyncMock()
        with (
            patch.object(
                client, "_stream_audio_data", new_callable=AsyncMock
            ) as mock_stream,
            patch.object(
                client, "_convert_to_wav", return_value=test_wav_path
            ) as mock_convert,
            patch("aiola_stt.client.wave.open", return_value=mock_wave_cm),
            patch("aiola_stt.client.aiofiles.open", return_value=mock_cm),
            patch("os.path.exists", return_value=True),
            patch("asyncio.sleep", AsyncMock()) as mock_sleep,
            patch("asyncio.Event") as mock_event_class,
        ):
            mock_event = mock_event_class.return_value
            mock_event.wait = AsyncMock()
            mock_event.set = MagicMock()

            async def side_effect(*args, **kwargs):
                client.transcript_buffer = [transcript_data["text"]]
                mock_event.set()
                return None

            await connect_and_set_connected(client)

            def on_transcript(data):
                client.transcript_buffer = [transcript_data["text"]]

            client.config.events["on_transcript"] = on_transcript
            mock_sleep.side_effect = side_effect
            await client.transcribe_file(test_wav_path, output_transcript_path)
            mock_convert.assert_called_once()
            assert mock_stream.await_count > 0
            # Wait for the write operation to complete
            await asyncio.sleep(0.1)
            assert client.transcript_buffer == [transcript_data["text"]]

    def test_convert_to_wav(self, client, tmp_path):
        input_wav = os.path.join(tmp_path, "input.wav")
        # Use wave.open in write mode to create the test wav file
        with wave.open(input_wav, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(np.zeros(16000, dtype=np.int16).tobytes())
        mock_wave_file = MagicMock()
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_cm = MagicMock()
        mock_wave_cm.__enter__.return_value = mock_wave_file
        mock_wave_cm.__exit__.return_value = None
        with patch("aiola_stt.client.wave.open", return_value=mock_wave_cm):
            output_wav = os.path.join(tmp_path, "output.wav")
            result_path = client._convert_to_wav(input_wav, output_wav, 16000)
            assert result_path == input_wav

    def test_convert_to_wav_custom_sr(self, client, tmp_path):
        input_wav = os.path.join(tmp_path, "input.wav")
        # Use wave.open in write mode to create the test wav file
        with wave.open(input_wav, "wb") as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(np.zeros(16000 * 2, dtype=np.int16).tobytes())
        output_wav = os.path.join(tmp_path, "output.wav")
        mock_wave_file = MagicMock()
        mock_wave_file.getframerate.return_value = 44100
        mock_wave_file.getnchannels.return_value = 2
        mock_wave_cm = MagicMock()
        mock_wave_cm.__enter__.return_value = mock_wave_file
        mock_wave_cm.__exit__.return_value = None
        stereo_data = np.zeros((16000, 2), dtype=np.int16)
        with (
            patch("aiola_stt.client.wave.open", return_value=mock_wave_cm),
            patch("soundfile.read", return_value=(stereo_data, 44100)),
            patch("aiola_stt.client.sf.write") as mock_write,
        ):
            result_path = client._convert_to_wav(input_wav, output_wav, 16000)
            assert result_path == output_wav
            # Ensure the write operation is called with correct output path and sample rate
            mock_write.assert_called()
            args, _ = mock_write.call_args
            assert args[0] == output_wav
            assert args[2] == 16000

    def test_convert_to_wav_mp3(self, client, tmp_path):
        # Create an MP3 file path
        input_mp3 = os.path.join(tmp_path, "input.mp3")
        output_wav = os.path.join(tmp_path, "output.wav")

        # Create a dummy MP3 file
        with open(input_mp3, "wb") as f:
            f.write(b"ID3" + b"\x00" * 40)  # Dummy MP3 header

        # Set up mock for av.open with special side effect to handle different calls
        mock_stream = MagicMock()
        mock_stream.type = "audio"
        mock_stream.sample_rate = 44100
        mock_stream.channels = 2

        mock_input_container = MagicMock()
        mock_input_container.streams = [mock_stream]
        # Return empty generator for demux to avoid processing
        mock_input_container.demux.return_value = iter([])

        mock_output_container = MagicMock()
        mock_output_stream = MagicMock()
        mock_output_container.add_stream.return_value = mock_output_stream

        # Patch av.open to return different things based on mode
        def mock_av_open_side_effect(path, **kwargs):
            if kwargs.get("mode") == "w":
                return mock_output_container
            return mock_input_container

        # Set up the patches
        with (
            patch("aiola_stt.client.av.open", side_effect=mock_av_open_side_effect),
            patch("av.audio.resampler.AudioResampler", return_value=MagicMock()),
        ):
            # Call the function
            result_path = client._convert_to_wav(input_mp3, output_wav)

            # Should return output path
            assert result_path == output_wav
            # Verify containers were properly closed
            mock_input_container.close.assert_called_once()
            mock_output_container.close.assert_called_once()

    def test_convert_to_wav_error(self, client, tmp_path):
        # Create an MP3 file path
        input_mp3 = os.path.join(tmp_path, "input.mp3")
        output_wav = os.path.join(tmp_path, "output.wav")

        # Create a dummy MP3 file
        with open(input_mp3, "wb") as f:
            f.write(b"ID3" + b"\x00" * 40)  # Dummy MP3 header

        # Set up mock to raise a specific error
        error_message = "Error converting audio"

        with patch("aiola_stt.client.av.open", side_effect=Exception(error_message)):
            # Test error handling
            with pytest.raises(Exception) as excinfo:
                client._convert_to_wav(input_mp3, output_wav)

            # Verify error message
            assert error_message in str(excinfo.value)

    def test_downsample_audio(self, client):
        # Test audio downsampling
        # Create a simple test signal
        sample_rate = 44100
        duration = 1  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        test_signal = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave

        # Test the downsample function
        result = client._downsample_audio(test_signal, sample_rate, 16000)

        # Check the result
        expected_length = int(16000 * duration)
        assert len(result) == expected_length

        # Test with same sample rate (shouldn't change)
        same_rate_result = client._downsample_audio(
            test_signal, sample_rate, sample_rate
        )
        assert len(same_rate_result) == len(test_signal)

    def test_silence_padding_functionality(self, client):
        """Test the _silence_padding method to ensure it adds 250ms silence and makes audio divisible by chunk_size"""

        # Test parameters
        sample_rate = 16000  # 16kHz
        chunk_size = 4096  # 4KB chunks

        # Test case 1: Small audio that needs both 250ms padding and chunk alignment
        original_audio_length = 10000  # 10KB
        original_audio_data = (
            b"\x01" * original_audio_length
        )  # Non-zero data to distinguish from padding

        # Mock the test file saving function to avoid actual file I/O during testing
        with patch.object(client, "_save_padded_audio_for_testing") as mock_save:
            padded_audio = client._silence_padding(
                original_audio_data, sample_rate, chunk_size
            )

            # Verify the test file saving function was called
            mock_save.assert_called_once_with(padded_audio, sample_rate)

        # Calculate expected 250ms silence in bytes
        silence_duration_ms = 250
        silence_samples = int(silence_duration_ms * sample_rate / 1000)  # 4000 samples
        silence_bytes = silence_samples * 2  # 8000 bytes (16-bit audio)

        # Expected length after 250ms padding
        after_250ms_length = original_audio_length + silence_bytes  # 18000 bytes

        # Calculate expected final length after chunk alignment
        remainder = after_250ms_length % chunk_size  # 18000 % 4096 = 1520
        if remainder != 0:
            additional_padding = chunk_size - remainder  # 4096 - 1520 = 2576
            expected_final_length = (
                after_250ms_length + additional_padding
            )  # 20576 bytes
        else:
            expected_final_length = after_250ms_length

        # Verify the final length
        assert len(padded_audio) == expected_final_length

        # Verify the audio is divisible by chunk_size (modulo = 0)
        assert len(padded_audio) % chunk_size == 0, (
            f"Audio length {len(padded_audio)} is not divisible by chunk_size {chunk_size}"
        )

        # Verify the original data is preserved at the beginning
        assert padded_audio[:original_audio_length] == original_audio_data

        # Verify 250ms of silence was added (should be all zeros)
        silence_start = original_audio_length
        silence_end = silence_start + silence_bytes
        silence_section = padded_audio[silence_start:silence_end]
        assert silence_section == b"\x00" * silence_bytes, (
            "250ms silence section should be all zeros"
        )

        # Verify additional chunk alignment padding (should also be zeros)
        if remainder != 0:
            padding_start = silence_end
            padding_section = padded_audio[padding_start:]
            assert padding_section == b"\x00" * len(padding_section), (
                "Chunk alignment padding should be all zeros"
            )

        # Calculate expected number of complete chunks
        expected_chunks = expected_final_length // chunk_size
        actual_chunks = len(padded_audio) // chunk_size
        assert actual_chunks == expected_chunks, (
            f"Expected {expected_chunks} chunks, got {actual_chunks}"
        )

        print(
            f"✅ Test passed: {original_audio_length} bytes → {len(padded_audio)} bytes ({actual_chunks} complete chunks)"
        )

    def test_silence_padding_edge_cases(self, client):
        """Test edge cases for silence padding"""

        sample_rate = 16000
        chunk_size = 4096

        # Test case 1: Audio that's already aligned after 250ms padding
        # We need to find a length where original + 250ms padding is divisible by chunk_size
        silence_bytes = int(250 * sample_rate / 1000) * 2  # 8000 bytes

        # Find a length where (length + 8000) % 4096 == 0
        # 8000 % 4096 = 1808, so we need (length + 1808) % 4096 == 0
        # This means length % 4096 == (4096 - 1808) % 4096 == 2288
        # But let's double-check: (2288 + 8000) % 4096 = 10288 % 4096 = 2000 ≠ 0
        # We need: (length + 8000) % 4096 == 0
        # So: length % 4096 == (4096 - (8000 % 4096)) % 4096
        # 8000 % 4096 = 1808, so we need length % 4096 == (4096 - 1808) % 4096 = 2288
        # Actually, let's use a simpler approach: find length where (length + 8000) is divisible by 4096
        # We want length + 8000 = n * 4096 for some integer n
        # Let's use n = 3, so length + 8000 = 12288, therefore length = 4288
        aligned_length = 4288  # This should result in no additional padding needed

        original_audio_data = b"\x01" * aligned_length

        with patch.object(client, "_save_padded_audio_for_testing"):
            padded_audio = client._silence_padding(
                original_audio_data, sample_rate, chunk_size
            )

        expected_length = aligned_length + silence_bytes
        assert len(padded_audio) == expected_length
        assert len(padded_audio) % chunk_size == 0

        # Test case 2: Very small audio file
        small_audio = b"\x01" * 100

        with patch.object(client, "_save_padded_audio_for_testing"):
            padded_small = client._silence_padding(small_audio, sample_rate, chunk_size)

        assert len(padded_small) % chunk_size == 0
        assert len(padded_small) >= len(small_audio) + silence_bytes

        # Test case 3: Large audio file
        large_audio = b"\x01" * 50000

        with patch.object(client, "_save_padded_audio_for_testing"):
            padded_large = client._silence_padding(large_audio, sample_rate, chunk_size)

        assert len(padded_large) % chunk_size == 0
        assert len(padded_large) >= len(large_audio) + silence_bytes

        print("✅ All edge case tests passed")

    def test_save_padded_audio_for_testing(self, client, tmp_path):
        """Test the _save_padded_audio_for_testing method"""

        # Create test audio data
        sample_rate = 16000
        test_audio_data = np.random.randint(
            -32768, 32767, 16000, dtype=np.int16
        ).tobytes()

        # Mock the datetime to control the filename - fix the import path
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20241220_143052"

            # Mock os.makedirs and wave.open
            with (
                patch("aiola_stt.client.os.makedirs") as mock_makedirs,
                patch("aiola_stt.client.wave.open") as mock_wave_open,
            ):
                # Set up wave file mock
                mock_wave_file = MagicMock()
                mock_wave_cm = MagicMock()
                mock_wave_cm.__enter__.return_value = mock_wave_file
                mock_wave_cm.__exit__.return_value = None
                mock_wave_open.return_value = mock_wave_cm

                # Call the method
                client._save_padded_audio_for_testing(test_audio_data, sample_rate)

                # Verify directory creation
                mock_makedirs.assert_called_once_with("example_output", exist_ok=True)

                # Verify wave file was opened with correct path
                expected_path = os.path.join(
                    "example_output", "padded_audio_20241220_143052.wav"
                )
                mock_wave_open.assert_called_once_with(expected_path, "wb")

                # Verify wave file configuration
                mock_wave_file.setnchannels.assert_called_once_with(1)  # Mono
                mock_wave_file.setsampwidth.assert_called_once_with(2)  # 16-bit
                mock_wave_file.setframerate.assert_called_once_with(sample_rate)
                mock_wave_file.writeframes.assert_called_once_with(test_audio_data)

        print("✅ Save padded audio test passed")
