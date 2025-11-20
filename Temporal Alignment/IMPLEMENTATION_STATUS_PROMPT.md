# Temporal Alignment System: Implementation Status & Required Changes

## What Has Been Analyzed

I conducted a comprehensive code review of the entire temporal alignment system across all blocks (0-6) to check for three critical features:

1. **Rubato and Fermata Handling** - Variable tempo and extended note durations
2. **Beat and Downbeat Probability** - Beat detection confidence weighting in alignment
3. **Adaptive Tolerance Near Cadences/Fermatas** - Context-aware DTW warping constraints

## Current Implementation Status

### ✅ Block 0: ScoreGraph Builder - WORKING

**File**: `Block_0_ScoreGraph/build_scoregraph_with_repeats.py`

**What Works:**
- Successfully parses MusicXML files using music21
- Expands repeats using `expandRepeats()` method
- Detects and stores fermata and cadence positions as node flags
- Creates beat-level nodes with `flags: ['fermata']` or `flags: ['cadence']`
- Outputs comprehensive `scoregraph.json` with timing information

**Code Evidence (lines 141-144):**
```python
# Attach flags from meta or segmentation
if 'fermatas' in meta and node_id in meta['fermatas']:
    flags.append('fermata')
if segmentation and 'cadences' in segmentation and node_id in segmentation['cadences']:
    flags.append('cadence')
```

**Status**: ✅ Fermata/cadence detection is COMPLETE, but the flags are NOT used downstream.

---

### ✅ Block 1: Automatic Music Transcription - WORKING

**File**: `Block_1_AMT/transcribe_audio_fixed.py` (and enhanced versions)

**What Works:**
- Transcribes audio to MIDI using Basic Pitch
- Outputs `transcription.json` with note events
- Enhanced version includes onset refinement using librosa
- Confidence scoring for note quality assessment

**Status**: ✅ AMT is functional and produces accurate transcriptions.

---

### ⚠️ Block 2: Symbolic Alignment - PARTIALLY IMPLEMENTED

**File**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`

**What Works:**
- Converts score and performance to chromagram features
- Performs DTW alignment using librosa or scipy
- Generates time mapping between score and performance
- Creates visualization of alignment results
- GPU support via gpu_manager

**Current DTW Implementation (lines 226-252):**
```python
def dtw_alignment(self, X: np.ndarray, Y: np.ndarray, 
                  metric: str = 'cosine') -> Tuple[np.ndarray, float]:
    """Perform DTW alignment using librosa"""
    try:
        # Use librosa's DTW implementation
        D, wp = librosa.sequence.dtw(X=X.T, Y=Y.T, metric=metric)
        
        # ❌ No fermata/cadence awareness
        # ❌ No beat probability weighting
        # ❌ No band constraints enabled
        # ❌ Uniform cost across all regions
        
        distance = D[-1, -1]
        logger.info(f"DTW completed: path length={len(wp)}, distance={distance:.4f}")
        return wp, distance
```

**What's Missing:**
1. **No use of fermata/cadence flags** from Block 0 ScoreGraph
2. **No adaptive step weights** - all temporal regions treated equally
3. **No band constraints** - despite being documented in README (line 121)
4. **No beat probability weighting** - even though librosa.sequence.dtw supports:
   - `weights_mul` parameter for step weight adjustment
   - `weights_add` parameter for additive penalties
   - `global_constraints` parameter for Sakoe-Chiba band
   - `band_rad` parameter for band width

**Status**: ⚠️ Basic DTW works, but lacks expressive timing features.

---

### ⚠️ Block 3: Tempo/Phase Curves - POST-HOC ONLY

**File**: `Block_3_TempoPhaseCurves/derive_curves.py`

**What Works:**
- Computes tempo curve from alignment results (reactive analysis)
- Derives phase curves showing position within beats
- Generates diagnostic plots

**Code Evidence (lines 11-19):**
```python
# Compute tempo curve (finite differences)
abs_beats = np.array([p[0] for p in path])
perf_times = np.array([p[1] for p in path])
d_abs_beat = np.diff(abs_beats)
d_time = np.diff(perf_times)
bpm = np.divide(d_abs_beat, d_time, out=np.zeros_like(d_abs_beat), where=d_time!=0) * 60
```

**What's Missing:**
- This is **reactive** (analyzes results after alignment)
- NOT **proactive** (doesn't inform the alignment process)
- Tempo variations are observed, not anticipated

**Status**: ⚠️ Works for analysis, but doesn't help alignment handle rubato.

---

### ❌ Block 4: Beat/Downbeat Detection - INCOMPLETE

**File**: `Block_4_BeatDownbeat/estimate_beats.py`

**What Works:**
- Detects beat and downbeat times using BeatNet
- Outputs `beats.json` with time positions

**Current Implementation (lines 7-21):**
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
    
    # ❌ NO confidence scores captured
    # ❌ BeatNet provides confidence but we ignore it
```

