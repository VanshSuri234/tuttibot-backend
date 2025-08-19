# Temporal Alignment Integration (Block 0 + Block 1)

This script demonstrates the integration of Block 0 (ScoreGraph builder) and Block 1 (AMT transcription) for temporal alignment. It takes the required inputs, runs both blocks in sequence, and prints the outputs for verification.

## Usage
1. Ensure all dependencies are installed:
   ```powershell
   pip install partitura basic-pitch
   ```
2. Place your input files in the appropriate folders:
   - `score.musicxml` (or `score.mid`)
   - `score_meta.json`
   - `perf.wav`
3. Run the script:
   ```powershell
   python integrate_temporal_alignment.py --score <score_path> --meta <meta_path> --audio <audio_path>
   ```

---
This is a minimal integration for temporal alignment. Full pipeline integration will be implemented later.
