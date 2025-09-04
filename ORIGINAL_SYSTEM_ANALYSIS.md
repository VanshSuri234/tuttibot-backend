# 🎯 TuttiBot v02 - Original System Analysis & Ideal Dependencies

## 📋 **ORIGINAL SYSTEM CONFIGURATION** (From analysis of provided files)

### **✅ Original Working Environment**
- **Python:** 3.10.12 (Ubuntu 20.04+)
- **System:** Linux CPU mode  
- **Total Packages:** 343 installed
- **Status:** Fully functional pipeline

### **🔑 Key Working Versions (From requirements_frozen.txt)**
```txt
# CORE FOUNDATION (Install First)
numpy==1.26.4                    ✅ CRITICAL VERSION
scipy==1.14.1                    ✅ WORKING

# ML FRAMEWORK (Install Second)  
tensorflow==2.15.0               ✅ TESTED & STABLE
tensorflow-estimator==2.15.0     ✅ MATCHING VERSION
tensorflow-io-gcs-filesystem==0.37.1

# AUDIO PROCESSING (Install Third)
librosa==0.10.2.post1           ✅ AUDIO ANALYSIS
soundfile==0.12.1               ✅ AUDIO I/O  
basic-pitch==0.4.0              ✅ AMT WORKING

# MUSIC PROCESSING
music21==5.7.2                  ⚠️ OUTDATED (but working)
pretty_midi==0.2.10             ✅ MIDI HANDLING

# SCIENTIFIC COMPUTING
pandas==1.5.3                   ⚠️ OUTDATED (but working)
scikit-learn==1.5.0             ✅ ML UTILITIES
matplotlib==3.6.2               ✅ VISUALIZATION

# SYSTEM INTEGRATION
docker==7.1.0                   ✅ CONTAINER SUPPORT
oemer==0.1.8                    ✅ PDF → MusicXML
opencv-python==4.11.0.86        ✅ IMAGE PROCESSING
requests==2.31.0                ✅ HTTP REQUESTS

# UTILITIES
tqdm==4.66.4                    ✅ PROGRESS BARS
PyYAML==6.0.1                   ✅ CONFIG FILES
jupyter==1.0.0                  ✅ DEVELOPMENT
```

---

## 🎯 **RECOMMENDED IDEAL VERSIONS** (Based on Original + Compatibility)

### **Option A: Exact Original Match (100% Compatible)**
```txt
# Use EXACTLY the original working versions
# Python 3.10.12 recommended

# INSTALL ORDER CRITICAL:
numpy==1.26.4
scipy==1.14.1
tensorflow==2.15.0
tensorflow-estimator==2.15.0
tensorflow-io-gcs-filesystem==0.37.1
librosa==0.10.2.post1
soundfile==0.12.1  
basic-pitch==0.4.0
music21==5.7.2
pretty_midi==0.2.10
pandas==1.5.3
scikit-learn==1.5.0
matplotlib==3.6.2
docker==7.1.0
oemer==0.1.8
opencv-python==4.11.0.86
requests==2.31.0
tqdm==4.66.4
PyYAML==6.0.1
```

### **Option B: Updated Ideal (Better but riskier)**
```txt
# Updated versions fixing known issues from DEPENDENCIES_REPORT.md
# Python 3.10.12 or 3.11.x

numpy==1.26.4                    # KEEP SAME (critical)
scipy==1.14.1                    # KEEP SAME
tensorflow==2.15.0               # KEEP SAME (working)
librosa==0.10.2.post1           # KEEP SAME
soundfile==0.12.1               # KEEP SAME
basic-pitch==0.4.0              # KEEP SAME

# UPDATED VERSIONS:
music21==9.1.0                  # Fix: 5.7.2 → 9.1.0 (as reported outdated)
pandas==2.0.3                   # Fix: 1.5.3 → 2.0.3 (as reported outdated)
pretty_midi==0.2.10             # KEEP SAME
scikit-learn==1.5.2             # Minor update
matplotlib==3.8.2               # Updated

# ADD MISSING DEPENDENCIES:
ffmpeg-python==0.2.0            # Missing in original
aubio==0.4.9                    # Missing but listed as needed
pathlib2>=2.3.0                 # Missing (though built-in in Python 3.10)
click>=8.0.0                    # Missing CLI utilities
```

---

## 🚀 **INSTALLATION STRATEGIES**

### **Strategy 1: Safe Clone (Recommended)**
```bash
#!/bin/bash
# Clone exact original environment

# Use Python 3.10.12
python3.10 -m venv tuttibot_original_clone
source tuttibot_original_clone/bin/activate

# Install in EXACT order from setup_tuttibot.sh:
pip install --upgrade pip

# Step 1: Core
pip install numpy==1.26.4 scipy==1.14.1

# Step 2: TensorFlow  
pip install tensorflow==2.15.0 tensorflow-estimator==2.15.0

# Step 3: Audio
pip install librosa==0.10.2.post1 soundfile==0.12.1

# Step 4: AMT
pip install basic-pitch==0.4.0

# Step 5: Music
pip install music21==5.7.2 pretty_midi==0.2.10

# Step 6: Rest
pip install pandas==1.5.3 scikit-learn==1.5.0 matplotlib==3.6.2
pip install docker==7.1.0 oemer==0.1.8 requests==2.31.0
pip install tqdm==4.66.4 PyYAML==6.0.1
pip install opencv-python==4.11.0.86

# Test imports
python -c "import tensorflow as tf, basic_pitch, librosa, music21; print('✅ All core imports working')"
```

### **Strategy 2: Docker Clone (100% Reproducible)**
```bash
# Use the provided Dockerfile exactly
cp Dockerfile.txt Dockerfile
docker build -t tuttibot-original .

# Run with Docker
docker run -v $(pwd):/data tuttibot-original python3 main_v02_fixed.py --pdf /data/Twinkle_pdf.pdf --audio /data/twinkle_full.wav
```

---

## 🎮 **GPU COMPATIBILITY NOTES**

From the original system analysis:
- **Original:** CPU-only mode (no NVIDIA drivers detected)
- **Your System:** Has NVIDIA RTX A4500 GPU

### **GPU Enhancement Strategy**
```bash
# Use original CPU versions but add GPU support:
pip install tensorflow-gpu==2.15.0  # Add GPU variant
# OR use tensorflow[and-cuda]==2.15.0

# Verify GPU detection:
python -c "import tensorflow as tf; print('GPU:', tf.config.list_physical_devices('GPU'))"
```

---

## 📋 **FINAL RECOMMENDATIONS**

### **For Maximum Compatibility (Choose this)**
1. **Use Python 3.10.12** (exact match to original)
2. **Use Strategy 1** (exact version clone) 
3. **Follow exact installation order** from setup_tuttibot.sh
4. **Add GPU support** as enhancement

### **Create This Exact Requirements File**
```txt
# requirements_original_clone.txt
# EXACT WORKING VERSIONS FROM ORIGINAL SYSTEM
# Python 3.10.12 required

numpy==1.26.4
scipy==1.14.1
tensorflow==2.15.0
tensorflow-estimator==2.15.0
librosa==0.10.2.post1
soundfile==0.12.1
basic-pitch==0.4.0
music21==5.7.2
pretty_midi==0.2.10
pandas==1.5.3
scikit-learn==1.5.0
matplotlib==3.6.2
docker==7.1.0
oemer==0.1.8
opencv-python==4.11.0.86
requests==2.31.0
tqdm==4.66.4
PyYAML==6.0.1
jupyter==1.0.0
```

This approach gives you **100% compatibility** with the proven working system!
