# Block 3: Pitch Evaluation System

**CPU-Optimized pitch accuracy evaluation for music performance grading**

## 📋 Overview

This module evaluates pitch accuracy by comparing musical scores with audio performances. It extracts pitches from both sources, compares them, and generates detailed grades with visualizations.

### Key Features

✅ **CPU-Friendly**: Uses `librosa.pyin` by default (no GPU required)  
✅ **Multiple Input Formats**: MusicXML, MIDI, WAV, MP3  
✅ **Comprehensive Metrics**: Cents error, accuracy percentages, grades  
✅ **Detailed Reports**: JSON, CSV, text summaries  
✅ **Visualizations**: Pitch curves, deviation plots, histograms  
✅ **Letter Grades**: A+ to F scale with feedback

---

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements_pitch.txt

# Or manually:
pip install music21 librosa numpy scipy matplotlib seaborn mir_eval soundfile
```

### Basic Usage

```bash
# Evaluate pitch accuracy
python evaluate_pitch.py \
    --score path/to/score.xml \
    --audio path/to/performance.wav \
    --output results/
```

### Output Structure

```
pitch_evaluation_20241102_143022/
├── EVALUATION_SUMMARY.txt          # Human-readable summary
├── evaluation_summary.json         # Complete results (JSON)
├── data/
│   ├── score_pitches.json         # Extracted score notes
│   ├── audio_pitches.json         # Extracted F0 from audio
│   └── comparison_results.json    # Detailed comparison
├── reports/
│   ├── pitch_grade.json           # Final grade + feedback
│   └── note_by_note_comparison.csv  # Spreadsheet data
└── visualizations/
    ├── 00_summary.png              # Overall summary
    ├── 01_pitch_curves.png         # Score vs audio F0
    ├── 02_deviation_over_time.png  # Cents error timeline
    ├── 03_deviation_histogram.png  # Distribution
    └── 04_accuracy_breakdown.png   # Category pie/bar charts
```

---

## 📊 Module Architecture

### Components

```
Block_3_PitchEvaluation/
├── __init__.py                     # Package initialization
├── requirements_pitch.txt          # Dependencies
├── README.md                       # This file
│
├── score_pitch_extractor.py       # Extract pitches from score
├── audio_pitch_extractor.py       # Extract F0 from audio (CPU)
├── pitch_comparator.py             # Compare & compute metrics
├── pitch_grader.py                 # Generate grades
├── pitch_visualizer.py             # Create plots
└── evaluate_pitch.py               # Main pipeline script
```

### Workflow

```
┌─────────────────┐
│  MusicXML/MIDI  │
│     Score       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ score_pitch_extractor   │──► Extract notes with:
│  (music21)              │    - MIDI pitch
└────────┬────────────────┘    - Frequency (Hz)
         │                     - Timing (onset/offset)
         │
         ▼
┌─────────────────────────┐
│  Audio Performance      │
│     (WAV/MP3)           │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ audio_pitch_extractor   │──► Extract F0 with:
│  (librosa pyin/CREPE)   │    - Frequency per frame
└────────┬────────────────┘    - Confidence scores
         │                     - Voiced/unvoiced
         │
         ▼
┌─────────────────────────┐
│   pitch_comparator      │──► Compute:
│  (cents error calc)     │    - Cents deviation
└────────┬────────────────┘    - Accuracy metrics
         │                     - Pass/fail rates
         │
         ▼
┌─────────────────────────┐
│   pitch_grader          │──► Generate:
│  (grading algorithm)    │    - Letter grade (A-F)
└────────┬────────────────┘    - Numeric score (0-100)
         │                     - Feedback text
         │
         ▼
┌─────────────────────────┐
│  pitch_visualizer       │──► Create:
│  (matplotlib/seaborn)   │    - Pitch curve plots
└─────────────────────────┘    - Deviation charts
                               - Summary figures
```

---

## 🔧 Detailed Usage

### 1. Score Pitch Extraction

```python
from score_pitch_extractor import ScorePitchExtractor

extractor = ScorePitchExtractor(reference_frequency=440.0)
extractor.load_score('score.xml')
notes = extractor.extract_notes()

# Access note data
for note in notes[:5]:
    print(f"{note.note_name}{note.octave}: {note.frequency_hz:.2f} Hz")

# Save to JSON
extractor.save_to_json('score_pitches.json')
```

### 2. Audio Pitch Extraction

```python
from audio_pitch_extractor import AudioPitchExtractor

# Use pYIN (fast, CPU-only, no dependencies)
extractor = AudioPitchExtractor(method='pyin')
extractor.load_audio('performance.wav')

# Optional: Check tuning
tuning = extractor.estimate_tuning()
print(f"Tuning offset: {tuning:+.2f} semitones")

# Extract pitch
frames = extractor.extract_pitch()

