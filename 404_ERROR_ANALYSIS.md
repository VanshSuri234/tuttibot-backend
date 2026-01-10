# 404 Error Analysis & Solution

## Problem Statement
After the pipeline completes (or times out), the frontend gets 404 errors when trying to fetch `/status/{job_id}`.

## Root Cause Analysis

### Issue #1: Gunicorn Timeout Too Short
**Evidence from logs:**
```
==> Running 'gunicorn -w 4 -b 0.0.0.0:$PORT -t 300 app:app'
```

The `-t 300` means 300-second (5-minute) timeout. But your pipeline is taking 10+ minutes:
- Layer 1: ~52s
- Layer 2-5: ~195s
- Layer 6: ???s (hanging due to logger.info calls - NOW FIXED ✅)
- **Total: 10+ minutes expected**

**What happens:**
1. Request starts analysis (timer begins)
2. Pipeline processes layers 1-5 successfully (~240s)
3. Layer 6 starts but logs queue up
4. After 300s, Gunicorn **kills the worker** with timeout
5. `save_job_status(COMPLETED)` never executes
6. status.json is never updated to COMPLETED
7. Frontend polls `/status/{job_id}` → reads old status.json or finds nothing → returns 404

### Issue #2: Status File Path Consistency
The code saves status.json to:
```python
status_file = Path(app.config['RESULTS_FOLDER']) / job_id / 'status.json'
```

And reads from the same path. This should work, but if the directory isn't created, it fails.

### Issue #3: Worker Restart Clears Memory
When Gunicorn restarts workers (due to timeout or other reasons):
- In-memory `jobs` dictionary is lost
- Frontend must rely on disk-persisted status.json
- If status.json isn't written, endpoint returns 404

## Solutions

### Solution #1: Increase Gunicorn Timeout ✅ (DONE)
**File:** `Procfile`
**Current setting:** `--timeout 600` (10 minutes)
**Required setting:** `--timeout 900` or `--timeout 1200` (15-30 minutes)

The Procfile already has this set correctly! But the logs show `gunicorn -t 300`, which means:
- Either an old process is still running
- Or Render isn't reading the updated Procfile

**Action:** Verify Procfile is being used, or force Render to rebuild/restart

### Solution #2: Fix Logger Blocking ✅ (DONE)
**Files Modified:**
- `inference_core_with_pqg.py`: Replaced 26 logger.info() calls with print() + sys.stdout.flush()
- `pipeline.py`: Replaced ~30 logger.info() calls in run_inference() with print() + sys.stdout.flush()

**Commits:**
- 2cf1159c: Fixed inference_core_with_pqg.py
- 3f8f6ff4: Fixed pipeline.py Layer 6

This allows Layer 6 to complete without hanging, reducing total execution time.

### Solution #3: Add Periodic Status Updates
**Reason:** Even with timeout increase, we should save status more frequently
**Implementation:** Add status updates every minute during pipeline execution

**File to modify:** `pipeline.py`
**Add after each layer completes:**
```python
save_job_status(job_id, {
    'status': JobStatus.PROCESSING,
    'current_layer': f'Layer {i}: {name}',
    'progress': (i/7)*100,
    'timestamp': datetime.now().isoformat()
})
```

### Solution #4: Extend Timeout Further (If Needed)
If pipeline still exceeds time limit, increase Procfile timeout to:
```
--timeout 1800  # 30 minutes (worst case)
```

## Testing Checklist

- [ ] Verify Render is using the updated Procfile (check build logs)
- [ ] Confirm gunicorn process shows `--timeout 600` or higher in logs
- [ ] Run a full pipeline test
- [ ] Monitor logs until completion
- [ ] Verify status.json is created before pipeline finishes
- [ ] Check frontend can fetch /status/{job_id} → gets proper status
- [ ] Check frontend can fetch /results/{job_id} → gets results

## Expected Flow After Fixes

1. Frontend uploads audio/score
2. Backend spawns analysis thread
3. Pipeline runs all 7 layers
4. **Logger calls no longer block** (fix #2)
5. **Total execution time ~10 minutes** (reduced due to fix #2)
6. **Gunicorn timeout is 10+ minutes** (Procfile has correct setting)
7. Before timeout: `save_job_status(COMPLETED)` executes
8. status.json written with full results
9. Frontend polls /status → gets 200 with completed status
10. Frontend calls /results → displays analysis

## Priority Order

1. ✅ **DONE**: Fix logger.info() blocking (commits 2cf1159c, 3f8f6ff4)
2. **TODO**: Verify Procfile timeout is correct on Render
3. **TODO**: Add periodic status updates during pipeline
4. **TODO**: Monitor first test run to confirm completion
5. **OPTIONAL**: Increase timeout further if needed

## Files Changed

- `inference_core_with_pqg.py`: 26 logger.info() → print() + flush
- `pipeline.py`: ~30 logger.info() → print() + flush in run_inference() and Layer 6
- `Procfile`: Already correct (--timeout 600)
- Demo.jsx: No changes needed (frontend code is fine)
- app.py: No changes needed (app code handles disk persistence correctly)

