# transport test

## prerequisites

- Server running
- Browser connected to http://localhost:5000
- Audio output device available

## manual test

1. Click Play - audio should start playing
2. Click Pause - audio should stop, position preserved
3. Click Play again - audio resumes from same position
4. Click -10s - position jumps back 10 seconds
5. Click +10s - position jumps forward 10 seconds
6. Position display updates during playback (~10Hz)

## API test

```bash
# play
curl -X POST http://localhost:5000/api/transport/play

# check position is advancing
curl http://localhost:5000/api/status
sleep 2
curl http://localhost:5000/api/status

# pause
curl -X POST http://localhost:5000/api/transport/pause

# seek to 60 seconds
curl -X POST "http://localhost:5000/api/transport/seek?position=60"

# verify position
curl http://localhost:5000/api/status
```

## remote UI test

```bash
# click play button via remote control
curl -X POST "http://localhost:5000/api/client/click?element=%23play-pause"

# check state
curl http://localhost:5000/api/status
```

## edge cases

1. Seek past end - should clamp to end
2. Seek before start - should clamp to 0
3. Play when already playing - should be no-op
4. Pause when already paused - should be no-op
5. Let audio play to end - should auto-pause at end
