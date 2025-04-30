import wave
from io import BytesIO

def create_mock_wav():
    buffer = BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        wav_file.writeframes(b'\x00' * 44100)
    buffer.seek(0)
    return buffer.getvalue() 