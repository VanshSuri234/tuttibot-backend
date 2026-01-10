# Comprehensive Pipeline Execution Logging Guide

## Overview

You now have **comprehensive execution flow logging** throughout the entire pipeline to identify exactly where it gets stuck when running on Render. The logging tracks:

- **Execution timing** at each stage
- **Memory usage** before/after each layer
- **Entry/exit points** for every function
- **Block-by-block progress** in temporal alignment
- **Error context** with full tracebacks

## Log Output Examples

### Example: Successful Pipeline Run

```
[EXECUTION_START] Job: abc123
[INPUTS] Audio: performance.wav | Score: score.xml
[OUTPUT_DIR] /results/abc123
[STATUS_UPDATE] Layer 0: Initializing

[CHECKPOINT] Importing MusicPerformancePipeline
[PIPELINE_INIT] Creating pipeline object for job abc123
[PIPELINE_INIT_COMPLETE] Pipeline object created successfully
[PIPELINE_EXECUTION_START] Calling pipeline.run_pipeline()

================================================================================
  🎵 MUSIC PERFORMANCE ANALYSIS PIPELINE - EXECUTION START
================================================================================
  📁 Audio File: performance.wav (...)
  🎼 Score File: score.xml (...)
  📤 Output Dir: /results/abc123 (abc123)
  ⏰ Started: 2026-01-10 12:34:56.123
================================================================================

[SYSTEM BEFORE_PIPELINE_INIT__abc123] RAM: 256.3MB (8.5%) | CPU: 12.3% | Threads: 5
[MEM PIPELINE_START] RSS: 256.3MB | VMS: 512.5MB | %: 8.5%

————————————————————————————————————————————————————————————————————————————————
[LAYER 1️⃣  INPUT STANDARDIZATION] Starting...
————————————————————————————————————————————————————————————————————————————————
[MEM LAYER_1_START] RSS: 256.3MB | VMS: 512.5MB | %: 8.5%
[INPUT LAYER] Starting input validation and standardization...
[INPUT LAYER] Importing MusicInputLayer...
[INPUT LAYER] MusicInputLayer imported successfully
[INPUT LAYER] Processing audio: performance.wav
[INPUT LAYER] Processing score: score.xml
[INPUT LAYER] ✅ Audio validated: performance.wav
[INPUT LAYER] ✅ Score validated: score.xml
[INPUT LAYER] ✅ COMPLETE in 2.34s
[MEM LAYER_1_END] RSS: 258.7MB | VMS: 514.2MB | %: 8.6%
✅ Layer 1 Complete: 2.34s

————————————————————————————————————————————————————————————————————————————————
[LAYER 2️⃣  AUDIO PROCESSING] Starting...
   - Noise reduction, normalization, segmentation (auditok)
————————————————————————————————————————————————————————————————————————————————
[MEM LAYER_2_START] RSS: 258.7MB | VMS: 514.2MB | %: 8.6%
[PROCESSING LAYER] Starting audio processing...
[PROCESSING LAYER] Importing ProcessingLayer...
[PROCESSING LAYER] ProcessingLayer imported successfully
[PROCESSING LAYER] Creating processor with data_dir: ...
[PROCESSING LAYER] Calling processing_layer.process()...
[PROCESSING LAYER] ✅ Audio processed: performance_processed.wav
[PROCESSING LAYER] Saving processing metadata...
[PROCESSING LAYER] ✅ Metadata saved: ...processing_metadata.json
[PROCESSING LAYER] ✅ COMPLETE in 45.67s
[MEM LAYER_2_END] RSS: 384.2MB | VMS: 768.5MB | %: 12.8%
✅ Layer 2 Complete: 45.67s

[Comment: Layer 2 is the slowest - processes audio through librosa, noisereduce, ffmpeg-normalize, and auditok]

————————————————————————————————————————————————————————————————————————————————
[LAYER 3️⃣  TEMPORAL ALIGNMENT] Starting...
   - Blocks: Scoregraph → Transcription → DTW → Beat Detection
————————————————————————————————————————————————————————————————————————————————
[MEM LAYER_3_START] RSS: 384.2MB | VMS: 768.5MB | %: 12.8%
[TEMPORAL ALIGNMENT] Starting temporal alignment (Blocks 0→1→4→Context→2)...
[TEMPORAL ALIGNMENT] Importing temporal alignment modules...

[TEMPORAL ALIGNMENT] Running Block 0: ScoreGraph Generation...
[TEMPORAL ALIGNMENT] ✅ Block 0 Complete: 3.21s

[TEMPORAL ALIGNMENT] Running Block 1: Audio Transcription...
[TEMPORAL ALIGNMENT] ✅ Block 1 Complete: 28.45s

[Comment: Block 1 uses basic-pitch which can be slow - may hang here on Render if GPU not available]

[TEMPORAL ALIGNMENT] Running Block 4: Beat Detection (optional)...
[TEMPORAL ALIGNMENT] ℹ️  Block 4 (optional): 5.12s

[TEMPORAL ALIGNMENT] Running Block 2: DTW Alignment...
[TEMPORAL ALIGNMENT] ✅ Block 2 Complete: 15.67s

[TEMPORAL ALIGNMENT] ✅ ALL BLOCKS COMPLETE: 52.45s
[MEM LAYER_3_END] RSS: 456.8MB | VMS: 912.3MB | %: 15.2%
✅ Layer 3 Complete: 52.45s

————————————————————————————————————————————————————————————————————————————————
[LAYER 4️⃣  FEATURE EXTRACTION] Starting...
   - Performance + Score features extraction
————————————————————————————————————————————————————————————————————————————————
[MEM LAYER_4_START] RSS: 456.8MB | VMS: 912.3MB | %: 15.2%
[EXTRACTION LAYER] Starting feature extraction...
[EXTRACTION LAYER] Importing ExtractionLayer...
[EXTRACTION LAYER] ExtractionLayer imported successfully
[EXTRACTION LAYER] Creating ExtractionLayer instance...
[EXTRACTION LAYER] Audio: ...performance_processed.wav
[EXTRACTION LAYER] Score: ...score.xml
[EXTRACTION LAYER] Calling extraction_layer.process_all()...
[EXTRACTION LAYER] ✅ Feature extraction complete: 8.92s
[MEM LAYER_4_END] RSS: 512.1MB | VMS: 1024.5MB | %: 17.1%
✅ Layer 4 Complete: 8.92s

————————————————————————————————————————————————————————————————————————————————
[LAYER 5️⃣  PQG-A2SA ANALYSIS] Starting...
   - Onset/Offset precision analysis (optional)
————————————————————————————————————————————————————————————————————————————————
[MEM LAYER_5_START] RSS: 512.1MB | VMS: 1024.5MB | %: 17.1%
[PQG-A2SA LAYER] Starting PQG-A2SA analysis...
[PQG-A2SA LAYER] Checking for MIDI score...
[PQG-A2SA LAYER] ⚠️  Using performance MIDI as score (not ideal)
[PQG-A2SA LAYER] Importing PQG-A2SA modules...
[PQG-A2SA LAYER] PQGAligner imported successfully
[PQG-A2SA LAYER] Creating PQGAligner instance and running alignment...
[PQG-A2SA LAYER] ✅ Alignment complete
[PQG-A2SA LAYER] Converting results and saving...
[PQG-A2SA LAYER] ✅ Results saved: (3.45s)
[MEM LAYER_5_END] RSS: 528.3MB | VMS: 1056.2MB | %: 17.6%
✅ Layer 5 Complete: 3.45s

————————————————————————————————————————————————————————————————————————————————
[LAYER 6️⃣  INFERENCE CORE] Starting...
   - Metric computation and analysis
————————————————————————————————————————————————————————————————————————————————
[MEM LAYER_6_START] RSS: 528.3MB | VMS: 1056.2MB | %: 17.6%
[INFERENCE LAYER] Starting inference core...
[INFERENCE LAYER] Importing inference modules...
[INFERENCE LAYER] Inference modules imported
[INFERENCE LAYER] Loading alignment results: .../alignment.json
[INFERENCE LAYER] ✅ Alignment metrics loaded (45 items)
[INFERENCE LAYER] Loading extraction features...
[INFERENCE LAYER] ✅ Performance features loaded
[INFERENCE LAYER] ✅ Score features loaded
[INFERENCE LAYER] ✅ PQG-A2SA metrics loaded
[INFERENCE LAYER] Creating comprehensive grading package...
[INFERENCE LAYER] Saving grading package...
[INFERENCE LAYER] ✅ Inference package saved: (1.23s)
[MEM LAYER_6_END] RSS: 534.7MB | VMS: 1068.3MB | %: 17.8%
✅ Layer 6 Complete: 1.23s

————————————————————————————————————————————————————————————————————————————————
[LAYER 7️⃣  FINAL GRADING] Starting...
   - Performance evaluation and grading
————————————————————————————————————————————————————————————————————————————————
[MEM LAYER_7_START] RSS: 534.7MB | VMS: 1068.3MB | %: 17.8%
[GRADING LAYER] Starting final grading layer...
[GRADING LAYER] Importing grading modules...
[GRADING LAYER] Grading modules imported
[GRADING LAYER] Loading grading package...
[GRADING LAYER] Loading: .../grading_package_master.json
[GRADING LAYER] Extracting metrics from package...
[GRADING LAYER] Using weights: {...}
[GRADING LAYER] Computing component scores...
[GRADING LAYER] Saving final grade JSON...
[GRADING LAYER] Generating performance report...
[GRADING LAYER] ✅ Final grade: 87.5/100
[GRADING LAYER] ✅ Grade saved: .../final_grade.json
[GRADING LAYER] ✅ Report saved: .../performance_report.txt
[GRADING LAYER] ✅ COMPLETE in 0.87s
[MEM LAYER_7_END] RSS: 542.1MB | VMS: 1074.6MB | %: 18.1%
✅ Layer 7 Complete: 0.87s

————————————————————————————————————————————————————————————————————————————————
[FINAL STEP] Generating Chatbot Context...
————————————————————————————————————————————————————————————————————————————————
[MEM CONTEXT_START] RSS: 542.1MB | VMS: 1074.6MB | %: 18.1%
✅ Chatbot Context Generated: 0.45s
[MEM CONTEXT_END] RSS: 548.9MB | VMS: 1082.1MB | %: 18.3%

————————————————————————————————————————————————————————————————————————————————
[SAVING] Pipeline Summary...
✅ Pipeline Summary Saved

================================================================================
  ✨ PIPELINE EXECUTION COMPLETE ✨
================================================================================

📊 LAYER EXECUTION TIMES:
   L1: 2.34s
   L2: 45.67s    ← Slowest: Audio processing with librosa, noisereduce, ffmpeg-normalize, auditok
   L3: 52.45s    ← Second slowest: DTW alignment with blocks 0,1,2,4
   L4: 8.92s
   L5: 3.45s
   L6: 1.23s
   L7: 0.87s

⏱️  TOTAL TIME: 115.93s
⏰ Completed: 2026-01-10 12:36:51.456
================================================================================
```

