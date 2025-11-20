# Temporal Alignment System: Rubato, Fermata, and Beat Probability Analysis

## Executive Summary

This document provides a comprehensive analysis of three critical features requested for the temporal alignment system:

1. **Rubato and Fermata Handling** - Variable tempo and extended note durations
2. **Beat and Downbeat Probability** - Beat detection confidence weighting
3. **Adaptive Tolerance Near Cadences/Fermatas** - Context-aware warping constraints

**Status**: ⚠️ **PARTIALLY IMPLEMENTED** - Some infrastructure exists, but key features are missing or incomplete.

---

## 1. Rubato and Fermata Handling

### ✅ What IS Implemented

#### Block 0: ScoreGraph - Fermata Detection (Metadata Only)
**File**: `Block_0_ScoreGraph/build_scoregraph_with_repeats.py` (lines 141-144)

```python
# Attach flags from meta or segmentation
if 'fermatas' in meta and node_id in meta['fermatas']:
    flags.append('fermata')
if segmentation and 'cadences' in segmentation and node_id in segmentation['cadences']:
    flags.append('cadence')
```

**Status**: ✅ **Metadata Collection Only**
- Fermata and cadence positions ARE detected and stored as flags in the ScoreGraph
- Each node can have `flags: ['fermata']` or `flags: ['cadence']`
- This information is available but **NOT USED** in subsequent alignment steps

#### Block 3: Tempo Curve Analysis
**File**: `Block_3_TempoPhaseCurves/derive_curves.py` (lines 8-30)

```python
# Compute tempo curve (finite differences)
abs_beats = np.array([p[0] for p in path])
perf_times = np.array([p[1] for p in path])
d_abs_beat = np.diff(abs_beats)
d_time = np.diff(perf_times)
bpm = np.divide(d_abs_beat, d_time, out=np.zeros_like(d_abs_beat), where=d_time!=0) * 60
```

**Status**: ✅ **Post-hoc Analysis**
- Tempo variations ARE computed AFTER alignment
- This allows observing rubato/fermata effects in the performance
- However, this is **REACTIVE** (analyzing results) not **PROACTIVE** (informing the alignment)

### ❌ What IS NOT Implemented

#### Variable Tempo in Alignment Cost Function
**Issue**: The DTW alignment treats all time regions equally.

**Current Implementation** (`Block_2_SymbolicAlignment/align_symbolic_enhanced.py`, lines 241-252):
```python
def dtw_alignment(self, X: np.ndarray, Y: np.ndarray, 
                  metric: str = 'cosine') -> Tuple[np.ndarray, float]:
    """Perform DTW alignment using librosa"""
    try:
        # Use librosa's DTW implementation
        D, wp = librosa.sequence.dtw(X=X.T, Y=Y.T, metric=metric)
        # ❌ No fermata/cadence awareness
        # ❌ No adaptive step weights
        # ❌ Uniform cost across all temporal regions
```

**What's Missing**:
- No special handling for regions marked with fermata flags
- No increased temporal flexibility near cadences
- Uniform DTW step penalties throughout the piece

#### Recommended Fix: Adaptive Step Weights

**Where**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`
**Function**: `dtw_alignment()` method

**Solution**:
```python
def dtw_alignment(self, X: np.ndarray, Y: np.ndarray, 
                  score_graph: Dict = None,
                  metric: str = 'cosine') -> Tuple[np.ndarray, float]:
    """
    Perform DTW alignment with fermata/cadence awareness
    
    Args:
        X: Score features [n_features, n_frames_score]
        Y: Performance features [n_features, n_frames_perf]
        score_graph: ScoreGraph with node flags for fermatas/cadences
        metric: Distance metric
    """
    
    # Step 1: Create adaptive weights based on fermata/cadence flags
    if score_graph and 'nodes' in score_graph:
        weights_mul = self._compute_adaptive_weights(
            n_frames=X.shape[1],
            nodes=score_graph['nodes']
        )
    else:
        weights_mul = None
    
    # Step 2: Use librosa DTW with adaptive weights
    try:
        D, wp = librosa.sequence.dtw(
            X=X.T, 
            Y=Y.T, 
            metric=metric,
            weights_mul=weights_mul,  # ✅ NEW: Adaptive weights
            global_constraints=False   # Allow flexibility near fermatas
        )
        
        distance = D[-1, -1]
        logger.info(f"DTW with adaptive weights: distance={distance:.4f}")
        return wp, distance
    except Exception as e:
        logger.warning(f"Adaptive DTW failed: {e}")
        # Fallback to standard DTW
        return self._dtw_scipy(X, Y, metric)

