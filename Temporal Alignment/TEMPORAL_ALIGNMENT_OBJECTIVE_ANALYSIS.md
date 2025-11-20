# Temporal Alignment Layer - Objective Analysis

## Date: 17 November 2025

---

## EXECUTIVE SUMMARY

**Primary Objective:** The temporal alignment layer (Blocks 0, 1, 4, 2) is designed to **ALIGN** the performance with the music score sheet, NOT to evaluate it.

**Purpose:** Create a precise time mapping between score time and performance time that accommodates musical expression (rubato, fermatas, cadences) while maintaining structural integrity.

**Evaluation Role:** The layer produces metrics and visualizations as **diagnostics** to validate alignment quality, but grading happens AFTER all alignment layers are complete.

---

## LAYER ARCHITECTURE: Block 0 → Block 1 → Block 4 → Block 2

### Block 0: ScoreGraph Builder
**Objective:** Create canonical score representation  
**Function:** ALIGNMENT PREPARATION  

```
Input:  score.musicxml / score.mid + score_meta.json
Output: scoregraph.json (linearized beat timeline with repeat expansion)
```

**What It Does:**
- Parses musical score structure (bars, beats, notes, tempo)
- Expands repeats to create "performed" sequence (as musician would play it)
- Flags expressive markings (fermatas, cadences) for tolerance handling
- Creates navigable graph with nodes representing beat positions

**Alignment vs Evaluation:**
- ✅ ALIGNMENT: Creates reference timeline for matching
- ❌ NOT EVALUATION: Doesn't compare performance to score
- 📊 Diagnostics: Reports number of nodes, bars, tempo marks

**Key Technical Detail:**
- Repeat expansion transforms written score M into performance sequence 𝕄
- Example: Verse (bars 1-8) + Chorus (bars 9-16, repeat 2x) → 40 bars total
- This ensures 1:1 mapping potential between score structure and performance

---

### Block 1: Automatic Music Transcription (AMT)
**Objective:** Convert performance audio to symbolic representation  
**Function:** ALIGNMENT PREPARATION  

```
Input:  performance.wav
Output: transcription.json + performance.mid (note events with timing/pitch)
```

**What It Does:**
- Uses Basic Pitch to transcribe audio → MIDI
- Extracts note events: onset time, offset time, pitch, velocity
- Creates symbolic representation comparable to score

**Alignment vs Evaluation:**
- ✅ ALIGNMENT: Creates performance representation in same domain as score
- ❌ NOT EVALUATION: Doesn't judge accuracy or errors
- 📊 Diagnostics: Reports total notes detected, duration

**Important:**
- This is feature extraction, not performance assessment
- Transcription errors are expected and handled by alignment algorithm
- Output feeds into both Context Alignment (pitch sequences) and Temporal Alignment (timing)

---

### Block 4: Beat & Downbeat Detection with Confidence
**Objective:** Identify rhythmic structure in performance  
**Function:** ALIGNMENT ENHANCEMENT  

```
Input:  performance.wav
Output: beats.json (beat times + downbeat markers + confidence scores)
```

**What It Does:**
- Detects beat positions in audio using BeatNet
- Identifies downbeats (measure boundaries)
- Assigns confidence scores (0.0-1.0) based on rhythmic clarity

**Alignment vs Evaluation:**
- ✅ ALIGNMENT: Provides anchoring points for temporal mapping
- ✅ ALIGNMENT: Confidence scores weight cost matrix in DTW
- ❌ NOT EVALUATION: Doesn't grade rhythmic accuracy
- 📊 Diagnostics: Reports beat count, average confidence

**How It Helps Alignment:**
1. **Beat Weighting**: High-confidence beats reduce DTW cost → path prefers these anchors
2. **Drift Prevention**: Strong beats stabilize alignment in unclear passages
3. **Rubato Handling**: Low confidence near fermatas allows timing flexibility

