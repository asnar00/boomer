# testbed/metering/spectrum

import numpy as np

NUM_BANDS = 32
MIN_FREQ = 20
MAX_FREQ = 20000

def measure(audio_chunk, sample_rate):
    """Compute logarithmic frequency band magnitudes"""
    # convert stereo to mono
    if audio_chunk.ndim > 1:
        audio_chunk = audio_chunk.mean(axis=1)

    # apply Hann window
    window = np.hanning(len(audio_chunk))
    windowed = audio_chunk * window

    # compute FFT and normalize by chunk size
    fft = np.fft.rfft(windowed)
    magnitudes = np.abs(fft) / len(audio_chunk)

    # frequency bins
    freqs = np.fft.rfftfreq(len(audio_chunk), 1/sample_rate)

    # create logarithmic band edges
    band_edges = np.logspace(np.log10(MIN_FREQ), np.log10(MAX_FREQ), NUM_BANDS + 1)

    # compute energy in each band
    bands = []
    for i in range(NUM_BANDS):
        low = band_edges[i]
        high = band_edges[i + 1]
        mask = (freqs >= low) & (freqs < high)
        if mask.any():
            band_energy = magnitudes[mask].mean()
        else:
            band_energy = 1e-10  # no data in this band
        bands.append(band_energy)

    # convert to dB
    bands = np.array(bands)
    bands_db = 20 * np.log10(bands + 1e-10)

    # normalize to reasonable range (clip to -80 to 0 dB)
    bands_db = np.clip(bands_db, -80, 0)

    return bands_db.tolist()

def compare(ref_bands, room_bands):
    """Compute mean absolute difference between spectra"""
    ref = np.array(ref_bands)
    room = np.array(room_bands)
    return float(np.mean(np.abs(ref - room)))
