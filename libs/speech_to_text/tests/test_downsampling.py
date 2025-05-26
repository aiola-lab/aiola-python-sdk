# flake8: noqa: D100,D101,D102,D103,D104,D105,D106,D107
# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from aiola_stt.config import AiolaConfig, AiolaQueryParams

@pytest.fixture
def client():
    """Create a client instance for testing."""
    # Create mock for AudioResampler
    mock_resampler = MagicMock()
    mock_resampler.resample = MagicMock(return_value=MagicMock())
    
    with patch('av.audio.resampler.AudioResampler', return_value=mock_resampler):
        from aiola_stt.client import AiolaSttClient
        
        config = AiolaConfig(
            api_key="test_token",
            query_params=AiolaQueryParams(
                flow_id="test_flow_id",
                execution_id="test123"
            )
        )
        
        return AiolaSttClient(config)

class TestAudioDownsampling:
    def test_downsample_audio(self, client):
        """Test that audio downsampling works correctly."""
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