**Example:**
```json
[
  {"t": 0.523, "downbeat": 1, "confidence": 0.912},  // Strong anchor
  {"t": 1.016, "downbeat": 0, "confidence": 0.875},  // Reliable
  {"t": 2.450, "downbeat": 0, "confidence": 0.234}   // Uncertain (fermata?)
]
```

---

### Block 2: Symbolic ↔ Symbolic Alignment (Core DTW)
**Objective:** Create precise time mapping between score and performance  
**Function:** PRIMARY ALIGNMENT EXECUTION  

```
Input:  scoregraph.json + performance.mid + beats.json (optional)
Output: alignment_results.json (score_time ↔ perf_time mapping + metrics)
```

**What It Does:**

#### Step 1: Feature Extraction
- Converts score and performance to **chromagram features** (12-D pitch class vectors)
- Creates comparable representations in same feature space
- Handles synthesis via pretty_midi for uniform processing

#### Step 2: Cost Matrix Construction
- Computes cosine distance between all frame pairs
- Optionally applies **beat weighting**: reduces cost near high-confidence beats
- Handles NaN values (silent frames) with epsilon padding

#### Step 3: DTW with Musical Intelligence
**Three key enhancements for musical alignment:**

1. **Sakoe-Chiba Band Constraint** (band_radius=0.25)
   - Constrains warping path to stay within realistic tempo range
   - Prevents absurd alignments (beginning → end)
   - Allows natural tempo variation while maintaining structure

2. **Beat-Weighted Cost Matrix** (uses Block 4 output)
   - Reduces alignment cost near high-confidence beats
   - Encourages path to pass through strong rhythmic anchors
   - Stabilizes alignment in rhythmically clear sections

3. **Adaptive Step Weights** (fermata/cadence awareness)
   - Detects fermata and cadence flags from ScoreGraph
   - Reduces horizontal/vertical step penalties near these points
   - Allows natural time stretching at expressive moments
   - Default weights: [1.0, 1.0, 1.0] → Relaxed: [1.0, 0.7, 0.7]

#### Step 4: Time Mapping Generation
- Extracts warping path: [(score_frame_i, perf_frame_j)]
- Converts frame indices to time in seconds
- Creates dense time map for downstream use

**Mathematical Formulation:**
```
Score Features:  X ∈ ℝ^(12×N)  (N = score frames)
Perf Features:   Y ∈ ℝ^(12×M)  (M = performance frames)

Cost Matrix:     C[i,j] = cosine_distance(X[:,i], Y[:,j])
                        × beat_weight[j]  (if beats available)

DTW Recurrence:  D[i,j] = C[i,j] + min(
                   w_diag × D[i-1,j-1],    // Match
                   w_horiz × D[i,j-1],     // Performance stretch
                   w_vert × D[i-1,j]       // Performance compress
                 )

Warping Path:    wp = backtrack(D)
Time Mapping:    {(t_score[i], t_perf[j]) for (i,j) in wp}
```

**Alignment vs Evaluation:**
- ✅ ALIGNMENT: Creates precise temporal correspondence
- ✅ ALIGNMENT: Handles expressive timing as natural variation
- ✅ ALIGNMENT: Accommodates rubato, fermatas, tempo changes
- ❌ NOT EVALUATION: Doesn't judge if timing deviations are "good" or "bad"
- 📊 Diagnostics: Confidence score, DTW distance, path length

**Output Example:**
```json
{
  "time_mapping": [
    {"score_time": 0.0, "perf_time": 0.0, "score_frame": 0, "perf_frame": 0},
    {"score_time": 0.5, "perf_time": 0.7, "score_frame": 22, "perf_frame": 31},
    ...
  ],
  "dtw_distance": 7.06,
  "confidence": 0.946,
  "alignment_metadata": {
    "beat_weighting_used": true,
    "adaptive_weights_used": true,
    "band_constraint_radius": 0.25
  }
}
```

---

## METRICS & VISUALIZATIONS: DIAGNOSTIC, NOT EVALUATIVE

