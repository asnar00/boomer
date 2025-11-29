# load-audio code

## dependencies

### backend (Python)

```bash
pip install flask flask-sock scipy numpy
```

### frontend

No dependencies - vanilla JS.

---

## backend (Python)

### audio.py - audio loading and storage

```python
import numpy as np
from scipy.io import wavfile
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AudioData:
    data: np.ndarray      # float32, shape (samples,) or (samples, channels)
    sample_rate: int
    channels: int
    duration: float

# global storage
audio_sources: dict[str, AudioData] = {}

def load_wav(path: str) -> AudioData:
    filepath = Path(path)
    if not filepath.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    sample_rate, data = wavfile.read(filepath)

    # convert to float32 normalized to [-1, 1]
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    elif data.dtype != np.float32:
        raise ValueError(f"Unsupported wav format: {data.dtype}")

    channels = 1 if data.ndim == 1 else data.shape[1]
    duration = len(data) / sample_rate

    return AudioData(data=data, sample_rate=sample_rate, channels=channels, duration=duration)

def load_audio_files():
    audio_sources['ref'] = load_wav('ref.wav')
    audio_sources['room'] = load_wav('room.wav')

    if audio_sources['ref'].sample_rate != audio_sources['room'].sample_rate:
        raise ValueError("Sample rates must match between ref.wav and room.wav")
```

### main.py - server setup (load-audio portion)

```python
from flask import Flask
from flask_sock import Sock
import json
from audio import load_audio_files, audio_sources

app = Flask(__name__, static_folder='../frontend', static_url_path='')
sock = Sock(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@sock.route('/ws')
def websocket(ws):
    # send audio metadata on connect
    metadata = {
        'type': 'audio_loaded',
        'ref': {
            'duration': audio_sources['ref'].duration,
            'sample_rate': audio_sources['ref'].sample_rate,
            'channels': audio_sources['ref'].channels
        },
        'room': {
            'duration': audio_sources['room'].duration,
            'sample_rate': audio_sources['room'].sample_rate,
            'channels': audio_sources['room'].channels
        }
    }
    ws.send(json.dumps(metadata))

    # keep connection open for future messages
    while True:
        message = ws.receive()
        if message is None:
            break
        # handle messages (transport commands etc) - implemented in transport feature

if __name__ == '__main__':
    load_audio_files()
    print(f"Loaded ref.wav: {audio_sources['ref'].duration:.1f}s")
    print(f"Loaded room.wav: {audio_sources['room'].duration:.1f}s")
    app.run(debug=True, port=5000)
```

## frontend (JavaScript)

### index.html

```html
<!DOCTYPE html>
<html>
<head>
    <title>Boomer Testbed</title>
    <style>
        body { font-family: monospace; padding: 20px; }
        #status { margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Boomer Testbed</h1>
    <div id="status">Connecting...</div>
    <script src="app.js"></script>
</body>
</html>
```

### app.js

```javascript
// testbed/load-audio
const status = document.getElementById('status');
let ws;

function connect() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = () => {
        status.textContent = 'Connected, waiting for audio info...';
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'audio_loaded') {
            status.textContent = `ref: ${msg.ref.duration.toFixed(1)}s, room: ${msg.room.duration.toFixed(1)}s @ ${msg.ref.sample_rate}Hz`;
        }
    };

    ws.onclose = () => {
        status.textContent = 'Disconnected. Reconnecting...';
        setTimeout(connect, 1000);
    };

    ws.onerror = () => {
        status.textContent = 'Connection error';
    };
}

connect();
```
