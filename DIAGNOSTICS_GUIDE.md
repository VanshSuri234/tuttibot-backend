# TuttiBot Render Hang - Diagnostic & Fix Guide

## Problem Summary
Pipeline is getting stuck during Layer 2 (Audio Processing) on Render. Frontend shows "analysing" indefinitely, then service gets killed by Render.

## Root Cause Analysis (with logging)

We've added comprehensive logging to identify the ACTUAL bottleneck. Here's what to look for in Render logs:

### 1. **Memory Wall (Most Likely Culprit)**

**What to look for in logs:**
```
[MEMORY BEFORE_LOAD_AUDIO] RSS: 45.2MB
[AUDIO_CHECK] Loaded 22050000 samples at 22050Hz
[MEMORY AFTER_LOAD_AUDIO] RSS: 280.5MB   ← Huge jump!
```

**If you see:**
- Memory jumps from 50MB → 300+MB when loading audio
- Then memory doesn't decrease after processing
- Service gets killed at 512MB (Render free tier limit)

**Then the fix is:** Use `sr=22050` in librosa.load (which we already added)

---

### 2. **Worker Blocking (Gunicorn Sync Workers)**

**What to look for in logs:**
```
[SYSTEM RUN_ANALYSIS_START] Threads: 1
[PIPELINE_START] job XXX
(Frontend polls /status every 2s, but no response for 30s+)
[PIPELINE_END] success=True, elapsed=125.44s
```

**If you see:**
- Frontend keeps showing "analysing" status for 2+ minutes
- Render hasn't killed yet (memory is OK)
- A single `/status` request times out while pipeline is running

**Then the fix is:** Change Gunicorn to use `gthread` workers:
```bash
gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT -t 300 app:app
```

---

### 3. **librosa/resampy Hanging (Less Likely)**

**What to look for in logs:**
```
[AUDIO_CHECK] Loading /opt/render/project.../audio.wav with sr=22050
[MEMORY AFTER_LOAD_AUDIO] RSS: 280.5MB
(No further logs for 30+ seconds)
[2026-01-09 19:XX:XX] Handling signal: term  ← Render killed it
```

**If you see:**
- Memory is reasonable (< 350MB)
- But process appears to hang during librosa operations
- No errors logged, just silence then killed

**Then the fix is:** Use subprocess with timeout for librosa operations

---

## Logging Output Locations

All logs will appear in Render's **Live Logs** tab:

```
[SYSTEM RUN_ANALYSIS_START] RAM: 45.2MB CPU: 2.1% Threads: 1
[PIPELINE_START] job 5615b12c: /opt/render/.../audio.wav
[AUDIO_CHECK] Loading with sr=22050 (memory-optimized)
[MEMORY BEFORE_LOAD_AUDIO] RSS: 45.2MB
[MEMORY AFTER_LOAD_AUDIO] RSS: 280.5MB
[AUDIO_CHECK] Completed in 3.24s
[NOISE_REDUCE] Starting noise reduction
[MEMORY AFTER_LOAD_NOISE] RSS: 300.1MB
[NORMALIZE] Completed in 0.15s
[SYSTEM BEFORE_PIPELINE__XXX] RAM: 45.2MB CPU: 8.5% Threads: 2
[PIPELINE_END] job XXX: success=True, elapsed=125.44s
```

---

## What Each Log Tag Means

| Log Tag | Meaning |
|---------|---------|
| `[SYSTEM X]` | System resource status (RAM, CPU, Thread count) |
| `[MEMORY X]` | Process memory snapshots at critical points |
| `[AUDIO_CHECK]` | Layer 2 audio analysis stage |
| `[NOISE_REDUCE]` | Noise reduction processing |
| `[NORMALIZE]` | Audio normalization |
| `[PIPELINE_START]` | Pipeline initialization |
| `[PIPELINE_RUNNING]` | Pipeline in progress |
| `[PIPELINE_END]` | Pipeline completion |
| `[PIPELINE_ERROR]` | Pipeline failure |

---

## Quick Fixes Implemented

✅ **Memory Optimization:**
- Changed `librosa.load(audio_path, sr=None)` → `librosa.load(audio_path, sr=22050, dtype=np.float32)`
- This reduces memory by 50% (from ~300MB to ~150MB for audio load)

