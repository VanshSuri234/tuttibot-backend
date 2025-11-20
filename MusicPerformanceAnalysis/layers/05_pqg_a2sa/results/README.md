# Results Directory - Bach10 01-AchGottundHerr

This directory contains alignment results and visualizations for the first piece in the Bach10 dataset.

## 📁 Contents

### Data Files (JSON)
- `bach10_01_alignment.json` - Complete alignment results (142 notes, 44 chords)
- `bach10_01_evaluation.json` - Evaluation metrics (MNE, MFE, alignment rates)

### Text Reports
- `bach10_01_alignment.txt` - Human-readable alignment summary
- `bach10_01_timing_comparison.txt` - MIDI vs aligned timing comparison

### Visualizations (PNG)
All plots are 150 DPI, publication-quality:

| File | Size | Description |
|------|------|-------------|
| `plot_00_summary.png` | 231 KB | **START HERE** - Comprehensive 6-panel overview |
| `plot_01_global_alignment.png` | 86 KB | Chord onset timing curve |
| `plot_02_error_distribution.png` | 62 KB | MNE/MFE histograms |
| `plot_03_alignment_rates.png` | 56 KB | Performance at thresholds |
| `plot_04_articulation_distribution.png` | 106 KB | Pie chart breakdown |
| `plot_05_per_instrument_stats.png` | 48 KB | Per-instrument comparison |
| `plot_06_error_scatter.png` | 130 KB | Individual note errors |
| `plot_07_error_boxplot.png` | 60 KB | Statistical distributions |
| `plot_08_timeline_visualization.png` | 76 KB | Note timeline (first 10s) |
| `plot_09_chord_timeline.png` | 45 KB | Chord boundaries |
| `plot_10_duration_distribution.png` | 69 KB | Duration by articulation |

## 🎯 Quick Start

**View comprehensive summary:**
```bash
# Linux
xdg-open plot_00_summary.png

# macOS
open plot_00_summary.png

# Windows
start plot_00_summary.png
```

**Read alignment results:**
```bash
cat bach10_01_alignment.txt
```

**Check metrics:**
```bash
cat bach10_01_evaluation.json | python3 -m json.tool
```

## 📊 Key Results

**Performance Metrics:**
- MNE (Mean Note Error): 0.00 ms
- MFE (Mean Frame Error): 131.16 ms
- Median offset error: 96.38 ms

**Alignment Rates:**
- 41.5% within 30ms
- 87.3% within 200ms ✅

**Articulation Detection:**
- 29 staccato notes (20.4%)
- 60 legato notes (42.3%)
- 53 uncertain notes (37.3%)

**Coverage:**
- 142 notes total
- 4 instruments
- 44 chords
- ~25 seconds audio

## 📖 Documentation

For detailed explanations of each plot:
- See `../VISUALIZATION_GUIDE.md`

For quick reference:
- See `../PLOT_QUICK_REFERENCE.md`

## 🔄 Regenerate

To regenerate all visualizations:
```bash
cd ..
python3 visualize_results.py
```

To regenerate alignment results:
```bash
cd ..
python3 run_bach10.py
```

## 📌 Notes

- All plots use consistent color scheme:
  - 🔴 Red = Staccato
  - 🔵 Cyan = Legato
  - 🟡 Yellow = Uncertain

- MNE = 0 because onsets are taken directly from MIDI (not refined yet)
- MFE shows offset refinement is working (articulation-guided)
- Comparing against MIDI score (not performance ground truth)

## 🎵 Source Data

**Audio:** `../Bach_10_Dataset/01-AchGottundHerr.wav`  
**MIDI:** `../Bach_10_Dataset/01-AchGottundHerr.mid`  

Bach chorale "Ach Gott und Herr" from Bach10 dataset:
- 4-part harmony (SATB)
- Synthetic audio from MIDI
- Clean recordings (ideal test case)

## ✨ Generated

**Date:** November 12, 2025  
**System:** PQG-A2SA Implementation  
**Algorithm:** Lian, Cheng & Zhang (2023)  
**Configuration:** HOP_LENGTH=1024, K_CL=10, IOI_DELTA=4, NMF_ITERATIONS=150
