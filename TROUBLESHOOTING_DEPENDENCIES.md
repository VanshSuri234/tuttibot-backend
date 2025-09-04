# TuttiBot v02 - Dependency Troubleshooting Guide

## Quick Setup (Recommended)

```bash
# 1. Run the automated setup
./setup_compatible_env.sh

# 2. Activate the environment
source activate_tuttibot_env.sh

# 3. Test the pipeline
python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav
```

## Manual Setup (If Automated Fails)

### Step 1: Python 3.10 Installation

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

#### CentOS/RHEL:
```bash
sudo yum install python310 python310-devel
```

#### macOS (via Homebrew):
```bash
brew install python@3.10
```

### Step 2: Virtual Environment
```bash
python3.10 -m venv tuttibot_compatible_env
source tuttibot_compatible_env/bin/activate
pip install --upgrade pip
```

### Step 3: Install Dependencies in Order
```bash
# Core ML stack first
pip install "numpy>=1.22.0,<1.24.0"
pip install tensorflow==2.12.0
pip install keras==2.12.0

# Basic Pitch and audio
pip install basic-pitch==0.3.0
pip install "librosa>=0.8.0,<0.11.0"

# PDF processing
pip install "onnxruntime>=1.10.0,<1.17.0"

# Rest of requirements
pip install -r requirements_compatible.txt
```

## Common Issues & Solutions

### Issue 1: TensorFlow GPU Not Detected
```bash
# Check NVIDIA drivers
nvidia-smi

# Check CUDA compatibility
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

# Install CUDA-compatible TensorFlow
pip install tensorflow[and-cuda]==2.12.0
```

### Issue 2: NumPy Version Conflicts
```bash
# Force correct NumPy version
pip uninstall numpy -y
pip install "numpy>=1.22.0,<1.24.0" --force-reinstall --no-deps
```

### Issue 3: Basic Pitch Model Loading Fails
```bash
# Clear Basic Pitch cache
rm -rf ~/.cache/basic_pitch/

# Test Basic Pitch installation
python -c "from basic_pitch.inference import predict; print('Basic Pitch OK')"
```

### Issue 4: ONNX Runtime Compatibility
```bash
# Install CPU-only version if GPU version fails
pip uninstall onnxruntime onnxruntime-gpu -y
pip install onnxruntime==1.15.1
```

### Issue 5: Music21 Font Issues
```bash
# Install system fonts (Ubuntu/Debian)
sudo apt install fonts-dejavu-core

# Configure music21
python -c "import music21; music21.configure.run()"
```

## Dependency Version Matrix

| Package | Version | Python | Notes |
|---------|---------|--------|-------|
| Python | 3.10.x | - | Required for all dependencies |
| TensorFlow | 2.12.0 | 3.8-3.11 | GPU support, stable |
| NumPy | 1.22-1.23 | 3.8+ | Critical for TensorFlow |
| Basic Pitch | 0.3.0 | 3.8-3.11 | Audio transcription |
| ONNX Runtime | 1.10-1.16 | 3.8+ | PDF processing |
| Librosa | 0.8-0.10 | 3.7+ | Audio analysis |

## Testing Your Installation

### Test 1: Core Components
```bash
python -c "
import tensorflow as tf
import numpy as np
import basic_pitch
import onnxruntime
import music21
print('✅ All core components loaded successfully')
print(f'TensorFlow: {tf.__version__}')
print(f'NumPy: {np.__version__}')
print(f'GPU Available: {len(tf.config.list_physical_devices(\"GPU\")) > 0}')
"
```

### Test 2: Basic Pitch Audio Transcription
```bash
# Create a simple test
python -c "
import numpy as np
import soundfile as sf
from basic_pitch.inference import predict

# Create test audio (1 second of 440Hz tone)
sr = 22050
duration = 1.0
t = np.linspace(0, duration, int(sr * duration))
audio = 0.5 * np.sin(2 * np.pi * 440 * t)
sf.write('test_tone.wav', audio, sr)

# Test Basic Pitch
try:
    model_output, midi_data, note_events = predict('test_tone.wav')
    print(f'✅ Basic Pitch working: {len(note_events)} notes detected')
except Exception as e:
    print(f'❌ Basic Pitch failed: {e}')
"
```

### Test 3: ONNX Runtime
```bash
python -c "
import onnxruntime as ort
print('✅ ONNX Runtime providers:', ort.get_available_providers())
"
```

## Performance Optimization

### GPU Memory Management
```python
# Add to your Python scripts
import tensorflow as tf
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Enable memory growth
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)
```

### Parallel Processing
```bash
# Set environment variables for better performance
export OMP_NUM_THREADS=4
export TF_NUM_INTEROP_THREADS=4
export TF_NUM_INTRAOP_THREADS=4
```

## Environment Management

### Save Current Environment
```bash
pip freeze > my_working_requirements.txt
```

### Clone Environment to Another System
```bash
# On source system
pip freeze > tuttibot_exact_versions.txt

# On target system
python3.10 -m venv tuttibot_env
source tuttibot_env/bin/activate
pip install -r tuttibot_exact_versions.txt
```

### Clean Installation
```bash
# Remove environment
rm -rf tuttibot_compatible_env/

# Start fresh
./setup_compatible_env.sh
```

## Advanced Troubleshooting

### Debug TensorFlow Installation
```python
import tensorflow as tf
print("TensorFlow version:", tf.__version__)
print("CUDA support:", tf.test.is_built_with_cuda())
print("GPU devices:", tf.config.list_physical_devices('GPU'))
print("CUDA version:", tf.sysconfig.get_build_info()['cuda_version'])
print("CuDNN version:", tf.sysconfig.get_build_info()['cudnn_version'])
```

### Debug Basic Pitch Models
```python
from basic_pitch import ICASSP_2022_MODEL_PATH
import os
print("Model path:", ICASSP_2022_MODEL_PATH)
print("Model exists:", os.path.exists(ICASSP_2022_MODEL_PATH))
```

## Contact & Support

If you encounter issues not covered here:
1. Check the specific error messages
2. Verify Python 3.10 installation
3. Ensure virtual environment is activated
4. Try the manual installation steps
5. Check GPU drivers and CUDA compatibility
