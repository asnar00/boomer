# testbed

Interactive environment for developing and testing audio processors.

## purpose

Provides a browser-based interface for:
- Loading reference and room-recorded audio files
- Playing back audio with standard transport controls
- Switching between different audio sources (ref, room, processed)
- Measuring audio qualities in real-time
- Applying and adjusting filter chains
- Comparing measurements between sources

The testbed ensures all processing runs in real-time, allowing immediate feedback while developing filters that simulate room acoustics.

## sub-features

- `load-audio` - Load wav files into memory on the backend
- `transport` - Play, pause, seek controls
- `source-switch` - Switch between ref/room/processed audio
- `metering` - Real-time audio quality measurements
- `filters` - Apply and configure processing chains
- `logging` - Unified logging across backend and frontend
- `remote-control` - HTTP API for programmatic control
