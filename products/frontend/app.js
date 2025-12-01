// testbed/load-audio, testbed/logging, testbed/remote-control, testbed/transport, testbed/source-switch, testbed/metering, testbed/metering/history/diff-view

const status = document.getElementById('status');
let ws;

// testbed/remote-control - state
let appState = {
    playing: false,
    position: 0,
    source: 'ref',
    duration: 0
};

// testbed/transport - UI elements
const playPauseBtn = document.getElementById('play-pause');
const skipBackBtn = document.getElementById('skip-back');
const skipForwardBtn = document.getElementById('skip-forward');
const positionDisplay = document.getElementById('position');

// testbed/source-switch - UI elements
const sourceRefBtn = document.getElementById('source-ref');
const sourceRoomBtn = document.getElementById('source-room');
const sourceProcessedBtn = document.getElementById('source-processed');

// testbed/logging
function log(category, message) {
    console.log(`[${category}] ${message}`);

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'log', category, message }));
    }
}

// testbed/transport - time formatting
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function connect() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = () => {
        log('ws', 'Connected to backend');
        status.textContent = 'Connected, waiting for audio info...';

        // restore persisted meter selection
        const savedMeter = localStorage.getItem('currentMeter');
        log('ws', `Saved meter from localStorage: ${savedMeter}`);
        if (savedMeter && availableMeters.includes(savedMeter)) {
            log('ws', `Restoring meter: ${savedMeter}`);
            selectMeter(savedMeter);
        }
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        // don't log state updates (too noisy at 10Hz)
        if (msg.type !== 'state') {
            log('ws', `Received: ${msg.type}`);
        }

        // testbed/load-audio
        if (msg.type === 'audio_loaded') {
            appState.duration = msg.ref.duration;
            // testbed/metering/history/zoom - only set viewEnd if not already loaded from localStorage
            if (viewEnd === 300 || viewEnd > msg.ref.duration) {
                viewEnd = msg.ref.duration;
            }
            status.textContent = `ref: ${msg.ref.duration.toFixed(1)}s, room: ${msg.room.duration.toFixed(1)}s @ ${msg.ref.sample_rate}Hz`;
            updateUI();
        }

        // testbed/remote-control - state sync
        if (msg.type === 'state') {
            appState = { ...appState, ...msg };
            updateUI();
        }

        // testbed/remote-control - client control
        if (msg.type === 'remote_click') {
            const el = document.querySelector(msg.element);
            if (el) {
                el.click();
                log('remote', `Clicked: ${msg.element}`);
            } else {
                log('remote', `Element not found: ${msg.element}`);
            }
        }

        if (msg.type === 'remote_eval') {
            try {
                const result = eval(msg.code);
                log('remote', `Eval result: ${result}`);
            } catch (e) {
                log('remote', `Eval error: ${e.message}`);
            }
        }

        if (msg.type === 'remote_refresh') {
            log('remote', 'Refreshing page');
            location.reload();
        }

        // testbed/metering/history/persistence - load history from server
        if (msg.type === 'meter_history') {
            if (msg.name === currentMeter) {
                // populate local history from server data
                for (const [time, data] of Object.entries(msg.ref)) {
                    meterHistory['ref'][parseFloat(time)] = data;
                }
                for (const [time, data] of Object.entries(msg.room)) {
                    meterHistory['room'][parseFloat(time)] = data;
                }
                if (msg.processed) {
                    for (const [time, data] of Object.entries(msg.processed)) {
                        meterHistory['processed'][parseFloat(time)] = data;
                    }
                }
                log('meter', `Loaded ${Object.keys(msg.ref).length} history buckets`);
                updateMeterDisplay();
            }
        }

        // testbed/metering/history
        if (msg.type === 'meter') {
            if (msg.name === currentMeter) {
                // store data in time-series history
                storeMeterData('ref', msg.time, msg.ref);
                storeMeterData('room', msg.time, msg.room);
                if (msg.processed) storeMeterData('processed', msg.time, msg.processed);
                updateMeterDisplay();
            }
        }
    };

    ws.onclose = () => {
        log('ws', 'Disconnected');
        status.textContent = 'Disconnected. Reconnecting...';
        setTimeout(connect, 1000);
    };

    ws.onerror = () => {
        log('ws', 'Connection error');
        status.textContent = 'Connection error';
    };
}

// testbed/transport, testbed/source-switch - UI update
function updateUI() {
    playPauseBtn.textContent = appState.playing ? 'Pause' : 'Play';
    positionDisplay.textContent = `${formatTime(appState.position)} / ${formatTime(appState.duration)}`;

    // source button highlights
    sourceRefBtn.classList.toggle('active', appState.source === 'ref');
    sourceRoomBtn.classList.toggle('active', appState.source === 'room');
    sourceProcessedBtn.classList.toggle('active', appState.source === 'processed');

    // update meter display when source changes
    updateMeterDisplay();
}

