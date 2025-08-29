# TuttiBot v02 - GPU-Ready Quick Start Guide 🚀

This guide provides step-by-step instructions to run TuttiBot v02 with GPU acceleration on both local systems and remote servers.

## 📋 Pre-Flight Checklist

### Step 1: Check GPU Availability
Before installing anything, verify GPU access:

```bash
# Check if NVIDIA drivers are installed
nvidia-smi

# Expected output: GPU information table
# If command not found: No GPU drivers installed
```

### Step 2: Check Python Environment
```bash
# Verify Python version (3.8+ required)
python3 --version

# Check pip
pip3 --version
```

### Step 3: Navigate to TuttiBot Directory
```bash
cd /path/to/your/TuttiBot/Workspace
ls -la  # Should see gpu_manager.py, main_v02_fixed.py, etc.
```

## 🏠 Local System Installation

### Quick Setup (Recommended)
```bash
# 1. Create virtual environment
python3 -m venv tuttibotv02_env
source tuttibotv02_env/bin/activate

# 2. Install dependencies (in order to avoid conflicts)
pip install numpy==1.23.5
pip install tensorflow==2.14.0
pip install torch torchvision torchaudio
pip install basic-pitch==0.2.5
pip install -r requirement_v02.txt

# 3. Test GPU detection
python gpu_manager.py
```

### Manual Dependency Resolution (if conflicts occur)
```bash
# Install core packages first
pip install numpy==1.23.5 scipy pandas

# Install TensorFlow with specific version
pip install tensorflow==2.14.0

# Install PyTorch (adjust CUDA version as needed)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install Basic Pitch (compatible version)
pip install basic-pitch==0.2.5

# Install remaining packages
pip install librosa soundfile music21 pretty_midi matplotlib psutil tqdm
```

## 🖥️ Remote Server Setup

### Step 1: Connect to Server
```bash
ssh username@your-server.com
```

### Step 2: Check System Environment
```bash
# Check if you're on a GPU-enabled server
nvidia-smi

# Check available Python versions
python3 --version
which python3

# Check if conda/modules are available
which conda || echo "Conda not available"
which module || echo "Module system not available"
```

### Step 3: Load Required Software (if using module system)
```bash
# Check available modules (if module system exists)
module avail | grep -i python
module avail | grep -i cuda

# Load modules (adjust based on available versions)
module load python/3.9.0  # or similar
module load cuda/11.8     # or similar
```

### Step 4: Navigate to Workspace
```bash
cd ~/Workspace  # or your workspace path
```

### Step 5: Setup Python Environment
```bash
# Option A: Using conda (if available)
conda create -n tuttibotv02 python=3.9
conda activate tuttibotv02

# Option B: Using pip virtual environment
python3 -m venv tuttibotv02_env
source tuttibotv02_env/bin/activate
```

### Step 6: Install Dependencies
```bash
# Install in specific order for server compatibility
pip install --upgrade pip
pip install numpy==1.23.5
pip install tensorflow==2.14.0
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install basic-pitch==0.2.5
pip install psutil librosa soundfile music21 pretty_midi matplotlib tqdm scipy pandas
```

### Step 7: Test GPU Access
```bash
# Navigate to workspace and test
cd ~/Workspace
python gpu_manager.py  # Should show GPU detected if available
```

## 🧪 Testing GPU Functionality

### Test 1: Basic GPU Detection
```bash
python gpu_manager.py
```
**Expected Output:**
```
🖥️  TuttiBot v02 - System & GPU Status
======================================================================
📍 ENVIRONMENT:
   � Running on local system (or 🖥️  Running on server)
   
🎮 GPU STATUS:
   ✅ GPU acceleration enabled
   🎯 Using GPU 0
   GPU 0: NVIDIA GeForce RTX 2080 Ti (8000/11264 MB free) 🎯 [SELECTED]

📚 LIBRARIES:
   TensorFlow: ✅ Available
   PyTorch: ✅ Available
```

### Test 2: Run Integration Tests
```bash
python test_gpu_integration.py --quick
```

### Test 3: Test Pipeline with Sample Data
```bash
# Basic run (auto GPU detection)
python main_v02_fixed.py --pdf INPUT_LAYER/score.pdf --audio INPUT_LAYER/audio.wav

# Force CPU mode (for comparison)
python main_v02_fixed.py --pdf INPUT_LAYER/score.pdf --audio INPUT_LAYER/audio.wav --cpu-only

# Use specific GPU
python main_v02_fixed.py --pdf INPUT_LAYER/score.pdf --audio INPUT_LAYER/audio.wav --gpu-id 0
```

