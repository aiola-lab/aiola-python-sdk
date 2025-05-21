# flake8: noqa: D100,D101,D102,D103,D104,D105,D106,D107
# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring
import asyncio
import os
import numpy as np
import pytest
import sys
import tempfile
import wave
from unittest.mock import AsyncMock, MagicMock, patch, mock_open, call, PropertyMock
from aiola_stt.config import AiolaConfig, AiolaQueryParams

# Constants from the actual implementation
REQUIRED_SAMPLE_RATE = 16000

@pytest.fixture
def config():
    return AiolaConfig(
        api_key="test_token",
        query_params=AiolaQueryParams(
            flow_id="test_flow_id",
            execution_id="test123"
        )
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
    with patch.dict('sys.modules', {
        'socketio': mock_socketio, 
        'sounddevice': mock_sd,
        'soundfile': mock_sf,
        'av': mock_av,
        'aiofiles': mock_aiofiles,
    }), patch('aiola_stt.client.REQUIRED_SAMPLE_RATE', REQUIRED_SAMPLE_RATE), \
       patch('av.audio.resampler.AudioResampler', return_value=mock_resampler):
        # Import modules
        from aiola_stt.config import AiolaConfig, AiolaQueryParams
        from aiola_stt.client import AiolaSttClient
        
        # Create client instance
        client_instance = AiolaSttClient(config, sio_client_factory=mock_socketio_factory)
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
        with wave.open(test_wav_path, 'wb') as wav_file:
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
        mock_wave_file.readframes.return_value = np.zeros(16000, dtype=np.int16).tobytes()
        mock_wave_cm = MagicMock()
        mock_wave_cm.__enter__.return_value = mock_wave_file
        mock_wave_cm.__exit__.return_value = None
        transcript_data = {"text": "Hello, this is a test transcript"}
        mock_file = MagicMock()
        mock_file.write = AsyncMock()
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_file)
        mock_cm.__aexit__ = AsyncMock()
        with patch.object(client, '_stream_audio_data', new_callable=AsyncMock) as mock_stream, \
             patch.object(client, '_convert_to_wav', return_value=test_wav_path) as mock_convert, \
             patch('aiola_stt.client.wave.open', return_value=mock_wave_cm), \
             patch('aiola_stt.client.aiofiles.open', return_value=mock_cm), \
             patch('os.path.exists', return_value=True), \
             patch('asyncio.create_task') as mock_create_task, \
             patch('asyncio.sleep', AsyncMock()) as mock_sleep, \
             patch('asyncio.Event') as mock_event_class:
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
        with wave.open(input_wav, 'wb') as wav_file:
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
        with patch('aiola_stt.client.wave.open', return_value=mock_wave_cm):
            output_wav = os.path.join(tmp_path, "output.wav")
            result_path = client._convert_to_wav(input_wav, output_wav, 16000)
            assert result_path == input_wav
    
    def test_convert_to_wav_custom_sr(self, client, tmp_path):
        input_wav = os.path.join(tmp_path, "input.wav")
        # Use wave.open in write mode to create the test wav file
        with wave.open(input_wav, 'wb') as wav_file:
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
        with patch('aiola_stt.client.wave.open', return_value=mock_wave_cm), \
             patch('soundfile.read', return_value=(stereo_data, 44100)), \
             patch('aiola_stt.client.sf.write') as mock_write:
            result_path = client._convert_to_wav(input_wav, output_wav, 16000)
            assert result_path == output_wav
            # Ensure the write operation is called with correct output path and sample rate
            mock_write.assert_called()
            args, kwargs = mock_write.call_args
            assert args[0] == output_wav
            assert args[2] == 16000
    
    def test_convert_to_wav_mp3(self, client, tmp_path):
        # Create an MP3 file path
        input_mp3 = os.path.join(tmp_path, "input.mp3")
        output_wav = os.path.join(tmp_path, "output.wav")
        
        # Create a dummy MP3 file
        with open(input_mp3, 'wb') as f:
            f.write(b'ID3' + b'\x00' * 40)  # Dummy MP3 header
        
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
            if kwargs.get('mode') == 'w':
                return mock_output_container
            return mock_input_container
        
        # Set up the patches
        with patch('aiola_stt.client.av.open', side_effect=mock_av_open_side_effect), \
             patch('av.audio.resampler.AudioResampler', return_value=MagicMock()):
            
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
        with open(input_mp3, 'wb') as f:
            f.write(b'ID3' + b'\x00' * 40)  # Dummy MP3 header
        
        # Set up mock to raise a specific error
        error_message = "Error converting audio"
        
        with patch('aiola_stt.client.av.open', side_effect=Exception(error_message)):
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
        same_rate_result = client._downsample_audio(test_signal, sample_rate, sample_rate)
        assert len(same_rate_result) == len(test_signal) 