# 📊 Quick Reference: PQG-A2SA Visualizations

## One-Liner for Each Plot

| # | File | What It Shows | Key Takeaway |
|---|------|---------------|--------------|
| **00** | `plot_00_summary.png` | Everything at a glance | **START HERE** - Complete overview |
| **01** | `plot_01_global_alignment.png` | Chord timing curve | Tempo tracking works ✓ |
| **02** | `plot_02_error_distribution.png` | Error histograms | MFE=131ms, Median=96ms |
| **03** | `plot_03_alignment_rates.png` | Performance at thresholds | 87% within 200ms ⭐ |
| **04** | `plot_04_articulation_distribution.png` | Articulation breakdown | 42% legato, 20% staccato |
| **05** | `plot_05_per_instrument_stats.png` | Compare 4 instruments | All instruments balanced |
| **06** | `plot_06_error_scatter.png` | Every note's error | Most notes <200ms |
| **07** | `plot_07_error_boxplot.png` | Error statistics | Medians 95-140ms |
| **08** | `plot_08_timeline_visualization.png` | Notes over time | Visual articulation validation |
| **09** | `plot_09_chord_timeline.png` | Chord boundaries | 44 chords detected |
| **10** | `plot_10_duration_distribution.png` | Duration by type | Staccato < Legato ✓ |

---

## 🚀 Quick Commands

```bash
# Generate all plots
cd /home/nikhilsingh/Documents/temp/Trials/Workspace/pqg_a2sa
python3 visualize_results.py

# View plots
cd results
ls -lh plot_*.png

# Open summary plot (replace with your image viewer)
xdg-open plot_00_summary.png       # Linux
open plot_00_summary.png           # macOS
start plot_00_summary.png          # Windows
```

---

## 📊 What Each Color Means

### Articulation Colors (Plots 04-08, 10):
- 🔴 **Red** = Staccato (short, detached notes)
- 🔵 **Cyan/Blue** = Legato (smooth, connected notes)  
- 🟡 **Yellow** = Uncertain (ambiguous articulation)

### Performance Colors (Plots 03):
- 🟢 **Green** = Good threshold (30ms)
- 🟡 **Yellow** = Medium threshold (60-150ms)
- 🔴 **Red** = Lenient threshold (200ms)

---

## 🎯 Use Cases

| Need | Use These Plots |
|------|----------------|
| **Quick check if system works** | Plot 00 |
| **Debug high errors** | Plots 06 + 07 |
| **Validate articulation** | Plots 04 + 08 + 10 |
| **Compare instruments** | Plots 05 + 07 |
| **Verify alignment** | Plots 01 + 03 |
| **Paper/presentation** | Plots 00 + 01 + 03 + 08 |
| **Understand errors** | Plots 02 + 06 + 07 |

---

## ✅ What "Good" Looks Like

| Plot | Good Performance |
|------|-----------------|
| 01 | Blue line follows green line closely |
| 02 | Most errors <150ms, few outliers |
| 03 | >80% bars filled for 200ms threshold |
| 04 | <30% uncertain, >40% detected types |
| 06 | Most dots below red 200ms line |
| 07 | Small boxes, medians <150ms |
| 08 | Clear color patterns (not all yellow) |
| 10 | Red box (staccato) lower than blue (legato) |

---

## 📈 Current Performance Summary

**Bach10 - 01-AchGottundHerr**

```
✅ Metrics:
   MNE:  0.00 ms (onsets from MIDI)
   MFE:  131.16 ms (offsets refined)
   Median: 96.38 ms

✅ Alignment Rates:
   ≤30ms:  41.5%
   ≤200ms: 87.3%  ⭐

✅ Articulation:
   Staccato: 29 notes (20.4%)
   Legato:   60 notes (42.3%)
   Uncertain: 53 notes (37.3%)

✅ Coverage:
   142 notes across 4 instruments
   44 chords in 25 seconds
   Balanced across instruments
```

---

## 🔧 Regenerate for Different Data

Edit `run_bach10.py` to use different piece:

```python
# Change these lines:
audio_file = "../Bach_10_Dataset/02-AchLiebenChristen.wav"
midi_file = "../Bach_10_Dataset/02-AchLiebenChristen.mid"
output_prefix = "bach10_02"
```

Then run:
```bash
python3 run_bach10.py
python3 visualize_results.py
```

---

## 📖 Full Documentation

- **VISUALIZATION_GUIDE.md** - Detailed plot explanations
- **visualize_results.py** - Source code with comments
- **EVALUATION_SUMMARY.md** - Numerical results
- **README.md** - System overview

---

**Generated**: November 12, 2025  
**System**: PQG-A2SA Audio-to-Score Alignment  
**Dataset**: Bach10 Chorales