def _compute_adaptive_weights(self, n_frames: int, nodes: List[Dict]) -> np.ndarray:
    """
    Compute multiplicative step weights that allow more temporal flexibility
    near fermatas and cadences.
    
    Returns:
        weights_mul: Array of shape [3,] for [diagonal, horizontal, vertical] steps
                     Lower values = more flexibility
    """
    # Default step weights (equal weighting)
    base_weights = np.array([1.0, 1.0, 1.0])
    
    # Check if we're in a fermata/cadence region
    # This would require mapping frames back to beat positions
    # For now, return uniform weights
    
    # TODO: Implement frame-to-beat mapping
    # TODO: Detect fermata/cadence regions
    # TODO: Reduce weights (e.g., 0.5x) in those regions
    
    return base_weights
```

**Variables to Update**:
1. `dtw_alignment()` signature - add `score_graph` parameter
2. `enhanced_alignment()` method - pass score_graph through
3. Add new method `_compute_adaptive_weights()`

---

## 2. Beat and Downbeat Probability

### ✅ What IS Implemented

#### Block 4: Beat Detection (Basic)
**File**: `Block_4_BeatDownbeat/estimate_beats.py` (lines 7-21)

```python
def estimate_beats(audio_path, beats_path):
    # Run BeatNet
    beatnet = BeatNet()
    beats, downbeats = beatnet.process(audio_path)
    # Format output
    beats_json = []
    for t in beats:
        beats_json.append({"t": t, "downbeat": 0})
    for t in downbeats:
        beats_json.append({"t": t, "downbeat": 1})
```

**Status**: ⚠️ **Detection Only, No Probabilities**
- Beat and downbeat TIMES are detected
- Binary flag for downbeat (0 or 1)
- **NO confidence scores or probabilities stored**

### ❌ What IS NOT Implemented

#### Beat Probability Extraction
**Issue**: BeatNet outputs include confidence scores, but they are NOT captured.

**What's Missing**:
```python
# Current: Only times, no confidence
beats_json.append({"t": t, "downbeat": 0})

# Should be:
beats_json.append({
    "t": t, 
    "downbeat": 0,
    "confidence": confidence_score  # ❌ MISSING
})
```

#### Beat Probability as Alignment Weight
**Issue**: Even if beat probabilities were captured, they are NOT used in DTW alignment.

**Current Flow**:
```
Block 4 (Beat Detection) → beats.json
                              ↓
                         [NOT USED IN BLOCK 2]
Block 2 (DTW Alignment) ← scoregraph.json + perf.mid only
```

**What's Missing**: Beat probabilities should influence alignment cost.

#### Recommended Fix: Beat-Weighted DTW

**Where**: `Block_4_BeatDownbeat/estimate_beats.py` + `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`

**Step 1: Capture Beat Probabilities**
```python
# File: Block_4_BeatDownbeat/estimate_beats.py
def estimate_beats(audio_path, beats_path):
    beatnet = BeatNet()
    
    # ✅ NEW: Get full output including confidence
    output = beatnet.process(audio_path, return_confidence=True)
    
    beats_json = []
    for beat_info in output['beats']:
        beats_json.append({
            "t": beat_info['time'],
            "downbeat": beat_info['is_downbeat'],
            "confidence": beat_info['confidence']  # ✅ NEW
        })
    
    with open(beats_path, 'w') as f:
        json.dump(beats_json, f, indent=2)
```

**Step 2: Use Beat Probabilities in DTW Cost**
```python
# File: Block_2_SymbolicAlignment/align_symbolic_enhanced.py
def enhanced_alignment(self, score_midi, perf_midi, beats_json=None):
    """
    Perform alignment with optional beat probability weighting
    
    Args:
        beats_json: Beat detection results with confidence scores
    """
    # Extract features
    score_chroma = self.midi_to_chroma(score_midi, max_duration)
    perf_chroma = self.midi_to_chroma(perf_midi, max_duration)
    
    # ✅ NEW: Apply beat-weighted cost if beats available
    if beats_json:
        cost_matrix = self._compute_beat_weighted_cost(
            score_chroma, 
            perf_chroma, 
            beats_json
        )
        D, wp = librosa.sequence.dtw(C=cost_matrix, backtrack=True)
    else:
        # Standard DTW
        D, wp = librosa.sequence.dtw(X=score_chroma.T, Y=perf_chroma.T)
    
    # ... rest of alignment

