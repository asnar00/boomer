# processor

Real-time audio processor that transforms ref audio and outputs to processed.

## behaviour

The processor takes ref audio as input and produces processed audio as output. Processing happens on-demand as audio is played back - only the chunks being played are processed.

A "processed" button appears in the source selector (after "room"). Selecting it plays the processed output. The processor is a passthrough initially (output equals input), providing a framework for adding actual processing later.

Processed audio is buffered so each position is only processed once. The buffer can be exported to processed.wav.

## metering

The processed source appears in metering like ref and room:
- Can be selected as the playing source for visualization
- Can be selected as comparison source
- History is stored per time bucket like other sources

## constraints

- Processing is lazy - only process what's needed for playback
- Buffer persists during session (cleared on server restart)
- Switching to processed source should be seamless (crossfade like other sources)
