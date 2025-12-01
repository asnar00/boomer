# zoom

Allows zooming and panning the time-series meter display.

## behaviour

The user can zoom in to see finer time detail or zoom out to see the full track. Panning moves the visible time window left or right when zoomed in.

Zoom levels range from showing the entire track duration to showing approximately 64 time buckets (6.4 seconds at 100ms resolution).

Zooming centers on the current playback position, keeping the play cursor at the same screen position.

During playback, the view auto-scrolls to keep the play cursor visible. When the cursor moves past 75% of the visible width, the view scrolls to keep it at 75%.

When using transport skip controls (±10s), if the cursor jumps outside the 25%-75% visible range, the view auto-scrolls to center it at 50%.

View state (zoom level and scroll position) persists across browser refresh.

## controls

- **+ button**: zoom in (halve visible duration, centered on playhead)
- **- button**: zoom out (double visible duration, centered on playhead)
- **Reset button**: reset to full track view (max zoom out)
- **Drag on canvas**: pan left/right when zoomed in (touch or mouse)

## display

The visible time window adjusts based on zoom level. Time axis labels update to reflect the current view range.
