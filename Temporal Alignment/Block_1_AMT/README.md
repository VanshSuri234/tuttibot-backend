# Block 1 — AMT: Audio to Symbolic (MIDI) for the Performance

This module transcribes performance audio (`perf.wav`) into symbolic note events (MIDI and JSON). You can choose from several open-source AMT models. For general instruments, Basic Pitch is recommended; for piano, Onsets & Frames; for multi-instrument, Omnizart.

## References
- Basic Pitch: https://github.com/spotify/basic-pitch
- Onsets & Frames: https://github.com/magenta/magenta/blob/master/magenta/models/onsets_frames_transcription/README.md
- Omnizart: https://github.com/Music-and-Culture-Technology-Lab/omnizart

## Inputs
- `perf.wav` (44.1 kHz, mono/stereo)

## Outputs
- `perf.mid` (transcribed MIDI)
- `perf_notes.json` (optional: array of {"pitch","onset_sec","offset_sec","velocity"})

## How to Run (Basic Pitch example)
1. Install dependencies:
   ```powershell
   pip install basic-pitch
   ```
2. Place your `perf.wav` file in this folder.
3. Run the script:
   ```powershell
   python transcribe_audio.py --audio perf.wav
   ```

## Validation
- Lists the first 20 events sorted by onset.
- Checks that tuning roughly matches `score_meta.json["tuning_hz"]` (±10 cents).

---
This implementation is based on the logic and algorithms from the [Basic Pitch](https://github.com/spotify/basic-pitch) repository.
