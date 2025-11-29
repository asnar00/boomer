# source-switch

Switch between audio sources during playback.

## behaviour

The frontend displays source selector buttons: "ref", "room", and later "processed". Clicking a source switches playback to that audio immediately, maintaining the current playback position.

Backend receives source switch commands and crossfades briefly (10-20ms) to avoid clicks.

## constraints

- Switching sources does not interrupt playback
- Position is preserved across switches
- Brief crossfade prevents audio clicks
- Visual indicator shows which source is active
