# spectrum test

## prerequisites

- Server running with spectrum measurement registered
- Browser connected

## manual test

1. Click "spectrum" tab
2. Start playback
3. Verify spectrum visualization updates in real-time
4. Blue (ref) and orange (room) spectra should be visible
5. Observe differences - room likely has less high frequency content
6. Difference score should be non-zero and change with the audio

## API test

```bash
# verify spectrum module is registered
curl -X POST "http://localhost:5000/api/client/eval?js=availableMeters.includes('spectrum')"
```

## visual verification

- Spectrum should respond to audio content (more bass = more low-end)
- Silent sections should show low values across all bands
- Loud sections should show higher values
- Room spectrum should generally be "duller" (less highs) than ref
