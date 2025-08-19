# Block 5 — Online (Real-Time) Follower Prototype, CPU-Only

This module runs online time warping (OTW) for audio or an HMM follower for MIDI using Matchmaker. It returns current score position in beats per frame and can simulate real-time from a file. No GPU or external API required.

## References
- Matchmaker: https://github.com/pymatchmaker/matchmaker
- Docs: https://pymatchmaker.readthedocs.io/

## Inputs
- `score.musicxml` or `score.mid`
- `perf.wav` (simulated streaming) or an actual audio/MIDI stream

## Outputs
- `online_trace.csv`: time_sec,score_abs_beat,bar,beat,conf

## How to Run
1. Install dependencies:
   ```powershell
   pip install matchmaker
   ```
2. Place your input files in this folder.
3. Run the script:
   ```powershell
   python follow_online_sim.py --score score.musicxml --audio perf.wav
   ```

## Validation
- Compares the online path to `time_map.json` (from Block 2).
- Computes mean absolute error in beats; adds a simple re-lock rule when error > threshold.

---
This implementation is based on the logic and algorithms from the [Matchmaker](https://github.com/pymatchmaker/matchmaker) repository.
