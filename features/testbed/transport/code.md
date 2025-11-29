# transport code

## dependencies

### backend (Python)

```bash
pip install sounddevice
```

### frontend

No dependencies - vanilla JS.

---

## backend (Python)

### playback.py

```python
import sounddevice as sd
import threading
import time
from audio import audio_sources
from state import state, broadcast_state
from logger import log

# playback state
stream = None
playback_position = 0  # in samples
playback_lock = threading.Lock()

def get_current_audio():
    return audio_sources[state.source].data

def audio_callback(outdata, frames, time_info, status):
    global playback_position

    audio = get_current_audio()
    sample_rate = audio_sources[state.source].sample_rate

    with playback_lock:
        start = playback_position
        end = start + frames

        if end >= len(audio):
            # reached end of audio
            end = len(audio)
            outdata[:end-start] = audio[start:end].reshape(-1, audio.shape[1] if audio.ndim > 1 else 1)
            outdata[end-start:] = 0  # silence for remaining
            playback_position = len(audio)
            # schedule stop (can't stop from callback)
            threading.Thread(target=stop_playback).start()
        else:
            if audio.ndim == 1:
                outdata[:] = audio[start:end].reshape(-1, 1)
            else:
                outdata[:] = audio[start:end]
            playback_position = end

def start_playback():
    global stream, playback_position

    if state.playing:
        return

    audio = get_current_audio()
    sample_rate = audio_sources[state.source].sample_rate
    channels = audio_sources[state.source].channels

    # if at end, restart from beginning
    with playback_lock:
        if playback_position >= len(audio):
            playback_position = 0

    stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=max(channels, 2),  # at least stereo output
        callback=audio_callback,
        blocksize=4096,  # larger buffer to prevent underruns
        latency='high'   # prioritize stability over low latency
    )
    stream.start()

    state.playing = True
    log('transport', f'Play from {state.position:.1f}s')
    broadcast_state()

def stop_playback():
    global stream

    if not state.playing:
        return

    if stream:
        stream.stop()
        stream.close()
        stream = None

    state.playing = False
    log('transport', f'Pause at {state.position:.1f}s')
    broadcast_state()

def seek(position_seconds):
    global playback_position

    sample_rate = audio_sources[state.source].sample_rate
    audio = get_current_audio()

    with playback_lock:
        playback_position = int(position_seconds * sample_rate)
        playback_position = max(0, min(playback_position, len(audio)))
        state.position = playback_position / sample_rate

    log('transport', f'Seek to {state.position:.1f}s')
    broadcast_state()

def position_update_loop():
    """Run in background thread to update position during playback"""
    while True:
        if state.playing:
            sample_rate = audio_sources[state.source].sample_rate
            with playback_lock:
                state.position = playback_position / sample_rate
            broadcast_state()
        time.sleep(0.1)  # 10Hz updates

def start_position_thread():
    thread = threading.Thread(target=position_update_loop, daemon=True)
    thread.start()
```

### main.py modifications

```python
from playback import start_playback, stop_playback, seek, start_position_thread

# in websocket handler, add transport message handling
@sock.route('/ws')
def websocket(ws):
    # ... existing code ...

    while True:
        message = ws.receive()
        if message is None:
            break

        data = json.loads(message)

        if data['type'] == 'log':
            log(data['category'], data['message'], source='frontend')

        # testbed/transport
        if data['type'] == 'play':
            start_playback()
        if data['type'] == 'pause':
            stop_playback()
        if data['type'] == 'seek':
            seek(data['position'])

    # ... rest of handler ...

# at startup, start position update thread
if __name__ == '__main__':
    init_logging()
    load_audio_files()
    state.duration = audio_sources['ref'].duration
    start_position_thread()
    # ... rest of startup ...
```

## frontend (JavaScript)

### index.html additions

```html
<div id="controls">
    <button id="skip-back">-10s</button>
    <button id="play-pause">Play</button>
    <button id="skip-forward">+10s</button>
    <span id="position">0:00 / 0:00</span>
</div>
```

### app.js additions

```javascript
// testbed/transport

const playPauseBtn = document.getElementById('play-pause');
const skipBackBtn = document.getElementById('skip-back');
const skipForwardBtn = document.getElementById('skip-forward');
const positionDisplay = document.getElementById('position');

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function updateUI() {
    // update play/pause button
    playPauseBtn.textContent = appState.playing ? 'Pause' : 'Play';

    // update position display
    positionDisplay.textContent = `${formatTime(appState.position)} / ${formatTime(appState.duration)}`;
}

playPauseBtn.addEventListener('click', () => {
    if (appState.playing) {
        ws.send(JSON.stringify({ type: 'pause' }));
        log('ui', 'Pause clicked');
    } else {
        ws.send(JSON.stringify({ type: 'play' }));
        log('ui', 'Play clicked');
    }
});

skipBackBtn.addEventListener('click', () => {
    const newPos = Math.max(0, appState.position - 10);
    ws.send(JSON.stringify({ type: 'seek', position: newPos }));
    log('ui', 'Skip back clicked');
});

skipForwardBtn.addEventListener('click', () => {
    const newPos = Math.min(appState.duration, appState.position + 10);
    ws.send(JSON.stringify({ type: 'seek', position: newPos }));
    log('ui', 'Skip forward clicked');
});
```
