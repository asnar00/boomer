# metering code

## dependencies

### backend (Python)

No additional dependencies for framework (individual measurements may add their own).

### frontend

No dependencies - vanilla JS with canvas for visualization.

---

## backend (Python)

### meters.py - metering framework

```python
# testbed/metering

import threading
import time
import json
import numpy as np
from audio import audio_sources
from state import state, connected_clients
import playback  # import module, not value (important for live updates)
from logger import log

# measurement registry
measurements = {}

# active subscriptions per client (ws -> set of measurement names)
client_subscriptions = {}

CHUNK_SIZE = 8192  # samples for measurement (gives ~5.4Hz resolution at 44.1kHz)
METER_RATE = 20    # Hz

def register_measurement(name, module):
    """Register a measurement module with the framework"""
    measurements[name] = module
    log('meter', f'Registered measurement: {name}')

def get_chunk_at_position(audio_data, position, chunk_size):
    """Extract a chunk of audio centered on position"""
    start = max(0, position - chunk_size // 2)
    end = min(len(audio_data), start + chunk_size)
    chunk = audio_data[start:end]

    # ensure we have enough samples (pad with zeros if needed)
    if len(chunk) < chunk_size:
        if audio_data.ndim == 1:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
        else:
            chunk = np.pad(chunk, ((0, chunk_size - len(chunk)), (0, 0)))

    return chunk

def metering_loop():
    """Background thread that computes and broadcasts measurements"""
    while True:
        if state.playing and client_subscriptions:
            sample_rate = audio_sources['ref'].sample_rate

            with playback.playback_lock:
                pos = playback.playback_position  # access via module, not imported value

            # get chunks from both sources at same position
            ref_chunk = get_chunk_at_position(audio_sources['ref'].data, pos, CHUNK_SIZE)
            room_chunk = get_chunk_at_position(audio_sources['room'].data, pos, CHUNK_SIZE)

            # compute measurements for subscribed clients
            for ws, subscribed in list(client_subscriptions.items()):
                for name in subscribed:
                    if name in measurements:
                        module = measurements[name]
                        try:
                            ref_data = module.measure(ref_chunk, sample_rate)
                            room_data = module.measure(room_chunk, sample_rate)
                            diff = module.compare(ref_data, room_data)

                            message = json.dumps({
                                'type': 'meter',
                                'name': name,
                                'ref': ref_data,
                                'room': room_data,
                                'diff': diff
                            })
                            ws.send(message)
                        except Exception as e:
                            log('meter', f'Error computing {name}: {e}')

        time.sleep(1.0 / METER_RATE)

def start_metering_thread():
    thread = threading.Thread(target=metering_loop, daemon=True)
    thread.start()

def subscribe(ws, name):
    if ws not in client_subscriptions:
        client_subscriptions[ws] = set()
    client_subscriptions[ws].add(name)
    log('meter', f'Subscribed to: {name}')

def unsubscribe(ws, name):
    if ws in client_subscriptions:
        client_subscriptions[ws].discard(name)
        log('meter', f'Unsubscribed from: {name}')

def client_disconnected(ws):
    if ws in client_subscriptions:
        del client_subscriptions[ws]
```

### measurements/spectrum.py - spectrum analyzer

```python
# testbed/metering/spectrum

import numpy as np

NUM_BANDS = 32
MIN_FREQ = 20
MAX_FREQ = 20000

def measure(audio_chunk, sample_rate):
    """Compute logarithmic frequency band magnitudes"""
    # convert stereo to mono
    if audio_chunk.ndim > 1:
        audio_chunk = audio_chunk.mean(axis=1)

    # apply Hann window
    window = np.hanning(len(audio_chunk))
    windowed = audio_chunk * window

    # compute FFT
    fft = np.fft.rfft(windowed)
    magnitudes = np.abs(fft)

    # frequency bins
    freqs = np.fft.rfftfreq(len(audio_chunk), 1/sample_rate)

    # create logarithmic band edges
    band_edges = np.logspace(np.log10(MIN_FREQ), np.log10(MAX_FREQ), NUM_BANDS + 1)

    # compute energy in each band
    bands = []
    for i in range(NUM_BANDS):
        low = band_edges[i]
        high = band_edges[i + 1]
        mask = (freqs >= low) & (freqs < high)
        if mask.any():
            band_energy = magnitudes[mask].mean()
        else:
            band_energy = 1e-10  # no data in this band
        bands.append(band_energy)

    # convert to dB
    bands = np.array(bands)
    bands_db = 20 * np.log10(bands + 1e-10)

    # normalize to reasonable range (clip to -80 to 0 dB)
    bands_db = np.clip(bands_db, -80, 0)

    return bands_db.tolist()

def compare(ref_bands, room_bands):
    """Compute mean absolute difference between spectra"""
    ref = np.array(ref_bands)
    room = np.array(room_bands)
    return float(np.mean(np.abs(ref - room)))
```

