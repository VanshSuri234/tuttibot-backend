# Block 2 — Symbolic ↔ Symbolic Alignment (Score vs. Transcribed Performance)

This module aligns the score (MusicXML/MIDI) to the transcribed performance (MIDI from AMT) at the note level, producing precise correspondences and a dense time map. It uses Parangonar and Partitura for alignment and file I/O.

## References
- Parangonar: https://github.com/sildater/parangonar
- Parangonada (optional): https://github.com/sildater/parangonada
- Partitura: https://github.com/CPJKU/partitura

## Inputs
- `score.musicxml` or `score.mid`
- `scoregraph.json` (from Block 0)
- `perf.mid` (from Block 1)

## Outputs
- `alignment.match` (standard MATCH format: note↔note links)
- `time_map.json` — dense list of pairs: {"method":"Parangonar.DualDTWNoteMatcher","path":[[score_abs_beat,perf_time_sec],...],"hop_sec":0.01}

## How to Run
1. Install dependencies:
   ```powershell
   pip install partitura parangonar
   ```
2. Place your input files in this folder.
3. Run the script:
   ```powershell
   python align_symbolic.py --score score.musicxml --scoregraph scoregraph.json --perf perf.mid
   ```

## Validation
- Produces `alignment.match` and `time_map.json`.
- Plots 30 random matched notes to confirm alignment.

---
This implementation is based on the logic and algorithms from the [Parangonar](https://github.com/sildater/parangonar) and [Partitura](https://github.com/CPJKU/partitura) repositories.
