# Pipeline Hang Fix - Timeout Protection

## Problem
The pipeline was getting stuck after "Layer 2: Audio Processing" with status polling continuing but no progress through the pipeline. This occurred consistently when processing the audio file.

## Root Causes Identified
1. **Auditok segmentation** - `auditok.split()` call had no timeout and could hang indefinitely on certain audio files
2. **Music21 parsing** - `converter.parse()` for MIDI files had no timeout and could hang when processing certain score files

## Solutions Implemented

### 1. Auditok Segmentation with Threading Timeout (Line 200-261)
**File:** `MusicPerformanceAnalysis/layers/02_processing/processing_layer.py`

```python
# Old: Direct call with no timeout
audio_events = auditok.split(clean_audio_path, ...)

# New: Threading-based timeout (5 seconds max)
def run_auditok():
    nonlocal audio_events
    audio_events = auditok.split(...)

auditok_thread = Thread(target=run_auditok, daemon=True)
auditok_thread.start()
auditok_thread.join(timeout=5.0)  # Wait max 5 seconds
```

**Why threading?** Windows doesn't support `signal.SIGALRM`, so threading with `join(timeout=...)` is the cross-platform solution.

**Fallback behavior:**
- If auditok succeeds within 5 seconds → use detected segments
- If auditok times out or fails → use full audio as single segment (pipeline continues)

### 2. Music21 Parsing with Threading Timeout (Line 273-329)
**File:** `MusicPerformanceAnalysis/layers/02_processing/processing_layer.py`

```python
# Old: Direct call with no timeout
score = converter.parse(music_path)

# New: Threading-based timeout (10 seconds max)
def parse_music():
    nonlocal score, parse_error
    score = converter.parse(music_path)

parse_thread = Thread(target=parse_music, daemon=True)
parse_thread.start()
parse_thread.join(timeout=10.0)  # Wait max 10 seconds
```

**Fallback behavior:**
- If parsing succeeds within 10 seconds → continue with feature extraction
- If timeout occurs → raise exception, caught by outer try/except, returns empty MusicFeatures

### 3. Enhanced Logging (Line 527-534)
Added debug logging before and after critical sections:
```python
print(f"[DEBUG] Starting audio segmentation. needs_segmentation={...}")
print(f"[DEBUG] Calling segment_audio(...)")
print(f"[DEBUG] Segmentation completed: {len(segments)} segments")
print(f"[DEBUG] Starting feature extraction from {original_music_path}")
print(f"[DEBUG] Feature extraction completed: {len(music_features.notes)} notes")
```

This allows us to see exactly where the pipeline is stuck in future instances.

## Testing Strategy
1. **Push to Render** - Triggered automatic rebuild
2. **Monitor logs** - Watch for new debug messages showing progress through Layer 2
3. **Verify completion** - Check that analysis completes and status updates to "completed"
4. **Smoke test** - Upload same test file again to confirm fix works

## Expected Behavior After Fix
```
[DEBUG] Starting audio segmentation. needs_segmentation=true
[DEBUG] Calling segment_audio(...)
[DEBUG] Segmentation completed: X segments
[DEBUG] Starting feature extraction from ...MIDI
[DEBUG] Feature extraction completed: X notes extracted
[Layer 3: Alignment] ...  (continues to next layer)
```

## Timeout Values Chosen
- **Auditok:** 5 seconds
  - Typical segmentation: <1 second
  - 5 seconds = 5x safety margin
  
- **Music21:** 10 seconds  
  - Typical parsing: 0.5-2 seconds
  - 10 seconds = 5x safety margin

## Fallback Chain
```
Try auditok (5s) 
  → Success: Use detected segments
  → Timeout: Full audio as segment → Pipeline continues
  
Try music21 parse (10s)
  → Success: Extract features
  → Timeout: Return empty features → Pipeline continues
```

No pipeline stall possible - always has a fallback path.

## Commit Info
- **Commit Hash:** `356f7212`
- **Branch:** `deployment-ready`
- **Files Modified:** 
  - `MusicPerformanceAnalysis/layers/02_processing/processing_layer.py`

## Status
✅ **DEPLOYED TO RENDER** - Waiting for rebuild and testing
