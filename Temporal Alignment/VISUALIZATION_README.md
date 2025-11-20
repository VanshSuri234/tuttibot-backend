# Alignment Results Visualization Tool

## What It Does

Generates clear, simple visualizations showing how well your performance matched the score. Creates separate PNG images for each aspect of the analysis, plus a text summary.

## Output Files

The tool creates 7 files:

### PNG Images (Separate Files):
1. **1_beat_confidence.png** - Shows where beats were detected and how confident the system is
2. **2_alignment_path.png** - Shows if you played at the right speed (tempo matching)
3. **3_pitch_matching.png** - Shows how many notes you played correctly
4. **4_tempo_variation.png** - Shows where you sped up or slowed down
5. **5_beat_alignment.png** - Shows how beats are weighted by confidence
6. **6_summary_dashboard.png** - Overall performance summary with color-coded grades

### Text File:
7. **performance_summary.txt** - Simple text summary of all metrics

## How to Use

### Basic Usage (with all data):
```bash
python visualize_results.py \
  --beats path/to/beats.json \
  --context path/to/context_alignment.json \
  --alignment path/to/alignment_results.json \
  --scoregraph path/to/scoregraph.json \
  --output my_visualizations
```

### Minimal Usage (only what you have):
```bash
python visualize_results.py --alignment alignment_results.json --output results_viz
```

The tool will skip any plots for which data is not available.

## Understanding the Visualizations

### 1. Beat Confidence
- **Green lines** = High confidence beats (computer is very sure)
- **Orange lines** = Medium confidence
- **Red lines** = Low confidence
- **Thick lines** = Downbeats (measure starts)

**For musicians:** Shows which beats the computer trusts most. High confidence beats guide the alignment.

---

### 2. Alignment Path
- **Diagonal line** = Your performance tempo
- **Black dashed line** = Perfect match
- **Gray shaded area** = Allowed tempo range (±25%)

**How to read:**
- Line on diagonal = You matched the tempo perfectly
- Steeper than diagonal = You played slower
- Flatter than diagonal = You played faster

**For musicians:** Like comparing your speedometer to the speed limit. Staying in the gray area means your tempo was reasonable.

---

### 3. Pitch Matching
- **Green bar** = Correct notes
- **Blue bar** = Total score notes
- **Orange bar** = Total performance notes
- **Percentage** = Your accuracy grade

**For musicians:** Simple! Shows how many notes you got right. Green = Excellent (>90%), Orange = Good (70-90%), Red = Needs work (<70%).

---

### 4. Tempo Variation
- **Blue shaded area** = You played faster than score
- **Red shaded area** = You played slower than score
- **Black line at 1.0** = Perfect tempo match

**For musicians:** Shows where you rushed or dragged. Useful for finding problem sections that need metronome practice.

---

### 5. Beat Alignment
- **Bigger circles** = Higher confidence beats
- **Smaller circles** = Lower confidence beats
- **Color** = Confidence level (green/orange/red)

**For musicians:** Shows which beats the alignment system trusts more. Bigger circles = stronger anchor points for matching.

---

### 6. Summary Dashboard
Color-coded boxes showing:
- **Pitch Accuracy** - Did you play the right notes?
- **Timing Consistency** - Did you keep steady tempo?
- **Beat Detection Quality** - How clear were your beats?
- **Fermata Handling** - Were expressive markings detected?

**Colors mean:**
- Green = Excellent (≥85%)
- Orange = Good (70-85%)
- Red = Needs Work (<70%)

**For musicians:** Your performance report card at a glance!

---

## Text Summary File

The `performance_summary.txt` file contains:
- All metrics in plain text
- Grade for each category
- Interpretation guide
- Easy to copy/paste or print

Example:
```
===========================================================
PERFORMANCE ANALYSIS SUMMARY
===========================================================

PITCH ACCURACY
-----------------------------------------------------------
  Correct notes: 187
  Total score notes: 200
  Accuracy: 93.5%
  Grade: EXCELLENT

BEAT DETECTION
-----------------------------------------------------------
  Total beats: 120
  Average confidence: 0.856
  
TEMPORAL ALIGNMENT
-----------------------------------------------------------
  Average tempo ratio: 1.023
  Overall: MATCHED score tempo
  Timing consistency: 89.2%
```

## For Non-Musicians

Think of this like a sports performance analysis:

1. **Beat Confidence** = Detecting when steps happened (high confidence = clear footwork)
2. **Alignment Path** = Did you finish the race on pace?
3. **Pitch Matching** = Did you hit the right targets?
4. **Tempo Variation** = Where did you speed up or slow down?
5. **Beat Alignment** = Which steps were most important?
6. **Summary Dashboard** = Your final score card

## Requirements

```bash
pip install matplotlib numpy
```

## Tips for Presenting Results

### To Students:
Show images 3 (Pitch Matching) and 6 (Summary Dashboard) first - these are easiest to understand.

### To Teachers:
Show image 4 (Tempo Variation) to identify problem sections that need practice.

### To Researchers:
All images together show comprehensive alignment quality. Text summary provides exact metrics.

### To Non-Technical Audience:
Start with Summary Dashboard (image 6), then explain colors: green = good, orange = okay, red = needs work.

## Customization

You can modify the script to:
- Change color schemes
- Adjust thresholds for grades
- Add more metrics
- Change image sizes (edit `figsize` parameters)
- Adjust DPI for higher/lower resolution (edit `dpi` parameter in `savefig` calls)

## Output Structure

```
visualizations/
├── 1_beat_confidence.png
├── 2_alignment_path.png
├── 3_pitch_matching.png
├── 4_tempo_variation.png
├── 5_beat_alignment.png
├── 6_summary_dashboard.png
└── performance_summary.txt
```

All files are named with numbers for easy ordering and understanding.
