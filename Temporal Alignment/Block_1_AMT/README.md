# Block 1: Automatic Music Transcription (AMT)

This block handles automatic transcription of audio to MIDI and structured note events using Basic Pitch.

## 📁 Final File Structure

```
Block_1_AMT/
├── transcribe_audio.py         # Original basic version
├── transcribe_audio_fixed.py   # Final working version ✅
├── README.md                   # This documentation
├── test_audio.wav             # Test audio file
├── transcription.json         # Sample output
└── output/                    # Basic Pitch output directory
    ├── test_audio_basic_pitch.mid
    └── test_audio_basic_pitch.csv
```

## 🎯 Which File to Use

**Use `transcribe_audio_fixed.py`** - This is the final working version that:
- ✅ Works end-to-end reliably
- ✅ Uses Basic Pitch CLI for stability
- ✅ Handles malformed data gracefully
- ✅ Outputs standardized JSON format
- ✅ Includes comprehensive error handling

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
