# testbed/processor, testbed/processor/ir-convolution

import numpy as np
from scipy.signal import fftconvolve
from audio import audio_sources, AudioData
from logger import log

# processed audio buffer - stores processed output for each time position
processed_buffer = None  # numpy array, same shape as ref audio
processed_valid = None   # boolean array tracking which samples have been processed

# testbed/processor/ir-convolution - IR parameters
TRAINING_DURATION = 90  # seconds
IR_MAX_LENGTH = 0.5     # seconds (balance between smear and frequency capture)
REGULARIZATION = 0.01

# Extracted impulse response
impulse_response = None

def extract_impulse_response(ref_data, room_data, sample_rate):
    """Extract impulse response using Wiener deconvolution"""
    global impulse_response

    training_samples = int(TRAINING_DURATION * sample_rate)
    ir_length_samples = int(IR_MAX_LENGTH * sample_rate)

    # Take training portion
    ref = ref_data[:training_samples].copy()
    room = room_data[:training_samples].copy()

    # Convert stereo to mono if needed
    if ref.ndim > 1:
        ref = np.mean(ref, axis=1)
    if room.ndim > 1:
        room = np.mean(room, axis=1)

    # Zero-pad to next power of 2
    n = 1
    while n < len(ref) + ir_length_samples:
        n *= 2

    ref_padded = np.zeros(n)
    room_padded = np.zeros(n)
    ref_padded[:len(ref)] = ref
    room_padded[:len(room)] = room

    # FFT
    ref_fft = np.fft.rfft(ref_padded)
    room_fft = np.fft.rfft(room_padded)

    # Wiener deconvolution
    ref_power = np.abs(ref_fft) ** 2
    ir_fft = room_fft * np.conj(ref_fft) / (ref_power + REGULARIZATION)

    # Inverse FFT
    ir = np.fft.irfft(ir_fft)

    # Take real part and truncate
    ir = np.real(ir[:ir_length_samples])

    # Apply fade-out window (last 10%)
    fade_samples = ir_length_samples // 10
    fade = np.linspace(1, 0, fade_samples)
    ir[-fade_samples:] *= fade

    # Normalize
    peak = np.max(np.abs(ir))
    if peak > 0:
        ir /= peak

    impulse_response = ir

    # Log IR characteristics
    peak_idx = np.argmax(np.abs(ir))
    log('processor', f'IR peak at sample {peak_idx} ({peak_idx/sample_rate*1000:.1f}ms)')

    return ir

def init_processor():
    """Initialize the processor with IR-convolved audio"""
    global processed_buffer, processed_valid, impulse_response

    ref = audio_sources['ref']
    room = audio_sources['room']

    # testbed/processor/ir-convolution - Extract impulse response
    log('processor', 'Extracting impulse response...')
    ir = extract_impulse_response(ref.data, room.data, ref.sample_rate)
    log('processor', f'IR extracted: {len(ir)} samples ({len(ir)/ref.sample_rate:.2f}s)')

    # Convert ref to mono for convolution
    ref_mono = ref.data.copy()
    if ref_mono.ndim > 1:
        ref_mono = np.mean(ref_mono, axis=1)

    # Convolve entire ref with IR (use 'full' and trim to maintain alignment)
    log('processor', 'Convolving ref with IR...')
    convolved_full = fftconvolve(ref_mono, ir, mode='full')
    # Trim to same length as input - IR starts at t=0, so just take first len(ref_mono) samples
    convolved = convolved_full[:len(ref_mono)]

    # Normalize to match room levels
    room_mono = room.data.copy()
    if room_mono.ndim > 1:
        room_mono = np.mean(room_mono, axis=1)

    room_rms = np.sqrt(np.mean(room_mono ** 2))
    conv_rms = np.sqrt(np.mean(convolved ** 2))
    if conv_rms > 0:
        convolved *= room_rms / conv_rms
    log('processor', f'Level matched: room RMS={room_rms:.4f}, conv RMS={conv_rms:.4f}')

    # Store as processed buffer (expand back to stereo if needed)
    if ref.data.ndim > 1:
        processed_buffer = np.column_stack([convolved, convolved])
    else:
        processed_buffer = convolved

    processed_valid = np.ones(len(ref.data), dtype=bool)  # All pre-processed

    # Register processed as an audio source
    audio_sources['processed'] = AudioData(
        data=processed_buffer,
        sample_rate=ref.sample_rate,
        channels=ref.channels,
        duration=ref.duration
    )

    log('processor', f'Initialized processor: {len(processed_buffer)} samples with IR convolution')

def process_chunk(start_sample, end_sample):
    """No-op since we pre-convolve everything at init"""
    # testbed/processor/ir-convolution - all processing done at init time
    pass

def get_processed_at_position(position_samples, num_samples):
    """Return processed data at position (already computed at init)"""
    if processed_buffer is None:
        return None

    start = max(0, position_samples)
    end = min(len(processed_buffer), position_samples + num_samples)

    return processed_buffer[start:end]

def clear_processed():
    """Clear processed buffer (call when parameters change)"""
    global processed_valid
    if processed_valid is not None:
        processed_valid[:] = False
        log('processor', 'Cleared processed buffer')

def save_processed_wav(filepath='processed.wav'):
    """Save the processed buffer to a WAV file"""
    from scipy.io import wavfile

    if processed_buffer is None:
        log('processor', 'No processed data to save')
        return False

    ref = audio_sources['ref']

    # Convert back to int16 for WAV
    audio_int16 = (processed_buffer * 32767).astype(np.int16)

    wavfile.write(filepath, ref.sample_rate, audio_int16)
    log('processor', f'Saved processed audio to {filepath}')
    return True
