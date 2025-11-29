# source-switch test

## prerequisites

- Server running
- Browser connected to http://localhost:5000
- Audio playing

## manual test

1. Start playback with ref source
2. Click "room" button - audio should smoothly switch to room recording
3. Click "ref" button - audio should smoothly switch back
4. Verify no clicks or pops during switch
5. Verify position is maintained across switches
6. Verify button highlights show correct active source

## API test

```bash
# start playing ref
curl -X POST http://localhost:5000/api/transport/play

# switch to room while playing
curl -X POST "http://localhost:5000/api/source?name=room"

# verify source changed
curl http://localhost:5000/api/status

# switch back to ref
curl -X POST "http://localhost:5000/api/source?name=ref"
```

## remote UI test

```bash
# click room button via remote control
curl -X POST "http://localhost:5000/api/client/click?element=%23source-room"

# verify source changed
curl http://localhost:5000/api/status
```

## edge cases

1. Switch while paused - should work, no crossfade needed
2. Switch to same source - should be no-op
3. Switch with invalid source name - should be ignored
4. Rapid switching - should handle gracefully
