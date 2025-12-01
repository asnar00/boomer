# spectrum code

## dependencies

### backend (Python)

```bash
# numpy already installed, scipy already installed
```

### frontend

No dependencies - uses canvas.

---

## backend (Python)

### meters/spectrum.py

```python
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
            band_energy = 1e-10  # avoid log(0)
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

### meters/__init__.py

```python
from . import spectrum

def register_all(register_fn):
    register_fn('spectrum', spectrum)
```

### main.py modifications

```python
from meters import register_all
from meters import spectrum  # and other measurements

# at startup, after imports
from meters import register_all
import meters as meter_modules

# in main block
if __name__ == '__main__':
    init_logging()
    load_audio_files()
    # ... existing setup ...

    # register measurements
    from meters import register_all
    register_all(register_measurement)

    start_metering_thread()
    # ... rest of startup ...
```

## frontend (JavaScript)

### app.js additions

```javascript
// testbed/metering/spectrum - visualizer

meterVisualizers['spectrum'] = function(ctx, canvas, refBands, roomBands) {
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

    function dbToY(db) {
        return padding.top + plotHeight * (1 - (db - minDb) / (maxDb - minDb));
    }

    function bandToX(i) {
        return padding.left + (i / (refBands.length - 1)) * plotWidth;
    }

    // draw grid
    ctx.strokeStyle = '#eee';
    ctx.lineWidth = 1;
    for (let db = minDb; db <= maxDb; db += 20) {
        const y = dbToY(db);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();

        ctx.fillStyle = '#666';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`${db}dB`, padding.left - 5, y + 3);
    }

    // draw ref spectrum (blue)
    ctx.strokeStyle = 'rgba(50, 100, 200, 0.8)';
    ctx.fillStyle = 'rgba(50, 100, 200, 0.3)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(bandToX(0), dbToY(refBands[0]));
    for (let i = 1; i < refBands.length; i++) {
        ctx.lineTo(bandToX(i), dbToY(refBands[i]));
    }
    ctx.stroke();

    // fill under ref
    ctx.lineTo(bandToX(refBands.length - 1), height - padding.bottom);
    ctx.lineTo(bandToX(0), height - padding.bottom);
    ctx.closePath();
    ctx.fill();

    // draw room spectrum (orange)
    ctx.strokeStyle = 'rgba(200, 100, 50, 0.8)';
    ctx.fillStyle = 'rgba(200, 100, 50, 0.3)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(bandToX(0), dbToY(roomBands[0]));
    for (let i = 1; i < roomBands.length; i++) {
        ctx.lineTo(bandToX(i), dbToY(roomBands[i]));
    }
    ctx.stroke();

    // labels
    ctx.fillStyle = '#333';
    ctx.font = '12px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('20Hz', padding.left, height - 10);
    ctx.fillText('20kHz', width - padding.right, height - 10);

    // legend
    ctx.fillStyle = 'rgba(50, 100, 200, 0.8)';
    ctx.fillRect(width - 100, 10, 15, 15);
    ctx.fillStyle = '#333';
    ctx.textAlign = 'left';
    ctx.fillText('ref', width - 80, 22);

    ctx.fillStyle = 'rgba(200, 100, 50, 0.8)';
    ctx.fillRect(width - 100, 30, 15, 15);
    ctx.fillStyle = '#333';
    ctx.fillText('room', width - 80, 42);
};
```