# Get pitch at specific time
freq = extractor.get_pitch_at_time(time=5.0, window=0.05)
print(f"Pitch at 5s: {freq:.2f} Hz")

# Save to JSON
extractor.save_to_json('audio_pitches.json')
```

### 3. Pitch Comparison

```python
from pitch_comparator import PitchComparator

comparator = PitchComparator(
    accuracy_threshold_cents=50.0,
    excellent_threshold_cents=25.0,
    good_threshold_cents=10.0
)

# Compare
comparisons = comparator.compare_notes(score_extractor, audio_extractor)

# Get metrics
metrics = comparator.get_metrics()
print(f"Mean error: {metrics['mean_absolute_cents_error']:.1f} cents")
print(f"Within ±25¢: {metrics['within_25_cents']:.1f}%")

# Save results
comparator.save_to_json('comparison.json')
comparator.save_to_csv('comparison.csv')
```

### 4. Grading

```python
from pitch_grader import PitchGrader

grader = PitchGrader()
grade = grader.grade_performance(metrics)

print(f"Grade: {grade.letter_grade}")
print(f"Score: {grade.numeric_score}/100")

# Print full report
grader.print_grade_report(grade)

# Save
grader.save_grade_report(grade, 'grade.json')
```

### 5. Visualization

```python
from pitch_visualizer import PitchVisualizer

viz = PitchVisualizer()

# Comprehensive report (all plots)
viz.create_comprehensive_report(
    score_notes,
    audio_frames,
    comparisons,
    metrics,
    grade.to_dict(),
    output_dir='visualizations/'
)

# Individual plots
viz.plot_pitch_curves(score_notes, audio_frames, 'curves.png')
viz.plot_cents_deviation(comparisons, 'deviation.png')
viz.plot_cents_histogram(comparisons, 'histogram.png')
viz.plot_accuracy_breakdown(metrics, 'breakdown.png')
```

---

## 📐 Understanding Cents

**Cents** are the standard unit for measuring pitch intervals:

- **1 cent** = 1/100 of a semitone
- **100 cents** = 1 semitone (e.g., C to C#)
- **1200 cents** = 1 octave

### Accuracy Thresholds

| Category | Cents Range | Description |
|----------|-------------|-------------|
| **Perfect** | < 10¢ | Imperceptible to most listeners |
| **Excellent** | 10-25¢ | Professional level |
| **Good** | 25-50¢ | Acceptable for performance |
| **Poor** | ≥ 50¢ | Noticeably out of tune |

### Reference:
- **±5 cents**: Top professional musicians
- **±10 cents**: Good amateur/student level
- **±25 cents**: Acceptable for non-professional
- **±50 cents**: Quarter-tone (clearly audible)
- **100 cents**: Half-step (very noticeable)

---

## ⚙️ Configuration Options

### Pitch Extraction Methods

#### pYIN (Default - CPU-Optimized)
```python
AudioPitchExtractor(method='pyin')
```
- **Pros**: Fast, CPU-only, no extra dependencies, good accuracy
- **Cons**: Can struggle with very noisy audio
- **Best for**: Most use cases, CPU-only systems

#### CREPE (Alternative - Better Accuracy)
```python
AudioPitchExtractor(method='crepe')
```
- **Pros**: Very accurate, state-of-the-art deep learning
- **Cons**: Slower on CPU, requires TensorFlow
- **Best for**: When accuracy is critical, quality audio

### Frequency Ranges

Adjust `fmin` and `fmax` based on instrument:

```python
# Piano (A0-C8)
AudioPitchExtractor(fmin=27.5, fmax=4186.0)

# Violin (G3-E7)
AudioPitchExtractor(fmin=196.0, fmax=2637.0)

# Male voice (E2-E4)
AudioPitchExtractor(fmin=82.4, fmax=329.6)

# Female voice (A3-A5)
AudioPitchExtractor(fmin=220.0, fmax=880.0)
```

### Reference Frequency

```python
# Standard concert pitch
ScorePitchExtractor(reference_frequency=440.0)

# Baroque pitch
ScorePitchExtractor(reference_frequency=415.0)

# High pitch (some orchestras)
ScorePitchExtractor(reference_frequency=442.0)
```

---

## 📈 Grading Scale

### Letter Grades

| Grade | MACE Range | Score | Description |
|-------|------------|-------|-------------|
| **A+** | 0-5¢ | 98-100 | Perfect |
| **A** | 5-10¢ | 93-97 | Excellent |
| **A-** | 10-15¢ | 88-92 | Very Good |
| **B+** | 15-20¢ | 83-87 | Good |
| **B** | 20-25¢ | 78-82 | Above Average |
| **B-** | 25-30¢ | 73-77 | Satisfactory |
| **C+** | 30-35¢ | 68-72 | Fair |
| **C** | 35-40¢ | 63-67 | Acceptable |
| **C-** | 40-45¢ | 58-62 | Below Average |
| **D** | 45-50¢ | 53-57 | Poor |
| **F** | >50¢ | 0-52 | Failing |

**MACE** = Mean Absolute Cents Error

---

## 🎯 Example Workflow

```bash
# 1. Prepare files
ls myfiles/
# score.xml
# performance.wav

