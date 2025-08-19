# Block 4 — Beat & Downbeat from Audio

This module extracts beat and downbeat times from the performance audio for diagnostics, visualizations, and gating re-locks. You can use BeatNet or madmom for this task.

## References
- BeatNet: https://github.com/mjhydri/BeatNet
- madmom: https://github.com/CPJKU/madmom

## Inputs
- `perf.wav` (44.1 kHz)

## Outputs
- `beats.json`: [{"t":12.345,"downbeat":1}, {"t":13.625,"downbeat":0}, ...]
- (optional) `activations.h5` (madmom’s ~100 fps probabilities)

## How to Run (BeatNet example)
1. Install dependencies:
   ```powershell
   pip install beatnet
   ```
2. Place your `perf.wav` file in this folder.
3. Run the script:
   ```powershell
   python estimate_beats.py --audio perf.wav
   ```

## Validation
- Overlay `beats.json` on the time map and check that downbeats align near bar downbeats from `scoregraph.json`.
- Report average deviation in ms and in beats.

---
This implementation is based on the logic and algorithms from the [BeatNet](https://github.com/mjhydri/BeatNet) repository.