### main.py modifications

```python
from meters import start_metering_thread, subscribe, unsubscribe, client_disconnected, register_measurement
from measurements import spectrum

# register measurements at startup
register_measurement('spectrum', spectrum)

# in websocket handler
@sock.route('/ws')
def websocket(ws):
    # ... existing connection code ...

    while True:
        message = ws.receive()
        if message is None:
            break

        data = json.loads(message)

        # ... existing handlers ...

        # testbed/metering
        if data['type'] == 'meter_subscribe':
            subscribe(ws, data['name'])
        if data['type'] == 'meter_unsubscribe':
            unsubscribe(ws, data['name'])

    # on disconnect
    client_disconnected(ws)
    connected_clients.remove(ws)
    log('ws', 'Client disconnected')

# at startup
if __name__ == '__main__':
    # ... existing startup ...
    start_metering_thread()
    app.run(debug=True, port=5000, threaded=True)
```

## frontend (JavaScript)

### index.html additions

```html
<!-- testbed/metering -->
<div id="meter-tabs">
    <!-- tabs populated by JS -->
</div>
<div id="meter-views">
    <span id="playing-source">Playing: ref</span>
    <span style="margin-left: 20px;">Compare to:</span>
    <select id="compare-source">
        <option value="">none</option>
        <option value="ref">ref</option>
        <option value="room">room</option>
        <option value="processed">processed</option>
    </select>
</div>
<div id="meter-display">
    <canvas id="meter-canvas" width="800" height="300"></canvas>
    <div id="meter-diff">Difference: --</div>
</div>
```

### CSS additions

```css
#meter-tabs { margin: 20px 0; }
#meter-tabs button { margin-right: 5px; padding: 8px 16px; }
#meter-tabs button.active { background: #333; color: white; }
#meter-views { margin: 10px 0; display: flex; align-items: center; gap: 10px; }
#meter-views select { padding: 6px; font-size: 14px; }
#meter-display { margin: 20px 0; }
#meter-canvas { border: 1px solid #ccc; }
#meter-diff { margin-top: 10px; font-size: 16px; }
```

### app.js additions

```javascript
// testbed/metering

const meterTabs = document.getElementById('meter-tabs');
const meterCanvas = document.getElementById('meter-canvas');
const meterDiff = document.getElementById('meter-diff');
const ctx = meterCanvas.getContext('2d');

// view mode controls
const playingSourceDisplay = document.getElementById('playing-source');
const compareSourceSelect = document.getElementById('compare-source');

const availableMeters = ['spectrum'];  // add more as implemented
let currentMeter = null;

// meter visualizers (each measurement adds its own)
const meterVisualizers = {};

// latest meter data for each source
let meterData = { ref: null, room: null, processed: null };

function initMeterTabs() {
    availableMeters.forEach(name => {
        const btn = document.createElement('button');
        btn.textContent = name;
        btn.id = `meter-tab-${name}`;
        btn.addEventListener('click', () => selectMeter(name));
        meterTabs.appendChild(btn);
    });
}

function selectMeter(name) {
    // unsubscribe from previous
    if (currentMeter) {
        ws.send(JSON.stringify({ type: 'meter_unsubscribe', name: currentMeter }));
        document.getElementById(`meter-tab-${currentMeter}`).classList.remove('active');
    }

    // subscribe to new
    currentMeter = name;
    localStorage.setItem('currentMeter', name);
    ws.send(JSON.stringify({ type: 'meter_subscribe', name }));
    document.getElementById(`meter-tab-${name}`).classList.add('active');
    log('ui', `Selected meter: ${name}`);

    // clear display and data
    ctx.clearRect(0, 0, meterCanvas.width, meterCanvas.height);
    meterDiff.textContent = 'Difference: --';
    meterData = { ref: null, room: null, processed: null };
}

function updateMeterDisplay() {
    if (!currentMeter || !meterVisualizers[currentMeter]) return;

    // always show the currently playing source
    const playingSource = appState.source;
    const playingData = meterData[playingSource];

    // update the display label
    playingSourceDisplay.textContent = `Playing: ${playingSource}`;

    // optionally compare to another source
    const compareSource = compareSourceSelect.value;
    const compareData = compareSource ? meterData[compareSource] : null;

    if (playingData) {
        meterVisualizers[currentMeter](ctx, meterCanvas, playingData, compareData, playingSource, compareSource);

        if (compareData) {
            // compute diff
            const diff = computeDiff(playingData, compareData);
            meterDiff.textContent = `Difference (${playingSource} vs ${compareSource}): ${diff.toFixed(2)} dB`;
        } else {
            meterDiff.textContent = '';
        }
    }
}

function computeDiff(dataA, dataB) {
    let sum = 0;
    for (let i = 0; i < dataA.length; i++) {
        sum += Math.abs(dataA[i] - dataB[i]);
    }
    return sum / dataA.length;
}

// compare source event handler
compareSourceSelect.addEventListener('change', updateMeterDisplay);

// handle meter messages (add to ws.onmessage handler)
if (msg.type === 'meter') {
    if (msg.name === currentMeter) {
        // store data for each source
        meterData.ref = msg.ref;
        meterData.room = msg.room;
        // processed will be null until we have processing
        updateMeterDisplay();
    }
}

// restore meter on connect (add to ws.onopen handler)
const savedMeter = localStorage.getItem('currentMeter');
if (savedMeter && availableMeters.includes(savedMeter)) {
    selectMeter(savedMeter);
}

// initialize tabs on load
initMeterTabs();
```

