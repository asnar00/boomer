# logging code

## dependencies

### backend (Python)

No additional dependencies - uses standard library.

### frontend

No dependencies - vanilla JS.

---

## backend (Python)

### logger.py

```python
from datetime import datetime
from pathlib import Path

LOG_DIR = Path('logs')
LOG_FILE = LOG_DIR / 'session.log'

def init_logging():
    LOG_DIR.mkdir(exist_ok=True)
    # clear log file on startup
    LOG_FILE.write_text('')
    log('system', 'Logging initialized')

def log(category: str, message: str, source: str = 'backend'):
    timestamp = datetime.now().strftime('%H:%M:%S.') + f'{datetime.now().microsecond // 1000:03d}'
    line = f'[{timestamp}] [{source}] [{category}] {message}'

    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')
```

### main.py modifications

```python
# add import
from logger import init_logging, log

# in websocket handler, add log message handling
@sock.route('/ws')
def websocket(ws):
    log('ws', 'Client connected')

    # ... existing audio_loaded message ...

    while True:
        message = ws.receive()
        if message is None:
            break

        data = json.loads(message)

        if data['type'] == 'log':
            log(data['category'], data['message'], source='frontend')

        # ... handle other message types ...

    log('ws', 'Client disconnected')

# at startup
if __name__ == '__main__':
    init_logging()
    load_audio_files()
    log('audio', f"Loaded ref.wav: {audio_sources['ref'].duration:.1f}s")
    log('audio', f"Loaded room.wav: {audio_sources['room'].duration:.1f}s")
    app.run(debug=True, port=5000)
```

## frontend (JavaScript)

### app.js modifications

```javascript
// testbed/logging

function log(category, message) {
    console.log(`[${category}] ${message}`);

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'log', category, message }));
    }
}

// update existing code to use log()
ws.onopen = () => {
    log('ws', 'Connected to backend');
    status.textContent = 'Connected, waiting for audio info...';
};

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    log('ws', `Received: ${msg.type}`);
    // ... rest of handler ...
};

ws.onclose = () => {
    log('ws', 'Disconnected');
    // ... rest of handler ...
};
```
