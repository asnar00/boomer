# source-switch pseudocode

## backend

### crossfade state

```
global:
    crossfade_samples = 0
    crossfade_from = null  (previous source audio)
    crossfade_length = sample_rate * 0.015  (15ms)
```

### switch source

```
function switch_source(new_source):
    if new_source == current source: return

    if currently playing:
        store current source audio as crossfade_from
        set crossfade_samples = crossfade_length

    set state.source = new_source
    broadcast state
```

### audio callback modification

```
in audio_callback:
    get samples from current source

    if crossfade_samples > 0:
        get same position samples from crossfade_from
        blend old -> new over crossfade_samples
        decrement crossfade_samples

    output blended audio
```

### handle source command from frontend

```
on websocket message:
    if type is "source":
        switch_source(message.name)
```

## frontend

### UI elements

```
on page load:
    create source buttons: "ref", "room"
    highlight currently active source
```

### button handlers

```
on source button click:
    send { type: "source", name: button_name }
```

### state updates

```
on state message from backend:
    update button highlights to show active source
```

## messages

```
frontend -> backend:
    source: { type: "source", name: "ref" | "room" }
```
