# logging test

## prerequisites

- Server running
- Browser connected to http://localhost:5000

## manual test

1. Start server, observe terminal shows timestamped log lines
2. Check logs/session.log file is created
3. Open browser to http://localhost:5000
4. Check terminal shows "[frontend] [ws] Connected to backend"
5. Check browser console shows log messages with category prefixes

## API test

```bash
# check log file exists and has content
cat logs/session.log
```

Should show timestamped entries from both backend and frontend.

## verify format

Each line should match: `[HH:MM:SS.mmm] [source] [category] message`
