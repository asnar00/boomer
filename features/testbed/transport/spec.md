# transport

Playback controls for audio navigation.

## behaviour

The frontend displays transport controls: play/pause button, current position, total duration. User can click play to start audio, pause to stop, and skip forward/back 10 seconds.

Backend streams audio to the system output via sounddevice. Playback position is tracked and sent to frontend periodically for display sync.

## controls

- **Play/Pause** - Toggle playback state
- **Skip back 10s** - Jump backward, clamped to start
- **Skip forward 10s** - Jump forward, clamped to end
- **Position display** - Shows current time / total duration

## constraints

- Playback must be gapless and glitch-free
- Position updates to frontend at ~10Hz (sufficient for UI)
- Pausing preserves position; play resumes from same point