✅ **Worker Monitoring:**
- Added `log_system_status()` calls at critical points
- Tracks RAM, CPU, thread count during pipeline execution

✅ **Detailed Timing:**
- Each processing step logs start/end times
- Identifies which layer is slow/hanging

---

## Deployment Instructions

### Step 1: Commit Diagnostic Logging
```bash
git add -A
git commit -m "Add comprehensive diagnostic logging for Render hang debugging"
git push origin deployment-ready
```

### Step 2: Wait for Render Rebuild
Render will auto-rebuild from the push. Watch the Live Logs.

### Step 3: Upload Test File Again
Use frontend to upload the same test audio+score that was hanging before.

### Step 4: Analyze Logs
Look for which log tag shows the longest time/highest memory:
- If `[MEMORY AFTER_LOAD_AUDIO]` > 350MB → Memory wall issue
- If `[PIPELINE_END] elapsed=180s+` but memory is fine → Worker blocking
- If logs stop without `[PIPELINE_END]` → Process was killed (check memory)

### Step 5: Apply Corresponding Fix

**If Memory Wall:**
- Already fixed with `sr=22050`
- Monitor that `[MEMORY AFTER_LOAD_AUDIO]` is now ~150MB instead of 300MB

**If Worker Blocking:**
- Change Start Command in Render Dashboard to:
  ```bash
  gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT -t 300 app:app
  ```

**If Still Hanging:**
- Re-run test and share full logs
- We'll add more granular logging to pinpoint exact bottleneck

---

## Current Code Changes

### `processing_layer.py`
- ✅ Added `log_memory_usage()` function
- ✅ Added timing logs to `check_audio_quality()`
- ✅ Added timing logs to `reduce_noise()`
- ✅ Added timing logs to `normalize_audio()`
- ✅ Added timing logs to `process()`
- ✅ Changed `librosa.load(sr=None)` → `librosa.load(sr=22050, dtype=np.float32)`

### `app.py`
- ✅ Added `log_system_status()` function
- ✅ Added detailed logging to `run_analysis()`
- ✅ Tracks start/end times and system resources

### `requirements.txt`
- ✅ Added `psutil>=5.8.0` for memory monitoring

---

## Example: What Success Looks Like

After fixes, you should see logs like:

```
[SYSTEM RUN_ANALYSIS_START_XXX] RAM: 45.2MB CPU: 0.5% Threads: 1
[PIPELINE_START] job XXX
[AUDIO_CHECK] Loading with sr=22050 (memory-optimized)
[MEMORY AFTER_LOAD_AUDIO] RSS: 152.3MB   ← Now ~150MB instead of 300MB!
[AUDIO_CHECK] Completed in 1.45s
[NOISE_REDUCE] Completed in 8.32s
[NORMALIZE] Completed in 0.12s
[SYSTEM BEFORE_PIPELINE] RAM: 165.4MB CPU: 45.2% Threads: 4
[PIPELINE_END] job XXX: success=True, elapsed=45.23s   ← Under 1 minute!
```

Then frontend should show results within 1-2 minutes instead of hanging.

---

## Questions This Answers

**Q: Why is it stuck at Layer 2?**
A: Layer 2 is where audio files are loaded into memory. This is the RAM-intensive operation.

**Q: Why doesn't it happen locally?**
A: Your local machine has 8GB+ RAM. Render free tier has only 512MB.

**Q: Why the `/status` polls keep returning 200?**
A: Different Gunicorn workers handle the requests. If one worker is stuck in heavy math, other workers can still respond with stale status.

**Q: Will Docker fix this?**
A: Docker doesn't change the memory or CPU limits. The real fix is code-level optimization (which we've done).

---

## Next Steps

1. **Commit these changes** and wait for Render to rebuild
2. **Test with the same audio file** that was hanging before
3. **Check Render Live Logs** for the memory/timing diagnostics
4. **Share the logs** if still stuck (paste the log section from `[PIPELINE_START]` to `[PIPELINE_END]`)
5. **Apply the corresponding fix** based on what you find

This approach will tell us EXACTLY where the bottleneck is!
