# 🚀 TuttiBot v02 - Complete Setup & Deployment Guide

## 📋 **Quick Start Summary**

**Python Version Required:** `3.10.12` (CRITICAL - do not use newer versions)  
**Environment:** Virtual environment with exact dependency versions  
**Requirements File:** `requirements_original_clone.txt`  
**Setup Time:** ~15-20 minutes  
**Status:** ✅ Tested and verified working

---

## 🎯 **Prerequisites**

### **System Requirements**
- **Operating System:** Linux (tested on Ubuntu)
- **Python:** 3.10.12 (exact version required)
- **Memory:** Minimum 4GB, Recommended 8GB+
- **Disk Space:** ~5GB for dependencies
- **Internet:** Required for package downloads

### **Required System Packages**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    python3.10-dev \
    python3.10-venv \
    build-essential \
    libsndfile1-dev \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0
```

### **Optional: Docker (for PDF conversion)**
```bash
# Install Docker (optional but recommended)
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER
# Log out and back in for docker group to take effect

# Pull Audiveris image for PDF processing
docker pull toprock/audiveris
```

---

## ⚙️ **Step-by-Step Installation**

### **Step 1: Python Version Management**

#### **Option A: Using pyenv (Recommended)**
```bash
# Install pyenv if not already installed
curl https://pyenv.run | bash

# Add to shell profile
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
source ~/.bashrc

# Install Python 3.10.12
pyenv install 3.10.12
pyenv local 3.10.12

# Verify version
python --version  # Should show: Python 3.10.12
```

#### **Option B: System Python (if 3.10.12 available)**
```bash
# Check if system has Python 3.10.12
python3.10 --version

# If available, use directly:
python3.10 -m venv tuttibot_py310_env
```

#### **Option C: Compile from Source (Last Resort)**
```bash
# Download and compile Python 3.10.12
wget https://www.python.org/ftp/python/3.10.12/Python-3.10.12.tar.xz
tar -xf Python-3.10.12.tar.xz
cd Python-3.10.12
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall
```

### **Step 2: Virtual Environment Creation**
```bash
# Create virtual environment with Python 3.10.12
python -m venv tuttibot_py310_env

# Activate environment
source tuttibot_py310_env/bin/activate

# Verify environment
python --version  # Must be 3.10.12
pip --version     # Should show path to venv
```

### **Step 3: Critical Dependencies Installation**

⚠️ **CRITICAL:** Install in this EXACT order to prevent conflicts

```bash
# Step 1: Upgrade pip first
pip install --upgrade pip

# Step 2: Lock NumPy to prevent TensorFlow conflicts
pip install "numpy==1.26.4"

# Step 3: Install core scientific computing
pip install "scipy==1.14.1"

# Step 4: Install TensorFlow ecosystem (exact versions)
pip install "tensorflow==2.15.0"
pip install "tensorflow-estimator==2.15.0"
pip install "tensorflow-io-gcs-filesystem==0.37.1"

# Step 5: Audio processing libraries
pip install "librosa==0.10.2.post1"
pip install "soundfile==0.12.1"

# Step 6: Music AI model
pip install "basic-pitch==0.4.0"

# Step 7: Music processing
pip install "music21==5.7.2"
pip install "pretty_midi==0.2.10"

# Step 8: Data science
pip install "pandas==1.5.3"
pip install "scikit-learn==1.5.0" 
pip install "matplotlib==3.6.2"

# Step 9: System integration
pip install "docker==7.1.0"
pip install "oemer==0.1.8"
pip install "opencv-python==4.11.0.86"
pip install "requests==2.31.0"
pip install "tqdm==4.66.4"
pip install "PyYAML==6.0.1"
pip install "jupyter==1.0.0"

# Step 10: PDF conversion support
pip install "pdf2image==1.17.0"
```

### **Step 4: Post-Installation Fixes**

⚠️ **IMPORTANT:** Some packages may force NumPy upgrades. Fix this:

```bash
# Force NumPy back to compatible version
pip install "numpy==1.26.4" --force-reinstall

# Ignore these warnings (they're non-critical):
# - opencv-python-headless numpy compatibility warning
# - Basic Pitch CoreML/TensorFlow warnings
```

### **Step 5: Installation Verification**
```bash
# Critical import test
python -c "
import sys
print(f'Python: {sys.version}')

import numpy as np
print(f'NumPy: {np.__version__}')

import tensorflow as tf
print(f'TensorFlow: {tf.__version__}')

import librosa
print(f'Librosa: {librosa.__version__}')

import basic_pitch
print('Basic Pitch: OK')

import music21
print(f'Music21: {music21.__version__}')

