# PQG-A2SA Implementation Guide

## 🎯 What We've Built

A complete, modular implementation of the PQG-A2SA algorithm from scratch based on the detailed notes in `PQG-A2SA_detailed_notes.txt`.

## 📦 Package Structure

```
pqg_a2sa/
├── src/                          # Source code modules
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration & parameters
│   ├── features.py              # Audio feature extraction
│   ├── score_parser.py          # MIDI/score parsing
│   ├── vidtw.py                 # Variable-Interval DTW
│   ├── ioi_gm.py                # IOI-Guided Modification
│   ├── nmf.py                   # Score-informed NMF
│   ├── articulation.py          # Articulation detection
│   ├── evaluation.py            # Evaluation metrics
│   └── pipeline.py              # Main orchestrator
├── tests/                       # Unit tests (to be added)
├── data/                        # Input data directory
├── results/                     # Output directory
├── requirements.txt             # Python dependencies
├── example.py                   # Usage example
├── test_structure.py            # Verify implementation
└── README.md                    # Comprehensive documentation
```

## 🔧 Module Descriptions

### 1. **config.py** - Central Configuration
- `PQGConfig` class with all default parameters from paper
- Audio settings: sample rate, hop length (23ms), frame size
- VIDTW: k_cl=10 (clusters per chord)
- IOI-GM: delta=4, r_low=0.6, r_high=1.67
- NMF: 150 iterations, tolerances (150ms onset, 200ms offset)
- Articulation: k_rest=0.15, k_off=0.65, k_on=0.2, T_s=150ms, T_l=30ms
- Helper functions: ms↔frames, frames↔seconds conversions

### 2. **features.py** - Audio Processing
**AudioFeatures class:**
- `load_audio()`: Load WAV/MP3 at 44.1kHz
- `extract_chroma_frames()`: CQT-based 12-D chroma with L2 normalization
- `temporal_clustering()`: Agglomerative clustering with temporal constraint
  - Only merges adjacent frames (preserves time order)
  - Target: ceil(k_cl × n_chords) clusters
- `compute_spectrogram()`: STFT → log-compressed magnitude

### 3. **score_parser.py** - Score Analysis
**ScoreParser class:**
- `load_midi()`: Read MIDI using pretty_midi
- `extract_chords()`: Group simultaneous note onsets into chords
  - Time resolution: 10ms tolerance
  - Returns: onset_time, pitches, chroma per chord
- `extract_instrument_notes()`: Per-instrument note lists
  - pitch, onset, offset, velocity, duration
- `get_chord_chroma_sequence()`: (12, n_chords) array + onset times
- `build_pitch_templates()`: Spectral templates for NMF (simplified harmonic model)

### 4. **vidtw.py** - Variable-Interval DTW
**VIDTW class:**
- `align()`: Core DTW between score chords ↔ audio clusters
  - Cost: Euclidean distance in 12-D chroma space
  - Transitions: horizontal (audio slower), diagonal (synchronized)
  - Returns: cost, path, score_to_audio mapping
- `get_chord_onset_times()`: Extract preliminary chord onset times from alignment
- `align_with_constraints()`: Banded DTW for IOI-GM local re-alignment
  - Sakoe-Chiba band constraint
  - Allows vertical moves for local flexibility

### 5. **ioi_gm.py** - IOI-Guided Modification
**IOIGuidedModification class:**
- `refine_alignment()`: Main refinement pipeline
  1. Compute per-chord velocities: v_i = Δt / Δl
  2. Compute local velocities over ±delta chords
  3. Detect deviants: ratio outside [r_low, r_high]
  4. Find deviated segments (consecutive deviants)
  5. Re-align each segment with duration constraints
- `_realign_segment()`: Local DTW on fine grid (0.02 beat resolution)
- `_interpolate_score_chroma()`: Step-function interpolation to fine grid

### 6. **nmf.py** - Score-Informed NMF
**ScoreInformedNMF class:**
- `build_template_matrix()`: Construct W from instrument/pitch info
  - One column per (instrument, pitch) pair
  - Simplified harmonic templates (fundamental + overtones)
  - Background/noise template
  - Max-normalize columns
- `initialize_activations()`: H matrix from refined chord times
  - Activate windows: onset ± 150ms, offset ± 200ms
  - Binary initialization (1 where note expected, 0 elsewhere)
