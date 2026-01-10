# TuttiBot Pipeline - Quick Reference & File Locations

## CRITICAL FILES FOR DEBUGGING

### REST API Entry Point
- **File:** `app.py` (608 lines)
- **Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\app.py`
- **Key Function:** `run_analysis(job_id, audio_path, score_path)` (Lines 318-450)
- **Purpose:** Background worker that calls MusicPerformancePipeline

### Pipeline Orchestrator
- **File:** `pipeline.py` (1290 lines)
- **Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\MusicPerformanceAnalysis\pipeline.py`
- **Key Class:** `MusicPerformancePipeline`
- **Key Method:** `run_pipeline()` (Lines 860-980)
- **Purpose:** Coordinates execution of all 7 layers

---

## LAYER FILES

### LAYER 1: INPUT STANDARDIZATION
- **File:** `input_layer.py` (548 lines)
- **Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\MusicPerformanceAnalysis\layers\01_input\`
- **Key Classes:** `AudioInputProcessor`, `ScoreInputProcessor`
- **Duration:** 2-5 seconds

### LAYER 2: PROCESSING ⚠️ BOTTLENECK
- **File:** `processing_layer.py` (764 lines)
- **Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\MusicPerformanceAnalysis\layers\02_processing\`
- **Key Class:** `ProcessingLayer`
- **Duration:** 30-60 seconds (HANGS on Render)
- **Diagnostic Logs:** `[MEMORY ...]`, `[AUDIO_CHECK]`, `[NOISE_REDUCE]`, `[NORMALIZE]`

### LAYER 3: TEMPORAL ALIGNMENT
**Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\MusicPerformanceAnalysis\layers\03_temporal_alignment\`

#### Block 0: ScoreGraph
- **File:** `build_scoregraph_with_notes.py` (285 lines)
- **Location:** `...layers\03_temporal_alignment\block_0_scoregraph\`
- **Duration:** 5-10 seconds

#### Block 1: Transcription
- **File:** `transcribe_enhanced.py` (245 lines)
- **Location:** `...layers\03_temporal_alignment\block_1_transcription\`
- **Duration:** 20-40 seconds

#### Block 4: Beat Detection (Optional)
- **File:** `estimate_beats_beatnet.py`
- **Location:** `...layers\03_temporal_alignment\block_4_beats\`
- **Duration:** 10-20 seconds

#### Block 2: DTW Alignment (MAIN COMPUTATION)
- **File:** `align_symbolic_enhanced_with_metrics.py` (1411 lines)
- **Location:** `...layers\03_temporal_alignment\block_2_dtw\`
- **Duration:** 30-60 seconds
- **Output:** `alignment_results.json` with grading metrics

### LAYER 4: FEATURE EXTRACTION
- **File:** `extraction_layer.py` (920 lines)
- **Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\MusicPerformanceAnalysis\layers\04_extraction\`
- **Key Classes:** `AudioFeatureExtractor`, `ScoreFeatureExtractor`
- **Duration:** 10-30 seconds

### LAYER 5: PQG-A2SA (OPTIONAL)
- **Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\MusicPerformanceAnalysis\layers\05_pqg_a2sa\`
- **Key Class:** `PQGAligner`
- **Duration:** 5-15 seconds

### LAYER 6: INFERENCE CORE
- **File:** `inference_core.py` (323 lines)
- **Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\MusicPerformanceAnalysis\layers\06_inference\`
- **Key Class:** `InferenceCore`
- **Duration:** 2-5 seconds
- **Output:** `grading_package_master.json`

### LAYER 7: GRADING
- **File:** `grading_layer.py` (548 lines)
- **Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\MusicPerformanceAnalysis\layers\07_grading\`
- **Key Class:** `GradingLayer`
- **Duration:** 1-2 seconds
- **Outputs:** 
  - `final_grade.json` (structured)
  - `performance_report.txt` (human readable)

---

## OUTPUT DIRECTORY STRUCTURE

After a successful run, results appear in:
```
results/{job_id}/
│
├── 01_input/
│   ├── audio_standardized.wav
│   ├── score_standardized.musicxml
│   └── input_metadata.json
│
├── 02_processing/
│   ├── data/
│   │   └── audio_processed.wav
│   ├── shared/
│   │   └── processed/
│   │       ├── audio_segments.json
│   │       └── music_features.json
│   └── processing_metadata.json
│
├── 03_temporal_alignment/
│   ├── scoregraph.json
│   ├── performance.mid
│   ├── beats.json [optional]
│   ├── context_alignment.json [optional]
│   └── alignment_output/
│       └── alignment_results.json ← GRADING METRICS
│
├── 04_extraction/
│   ├── performance_features.json
│   └── score_features.json
│
├── 05_pqg_a2sa/
│   └── pqg_a2sa_results.json [optional]
│
├── 06_inference/
│   └── grading_package_master.json
│
├── 07_grading/
│   ├── final_grade.json
│   └── performance_report.txt
│
├── pipeline_summary.json
└── chatbot_context.json
```

---

## KEY FILES WITH RECENT OPTIMIZATIONS

### ✅ MODIFIED WITH MEMORY OPTIMIZATIONS:
1. **processing_layer.py** (Line 145)
   ```python
   # BEFORE: data, sr = librosa.load(audio_path, sr=None)
   # AFTER:  data, sr = librosa.load(audio_path, sr=22050, dtype=np.float32)
   # Impact: 300 MB → 75 MB (75% reduction)
   ```

### ✅ MODIFIED WITH DIAGNOSTIC LOGGING:
1. **processing_layer.py** (Lines 20-35)
   - Added `log_memory_usage()` function
   - Added `[MEMORY ...]` tags at critical points
   - Added timing with `start_time` tracking

2. **processing_layer.py** (All major functions)
   - Added `log_memory_usage()` calls
   - Added `[AUDIO_CHECK]`, `[NOISE_REDUCE]`, `[NORMALIZE]` tags
   - Added elapsed time logging

3. **app.py** (Lines 22-42)
   - Added `log_system_status()` function
   - Logs RAM, CPU%, thread count

4. **app.py** (run_analysis function, Lines 318-450)
   - Added `[PIPELINE_START]`, `[PIPELINE_RUNNING]`, `[PIPELINE_END]` tags
   - Added elapsed time tracking
   - System status logging at 4 points

### ✅ MODIFIED DEPENDENCIES:
1. **requirements.txt**
   - Added `psutil>=5.8.0` for system monitoring

---

## EXECUTION FLOW SUMMARY

```
User uploads audio + score
        ↓
