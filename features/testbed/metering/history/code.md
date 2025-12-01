# history code

## backend (Python)

### meters.py modifications

```python
# add time to meter message
message = json.dumps({
    'type': 'meter',
    'name': name,
    'time': pos / sample_rate,  # time in seconds
    'ref': ref_data,
    'room': room_data,
    'diff': diff
})
```

### spectrum.py - normalize FFT

```python
# compute FFT and normalize by chunk size
fft = np.fft.rfft(windowed)
magnitudes = np.abs(fft) / len(audio_chunk)
```

## frontend (JavaScript)

### app.js modifications

```javascript
// testbed/metering/history

// replace meterData with history storage
// meterHistory[source][timeBucket] = measurement_data
let meterHistory = { ref: {}, room: {}, processed: {} };

const TIME_BUCKET_SIZE = 0.1;  // 100ms buckets

function timeBucket(time) {
    return Math.floor(time / TIME_BUCKET_SIZE) * TIME_BUCKET_SIZE;
}

function storeMeterData(source, time, data) {
    const bucket = timeBucket(time);
    meterHistory[source][bucket] = data;
}

// update meter message handler
if (msg.type === 'meter') {
    if (msg.name === currentMeter) {
        storeMeterData('ref', msg.time, msg.ref);
        storeMeterData('room', msg.time, msg.room);
        updateMeterDisplay();
    }
}

// update selectMeter to clear history
function selectMeter(name) {
    // ... existing unsubscribe code ...

    // clear history instead of meterData
    meterHistory = { ref: {}, room: {}, processed: {} };

    // ... rest of function ...
}

// update updateMeterDisplay to pass history
function updateMeterDisplay() {
    if (!currentMeter || !meterVisualizers[currentMeter]) return;

    const playingSource = appState.source;
    const compareSource = compareSourceSelect.value;

    playingSourceDisplay.textContent = `Playing: ${playingSource}`;

    meterVisualizers[currentMeter](
        ctx, meterCanvas,
        meterHistory[playingSource],
        compareSource ? meterHistory[compareSource] : null,
        playingSource, compareSource,
        appState.position, appState.duration
    );

    meterDiff.textContent = '';
}
```

### spectrum visualizer (spectrogram)

```javascript
// testbed/metering/history - spectrum as spectrogram
meterVisualizers['spectrum'] = function(ctx, canvas, historyA, historyB, labelA, labelB, currentTime, duration) {
    const width = canvas.width;
    const height = canvas.height;
    const padding = { left: 50, right: 20, top: 20, bottom: 30 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;

    // clear
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, width, height);

    // dB range for color mapping
    const minDb = -80;
    const maxDb = 0;

    function dbToColor(db) {
        const t = Math.max(0, Math.min(1, (db - minDb) / (maxDb - minDb)));
        // blue (cold/quiet) -> red (hot/loud)
        const r = Math.floor(255 * t);
        const g = Math.floor(255 * Math.sin(t * Math.PI) * 0.5);
        const b = Math.floor(255 * (1 - t));
        return `rgb(${r}, ${g}, ${b})`;
    }

    function drawSpectrogram(history, yOffset, plotH) {
        const times = Object.keys(history).map(Number).sort((a, b) => a - b);
        if (times.length === 0) return;

        const numBands = history[times[0]].length;
        const bandHeight = plotH / numBands;

        for (const time of times) {
            if (time < viewStart || time > viewEnd) continue;

            const x = padding.left + ((time - viewStart) / (viewEnd - viewStart)) * plotWidth;
            const bucketWidth = Math.max((TIME_BUCKET_SIZE / (viewEnd - viewStart)) * plotWidth, 1);
            const bands = history[time];

            for (let i = 0; i < bands.length; i++) {
                const y = yOffset + plotH - (i + 1) * bandHeight;
                ctx.fillStyle = dbToColor(bands[i]);
                ctx.fillRect(x, y, bucketWidth + 0.5, bandHeight + 0.5);
            }
        }
    }

    // draw spectrogram(s)
    if (historyB && Object.keys(historyB).length > 0) {
        // split view: A on top, B on bottom
        const halfHeight = plotHeight / 2;
        drawSpectrogram(historyA, padding.top, halfHeight - 2);
        drawSpectrogram(historyB, padding.top + halfHeight + 2, halfHeight - 2);

        // labels
        ctx.fillStyle = '#fff';
        ctx.font = '10px monospace';
        ctx.fillText(labelA, padding.left + 5, padding.top + 15);
        ctx.fillText(labelB, padding.left + 5, padding.top + halfHeight + 17);
    } else {
        drawSpectrogram(historyA, padding.top, plotHeight);
    }

    // draw playback position line
    if (currentTime >= viewStart && currentTime <= viewEnd) {
        const x = padding.left + ((currentTime - viewStart) / (viewEnd - viewStart)) * plotWidth;
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x, padding.top);
        ctx.lineTo(x, height - padding.bottom);
        ctx.stroke();
    }

    // time axis
    ctx.fillStyle = '#999';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    const viewDuration = viewEnd - viewStart;
    const timeStep = Math.pow(10, Math.floor(Math.log10(viewDuration / 5)));
    for (let t = Math.ceil(viewStart / timeStep) * timeStep; t <= viewEnd; t += timeStep) {
        const x = padding.left + ((t - viewStart) / viewDuration) * plotWidth;
        ctx.fillText(formatTime(t), x, height - 10);
    }

    // frequency axis (20Hz to 20kHz)
    ctx.textAlign = 'right';
    const freqLabels = [20, 100, 1000, 10000, 20000];
    const numBands = 32;
    for (const freq of freqLabels) {
        const bandIndex = Math.log(freq / 20) / Math.log(20000 / 20) * (numBands - 1);
        const y = padding.top + plotHeight - (bandIndex / numBands) * plotHeight;
        const label = freq >= 1000 ? `${freq/1000}k` : `${freq}`;
        ctx.fillText(label, padding.left - 5, y + 3);
    }
};
```
