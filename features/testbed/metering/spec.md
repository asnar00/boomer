# metering

Real-time audio quality measurements with unified interface and tabbed visualization.

## behaviour

The frontend displays a tab bar showing available measurement types. Selecting a tab shows a visualization area displaying that measurement for the currently playing audio source, updated in real-time during playback.

The meter always displays the currently playing source (ref, room, or processed). Optionally, a second source can be selected for comparison, showing both side-by-side with a difference score.

Backend computes measurements from the current playback position and streams them to the frontend. Each measurement type follows a common interface: measure, compare, and visualize.

Meter selection persists across page refreshes using localStorage.

## interface

Each measurement type implements:
- **measure** - Extract values from an audio chunk
- **compare** - Compute difference between two measurements
- **visualize** - Render measurement in the UI (bar graph for spectrum)

## UI layout

- Tab bar below transport controls showing measurement types
- "Playing: [source]" label showing which source is currently active
- "Compare to:" dropdown to optionally select a second source for comparison (none/ref/room/processed)
- Visualization area shows bar graph for current measurement
- Difference score displayed when comparing two sources

## technical notes

- FFT chunk size: 8192 samples (~5.4Hz resolution at 44.1kHz) to ensure all frequency bands have real data
- 32 logarithmic frequency bands from 20Hz to 20kHz
- Meter update rate: 20Hz
- Uses `import playback` and `playback.playback_position` (not `from playback import playback_position`) to get live position updates

## sub-features

- `spectrum` - Frequency spectrum analysis (implemented)
- `dynamics` - Dynamic range / compression
- `stereo` - Stereo width and correlation
- `reverb` - Reverb and decay characteristics
- `transients` - Attack sharpness
- `level` - RMS and peak levels