Flask /upload endpoint (app.py)
        ↓
Spawn background thread
        ↓
run_analysis(job_id, audio_path, score_path)
        ↓
Instantiate MusicPerformancePipeline(audio, score, output_dir)
        ↓
pipeline_obj.run_pipeline()  ← ENTRY TO pipeline.py
        ↓
┌─────────────────────────────┐
│ Layer 1: Input Validation   │ 2-5s    ✓ Works
├─────────────────────────────┤
│ Layer 2: Audio Processing   │ 30-60s  ⚠️ HANGS on Render
├─────────────────────────────┤
│ Layer 3: Temporal Alignment │ 90-140s ✗ Unreachable
│ (Block 0, 1, 4, 2)          │
├─────────────────────────────┤
│ Layer 4: Extraction         │ 10-30s  ✗ Unreachable
│ (parallel with 5)           │
├─────────────────────────────┤
│ Layer 5: PQG-A2SA [opt]     │ 5-15s   ✗ Unreachable
├─────────────────────────────┤
│ Layer 6: Inference Core     │ 2-5s    ✗ Unreachable
├─────────────────────────────┤
│ Layer 7: Grading            │ 1-2s    ✗ Unreachable
├─────────────────────────────┤
│ Chatbot Context Aggregation │ 1-2s    ✗ Unreachable
└─────────────────────────────┘
        ↓
Parse final_grade.json + performance_report.txt (app.py)
        ↓
Extract grade via regex (app.py, Lines 400-440)
        ↓
Return to user via /results/{job_id} endpoint
        ↓
