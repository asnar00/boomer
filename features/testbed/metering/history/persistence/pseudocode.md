# persistence pseudocode

## backend

```
// server-side history storage
meter_history = {}  // meter_history[meter_name][source][time_bucket] = data

function store_meter_data(meter_name, time, ref_data, room_data):
    if meter_name not in meter_history:
        meter_history[meter_name] = { ref: {}, room: {} }

    bucket = floor(time / BUCKET_SIZE) * BUCKET_SIZE
    meter_history[meter_name]['ref'][bucket] = ref_data
    meter_history[meter_name]['room'][bucket] = room_data

function get_meter_history(meter_name):
    if meter_name in meter_history:
        return meter_history[meter_name]
    return { ref: {}, room: {} }

// in metering_loop, after computing measurements:
store_meter_data(name, time, ref_data, room_data)

// in subscribe handler:
function subscribe(ws, name):
    // ... existing subscription code ...

    // send existing history to new subscriber
    history = get_meter_history(name)
    ws.send({
        type: 'meter_history',
        name: name,
        ref: history['ref'],
        room: history['room']
    })
```

## frontend

```
// in message handler:
if msg.type == 'meter_history':
    if msg.name == currentMeter:
        // populate local history from server data
        for time, data in msg.ref:
            meterHistory['ref'][time] = data
        for time, data in msg.room:
            meterHistory['room'][time] = data
        updateMeterDisplay()
```
