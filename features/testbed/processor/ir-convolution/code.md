# ir-convolution code

## backend

### processor.py additions

```python
# testbed/processor/ir-convolution

from scipy.signal import fftconvolve

# IR parameters
TRAINING_DURATION = 90  # seconds
IR_MAX_LENGTH = 2.0     # seconds
REGULARIZATION = 0.01

# Extracted impulse response
impulse_response = None

def extract_impulse_response(ref_data, room_data, sample_rate):
    """Extract impulse response using Wiener deconvolution"""
    global impulse_response

    training_samples = int(TRAINING_DURATION * sample_rate)
    ir_length_samples = int(IR_MAX_LENGTH * sample_rate)

    # Take training portion
    ref = ref_data[:training_samples]
    room = room_data[:training_samples]

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
    return ir
```

### init_processor modification

```python
def init_processor():
    """Initialize the processor with IR-convolved audio"""
    global processed_buffer, processed_valid, impulse_response

    ref = audio_sources['ref']
    room = audio_sources['room']

    # Extract impulse response
    log('processor', 'Extracting impulse response...')
    ir = extract_impulse_response(ref.data, room.data, ref.sample_rate)
    log('processor', f'IR extracted: {len(ir)} samples ({len(ir)/ref.sample_rate:.2f}s)')

    # Convert ref to mono for convolution
    ref_mono = ref.data
    if ref_mono.ndim > 1:
        ref_mono = np.mean(ref_mono, axis=1)

    # Convolve entire ref with IR
    log('processor', 'Convolving ref with IR...')
    convolved = fftconvolve(ref_mono, ir, mode='same')

    # Normalize to match room levels
    room_mono = room.data
    if room_mono.ndim > 1:
        room_mono = np.mean(room_mono, axis=1)

    room_rms = np.sqrt(np.mean(room_mono ** 2))
    conv_rms = np.sqrt(np.mean(convolved ** 2))
    if conv_rms > 0:
        convolved *= room_rms / conv_rms

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

    log('processor', f'Initialized processor: {len(processed_buffer)} samples, RMS matched to room')
```

### process_chunk modification

```python
def process_chunk(start_sample, end_sample):
    """No-op since we pre-convolve everything at init"""
    pass  # All processing done at init time
```
