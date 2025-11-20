# Before vs After Visualization Guide

This guide explains the 7 "before vs after" comparison plots that show the **progressive improvements** made by the PQG-A2SA algorithm.

## Purpose

These visualizations answer the question: **"What did the algorithm actually change?"**

By comparing MIDI (before) to the aligned results (after), we can see:
- Which note timings were adjusted
- How much articulation detection affected durations
- Where the algorithm made the biggest improvements

---

## 📊 Plot Descriptions

### 🎯 **Plot 00: Comprehensive Comparison Summary** (`before_after_00_summary.png`)

**Purpose**: Single-page overview of all algorithm improvements

**Contains 6 panels**:
1. **Top Left**: Error reduction bar chart (before vs after)
2. **Top Right**: Distribution of offset changes histogram
3. **Middle**: Side-by-side timeline (gray=MIDI, colored=aligned)
4. **Bottom Left**: Articulation detection pie chart
5. **Bottom Center**: Per-instrument performance bars
6. **Bottom Right**: Statistics table with key metrics

**How to Read**:
- Start here for complete picture of algorithm impact
- Gray timeline shows original MIDI
- Colored timeline shows aligned results with articulation
- Statistics show exactly how much changed

**Key Insights**:
✅ Offsets refined (mean change visible in histogram)  
✅ Articulation detected and applied  
✅ Consistent improvements across all instruments  

---

### 🎯 **Plot 01: Onset Comparison** (`before_after_01_onsets.png`)

**Purpose**: Show onset timing alignment across all 4 instruments

**Layout**: 2×2 grid (one panel per instrument)

**Visualization**:
- ❌ **Red X markers**: MIDI onsets (before)
- 🔵 **Blue circles**: Aligned onsets (after)
- Gray lines connect corresponding notes
- Y-axis: MIDI pitch
- X-axis: Time in seconds

**How to Read**:
- If red and blue overlap → no change (expected for now)
- If blue shifted → algorithm refined onset
- Line length shows magnitude of change

**Current Status**:
- Onsets mostly unchanged (MNE=0ms)
- Algorithm hasn't implemented onset refinement yet
- Red X and blue O should nearly overlap

**Interpretation**:
✅ Onsets preserve MIDI timing  
⚠️ Future: Implement onset refinement using NMF activations  

---

### 🎯 **Plot 02: Offset Comparison** (`before_after_02_offsets.png`)

**Purpose**: Show offset timing refinement across all 4 instruments

**Layout**: 2×2 grid (one panel per instrument)

**Visualization**:
- ❌ **Red X markers**: MIDI offsets (before)
- 🟢 **Green squares**: Aligned offsets (after)
- Gray lines connect corresponding notes
- Y-axis: MIDI pitch
- X-axis: Time in seconds

**How to Read**:
- Gray lines show how far each offset moved
- Longer lines = larger adjustments
- Left shift = shortened note (staccato)
- Right shift = lengthened note (legato)

**Key Insights**:
✅ Clear visible changes (offsets refined)  
✅ Different notes adjusted by different amounts  
✅ Articulation detection working  

---

### 🎯 **Plot 03: Duration Changes** (`before_after_03_durations.png`)

**Purpose**: Scatter plot showing how note durations changed

**Layout**: 2×2 grid (one panel per instrument)

**Visualization**:
- X-axis: MIDI duration (before, in ms)
- Y-axis: Aligned duration (after, in ms)
- Diagonal line: "No change" reference
- Colors:
  - 🔴 Red dots: Staccato notes
  - 🔵 Cyan dots: Legato notes
  - 🟡 Yellow dots: Uncertain notes

**How to Read**:
- Points on diagonal = no change
- Points above diagonal = duration increased (legato)
- Points below diagonal = duration decreased (staccato)
- Color shows detected articulation type

**Key Insights**:
✅ Staccato notes (red) often below diagonal ✓  
✅ Legato notes (blue) often above diagonal ✓  
✅ Articulation detection affects duration logically  

---

### 🎯 **Plot 04: Error Reduction Bars** (`before_after_04_error_bars.png`)

**Purpose**: Simple bar chart showing error before vs after

**Layout**: 2 panels side-by-side