## How to Analyze Logs When Pipeline Gets Stuck

### Step 1: Deploy and Monitor Logs on Render

1. Go to Render Dashboard → Select tuttibot-backend
2. Click "Logs" tab
3. Upload audio + score via API
4. Watch logs in real-time

### Step 2: Identify Stuck Layer

Look for which layer's logs STOP appearing:

```
✅ Layer 2 Complete: 45.67s
✅ Layer 3 Complete: 52.45s
✅ Layer 4 Complete: 8.92s
[LAYER 5️⃣  PQG-A2SA ANALYSIS] Starting...
[PQG-A2SA LAYER] Starting PQG-A2SA analysis...
[PQG-A2SA LAYER] Checking for MIDI score...

(no more logs = STUCK in Layer 5)
```

### Step 3: Common Stuck Points

**If stuck in Layer 2 (Audio Processing)**

- Check: Librosa or ffmpeg-normalize is hanging
- Likely: Audio file too large or invalid format
- Fix: Ensure audio is WAV/MP3 and under 10MB

**If stuck in Layer 3, Block 1 (Transcription)**

- Check: basic-pitch audio transcription taking too long
- Likely: GPU not available or hanging
- Fix: May need GPU optimization or timeout

**If stuck in Layer 5 (PQG-A2SA)**

