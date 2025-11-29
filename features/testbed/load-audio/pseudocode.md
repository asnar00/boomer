# load-audio pseudocode

## backend

### on startup

```
function load_audio_files():
    ref_audio = load_wav("ref.wav")
    room_audio = load_wav("room.wav")

    if ref_audio.sample_rate != room_audio.sample_rate:
        raise error "sample rates must match"

    store ref_audio and room_audio for playback

function load_wav(path):
    if file does not exist:
        raise error with clear message

    read wav file
    convert to float array in range [-1, 1]
    return { data, sample_rate, channels, duration }
```

## frontend

### on connect

```
connect to backend via websocket

when connection established:
    receive audio_loaded message with metadata
    display "ref: {duration}s, room: {duration}s, {sample_rate}Hz"

when connection fails:
    display error message
```

## messages

```
backend -> frontend:
    audio_loaded: { ref: {duration, sample_rate, channels}, room: {duration, sample_rate, channels} }
    error: { message }
```
