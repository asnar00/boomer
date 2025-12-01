# zoom code

## frontend (HTML)

### index.html additions

```html
<div id="zoom-controls">
    <button id="zoom-out">-</button>
    <button id="zoom-reset">Reset</button>
    <button id="zoom-in">+</button>
</div>
```

## frontend (JavaScript)

### app.js additions

```javascript
// testbed/metering/history/zoom - view state (persisted)
let viewStart = parseFloat(localStorage.getItem('viewStart')) || 0;
let viewEnd = parseFloat(localStorage.getItem('viewEnd')) || 300;
const MIN_VISIBLE_BUCKETS = 64;

function saveViewState() {
    localStorage.setItem('viewStart', viewStart);
    localStorage.setItem('viewEnd', viewEnd);
}

// gesture state for zoom/pan
let dragState = null;

// UI elements
const zoomInBtn = document.getElementById('zoom-in');
const zoomOutBtn = document.getElementById('zoom-out');
const zoomResetBtn = document.getElementById('zoom-reset');

function initZoomControls() {
    // set initial view to full track
    viewEnd = appState.duration || 300;

    // button controls
    zoomInBtn.addEventListener('click', () => zoomBy(0.5));
    zoomOutBtn.addEventListener('click', () => zoomBy(2));
    zoomResetBtn.addEventListener('click', resetZoom);

    // drag to pan (touch and mouse)
    meterCanvas.addEventListener('touchstart', handleTouchStart, { passive: false });
    meterCanvas.addEventListener('touchmove', handleTouchMove, { passive: false });
    meterCanvas.addEventListener('touchend', handleTouchEnd);
    meterCanvas.addEventListener('mousedown', handleMouseDown);
    meterCanvas.addEventListener('mousemove', handleMouseMove);
    meterCanvas.addEventListener('mouseup', handleMouseUp);
    meterCanvas.addEventListener('mouseleave', handleMouseUp);
}

function zoomBy(factor) {
    const currentDuration = viewEnd - viewStart;
    const playPos = appState.position;

    // calculate where play cursor is on screen (0-1)
    const playRatio = (playPos - viewStart) / currentDuration;

    let newDuration = currentDuration * factor;

    // clamp zoom
    const minDuration = MIN_VISIBLE_BUCKETS * TIME_BUCKET_SIZE;
    const maxDuration = appState.duration;
    newDuration = Math.max(minDuration, Math.min(maxDuration, newDuration));

    // zoom centered on play cursor, keeping it at same screen position
    viewStart = playPos - playRatio * newDuration;
    viewEnd = viewStart + newDuration;

    // clamp to bounds
    if (viewStart < 0) {
        viewStart = 0;
        viewEnd = newDuration;
    }
    if (viewEnd > appState.duration) {
        viewEnd = appState.duration;
        viewStart = appState.duration - newDuration;
    }

    saveViewState();
    updateMeterDisplay();
}

function handleTouchStart(e) {
    if (e.touches.length === 1) {
        e.preventDefault();
        dragState = {
            startX: e.touches[0].clientX,
            startViewStart: viewStart
        };
    }
}

function handleTouchMove(e) {
    if (e.touches.length === 1 && dragState) {
        e.preventDefault();
        const deltaX = e.touches[0].clientX - dragState.startX;
        const rect = meterCanvas.getBoundingClientRect();
        const padding = { left: 50, right: 20 };
        const plotWidth = meterCanvas.width - padding.left - padding.right;
        const deltaTime = (deltaX / plotWidth) * (viewEnd - viewStart);

        const viewDuration = viewEnd - viewStart;
        let newStart = dragState.startViewStart - deltaTime;
        let newEnd = newStart + viewDuration;

        if (newStart < 0) {
            newStart = 0;
            newEnd = viewDuration;
        }
        if (newEnd > appState.duration) {
            newEnd = appState.duration;
            newStart = appState.duration - viewDuration;
        }

        viewStart = newStart;
        viewEnd = newEnd;
        updateMeterDisplay();
    }
}

function handleTouchEnd(e) {
    if (dragState) saveViewState();
    dragState = null;
}

function handleMouseDown(e) {
    dragState = {
        startX: e.clientX,
        startViewStart: viewStart
    };
}

function handleMouseMove(e) {
    if (!dragState) return;

    const deltaX = e.clientX - dragState.startX;
    const rect = meterCanvas.getBoundingClientRect();
    const padding = { left: 50, right: 20 };
    const plotWidth = meterCanvas.width - padding.left - padding.right;
    const deltaTime = (deltaX / plotWidth) * (viewEnd - viewStart);

    const viewDuration = viewEnd - viewStart;
    let newStart = dragState.startViewStart - deltaTime;
    let newEnd = newStart + viewDuration;

    if (newStart < 0) {
        newStart = 0;
        newEnd = viewDuration;
    }
    if (newEnd > appState.duration) {
        newEnd = appState.duration;
        newStart = appState.duration - viewDuration;
    }

    viewStart = newStart;
    viewEnd = newEnd;
    updateMeterDisplay();
}

function handleMouseUp() {
    if (dragState) saveViewState();
    dragState = null;
}

function resetZoom() {
    viewStart = 0;
    viewEnd = appState.duration;
    saveViewState();
    updateMeterDisplay();
}

// update viewEnd when duration is known
// (add to audio_loaded handler)
if (msg.type === 'audio_loaded') {
    // ... existing code ...
    viewEnd = msg.ref.duration;
}

// initialize controls
initZoomControls();
```

### updateMeterDisplay auto-scroll

```javascript
function updateMeterDisplay() {
    if (!currentMeter || !meterVisualizers[currentMeter]) return;

    // testbed/metering/history/zoom - auto-scroll when playing
    if (appState.playing && !dragState) {
        const viewDuration = viewEnd - viewStart;
        const playRatio = (appState.position - viewStart) / viewDuration;

        // if play cursor past 75% of view, scroll to keep it at 75%
        if (playRatio > 0.75) {
            const newStart = appState.position - 0.75 * viewDuration;
            viewStart = Math.min(newStart, appState.duration - viewDuration);
            viewEnd = viewStart + viewDuration;
            saveViewState();
        }
    }

    // ... rest of display code ...
}
```

### transport skip handlers with auto-scroll

```javascript
skipBackBtn.addEventListener('click', () => {
    const newPos = Math.max(0, appState.position - 10);
    ws.send(JSON.stringify({ type: 'seek', position: newPos }));
    ensureCursorVisible(newPos);
    log('ui', 'Skip back clicked');
});

skipForwardBtn.addEventListener('click', () => {
    const newPos = Math.min(appState.duration, appState.position + 10);
    ws.send(JSON.stringify({ type: 'seek', position: newPos }));
    ensureCursorVisible(newPos);
    log('ui', 'Skip forward clicked');
});

// testbed/metering/history/zoom - scroll to keep cursor visible after seek
function ensureCursorVisible(pos) {
    const viewDuration = viewEnd - viewStart;
    const posRatio = (pos - viewStart) / viewDuration;

    // if cursor outside 25%-75% range, scroll to center it at 50%
    if (posRatio < 0.25 || posRatio > 0.75) {
        viewStart = pos - 0.5 * viewDuration;
        viewEnd = viewStart + viewDuration;

        // clamp to bounds
        if (viewStart < 0) {
            viewStart = 0;
            viewEnd = viewDuration;
        }
        if (viewEnd > appState.duration) {
            viewEnd = appState.duration;
            viewStart = appState.duration - viewDuration;
        }

        saveViewState();
        updateMeterDisplay();
    }
}
```