// testbed/transport - button handlers
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

// testbed/source-switch - button handlers
sourceRefBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'source', name: 'ref' }));
    log('ui', 'Source: ref');
});

sourceRoomBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'source', name: 'room' }));
    log('ui', 'Source: room');
});

sourceProcessedBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'source', name: 'processed' }));
    log('ui', 'Source: processed');
});

// testbed/metering

const meterTabs = document.getElementById('meter-tabs');
const meterCanvas = document.getElementById('meter-canvas');
const meterDiff = document.getElementById('meter-diff');
const ctx = meterCanvas.getContext('2d');

// view mode controls
const playingSourceDisplay = document.getElementById('playing-source');
const compareSourceSelect = document.getElementById('compare-source');

// testbed/metering/history/diff-view - state and UI elements
let diffViewEnabled = true;
let diffTolerance = 1;
const diffViewToggle = document.getElementById('diff-view-toggle');
const diffToleranceSlider = document.getElementById('diff-tolerance');
const diffToleranceValue = document.getElementById('diff-tolerance-value');

const availableMeters = ['spectrum'];  // add more as implemented
let currentMeter = null;

// meter visualizers (each measurement adds its own)
const meterVisualizers = {};

// testbed/metering/history - time-series data storage
let meterHistory = { ref: {}, room: {}, processed: {} };
const TIME_BUCKET_SIZE = 0.1;  // 100ms buckets

// testbed/metering/history/zoom - view state (persisted)
let viewStart = parseFloat(localStorage.getItem('viewStart')) || 0;
let viewEnd = parseFloat(localStorage.getItem('viewEnd')) || 300;
const MIN_VISIBLE_BUCKETS = 64;

function saveViewState() {
    localStorage.setItem('viewStart', viewStart);
    localStorage.setItem('viewEnd', viewEnd);
}

// gesture state for zoom/pan
let pinchState = null;
let dragState = null;
let lastTapTime = 0;

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

    // clear display and history
    ctx.clearRect(0, 0, meterCanvas.width, meterCanvas.height);
    meterDiff.textContent = '';
    meterHistory = { ref: {}, room: {}, processed: {} };
}

// testbed/metering/history - helper functions
function timeBucket(time) {
    return Math.floor(time / TIME_BUCKET_SIZE) * TIME_BUCKET_SIZE;
}

function storeMeterData(source, time, data) {
    const bucket = timeBucket(time);
    meterHistory[source][bucket] = data;
}

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

    const playingSource = appState.source;
    const compareSource = compareSourceSelect.value;

    playingSourceDisplay.textContent = `Playing: ${playingSource}`;

    // testbed/metering/history - pass history data to visualizer
    meterVisualizers[currentMeter](
        ctx, meterCanvas,
        meterHistory[playingSource],
        compareSource ? meterHistory[compareSource] : null,
        playingSource, compareSource,
        appState.position, appState.duration
    );

    meterDiff.textContent = '';
}

// compare source event handler
compareSourceSelect.addEventListener('change', updateMeterDisplay);

