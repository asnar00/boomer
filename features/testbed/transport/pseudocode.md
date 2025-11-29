# transport pseudocode

## backend

### audio playback

```
global:
    audio_stream = null
    playback_position = 0 (in samples)

function start_playback():
    if already playing: return

    open audio output stream with callback
    set playing = true
    broadcast state

function stop_playback():
    if not playing: return

    close audio output stream
    set playing = false
    broadcast state

function audio_callback(output_buffer):
    get current source audio data

    samples_needed = length of output_buffer
    start = playback_position
    end = start + samples_needed

    if end > length of audio:
        end = length of audio
        stop_playback after this buffer

    copy audio[start:end] to output_buffer
    playback_position = end

function seek(position_seconds):
    playback_position = position_seconds * sample_rate
    clamp to valid range
    broadcast state
```

### position updates

```
function position_update_loop():
    while running:
        if playing:
            update state.position from playback_position
            broadcast state
        sleep 100ms (10Hz)
```

### handle transport commands from frontend

```
on websocket message:
    if type is "play": start_playback()
    if type is "pause": stop_playback()
    if type is "seek": seek(position)
```

## frontend

### UI elements

```
on page load:
    create play/pause button
    create skip back button (-10s)
    create skip forward button (+10s)
    create position display (current / total)
```

### button handlers

```
on play/pause click:
    send { type: "play" } or { type: "pause" } based on current state

on skip back click:
    send { type: "seek", position: current_position - 10 }

on skip forward click:
    send { type: "seek", position: current_position + 10 }
```

### state updates

```
on state message from backend:
    update position display
    update play/pause button appearance
```

## messages

```
frontend -> backend:
    play: { type: "play" }
    pause: { type: "pause" }
    seek: { type: "seek", position: seconds }
```