print('✅ All critical imports successful!')
"
```

**Expected Output:**
```
Python: 3.10.12 (main, Sep  4 2025, 17:55:49) [GCC 11.5.0]
NumPy: 1.26.4
TensorFlow: 2.15.0
Librosa: 0.10.2.post1
Basic Pitch: OK
Music21: 5.7.2
✅ All critical imports successful!
```

---

## 🏃‍♂️ **Alternative: Automated Installation**

### **Using the Deployment Script**
```bash
# Clone/download the project
cd /path/to/TuttiBot/Workspace

# Make script executable
chmod +x deploy_python310.sh

# Run automated deployment
./deploy_python310.sh

# Follow the prompts and wait for completion
```

### **Using Requirements File**
```bash
# Option 1: Install all at once (may have conflicts)
pip install -r requirements_original_clone.txt

# Option 2: Install in order (recommended)
cat requirements_original_clone.txt | xargs -n 1 pip install

# Option 3: Force exact versions
pip install -r requirements_original_clone.txt --force-reinstall
```

---

## � **GPU Setup & Acceleration (Optional but Recommended)**

⚠️ **IMPORTANT:** For systems with NVIDIA GPUs, follow these steps to enable GPU acceleration:

### **Step 1: Verify GPU Availability**
```bash
# Check if NVIDIA GPU is available
nvidia-smi

# Should show your GPU details (e.g., RTX A4500, RTX 3080, etc.)
```

### **Step 2: Install GPU-Specific CUDA Libraries**
After completing the main installation, install these GPU libraries:

```bash
# Install cuDNN compatible with TensorFlow 2.15.0
pip install "nvidia-cudnn-cu11==8.9.4.25"

# Install CUDA runtime libraries
pip install "nvidia-cuda-runtime-cu11"

# Install additional CUDA libraries
pip install "nvidia-cublas-cu11"
```

### **Step 3: Verify GPU Detection**
```bash
# Test TensorFlow GPU detection
python -c "
import tensorflow as tf
print('GPU Available:', tf.config.list_physical_devices('GPU'))
print('GPU Count:', len(tf.config.list_physical_devices('GPU')))
if tf.config.list_physical_devices('GPU'):
    print('✅ GPU Ready for TuttiBot!')
else:
    print('❌ GPU not detected, will use CPU')
"
```

### **Step 4: Test Basic Pitch GPU**
```bash
# Test Basic Pitch with GPU
mkdir -p /tmp/gpu_test
basic-pitch /tmp/gpu_test --save-midi --save-note-events twinkle_full.wav

# Should show: "Created device /job:localhost/replica:0/task:0/device:GPU:0"
```

---

## �🎵 **Running TuttiBot v02**

### **Basic Usage (CPU Mode)**
```bash
# Activate environment
source tuttibot_py310_env/bin/activate

# Navigate to project directory
cd /path/to/TuttiBot/Workspace

# Run pipeline with CPU only
python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav --cpu-only

# Or with MusicXML file
python main_v02_fixed.py --musicxml score.musicxml --audio audio.wav --cpu-only
```

### **GPU Accelerated Usage (Recommended)**
```bash
# Activate environment
source tuttibot_py310_env/bin/activate

# Navigate to project directory
cd /path/to/TuttiBot/Workspace

# Run with GPU acceleration (auto-detect best GPU)
python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav

# Run with specific GPU ID (for multi-GPU systems)
python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav --gpu-id 0
```

### **Command Line Options**
```bash
# Full parameter list
python main_v02_fixed.py \
    --pdf input_score.pdf \          # PDF score file
    --audio input_audio.wav \        # Audio file
    --output ./custom_output \       # Output directory (optional)
    --device cpu \                   # Force CPU mode (optional)
    --verbose                        # Verbose logging (optional)
