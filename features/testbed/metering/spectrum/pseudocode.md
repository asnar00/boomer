# spectrum pseudocode

## backend

### measure

```
function measure(audio_chunk, sample_rate):
    if stereo: convert to mono by averaging channels

    apply window function (Hann) to reduce spectral leakage
    compute FFT
    take magnitude of positive frequencies
    convert to dB scale (20 * log10)

    group into logarithmic frequency bands (e.g., 32 bands)
    return array of band magnitudes in dB
```

### compare

```
function compare(ref_bands, room_bands):
    compute absolute difference for each band
    return mean of differences
```

## frontend

### visualize

```
function visualize(ctx, canvas, ref_bands, room_bands):
    clear canvas

    calculate x positions for each band (logarithmic spacing)
    calculate y scale (dB range, e.g., -60 to 0)

    draw ref spectrum as filled area or line (blue)
    draw room spectrum as filled area or line (orange)

    draw frequency axis labels
    draw dB axis labels
```
