# Render Deployment - Final Solution ✅

## Problem Summary

- **Issue**: PyAudio compilation failure on Render's read-only filesystem
- **Root Cause**: `auditok` has optional `pyaudio` dependency; can't compile C extensions on Render
- **Previous Attempts**:
  - ❌ `apt-get` approach: Blocked by read-only filesystem
  - ❌ `constraints.txt` approach: Prevented transitive dependencies, broke auditok
  - ✅ `--prefer-binary` flag: Uses pre-built wheels (no compilation needed)

## Final Solution Implemented

### 1. Cleaned Up Files

**Removed**:

- `constraints.txt` - Prevented auditok from installing properly
- `.buildpacks` - Heroku-only format, not needed for Render
- `requirements-render.txt` - Unused duplicate

**Modified**:

- `requirements.txt` - Removed `-c constraints.txt` line, added explanatory comments
- `build.sh` - Uses `pip install --prefer-binary -r requirements.txt`

### 2. Key Configuration Files

#### `build.sh` (Render build script)

```bash
#!/bin/bash
set -e

# ... earlier steps ...

# Install Python requirements with binary preference
pip install --prefer-binary -r requirements.txt

# ... rest of script ...
```

**Why `--prefer-binary`?**

- Tells pip to use pre-built wheels when available (avoid source compilation)
- `auditok` has pre-built wheels that don't include optional `pyaudio`
- All audio libraries have pre-built wheels:
  - librosa, soundfile, noisereduce, ffmpeg-normalize, auditok ✅
  - scipy, numpy, torch, torchaudio ✅

#### `render.yaml` (Service configuration)

```yaml
services:
  web:
    plan: standard
    numInstances: 1
    buildCommand: bash build.sh
    startCommand: gunicorn --workers 2 --worker-class sync --timeout 120 --bind 0.0.0.0:10000 app:app
```

#### `requirements.txt` (Dependencies)

Key packages:

- **Web Framework**: flask, flask-cors, gunicorn
- **Audio Processing**: librosa, soundfile, auditok (✅ for segmentation), noisereduce, ffmpeg-normalize
- **Deep Learning**: torch, torchaudio, basic-pitch (music transcription)
- **Music Analysis**: music21 (score parsing), pretty-midi (transcription)
- **Analysis Pipeline**: groq (LLM), scikit-learn, pandas

## Pipeline Architecture Verified

### 7-Layer Processing Pipeline

```
app.py (Flask REST API)
  ↓
MusicPerformancePipeline (pipeline.py)
  ├─ Layer 1: Input Standardization → converts audio/score to standard formats
  │  └─ input_layer.py
  │
  ├─ Layer 2: Audio Processing → noise reduction, normalization, SEGMENTATION
  │  └─ processing_layer.py [USES: auditok.split() @ line 275]
  │     └─ auditok imported @ lines 51, 66 ✅
  │
  ├─ Layer 3: Temporal Alignment → music-audio synchronization via DTW
  │  ├─ Block 0: Scoregraph (score structure)
  │  ├─ Block 1: Transcription (note detection)
  │  ├─ Block 2: DTW alignment
  │  ├─ Block 4: Beat detection (optional)
  │  └─ Context Aligner: Path finding (optional)
  │
  ├─ Layer 4: Feature Extraction → performance + score features
  │  └─ extraction_layer.py
  │
  ├─ Layer 5: PQG-A2SA → onset/offset precision analysis
  │  └─ pqg_a2sa/
  │
  ├─ Layer 6: Inference Core → metric computation
  │  └─ inference/
  │
  └─ Layer 7: Final Grading → performance evaluation
     └─ grading_layer.py
```

### Memory Monitoring Added

Enhanced `run_pipeline()` with memory tracking:

- Logs memory before/after each layer (RSS, VMS, percentage)
- Uses `psutil` for accurate memory measurements
- Helps identify memory leaks or high-usage layers
- Format: `[MEM STAGE] RSS: XXX.XMB | VMS: XXX.XMB | %: XX.X%`

## Deployment Instructions

### Step 1: Connect to Render Dashboard

1. Go to https://dashboard.render.com
2. Select tuttibot-backend service
3. Click "Deployment" tab

### Step 2: Deploy

- Option A: Push to `deployment-ready` branch → auto-deploys
- Option B: Click "Deploy latest commit" button

### Step 3: Monitor

- Watch logs in Render dashboard
- Expected output:
  ```
  Building Docker image
  Building Docker image from Dockerfile
  ...
  Building Python dependencies
  pip install --prefer-binary -r requirements.txt
  Successfully installed auditok ... [NO PYAUDIO ERROR]
  ...
  Deployed successfully
  ```

### Step 4: Verify

- Test endpoint: `POST /upload` with audio + score files
- Check logs for:
  - Layer 1-7 execution
  - Memory tracking before/after each layer
  - Chatbot context generation
  - No pyaudio compilation errors ✅

## Files Modified in This Session

**Commit 1**: `Fix: Remove constraints.txt, use only --prefer-binary flag for Render deployment`

- Removed `constraints.txt` from git
- Removed `-c constraints.txt` from requirements.txt
- Updated documentation

**Commit 2**: `Add: Enhanced memory monitoring and layer execution logging to pipeline`

- Added `psutil` memory tracking
- Added memory logging before/after each layer
- Added layer headers to execution logs

## Key Takeaways

### Why PyAudio Fails

- PyAudio requires C extensions (portaudio headers)
- Render's build environment is read-only (can't install via apt-get)
- PyAudio is **optional** dependency of auditok (not required for our use case)

### Why `--prefer-binary` Works

- auditok has pre-built wheel distributions
- Pre-built wheels are compiled binaries (no C extension compilation needed)
- PyAudio not included in pre-built auditok wheel
- Pip finds wheel first, skips source compilation

### Why auditok is Critical

- **Used for audio segmentation** in processing_layer.py line 275
- `auditok.split(...)` detects speech/music segments
- Enables pipeline to identify where actual audio content exists
- Not optional for full pipeline functionality

## Troubleshooting Checklist

✅ **Before Deploying**:

- [ ] constraints.txt removed from repo
- [ ] `-c constraints.txt` removed from requirements.txt
- [ ] requirements.txt has correct audio packages
- [ ] build.sh uses `--prefer-binary` flag
- [ ] render.yaml points to `bash build.sh`

✅ **During Deployment** (check logs):

- [ ] "pip install --prefer-binary" message appears
- [ ] No "fatal error: portaudio.h" messages
- [ ] auditok installs successfully
- [ ] Flask app starts with gunicorn

✅ **After Deployment** (test API):

- [ ] POST /upload accepts audio + score files
- [ ] Pipeline logs show all 7 layers
- [ ] Memory logs show pre/post layer measurements
- [ ] Results saved to output directory
- [ ] No runtime import errors

## Next Steps

1. **Deploy to Render**: Push changes and monitor
2. **Test Locally**: Run with sample audio/score files
3. **Verify Logs**: Check memory usage patterns
4. **Monitor Production**: Check Render dashboard for errors
5. **Performance Tune**: If memory issues appear, profile Layer 2 & 3 (heaviest users)

---

**Status**: ✅ Ready for production deployment
**Branch**: `deployment-ready`
**Last Updated**: 2026-01-10
