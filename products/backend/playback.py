# testbed/transport, testbed/source-switch, testbed/processor

import sounddevice as sd
import numpy as np
import threading
import time
from audio import audio_sources
from state import state, broadcast_state
from logger import log
import processor

# playback state
stream = None
playback_position = 0  # in samples
playback_lock = threading.Lock()

# crossfade state (source-switch)
crossfade_samples = 0
crossfade_from_audio = None
CROSSFADE_MS = 15  # milliseconds

def get_current_audio():
    # For processed source, ensure data is processed before returning
    if state.source == 'processed':
        return audio_sources['processed'].data
    return audio_sources[state.source].data

def audio_callback(outdata, frames, time_info, status):
    global playback_position, crossfade_samples, crossfade_from_audio

    with playback_lock:
        start = playback_position
        end = start + frames

    # testbed/processor - ensure processed data is ready before playback
    if state.source == 'processed':
        processor.process_chunk(start, end)

    audio = get_current_audio()

    with playback_lock:

        if end >= len(audio):
            # reached end of audio
            end = len(audio)
            samples_to_copy = end - start
            if audio.ndim == 1:
                outdata[:samples_to_copy, 0] = audio[start:end]
                if outdata.shape[1] > 1:
                    outdata[:samples_to_copy, 1] = audio[start:end]
            else:
                outdata[:samples_to_copy] = audio[start:end]
            outdata[samples_to_copy:] = 0  # silence for remaining
            playback_position = len(audio)
            # schedule stop (can't stop from callback)
            threading.Thread(target=stop_playback).start()
        else:
            if audio.ndim == 1:
                outdata[:, 0] = audio[start:end]
                if outdata.shape[1] > 1:
                    outdata[:, 1] = audio[start:end]
            else:
                outdata[:] = audio[start:end]

            # apply crossfade if switching sources
            if crossfade_samples > 0 and crossfade_from_audio is not None:
                fade_frames = min(frames, crossfade_samples)

                # get old source audio
                old_end = min(start + fade_frames, len(crossfade_from_audio))
                old_samples = crossfade_from_audio[start:old_end]

                # create crossfade ramp
                t = np.linspace(0, 1, fade_frames)
                fade_in = t.reshape(-1, 1)
                fade_out = (1 - t).reshape(-1, 1)

                # make old samples stereo if needed
                if crossfade_from_audio.ndim == 1:
                    old_stereo = np.column_stack([old_samples, old_samples])
                else:
                    old_stereo = old_samples

                # blend (only for frames we have old data for)
                blend_frames = min(fade_frames, len(old_stereo))
                outdata[:blend_frames] = (outdata[:blend_frames] * fade_in[:blend_frames] +
                                          old_stereo[:blend_frames] * fade_out[:blend_frames])

                crossfade_samples -= fade_frames
                if crossfade_samples <= 0:
                    crossfade_from_audio = None

            playback_position = end

def start_playback():
    global stream, playback_position

    if state.playing:
        return

    audio = get_current_audio()
    sample_rate = audio_sources[state.source].sample_rate
    channels = audio_sources[state.source].channels

    # if at end, restart from beginning
    with playback_lock:
        if playback_position >= len(audio):
            playback_position = 0

    stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=max(channels, 2),  # at least stereo output
        callback=audio_callback,
        blocksize=4096,  # larger buffer to prevent underruns
        latency='high'   # prioritize stability over low latency
    )
    stream.start()

    state.playing = True
    log('transport', f'Play from {state.position:.1f}s')
    broadcast_state()

def stop_playback():
    global stream

    if not state.playing:
        return

    if stream:
        stream.stop()
        stream.close()
        stream = None

    state.playing = False
    log('transport', f'Pause at {state.position:.1f}s')
    broadcast_state()

def seek(position_seconds):
    global playback_position

    sample_rate = audio_sources[state.source].sample_rate
    audio = get_current_audio()

    with playback_lock:
        playback_position = int(position_seconds * sample_rate)
        playback_position = max(0, min(playback_position, len(audio)))
        state.position = playback_position / sample_rate

    log('transport', f'Seek to {state.position:.1f}s')
    broadcast_state()

def switch_source(new_source):
    global crossfade_samples, crossfade_from_audio

    if new_source not in ['ref', 'room', 'processed']:
        return
    if new_source == state.source:
        return

    with playback_lock:
        if state.playing:
            # store current audio for crossfade
            crossfade_from_audio = audio_sources[state.source].data
            sample_rate = audio_sources[state.source].sample_rate
            crossfade_samples = int(sample_rate * CROSSFADE_MS / 1000)

        state.source = new_source

    log('transport', f'Source: {new_source}')
    broadcast_state()

def position_update_loop():
    """Run in background thread to update position during playback"""
    while True:
        if state.playing:
            sample_rate = audio_sources[state.source].sample_rate
            with playback_lock:
                state.position = playback_position / sample_rate
            broadcast_state()
        time.sleep(0.1)  # 10Hz updates

def start_position_thread():
    thread = threading.Thread(target=position_update_loop, daemon=True)
    thread.start()
