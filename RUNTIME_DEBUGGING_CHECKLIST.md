# 🚨 TuttiBot Runtime Debugging Checklist

## **Before Running Pipeline - Quick Health Check**

```bash
# 1. Environment Check
python --version              # Must be 3.10.12
which python                  # Should be in tuttibot_py310_env

# 2. Critical Import Test
python -c "
import numpy; print('NumPy:', numpy.__version__)     # Must be 1.26.4
import tensorflow; print('TF:', tensorflow.__version__)  # Must be 2.15.0
import basic_pitch; print('Basic Pitch: OK')
import librosa; print('Librosa: OK')
import music21; print('Music21: OK')
import auditok; print('Auditok: OK')
print('✅ ALL IMPORTS SUCCESSFUL')
"
```

## **Common Runtime Errors & Instant Fixes**

### ❌ `Error in audio segmentation: unknown format: 65534`
**Problem:** auditok can't read the WAV file format  
**Instant Fix:** Already fixed in `PROCESSING_LAYER/processing_layer.py` with format standardization  
**Prevention:** Always process audio through soundfile first

### ❌ `'Score' object has no attribute 'flatten'`
**Problem:** music21 API changed, `flatten()` method no longer exists  
**Instant Fix:** Already fixed in `PROCESSING_LAYER/processing_layer.py` using `score.flat`  
**Prevention:** Use `score.flat.notesAndRests` instead of `score.flatten().notesAndRests`

### ❌ `AttributeError: _ARRAY_API not found`
**Problem:** NumPy 2.x vs TensorFlow compatibility  
**Instant Fix:**
```bash
pip install "numpy==1.26.4" --force-reinstall
```

### ❌ `Cannot dlopen some GPU libraries`
**Problem:** Missing or wrong CUDA/cuDNN versions  
**Instant Fix:**
```bash
pip install "nvidia-cudnn-cu11==8.9.4.25" --force-reinstall
```

## **Pipeline Output Quality Check**

### ✅ Good Results Indicators:
- Audio segments: 1-10 segments (not 0, not 100+)
- Music features: >0 notes extracted
- Key signature detected (not "Unknown")
- Processing time: 10-30 seconds total
- No error messages in output

### ❌ Bad Results Indicators:
- 0 segments detected → Audio segmentation failed
- 0 music features → Score parsing failed  
- Many fallback messages → Core algorithms not working
- Processing time >60 seconds → Something is struggling

## **Emergency Recovery**

If everything breaks:
```bash
# Nuclear option - rebuild environment
rm -rf tuttibot_py310_env
python -m venv tuttibot_py310_env
source tuttibot_py310_env/bin/activate
pip install --upgrade pip
pip install "numpy==1.26.4"
pip install -r requirements_original_clone.txt
pip install "numpy==1.26.4" --force-reinstall
```

## **Expected Working Output Example**
```
🎵 STEP 1: INPUT LAYER ✅
✅ Audio processed: Already correct format
✅ Score processed: PDF converted to MusicXML

🔧 STEP 2: PROCESSING LAYER ✅  
Audio segmentation completed: 3 segments found
Music feature extraction completed: 27 notes, C major key, 4/4 time
✅ Audio cleaned and segmented: 3 segments
✅ Music features extracted: 27 features

📊 STEP 3: EXTRACTION LAYER ✅
✅ Audio features extracted: 840.1 KB
✅ Score features extracted: 1.8 KB

🎉 PIPELINE COMPLETED SUCCESSFULLY! 🎉
⏱️ Total processing time: 14.3 seconds
```

**Key Success Metrics:**
- Segments detected: 3 (reasonable for music piece)
- Notes extracted: 27 (matches expected melody)
- No error messages or fallback warnings
- Reasonable processing time (~14 seconds)

---

**Last Updated:** September 4, 2025  
**Use this checklist BEFORE reporting any issues!**
