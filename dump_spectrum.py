# Dump spectrum history to CSV with ref, room, and processed
import sys
sys.path.insert(0, '/Users/asnaroo/Desktop/experiments/boomer/products/backend')

import json
from pathlib import Path

# Load history from disk
HISTORY_FILE = Path('/Users/asnaroo/Desktop/experiments/boomer/meter_history.json')

with open(HISTORY_FILE, 'r') as f:
    data = json.load(f)

# Get spectrum data
spectrum = data.get('spectrum', {})
ref_history = spectrum.get('ref', {})
room_history = spectrum.get('room', {})
processed_history = spectrum.get('processed', {})

# Time range: 45-50 seconds
start_time = 45.0
end_time = 50.0

# Get sorted time buckets in range
times = sorted([float(t) for t in ref_history.keys() if start_time <= float(t) <= end_time])

if not times:
    print("No data in time range")
    sys.exit(1)

# Figure out number of bands from first entry
num_bands = len(ref_history[str(times[0])])
print(f"Found {len(times)} time buckets with {num_bands} frequency bands")

# Write CSV
filepath = '/Users/asnaroo/Desktop/experiments/boomer/spectrum_comparison.csv'
with open(filepath, 'w') as f:
    # Header row
    header = ['time', 'source'] + [f'band_{i}' for i in range(num_bands)]
    f.write(','.join(header) + '\n')
    
    # Data rows - ref/room/processed for each time bucket
    for t in times:
        t_str = str(t)
        ref_data = ref_history.get(t_str, [0] * num_bands)
        room_data = room_history.get(t_str, [0] * num_bands)
        processed_data = processed_history.get(t_str, [0] * num_bands)
        
        # Ref row
        ref_row = [f'{t:.1f}', 'ref'] + [f'{v:.2f}' for v in ref_data]
        f.write(','.join(ref_row) + '\n')
        
        # Room row
        room_row = [f'{t:.1f}', 'room'] + [f'{v:.2f}' for v in room_data]
        f.write(','.join(room_row) + '\n')
        
        # Processed row
        proc_row = [f'{t:.1f}', 'processed'] + [f'{v:.2f}' for v in processed_data]
        f.write(','.join(proc_row) + '\n')

print(f'Exported {len(times)} buckets to {filepath}')
