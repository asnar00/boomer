# remote-control test

## prerequisites

- Server running
- Browser connected to http://localhost:5000

## API control tests

```bash
# get current status
curl http://localhost:5000/api/status

# play
curl -X POST http://localhost:5000/api/transport/play

# pause
curl -X POST http://localhost:5000/api/transport/pause

# seek to 30 seconds
curl -X POST "http://localhost:5000/api/transport/seek?position=30"

# switch source
curl -X POST "http://localhost:5000/api/source?name=room"
```

Each should return JSON with updated state.

## client control tests

```bash
# simulate click (once UI has buttons)
curl -X POST "http://localhost:5000/api/client/click?element=%23play-button"

# execute JS in frontend
curl -X POST "http://localhost:5000/api/client/eval?js=console.log('hello')"

# refresh all clients
curl -X POST http://localhost:5000/api/client/refresh
```

Check browser console shows execution result.
Check browser reloads when refresh is called.
Check logs/session.log shows remote control events.

## state sync test

1. Open two browser tabs to http://localhost:5000
2. Call play API
3. Both tabs should update to show playing state
