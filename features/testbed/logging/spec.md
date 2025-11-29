# logging

Unified logging across backend and frontend for tracing and debugging.

## behaviour

All significant events are logged with a consistent format: timestamp, source (backend/frontend), category, and message. Logs are written to a file and also output to terminal (backend) and browser console (frontend).

Frontend logs are sent to backend via websocket so all logs end up in one file.

## categories

- audio - Audio loading, playback events
- ws - Websocket connection events
- transport - Play, pause, seek actions
- ui - User interactions
