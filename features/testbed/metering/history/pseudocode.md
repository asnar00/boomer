# history pseudocode

## backend

### meter message

```
add time field to meter message:
    time = current_position / sample_rate (in seconds)

meter message now contains:
    type, name, time, ref, room, diff
```

## frontend

### data storage

```
replace single meterData with history storage:
    meterHistory[source][timeBucket] = measurement_data

timeBucket = round time to nearest bucket size (e.g., 0.1 seconds)

on meter message received:
    store ref data at message.time in meterHistory.ref
    store room data at message.time in meterHistory.room
```

### visualization

```
function updateMeterDisplay():
    get sorted list of time buckets from history

    for playing source:
        get all data points from meterHistory[source]

    if comparing:
        get all data points from meterHistory[compareSource]

    call visualizer with history data, current position, duration

spectrum visualizer (spectrogram mode):
    clear canvas

    for each time bucket with data:
        x = time position on canvas
        for each frequency band:
            y = frequency band position
            color = magnitude to color (blue/cold = low, red/hot = high)
            draw colored rectangle at (x, y)

    draw vertical line at current playback position
    draw time axis labels
    draw frequency axis labels

    if comparing:
        either split canvas vertically (top/bottom)
        or draw difference as separate color scale
```

### clearing history

```
on meter tab change:
    clear meterHistory for all sources

on seek (optional):
    could keep history or clear depending on preference
```