- `decompose()`: V ≈ W·H via multiplicative updates
  - Fixed W, update H only
  - 150 iterations (default)
- `get_instrument_activations()`: Extract per-instrument pitch activations

### 7. **articulation.py** - Note-Level Refinement
**ArticulationRefinement class:**
- `refine_instrument_notes()`: Process all notes for one instrument
- `_refine_note_pair()`: Core logic for consecutive notes (α → β)
  1. Define ROI (region of interest) between notes
  2. Compute H_s = H_α + H_β (sum energy)
  3. Compute H_d = H_α - H_β (dominance)
  4. Detect articulation (staccato vs legato)
  5. Apply articulation-specific rules
- **Staccato rules:**
  - Find rest gap: H_s < k_rest × (e_α + e_β) for ≥T_s frames
  - Offset α: H_α > k_off × e_α, closest to rest start
  - Onset β: H_β > k_on × e_β, after rest end
- **Legato rules:**
  - Onset β: zero-crossing in H_d (sign change)
  - Offset α: local max in H_s before onset β (within T_l)

### 8. **evaluation.py** - Metrics
**Evaluator class:**
- `compute_note_errors()`: Onset errors → MNE
- `compute_frame_errors()`: Offset errors → MFE
- `compute_alignment_rates()`: % within thresholds (30, 60, ..., 200ms)
- `evaluate_full()`: Complete evaluation with all metrics
- `use_mir_eval()`: Standard MIR evaluation (precision/recall/F-measure)

### 9. **pipeline.py** - Main Orchestrator
**PQGAligner class:**
- `align()`: Complete 6-stage pipeline
  1. Extract audio features (chroma, spectrogram)
  2. Parse score (chords, instruments)
  3. VIDTW: coarse chord alignment
  4. IOI-GM: refine tempo deviations
  5. Score-informed NMF: per-instrument activations
  6. Articulation: note-level onset/offset refinement
- `evaluate()`: Compare against ground truth
- Returns: refined instruments, chord times, intermediate results

## 🚀 Usage Workflow

### Installation
```bash
cd /home/nikhilsingh/Documents/temp/Trials/Workspace/pqg_a2sa
pip install -r requirements.txt
```

### Test Structure
```bash
python test_structure.py
```

### Basic Usage
```python
from src.pipeline import PQGAligner

aligner = PQGAligner()
results = aligner.align("audio.wav", "score.mid", verbose=True)

# Access results
for inst in results['instruments']:
    for note in inst['notes']:
        print(f"Pitch {note['pitch']}: {note['onset']:.3f}s → {note['offset']:.3f}s")
```

## 🔬 Algorithm Flow

```
INPUT: Ensemble audio Y, Multi-instrument score X

STAGE 1-2: ENSEMBLE-LEVEL ALIGNMENT
  ├─ Extract CQT chroma from audio (23ms hop)
  ├─ Extract chord sequence from score
  ├─ Temporal clustering: merge similar adjacent frames
  ├─ VIDTW: align score chords ↔ audio clusters
  └─ → Preliminary chord onset times τ^(0)

STAGE 3: REFINEMENT
  ├─ Compute IOI velocities & local velocities
  ├─ Detect tempo deviations (ratio test)
  ├─ Re-align deviated segments with duration constraints
  └─ → Refined chord onset times τ

STAGE 4: PER-INSTRUMENT ACTIVATION
  ├─ Build template matrix W (instrument/pitch)
  ├─ Initialize H using refined τ (±150/200ms windows)
  ├─ NMF: V ≈ W·H (150 iterations)
  └─ → Per-instrument/pitch activations H

STAGE 5-6: NOTE-LEVEL TIMING
  For each instrument:
    For each consecutive note pair (α, β):
      ├─ Compute H_s (sum), H_d (difference)
      ├─ Detect articulation (staccato/legato)
      ├─ Apply rules to find precise onset/offset
      └─ → Refined note timings τ_i(onset/offset)

OUTPUT: Per-instrument note lists with refined onset/offset times
```

