# Block 0 — Build the ScoreGraph

This module parses MusicXML/MIDI and creates a canonical, linearized score timeline with bars, beats, and node durations. It expands repeats/voltas and attaches flags (fermatas/cadences) from XML or JSONs. The output is `scoregraph.json`.

## References
- Partitura (MusicXML/MIDI I/O & alignment utilities): https://github.com/CPJKU/partitura
- Docs: https://partitura.readthedocs.io/en/latest/Tutorial/notebook.html

## Inputs
- `score.musicxml` or `score.mid`
- `score_meta.json` (meter, key, tuning Hz, optional fermatas/cadences)
- (optional) `segmentation.json` (if it includes structural cues)

## Outputs
- `scoregraph.json` with:
  - bars: list of bars with time signatures and downbeat absolute beat
  - nodes: list of nodes with fields: id, bar, beat, abs_beat, D_beats, flags
  - tempo_marks, key_signature, tuning_hz
  - maps: definitions for (bar,beat) ↔ abs_beat

## How to Run
1. Install dependencies:
   ```powershell
   pip install partitura
   ```
2. Place your input files in this folder.
3. Run the script:
   ```powershell
   python build_scoregraph.py --score score.musicxml --meta score_meta.json [--seg segmentation.json]
   ```

## Validation
- Prints the first 10 nodes from the scoregraph for verification.

---
This implementation is based on the logic and algorithms from the [Partitura](https://github.com/CPJKU/partitura) repository.