- Check: MIDI alignment is taking too long
- Likely: High-sample-rate audio or complex score
- Fix: Downsample audio or simplify score

### Step 4: Check Memory Usage

Look at memory progression:

```
[MEM LAYER_1_START] RSS: 256.3MB | VMS: 512.5MB | %: 8.5%
...
[MEM LAYER_2_START] RSS: 258.7MB | VMS: 514.2MB | %: 8.6%
[MEM LAYER_2_END] RSS: 384.2MB | VMS: 768.5MB | %: 12.8%  ← Used 125MB
[MEM LAYER_3_START] RSS: 384.2MB | VMS: 768.5MB | %: 12.8%
[MEM LAYER_3_END] RSS: 456.8MB | VMS: 912.3MB | %: 15.2%   ← Used 72MB
```

**Normal pattern**: Memory grows 5-20MB per layer, then releases
**Problem pattern**: Memory keeps growing without release (memory leak)

### Step 5: Check Block-by-Block Progress

For Layer 3, logs will show which block is stuck:

```
[TEMPORAL ALIGNMENT] Running Block 0: ScoreGraph Generation...
[TEMPORAL ALIGNMENT] ✅ Block 0 Complete: 3.21s

[TEMPORAL ALIGNMENT] Running Block 1: Audio Transcription...
(no more logs = STUCK in Block 1)
```

