# 🚀 TuttiBot v02 - Command Reference Guide

## 📋 **Quick Reference**

This document provides all the essential commands to run TuttiBot v02 with both CPU and GPU acceleration.

---

## 🔧 **Setup Commands**

### **Environment Activation**
```bash
# Activate the Python 3.10.12 environment
source tuttibot_py310_env/bin/activate

# Navigate to workspace
cd /path/to/TuttiBot/Workspace
```

### **GPU Setup (One-time)**
```bash
# Install GPU libraries for TensorFlow 2.15.0
pip install "nvidia-cudnn-cu11==8.9.4.25"
pip install "nvidia-cuda-runtime-cu11"  
pip install "nvidia-cublas-cu11"

# Verify GPU detection
python -c "import tensorflow as tf; print('GPUs:', tf.config.list_physical_devices('GPU'))"
```

---

## 🖥️ **CPU Mode Commands**

### **Basic PDF + Audio Processing**
```bash
# Standard PDF to audio alignment (CPU only)
python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav --cpu-only

# With custom output directory
python main_v02_fixed.py --pdf score.pdf --audio audio.wav --output ./my_results --cpu-only
```

### **MusicXML + Audio Processing**
```bash
# MusicXML file instead of PDF
python main_v02_fixed.py --musicxml score.musicxml --audio audio.wav --cpu-only

# Multiple processing with CPU
python main_v02_fixed.py --musicxml composition.xml --audio performance.wav --cpu-only
```

### **MIDI + Audio Processing**
```bash
# MIDI file as score input
python main_v02_fixed.py --midi score.mid --audio audio.wav --cpu-only
```

---

## � **Complete Pipeline (main.py) - Multi-Layer Analysis**

### **Full Pipeline Processing**
```bash
# Complete audio-score analysis (3-layer pipeline)
python main.py audio.wav score.pdf

# With different formats
python main.py recording.mp3 sheet_music.musicxml
python main.py performance.wav composition.mid

# Help and format information
python main.py --help
```

### **Supported Input Formats**
```bash
# Audio formats: WAV, MP3, FLAC, AAC, OGG
python main.py song.mp3 score.pdf
python main.py concert.flac composition.xml

# Score formats: PDF, MusicXML, MIDI
python main.py audio.wav score.pdf          # PDF via Audiveris
python main.py audio.wav score.musicxml     # MusicXML direct
python main.py audio.wav composition.mid    # MIDI direct
```

### **Pipeline Output Structure**
```bash
# Output directory: tuttibot_output_YYYYMMDD_HHMMSS/
# ├── 01_input_layer/      # Standardized inputs
# ├── 02_processing_layer/ # Audio cleaning & analysis
# ├── 03_extraction_layer/ # Advanced feature extraction
# └── 04_final_results/    # Key outputs for analysis
```

---

## �🎮 **GPU Mode Commands (Recommended)**

### **Auto-GPU Detection**
```bash
# Let TuttiBot auto-detect and use best GPU
python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav

# MusicXML with auto-GPU
python main_v02_fixed.py --musicxml score.musicxml --audio audio.wav

# MIDI with auto-GPU  
python main_v02_fixed.py --midi score.mid --audio audio.wav
```

### **Specific GPU Selection**
```bash
# Use GPU 0 specifically
python main_v02_fixed.py --pdf score.pdf --audio audio.wav --gpu-id 0

# Use GPU 1 (multi-GPU systems)
python main_v02_fixed.py --pdf score.pdf --audio audio.wav --gpu-id 1

# Custom output with specific GPU
python main_v02_fixed.py --pdf score.pdf --audio audio.wav --gpu-id 0 --output ./gpu_results
```

---

## 📊 **Diagnostic Commands**

### **System Status**
```bash
# Check GPU availability
nvidia-smi

# Check Python environment
python --version
which python
```

### **TuttiBot Health Check**
```bash
# Test critical imports
python -c "
import sys
print(f'Python: {sys.version}')
import numpy as np
print(f'NumPy: {np.__version__}')
import tensorflow as tf
print(f'TensorFlow: {tf.__version__}')
print(f'GPU Available: {len(tf.config.list_physical_devices(\"GPU\"))} GPUs')
import librosa
print(f'Librosa: {librosa.__version__}')
import basic_pitch
print('Basic Pitch: OK')
print('✅ All systems ready!')
"
```

### **GPU Detection Test**
```bash
# Test GPU manager
python -c "
from gpu_manager import GPUManager
gpu = GPUManager()
print('GPU Info:', gpu.gpu_info['gpu_count'], 'GPUs detected')
print('Device Config:', gpu.device_config['use_gpu'])
if gpu.device_config['use_gpu']:
    print('✅ GPU Ready!')
else:
    print('❌ GPU Not Available')
"
```

