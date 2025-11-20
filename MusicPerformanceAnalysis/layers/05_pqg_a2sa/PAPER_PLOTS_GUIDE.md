# 📊 Paper-Style Plot Generator - Quick Guide

## ✨ Simple One-Command Solution

This script takes **audio + MIDI** and generates **publication-ready plots** matching the paper's style.

## 🚀 Usage

```bash
python3 generate_paper_plots.py <audio_file> <midi_file> [output_prefix]
```

### Examples:

```bash
# Basic usage
python3 generate_paper_plots.py song.wav song.mid

# With custom output name
python3 generate_paper_plots.py Bach10/01.wav Bach10/01.mid bach01

# Another piece
python3 generate_paper_plots.py mymusic.mp3 mymusic.mid results
```

## 📂 What You Get

The script creates a `paper_plots/` directory with:

### 🖼️ 5 Publication-Quality Figures (300 DPI):

1. **`{prefix}_fig1_alignment_curve.png`**
   - Global alignment curve showing chord timing
   - Compares PQG-A2SA vs constant tempo
   - ✅ Similar to Figure 1 in paper

2. **`{prefix}_fig2_error_histogram.png`**
   - Dual histogram: onset errors & offset errors
   - Shows MNE and MFE distributions
   - ✅ Similar to Figure 3 in paper

3. **`{prefix}_fig3_alignment_rates.png`**
   - Bar chart at 6 thresholds (30-200ms)
   - Compares onset vs offset alignment rates
   - ✅ Performance summary figure

4. **`{prefix}_fig4_articulation_pie.png`**
   - Pie chart: Staccato / Legato / Uncertain
   - Shows articulation detection distribution
   - ✅ Similar to Figure 4 in paper

5. **`{prefix}_fig5_timeline.png`**
   - Multi-track piano roll timeline
   - Notes colored by articulation
   - First 10 seconds displayed
   - ✅ Similar to Figure 5 in paper

### 📄 1 Text Summary Table:

6. **`{prefix}_summary_table.txt`**
   - Complete numerical results
   - All metrics, rates, and statistics
   - Ready to copy into paper

## 📊 Example Output

For Bach10 piece #01:

```
paper_plots/
├── bach01_fig1_alignment_curve.png ........ 118 KB (high quality)
├── bach01_fig2_error_histogram.png ........ 107 KB
├── bach01_fig3_alignment_rates.png ........ 111 KB
├── bach01_fig4_articulation_pie.png ....... 164 KB
├── bach01_fig5_timeline.png ............... 176 KB
└── bach01_summary_table.txt ............... 3.2 KB (text)
```

## ⚡ What Happens When You Run It

```
1. Loads audio and MIDI
2. Runs PQG-A2SA alignment (6 stages):
   ✓ Audio features
   ✓ Score parsing
   ✓ VIDTW alignment
   ✓ IOI-guided refinement
   ✓ Score-informed NMF
   ✓ Articulation detection
3. Evaluates against MIDI reference
4. Generates 5 plots + 1 table
5. Done!
```

**Time:** ~30-60 seconds for a 30-second piece

## 🎨 Plot Characteristics

All plots use:
- ✅ **300 DPI** - Publication quality
- ✅ **Serif fonts** (Times New Roman style)
- ✅ **Paper style** theme (clean, professional)
- ✅ **Consistent colors** matching the paper
- ✅ **Proper labels** and legends
- ✅ **High contrast** for printing

## 📋 Typical Results

For a well-aligned piece, you should see:

- **MNE:** 0-50 ms (onsets)
- **MFE:** 80-150 ms (offsets)
- **Offset ≤200ms:** >80%
- **Articulation detected:** 60-80% of notes

## 🔧 Requirements

Already installed if you've set up PQG-A2SA:

```bash
- numpy
- matplotlib
- seaborn
- pretty_midi
- librosa
- scikit-learn
- scipy
```

## 💡 Tips

### For Best Results:

1. **Audio Quality:** Use clean recordings (Bach10 dataset works great)
2. **MIDI Sync:** MIDI should match audio timing roughly
3. **File Formats:** 
   - Audio: `.wav`, `.mp3`, `.flac`
   - MIDI: `.mid`, `.midi`

### Customization:

Edit `generate_paper_plots.py` to change:

```python
# Line 30-35: Style settings
plt.rcParams['figure.dpi'] = 300      # Change resolution
plt.rcParams['font.family'] = 'serif'  # Change font

# Line 288: Timeline window
time_window=10.0  # Show more/less seconds

# Line 213: Color scheme
colors = {'staccato': '#E74C3C', ...}  # Change colors
```

## 🎯 Use Cases

| Scenario | Command | Purpose |
|----------|---------|---------|
| **Quick assessment** | Run with defaults | See if alignment works |
| **Paper figures** | Run with good prefix | Generate for publication |
| **Dataset evaluation** | Loop over files | Batch process |
| **Parameter tuning** | Edit config, re-run | Test different settings |

## 📝 Compare Multiple Runs

```bash
# Baseline
python3 generate_paper_plots.py song.wav song.mid baseline

# After tuning
python3 generate_paper_plots.py song.wav song.mid tuned

# Compare the outputs visually or programmatically
```

## 🚀 Batch Processing

```bash
# Process all Bach10 pieces
for i in {01..10}; do
    python3 generate_paper_plots.py \
        ../Bach_10_Dataset/${i}*.wav \
        ../Bach_10_Dataset/${i}*.mid \
        bach${i}
done
```

## ✅ Success Indicators

When you run it, you should see:

```
✅ Alignment complete! Total notes refined: X
✅ ALL PLOTS GENERATED SUCCESSFULLY!
   MNE: X.XX ms
   MFE: X.XX ms
   Offset alignment ≤200ms: XX.X%
```

## ❌ Common Issues

### Issue: "Audio file not found"
**Solution:** Check file path, use absolute or relative path correctly

### Issue: "MIDI file not found"  
**Solution:** Ensure `.mid` extension, check path

### Issue: "Module not found"
**Solution:** Activate virtual environment or install dependencies

### Issue: Plots look wrong
**Solution:** Check that audio/MIDI match (same piece, same tempo)

## 📖 More Information

- **Full documentation:** See `VISUALIZATION_GUIDE.md`
- **All plot details:** See `PLOT_QUICK_REFERENCE.md`
- **Algorithm details:** See paper (Lian, Cheng & Zhang, 2023)

## 🎉 Summary

**One simple command = 5 paper-quality plots + 1 summary table!**

```bash
python3 generate_paper_plots.py audio.wav score.mid myresults
```

That's it! Your plots are ready for papers, presentations, or analysis.

---

**Generated:** November 13, 2025  
**Script:** `generate_paper_plots.py`  
**Based on:** PQG-A2SA (Lian, Cheng & Zhang, 2023)