def _compute_beat_weighted_cost(self, X, Y, beats_json):
    """
    Compute cost matrix with beat probability weighting
    
    High-confidence beats get lower cost → preferred alignment anchors
    """
    from scipy.spatial.distance import cdist
    
    # Base cost matrix (cosine distance)
    C = cdist(X.T, Y.T, metric='cosine')
    
    # Map beat times to frames
    beat_frames = librosa.time_to_frames(
        [b['t'] for b in beats_json],
        sr=self.sr,
        hop_length=self.hop_length
    )
    beat_confidences = np.array([b['confidence'] for b in beats_json])
    
    # Create confidence mask for Y (performance) axis
    conf_mask = np.ones(Y.shape[1])
    for frame, conf in zip(beat_frames, beat_confidences):
        if 0 <= frame < len(conf_mask):
            # Reduce cost near high-confidence beats
            window = slice(max(0, frame-2), min(len(conf_mask), frame+3))
            conf_mask[window] *= (1.0 / (1.0 + conf))  # Lower = better
    
    # Apply mask to cost matrix
    C = C * conf_mask[np.newaxis, :]
    
    return C
```

**Variables to Update**:
1. `estimate_beats()` - add confidence extraction
2. `enhanced_alignment()` signature - add `beats_json` parameter
3. Add new method `_compute_beat_weighted_cost()`
4. Integration in `align_score_performance()` - load and pass beats.json

---

## 3. Adaptive Tolerance Near Cadences/Fermatas

### ✅ What IS Documented (But Not Implemented)

#### README Documentation
**File**: `Temporal Alignment/README.md` (line 121)

```
- Band constraint (Sakoe–Chiba) for tempo stability: 
  | i − α j | ≤ w, where α is global tempo ratio estimate 
  and w a half-width; improves robustness and speed.
```

**Status**: ⚠️ **DOCUMENTED BUT NOT IMPLEMENTED**
- The README describes Sakoe-Chiba band constraints
- These ARE supported by librosa's DTW (`global_constraints=True`, `band_rad=0.25`)
- However, the implementation does NOT use these parameters

#### Block 6: Rubato Tolerance (Placeholder)
**File**: `Block_6_ToleranceRelock/tolerance_and_relock.py` (lines 20-26)

```python
# Simulate confidence drop and relock
conf = float(row['conf'])
if conf < 0.5:
    # Perform coarse DTW on last few seconds (placeholder logic)
    # Use SyncToolbox DTW API for actual relock
    # Here, just copy previous stable value
```

**Status**: ⚠️ **PLACEHOLDER ONLY**
- Conceptual framework exists
- Actual adaptive tolerance logic NOT implemented

### ❌ What IS NOT Implemented

#### Static Band Constraint
**Current Implementation** (`Block_2_SymbolicAlignment/align_symbolic_enhanced.py`, line 242):
```python
D, wp = librosa.sequence.dtw(X=X.T, Y=Y.T, metric=metric)
# ❌ global_constraints=False (default)
# ❌ band_rad not specified
# ❌ No adaptive band width
```

**What's Missing**:
- No Sakoe-Chiba band constraint applied
- DTW explores full alignment space → slower and less robust
- No tempo ratio estimation to set band center

#### Adaptive Band Width
**What's Missing**: Band width should EXPAND near fermatas/cadences.

**Concept**:
```
Normal regions:    |i - αj| ≤ w_normal    (e.g., w=20 frames)
Fermata regions:   |i - αj| ≤ w_fermata   (e.g., w=50 frames)
Cadence regions:   |i - αj| ≤ w_cadence   (e.g., w=40 frames)
```

This allows:
- Tighter constraint (faster, more stable) in metronomic passages
- Looser constraint (flexible timing) near expressive moments

#### Recommended Fix: Adaptive Band Constraints

**Where**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`

