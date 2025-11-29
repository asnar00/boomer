# load-audio

Load wav files into memory for playback and processing.

## behaviour

On startup, the backend loads `ref.wav` and `room.wav` from the project root. Audio data is stored as arrays of floats, normalized to range [-1, 1]. Sample rate and channel count are preserved.

The frontend connects to the backend via websocket and receives confirmation that audio is loaded, along with metadata (duration, sample rate, channels).

## constraints

- Support stereo and mono wav files
- Sample rates must match; error if they differ
- Report errors clearly if files are missing or corrupt
