# testbed/load-audio, testbed/logging, testbed/remote-control, testbed/transport, testbed/metering, testbed/processor

from flask import Flask, request, jsonify
from flask_sock import Sock
import json
from audio import load_audio_files, audio_sources
from logger import init_logging, log
from state import state, connected_clients, get_state_dict, broadcast_state
from playback import start_playback, stop_playback, seek, start_position_thread, switch_source
from meters import start_metering_thread, subscribe, unsubscribe, client_disconnected, register_measurement, get_meter_history, load_history_from_disk, save_history_to_disk, export_meter_csv
from measurements import register_all
import processor

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

        # testbed/metering
        if data['type'] == 'meter_subscribe':
            subscribe(ws, data['name'])
        if data['type'] == 'meter_unsubscribe':
            unsubscribe(ws, data['name'])

    # testbed/metering - cleanup on disconnect
    client_disconnected(ws)
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

# testbed/metering/history/persistence - export API
@app.route('/api/meter/export')
def api_meter_export():
    meter = request.args.get('meter', 'spectrum')
    start = float(request.args.get('start', 0))
    end = float(request.args.get('end', 60))
    filepath = request.args.get('file', 'meter_export.csv')

    success = export_meter_csv(meter, start, end, filepath)
    if success:
        return jsonify({'status': 'ok', 'file': filepath})
    else:
        return jsonify({'status': 'error', 'message': 'No data in range'}), 404

if __name__ == '__main__':
    init_logging()
    load_audio_files()
    processor.init_processor()  # testbed/processor
    state.duration = audio_sources['ref'].duration
    log('audio', f"Loaded ref.wav: {audio_sources['ref'].duration:.1f}s")
    log('audio', f"Loaded room.wav: {audio_sources['room'].duration:.1f}s")
    start_position_thread()
    # testbed/metering
    register_all(register_measurement)
    load_history_from_disk()  # testbed/metering/history/persistence
    start_metering_thread()
    app.run(debug=True, port=5000, threaded=True)
