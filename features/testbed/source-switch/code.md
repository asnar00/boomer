# source-switch code

## dependencies

No additional dependencies.

---

## backend (Python)

### playback.py modifications

```python
# crossfade state
crossfade_samples = 0
crossfade_from_audio = None
CROSSFADE_MS = 15  # milliseconds

def switch_source(new_source):
    global crossfade_samples, crossfade_from_audio

    if new_source not in ['ref', 'room']:
        return
    if new_source == state.source:
        return

    with playback_lock:
        if state.playing:
            # store current audio for crossfade
            crossfade_from_audio = audio_sources[state.source].data
            sample_rate = audio_sources[state.source].sample_rate
            crossfade_samples = int(sample_rate * CROSSFADE_MS / 1000)

        state.source = new_source

    log('transport', f'Source: {new_source}')
    broadcast_state()

def audio_callback(outdata, frames, time_info, status):
    global playback_position, crossfade_samples, crossfade_from_audio

    audio = get_current_audio()

    with playback_lock:
        start = playback_position
        end = start + frames

        if end >= len(audio):
            # reached end - handle as before
            # ... existing end-of-audio code ...
        else:
            if audio.ndim == 1:
                outdata[:, 0] = audio[start:end]
                if outdata.shape[1] > 1:
                    outdata[:, 1] = audio[start:end]
            else:
                outdata[:] = audio[start:end]

            # apply crossfade if switching sources
            if crossfade_samples > 0 and crossfade_from_audio is not None:
                fade_frames = min(frames, crossfade_samples)

                # get old source audio
                if crossfade_from_audio.ndim == 1:
                    old_samples = crossfade_from_audio[start:start+fade_frames]
                else:
                    old_samples = crossfade_from_audio[start:start+fade_frames]

                # create crossfade ramp
                t = np.linspace(0, 1, fade_frames)
                fade_in = t.reshape(-1, 1)
                fade_out = (1 - t).reshape(-1, 1)

                # blend
                if crossfade_from_audio.ndim == 1:
                    old_stereo = np.column_stack([old_samples, old_samples])
                else:
                    old_stereo = old_samples

                outdata[:fade_frames] = (outdata[:fade_frames] * fade_in +
                                         old_stereo[:fade_frames] * fade_out)

                crossfade_samples -= fade_frames
                if crossfade_samples <= 0:
                    crossfade_from_audio = None

            playback_position = end
```

### main.py modifications

```python
from playback import start_playback, stop_playback, seek, start_position_thread, switch_source

# in websocket handler
if data['type'] == 'source':
    switch_source(data['name'])

# update api_source to use switch_source
@app.route('/api/source', methods=['POST'])
def api_source():
    name = request.args.get('name', 'ref')
    switch_source(name)
    return jsonify(get_state_dict())
```

## frontend (JavaScript)

### index.html additions

```html
<div id="sources">
    <button id="source-ref" class="source-btn active">ref</button>
    <button id="source-room" class="source-btn">room</button>
</div>
```

### CSS additions

```css
#sources { margin: 20px 0; }
.source-btn { margin-right: 10px; padding: 10px 20px; font-size: 16px; }
.source-btn.active { background: #333; color: white; }
```

### app.js additions

```javascript
// testbed/source-switch

const sourceRefBtn = document.getElementById('source-ref');
const sourceRoomBtn = document.getElementById('source-room');

function updateUI() {
    // existing updates...
    playPauseBtn.textContent = appState.playing ? 'Pause' : 'Play';
    positionDisplay.textContent = `${formatTime(appState.position)} / ${formatTime(appState.duration)}`;

    // source button highlights
    sourceRefBtn.classList.toggle('active', appState.source === 'ref');
    sourceRoomBtn.classList.toggle('active', appState.source === 'room');
}

sourceRefBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'source', name: 'ref' }));
    log('ui', 'Source: ref');
});

sourceRoomBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'source', name: 'room' }));
    log('ui', 'Source: room');
});
```
