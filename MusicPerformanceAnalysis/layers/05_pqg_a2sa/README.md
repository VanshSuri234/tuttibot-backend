# PQG-A2SA: Performance Quantification Guided Audio-to-Score Alignment

Complete Python implementation of **PQG-A2SA** (Lian–Cheng–Zhang, 2023) for orchestral music alignment.

## 📄 Paper Reference

> Zhicheng Lian, Haonan Cheng, and Jiawan Zhang, "PQG-A2SA: Performance Quantification Guided Audio-to-Score Alignment for Orchestral Music," IEEE/ACM TASLP, vol. 31, 2023.

## 🎯 What is PQG-A2SA?

PQG-A2SA aligns **multi-instrument orchestral scores** to **single ensemble audio recordings** at the **note level**, estimating precise onset and offset times for every note across all instruments. Unlike traditional methods, it handles:

- ✅ Multi-instrument complexity
- ✅ Tempo variations and deviations
- ✅ Articulation differences (staccato vs legato)
- ✅ Soft onsets and offsets
- ✅ Single ensemble mix (no separated stems required)

## 🏗️ Architecture Overview

The pipeline consists of 6 stages:

```
1. Audio Features → CQT chroma (23ms hop) + Temporal clustering
2. Score Parsing → Chord sequences + Per-instrument notes
3. VIDTW → Coarse chord-level alignment (tempo-free)
4. IOI-GM → Refine tempo deviations using Inter-Onset Intervals
5. Score-Informed NMF → Per-instrument/pitch activations from ensemble mix
6. Articulation → Note-level onset/offset refinement (staccato/legato)
```

### Key Innovations

- **Variable-Interval DTW (VIDTW)**: Tempo-free alignment by clustering audio frames
- **IOI-Guided Modification (IOI-GM)**: Local re-alignment of tempo deviations
- **Score-Informed NMF**: Extract per-instrument evidence from ensemble without hard separation
- **Articulation Detection**: Staccato vs legato rules for precise note boundaries

## 📦 Installation

```bash
# Clone or download this repository
cd pqg_a2sa

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

- `librosa`: Audio feature extraction (CQT, chroma)
- `pretty_midi`: MIDI score parsing
- `scikit-learn`: NMF decomposition
- `mir_eval`: Evaluation metrics
- `numpy`, `scipy`: Scientific computing

## 🚀 Quick Start

### Basic Usage

```python
from src.pipeline import PQGAligner

# Initialize aligner
aligner = PQGAligner()

# Align audio to score
results = aligner.align(
    audio_path="your_performance.wav",
    midi_path="your_score.mid",
    verbose=True
)

# Access refined note timings
for inst in results['instruments']:
    print(f"{inst['name']}: {len(inst['notes'])} notes")
    for note in inst['notes']:
        print(f"  Pitch {note['pitch']}: "
              f"onset={note['onset']:.3f}s, "
              f"offset={note['offset']:.3f}s, "
              f"articulation={note['articulation']}")
```

### Run Example

```bash
# Place your audio and MIDI files in data/
python example.py
```

## 📊 Default Parameters

All parameters are configurable in `src/config.py`:

```python
# Audio features
HOP_LENGTH = 1024      # ~23ms at 44.1kHz
N_CHROMA = 12          # 12 pitch classes

# VIDTW
K_CL = 10              # Clusters per chord

# IOI-GM
IOI_DELTA = 4          # ±4 chords for local velocity
R_LOW = 0.6            # Deviation thresholds
R_HIGH = 1.67

# NMF
NMF_ITERATIONS = 150
ONSET_TOLERANCE_MS = 150
OFFSET_TOLERANCE_MS = 200

# Articulation
K_REST = 0.15          # Rest detection
T_S_MS = 150           # Staccato gap minimum
T_L_MS = 30            # Legato window
```

## 📁 Project Structure

```
pqg_a2sa/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration parameters
│   ├── features.py           # Audio feature extraction
│   ├── score_parser.py       # MIDI/score parsing
│   ├── vidtw.py              # Variable-Interval DTW
│   ├── ioi_gm.py             # IOI-Guided Modification
│   ├── nmf.py                # Score-informed NMF
│   ├── articulation.py       # Articulation detection
│   ├── evaluation.py         # Metrics (MNE, MFE)
│   └── pipeline.py           # Main orchestrator
├── tests/                    # Unit tests
├── data/                     # Input audio/MIDI files
├── results/                  # Output alignments
├── requirements.txt          # Dependencies
├── example.py                # Usage example
└── README.md                 # This file
```

## 🔬 Evaluation Metrics

The implementation provides:

- **MNE** (Mean Note Error): Average onset error in milliseconds
- **MFE** (Mean Frame Error): Average offset error in milliseconds
- **Alignment Rates**: Percentage of notes aligned within thresholds (30, 60, 90, ..., 200 ms)

```python
# Evaluate against ground truth
evaluation = aligner.evaluate(results, ground_truth_notes)
print(f"MNE: {evaluation['overall']['MNE']*1000:.2f} ms")
print(f"MFE: {evaluation['overall']['MFE']*1000:.2f} ms")
```

## 🧪 Testing with Bach10 Dataset

The paper uses the **Bach10 Dataset** (Duan & Pardo) for evaluation:

```python
# Example test on Bach10
audio_path = "Bach10/01-AchGottundHerr/01-AchGottundHerr.wav"
midi_path = "Bach10/01-AchGottundHerr/01-AchGottundHerr.mid"