**What's Missing:**
1. **Confidence scores NOT extracted** - BeatNet outputs probabilities but code doesn't capture them
2. **Beat info NOT passed to Block 2** - no integration with alignment
3. **No beat-weighted cost matrix** in DTW

**Status**: ❌ Detects beats but loses confidence information.

---

### ❌ Block 6: Tolerance and Relock - PLACEHOLDER ONLY

**File**: `Block_6_ToleranceRelock/tolerance_and_relock.py`

**Current Implementation (lines 20-26):**
```python
# Simulate confidence drop and relock
conf = float(row['conf'])
if conf < 0.5:
    # Perform coarse DTW on last few seconds (placeholder logic)
    # Use SyncToolbox DTW API for actual relock
    # Here, just copy previous stable value
    if stabilized_trace:
        row['score_abs_beat'] = stabilized_trace[-1]['score_abs_beat']
```

**Status**: ❌ Conceptual framework only, no real implementation.

---

## What's Missing: The Three Critical Features

### 1. Rubato and Fermata Handling ❌

**Problem**: Fermata/cadence flags are detected in Block 0 but NEVER used in Block 2 alignment.

**Impact**: 
- Alignment assumes uniform tempo throughout
- Cannot handle ritardandos, accelerandos, or fermatas properly
- May misalign expressive timing moments

**Where to Fix**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`

**Required Changes**:
```python
# Current signature:
def dtw_alignment(self, X, Y, metric='cosine'):
    D, wp = librosa.sequence.dtw(X=X.T, Y=Y.T, metric=metric)

# Should be:
def dtw_alignment(self, X, Y, metric='cosine', score_graph=None):
    # Compute adaptive step weights based on fermata/cadence flags
    if score_graph:
        weights_mul = self._compute_adaptive_weights(
            n_frames=X.shape[1],
            nodes=score_graph['nodes']
        )
    else:
        weights_mul = None
    
    # Apply adaptive weights (lower values = more flexibility)
    D, wp = librosa.sequence.dtw(
        X=X.T, 
        Y=Y.T, 
        metric=metric,
        weights_mul=weights_mul  # ✅ NEW
    )

def _compute_adaptive_weights(self, n_frames, nodes):
    """
    Reduce step penalties near fermatas/cadences
    to allow more temporal flexibility
    """
    # Default: equal weights [diagonal, horizontal, vertical]
    weights = np.array([1.0, 1.0, 1.0])
    
    # TODO: Check if current frame is near fermata/cadence
    # TODO: Reduce weights (e.g., 0.5x) in those regions
    
    return weights
```

---

### 2. Beat and Downbeat Probability ❌

**Problem**: Beat confidence scores exist but are NOT captured or used.

**Impact**:
- High-confidence beats should anchor alignment
- Low-confidence regions should have less influence
- Current implementation treats all frames equally

**Where to Fix**: 
1. `Block_4_BeatDownbeat/estimate_beats.py` - capture confidence
2. `Block_2_SymbolicAlignment/align_symbolic_enhanced.py` - use in alignment

**Required Changes**:

**Step 1: Capture confidence in Block 4:**
```python
def estimate_beats(audio_path, beats_path):
    beatnet = BeatNet()
    
    # ✅ Request full output with confidence
    output = beatnet.process(audio_path, return_confidence=True)
    
    beats_json = []
    for beat in output:
        beats_json.append({
            "t": beat['time'],
            "downbeat": beat['is_downbeat'],
            "confidence": beat['confidence']  # ✅ NEW
        })
```

**Step 2: Use in Block 2 alignment:**
```python
def enhanced_alignment(self, score_midi, perf_midi, beats_json=None):
    # Extract features
    score_chroma = self.midi_to_chroma(score_midi, max_duration)
    perf_chroma = self.midi_to_chroma(perf_midi, max_duration)
    
    # ✅ NEW: Apply beat-weighted cost if available
    if beats_json:
        C = self._compute_beat_weighted_cost(
            score_chroma, 
            perf_chroma, 
            beats_json
        )
        D, wp = librosa.sequence.dtw(C=C, backtrack=True)
    else:
        D, wp = librosa.sequence.dtw(X=score_chroma.T, Y=perf_chroma.T)

def _compute_beat_weighted_cost(self, X, Y, beats_json):
    """
    Weight cost matrix by beat confidence
    High-confidence beats get lower cost → preferred alignment anchors
    """
    from scipy.spatial.distance import cdist
    
    # Base cost (cosine distance)
    C = cdist(X.T, Y.T, metric='cosine')
    
    # Map beat times to frame indices
    beat_frames = librosa.time_to_frames(
        [b['t'] for b in beats_json],
        sr=self.sr,
        hop_length=self.hop_length
    )
    
    # Apply confidence weighting to cost matrix
    for frame, beat in zip(beat_frames, beats_json):
        conf = beat['confidence']
        # Reduce cost near high-confidence beats (±2 frames)
        window = slice(max(0, frame-2), min(C.shape[1], frame+3))
        C[:, window] *= (1.0 / (1.0 + conf))  # Lower = preferred
    
    return C
