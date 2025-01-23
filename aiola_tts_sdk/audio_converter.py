from typing import Literal
import wave
import struct
import math
from io import BytesIO

# Define valid audio formats
AudioFormat = Literal["LINEAR16", "MULAW", "PCM"]

class AudioConverter:
    """Audio format converter for the TTS client."""

    def __init__(self, target_format: AudioFormat):
        """
        Initialize the audio converter.
        
        :param target_format: The target audio format to convert to
        """
        self.target_format = target_format

    def convert(self, audio_bytes: bytes) -> bytes:
        """
        Convert audio data to the target format.
        
        :param audio_bytes: Input audio data in WAV format
        :return: Converted audio data in the specified format
        """
        # Read WAV file from bytes
        with wave.open(BytesIO(audio_bytes), 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)

        # Convert based on format
        if self.target_format == "LINEAR16":
            return self._to_linear16(frames, params)
        elif self.target_format == "PCM":
            return self._to_pcm(frames, params)
        elif self.target_format == "MULAW":
            return self._to_mulaw(frames, params)

        return audio_bytes

    def _to_linear16(self, frames: bytes, params: wave._wave_params) -> bytes:
        """
        Convert audio to LINEAR16 format (16-bit PCM stereo)
        
        LINEAR16 specifications:
        - 16-bit depth
        - Stereo (2 channels)
        - Linear PCM encoding
        - Signed integer samples
        - Little-endian byte order
        """
        # Convert to 16-bit if needed
        if params.sampwidth != 2:
            # Convert to 16-bit samples
            new_frames = bytearray()
            for i in range(0, len(frames), params.sampwidth):
                sample = int.from_bytes(frames[i:i+params.sampwidth], 'little')
                new_frames.extend(struct.pack('<h', sample))
            frames = bytes(new_frames)

        # Convert to stereo if mono
        if params.nchannels == 1:
            # Duplicate mono channel to create stereo
            new_frames = bytearray()
            for i in range(0, len(frames), 2):
                sample = frames[i:i+2]  # Get 16-bit sample
                new_frames.extend(sample)  # Left channel
                new_frames.extend(sample)  # Right channel (duplicate)
            frames = bytes(new_frames)

        return self._create_wav(frames, 2, params.framerate, 2)

    def _to_pcm(self, frames: bytes, params: wave._wave_params) -> bytes:
        """Convert audio to PCM format (16-bit mono)"""
        if params.sampwidth != 2:
            # Convert to 16-bit samples
            new_frames = bytearray()
            for i in range(0, len(frames), params.sampwidth):
                sample = int.from_bytes(frames[i:i+params.sampwidth], 'little')
                new_frames.extend(struct.pack('<h', sample))
            frames = bytes(new_frames)

        if params.nchannels == 2:
            # Convert stereo to mono by averaging channels
            new_frames = bytearray()
            for i in range(0, len(frames), 4):  # 4 bytes per stereo sample
                left = struct.unpack('<h', frames[i:i+2])[0]
                right = struct.unpack('<h', frames[i+2:i+4])[0]
                mono = (left + right) // 2
                new_frames.extend(struct.pack('<h', mono))
            frames = bytes(new_frames)

        return self._create_wav(frames, 1, params.framerate, 2)

    def _to_mulaw(self, frames: bytes, params: wave._wave_params) -> bytes:
        """Convert audio to mu-law format (8-bit mono)"""
        # First convert to 16-bit mono if needed
        if params.sampwidth != 2 or params.nchannels == 2:
            frames = self._to_pcm(frames, params)
            with wave.open(BytesIO(frames), 'rb') as wav_file:
                params = wav_file.getparams()
                frames = wav_file.readframes(params.nframes)

        # Convert to 8-bit mu-law
        MU = 10  # mu-law compression parameter
        new_frames = bytearray()
        for i in range(0, len(frames), 2):
            sample = struct.unpack('<h', frames[i:i+2])[0]
            # Normalize to [-1, 1]
            normalized = sample / 32767.0
            # mu-law compression
            if normalized >= 0:
                compressed = math.log(1 + MU * normalized) / math.log(1 + MU)
                # Scale to [128, 255]
                compressed = int(128 + (compressed * 127))
            else:
                compressed = math.log(1 + MU * abs(normalized)) / math.log(1 + MU)
                # Scale to [0, 127]
                compressed = int(127 - (compressed * 127))
            new_frames.append(compressed)

        # Use original sample rate instead of fixed 8000Hz
        return self._create_wav(bytes(new_frames), 1, params.framerate, 1)

    def _create_wav(self, frames: bytes, channels: int, framerate: int, sampwidth: int) -> bytes:
        """Create a WAV file from audio frames."""
        buffer = BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sampwidth)
            wav_file.setframerate(framerate)
            wav_file.writeframes(frames)
        return buffer.getvalue() 