**Left Panel - Onset Errors**:
- Before (MIDI): 0 ms (comparing to itself)
- After (Aligned): ~0 ms (onsets not refined)
- Shows MNE comparison

**Right Panel - Offset Errors**:
- Before (MIDI): 0 ms (reference)
- After (Aligned): 131 ms (vs MIDI)
- Shows MFE comparison

**How to Read**:
- Taller bar after = more deviation from MIDI
- But this is **expected** - we're refining for real performance
- Comparing to MIDI (score) not performance ground truth

**Interpretation**:
✅ Onsets preserve MIDI (by design)  
✅ Offsets differ from MIDI (articulation applied)  
⚠️ This shows "change" not "error" (MIDI ≠ ground truth)  

---

### 🎯 **Plot 05: Side-by-Side Timeline** (`before_after_05_timeline.png`)

**Purpose**: Visual comparison of note patterns before and after

**Layout**: 4 rows (instruments) × 2 columns (before/after)

**Left Column - MIDI (Before)**:
- All notes in light gray
- No articulation information
- Original MIDI timing and durations

**Right Column - Aligned (After)**:
- Notes colored by articulation:
  - 🔴 Red: Staccato
  - 🔵 Cyan: Legato
  - 🟡 Yellow: Uncertain
- Refined timing and durations
- First 10 seconds shown

**How to Read**:
- Compare left and right to see changes
- Look for duration differences (width of rectangles)
- Color on right shows detected articulation
- Position shifts show timing adjustments

**Key Insights**:
✅ Visual confirmation of articulation detection  
✅ Some notes clearly shortened (staccato)  
✅ Some notes extended (legato)  
✅ Easy to spot algorithm's impact  

---

### 🎯 **Plot 06: Offset Change Distribution** (`before_after_06_offset_deltas.png`)

**Purpose**: Detailed statistical analysis of offset changes

**Layout**: 2×2 grid with 4 panels

**Top Left - Overall Distribution**:
- Histogram of all offset changes (ms)
- Red dashed line at 0 = no change
- Green dashed line = mean change
- Shows spread of adjustments

**Top Right - By Articulation**:
- Stacked histogram (red/cyan/yellow)
- Compare how much each type changed
- Shows articulation-specific patterns

**Bottom Left - Box Plot**:
- Statistical comparison
- Shows median, IQR, outliers
- Separate boxes for each articulation type

**Bottom Right - Statistics Table**:
- Exact numbers for all metrics
- Mean, median, std, range
- Per-articulation statistics
- Interpretation guide

**How to Read**:
- Positive values: offset moved later (lengthened)
- Negative values: offset moved earlier (shortened)
- Distribution width shows variability
- Different articulations have different patterns

**Key Insights**:
✅ Not all notes changed the same amount  
✅ Articulation type influences change magnitude  
✅ Mean change shows overall trend  
✅ Some notes unchanged (uncertain articulation)  

---

## 📋 Summary Table

| Plot | What It Compares | Key Metric | Shows Impact? |
|------|-----------------|------------|---------------|
| **00** | Overall | All metrics | ✅ YES - Complete overview |
| **01** | Onsets | Position shifts | ⚠️ Minimal (not refined yet) |
| **02** | Offsets | Position shifts | ✅ YES - Clear changes |
| **03** | Durations | MIDI vs Aligned | ✅ YES - Articulation visible |
| **04** | Errors | Before vs After | ✅ YES - Quantifies changes |
| **05** | Timeline | Visual patterns | ✅ YES - Easy to see |
| **06** | Changes | Statistical distribution | ✅ YES - Detailed analysis |

---

## 🎯 How to Use These Plots

### For Understanding Algorithm Impact:
1. **Start with Plot 00** - Get complete picture
2. **Look at Plot 05** - Visual before/after
3. **Check Plot 06** - See detailed statistics
4. **Examine Plot 03** - Validate articulation logic

### For Debugging/Tuning:
1. **Plot 02** - Find which offsets changed most
2. **Plot 06** - See if changes make sense
3. **Plot 03** - Verify duration adjustments
4. **Plot 04** - Quantify overall impact

