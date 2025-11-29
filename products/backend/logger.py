# testbed/logging

from datetime import datetime
from pathlib import Path

LOG_DIR = Path('logs')
LOG_FILE = LOG_DIR / 'session.log'

def init_logging():
    LOG_DIR.mkdir(exist_ok=True)
    LOG_FILE.write_text('')
    log('system', 'Logging initialized')

def log(category: str, message: str, source: str = 'backend'):
    timestamp = datetime.now().strftime('%H:%M:%S.') + f'{datetime.now().microsecond // 1000:03d}'
    line = f'[{timestamp}] [{source}] [{category}] {message}'

    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')
