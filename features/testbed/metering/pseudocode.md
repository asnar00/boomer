# metering pseudocode

## backend

### measurement registry

```
measurements = dictionary of measurement_name -> measurement_module

each measurement_module provides:
    measure(audio_chunk, sample_rate) -> measurement_data
    compare(data_a, data_b) -> difference_score
```

### metering loop

```
CHUNK_SIZE = 8192  # ~5.4Hz resolution at 44.1kHz
METER_RATE = 20    # Hz

function metering_loop():
    while running:
        if playing and has_subscriptions:
            with playback_lock:
                pos = playback.playback_position  # use module reference, not imported value

            ref_chunk = get_chunk_at_position(ref_audio, pos, CHUNK_SIZE)
            room_chunk = get_chunk_at_position(room_audio, pos, CHUNK_SIZE)

            for each client, subscribed_measurements:
                for each measurement_name in subscribed:
                    ref_data = measurement.measure(ref_chunk, sample_rate)
                    room_data = measurement.measure(room_chunk, sample_rate)
                    diff = measurement.compare(ref_data, room_data)

                    send to client: {
                        type: "meter",
                        name: measurement_name,
                        ref: ref_data,
                        room: room_data,
                        diff: diff
                    }

        sleep 1/METER_RATE seconds
```

### handle metering commands

```
on websocket message:
    if type is "meter_subscribe":
        add measurement to client_subscriptions[ws]

    if type is "meter_unsubscribe":
        remove measurement from client_subscriptions[ws]

on client disconnect:
    delete client_subscriptions[ws]
```

## frontend

### initialization

```
on page load:
    create tab for each available measurement type

on websocket connect:
    restore meter selection from localStorage
    if saved meter exists:
        select that meter (subscribe)
```

### tab bar

```
on tab click:
    unsubscribe from previous measurement
    save new selection to localStorage
    subscribe to new measurement
    update tab highlights
    clear display
```

### visualization

```
on meter message:
    if message.name matches current meter:
        store ref and room data
        call updateMeterDisplay()

function updateMeterDisplay():
    playingSource = appState.source  # currently playing (ref/room/processed)
    playingData = meterData[playingSource]

    compareSource = compare dropdown value (or empty for none)
    compareData = meterData[compareSource] if comparing

    call visualizer(playingData, compareData, playingSource, compareSource)

    if comparing:
        compute and display difference score
```

### spectrum visualizer

```
function visualize_spectrum(ctx, canvas, bandsA, bandsB, labelA, labelB):
    clear canvas
    draw grid (-80dB to 0dB)

    if comparing (bandsB exists):
        bar_width = half width per band
        draw bandsA bars (blue) on left
        draw bandsB bars (orange) on right
        draw legend with labels
    else:
        bar_width = full width per band
        draw bandsA bars (blue)

    draw frequency labels (20Hz to 20kHz, logarithmic)
```

## messages

```
frontend -> backend:
    meter_subscribe: { type: "meter_subscribe", name: measurement_name }
    meter_unsubscribe: { type: "meter_unsubscribe", name: measurement_name }

backend -> frontend:
    meter: { type: "meter", name, ref, room, diff }
```

## persistence

```
localStorage keys:
    currentMeter - selected meter tab name
```
