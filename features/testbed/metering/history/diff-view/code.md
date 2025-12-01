# diff-view code

## frontend (HTML)

### index.html additions

```html
<div id="diff-controls">
    <label>
        <input type="checkbox" id="diff-view-toggle"> Diff View
    </label>
    <label>
        Tolerance: <input type="range" id="diff-tolerance" min="1" max="10" value="3">
        <span id="diff-tolerance-value">3</span>dB
    </label>
</div>
```

## frontend (JavaScript)

### app.js additions

```javascript
// testbed/metering/history/diff-view - state
let diffViewEnabled = false;
let diffTolerance = 3;

// UI elements
const diffViewToggle = document.getElementById('diff-view-toggle');
const diffToleranceSlider = document.getElementById('diff-tolerance');
const diffToleranceValue = document.getElementById('diff-tolerance-value');

// testbed/metering/history/diff-view - color function
function diffToColor(diff, tolerance) {
    const absDiff = Math.abs(diff);

    if (absDiff < tolerance) {
        // Green zone - matched within tolerance
        // Brighter green as diff approaches zero
        const t = 1 - (absDiff / tolerance);
        const intensity = Math.floor(100 + 155 * t);
        return `rgb(0, ${intensity}, 0)`;
    } else if (diff > 0) {
        // Red zone - room louder than processed (need more gain)
        const t = Math.min(1, (absDiff - tolerance) / 20);
        const intensity = Math.floor(100 + 155 * t);
        return `rgb(${intensity}, 0, 0)`;
    } else {
        // Blue zone - processed louder than room (need less gain)
        const t = Math.min(1, (absDiff - tolerance) / 20);
        const intensity = Math.floor(100 + 155 * t);
        return `rgb(0, 0, ${intensity})`;
    }
}

function drawDiffSpectrogram(roomHistory, processedHistory, yOffset, plotH) {
    const times = Object.keys(roomHistory).map(Number).sort((a, b) => a - b);
    if (times.length === 0) return;

    const numBands = roomHistory[times[0]].length;
    const bandHeight = plotH / numBands;

    for (const time of times) {
        if (time < viewStart || time > viewEnd) continue;
        if (!processedHistory[time]) continue;

        const x = padding.left + ((time - viewStart) / (viewEnd - viewStart)) * plotWidth;
        const bucketWidth = Math.max((TIME_BUCKET_SIZE / (viewEnd - viewStart)) * plotWidth, 1);
        const roomBands = roomHistory[time];
        const processedBands = processedHistory[time];

        for (let i = 0; i < numBands; i++) {
            const diff = roomBands[i] - processedBands[i];
            const y = yOffset + plotH - (i + 1) * bandHeight;
            ctx.fillStyle = diffToColor(diff, diffTolerance);
            ctx.fillRect(x, y, bucketWidth + 0.5, bandHeight + 0.5);
        }
    }
}

// event handlers
diffViewToggle.addEventListener('change', (e) => {
    diffViewEnabled = e.target.checked;
    updateMeterDisplay();
});

diffToleranceSlider.addEventListener('input', (e) => {
    diffTolerance = parseInt(e.target.value);
    diffToleranceValue.textContent = diffTolerance;
    updateMeterDisplay();
});
```

### spectrum visualizer modification

```javascript
// In meterVisualizers['spectrum'], add diff view mode:

if (diffViewEnabled && meterHistory['room'] && meterHistory['processed']) {
    // Diff view mode - show room minus processed
    drawDiffSpectrogram(meterHistory['room'], meterHistory['processed'], padding.top, plotHeight);

    // Label
    ctx.fillStyle = '#fff';
    ctx.font = '10px monospace';
    ctx.fillText('Diff: room - processed', padding.left + 5, padding.top + 15);
} else {
    // Normal view mode (existing code)
    // ...
}
```
