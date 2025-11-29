# load-audio test

## prerequisites

- ref.wav and room.wav in project root
- backend dependencies installed

## manual test

1. Start the server: `python products/backend/main.py`
2. Check terminal shows "Loaded ref.wav: Xs" and "Loaded room.wav: Xs"
3. Open http://localhost:5000 in browser
4. Verify status shows audio duration and sample rate

## API test

```bash
# with server running
curl http://localhost:5000/api/status
```

Should return JSON with duration > 0.

## error cases

1. Remove ref.wav, start server - should show clear error message
2. Use mismatched sample rates - should show "sample rates must match" error
