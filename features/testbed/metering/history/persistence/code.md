# persistence code

## backend (Python)

### meters.py modifications

```python
# testbed/metering/history/persistence - server-side history storage
meter_history = {}  # meter_history[meter_name][source][time_bucket] = data
TIME_BUCKET_SIZE = 0.1  # 100ms buckets, must match frontend

def time_bucket(time):
    return round(time / TIME_BUCKET_SIZE) * TIME_BUCKET_SIZE

def store_meter_data(meter_name, time, ref_data, room_data):
    if meter_name not in meter_history:
        meter_history[meter_name] = {'ref': {}, 'room': {}}

    bucket = time_bucket(time)
    meter_history[meter_name]['ref'][bucket] = ref_data
    meter_history[meter_name]['room'][bucket] = room_data

def get_meter_history(meter_name):
    if meter_name in meter_history:
        return meter_history[meter_name]
    return {'ref': {}, 'room': {}}

# in metering_loop, after computing measurements:
# ... existing code ...
store_meter_data(name, pos / sample_rate, ref_data, room_data)

# update subscribe function:
def subscribe(ws, name):
    if ws not in client_subscriptions:
        client_subscriptions[ws] = set()
    client_subscriptions[ws].add(name)
    log('meter', f'Subscribed to: {name}')

    # send existing history to new subscriber
    history = get_meter_history(name)
    message = json.dumps({
        'type': 'meter_history',
        'name': name,
        'ref': history['ref'],
        'room': history['room']
    })
    ws.send(message)
```

## frontend (JavaScript)

### app.js modifications

```javascript
// in ws.onmessage handler, add:
if (msg.type === 'meter_history') {
    if (msg.name === currentMeter) {
        // populate local history from server data
        for (const [time, data] of Object.entries(msg.ref)) {
            meterHistory['ref'][parseFloat(time)] = data;
        }
        for (const [time, data] of Object.entries(msg.room)) {
            meterHistory['room'][parseFloat(time)] = data;
        }
        log('meter', `Loaded ${Object.keys(msg.ref).length} history buckets`);
        updateMeterDisplay();
    }
}
```