results = aligner.align(audio_path, midi_path)
```

## 🎓 How It Works (Detailed)

### Stage 1: Feature Extraction
- Load ensemble audio
- Compute CQT-based chroma (12-D per frame, ~23ms hop)
- Temporal clustering: merge similar adjacent frames → ~10× number of chords

### Stage 2: Score Parsing
- Extract chord sequence (notes with simultaneous onsets)
- Extract per-instrument note lists
- Compute 12-D chroma per chord

### Stage 3: VIDTW (Coarse Alignment)
- DTW between score chord chromas and audio cluster chromas
- Tempo-free: ignores duration, aligns based on harmony
- Output: preliminary chord onset times

### Stage 4: IOI-GM (Refinement)
- Compute per-chord velocity: `v_i = Δt / Δl`
- Compute local average velocity over ±4 chords
- Detect deviants: ratio outside [0.6, 1.67]
- Re-align deviated segments with duration constraints

### Stage 5: Score-Informed NMF
- Build template matrix `W`: one column per (instrument, pitch)
- Initialize activations `H` using refined chord times (±150/200ms)
- Decompose: `V ≈ W·H` (150 iterations)
- Extract per-instrument/pitch activations from ensemble mix

### Stage 6: Articulation Refinement
For each consecutive note pair `(α → β)`:
- Compute sum signal `H_s = H_α + H_β`
- Compute difference signal `H_d = H_α - H_β`
- **Staccato**: detect rest gap → find offset before gap, onset after gap
- **Legato**: find zero-crossing in `H_d` → find offset near onset

## 🔧 Advanced Usage

### Custom Configuration

```python
from src.config import PQGConfig

# Customize parameters
config = PQGConfig()
config.K_CL = 15               # More clusters
config.NMF_ITERATIONS = 200    # More NMF iterations
config.IOI_DELTA = 6           # Wider IOI window

aligner = PQGAligner(config)
```

### Access Intermediate Results

```python
results = aligner.align(audio_path, midi_path)

# Intermediate data
intermediate = results['intermediate']
audio_chroma = intermediate['audio_chroma']
cluster_chroma = intermediate['cluster_chroma']
chord_onsets_preliminary = intermediate['chord_onsets_preliminary']
spectrogram = intermediate['spectrogram']
H = intermediate['H']  # NMF activations
```

## 📚 Implementation Details

### Temporal Clustering
- Agglomerative clustering with **temporal constraint**
- Only adjacent frames can merge (preserves time order)
- Target: `L_cluster = ceil(k_cl * L_chord)` where `k_cl=10`

### DTW Cost Function
```
D(x, y) = d(x, y) + min{D(x, y-1), D(x-1, y-1)}
```
- Horizontal: audio slower than score
- Diagonal: synchronized advance

### NMF Update Rule
```
H ← H ⊙ (W^T V) / (W^T W H + ε)
```
- Multiplicative update with fixed W
- 150 iterations (paper default)

### Articulation Thresholds
- Rest detection: `H_s < 0.15 * (e_α + e_β)` for ≥150ms
- Staccato offset: `H_α > 0.65 * e_α` closest to rest
- Staccato onset: `H_β > 0.2 * e_β` after rest
- Legato: zero-crossing in `H_d`, local max in `H_s`

## 🐛 Troubleshooting

### Import errors
Make sure you're running from the project root:
```bash
python example.py  # Not: python src/example.py
```

### Missing dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Poor alignment results
- Check tempo: extreme tempo changes may need larger `IOI_DELTA`
- Check audio quality: noisy recordings affect chroma
- Check score accuracy: mismatched pitches will fail

## 📖 Citation

If you use this implementation, please cite the original paper:

```bibtex
@article{lian2023pqga2sa,
  title={PQG-A2SA: Performance Quantification Guided Audio-to-Score Alignment for Orchestral Music},
  author={Lian, Zhicheng and Cheng, Haonan and Zhang, Jiawan},
  journal={IEEE/ACM Transactions on Audio, Speech, and Language Processing},
  volume={31},
  year={2023}
}
```

## 📜 License

This implementation is for research and educational purposes. Refer to the original paper for algorithmic details.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Real instrument harmonic templates (instead of synthetic)
- Music21 support for MusicXML scores
- Visualization tools for alignment results
- Batch processing utilities
- GPU acceleration for NMF

## 📧 Contact

For questions or issues, please open a GitHub issue or refer to `PQG-A2SA_detailed_notes.txt` for comprehensive algorithm details.

---

**Built with ❤️ based on PQG-A2SA (Lian-Cheng-Zhang, 2023)**
