# Temporal Alignment System — Blocks 0, 1, and 2

## Overview

This subsystem synchronizes symbolic scores with audio performances in three steps: Block 0 builds a linearized ScoreGraph from MusicXML/MIDI with repeats expanded; Block 1 transcribes performance audio to symbolic notes; Block 2 aligns score and performance symbolically to produce a dense time map used by downstream analysis.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐
│   Block 0       │    │   Block 1       │    │         Block 2         │
│  ScoreGraph     │    │     AMT         │    │  Symbolic↔Symbolic DTW  │
│   Builder       │    │ (Audio→MIDI)    │    │   (Score vs. Perf)      │
└─────────────────┘    └─────────────────┘    └─────────────────────────┘
        │                       │                        │
        ▼                       ▼                        ▼
   scoregraph.json        transcription.json     alignment_results.json
                                              + time_map.json (dense)
```

Integration points in `main_hybrid_v02.py` call these blocks after preprocessing. See also `Temporal Alignment/integrate_temporal_alignment.md` for a minimal driver.

---

## Block 0 — ScoreGraph Builder

Purpose
- Parse MusicXML/MIDI and produce a canonical, linearized beat timeline with repeat expansion and optional structural flags (fermatas/cadences).

Inputs
- `score.musicxml` or `score.mid`
- `score_meta.json` (meter, key, tuning Hz, optional flags)
- Optional: `segmentation.json`

Outputs
- `scoregraph.json` with bars, nodes, tempo marks, and maps (bar,beat) ↔ abs_beat. Many flows also include `musical_notes` with note-level pitch, onset, duration in seconds.

How to run
```bash
cd "Temporal Alignment/Block_0_ScoreGraph"
python3 build_scoregraph_with_repeats.py --score test_with_repeats.musicxml --meta score_meta.json
```

Data schema (excerpt)
```json
{
  "bars": [{"bar":1, "time_sig":"4/4", "downbeat_abs_beat":0.0}],
  "nodes": [{"id":"1_1","bar":1,"beat":1,"abs_beat":0.0,"D_beats":1.0,"flags":[]}],
  "tempo_marks": [{"beat":0,"bpm":120}],
  "maps": {"bar_beat_to_abs_beat": {"1,1": 0.0}}
}
```

Math (repeat expansion and timing)
- Absolute beat for bar b, local beat β: abs_beat(b,β) = downbeat_abs_beat(b) + (β−1).
- Time from beat via tempo curve T(β) in BPM sampled at node i with duration Δβ_i:
  t = ∑_i Δβ_i · 60 / T_i. With constant tempo T, t(β) = β · 60/T.
- Repeat expansion transforms the written measure list M into an expanded performance sequence 𝕄 by applying XML directives (repeat, endings, D.C./D.S.). See `REPEAT_EXPANSION_EXPLANATION.md`.

---

## Block 1 — Automatic Music Transcription (AMT)

Purpose
- Convert performance audio into symbolic note events using Basic Pitch; output standardized JSON and MIDI for alignment.

Inputs/Outputs
- Input: `perf.wav` (44.1 kHz recommended)
- Output: `output/<stem>_basic_pitch.mid`, `output/<stem>_basic_pitch.csv`, and `transcription.json` (normalized note list)

How to run
```bash
cd "Temporal Alignment/Block_1_AMT"
python3 transcribe_audio_fixed.py --audio perf.wav --output-dir output --json-output transcription.json
```

Transcription JSON (excerpt)
```json
{
  "notes": [{"onset_time":0.12,"offset_time":0.80,"duration":0.68,"pitch_midi":72,"velocity":73}],
  "metadata": {"transcription_method":"basic_pitch_cli","total_notes":123}
}
```

Notes
- Uses the Basic Pitch CLI for stability; robust parsing handles malformed CSV rows; integrates GPU if available via `gpu_manager`.

---

## Block 2 — Symbolic ↔ Symbolic Alignment

Purpose
- Align score (from Block 0) and performance (from Block 1) at high resolution using DTW over chroma features; produce a dense time map and quality metrics.

Two implementations
- Reference (external): Partitura + Parangonar (`align_symbolic.py`).
- Lightweight (in-repo): PrettyMIDI + librosa DTW (`align_symbolic_enhanced.py`).

Inputs
- `Block_0_ScoreGraph/scoregraph.json`
- `Block_1_AMT/output/<stem>_basic_pitch.mid` or `transcription.json`→MIDI

Outputs
- `block_2_enhanced_output/enhanced_alignment_complete.json` (warping path, metrics)
- `block_2_enhanced_output/alignment_results.json` and `alignment_visualization.png`
- Optionally: `time_map.json` (dense pairs [score_time, perf_time])

How to run (enhanced aligner)
```bash
cd "Temporal Alignment/Block_2_SymbolicAlignment"
python3 align_symbolic_enhanced.py ../Block_0_ScoreGraph/scoregraph.json ../Block_1_AMT/output/<stem>_basic_pitch.mid -o block_2_enhanced_output
```

Mathematical formulation
- Feature construction: derive 12-D chroma sequences X ∈ R^{12×N} (score) and Y ∈ R^{12×M} (performance) by synthesis→CQT or piano-roll chroma. Columns are ℓ2-normalized.
- Local cost (default cosine distance): c(i,j) = 1 − ⟨x_i, y_j⟩ / (||x_i||·||y_j||).
  - Optional transposition invariance: c_tr(i,j) = 1 − max_{τ∈{0..11}} ⟨x_i, S_τ y_j⟩ / (||x_i||·||y_j||), where S_τ circularly shifts chroma by τ.
- DTW recurrence with monotonicity and continuity:
  D(i,j) = c(i,j) + min{ D(i−1,j), D(i,j−1), D(i−1,j−1) }, with D(0,0)=c(0,0).
  Backtracking yields warping path w = {(i_k,j_k)}_k.
- Band constraint (Sakoe–Chiba) for tempo stability: | i − α j | ≤ w, where α is global tempo ratio estimate and w a half-width; improves robustness and speed.
- Time map: map frames to seconds by t_score(i) = i·H/sr and t_perf(j) = j·H/sr; the final dense map is {(t_score(i_k), t_perf(j_k))}.

Quality metrics
- DTW distance D(N,M); mean cosine similarity along path; local tempo ratio r_k = Δt_perf/Δt_score; visualization compares path vs diagonal.

---

## End-to-end usage

```bash
# Block 0
cd "Temporal Alignment/Block_0_ScoreGraph"
python3 build_scoregraph_with_repeats.py --score test_with_repeats.musicxml --meta score_meta.json

# Block 1
cd "../Block_1_AMT"
python3 transcribe_audio_fixed.py --audio perf.wav --output-dir output --json-output transcription.json

# Block 2
cd "../Block_2_SymbolicAlignment"
python3 align_symbolic_enhanced.py ../Block_0_ScoreGraph/scoregraph.json ../Block_1_AMT/output/perf_basic_pitch.mid -o block_2_enhanced_output
```

## References
- Partitura: https://github.com/CPJKU/partitura
- Parangonar: https://github.com/sildater/parangonar
- PrettyMIDI: https://github.com/craffel/pretty-midi
- Librosa: https://github.com/librosa/librosa
- Basic Pitch: https://github.com/spotify/basic-pitch