## Log File Location

Logs are also saved to files:

- **Local development**: Console output + gunicorn logs
- **Render production**: Check Render dashboard "Logs" tab in real-time

## Environment Variables to Enable More Logging

Add to `render.yaml` or set in Render dashboard:

```yaml
env:
  PYTHONUNBUFFERED: "1" # Flush logs immediately
  LOGLEVEL: "DEBUG" # More detailed logs (optional)
```

## Key Log Markers for Monitoring

### Success Indicators

```
✅ Layer X Complete: Y.ZZs
[MEM LAYER_X_END] RSS: XXX.XMB | VMS: XXX.XMB | %: XX.X%
```

### Failure Indicators

```
❌ Layer X FAILED
❌ Layer X Exception: error message
⚠️  Layer X Error (continuing): error message
```

### Performance Warnings

```
Layer 2 (Audio Processing): >60s = may hang on Render
Layer 3, Block 1 (Transcription): >120s = GPU timeout possible
Memory growth: +50MB+ per layer = potential memory leak
```

## What to Report if Pipeline is Stuck

When asking for help, include:

1. **Last successful log line** - where it got stuck
2. **Layer execution times** - which was slowest
3. **Memory progression** - any unexplained jumps
4. **Audio file details** - size, format, duration
5. **Score file details** - format, instrument count

Example:

```
Pipeline stuck in Layer 5 (PQG-A2SA)
Last log: [PQG-A2SA LAYER] Checking for MIDI score...
Layer times: L1: 2.3s, L2: 45.6s, L3: 52.4s, L4: 8.9s, L5: HUNG
Memory: 256MB → 548MB (normal growth)
Audio: 5.2MB, 48kHz, mono, WAV
Score: 4KB, MusicXML, SATB
```

---

**Status**: ✅ Ready to deploy with comprehensive logging  
**Branch**: `deployment-ready`  
**Date**: 2026-01-10
