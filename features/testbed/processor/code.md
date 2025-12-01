# processor code

## backend (Python)

### processor.py (new file)

```python
# testbed/processor

import numpy as np
from audio import audio_sources, AudioData
from logger import log

# processed audio buffer
processed_buffer = None
processed_valid = None

def init_processor():
    global processed_buffer, processed_valid

    ref = audio_sources['ref']
    processed_buffer = np.zeros_like(ref.data)
    processed_valid = np.zeros(len(ref.data), dtype=bool)

    audio_sources['processed'] = AudioData(
        data=processed_buffer,
        sample_rate=ref.sample_rate,
        channels=ref.channels,
        duration=ref.duration
    )
    log('processor', f'Initialized: {len(processed_buffer)} samples')

def process_chunk(start_sample, end_sample):
    global processed_buffer, processed_valid

    if processed_buffer is None:
        return

    ref_data = audio_sources['ref'].data
    start = max(0, start_sample)
    end = min(len(ref_data), end_sample)

    if start >= end:
        return

    if np.all(processed_valid[start:end]):
        return

    # === PROCESSING (passthrough for now) ===
    processed_buffer[start:end] = ref_data[start:end]
    # === END PROCESSING ===

    processed_valid[start:end] = True

def save_processed_wav(filepath='processed.wav'):
    from scipy.io import wavfile

    if processed_buffer is None:
        return False

    ref = audio_sources['ref']
    audio_int16 = (processed_buffer * 32767).astype(np.int16)
    wavfile.write(filepath, ref.sample_rate, audio_int16)
    log('processor', f'Saved to {filepath}')
    return True
```

### playback.py modifications

```python
# add import at top
import processor

# modify switch_source to accept 'processed'
def switch_source(new_source):
    if new_source not in ['ref', 'room', 'processed']:
        return
    # ... rest unchanged ...

# in audio_callback, before reading audio:
# ensure processed chunk is ready when playing processed source
if state.source == 'processed':
    processor.process_chunk(start, end)
```

### main.py modifications

```python
# add import
import processor

# after load_audio_files(), add:
processor.init_processor()
```

### meters.py modifications

```python
# in metering_loop, compute processed measurements too:
ref_chunk = get_chunk_at_position(audio_sources['ref'].data, pos, CHUNK_SIZE)
room_chunk = get_chunk_at_position(audio_sources['room'].data, pos, CHUNK_SIZE)

# ensure processed data exists at this position
processor.process_chunk(pos - CHUNK_SIZE//2, pos + CHUNK_SIZE//2)
processed_chunk = get_chunk_at_position(audio_sources['processed'].data, pos, CHUNK_SIZE)

# compute and store for all three sources
ref_data = module.measure(ref_chunk, sample_rate)
room_data = module.measure(room_chunk, sample_rate)
processed_data = module.measure(processed_chunk, sample_rate)

store_meter_data(name, meter_time, ref_data, room_data, processed_data)
```

## frontend (HTML)

### index.html modifications

```html
<!-- add processed button after room -->
<div id="source-selector">
    <button id="source-ref">ref</button>
    <button id="source-room">room</button>
    <button id="source-processed">processed</button>
</div>

<!-- add processed to compare dropdown -->
<select id="compare-source">
    <option value="">None</option>
    <option value="ref">ref</option>
    <option value="room">room</option>
    <option value="processed">processed</option>
</select>
```

## frontend (JavaScript)

### app.js modifications

```javascript
// add processed button element
const sourceProcessedBtn = document.getElementById('source-processed');

// add click handler
sourceProcessedBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'source', name: 'processed' }));
    log('ui', 'Source: processed');
});

// update UI to highlight processed button
function updateUI() {
    // ... existing code ...
    sourceProcessedBtn.classList.toggle('active', appState.source === 'processed');
}

// update meterHistory to include processed
let meterHistory = { ref: {}, room: {}, processed: {} };
```
