# testbed/load-audio

import numpy as np
from scipy.io import wavfile
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AudioData:
    data: np.ndarray      # float32, shape (samples,) or (samples, channels)
    sample_rate: int
    channels: int
    duration: float

# global storage
audio_sources: dict[str, AudioData] = {}

def load_wav(path: str) -> AudioData:
    filepath = Path(path)
    if not filepath.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    sample_rate, data = wavfile.read(filepath)

    # convert to float32 normalized to [-1, 1]
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    elif data.dtype != np.float32:
        raise ValueError(f"Unsupported wav format: {data.dtype}")

    channels = 1 if data.ndim == 1 else data.shape[1]
    duration = len(data) / sample_rate

    return AudioData(data=data, sample_rate=sample_rate, channels=channels, duration=duration)

def load_audio_files():
    audio_sources['ref'] = load_wav('ref.wav')
    audio_sources['room'] = load_wav('room.wav')

    if audio_sources['ref'].sample_rate != audio_sources['room'].sample_rate:
        raise ValueError("Sample rates must match between ref.wav and room.wav")
