# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Boomer is a real-time audio processing system that simulates the sound of a big room. The goal is to create filters that can transform clean audio (ref.wav) to match room-recorded audio (room.wav), simulating the effect of a large PA system, venue acoustics, audience absorption, and recording equipment.

## Architecture Goals

The system should model these audio transformations as chainable processors:
- PA system output characteristics
- Echo, resonance, and reverb from venue interactions
- Audience absorption effects
- Recording equipment characteristics (cellphone)

Each processor must support:
1. Measuring audio qualities (q_ref, q_room, q_test)
2. Comparing measurements between audio files
3. Real-time processing capability

## Development Approach

The iterative optimization loop:
1. Measure qualities of ref.wav and room.wav
2. Apply processor with settings P to ref.wav → test.wav
3. Compare q_test with q_room
4. Adjust P to minimize difference

Build an interactive playback interface that displays measurements in real-time while ensuring all processors can run at audio sample rates.

## Documentation Structure

All code is documented using feature-modular specifications (see `features.md`):

- `/features/A/B/` - Nested feature specs, each containing:
  - `spec.md` - What and why (max 150 words)
  - `pseudocode.md` - Natural language implementation steps
  - `code.md` - Actual code snippets

- `/products/` - Implementation code, separated by product:
  - `backend/` - Python audio processing server (sounddevice)
  - `frontend/` - Browser UI (HTML/JS)

Product code must reference the feature path it implements via comments. Ad-hoc code changes should flow back to update the feature docs.
