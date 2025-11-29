// testbed/load-audio, testbed/logging, testbed/remote-control, testbed/transport, testbed/source-switch

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
    log('ui', 'Skip back clicked');
});

skipForwardBtn.addEventListener('click', () => {
    const newPos = Math.min(appState.duration, appState.position + 10);
    ws.send(JSON.stringify({ type: 'seek', position: newPos }));
    log('ui', 'Skip forward clicked');
});

// testbed/source-switch - button handlers
sourceRefBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'source', name: 'ref' }));
    log('ui', 'Source: ref');
});

sourceRoomBtn.addEventListener('click', () => {
    ws.send(JSON.stringify({ type: 'source', name: 'room' }));
    log('ui', 'Source: room');
});

connect();