The temporal alignment layer produces various metrics and visualizations. These serve to:
1. **Validate alignment quality** (is the mapping reliable?)
2. **Debug alignment failures** (where did DTW struggle?)
3. **Provide transparency** (show users what happened)

**These are NOT grading metrics.** They assess alignment confidence, not performance quality.

### Metrics Produced:

#### 1. Alignment Confidence (0.0 - 1.0)
**What It Measures:** Mean cosine similarity along warping path  
**Purpose:** Indicates how well score and performance features matched  
**Interpretation:**
- High (>0.85): Strong feature correlation, reliable alignment
- Medium (0.6-0.85): Reasonable alignment, some uncertainty
- Low (<0.6): Poor feature match, alignment may be unreliable

**NOT Performance Grading:** Low confidence could mean:
- Transcription errors (AMT issue, not performer error)
- Different instrumentation (timbre mismatch)
- Background noise
- Legitimate performance with poor audio quality

#### 2. DTW Distance (lower = better)
**What It Measures:** Cumulative cost of warping path  
**Purpose:** Quantifies alignment difficulty  
**Interpretation:**
- Low: Easy alignment (similar tempos, clear features)
- High: Difficult alignment (requires lots of warping)

**NOT Performance Grading:** High distance could mean:
- Extreme rubato (artistic choice)
- Transcription challenges
- Feature extraction issues

#### 3. Path Length
**What It Measures:** Number of alignment points  
**Purpose:** Shows alignment granularity  
**Interpretation:** More points = finer temporal resolution

#### 4. Tempo Ratios (along warping path)
**What It Measures:** Local tempo ratio = Δt_perf / Δt_score  
**Purpose:** Reveals where performer sped up or slowed down  
**Interpretation:**
- Ratio = 1.0: Perfect tempo match
- Ratio > 1.0: Performer slower than score
- Ratio < 1.0: Performer faster than score

**NOT Performance Grading:** Shows tempo variation, doesn't judge it

### Visualizations Produced:

#### 1. Alignment Path Plot
- X-axis: Score time (seconds)
- Y-axis: Performance time (seconds)
- Diagonal line = perfect tempo match
- Deviations show tempo variations

**Purpose:** Visual validation that alignment makes musical sense

#### 2. Tempo Deviation Plot
- Shows tempo ratio over time
- Blue = speeding up, Red = slowing down
- Reference line at 1.0 (no deviation)

**Purpose:** Identify where tempo changed

#### 3. Warping Path Visualization
- Frame-level alignment path
- Shows DTW trajectory through cost matrix

**Purpose:** Technical validation for debugging

#### 4. Quality Metrics Bar Chart
- Shows DTW distance, confidence, durations
- Color-coded for quick assessment

**Purpose:** At-a-glance alignment quality check

---

## KEY DISTINCTION: ALIGNMENT vs EVALUATION

### What Temporal Alignment DOES:
✅ **Find correspondences** between score positions and performance times  
✅ **Handle expressive timing** (rubato, fermatas) as natural musical variation  
✅ **Create time map** for downstream analysis  
✅ **Provide diagnostics** to validate mapping quality  
✅ **Accommodate musical expression** without penalizing it  

### What Temporal Alignment DOES NOT DO:
❌ **Grade performance quality** (too fast/slow is not judged as error)  
❌ **Evaluate accuracy** (wrong notes are transcription issues, not alignment issues)  
❌ **Assess musicality** (rubato is mapped, not criticized)  
❌ **Produce final scores** (that comes later in evaluation layer)  

### The Musical Analogy:
**Alignment = Translation**  
"At 10 seconds into the score, the performer was at 12 seconds in the recording."

**Evaluation = Judgment**  
"The performer played 20% too slowly in this section - Grade: C+"

**Temporal Alignment provides the first. Grading happens AFTER, using the alignment as input.**

---