**Solution**:
```python
def dtw_alignment_adaptive_band(self, X: np.ndarray, Y: np.ndarray,
                                 score_graph: Dict = None,
                                 metric: str = 'cosine') -> Tuple[np.ndarray, float]:
    """
    DTW with adaptive Sakoe-Chiba band width based on fermatas/cadences
    """
    
    # Step 1: Estimate global tempo ratio α
    alpha = self._estimate_tempo_ratio(X, Y)
    
    # Step 2: Compute frame-wise band width
    if score_graph:
        band_rad_adaptive = self._compute_adaptive_band_width(
            n_frames=X.shape[1],
            nodes=score_graph['nodes'],
            base_band_rad=0.25
        )
    else:
        band_rad_adaptive = 0.25  # Default 25% deviation
    
    # Step 3: Apply adaptive band constraint
    # Note: librosa.sequence.dtw supports only global band_rad,
    # so we need to use a custom implementation or pre-compute C with mask
    
    C = self._compute_distance_with_adaptive_band(
        X, Y, metric, alpha, band_rad_adaptive
    )
    
    D, wp = librosa.sequence.dtw(C=C, backtrack=True)
    
    return wp, D[-1, -1]

def _estimate_tempo_ratio(self, X: np.ndarray, Y: np.ndarray) -> float:
    """
    Estimate global tempo ratio α = N/M
    where N = score frames, M = performance frames
    """
    return X.shape[1] / Y.shape[1]

def _compute_adaptive_band_width(self, n_frames: int, 
                                  nodes: List[Dict],
                                  base_band_rad: float) -> np.ndarray:
    """
    Compute frame-by-frame band width
    
    Returns:
        band_widths: Array of shape [n_frames] with adaptive band radius
    """
    band_widths = np.full(n_frames, base_band_rad)
    
    # Map nodes to frames
    for node in nodes:
        if 'fermata' in node.get('flags', []) or 'cadence' in node.get('flags', []):
            # TODO: Map abs_beat to frame index
            # For now, this is a placeholder
            # frame_idx = self._beat_to_frame(node['abs_beat'])
            
            # Widen band near fermata/cadence
            # window = slice(max(0, frame_idx-10), min(n_frames, frame_idx+10))
            # band_widths[window] = base_band_rad * 2.0  # 2x wider
            pass
    
    return band_widths

def _compute_distance_with_adaptive_band(self, X, Y, metric, alpha, band_rad):
    """
    Compute distance matrix with adaptive Sakoe-Chiba band mask
    """
    from scipy.spatial.distance import cdist
    
    C = cdist(X.T, Y.T, metric=metric)
    N, M = C.shape
    
    # Create adaptive band mask
    for i in range(N):
        for j in range(M):
            # Check if (i,j) is within adaptive band
            expected_j = alpha * i
            deviation = abs(j - expected_j)
            max_deviation = band_rad * M  # Can be adaptive per frame
            
            if deviation > max_deviation:
                C[i, j] = np.inf  # Exclude from search space
    
    return C
```

**Variables to Update**:
1. Add new method `dtw_alignment_adaptive_band()`
2. Add helper methods: `_estimate_tempo_ratio()`, `_compute_adaptive_band_width()`, `_compute_distance_with_adaptive_band()`
3. Integrate frame-to-beat and beat-to-frame mapping utilities
4. Update `enhanced_alignment()` to use adaptive band DTW

---

## Implementation Priority Roadmap

### Priority 1: Critical Features (Immediate)

#### 1.1 Capture Beat Probabilities
- **File**: `Block_4_BeatDownbeat/estimate_beats.py`
- **Change**: Extract and store confidence scores from BeatNet
- **Effort**: LOW (1-2 hours)
- **Impact**: HIGH (enables downstream weighting)

#### 1.2 Apply Sakoe-Chiba Band Constraint
- **File**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`
- **Change**: Enable `global_constraints=True, band_rad=0.25` in librosa DTW
- **Effort**: LOW (30 minutes)
- **Impact**: MEDIUM (faster, more robust alignment)

### Priority 2: Enhanced Features (Short-term)

#### 2.1 Beat-Weighted DTW Cost
- **File**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`
- **Change**: Implement `_compute_beat_weighted_cost()` method
- **Effort**: MEDIUM (4-6 hours)
- **Impact**: HIGH (improves alignment accuracy)

#### 2.2 Fermata/Cadence-Aware Step Weights
- **File**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`
- **Change**: Implement `_compute_adaptive_weights()` method
- **Effort**: MEDIUM (4-6 hours)
- **Impact**: HIGH (handles rubato/fermata correctly)

### Priority 3: Advanced Features (Long-term)

#### 3.1 Adaptive Band Width
- **File**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`
- **Change**: Implement frame-wise adaptive Sakoe-Chiba bands
- **Effort**: HIGH (8-12 hours)
- **Impact**: VERY HIGH (optimal handling of expressive timing)

