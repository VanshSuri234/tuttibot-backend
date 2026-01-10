# 📋 Quick Reference: Pipeline Execution Logging

## What You Get Now

**Before**: Pipeline works locally but hangs on Render → no visibility into why  
**After**: Complete execution flow tracking with timing and memory monitoring at each stage

## Deploy & Monitor

```bash
# 1. Deploy to Render (auto-deploys from deployment-ready branch)
git push origin deployment-ready

# 2. Go to Render Dashboard → tuttibot-backend → Logs tab
# (Keep this open to watch real-time execution)

# 3. Submit audio + score file to API
curl -X POST https://your-api.onrender.com/upload \
  -F "audio=@performance.wav" \
  -F "score=@score.xml"

# 4. Watch logs stream in real-time
```

## Understanding the Logs

### Success Output (All Green ✅)
```
[LAYER 1️⃣  INPUT STANDARDIZATION] Starting...
[INPUT LAYER] ✅ COMPLETE in 2.34s
✅ Layer 1 Complete: 2.34s

[LAYER 2️⃣  AUDIO PROCESSING] Starting...
[PROCESSING LAYER] ✅ COMPLETE in 45.67s
✅ Layer 2 Complete: 45.67s

... (continues through Layer 7)

[LAYER 7️⃣  FINAL GRADING] Starting...
[GRADING LAYER] ✅ Final grade: 87.5/100
✅ Layer 7 Complete: 0.87s

⏱️  TOTAL TIME: 115.93s
```

### Stuck Detection (Red ❌)
```
✅ Layer 2 Complete: 45.67s
✅ Layer 3 Complete: 52.45s
[LAYER 4️⃣  FEATURE EXTRACTION] Starting...
[EXTRACTION LAYER] Starting feature extraction...

(NO MORE LOGS = STUCK in Layer 4)
```

## Quick Diagnostics

| What Happened | Check These Logs |
|---|---|
| Entire pipeline stuck | Last `[LAYER X]` line |
| One layer very slow (>60s) | `✅ Layer X Complete: Y.ZZs` |
| Memory keeps growing | `[MEM LAYER_X_START]` and `[MEM LAYER_X_END]` |
| Specific block stuck (L3) | `[TEMPORAL ALIGNMENT] Block X` logs |
| Error occurred | Search for `❌` or `Error:` |

## Expected Timings (Baseline)

```
Layer 1 (Input):       2-5s     ✅ Quick
Layer 2 (Processing):  40-60s   🔴 Slowest (audio)
Layer 3 (Alignment):   30-80s   🔴 Slow (DTW)
Layer 4 (Extraction):  5-15s    ✅ Normal
Layer 5 (PQG):        2-5s     ✅ Normal
Layer 6 (Inference):  1-2s     ✅ Quick
Layer 7 (Grading):    0.5-1s   ✅ Quick
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:                80-170s   ⏱️  Varies by audio
```

If your times are **2-3x longer**, check:
- Audio file size (should be <10MB)
- Render memory limit (may need upgrade)
- Score complexity (many instruments?)

## Memory Should Look Like This

```
[MEM LAYER_1_START] RSS: 256MB
[MEM LAYER_1_END]   RSS: 258MB    (+2MB, normal)

[MEM LAYER_2_START] RSS: 258MB
[MEM LAYER_2_END]   RSS: 384MB    (+126MB, expected - audio processing)

[MEM LAYER_3_START] RSS: 384MB
[MEM LAYER_3_END]   RSS: 456MB    (+72MB, normal - DTW)

[MEM LAYER_4_START] RSS: 456MB
[MEM LAYER_4_END]   RSS: 512MB    (+56MB, normal)
```

**Red flags**:
- Any layer using >600MB (memory leak)
- Memory not released between layers
- Progressive growth: 256 → 384 → 512 → 640 → 780 (leak!)

## Top Troubleshooting Scenarios

### Scenario 1: Stuck in Layer 2 (Audio Processing)
**Likely cause**: Librosa processing or ffmpeg-normalize hanging  
**Fix**:
1. Reduce audio file size (<5MB)
2. Check audio format (must be WAV/MP3)
3. Check audio duration (<10 minutes)

### Scenario 2: Stuck in Layer 3, Block 1 (Transcription)
**Likely cause**: basic-pitch GPU timeout or slow CPU  
**Fix**:
1. Upgrade Render plan to include GPU
2. OR reduce audio quality/length
3. OR add timeout handling in code

### Scenario 3: Stuck in Layer 5 (PQG-A2SA)
**Likely cause**: MIDI alignment too complex  
**Fix**:
1. Simplify score (fewer instruments)
2. Reduce audio resolution
3. May need timeout increase

### Scenario 4: All Layers Complete but API Hangs
**Likely cause**: Chatbot context generation or JSON serialization  
**Check logs** for:
- `[FINAL STEP] Generating Chatbot Context...`
- If this doesn't show "Complete", that's the issue

## Log Search Patterns

### Find Timing Summary
```
Search logs for: "Layer Execution Times"
or: "Layer X Complete:"
```

### Find Errors
```
Search for: ❌
or: Error
```

### Find Memory Issues
```
Search for: [MEM
Look for continuous growth across layers
```

### Find Block Progress (Layer 3)
```
Search for: Block 0
then: Block 1
then: Block 2
If one doesn't appear, that block is stuck
```

## Files to Check After Pipeline Completes

In `/results/{job_id}/`:
```
pipeline_summary.json          ← Layer times and overall stats
07_grading/
  ├── final_grade.json         ← Numerical score (0-100)
  └── performance_report.txt   ← Human-readable report
chatbot_context.json           ← All data for LLM response
```

## Report Template if Pipeline Fails

```
PIPELINE EXECUTION FAILURE REPORT

Stuck Location: [e.g., Layer 3, Block 1 (Transcription)]
Last Log: [copy exact log line]

Audio: [size, duration, format]
Score: [format, instruments]

Layer Timings:
- Layer 1: Xs
- Layer 2: Xs
- Layer 3: Xs (STUCK)

Memory Progression:
- Start: XXXmb
- After L2: XXXmb
- After L3: [didn't reach]

Expected vs Actual:
- Expected: ~120s
- Actual: ~90s (hung at 90s)

Log Excerpt:
[paste last 5 log lines]
```

## Render Dashboard Navigation

1. **Dashboard** → Select "tuttibot-backend"
2. **Logs** tab (rightmost)
3. **See full logs** link (bottom right)
4. Use browser find (Ctrl+F) to search logs
5. Scroll down to see latest logs

## Environment Variables (if needed)

Add to Render dashboard "Environment" settings:
```
PYTHONUNBUFFERED=1    (flush logs immediately)
LOGLEVEL=DEBUG        (optional, more verbose)
```

## Next Steps if Pipeline Gets Stuck

1. ✅ Deploy code with logging
2. ✅ Submit audio file
3. ✅ Watch Render logs in real-time
4. ✅ Identify which layer is stuck
5. ✅ Note exact timing and memory
6. ✅ Create issue report with findings
7. ✅ Adjust code or infrastructure accordingly

---

**Ready to deploy?**

```bash
git push origin deployment-ready
# Then open Render Dashboard and monitor logs
```

**Key Point**: The logging system will show you **exactly** where the pipeline gets stuck and **why**, so you can fix it with confidence.