## WHY SEPARATE ALIGNMENT FROM EVALUATION?

### 1. Musical Expression is NOT Error
Musicians intentionally deviate from written tempo for artistic effect:
- **Rubato**: Speeding up or slowing down expressively
- **Fermatas**: Holding notes longer than written
- **Cadential ritardando**: Slowing at phrase endings

If alignment penalized these, it would fail on expressive performances.

### 2. Alignment Must Be Robust First
Before grading, we need reliable correspondences:
- Which score note maps to which performance moment?
- Where did the performer repeat sections?
- How did tempo vary across the piece?

Without accurate alignment, evaluation is meaningless.

### 3. Grading Requires Context
A "slow" tempo might be:
- ✅ Intentional and beautiful (Grade: A)
- ❌ Struggling with difficult passage (Grade: C)
- ✅ Marked "Adagio" in score (Grade: A)

Alignment provides the "what happened" data. Evaluation layer decides "was it good?"

---

## CURRENT STATE: ALIGNMENT COMPLETE, EVALUATION SEPARATE

### What Currently Exists:

**Temporal Alignment Pipeline:**
```
Block 0 (ScoreGraph) → Block 1 (AMT) → Block 4 (Beats) → Block 2 (DTW)
                                                              ↓
                                                    alignment_results.json
                                                              ↓
                                                      [Visualizations]
```

**Output:** 
- Time mapping (score ↔ performance)
- Alignment confidence metrics
- Tempo variation curves
- Diagnostic visualizations

**Evaluation/Grading Layer (Separate):**
- Uses alignment output as input
- Compares performance to score expectations
- Applies grading rubrics
- Produces performance scores

### Integration Points:

From `main_hybrid_v02.py`:
```python
def run_temporal_alignment(...):
    """Run temporal alignment blocks (Block 0 → Block 1 → Block 2)"""
    # Block 0: Build ScoreGraph
    scoregraph = build_scoregraph(score_path, meta_path, None)
    
    # Block 1: Transcribe audio
    transcription_result = transcribe_audio_basic_pitch(audio_path, ...)
    
    # Block 4: Beat detection (optional enhancement)
    # beats_json = estimate_beats(audio_path, ...)
    
    # Block 2: DTW alignment
    aligner = EnhancedSymbolicAligner(gpu_manager=gpu_manager)
    alignment_result = aligner.align_score_performance(
        score_graph_path=scoregraph_path,
        performance_midi_path=midi_path,
        beats_json_path=beats_json_path,  # Optional
        output_dir=block2_dir
    )
    
    # Return alignment for downstream use
    return {
        'scoregraph': scoregraph,
        'transcription': transcription_result,
        'alignment': alignment_result,
        ...
    }
```

**Note:** This returns alignment data. Grading happens in a separate evaluation layer.

---

## RECOMMENDATIONS

### 1. Keep Alignment and Evaluation Separate ✅

**Current approach is correct:**
- Temporal alignment focuses on finding correspondences
- Evaluation layer (implemented separately) uses alignment for grading
- Clean separation of concerns

### 2. Enhance Alignment Diagnostics (Good to Have) 📊

**Current visualizations are valuable:**
- Alignment path plot validates mapping quality
- Tempo variation shows expressive timing
- Confidence metrics indicate reliability

**These help users understand:**
- "The alignment worked well in this section"
- "DTW struggled here - maybe check transcription quality"
- "Performance had extreme rubato at measure 45"

**Recommendation:** Keep these visualizations as diagnostic tools, clearly labeled as "alignment quality" not "performance quality"

### 3. Document the Pipeline Flow Clearly 📝

**Users should understand:**
```
Input → Alignment Layers → Evaluation Layer → Output

Alignment asks: "What corresponds to what?"
Evaluation asks: "Was it played correctly?"
```

### 4. Consider Separating Visualization into Two Types

**Type 1: Alignment Diagnostics** (current Block 2 output)
- Alignment path
- Warping path
- DTW metrics
- Confidence scores
- Purpose: Validate alignment quality

