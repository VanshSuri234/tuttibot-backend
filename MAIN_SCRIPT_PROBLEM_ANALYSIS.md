# TuttiBot v02 Main Script Problems and Solutions

## 📊 **Current Status Summary**

### ✅ **RESOLVED ISSUES:**
1. **Missing dependencies** - Installed all core packages
2. **Block 0 (ScoreGraph) tempo bug** - Fixed None tempo issue
3. **Python cache conflicts** - Cleared and resolved
4. **Input Layer working** - MusicXML processing successful
5. **GPU Manager working** - Proper CPU fallback detected

### ⚠️ **CURRENT ISSUE:**
**Block 1 (AMT) - Basic Pitch not available**
- `basic-pitch` command not found
- Package conflicts with Python 3.13 and TensorFlow versions

### 🛠️ **DETAILED FIXES APPLIED:**

#### 1. **Dependency Installation:**
```bash
✅ pip install psutil numpy scipy pandas matplotlib
✅ pip install music21 pretty_midi mido  
✅ pip install librosa soundfile audioread==3.0.1
✅ pip install pdf2image oemer
```

#### 2. **Block 0 ScoreGraph Fix:**
**Problem:** `TypeError: unsupported operand type(s) for /: 'float' and 'NoneType'`

**Root Cause:** Tempo variable was None when no tempo markings found in score

**Solution Applied:**
```python
# OLD CODE (broken):
def extract_musical_notes(part, tempo=120.0):
    tempo_markings = part.flat.getElementsByClass(music21_tempo.TempoIndication)
    if tempo_markings:
        tempo = tempo_markings[0].number
    # tempo could be None here!

# NEW CODE (fixed):
def extract_musical_notes(part, default_tempo=120.0):
    tempo = default_tempo  # Always start with default
    tempo_markings = part.flat.getElementsByClass(music21_tempo.TempoIndication)
    if tempo_markings:
        tempo = tempo_markings[0].number
    if tempo is None:  # Extra safety check
        tempo = default_tempo
```

#### 3. **Block 0 Results:**
✅ **Successfully processed test.musicxml:**
- Total measures: 153
- Total beat nodes: 610  
- Total note nodes: 808
- Total nodes: 1418
- ScoreGraph saved successfully

### 🔧 **REMAINING SOLUTION OPTIONS:**

#### **Option 1: Install TensorFlow for basic-pitch (Challenging)**
```bash
# This has compatibility issues with Python 3.13
pip install tensorflow>=2.20.0
pip install basic-pitch
```
**Issues:** TensorFlow 2.20.0 vs basic-pitch requirement conflict

#### **Option 2: Alternative AMT Method (Recommended)**
Modify Block 1 to use librosa-based onset detection:
```python
import librosa
import numpy as np

def simple_amt_with_librosa(audio_path):
    y, sr = librosa.load(audio_path)
    # Onset detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    
    # Simple pitch tracking
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    # ... process to extract notes
```

#### **Option 3: Use Python 3.11 Environment**
```bash
conda create -n tuttibot_py311 python=3.11
conda activate tuttibot_py311
pip install -r requirement_v02_gpu.txt  # Original requirements work with 3.11
```

### 🎯 **CURRENT WORKING FEATURES:**
1. ✅ **GPU Detection & Management** - Working with CPU fallback
2. ✅ **Input Layer** - MusicXML processing successful  
3. ✅ **Block 0 (ScoreGraph)** - Complete score analysis working
4. ⚠️ **Block 1 (AMT)** - Needs alternative implementation
5. ❓ **Block 2 (Alignment)** - Not yet tested
6. ❓ **Output Generation** - Not yet tested

### 📝 **RECOMMENDATIONS:**

**Immediate Fix:** 
Replace basic-pitch with librosa-based AMT to continue testing the pipeline

**Long-term Solution:**
Use Python 3.11 environment for full basic-pitch compatibility

**Next Steps:**
1. Implement librosa AMT fallback in Block 1
2. Test Block 2 (Alignment) 
3. Complete end-to-end pipeline test
4. Document all compatibility requirements
