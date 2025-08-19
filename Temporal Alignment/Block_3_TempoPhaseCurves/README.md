# Block 3 — Derive Tempo & Phase from the Time Map

This module computes the tempo curve (BPM over performance time) and in-node phase φ (0..1 within each node/beat) using D_beats from the ScoreGraph. These signals provide analytics and support rubato-tolerant tracking.

## References
- Partitura (metric utilities / note arrays): https://github.com/CPJKU/partitura
- Docs: https://partitura.readthedocs.io/en/latest/Tutorial/notebook.html

## Inputs
- `time_map.json` (from Block 2)
- `scoregraph.json` (from Block 0)

## Outputs
- `tempo_curve.csv` (columns: abs_beat,bpm)
- `phase_curve.csv` (columns: abs_beat,phi)
- (optional) `diagnostics.png` (tempo vs. abs_beat plot)

## How to Run
1. Install dependencies:
   ```powershell
   pip install partitura matplotlib
   ```
2. Place your input files in this folder.
3. Run the script:
   ```powershell
   python derive_curves.py --timemap time_map.json --scoregraph scoregraph.json
   ```

## Validation
- Recomputes the tempo curve two ways (finite differences on the time map vs. note IOIs from MATCH); the curves should agree within a few BPM except at boundaries.

---
This implementation is based on the logic and algorithms from the [Partitura](https://github.com/CPJKU/partitura) repository.
