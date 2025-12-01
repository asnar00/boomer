# spectrum

Frequency spectrum analysis showing energy distribution across frequency bands.

## behaviour

Computes FFT of audio chunk and converts to logarithmic frequency bands. Displays ref and room spectra overlaid, with ref in one color and room in another. Difference score is the mean absolute difference across bands.

## visualization

- X-axis: frequency (logarithmic scale, ~20Hz to ~20kHz)
- Y-axis: magnitude in dB
- Ref spectrum shown as one color (e.g., blue)
- Room spectrum shown as another color (e.g., orange)
- Overlaid so differences are visible

## expected differences

Room recording likely shows:
- Rolled-off high frequencies (absorption, phone mic)
- Boosted or resonant low-mid frequencies (room modes)
- Overall different shape due to PA + room + phone response
