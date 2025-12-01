# diff-view

Displays the difference between room and processed audio as a color-coded spectrogram.

## behaviour

Instead of showing raw spectral data, this mode shows how well the processed audio matches the room target. The difference (room minus processed) is displayed for each frequency band at each time point.

The goal is to make the processor produce output that matches room. A perfect match shows all green. Errors are color-coded by direction: red means processed is too quiet (positive diff), blue means processed is too loud (negative diff).

## color mapping

- Green: difference near zero (within tolerance)
- Red: positive difference (room louder than processed - need more gain)
- Blue: negative difference (processed louder than room - need less gain)

Color intensity scales with the magnitude of the difference.

## controls

A tolerance slider controls how wide the "green zone" is (default 3dB). Values within tolerance appear green; values outside fade to red or blue.
