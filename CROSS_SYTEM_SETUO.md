# TuttiBot v02 Cross-System Compatibility Guide

**Issue:** Dependency conflicts across different systems, especially Python 3.11+  
**Root Cause:** ML libraries (TensorFlow, NumPy, Basic Pitch) have strict version dependencies that conflict  

## 🐍 Python Version Compatibility Matrix

| Python Version | TensorFlow | Basic Pitch | NumPy | Status |
|----------------|------------|-------------|-------|---------|
| **3.8.x** | 2.4-2.15 | ✅ 0.4.0 | 1.19-1.26 | ✅ **BEST** |
| **3.9.x** | 2.5-2.15 | ✅ 0.4.0 | 1.19-1.26 | ✅ **GOOD** |
| **3.10.x** | 2.8-2.15 | ✅ 0.4.0 | 1.21-1.26 | ✅ **CURRENT** |
| **3.11.x** | 2.12-2.15 | ⚠️ Issues | 1.23-1.26 | ⚠️ **PROBLEMATIC** |
| **3.12.x** | 2.16+ | ❌ Not supported | 1.26+ | ❌ **AVOID** |

## 🔥 Common Conflict Scenarios

### Scenario 1: Python 3.11 System
```bash
# What typically happens:
pip install basic-pitch
# → Installs basic-pitch 0.4.0
# → Requires tensorflow>=2.11,<2.16  
# → Installs tensorflow 2.15
# → But tensorflow 2.15 requires numpy<1.27,>=1.21
# → basic-pitch also needs librosa
# → librosa needs numba
# → numba conflicts with newer numpy
# → DEPENDENCY HELL!
```

### Scenario 2: Existing TensorFlow Installation
```bash
# System has TensorFlow 2.16+ (for other projects)
pip install basic-pitch
# → ERROR: basic-pitch requires tensorflow<2.16
```

## 🛠️ **TESTED SOLUTIONS**

### Solution 1: Conda Environment (RECOMMENDED)
```bash
# Create isolated environment with Python 3.10
conda create -n tuttibot python=3.10
conda activate tuttibot

# Install in specific order
conda install numpy=1.26.4
conda install -c conda-forge librosa
pip install tensorflow==2.15.0
pip install basic-pitch==0.4.0
pip install music21==5.7.2  # Use working version, not latest
pip install oemer docker
```

### Solution 2: Fresh Virtual Environment 
```bash
# Use Python 3.10 if available, otherwise 3.9
python3.10 -m venv tuttibot_env
source tuttibot_env/bin/activate

# Critical: Install in ORDER
pip install --upgrade pip
pip install numpy==1.26.4
pip install tensorflow==2.15.0
pip install basic-pitch==0.4.0
pip install librosa==0.10.2
pip install music21==5.7.2
pip install scipy==1.14.1
pip install scikit-learn==1.5.0
pip install pandas==1.5.3
pip install oemer docker matplotlib
```

### Solution 3: Docker Container (ULTIMATE)
```dockerfile
# Dockerfile.tuttibot
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libsndfile1 \\
    ffmpeg \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements_frozen.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements_frozen.txt

# Copy application
COPY . .

CMD ["python", "main_v02_fixed.py"]
```

## 📋 Frozen Requirements (TESTED WORKING)

Create `requirements_frozen.txt`:
```txt
# FROZEN VERSIONS - TESTED ON PYTHON 3.10.12
# DO NOT CHANGE UNLESS TESTING THOROUGHLY

# Core - INSTALL FIRST
numpy==1.26.4
scipy==1.14.1

# ML Framework - INSTALL SECOND  
tensorflow==2.15.0
tensorflow-estimator==2.15.0

# Audio Processing - INSTALL THIRD
librosa==0.10.2.post1
soundfile==0.12.1
basic-pitch==0.4.0

# Music Processing
music21==5.7.2
pretty_midi==0.2.10

# Scientific
pandas==1.5.3
scikit-learn==1.5.0
matplotlib==3.6.2

# System
docker==7.1.0
oemer==0.1.8
requests==2.31.0

# Optional but recommended
tqdm==4.66.4
PyYAML==6.0.1
```

## 🚨 System-Specific Fixes

### For Python 3.11 Systems:
```bash
# Option A: Force Python 3.10 installation
sudo apt install python3.10 python3.10-venv python3.10-dev
python3.10 -m venv tuttibot_env

# Option B: Use pyenv to manage versions  
curl https://pyenv.run | bash
pyenv install 3.10.12
pyenv virtualenv 3.10.12 tuttibot
pyenv activate tuttibot
```

### For macOS (Apple Silicon):
```bash
# Use conda-forge for better ARM64 support
conda create -n tuttibot python=3.10 -c conda-forge
conda activate tuttibot
conda install -c conda-forge tensorflow numpy librosa
pip install basic-pitch oemer music21
```

### For Windows:
```powershell
# Use Anaconda/Miniconda
conda create -n tuttibot python=3.10
conda activate tuttibot
conda install tensorflow numpy scipy
pip install basic-pitch librosa music21 oemer
```

## 🔍 Debugging Dependency Issues

### Check Current Conflicts:
```bash
pip check  # Shows all conflicts
pip list --outdated  # Shows outdated packages
python -c "import tensorflow; print(tensorflow.__version__)"
python -c "import basic_pitch; print('Basic Pitch OK')"
```

### Force Clean Installation:
```bash
pip freeze > backup_requirements.txt  # Backup first
pip uninstall -y tensorflow tensorflow-estimator basic-pitch librosa numpy
pip cache purge
pip install numpy==1.26.4 tensorflow==2.15.0 basic-pitch==0.4.0
```

## ⚡ Quick System Setup Script

Create `setup_tuttibot.sh`:
```bash
#!/bin/bash
set -e

echo "🔧 Setting up TuttiBot v02 Environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Detected Python $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == "3.11" || "$PYTHON_VERSION" == "3.12" ]]; then
    echo "⚠️  Python $PYTHON_VERSION detected. Recommend using Python 3.10"
    echo "Install Python 3.10 and rerun with: python3.10 setup_tuttibot.sh"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv tuttibot_env
source tuttibot_env/bin/activate

# Upgrade pip
pip install --upgrade pip

echo "📥 Installing dependencies in order..."
pip install numpy==1.26.4
pip install tensorflow==2.15.0  
pip install basic-pitch==0.4.0
pip install librosa==0.10.2.post1
pip install music21==5.7.2
pip install scipy==1.14.1
pip install pandas==1.5.3
pip install oemer docker matplotlib

echo "✅ Setup complete!"
echo "Activate with: source tuttibot_env/bin/activate"
```

## 💡 Prevention Strategy
1. **Always use virtual environments**
2. **Pin exact versions in production**
3. **Test on target Python version first**
4. **Use Docker for ultimate consistency**
5. **Keep a working requirements freeze**

This guide should solve the cross-system dependency issues you're experiencing!
