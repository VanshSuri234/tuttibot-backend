# Block 2: Enhanced Symbolic Alignment with Beat Weighting

## What This Does

This module aligns a musical score with an audio performance at a fine-grained level. It finds exactly which moment in the performance corresponds to each moment in the score, creating a detailed time map.

## Key Improvements

### 1. Band Constraint (Sakoe-Chiba)
The alignment now uses a constraint that assumes the performance tempo is reasonably close to the score tempo. This makes alignment faster and more stable, preventing wild mismatches.

### 2. Beat Weighting
When beat positions are provided from Block 4, the aligner pays special attention to high-confidence beats. These become anchor points that guide the alignment, making it more accurate.

### 3. Fermata and Cadence Awareness
If the score marks fermatas (hold notes) or cadences (phrase endings), the aligner allows more timing flexibility in those regions. This handles expressive rubato properly.

## Input

Required:
- ScoreGraph JSON from Block 0 (musical structure)
- Performance MIDI from Block 1 (transcribed audio)

Optional:
- Beats JSON from Block 4 (for beat weighting)

## Output

A comprehensive alignment package including:
- Time mapping: pairs of (score_time, performance_time) showing correspondence
- Warping path: the DTW alignment path through the feature space
- Confidence score: how well the performance matches the score
- Visualization: graphs showing the alignment quality
- Metadata: which features were used (beat weighting, fermata adaptation, etc.)

Example output structure:
```json
{
  "time_mapping": [
    {"score_time": 0.5, "perf_time": 0.48},
    {"score_time": 1.0, "perf_time": 0.95}
  ],
  "confidence": 0.924,
  "alignment_metadata": {
    "beat_weighting_used": true,
    "adaptive_weights_used": true,
    "band_constraint_radius": 0.25
  }
}
```

## How to Use

Basic usage (standard alignment):
```bash
python align_symbolic_enhanced.py scoregraph.json performance.mid --output results/
```

With beat weighting (recommended):
```bash
python align_symbolic_enhanced.py scoregraph.json performance.mid --beats beats.json --output results/
```

## How It Works

1. Convert both score and performance to chromagram features (12-dimensional pitch profiles)
2. If beats are provided, create a cost matrix that prefers aligning to high-confidence beats
3. If fermatas/cadences are marked, adjust step penalties to allow more timing flexibility
4. Run Dynamic Time Warping (DTW) with Sakoe-Chiba band constraint
5. Extract the optimal alignment path and convert to time mappings
6. Calculate confidence based on feature similarity along the path
7. Generate visualizations showing alignment quality

## Technical Notes

### Band Constraint
The Sakoe-Chiba band restricts the search space to paths where the tempo ratio stays within 25% of the estimated global tempo. This prevents absurd alignments where, for example, the beginning of the performance matches the end of the score.

### Beat Weighting
High-confidence beats receive lower cost in the DTW matrix. The aligner naturally prefers to align score beats with confident performance beats, improving accuracy especially at measure boundaries.

### Adaptive Weights
Near fermatas and cadences, the horizontal and vertical step penalties are reduced by 30%. This allows the performance to stretch or compress time relative to the score in these expressive moments.

## Visualizations Explained

The output includes a four-panel visualization:

1. Top-left: Score time vs Performance time
   - Should be roughly linear
   - Steeper slopes = faster performance
   - Flatter slopes = slower performance

2. Top-right: Local tempo ratio over time
   - Shows where performer speeds up or slows down
   - Value of 1.0 = matching score tempo
   - Above 1.0 = slower than score
   - Below 1.0 = faster than score

3. Bottom-left: Quality metrics bar chart
   - Lower DTW distance = better match
   - Higher confidence = stronger alignment

4. Bottom-right: Warping path
   - Should be smooth and roughly diagonal
   - Sharp changes indicate timing variations

## For Musicians

This is like having an expert musician watch the performance with the score and say "at 2.3 seconds in the recording, you played the note that appears at beat 5 in the score." The system does this for every moment in the piece.

The beat weighting ensures the system trusts clear beats more than ambiguous ones. The fermata awareness lets the performer hold notes or slow down at cadences without confusing the aligner.

## What Changed from Original

The original version used basic DTW without constraints or musical awareness. The updated version:
- Runs faster with band constraints
- More accurate with beat weighting
- Handles expressive timing with fermata/cadence adaptation
- Provides richer metadata about what features were used
- Better visualizations for understanding results
