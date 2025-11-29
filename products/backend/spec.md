# backend

Python server handling audio loading, processing, and playback.

## technology

- **Python 3.11+**
- **Flask** - HTTP server for serving frontend
- **flask-sock** - Websocket support for real-time communication
- **sounddevice** - Audio playback to system output
- **scipy.io.wavfile** - Reading wav files

## setup

```
cd products/backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## running

```
python main.py
```

Serves frontend at http://localhost:5000
