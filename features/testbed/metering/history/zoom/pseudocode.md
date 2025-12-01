# zoom pseudocode

## state

```
viewStart = load from storage, or 0
viewEnd = load from storage, or duration

min buckets visible = 64
max buckets visible = duration / bucket_size
```

## persistence

```
function saveViewState():
    save viewStart to storage
    save viewEnd to storage

// call saveViewState after any view change
```

## zoom (button controls)

```
on zoom in button (+):
    zoomBy(0.5)  // halve duration

on zoom out button (-):
    zoomBy(2)    // double duration

on reset button:
    viewStart = 0
    viewEnd = duration
    saveViewState()
    redraw

function zoomBy(factor):
    currentDuration = viewEnd - viewStart
    playPos = current playback position

    // where is play cursor on screen (0-1)
    playRatio = (playPos - viewStart) / currentDuration

    newDuration = currentDuration * factor

    // clamp to min/max zoom
    minDuration = 64 * bucket_size
    maxDuration = track_duration
    newDuration = clamp(newDuration, minDuration, maxDuration)

    // zoom centered on playhead (keep at same screen position)
    viewStart = playPos - playRatio * newDuration
    viewEnd = viewStart + newDuration

    // clamp to track bounds
    if viewStart < 0:
        viewStart = 0
        viewEnd = newDuration
    if viewEnd > duration:
        viewEnd = duration
        viewStart = duration - newDuration

    saveViewState()
    redraw
```

## auto-scroll during playback

```
in updateMeterDisplay():
    if playing and not dragging:
        viewDuration = viewEnd - viewStart
        playRatio = (playPosition - viewStart) / viewDuration

        // if cursor past 75% of view, scroll to keep it at 75%
        if playRatio > 0.75:
            newStart = playPosition - 0.75 * viewDuration
            viewStart = min(newStart, duration - viewDuration)
            viewEnd = viewStart + viewDuration
            saveViewState()
```

## auto-scroll on transport skip

```
function ensureCursorVisible(pos):
    viewDuration = viewEnd - viewStart
    posRatio = (pos - viewStart) / viewDuration

    // if cursor outside 25%-75% range, scroll to center it at 50%
    if posRatio < 0.25 or posRatio > 0.75:
        viewStart = pos - 0.5 * viewDuration
        viewEnd = viewStart + viewDuration

        // clamp to track bounds
        if viewStart < 0:
            viewStart = 0
            viewEnd = viewDuration
        if viewEnd > duration:
            viewEnd = duration
            viewStart = duration - viewDuration

        saveViewState()
        redraw

// call ensureCursorVisible after skip back/forward button clicks
```

## pan (drag)

```
track drag state:
    dragStartX = null
    dragStartViewStart = null

on touch start (1 finger) or mouse down:
    dragStartX = touch/mouse X position
    dragStartViewStart = viewStart

on touch move (1 finger) or mouse move (while dragging):
    deltaX = current X - dragStartX
    deltaTime = deltaX * (viewEnd - viewStart) / canvas_width

    newStart = dragStartViewStart - deltaTime
    viewDuration = viewEnd - viewStart
    newEnd = newStart + viewDuration

    // clamp to track bounds
    if newStart < 0:
        newStart = 0
        newEnd = viewDuration
    if newEnd > duration:
        newEnd = duration
        newStart = duration - viewDuration

    viewStart = newStart
    viewEnd = newEnd
    redraw

on touch end or mouse up:
    if was dragging:
        saveViewState()
    clear drag state
```

## visualization update

```
in visualizer:
    only draw buckets where time >= viewStart and time < viewEnd

    map time to X position:
        x = (time - viewStart) / (viewEnd - viewStart) * canvas_width

    update time axis labels to show viewStart to viewEnd range
```
