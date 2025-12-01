# Dump ref, room, and processed audio to CSV for analysis
import sys
sys.path.insert(0, '/Users/asnaroo/Desktop/experiments/boomer/products/backend')

import numpy as np
from audio import load_audio_files, audio_sources
from processor import init_processor

# Load audio
load_audio_files()
init_processor()

# Get the three sources
ref = audio_sources['ref'].data
room = audio_sources['room'].data
processed = audio_sources['processed'].data

sample_rate = audio_sources['ref'].sample_rate

# Convert to mono if stereo
if ref.ndim > 1:
    ref = np.mean(ref, axis=1)
if room.ndim > 1:
    room = np.mean(room, axis=1)
if processed.ndim > 1:
    processed = np.mean(processed, axis=1)

# Time range: 47-48 seconds (where the kicks start)
start_sec = 47.0
end_sec = 48.0
start_sample = int(start_sec * sample_rate)
end_sample = int(end_sec * sample_rate)

# Extract segments
ref_seg = ref[start_sample:end_sample]
room_seg = room[start_sample:end_sample]
processed_seg = processed[start_sample:end_sample]

# Create time array
times = np.arange(start_sample, end_sample) / sample_rate

# Write to CSV
with open('/Users/asnaroo/Desktop/experiments/boomer/audio_comparison.csv', 'w') as f:
    f.write('time,ref,room,processed\n')
    for i in range(len(times)):
        f.write(f'{times[i]:.6f},{ref_seg[i]:.6f},{room_seg[i]:.6f},{processed_seg[i]:.6f}\n')

print(f'Wrote {len(times)} samples ({start_sec}-{end_sec}s) to audio_comparison.csv')
print(f'Sample rate: {sample_rate}')
