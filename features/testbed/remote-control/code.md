# remote-control code

## dependencies

### backend (Python)

No additional dependencies.

### frontend

No dependencies - vanilla JS.

---

## backend (Python)

### state.py

```python
from dataclasses import dataclass, asdict
from typing import List
import json

@dataclass
class AppState:
    playing: bool = False
    position: float = 0.0
    source: str = 'ref'
    duration: float = 0.0

state = AppState()
connected_clients: List = []

def get_state_dict():
    return {'type': 'state', **asdict(state)}

def broadcast_state():
    message = json.dumps(get_state_dict())
    for ws in connected_clients:
        try:
            ws.send(message)
        except:
            pass  # client may have disconnected
```

### main.py modifications

```python
from flask import request, jsonify
from state import state, connected_clients, get_state_dict, broadcast_state

# track connected clients
@sock.route('/ws')
def websocket(ws):
    connected_clients.append(ws)
    log('ws', 'Client connected')

    # ... existing code ...

    # on disconnect
    connected_clients.remove(ws)
    log('ws', 'Client disconnected')

# API endpoints
@app.route('/api/status')
def api_status():
    return jsonify(get_state_dict())

@app.route('/api/transport/play', methods=['POST'])
def api_play():
    state.playing = True
    log('transport', 'Play (via API)')
    broadcast_state()
    return jsonify(get_state_dict())

@app.route('/api/transport/pause', methods=['POST'])
def api_pause():
    state.playing = False
    log('transport', 'Pause (via API)')
    broadcast_state()
    return jsonify(get_state_dict())

@app.route('/api/transport/seek', methods=['POST'])
def api_seek():
    position = float(request.args.get('position', 0))
    state.position = max(0, min(position, state.duration))
    log('transport', f'Seek to {state.position:.1f}s (via API)')
    broadcast_state()
    return jsonify(get_state_dict())

@app.route('/api/source', methods=['POST'])
def api_source():
    name = request.args.get('name', 'ref')
    if name in ['ref', 'room']:
        state.source = name
        log('transport', f'Source: {name} (via API)')
    broadcast_state()
    return jsonify(get_state_dict())

# client control endpoints
@app.route('/api/client/click', methods=['POST'])
def api_client_click():
    element = request.args.get('element', '')
    message = json.dumps({'type': 'remote_click', 'element': element})
    log('remote', f'Click: {element}')
    for ws in connected_clients:
        try:
            ws.send(message)
        except:
            pass
    return jsonify(get_state_dict())

@app.route('/api/client/eval', methods=['POST'])
def api_client_eval():
    code = request.args.get('js', '')
    message = json.dumps({'type': 'remote_eval', 'code': code})
    log('remote', f'Eval: {code[:50]}...' if len(code) > 50 else f'Eval: {code}')
    for ws in connected_clients:
        try:
            ws.send(message)
        except:
            pass
    return jsonify(get_state_dict())

@app.route('/api/client/refresh', methods=['POST'])
def api_client_refresh():
    message = json.dumps({'type': 'remote_refresh'})
    log('remote', 'Refresh all clients')
    for ws in connected_clients:
        try:
            ws.send(message)
        except:
            pass
    return jsonify({'status': 'ok'})

# set duration after loading audio
if __name__ == '__main__':
    init_logging()
    load_audio_files()
    state.duration = audio_sources['ref'].duration
    # ... rest of startup ...
```

## frontend (JavaScript)

### app.js modifications

```javascript
// testbed/remote-control

// state
let appState = {
    playing: false,
    position: 0,
    source: 'ref',
    duration: 0
};

// handle incoming messages
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    log('ws', `Received: ${msg.type}`);

    if (msg.type === 'audio_loaded') {
        appState.duration = msg.ref.duration;
        status.textContent = `ref: ${msg.ref.duration.toFixed(1)}s, room: ${msg.room.duration.toFixed(1)}s @ ${msg.ref.sample_rate}Hz`;
    }

    if (msg.type === 'state') {
        appState = { ...msg };
        updateUI();
    }

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

function updateUI() {
    // update UI elements to reflect appState
    // (implemented in transport feature)
}
```