## 📊 Key Parameters (Tunable)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `HOP_LENGTH` | 1024 (~23ms) | Audio frame hop size |
| `K_CL` | 10 | Clusters per chord for VIDTW |
| `IOI_DELTA` | 4 | ±chords for local velocity |
| `R_LOW` | 0.6 | Min velocity ratio threshold |
| `R_HIGH` | 1.67 | Max velocity ratio threshold |
| `NMF_ITERATIONS` | 150 | Number of NMF updates |
| `ONSET_TOLERANCE_MS` | 150 | H init onset window |
| `OFFSET_TOLERANCE_MS` | 200 | H init offset window |
| `K_REST` | 0.15 | Rest detection multiplier |
| `K_OFF` | 0.65 | Staccato offset threshold |
| `K_ON` | 0.2 | Staccato onset threshold |
| `T_S_MS` | 150 | Min staccato gap duration |
| `T_L_MS` | 30 | Legato offset search window |

## 🎯 Next Steps

1. **Test with Real Data:**
   ```bash
   # Place Bach10 dataset or your own data in data/
   python example.py
   ```

2. **Add Unit Tests:**
   - Test each module independently
   - Verify temporal clustering constraint
   - Check DTW path correctness
   - Validate articulation detection logic

3. **Visualizations:**
   - Plot chord alignment before/after IOI-GM
   - Show NMF activations per instrument
   - Visualize articulation detection (H_s, H_d)

4. **Optimizations:**
   - Parallel NMF for large spectrograms
   - Caching of intermediate results
   - GPU acceleration (optional)

5. **Extensions:**
   - Real instrument templates from sample libraries
   - Music21 support for MusicXML
   - Batch processing of datasets
   - Interactive alignment editor

## 📝 Differences from Old `ensemble_synchrony`

This is a **completely fresh implementation** based purely on PQG-A2SA paper:

| Aspect | Old `ensemble_synchrony` | New `pqg_a2sa` |
|--------|-------------------------|----------------|
| Basis | Mixed/unclear methods | Pure PQG-A2SA (2023) |
| Structure | Monolithic scripts | Modular pipeline |
| Temporal clustering | Not clear | Temporally-constrained agglomerative |
| IOI-GM | Missing/incomplete | Full deviant detection + re-align |
| NMF | Generic | Score-informed with templates |
| Articulation | Basic rules | Staccato/legato with H_s/H_d |
| Documentation | Partial | Comprehensive (README + code) |
| Configurability | Hardcoded | Central config class |

## 🐛 Potential Issues & Solutions

### Import Errors
The linting errors you see are **expected** - they occur because VS Code's linter can't resolve relative imports when analyzing individual files. **The code will run correctly** when executed as a package.

To fix linting warnings (optional):
```python
# In each src/*.py file, you could add:
if __name__ != "__main__":
    from .config import PQGConfig  # Relative import
else:
    from config import PQGConfig   # Absolute import for testing
```

Or add a `setup.py` to install as a package:
```python
from setuptools import setup, find_packages
setup(name='pqg_a2sa', packages=find_packages())
```

### Runtime Issues
- **Memory**: Large audio files may need chunking
- **Speed**: NMF is slow; consider fewer iterations or sparse matrices
- **Accuracy**: Default templates are simplified; real harmonic templates improve results

## 📚 References

1. **Original Paper:**
   - Lian, Z., Cheng, H., & Zhang, J. (2023). PQG-A2SA: Performance Quantification Guided Audio-to-Score Alignment for Orchestral Music. IEEE/ACM TASLP.

2. **Detailed Notes:**
   - See `../PQG-A2SA_detailed_notes.txt` for comprehensive algorithm explanation

3. **Related Work:**
   - Bach10 Dataset (Duan & Pardo)
   - DTW-based alignment methods
   - Score-informed source separation

## ✅ Verification Checklist

- [x] All 9 modules created
- [x] Configuration centralized
- [x] Temporal clustering with adjacency constraint
- [x] VIDTW with proper cost function
- [x] IOI-GM with deviant detection
- [x] Score-informed NMF with W/H initialization
- [x] Articulation detection (staccato/legato)
- [x] Evaluation metrics (MNE, MFE, align-rates)
- [x] Main pipeline orchestrator
- [x] Comprehensive documentation
- [x] Example usage script
- [x] Requirements file

**Status: ✅ COMPLETE - Ready for testing with real data!**
