# ir-convolution pseudocode

## backend

### extract_impulse_response

function extract_impulse_response(ref_audio, room_audio, training_samples, ir_length_samples, regularization):

    take first training_samples from both ref and room

    if stereo, convert to mono by averaging channels

    zero-pad both to next power of 2 for efficient FFT

    compute FFT of both signals

    apply Wiener deconvolution:
        ir_fft = room_fft * conjugate(ref_fft) / (|ref_fft|² + regularization)

    inverse FFT to get time-domain IR

    take real part only

    truncate to ir_length_samples

    apply fade-out window to avoid clicks at end

    normalize IR so peak is 1.0

    return IR

### init_processor modification

in init_processor:
    after initializing buffers

    extract IR using first 90 seconds of ref and room
    store IR for later use in processing

    log IR extraction details (length, peak value, etc.)

### process_chunk modification

in process_chunk:
    instead of copying ref to processed

    convolve the requested chunk of ref with the IR

    note: convolution extends the signal, so we need to handle overlap

    store result in processed buffer

### convolution strategy

For efficient chunk-based convolution:

    option 1: pre-convolve entire ref with IR at startup (simple but memory-heavy)

    option 2: overlap-add convolution for each chunk (complex but memory-efficient)

    start with option 1 for simplicity - convolve full ref at init time