### **Basic Pitch GPU Test**
```bash
# Test Basic Pitch with GPU
mkdir -p /tmp/bp_test
basic-pitch /tmp/bp_test --save-midi --save-note-events twinkle_full.wav

# Check for GPU usage in output
# Should show: "Created device /job:localhost/replica:0/task:0/device:GPU:0"
```

---

## 🎯 **Performance Comparison Commands**

### **CPU vs GPU Benchmark**
```bash
# Run same file with CPU
time python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav --cpu-only

# Run same file with GPU  
time python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav --gpu-id 0

# Compare execution times
```

### **Memory Usage Monitoring**
```bash
# Monitor GPU memory during processing
watch -n 1 nvidia-smi

# Monitor system memory
htop
```

---

## 🔍 **Troubleshooting Commands**

### **Fix GPU Detection Issues**
```bash
# Reinstall GPU libraries
pip install "nvidia-cudnn-cu11==8.9.4.25" --force-reinstall
pip install "nvidia-cuda-runtime-cu11" --force-reinstall

# Test TensorFlow GPU
python -c "
import tensorflow as tf
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print(f'✅ {len(gpus)} GPU(s) detected')
    for i, gpu in enumerate(gpus):
        print(f'  GPU {i}: {gpu}')
else:
    print('❌ No GPUs detected by TensorFlow')
"
```

### **Fix NumPy Issues**
```bash
# Force correct NumPy version
pip install "numpy==1.26.4" --force-reinstall

# Verify NumPy version
python -c "import numpy; print('NumPy:', numpy.__version__)"
```

### **Clean Environment Reset**
```bash
# Deactivate and recreate environment
deactivate
rm -rf tuttibot_py310_env

# Recreate from scratch
python -m venv tuttibot_py310_env
source tuttibot_py310_env/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install "numpy==1.26.4"
# ... continue with installation steps
```

---

## 📁 **File Organization Commands**

### **Check Results**
```bash
# List output directories
ls -la ./Output/

# Check latest results
ls -la ./Output/tuttibotv02_output_*/

# View summary report
cat ./Output/tuttibotv02_output_*/final_output/summary_report.txt
```

### **Clean Old Results**
```bash
# Remove results older than 7 days
find ./Output/ -type d -name "tuttibotv02_output_*" -mtime +7 -exec rm -rf {} +

# Keep only latest 5 results
ls -1t ./Output/tuttibotv02_output_* | tail -n +6 | xargs rm -rf
```

---

## ⚡ **Quick Start Cheat Sheet**

### **Most Common Commands**

#### **CPU Mode (Slower but Compatible)**
```bash
source tuttibot_py310_env/bin/activate
python main_v02_fixed.py --pdf score.pdf --audio audio.wav --cpu-only
```

#### **GPU Mode (Faster, Recommended)**
```bash
source tuttibot_py310_env/bin/activate  
python main_v02_fixed.py --pdf score.pdf --audio audio.wav --gpu-id 0
```

#### **Health Check**
```bash
nvidia-smi && python -c "import tensorflow as tf; print('GPUs:', len(tf.config.list_physical_devices('GPU')))"
```

---

## 🎵 **Example Workflows**

### **Research Paper Processing**
```bash
# Process multiple files with GPU acceleration
for pdf in papers/*.pdf; do
  audio="${pdf%.pdf}.wav"
  if [ -f "$audio" ]; then
    echo "Processing: $pdf + $audio"
    python main_v02_fixed.py --pdf "$pdf" --audio "$audio" --gpu-id 0 --output "./results/$(basename ${pdf%.pdf})"
  fi
done
```

### **Batch Processing with Error Handling**
```bash
#!/bin/bash
# Process files with fallback to CPU if GPU fails
for pdf in *.pdf; do
  audio="${pdf%.pdf}.wav"
  if [ -f "$audio" ]; then
    echo "Attempting GPU processing: $pdf"
    if ! python main_v02_fixed.py --pdf "$pdf" --audio "$audio" --gpu-id 0; then
      echo "GPU failed, falling back to CPU"
      python main_v02_fixed.py --pdf "$pdf" --audio "$audio" --cpu-only
    fi
  fi
done
```

---

*Last Updated: September 4, 2025*  
*TuttiBot v02 Command Reference*  
*For technical support, see DEPENDENCY_PROBLEMS_AND_SOLUTIONS.md*
