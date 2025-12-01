# processor pseudocode

## backend

### initialization

```
processed_buffer = empty array, same size as ref audio
processed_valid = boolean array tracking which samples are processed

function init_processor():
    allocate processed_buffer matching ref audio shape
    set all processed_valid to false
    register 'processed' as audio source pointing to processed_buffer
```

### processing

```
function process_chunk(start_sample, end_sample):
    // skip if already processed
    if all samples in range are valid:
        return

    input = ref audio from start to end

    // === PROCESSING ===
    output = input  // passthrough for now
    // === END PROCESSING ===

    store output in processed_buffer
    mark range as valid

function get_processed_audio(position, num_samples):
    process_chunk(position, position + num_samples)
    return processed_buffer slice
```

### playback integration

```
in audio_callback:
    if source is 'processed':
        ensure chunk is processed before playback
        // processed_buffer is already registered as audio source
```

### source switching

```
in switch_source:
    accept 'processed' as valid source (in addition to ref, room)
```

### export

```
function save_processed_wav(filepath):
    convert processed_buffer to int16
    write as wav file
```

## frontend

### UI

```
add button: "processed" after "room" in source selector
style same as ref/room buttons
highlight when selected
```

### metering

```
// processed already works via existing source mechanism
// just needs to be added to compare dropdown options
add 'processed' to compare source dropdown
```
