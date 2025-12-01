# metering test

## prerequisites

- Server running
- Browser connected to http://localhost:5000
- At least one measurement registered (e.g., spectrum)

## manual test

1. Verify meter tabs appear below source buttons
2. Click a tab - should highlight
3. Start playback - visualization should update in real-time
4. Switch tabs - should show different measurement
5. Stop playback - updates should pause
6. Switch sources - measurements should reflect different audio

## API test

```bash
# check available measurements
curl -X POST "http://localhost:5000/api/client/eval?js=availableMeters"
```

## subscription test

1. Open browser console
2. Start playback
3. Select a meter tab
4. Verify meter messages arriving (check logs)
5. Switch tabs - verify subscription changes

## performance test

1. Play audio with meter active
2. Verify no audio glitches (metering shouldn't affect playback)
3. Check CPU usage is reasonable
