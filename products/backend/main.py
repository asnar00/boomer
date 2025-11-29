# testbed/load-audio, testbed/logging, testbed/remote-control, testbed/transport

from flask import Flask, request, jsonify
from flask_sock import Sock
import json
from audio import load_audio_files, audio_sources
from logger import init_logging, log
from state import state, connected_clients, get_state_dict, broadcast_state
from playback import start_playback, stop_playback, seek, start_position_thread, switch_source

app = Flask(__name__, static_folder='../frontend', static_url_path='')
sock = Sock(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@sock.route('/ws')
def websocket(ws):
    connected_clients.append(ws)
    log('ws', 'Client connected')

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

        data = json.loads(message)

        # testbed/logging - handle frontend log messages
        if data['type'] == 'log':
            log(data['category'], data['message'], source='frontend')

        # testbed/transport - handle transport commands
        if data['type'] == 'play':
            start_playback()
        if data['type'] == 'pause':
            stop_playback()
        if data['type'] == 'seek':
            seek(data['position'])

        # testbed/source-switch
        if data['type'] == 'source':
            switch_source(data['name'])

    connected_clients.remove(ws)
    log('ws', 'Client disconnected')

# testbed/remote-control - API endpoints

@app.route('/api/status')
def api_status():
    return jsonify(get_state_dict())

@app.route('/api/transport/play', methods=['POST'])
def api_play():
    start_playback()
    return jsonify(get_state_dict())

@app.route('/api/transport/pause', methods=['POST'])
def api_pause():
    stop_playback()
    return jsonify(get_state_dict())

@app.route('/api/transport/seek', methods=['POST'])
def api_seek():
    position = float(request.args.get('position', 0))
    seek(position)
    return jsonify(get_state_dict())

@app.route('/api/source', methods=['POST'])
def api_source():
    name = request.args.get('name', 'ref')
    switch_source(name)
    return jsonify(get_state_dict())

# testbed/remote-control - client control endpoints

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

if __name__ == '__main__':
    init_logging()
    load_audio_files()
    state.duration = audio_sources['ref'].duration
    log('audio', f"Loaded ref.wav: {audio_sources['ref'].duration:.1f}s")
    log('audio', f"Loaded room.wav: {audio_sources['room'].duration:.1f}s")
    start_position_thread()
    app.run(debug=True, port=5000, threaded=True)
