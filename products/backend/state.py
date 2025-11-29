# testbed/remote-control

from dataclasses import dataclass, asdict
from typing import List
import json

@dataclass
class AppState:
    playing: bool = False
    position: float = 0.0
    source: str = 'ref'
    duration: float = 0.0

state = AppState()
connected_clients: List = []

def get_state_dict():
    return {'type': 'state', **asdict(state)}

def broadcast_state():
    message = json.dumps(get_state_dict())
    for ws in connected_clients:
        try:
            ws.send(message)
        except:
            pass  # client may have disconnected