# 2. Run evaluation
python evaluate_pitch.py \
    --score myfiles/score.xml \
    --audio myfiles/performance.wav \
    --output results/ \
    --method pyin

# 3. Check results
cat results/pitch_evaluation_*/EVALUATION_SUMMARY.txt

# 4. View visualizations
open results/pitch_evaluation_*/visualizations/00_summary.png

# 5. Analyze CSV data
libreoffice results/pitch_evaluation_*/reports/note_by_note_comparison.csv
```

---

## 🔍 Troubleshooting

### "No notes could be measured from audio"

**Causes:**
- Audio is too quiet or has too much noise
- Wrong frequency range (fmin/fmax)
- Audio and score don't match

**Solutions:**
```bash
# Try CREPE for better accuracy
python evaluate_pitch.py --score score.xml --audio audio.wav --method crepe

# Adjust frequency range (example for bass instrument)
# Edit audio_pitch_extractor.py line 32-33:
# fmin: float = 40.0,  # Lower for bass
# fmax: float = 1000.0,
```

### "Pitch is consistently sharp/flat"

**Cause:** Performance tuning differs from A=440Hz

**Solution:**
```bash
# Check detected tuning first
python audio_pitch_extractor.py --audio audio.wav --estimate-tuning

# If it shows +0.50 semitones, use:
python evaluate_pitch.py --score score.xml --audio audio.wav --reference-freq 454.5
```

### Low measurement rate

**Cause:** Unclear articulation or audio quality issues

**Solutions:**
- Ensure audio is clear, not too much reverb
- Check that audio matches the score (no extra notes)
- Try adjusting `confidence_threshold` in `audio_pitch_extractor.py`

---

## 🧪 Testing

Test with provided samples:

```bash
# Test score extraction
python score_pitch_extractor.py --score ../../Sample_Music_Sheet1.xml --output test_score.json

# Test audio extraction  
python audio_pitch_extractor.py --audio ../test_audio.wav --output test_audio.json --method pyin

# Full evaluation
python evaluate_pitch.py \
    --score ../../Sample_Music_Sheet1.xml \
    --audio ../test_audio.wav \
    --output test_results/
```

---

## 📚 References

### Libraries Used

- **music21**: https://github.com/cuthbertLab/music21
- **librosa**: https://github.com/librosa/librosa
- **CREPE**: https://github.com/marl/crepe
- **matplotlib**: https://matplotlib.org/
- **seaborn**: https://seaborn.pydata.org/

### Research Papers

1. **pYIN**: Mauch, M., & Dixon, S. (2014). "pYIN: A fundamental frequency estimator using probabilistic threshold distributions"

2. **CREPE**: Kim, J. W., et al. (2018). "CREPE: A Convolutional Representation for Pitch Estimation"

3. **Pitch Perception**: Moore, B. C. J. (2012). "An Introduction to the Psychology of Hearing"

---

## 🤝 Integration with Main Pipeline

To integrate with the main TuttiBot pipeline:

```python
# In main_hybrid_v02.py, add after Block 2:

# Step 4: Pitch Evaluation (optional)
if args.evaluate_pitch:
    pitch_output_dir = os.path.join(output_dir, '04_pitch_evaluation')
    
    from Temporal_Alignment.Block_3_PitchEvaluation.evaluate_pitch import evaluate_pitch
    
    pitch_results = evaluate_pitch(
        score_path=input_results['score_path'],
        audio_path=input_results['audio_path'],
        output_dir=pitch_output_dir,
        method='pyin'  # CPU-friendly
    )
```

---

## 📝 License

This module is part of the TuttiBot project and follows the same license.

---

## 💡 Tips for Best Results

1. **Audio Quality**: Use clean, clear recordings
2. **Match Instruments**: Adjust frequency ranges per instrument
3. **Check Tuning**: Use `--estimate-tuning` first
4. **CPU Performance**: Use `pyin` for speed, `crepe` for accuracy
5. **Visualization**: Plots help identify problem areas
6. **CSV Export**: Great for detailed analysis in Excel/Sheets

---

## 🆘 Support

For issues or questions:
1. Check this README thoroughly
2. Review example output files
3. Test with sample files first
4. Check library versions: `pip list | grep -E "music21|librosa|matplotlib"`

---

**Version**: 1.0.0  
**Last Updated**: November 2024  
**CPU-Optimized**: ✅ No GPU required