```

### **Expected Pipeline Stages**
1. **Input Layer**: PDF → MusicXML conversion
2. **Processing Layer**: Audio analysis and score parsing
3. **Temporal Alignment**: DTW-based synchronization
4. **Output Generation**: Results and visualizations

### **Success Indicators**
- Processing completes without errors
- Alignment confidence > 0.8 (80%)
- Output files generated in results directory
- Summary report shows "Status: SUCCESS"

---

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

#### **Issue 1: NumPy Compatibility Error**
```
AttributeError: _ARRAY_API not found
```
**Solution:**
```bash
pip install "numpy==1.26.4" --force-reinstall
```

#### **Issue 2: TensorFlow Import Error**
```
ModuleNotFoundError: No module named 'tensorflow'
```
**Solution:**
```bash
# Reinstall TensorFlow with exact version
pip uninstall tensorflow
pip install "tensorflow==2.15.0"
```

#### **Issue 3: PDF Conversion Fails**
```
pdf2image not available
```
**Solution:**
```bash
pip install pdf2image
# Also install system dependency:
sudo apt-get install poppler-utils
```

#### **Issue 4: Basic Pitch Warnings**
```
WARNING: Tensorflow is not installed
WARNING: Coremltools is not installed
```
**Solution:** These are non-critical warnings. Basic Pitch will work with TFLite runtime.

#### **Issue 5: Python Version Wrong**
```
Current Python: 3.12.7
```
**Solution:**
```bash
# Use pyenv to switch
pyenv local 3.10.12
# Recreate virtual environment
rm -rf tuttibot_py310_env
python -m venv tuttibot_py310_env
```

### **GPU-Specific Issues & Solutions**

#### **Issue 6: GPU Not Detected by TensorFlow**
```
GPU Available: []
Cannot dlopen some GPU libraries
```
**Problem:** TensorFlow cannot load GPU libraries.
**Solution:**
```bash
# Install compatible CUDA libraries
pip install "nvidia-cudnn-cu11==8.9.4.25"
pip install "nvidia-cuda-runtime-cu11"
pip install "nvidia-cublas-cu11"

# Verify GPU detection
python -c "import tensorflow as tf; print('GPU:', tf.config.list_physical_devices('GPU'))"
```

#### **Issue 7: cuDNN Version Mismatch**
```
Loaded runtime CuDNN library: 8.6.0 but source was compiled with: 8.9.4
DNN library is not found
```
**Problem:** cuDNN version incompatibility.
**Solution:**
```bash
# Install exact cuDNN version
pip install "nvidia-cudnn-cu11==8.9.4.25" --force-reinstall

# Test Basic Pitch
basic-pitch /tmp/test --save-midi test_audio.wav
```

#### **Issue 8: Pipeline Using CPU Instead of GPU**
```
🎮 GPU STATUS: ⚠️ No GPU detected, switching to CPU
Processing Mode: CPU
```
**Problem:** GPU detection failed or CUDA libraries missing.
**Solution:**
```bash
# 1. Check GPU availability
nvidia-smi

# 2. Install GPU libraries
pip install "nvidia-cudnn-cu11==8.9.4.25"
pip install "nvidia-cuda-runtime-cu11"

# 3. Run with explicit GPU flag
python main_v02_fixed.py --pdf score.pdf --audio audio.wav --gpu-id 0
```

#### **Issue 9: GPU Memory Errors**
```
CUDA out of memory
ResourceExhaustedError
```
**Solution:**
```bash
# Force CPU mode for large files
python main_v02_fixed.py --pdf score.pdf --audio audio.wav --cpu-only

# Or use specific GPU with sufficient memory
python main_v02_fixed.py --pdf score.pdf --audio audio.wav --gpu-id 1
```

### **Diagnostic Commands**
```bash
# Check environment
which python
python --version
pip list | grep -E "(numpy|tensorflow|basic-pitch)"

# Test critical imports individually
python -c "import numpy; print(numpy.__version__)"
python -c "import tensorflow; print(tensorflow.__version__)"
python -c "import basic_pitch"

# GPU-specific diagnostics
nvidia-smi  # Check GPU availability
python -c "
import tensorflow as tf
print('GPU Available:', tf.config.list_physical_devices('GPU'))
print('CUDA Built:', tf.test.is_built_with_cuda())
"

