# Block 6 — Rubato Tolerance + Auto Re-lock Logic

This module uses segmentation and beat information to define per-beat tolerance masks and perform local, coarse DTW re-locks when confidence drops. SyncToolbox is used for efficient DTW and quick relocks.

## References
- SyncToolbox: https://github.com/meinardmueller/synctoolbox
- DTW API: https://meinardmueller.github.io/synctoolbox/build/html/dtw.html

## Inputs
- `segmentation.json`
- `beats.json` (optional)
- `online_trace.csv` (from Block 5, if streaming)

## Outputs
- `online_trace_stabilized.csv` (with fewer large jumps; “re-locks” near downbeats)

## How to Run
1. Install dependencies:
   ```powershell
   pip install synctoolbox
   ```
2. Place your input files in this folder.
3. Run the script:
   ```powershell
   python tolerance_and_relock.py --seg segmentation.json --beats beats.json --trace online_trace.csv
   ```

## Validation
- Inject synthetic pauses/jumps in a test run; verify re-lock occurs within ≤2 bars, preferably on a downbeat.

---
This implementation is based on the logic and algorithms from the [SyncToolbox](https://github.com/meinardmueller/synctoolbox) repository.