**Type 2: Performance Evaluation** (evaluation layer output)
- Pitch accuracy grades
- Rhythm accuracy scores  
- Tempo appropriateness ratings
- Overall performance grade
- Purpose: Assess performance quality

### 5. Maintain Block 2 Evaluation Graphs as Diagnostic Tools ✅

**The current graphs at the end of Block 2 are valuable:**
- They validate that alignment succeeded
- They help debug when alignment fails
- They provide transparency for users

**Important:** Label them clearly as:
- "Alignment Quality Metrics" (NOT "Performance Quality")
- "Temporal Correspondence Validation"
- "DTW Diagnostic Visualizations"

This prevents confusion about their purpose.

---

## CONCLUSION

### Primary Finding:
**The temporal alignment layer (Blocks 0, 1, 4, 2) is correctly designed for ALIGNMENT, not EVALUATION.**

### Objective Confirmed:
The layer's purpose is to:
1. Create canonical score representation (Block 0)
2. Transcribe performance to comparable format (Block 1)
3. Identify rhythmic anchors (Block 4)
4. Find precise temporal correspondences (Block 2)

This provides the foundation for downstream evaluation, but does not perform grading itself.

### Current Implementation Status:
✅ **Alignment objective is clear and correctly implemented**  
✅ **Musical expression is handled appropriately (not penalized)**  
✅ **Diagnostics are useful for validation**  
✅ **Separation from evaluation is maintained**  

### Answer to Your Question:

> "Is the objective of the layer to align the performance with the score sheet or to evaluate the performance against the score sheet?"

**Answer:** The objective is to **ALIGN** the performance with the score sheet.

- Alignment creates the mapping (score time ↔ performance time)
- Evaluation happens later, USING this alignment as input
- The graphs/metrics at the end of Block 2 are diagnostic tools to validate alignment quality, not performance quality

### Regarding Evaluation Graphs:

> "It is good to have evaluation or graphs which are present at the end of this layer separately"

**Answer:** ✅ Yes, the current approach is good.

- The graphs at the end of Block 2 serve as **alignment diagnostics**
- They help validate that the temporal mapping is reliable
- They are separate from performance evaluation (which happens in a different layer)
- Keep them, but ensure they are clearly labeled as alignment quality metrics

---

## TECHNICAL SUMMARY

### Block Sequence: 0 → 1 → 4 → 2

| Block | Name | Input | Output | Objective |
|-------|------|-------|--------|-----------|
| **0** | ScoreGraph | MusicXML/MIDI | scoregraph.json | Create reference timeline |
| **1** | AMT | Audio WAV | transcription.json + MIDI | Transcribe performance |
| **4** | Beat Detection | Audio WAV | beats.json | Find rhythmic anchors |
| **2** | DTW Alignment | All above | alignment_results.json | Map score ↔ performance |

### Key Algorithms:

1. **Repeat Expansion** (Block 0): Unfolds score structure
2. **Basic Pitch Transcription** (Block 1): Audio → symbolic
3. **BeatNet Detection** (Block 4): Rhythm tracking with confidence
4. **DTW with Enhancements** (Block 2):
   - Beat-weighted cost matrix
   - Sakoe-Chiba band constraints
   - Adaptive fermata/cadence tolerance

### Output Format:
```json
{
  "time_mapping": [...],        // Dense score↔perf correspondence
  "dtw_distance": 7.06,         // Alignment difficulty
  "confidence": 0.946,          // Feature correlation quality
  "alignment_metadata": {...}   // Configuration used
}
```

### Distinction:
- **These metrics assess ALIGNMENT quality** (did we find good correspondences?)
- **NOT performance quality** (did the musician play well?)

---

**Document Purpose:** Clarify the objective and scope of the temporal alignment layer for future development and integration with evaluation systems.

**Status:** Complete analysis based on codebase review (17 Nov 2025)