# Test GPU manager
python -c "
from gpu_manager import GPUManager
gpu = GPUManager()
print('GPU Info:', gpu.gpu_info)
print('Device Config:', gpu.device_config)
"
```

---

## 📊 **Version Compatibility Matrix**

### **Tested Working Combinations**
| Component | Version | Status | Notes |
|-----------|---------|---------|-------|
| Python | 3.10.12 | ✅ Required | Exact version needed |
| NumPy | 1.26.4 | ✅ Critical | Must be locked |
| TensorFlow | 2.15.0 | ✅ Required | For Basic Pitch |
| Basic Pitch | 0.4.0 | ✅ Working | With warnings (OK) |
| Librosa | 0.10.2.post1 | ✅ Stable | Audio processing |
| Music21 | 5.7.2 | ✅ Working | Score processing |

### **GPU Compatibility Matrix**
| Component | Version | Status | Notes |
|-----------|---------|---------|-------|
| CUDA Driver | 12.4 | ✅ Working | System level |
| cuDNN | 8.9.4.25 | ✅ Required | Exact version for TF 2.15.0 |
| nvidia-cublas-cu11 | Latest | ✅ Working | CUDA math library |
| nvidia-cuda-runtime-cu11 | Latest | ✅ Working | CUDA runtime |
| TensorFlow GPU | 2.15.0 | ✅ Working | With correct cuDNN |
| Basic Pitch GPU | 0.4.0 | ✅ Working | GPU acceleration enabled |

### **Tested GPU Hardware**
| GPU Model | Memory | Status | Performance |
|-----------|---------|---------|-------------|
| NVIDIA RTX A4500 | 20GB | ✅ Excellent | ~3x faster than CPU |
| NVIDIA RTX 3080 | 10GB | ✅ Very Good | ~2.5x faster than CPU |
| NVIDIA RTX 4090 | 24GB | ✅ Excellent | ~4x faster than CPU |

### **Known Incompatible Combinations**
| Python | NumPy | TensorFlow | Status | Issue |
|--------|-------|------------|---------|-------|
| 3.12.x | 2.x.x | 2.15.0 | ❌ Broken | NumPy 2.x breaks TF |
| 3.12.x | 1.26.4 | 2.20.0 | ❌ Blocked | Python 3.12 needs TF>=2.16 |
| 3.11.x | 2.x.x | 2.15.0 | ❌ Broken | Same NumPy issue |

---

## 🐳 **Docker Alternative (Advanced)**

### **Dockerfile Approach**
```dockerfile
# Use provided Dockerfile
FROM python:3.10.12-slim

# Copy requirements
COPY requirements_original_clone.txt /app/

# Install dependencies in order
RUN pip install -r requirements_original_clone.txt

# Copy application
COPY . /app/
WORKDIR /app

# Run pipeline
CMD ["python", "main_v02_fixed.py", "--pdf", "Twinkle_pdf.pdf", "--audio", "twinkle_full.wav"]
```

### **Docker Usage**
```bash
# Build image
docker build -t tuttibot-v02 .

# Run pipeline
docker run -v $(pwd):/data tuttibot-v02 \
    python main_v02_fixed.py --pdf /data/score.pdf --audio /data/audio.wav
```

---

## 📁 **Directory Structure**

### **Project Layout**
```
TuttiBot/Workspace/
├── main_v02_fixed.py                    # Main pipeline script
├── requirements_original_clone.txt      # Exact dependencies
├── deploy_python310.sh                 # Auto setup script
├── Twinkle_pdf.pdf                     # Example score
├── twinkle_full.wav                    # Example audio
├── tuttibot_py310_env/                 # Virtual environment
├── Output/                             # Results directory
│   └── tuttibotv02_output_YYYYMMDD_HHMMSS/
│       ├── final_output/
│       │   ├── summary_report.txt      # Results summary
│       │   ├── alignment_visualization.png
│       │   └── temporal_alignment.csv
│       └── intermediate/               # Processing files
└── INPUT_LAYER/                        # Input processing modules
    ├── input_layer.py
    └── requirements_input.txt
```

---

## ✅ **Final Checklist**

### **Pre-Installation**
- [ ] Linux system with required packages
- [ ] Python 3.10.12 available (via pyenv/system/source)
- [ ] Virtual environment tools installed
- [ ] Internet connection for downloads

### **Installation Process**
- [ ] Virtual environment created with Python 3.10.12
- [ ] Dependencies installed in correct order
- [ ] NumPy locked to version 1.26.4
- [ ] Critical imports tested successfully
- [ ] PDF conversion tools installed

### **Verification**
- [ ] All import tests pass
- [ ] Pipeline runs without errors
- [ ] Output files generated correctly
- [ ] Alignment confidence > 80%

### **Production Ready**
- [ ] Environment documented and backed up
- [ ] Requirements file matches installation
- [ ] Deployment script tested
- [ ] Troubleshooting procedures documented

---

## 🎯 **Performance Expectations**

### **Processing Time**
- **PDF Conversion**: 30-60 seconds
- **Audio Analysis**: 1-2 minutes
- **Temporal Alignment**: 30-60 seconds
- **Total Pipeline**: 2-4 minutes

### **Resource Usage**
- **Memory**: 2-4GB during processing
- **CPU**: High utilization during ML inference
- **Disk**: ~100MB per processing session
- **GPU**: Optional, can accelerate TensorFlow operations

### **Quality Metrics**
- **Alignment Confidence**: Target >85%
- **DTW Distance**: Lower is better
- **Note Detection**: Depends on audio quality
- **Success Rate**: >95% with proper setup

---

*Last Updated: September 4, 2025*  
*TuttiBot v02 - Complete Deployment Guide*  
*Tested and Verified Working Configuration*