// testbed/metering/history - spectrum as spectrogram
meterVisualizers['spectrum'] = function(ctx, canvas, historyA, historyB, labelA, labelB, currentTime, duration) {
    const width = canvas.width;
    const height = canvas.height;
    const errorBarHeight = diffViewEnabled ? 15 : 0;
    const padding = { left: 50, right: 20, top: 20 + errorBarHeight, bottom: 30 };
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
        // black -> blue -> red -> yellow
        // -80 to -50: black to blue (0 to 0.375)
        // -50 to -10: blue to red (0.375 to 0.875)
        // -10 to 0: red to yellow (0.875 to 1.0)
        let r, g, b;
        if (t < 0.375) {
            // black to blue (-80 to -50 dB)
            const s = t / 0.375;
            r = 0;
            g = 0;
            b = Math.floor(255 * s);
        } else if (t < 0.875) {
            // blue to red (-50 to -10 dB)
            const s = (t - 0.375) / 0.5;
            r = Math.floor(255 * s);
            g = 0;
            b = Math.floor(255 * (1 - s));
        } else {
            // red to yellow (-10 to 0 dB)
            const s = (t - 0.875) / 0.125;
            r = 255;
            g = Math.floor(255 * s);
            b = 0;
        }
        return `rgb(${r}, ${g}, ${b})`;
    }

    // testbed/metering/history/diff-view - color function for difference display
    function diffToColor(diff, tolerance) {
        const absDiff = Math.abs(diff);

        if (absDiff < tolerance) {
            // Green zone - matched within tolerance
            // Brighter green as diff approaches zero
            const t = 1 - (absDiff / tolerance);
            const intensity = Math.floor(100 + 155 * t);
            return `rgb(0, ${intensity}, 0)`;
        } else if (diff > 0) {
            // Blue zone - playing source has less energy than comparator
            const t = Math.min(1, (absDiff - tolerance) / 20);
            const intensity = Math.floor(100 + 155 * t);
            return `rgb(0, 0, ${intensity})`;
        } else {
            // Red zone - playing source has more energy than comparator
            const t = Math.min(1, (absDiff - tolerance) / 20);
            const intensity = Math.floor(100 + 155 * t);
            return `rgb(${intensity}, 0, 0)`;
        }
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

    // testbed/metering/history/diff-view - draw diff spectrogram
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

    // testbed/metering/history/diff-view - draw error summary bar at top
    function drawErrorBar(histA, histB) {
        const times = Object.keys(histB).map(Number).sort((a, b) => a - b);
        if (times.length === 0) return;

        for (const time of times) {
            if (time < viewStart || time > viewEnd) continue;
            if (!histA[time]) continue;

            const x = padding.left + ((time - viewStart) / (viewEnd - viewStart)) * plotWidth;
            const bucketWidth = Math.max((TIME_BUCKET_SIZE / (viewEnd - viewStart)) * plotWidth, 1);
            const bandsA = histA[time];
            const bandsB = histB[time];

            // Calculate RMS error across all bands
            let sumSq = 0;
            for (let i = 0; i < bandsA.length; i++) {
                const diff = bandsB[i] - bandsA[i];
                sumSq += diff * diff;
            }
            const rms = Math.sqrt(sumSq / bandsA.length);

            // Use same color logic but with RMS as the "diff"
            // Positive RMS means there's error - use diffToColor with sign based on average
            let sumDiff = 0;
            for (let i = 0; i < bandsA.length; i++) {
                sumDiff += bandsB[i] - bandsA[i];
            }
            const avgDiff = sumDiff / bandsA.length;

            // Color based on RMS magnitude, sign from average diff direction
            const signedError = avgDiff >= 0 ? rms : -rms;
            ctx.fillStyle = diffToColor(signedError, diffTolerance);
            ctx.fillRect(x, 20, bucketWidth + 0.5, errorBarHeight);
        }
    }

    // testbed/metering/history/diff-view - check if diff view mode should be used
    const hasDiffData = historyA && historyB &&
                        Object.keys(historyA).length > 0 &&
                        Object.keys(historyB).length > 0;

    if (diffViewEnabled && hasDiffData) {
        // Diff view mode - show compareSource minus playingSource
        drawDiffSpectrogram(historyB, historyA, padding.top, plotHeight);
        drawErrorBar(historyA, historyB);

        // Label
        ctx.fillStyle = '#fff';
        ctx.font = '10px monospace';
        ctx.fillText(`Diff: ${labelB} - ${labelA}`, padding.left + 5, padding.top + 15);
    } else if (historyB && Object.keys(historyB).length > 0) {
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

// initialize meter tabs
initMeterTabs();

// testbed/metering/history/zoom - zoom and pan controls
const zoomInBtn = document.getElementById('zoom-in');
const zoomOutBtn = document.getElementById('zoom-out');
const zoomResetBtn = document.getElementById('zoom-reset');

function initZoomControls() {
    // testbed/metering/history/zoom - only reset view if not loaded from localStorage
    // (viewStart/viewEnd already loaded from localStorage at declaration time)

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

function xToTime(x) {
    const rect = meterCanvas.getBoundingClientRect();
    const padding = { left: 50, right: 20 };
    const plotWidth = meterCanvas.width - padding.left - padding.right;
    const relX = x - rect.left - padding.left;
    return viewStart + (relX / plotWidth) * (viewEnd - viewStart);
}

function getTouchDistance(touches) {
    const dx = touches[0].clientX - touches[1].clientX;
    const dy = touches[0].clientY - touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
}

function getTouchMidpoint(touches) {
    return (touches[0].clientX + touches[1].clientX) / 2;
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

        // clamp to bounds
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

// mouse fallback
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

// initialize zoom controls
initZoomControls();

// testbed/metering/history/diff-view - event handlers
diffViewToggle.addEventListener('change', (e) => {
    diffViewEnabled = e.target.checked;
    updateMeterDisplay();
});

diffToleranceSlider.addEventListener('input', (e) => {
    diffTolerance = parseInt(e.target.value);
    diffToleranceValue.textContent = diffTolerance;
    updateMeterDisplay();
});

connect();