### spectrum visualizer (bar graph)

```javascript
// testbed/metering/spectrum - visualizer (bar graph)
meterVisualizers['spectrum'] = function(ctx, canvas, bandsA, bandsB, labelA, labelB) {
    const width = canvas.width;
    const height = canvas.height;
    const padding = { left: 50, right: 20, top: 20, bottom: 30 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;

    // clear
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, width, height);

    // dB range
    const minDb = -80;
    const maxDb = 0;

    const numBands = bandsA ? bandsA.length : (bandsB ? bandsB.length : 32);
    const barWidth = plotWidth / numBands;
    const gap = 2;
    const halfBar = bandsB ? (barWidth - gap) / 2 : barWidth - gap;

    function dbToHeight(db) {
        return plotHeight * (db - minDb) / (maxDb - minDb);
    }

    // draw grid
    ctx.strokeStyle = '#eee';
    ctx.lineWidth = 1;
    for (let db = minDb; db <= maxDb; db += 20) {
        const y = padding.top + plotHeight * (1 - (db - minDb) / (maxDb - minDb));
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();

        ctx.fillStyle = '#666';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`${db}dB`, padding.left - 5, y + 3);
    }

    const baseline = height - padding.bottom;

    // draw bars for first spectrum (blue)
    if (bandsA) {
        ctx.fillStyle = 'rgba(50, 100, 200, 0.8)';
        for (let i = 0; i < bandsA.length; i++) {
            const x = padding.left + i * barWidth;
            const h = dbToHeight(bandsA[i]);
            ctx.fillRect(x, baseline - h, halfBar, h);
        }
    }

    // draw bars for second spectrum (orange) if comparing
    if (bandsB) {
        ctx.fillStyle = 'rgba(200, 100, 50, 0.8)';
        for (let i = 0; i < bandsB.length; i++) {
            const x = padding.left + i * barWidth + halfBar;
            const h = dbToHeight(bandsB[i]);
            ctx.fillRect(x, baseline - h, halfBar, h);
        }
    }

    // frequency labels for each band
    ctx.fillStyle = '#666';
    ctx.font = '9px monospace';
    ctx.textAlign = 'center';

    // logarithmic frequency bands (matching backend: 20Hz to 20kHz, 32 bands)
    const minFreq = 20;
    const maxFreq = 20000;
    for (let i = 0; i < numBands; i++) {
        const freq = minFreq * Math.pow(maxFreq / minFreq, i / (numBands - 1));
        const x = padding.left + i * barWidth + barWidth / 2;

        // format frequency label
        let label;
        if (freq >= 1000) {
            label = (freq / 1000).toFixed(freq >= 10000 ? 0 : 1) + 'k';
        } else {
            label = Math.round(freq).toString();
        }

        // only show every few labels to avoid crowding
        if (i % 4 === 0 || i === numBands - 1) {
            ctx.fillText(label, x, height - 10);
        }
    }

    // legend
    if (bandsB && labelA && labelB) {
        ctx.fillStyle = 'rgba(50, 100, 200, 0.8)';
        ctx.fillRect(width - 100, 10, 15, 15);
        ctx.fillStyle = '#333';
        ctx.textAlign = 'left';
        ctx.fillText(labelA, width - 80, 22);

        ctx.fillStyle = 'rgba(200, 100, 50, 0.8)';
        ctx.fillRect(width - 100, 30, 15, 15);
        ctx.fillStyle = '#333';
        ctx.fillText(labelB, width - 80, 42);
    }
};
```
