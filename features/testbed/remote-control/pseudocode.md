# remote-control pseudocode

## backend

### state

```
global state:
    playing = false
    position = 0
    source = "ref"
    duration = (from loaded audio)
    connected_clients = list of websocket connections
```

### API endpoints

```
GET /api/status:
    return current state as response

POST /api/transport/play:
    set playing = true
    broadcast state to all clients
    return current state

POST /api/transport/pause:
    set playing = false
    broadcast state to all clients
    return current state

POST /api/transport/seek:
    position = request parameter "position"
    clamp position to valid range
    broadcast state to all clients
    return current state

POST /api/source:
    source = request parameter "name"
    broadcast state to all clients
    return current state
```

### client control endpoints

```
POST /api/client/click:
    element = request parameter "element"
    send to all clients: { type: "remote_click", element }
    return current state

POST /api/client/eval:
    code = request parameter "js"
    send to all clients: { type: "remote_eval", code }
    return current state

POST /api/client/refresh:
    send to all clients: { type: "remote_refresh" }
    return ok
```

### broadcast function

```
function broadcast_state():
    message = { type: "state", playing, position, source, duration }
    for each client in connected_clients:
        send message to client
```

## frontend

### handle remote control messages

```
on websocket message:
    if type is "remote_click":
        find element by selector
        if found: trigger click event
        log result

    if type is "remote_eval":
        execute code
        log result

    if type is "remote_refresh":
        reload the page

    if type is "state":
        update UI to reflect new state
```

## messages

```
backend -> frontend:
    state: { type: "state", playing, position, source, duration }
    remote_click: { type: "remote_click", element: selector }
    remote_eval: { type: "remote_eval", code: string }
    remote_refresh: { type: "remote_refresh" }
```
