# diff-view pseudocode

## frontend

### state

- diffViewEnabled: whether diff view mode is active
- diffTolerance: threshold for "matched" zone in dB (default 3)

### UI additions

Add checkbox to toggle diff view mode.
Add slider for tolerance (1-10 dB range).

### color function

function diffToColor(diff, tolerance):
    if absolute value of diff is less than tolerance:
        return green (intensity based on how close to zero)
    else if diff is positive (room louder):
        return red (intensity based on magnitude)
    else (diff is negative, processed louder):
        return blue (intensity based on magnitude)

### spectrogram drawing

When diff view is enabled and both room and processed history exist:

For each time bucket:
    For each frequency band:
        diff = room value - processed value
        color = diffToColor(diff, tolerance)
        draw rectangle at time/frequency with color

Show single full-height spectrogram (not split view).

### display updates

When diff view checkbox changes, redraw meter display.
When tolerance slider changes, redraw meter display.