Display on frontend with chat interface
```

---

## DIAGNOSIS PROCEDURE

### Step 1: Push Changes to Render
```bash
git add -A
git commit -m "Add comprehensive diagnostic logging to identify Render hang"
git push origin deployment-ready
```

### Step 2: Wait for Rebuild
Render automatically rebuilds from GitHub (1-2 minutes)

### Step 3: Run Test Upload
1. Use frontend to upload same problematic audio file
2. Monitor Render Live Logs during execution
3. Look for log patterns:

### Step 4: Identify Root Cause from Logs

**Pattern 1: Memory Wall**
```
[MEMORY AFTER_LOAD_AUDIO] RSS: 350.0MB
[MEMORY AFTER_REDUCE_NOISE] RSS: 380.0MB
[SYSTEM ...] RAM: 400.0MB (78.1%)
[SYSTEM ...] RAM: 450.0MB (87.9%)
[SYSTEM ...] RAM: 500.0MB (97.7%)
[SYSTEM ...] RAM: 512.0MB (100%)
→ Service killed
```
**Fix:** Memory optimization already applied (sr=22050 should reduce to ~150MB)

**Pattern 2: Gunicorn Worker Blocking**
```
[PIPELINE_START] job abc123
[PIPELINE_RUNNING] job abc123
[Request] GET /status/abc123 → TIMEOUT
[Request] GET /status/abc123 → TIMEOUT
[Request] GET /status/abc123 → TIMEOUT
→ 5+ minutes of timeouts while pipeline running
→ Service killed
```
**Fix:** Change Render Start Command from:
```bash
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```
To:
```bash
gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT -t 300 app:app
```

**Pattern 3: Music21 Parsing Hang**
```
[PIPELINE_START] job abc123: /uploads/audio.wav
[PIPELINE_RUNNING] job abc123
[Layer 2: Audio Processing]
[AUDIO_CHECK] Completed in 8.23s
[NOISE_REDUCE] Completed in 22.34s
[NORMALIZE] Completed in 5.12s
[Block 0: ScoreGraph Generation]
[Loading score with music21...]
→ No more logs for 5+ minutes
→ Service killed
```
**Fix:** Implement subprocess wrapper with timeout (not yet done)

---

## CURRENT STATUS

| Item | Status | Evidence |
|------|--------|----------|
| Memory optimization | ✅ Applied | `sr=22050, dtype=np.float32` in processing_layer.py line 145 |
| Diagnostic logging | ✅ Applied | 20+ log points added, psutil monitoring enabled |
| Memory tracking | ✅ Applied | `[MEMORY ...]` tags at 8+ critical points |
| Pipeline timing | ✅ Applied | `[PIPELINE_*]` tags with elapsed seconds |
| System monitoring | ✅ Applied | `[SYSTEM ...]` tags logging RAM/CPU/threads |
| Render deployment | ⏳ Pending | Awaiting git push to Render |
| Real-world testing | ⏳ Pending | Awaiting Render rebuild + test upload |
| Root cause analysis | ⏳ Pending | Awaiting log analysis from test run |
| Worker fix | ⏳ Pending | May need Gunicorn threading config change |
| Score parsing fix | ⏳ Pending | May need subprocess wrapper implementation |

---

## COMMANDS FOR DEPLOYMENT

### Push Diagnostic Logging to Render
```bash
cd c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace
git add -A
git commit -m "Add comprehensive diagnostic logging for Layer 2 bottleneck analysis"
git push origin deployment-ready
```

### Monitor Render Build
```bash
# In Render dashboard, watch the deployment logs:
# https://dashboard.render.com
```

### Trigger Test Run
1. Open frontend at https://music4-d.vercel.app
2. Upload same audio file that was hanging
3. Monitor Render Live Logs in parallel:
   - Click on "Live Logs" button in Render dashboard
   - Watch for `[MEMORY ...]`, `[SYSTEM ...]`, `[PIPELINE ...]` tags

### Analyze Logs
Once test completes (success or failure):
1. Save Render logs to file
2. Search for memory pattern (Memory Wall)
3. Search for timeout pattern (Worker Blocking)
4. Search for hang pattern (Parsing Hang)
5. Match to one of 3 scenarios above
6. Apply corresponding fix

---

## FILES NOT YET CREATED/MODIFIED

These may be needed if diagnosis points to them:

### If Worker Blocking Issue:
- Modify Render start command (change from sync to async workers)
- File: Render dashboard → Settings → Start Command
- Change to: `gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT -t 300 app:app`

### If Music21 Parsing Hang:
- Create: `parse_score_helper.py` (subprocess wrapper with timeout)
- Modify: `block_0_scoregraph/build_scoregraph_with_notes.py` to use subprocess
- Add timeout: 10 seconds for score parsing

### If Further Memory Optimizations Needed:
- Implement: Chunk-based audio processing (process in segments)
- File: `processing_layer.py`
- Method: Instead of loading entire audio, process in 30-second chunks

---

## CRITICAL RENDER ENVIRONMENT DETAILS

| Setting | Value | Impact |
|---------|-------|--------|
| Free Tier RAM | 512 MB | Very tight for audio processing |
| CPU | 0.5 CPU | Slow at heavy computation |
| Worker Model | Sync (blocking) | Each worker blocks others |
| Timeout | ~5 minutes | Pipeline must complete in <300s |
| Python Version | 3.10 | ✓ Compatible |
| Build Time | 2-3 min | Automatic from GitHub |

---

## QUICK DEBUGGING CHECKLIST

- [ ] Pull latest code from GitHub
- [ ] Check `requirements.txt` has `psutil>=5.8.0`
- [ ] Verify processing_layer.py line 145 has `sr=22050, dtype=np.float32`
- [ ] Verify processing_layer.py has `log_memory_usage()` function
- [ ] Verify app.py has `log_system_status()` function
- [ ] Push to Render with: `git push origin deployment-ready`
- [ ] Wait for Render rebuild (2-3 min)
- [ ] Run test upload via frontend
- [ ] Monitor Render Live Logs
- [ ] Capture full log output
- [ ] Search for Memory Wall / Worker Blocking / Parsing Hang pattern
- [ ] Apply specific fix based on pattern match
- [ ] Re-test to verify fix
- [ ] Document findings

---

END OF QUICK REFERENCE