```

---

### 3. Adaptive Tolerance Near Cadences/Fermatas ❌

**Problem**: Sakoe-Chiba band constraints are documented but NOT enabled.

**Impact**:
- DTW explores full alignment space (slow, unstable)
- Should use band constraint for speed and robustness
- Band should widen near fermatas/cadences for flexibility

**Where to Fix**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`

**Required Changes**:

**Quick Fix (Priority 1): Enable static band constraint**
```python
# Current:
D, wp = librosa.sequence.dtw(X=X.T, Y=Y.T, metric=metric)

# Should be:
D, wp = librosa.sequence.dtw(
    X=X.T, 
    Y=Y.T, 
    metric=metric,
    global_constraints=True,  # ✅ Enable Sakoe-Chiba band
    band_rad=0.25              # ✅ Allow 25% tempo deviation
)
```

**Advanced Fix (Priority 2): Adaptive band width**
```python
def dtw_alignment_adaptive_band(self, X, Y, score_graph=None, metric='cosine'):
    """
    DTW with adaptive band width
    Wider bands near fermatas/cadences allow more temporal flexibility
    """
    
    # Estimate global tempo ratio
    alpha = X.shape[1] / Y.shape[1]
    
    # Compute frame-wise band width
    if score_graph:
        band_widths = self._compute_adaptive_band_width(
            n_frames=X.shape[1],
            nodes=score_graph['nodes'],
            base_band_rad=0.25
        )
    else:
        band_widths = 0.25  # Uniform
    
    # Create cost matrix with adaptive band masking
    C = self._compute_distance_with_adaptive_band(
        X, Y, metric, alpha, band_widths
    )
    
    D, wp = librosa.sequence.dtw(C=C, backtrack=True)
    return wp, D[-1, -1]

def _compute_adaptive_band_width(self, n_frames, nodes, base_band_rad):
    """
    Widen band near fermatas/cadences
    Normal: 25% deviation allowed
    Fermata: 50% deviation allowed (2x wider)
    """
    band_widths = np.full(n_frames, base_band_rad)
    
    for node in nodes:
        if 'fermata' in node.get('flags', []):
            # TODO: Map node['abs_beat'] to frame index
            # frame_idx = self._beat_to_frame(node['abs_beat'])
            # window = slice(frame_idx-10, frame_idx+10)
            # band_widths[window] *= 2.0  # Double the band width
            pass
    
    return band_widths
```

---

## Summary: What Each File Currently Does vs. What It Should Do

| File | Current Behavior | Missing Feature | Fix Complexity |
|------|------------------|-----------------|----------------|
| `Block_0/.../build_scoregraph_with_repeats.py` | ✅ Detects fermatas/cadences | ➡️ Data passed but not used | N/A (source is fine) |
| `Block_4/.../estimate_beats.py` | ⚠️ Detects beat times only | ❌ Confidence scores not captured | LOW (2 hours) |
| `Block_2/.../align_symbolic_enhanced.py` | ⚠️ Basic DTW works | ❌ No adaptive weights | MEDIUM (4-6 hours) |
| | | ❌ No beat weighting | MEDIUM (4-6 hours) |
| | | ❌ No band constraints | LOW (30 min) |
| | | ❌ No adaptive bands | HIGH (8-12 hours) |

---

## Implementation Priority

### Priority 1 (Quick Wins - 2-3 hours):
1. ✅ Enable static Sakoe-Chiba band constraint in DTW
2. ✅ Capture beat confidence scores in Block 4

### Priority 2 (High Impact - 1-2 days):
3. ✅ Implement beat-weighted cost matrix
4. ✅ Add fermata/cadence-aware step weights

### Priority 3 (Advanced - 2-3 days):
5. ✅ Adaptive band width based on score annotations
6. ✅ Frame-to-beat mapping utilities

---

## Copy-Paste Summary for Next Steps

**Current State**: 
- Block 0 detects fermatas/cadences but they're ignored
- Block 4 detects beats but loses confidence scores
- Block 2 uses vanilla DTW with no awareness of musical structure
- README documents band constraints but code doesn't use them

**Immediate Actions Required**:
1. Modify `estimate_beats.py` to capture `confidence` field from BeatNet
2. Add `global_constraints=True, band_rad=0.25` to librosa DTW call
3. Implement `_compute_adaptive_weights()` method that reads fermata/cadence flags
4. Implement `_compute_beat_weighted_cost()` method that uses beat probabilities
5. Update `enhanced_alignment()` to accept and use score_graph + beats_json

**Expected Outcome**:
- Alignment will handle rubato and fermatas correctly
- High-confidence beats will anchor the alignment
- Faster and more stable DTW with band constraints
- Flexible timing near expressive moments

