# logging pseudocode

## backend

### log function

```
function log(category, message):
    timestamp = current time formatted as HH:MM:SS.mmm
    source = "backend"
    line = format "[{timestamp}] [{source}] [{category}] {message}"

    print line to terminal
    append line to log file
```

### on startup

```
create logs directory if it doesn't exist
clear or create session log file
log("audio", "Server starting")
```

### on websocket message from frontend

```
if message type is "log":
    timestamp = current time
    source = "frontend"
    line = format "[{timestamp}] [{source}] [{category}] {message}"

    print line to terminal
    append line to log file
```

## frontend

### log function

```
function log(category, message):
    print to browser console with category prefix
    send to backend via websocket: { type: "log", category, message }
```

## messages

```
frontend -> backend:
    log: { type: "log", category: string, message: string }
```
