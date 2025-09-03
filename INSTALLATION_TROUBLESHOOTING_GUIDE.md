# TuttiBot v02 GPU Requirements Installation Guide

## Problems Identified with `requirement_v02_gpu.txt`

### 1. **Python 3.13 Compatibility Issues**
**Problem:** You're using Python 3.13.5, which is very new and has limited support for some ML libraries.

**Specific Issues Found:**
- `audioread>=2.1.0` fails due to missing `imp` module in Python 3.13
- `basic-pitch>=0.4.0` requires `tensorflow<2.15.1` but Python 3.13 only supports `tensorflow>=2.20.0`
- Version conflicts between TensorFlow and basic-pitch

### 2. **Package Version Conflicts**
**Error Details:**
```
ERROR: Cannot install basic-pitch 0.4.0 and tensorflow>=2.8.0 because these package versions have conflicting dependencies.
The conflict is caused by:
    basic-pitch 0.4.0 depends on tensorflow<2.15.1 and >=2.4.1
    But only tensorflow>=2.20.0 is available for Python 3.13
```

### 3. **Unnecessary Dependencies**
**Problem:** `pathlib` and `argparse` are built into Python 3.4+ and don't need separate installation.

## Solutions Implemented

### ✅ Fixed Requirements File: `requirement_v02_gpu_fixed.txt`

**Key Changes:**
1. **Fixed audioread:** `audioread==3.0.1` (compatible with Python 3.13)
2. **Removed basic-pitch temporarily** due to TensorFlow conflicts
3. **Updated TensorFlow:** `tensorflow>=2.20.0` (only version supporting Python 3.13)
4. **Removed built-in modules:** `pathlib` and `argparse`
5. **Added setuptools:** `setuptools>=65.0.0` for compatibility

### Alternative AMT Solutions (since basic-pitch conflicts):

1. **Option 1: Use librosa for onset detection**
   ```python
   import librosa
   y, sr = librosa.load('audio.wav')
   onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
   ```

2. **Option 2: Custom TensorFlow AMT implementation**
   - Use TensorFlow 2.20.0 directly for custom neural networks
   - Implement pitch detection using spectrograms

3. **Option 3: PyTorch-based AMT**
   - Use PyTorch (already in requirements) for custom AMT
   - Alternative libraries like `madmom`

## Installation Instructions

### Method 1: Use Fixed Requirements (Recommended)
```bash
cd /home/admin1/TuttiBot/Workspace
pip install -r requirement_v02_gpu_fixed.txt
```

### Method 2: Use Python 3.11 for Full Compatibility
If you need basic-pitch specifically:
```bash
# Create new conda environment with Python 3.11
conda create -n tuttibot_py311 python=3.11
conda activate tuttibot_py311
pip install -r requirement_v02_gpu.txt  # Original file will work with Python 3.11
```

### Method 3: Individual Package Installation
If you encounter issues:
```bash
# Install core packages first
pip install numpy scipy pandas matplotlib seaborn

# Install audio processing
pip install librosa soundfile audioread==3.0.1

# Install music processing
pip install music21 pretty_midi mido

# Install ML frameworks
pip install tensorflow>=2.20.0 torch torchaudio

# Install utilities
pip install psutil numba tqdm
```

## Verification

Test the installation:
```bash
python -c "
import tensorflow as tf
import torch
import librosa
import music21
print('✅ All core packages imported successfully')
print(f'TensorFlow: {tf.__version__}')
print(f'PyTorch: {torch.__version__}')
print(f'GPU Available (TF):', tf.config.list_physical_devices('GPU'))
print(f'GPU Available (PyTorch):', torch.cuda.is_available())
"
```

## GPU Status

The fixed requirements include full GPU support:
- **TensorFlow 2.20.0** with CUDA support
- **PyTorch 2.8.0** with CUDA support
- **Automatic CPU fallback** if GPU not available
- **NVIDIA CUDA libraries** automatically installed

## Next Steps

1. ✅ **Install fixed requirements:** Use `requirement_v02_gpu_fixed.txt`
2. ⚠️ **Update AMT code:** Modify Block 1 to use alternative AMT methods
3. 🔧 **Test pipeline:** Run `main_v02_fixed.py` with sample data
4. 📊 **Monitor GPU:** Use the built-in GPU manager

## Notes

- The fixed requirements file removes the problematic `basic-pitch` dependency
- You can implement custom AMT using TensorFlow 2.20.0 or PyTorch
- All other functionality (ScoreGraph, Alignment) works perfectly
- Consider using Python 3.11 if you specifically need `basic-pitch`
