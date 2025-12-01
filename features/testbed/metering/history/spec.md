# history

Displays meter measurements over time rather than just the current instant.

## behaviour

Instead of showing a single measurement at the current playback position, the display shows all measurements collected so far, plotted against time on the X-axis.

Each measurement at time T is stored in a time bucket. The visualization renders all buckets as a 2D plot: time (X) vs measurement values (Y). For spectrum, this becomes a spectrogram with frequency on Y-axis and color indicating magnitude.

Separate history is maintained for each source (ref, room, processed) and each meter type.

## display

- X-axis: time in seconds
- Y-axis: measurement-specific (frequency bands for spectrum, dB for levels, etc.)
- Current playback position shown as a vertical line
- Comparison mode overlays or shows side-by-side histories for two sources
