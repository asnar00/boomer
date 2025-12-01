# ir-convolution

Extracts an impulse response from ref and room audio, then applies it to ref via convolution to simulate room acoustics.

## behaviour

On startup, the processor extracts an impulse response by deconvolving the room recording from the ref recording. This IR captures the room's acoustic signature including reverb, frequency response, and resonances.

When processing audio, ref is convolved with this IR to produce output that should closely match the room recording's acoustic character.

## extraction

Uses Wiener deconvolution with regularization to avoid noise amplification:
- Takes first 90 seconds of ref and room audio for extraction
- Computes IR in frequency domain: IR = room × conj(ref) / (|ref|² + ε)
- Transforms back to time domain and truncates to reasonable length

## parameters

- Training duration: how much audio to use for IR extraction (default 90s)
- IR length: maximum length of extracted IR (default 2s)
- Regularization: controls noise/artifact tradeoff (default 0.01)
