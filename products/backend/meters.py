# testbed/metering, testbed/processor

import threading
import time
import json
import numpy as np
from pathlib import Path
from audio import audio_sources
from state import state, connected_clients
import playback
import processor
from logger import log

# measurement registry
measurements = {}

# active subscriptions per client (ws -> set of measurement names)
client_subscriptions = {}

# testbed/metering/history/persistence - server-side history storage
meter_history = {}  # meter_history[meter_name][source][time_bucket] = data
TIME_BUCKET_SIZE = 0.1  # 100ms buckets, must match frontend
HISTORY_FILE = Path('meter_history.json')

def save_history_to_disk():
    """Save meter history to disk"""
    # Convert float keys to strings for JSON
    serializable = {}
    for meter_name, sources in meter_history.items():
        serializable[meter_name] = {}
        for source, buckets in sources.items():
            serializable[meter_name][source] = {str(k): v for k, v in buckets.items()}

    with open(HISTORY_FILE, 'w') as f:
        json.dump(serializable, f)
    log('meter', f'Saved history to {HISTORY_FILE}')

def load_history_from_disk():
    """Load meter history from disk"""
    global meter_history
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            data = json.load(f)
        # Convert string keys back to floats
        for meter_name, sources in data.items():
            meter_history[meter_name] = {}
            for source, buckets in sources.items():
                meter_history[meter_name][source] = {float(k): v for k, v in buckets.items()}
        log('meter', f'Loaded {sum(len(s.get("ref", {})) for s in meter_history.values())} history buckets from {HISTORY_FILE}')

CHUNK_SIZE = 8192  # samples for measurement (gives ~5.4Hz resolution at 44.1kHz)
METER_RATE = 20    # Hz

def time_bucket(t):
    """Floor time to bucket boundary (must match frontend)"""
    import math
    return math.floor(t / TIME_BUCKET_SIZE) * TIME_BUCKET_SIZE

_save_counter = 0
_SAVE_INTERVAL = 100  # save every N buckets

def store_meter_data(meter_name, t, ref_data, room_data, processed_data=None):
    """Store meter data in server-side history"""
    global _save_counter

    if meter_name not in meter_history:
        meter_history[meter_name] = {'ref': {}, 'room': {}, 'processed': {}}

    bucket = time_bucket(t)
    meter_history[meter_name]['ref'][bucket] = ref_data
    meter_history[meter_name]['room'][bucket] = room_data
    if processed_data is not None:
        meter_history[meter_name]['processed'][bucket] = processed_data

    # Periodically save to disk
    _save_counter += 1
    if _save_counter >= _SAVE_INTERVAL:
        _save_counter = 0
        save_history_to_disk()

def get_meter_history(meter_name):
    """Get stored history for a meter"""
    if meter_name in meter_history:
        return meter_history[meter_name]
    return {'ref': {}, 'room': {}, 'processed': {}}

def export_meter_csv(meter_name, start_time, end_time, filepath):
    """Export meter history to CSV with alternating ref/room rows"""
    history = get_meter_history(meter_name)
    if not history['ref']:
        return False

    # Get sorted time buckets in range
    times = sorted([t for t in history['ref'].keys() if start_time <= t <= end_time])

    if not times:
        return False

    # Figure out number of bands from first entry
    num_bands = len(history['ref'][times[0]])

    with open(filepath, 'w') as f:
        # Header row
        header = ['time', 'source'] + [f'band_{i}' for i in range(num_bands)]
        f.write(','.join(header) + '\n')

        # Data rows - alternating ref/room for each time bucket
        for t in times:
            ref_data = history['ref'].get(t, [0] * num_bands)
            room_data = history['room'].get(t, [0] * num_bands)

            # Ref row
            ref_row = [f'{t:.1f}', 'ref'] + [f'{v:.2f}' for v in ref_data]
            f.write(','.join(ref_row) + '\n')

            # Room row
            room_row = [f'{t:.1f}', 'room'] + [f'{v:.2f}' for v in room_data]
            f.write(','.join(room_row) + '\n')

    log('meter', f'Exported {len(times)} buckets to {filepath}')
    return True

def register_measurement(name, module):
    """Register a measurement module with the framework"""
    measurements[name] = module
    log('meter', f'Registered measurement: {name}')

def get_chunk_at_position(audio_data, position, chunk_size):
    """Extract a chunk of audio centered on position"""
    start = max(0, position - chunk_size // 2)
    end = min(len(audio_data), start + chunk_size)
    chunk = audio_data[start:end]

    # ensure we have enough samples (pad with zeros if needed)
    if len(chunk) < chunk_size:
        if audio_data.ndim == 1:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
        else:
            chunk = np.pad(chunk, ((0, chunk_size - len(chunk)), (0, 0)))

    return chunk

def metering_loop():
    """Background thread that computes and broadcasts measurements"""
    while True:
        if state.playing and client_subscriptions:
            sample_rate = audio_sources['ref'].sample_rate

            with playback.playback_lock:
                pos = playback.playback_position

            # get chunks from all sources at same position
            ref_chunk = get_chunk_at_position(audio_sources['ref'].data, pos, CHUNK_SIZE)
            room_chunk = get_chunk_at_position(audio_sources['room'].data, pos, CHUNK_SIZE)

            # testbed/processor - ensure processed data exists and get chunk
            processor.process_chunk(pos - CHUNK_SIZE // 2, pos + CHUNK_SIZE // 2)
            processed_chunk = get_chunk_at_position(audio_sources['processed'].data, pos, CHUNK_SIZE)

            # compute measurements for subscribed clients
            for ws, subscribed in list(client_subscriptions.items()):
                for name in subscribed:
                    if name in measurements:
                        module = measurements[name]
                        try:
                            ref_data = module.measure(ref_chunk, sample_rate)
                            room_data = module.measure(room_chunk, sample_rate)
                            processed_data = module.measure(processed_chunk, sample_rate)
                            diff = module.compare(ref_data, room_data)

                            meter_time = pos / sample_rate

                            # testbed/metering/history/persistence - store on server
                            store_meter_data(name, meter_time, ref_data, room_data, processed_data)

                            # testbed/metering/history - add time to message
                            message = json.dumps({
                                'type': 'meter',
                                'name': name,
                                'time': meter_time,
                                'ref': ref_data,
                                'room': room_data,
                                'processed': processed_data,
                                'diff': diff
                            })
                            ws.send(message)
                        except Exception as e:
                            log('meter', f'Error computing {name}: {e}')

        time.sleep(1.0 / METER_RATE)

def start_metering_thread():
    thread = threading.Thread(target=metering_loop, daemon=True)
    thread.start()

def subscribe(ws, name):
    if ws not in client_subscriptions:
        client_subscriptions[ws] = set()
    client_subscriptions[ws].add(name)
    log('meter', f'Subscribed to: {name}')

    # testbed/metering/history/persistence - send existing history to new subscriber
    history = get_meter_history(name)
    history_size = len(history['ref'])
    if history_size > 0:
        message = json.dumps({
            'type': 'meter_history',
            'name': name,
            'ref': history['ref'],
            'room': history['room'],
            'processed': history['processed']
        })
        ws.send(message)
        log('meter', f'Sent {history_size} history buckets for {name}')

def unsubscribe(ws, name):
    if ws in client_subscriptions:
        client_subscriptions[ws].discard(name)
        log('meter', f'Unsubscribed from: {name}')

def client_disconnected(ws):
    if ws in client_subscriptions:
        del client_subscriptions[ws]
