# remote-control

HTTP API for programmatic control of the testbed, enabling automated testing.

## behaviour

Two levels of control:

1. **API control** - Direct backend endpoints, bypassing the frontend. Tests server logic in isolation.

2. **Client control** - Commands sent to frontend via websocket, which executes UI actions. Tests the full client-server round-trip.

API endpoints exist for getting status, controlling transport (play, pause, seek), and switching audio source.

Client control allows simulating clicks on UI elements, executing arbitrary code in the frontend context, and triggering page refreshes.

All endpoints return current state. State updates are broadcast to all connected frontends.

## constraints

- API actions behave identically to UI actions
- Client control actions trigger real UI code paths