## 🐛 Troubleshooting Common Issues

### Issue 1: "No module named 'psutil'"
```bash
pip install psutil
```

### Issue 2: "tensorflow version conflicts"
```bash
# Uninstall and reinstall with specific versions
pip uninstall tensorflow basic-pitch
pip install tensorflow==2.14.0
pip install basic-pitch==0.2.5
```

### Issue 3: "CUDA out of memory"
```bash
# Check GPU memory
nvidia-smi

# Run with CPU fallback
python main_v02_fixed.py --cpu-only --pdf score.pdf --audio audio.wav
```

### Issue 4: "nvidia-smi not found" on Server
```bash
# Check if you're on a GPU-enabled server
echo "Current server: $(hostname)"

# Check if NVIDIA drivers are installed
which nvidia-smi || echo "NVIDIA drivers not installed"

# Contact system administrator if no GPU access
```

### Issue 5: Package conflicts during installation
```bash
# Create fresh environment
rm -rf tuttibotv02_env
python3 -m venv tuttibotv02_env
source tuttibotv02_env/bin/activate

# Install packages individually in order
pip install numpy==1.23.5
pip install tensorflow==2.14.0
pip install basic-pitch==0.2.5
# ... continue with remaining packages
```

## 🚀 Running the Full Pipeline

### Basic Usage
```bash
# Activate environment
source tuttibotv02_env/bin/activate  # or conda activate tuttibotv02

# Run pipeline with auto GPU detection
python main_v02_fixed.py \
    --pdf INPUT_LAYER/score.pdf \
    --audio INPUT_LAYER/audio.wav \
    --output ./Output
```

### Advanced Options
```bash
# Use specific GPU (multi-GPU systems)
python main_v02_fixed.py \
    --pdf score.pdf \
    --audio audio.wav \
    --gpu-id 1

# Force CPU mode
python main_v02_fixed.py \
    --pdf score.pdf \
    --audio audio.wav \
    --cpu-only

# Custom output directory
python main_v02_fixed.py \
    --pdf score.pdf \
    --audio audio.wav \
    --output /path/to/custom/output
```

## 📊 Performance Expectations

| Component | CPU Time | GPU Time | Speedup |
|-----------|----------|----------|---------|
| PDF→XML | ~5s | ~5s | 1x (no GPU) |
| ScoreGraph | ~10s | ~10s | 1x (no GPU) |
| AMT (Basic Pitch) | ~120s | ~30s | 4x |
| Feature Extract | ~45s | ~15s | 3x |
| Alignment | ~30s | ~20s | 1.5x |
| **Total** | **~210s** | **~80s** | **~2.6x** |

*Performance on RTX 2080 Ti with 3-minute audio file*

## 📁 File Structure Check

Make sure your workspace has these files:
```
Workspace/
├── gpu_manager.py                    ✅ GPU detection & management
├── main_v02_fixed.py                 ✅ Main pipeline (GPU-ready)
├── requirement_v02.txt               ✅ Dependencies
├── test_gpu_integration.py           ✅ Testing suite
├── install_gpu.sh                    ✅ Auto installer
├── INPUT_LAYER/
│   ├── score.pdf                     📄 Your input score
│   └── audio.wav                     🎵 Your input audio
└── Temporal Alignment/               📁 Processing blocks
    ├── Block_0_ScoreGraph/
    ├── Block_1_AMT/
    └── Block_2_SymbolicAlignment/
```

## 🆘 Quick Help Commands

```bash
# Check GPU status
python gpu_manager.py

# Test specific GPU
python gpu_manager.py --gpu-id 0

# Run integration tests
python test_gpu_integration.py

# Check pipeline help
python main_v02_fixed.py --help

# Monitor GPU during processing
watch -n 1 nvidia-smi
```

## 📞 Support

If you encounter issues:
1. ✅ Check this guide first
2. 🧪 Run `python test_gpu_integration.py` for diagnostics
3. 📊 Check `python gpu_manager.py` output
4. 📋 Share the exact error message and system info

---

**Happy Processing!** 🎼✨ Your TuttiBot v02 is now GPU-ready for high-performance temporal alignment!
