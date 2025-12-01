# persistence

Stores meter history on the server so it survives browser refresh.

## behaviour

- Server maintains meter history for each measurement type (e.g., spectrum)
- History is stored per-source (ref, room) with time-bucketed data
- When a client connects and subscribes to a meter, server sends all existing history
- New measurements are stored on server and broadcast to clients as before
- History persists across client disconnects/reconnects
- History is cleared when switching meters (as before)

## data flow

1. Client connects and subscribes to meter (e.g., "spectrum")
2. Server sends `meter_history` message with all stored data for that meter
3. Client populates its local history from server data
4. Playback continues, new measurements stored on server and sent to clients
5. On browser refresh, client reconnects and receives full history again

## storage

- In-memory on server (lost on server restart, which is fine for testbed)
- Keyed by meter name, then source, then time bucket
