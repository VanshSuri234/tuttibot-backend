# Context Aligner: Structural Path Finding with DAG + Needleman-Wunsch

## What This Does

This module determines which path through the musical score the performer actually played. It handles structural variations like repeats, da capo, dal segno, and other navigational elements that make the performed sequence different from a simple linear reading of the score.

## The Problem

Musical scores often contain repeat signs, first/second endings, da capo (D.C.), dal segno (D.S.), and codas. A performer might:
- Play a repeated section twice or skip it
- Take the first ending on the first pass, second ending on the repeat
- Jump to a different part of the score following D.C. or D.S. markings

The context aligner figures out exactly which notes were played and in what order, mapping the performance back to the score structure.

## How It Works

### 1. Build Score DAG
Converts the ScoreGraph (from Block 0) into a Directed Acyclic Graph (DAG) where:
- Each node = one beat position in the score
- Edges = possible transitions (next beat, or jump to repeat)

### 2. Extract Pitch Sequences
- Score: Get all note pitches in order from `musical_notes`
- Performance: Get all transcribed pitches in order from Block 1

### 3. Needleman-Wunsch Alignment
Performs global sequence alignment using dynamic programming:
- **Match**: Same pitch in score and performance → +2.0 points
- **Mismatch**: Different pitches → -1.0 points
- **Gap**: Missing note (insertion/deletion) → -0.5 points

The algorithm finds the optimal alignment that maximizes the total score.

### 4. Map to Beat Nodes
Converts the pitch-level alignment back to beat positions, creating the "path" through the score that the performer took.

## Input

Required:
- `score_graph.json`: ScoreGraph with DAG edges (from Block 0)
- `transcription.json`: AMT transcription (from Block 1)

## Output

A context alignment JSON containing:

```json
{
  "selected_path": ["1_1", "1_2", "1_3", "1_4", "2_1", ...],
  "alignment_score": 234.5,
  "pitch_matches": {
    "matches": 187,
    "total_score_notes": 200,
    "total_perf_notes": 195,
    "match_percentage": 93.5
  },
  "metadata": {
    "score_graph": "scoregraph.json",
    "transcription": "transcription.json",
    "method": "DAG + Needleman-Wunsch"
  }
}
```

### Output Fields Explained

- **selected_path**: List of beat node IDs showing which beats the performer played in sequence
- **alignment_score**: Total alignment score (higher = better match)
- **pitch_matches.matches**: Number of exact pitch matches
- **pitch_matches.match_percentage**: What percent of score notes were played correctly

## How to Use

Basic usage:
```bash
python context_aligner.py scoregraph.json transcription.json
```

With custom output path:
```bash
python context_aligner.py scoregraph.json transcription.json --output my_results.json
```

Adjust alignment parameters:
```bash
python context_aligner.py scoregraph.json transcription.json \
  --match-score 3.0 \
  --mismatch-penalty -2.0 \
  --gap-penalty -1.0
```

## Integration with Pipeline

The context aligner runs between Block 1 (AMT) and Block 2 (Temporal Alignment):

```
Block 0: ScoreGraph → scoregraph.json (with edges)
Block 1: AMT → transcription.json
   ↓
Context Aligner → context_alignment.json (which path?)
   ↓
Block 2: Temporal Alignment → alignment_results.json (precise timing)
```

This two-stage approach separates:
1. **Structure** (which notes) - Context Aligner
2. **Timing** (when exactly) - Block 2 DTW

## Algorithm Details

### Needleman-Wunsch Overview
This is a global sequence alignment algorithm originally developed for DNA sequencing. It finds the optimal way to align two sequences by:

1. Creating a scoring matrix [N+1 x M+1] where N=score length, M=performance length
2. Filling the matrix using dynamic programming with scoring rules
3. Backtracking from bottom-right to top-left to find the optimal path

### Scoring Rules
```python
match_score = 2.0           # Reward for same pitch
mismatch_penalty = -1.0     # Penalty for different pitch
gap_penalty = -0.5          # Penalty for missing note
```

These values can be tuned:
- Higher match_score: More strict, prefers exact matches
- More negative penalties: Allows more flexibility with errors

### Why This Works for Music
Unlike simple DTW (which only considers timing), Needleman-Wunsch:
- Handles insertions (extra notes played)
- Handles deletions (notes skipped)
- Finds global optimal match (considers entire piece)
- Works well with pitch sequences (discrete symbols)

## Match Percentage Interpretation

- **>90%**: Excellent match, performer played the score accurately
- **80-90%**: Good match, minor deviations or mistakes
- **70-80%**: Fair match, some structural differences
- **<70%**: Poor match, significant differences or wrong piece

## For Musicians

Think of this as answering the question: "Did the performer take the repeat? Which ending did they play?"

The system looks at all the notes that were actually performed and figures out which path through the score produces that exact sequence. This is especially important for:
- Pieces with multiple repeat sections
- Complex structures with D.C. al Fine or D.S. al Coda
- Comparing different interpretations of the same score

## Technical Notes

### DAG Construction
Uses NetworkX to represent the score as a graph:
- Nodes have attributes: bar, beat, abs_beat, flags (fermata/cadence)
- Edges represent valid transitions between beats
- Currently linear (beat N → beat N+1) but extensible for repeats

### Sequence Extraction
Sorts notes by time before extracting pitches:
- Score: Sort by `offset_beats`
- Performance: Sort by `start_time` or `onset`

This ensures sequences are in correct temporal order.

### Path Mapping
After alignment, maps note-level matches back to beat-level nodes using:
- Find closest beat node to each matched note's timestamp
- Remove duplicates (multiple notes on same beat)
- Result: Sequence of beat positions that were played

## Limitations

1. **Pitch-based only**: Doesn't consider rhythm or timing (that's Block 2's job)
2. **Linear path assumption**: Current implementation assumes one forward path
3. **Transcription quality**: Results depend on Block 1 AMT accuracy
4. **No octave transposition**: Expects pitches to match exactly (MIDI note numbers)

## Future Enhancements

Potential improvements:
- Add rhythm weighting (consider note durations)
- Support octave-invariant matching
- Handle multiple paths through DAG (complex repeat structures)
- Use harmonic context (chord progressions) in addition to pitches
- Confidence weighting based on AMT confidence scores

## What Changed from Original System

This is a completely new component. The original system:
- Assumed linear score reading
- Handled repeats by pre-expanding the score
- No explicit structural path finding

The new context aligner:
- Explicitly models score structure as DAG
- Finds performed path through structural options
- Separates structure from timing concerns
- Provides path confidence metrics