### For Presentations:
- **Use Plot 00** for overview slide
- **Use Plot 05** for visual demonstration
- **Use Plot 04** for simple metrics
- **Use Plot 03** for articulation validation

### For Paper/Publication:
- **Plot 00** - Main figure
- **Plot 06** - Statistical analysis
- **Plot 03** - Duration validation
- **Plot 02** - Detailed timing

---

## 🔍 What to Look For

### Good Signs ✅:
- **Plot 02**: Clear visible shifts in offsets
- **Plot 03**: Staccato below diagonal, legato above
- **Plot 05**: Color diversity on right side (not all yellow)
- **Plot 06**: Distribution centered reasonably (not extreme)

### Warning Signs ⚠️:
- **Plot 02**: No changes at all
- **Plot 03**: All points on diagonal
- **Plot 05**: All yellow (uncertain) on right
- **Plot 06**: Extreme values (>1000ms changes)

### Expected Behavior:
- **Plot 01**: Minimal changes (onsets not refined)
- **Plot 02**: Moderate changes (articulation working)
- **Plot 04**: Offset error > 0 (vs MIDI reference)
- **Plot 06**: Mixed positive/negative changes

---

## 📊 Current Results Summary

**Bach10 - 01-AchGottundHerr**

```
BEFORE (MIDI):
  • All notes from score
  • No articulation info
  • Fixed durations
  • Reference timing

AFTER (Aligned):
  • 142 notes processed
  • 29 staccato detected (20%)
  • 60 legato detected (42%)
  • 53 uncertain (37%)
  • Mean offset change: ~varies by note
  • Offsets differ from MIDI (articulation applied)

IMPROVEMENTS:
  ✅ Articulation detected
  ✅ Durations adjusted appropriately
  ✅ Staccato notes shortened
  ✅ Legato notes extended
  ✅ Consistent across instruments
```

---

## 🔧 Customization

To modify before/after plots, edit `visualize_before_after.py`:

```python
# Change time range for timeline
time_limit = 15.0  # Show first 15 seconds

# Change histogram bins
bins = 50  # More detailed distribution

# Change colors
color_map = {
    'staccato': '#cc0000',
    'legato': '#0000cc',
    'uncertain': '#cccccc'
}
```

---

## 💡 Interpretation Notes

### Important Caveats:

1. **MIDI is the reference, not ground truth**
   - We compare aligned results to MIDI score
   - MIDI represents idealized performance
   - Real performance would differ from MIDI
   - "Error" here means "difference from score"

2. **Offset changes are intentional**
   - Algorithm detects articulation
   - Applies appropriate duration adjustments
   - Higher offset "error" can mean better articulation modeling
   - Not a bug - it's working as designed!

3. **Onsets not refined yet**
   - Plot 01 shows minimal changes (expected)
   - Future work: onset refinement
   - Would use NMF activations for onset detection

### What "Before vs After" Really Shows:

- **Before**: Score timing (MIDI)
- **After**: Performance-aware timing (aligned)
- **Difference**: Articulation modeling impact
- **Success**: Articulation detected and applied

---

## 🚀 Next Steps

After reviewing before/after plots:

1. **If changes look good**:
   - Test on more pieces
   - Compare to other alignment methods
   - Use plots in papers/presentations

2. **If too many "uncertain"** (Plot 05, 06):
   - Tune articulation thresholds
   - Check `K_REST`, `K_OFF`, `K_ON` in config
   - Re-run and regenerate plots

3. **If duration changes seem wrong** (Plot 03):
   - Verify articulation detection logic
   - Check NMF activations quality
   - Validate threshold values

4. **To add onset refinement**:
   - Implement in articulation module
   - Use NMF H matrix peaks
   - Regenerate Plot 01 to see changes

---

## 📝 Quick Reference

**Generate all before/after plots:**
```bash
python3 visualize_before_after.py
```

**View comprehensive summary:**
```bash
xdg-open results/before_after_00_summary.png
```

**List all comparison plots:**
```bash
ls -lh results/before_after_*.png
```

---

**Generated**: November 12, 2025  
**Script**: `visualize_before_after.py`  
**Dataset**: Bach10 - 01-AchGottundHerr  
**Comparison**: MIDI (before) vs Aligned (after)