#### 3.2 Frame-to-Beat Mapping Utilities
- **File**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`
- **Change**: Add bidirectional mapping between frames and beat positions
- **Effort**: MEDIUM (4-6 hours)
- **Impact**: MEDIUM (enables spatial feature mapping)

---

## Summary Table

| Feature | Status | Location | Implementation Gap |
|---------|--------|----------|-------------------|
| **Rubato/Fermata Detection** | ✅ Partial | Block 0 | Flags stored but not used |
| **Flexible Timing in DTW** | ❌ Missing | Block 2 | No adaptive step weights |
| **Beat Detection** | ✅ Partial | Block 4 | Times only, no probabilities |
| **Beat Probability Storage** | ❌ Missing | Block 4 | Confidence scores not captured |
| **Beat-Weighted Alignment** | ❌ Missing | Block 2 | Beat info not used in DTW |
| **Sakoe-Chiba Band** | ❌ Missing | Block 2 | Documented but not enabled |
| **Adaptive Band Width** | ❌ Missing | Block 2 | No fermata/cadence adaptation |
| **Tempo Curve Analysis** | ✅ Complete | Block 3 | Post-hoc only (not proactive) |

---

## Code Changes Checklist

### Block 2: `align_symbolic_enhanced.py`

```python
# ✅ Add these imports
from typing import Dict, List, Optional

# ✅ Modify __init__
class EnhancedSymbolicAligner:
    def __init__(self, ..., enable_adaptive_dtw=True):
        self.enable_adaptive_dtw = enable_adaptive_dtw

# ✅ Update dtw_alignment signature
def dtw_alignment(self, X, Y, metric='cosine', 
                  score_graph=None,  # NEW
                  beats_json=None):   # NEW

# ✅ Add new methods
def _compute_adaptive_weights(self, n_frames, nodes):
    # Implementation for fermata/cadence weights
    
def _compute_beat_weighted_cost(self, X, Y, beats_json):
    # Implementation for beat probability weighting
    
def _estimate_tempo_ratio(self, X, Y):
    # Implementation for tempo ratio estimation
    
def _compute_adaptive_band_width(self, n_frames, nodes, base_band_rad):
    # Implementation for adaptive Sakoe-Chiba bands
```

### Block 4: `estimate_beats.py`

```python
# ✅ Modify estimate_beats function
def estimate_beats(audio_path, beats_path):
    beatnet = BeatNet()
    
    # ✅ NEW: Request confidence scores
    output = beatnet.process(audio_path, return_confidence=True)
    
    beats_json = []
    for beat in output:
        beats_json.append({
            "t": beat['time'],
            "downbeat": beat['is_downbeat'],
            "confidence": beat['confidence']  # ✅ NEW
        })
```

### Integration: Load beats.json in Block 2

```python
# ✅ In align_score_performance method
def align_score_performance(self, score_graph_path, 
                           performance_midi_path,
                           beats_json_path=None):  # ✅ NEW parameter
    
    # Load existing inputs
    score_graph = self.load_score_graph(score_graph_path)
    perf_midi = self.load_performance_midi(performance_midi_path)
    
    # ✅ NEW: Load beat probabilities if available
    beats_json = None
    if beats_json_path and Path(beats_json_path).exists():
        with open(beats_json_path, 'r') as f:
            beats_json = json.load(f)
    
    # Pass to enhanced_alignment
    alignment_results = self.enhanced_alignment(
        score_midi, 
        perf_midi,
        score_graph=score_graph,  # ✅ NEW
        beats_json=beats_json      # ✅ NEW
    )
```

---

## Testing Recommendations

### Test Case 1: Fermata Handling
**Input**: Score with explicit fermata at measure 4, beat 3
**Expected**: Alignment shows increased temporal flexibility at that location
**Validation**: Check local tempo ratio variance near fermata vs. other regions

### Test Case 2: Beat Probability Weighting
**Input**: Performance with clear downbeats (high confidence) and weak inner beats (low confidence)
**Expected**: Alignment anchors strongly to downbeats
**Validation**: Compare alignment path with/without beat weighting

### Test Case 3: Cadence Rubato
**Input**: Performance with ritardando at final cadence
**Expected**: Alignment successfully follows tempo deceleration
**Validation**: Tempo curve should show smooth deceleration, not discrete jumps

---

## Conclusion

The temporal alignment system has a **solid foundation** with comprehensive score parsing, beat detection, and DTW alignment. However, **three critical features are either incomplete or missing**:

1. **Rubato/Fermata** - Flags are detected but NOT used to adapt alignment flexibility
2. **Beat Probabilities** - Beat times are detected but confidence scores are NOT captured or used
3. **Adaptive Tolerance** - Band constraints are documented but NOT implemented; no adaptive width near expressive moments

**Recommended Action**: Implement Priority 1 changes first (beat probabilities + band constraints) for immediate improvement, then proceed to Priority 2 (weighting functions) for advanced rubato handling.

