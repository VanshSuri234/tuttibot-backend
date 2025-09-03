#!/bin/bash
# TuttiBot v02 - Complete Installation Script
# This script installs all dependencies and verifies the installation

echo "🚀 Starting TuttiBot v02 Complete Installation..."
echo "=================================================="
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
echo "=================================================="

# Install all requirements
echo "📦 Installing all requirements..."
pip install -r requirement_v02_gpu_fixed.txt

# Check installation status
echo ""
echo "🔍 Verifying installation..."
echo "=================================================="

# Test core imports
python -c "
import sys
print('Python version:', sys.version)
print()

# Test core packages
try:
    import numpy as np
    print('✅ NumPy:', np.__version__)
except ImportError as e:
    print('❌ NumPy failed:', e)

try:
    import scipy
    print('✅ SciPy:', scipy.__version__)
except ImportError as e:
    print('❌ SciPy failed:', e)

try:
    import pandas as pd
    print('✅ Pandas:', pd.__version__)
except ImportError as e:
    print('❌ Pandas failed:', e)

try:
    import matplotlib
    print('✅ Matplotlib:', matplotlib.__version__)
except ImportError as e:
    print('❌ Matplotlib failed:', e)

# Test audio processing
try:
    import librosa
    print('✅ Librosa:', librosa.__version__)
except ImportError as e:
    print('❌ Librosa failed:', e)

try:
    import soundfile
    print('✅ SoundFile:', soundfile.__version__)
except ImportError as e:
    print('❌ SoundFile failed:', e)

try:
    import audioread
    print('✅ AudioRead:', audioread.__version__)
except ImportError as e:
    print('❌ AudioRead failed:', e)

# Test music processing
try:
    import music21
    print('✅ Music21:', music21.__version__)
except ImportError as e:
    print('❌ Music21 failed:', e)

try:
    import pretty_midi
    print('✅ Pretty MIDI:', pretty_midi.__version__)
except ImportError as e:
    print('❌ Pretty MIDI failed:', e)

try:
    import mido
    print('✅ Mido:', mido.__version__)
except ImportError as e:
    print('❌ Mido failed:', e)

# Test ML frameworks
try:
    import tensorflow as tf
    print('✅ TensorFlow:', tf.__version__)
    print('  GPU devices:', len(tf.config.list_physical_devices(\"GPU\")))
except ImportError as e:
    print('❌ TensorFlow failed:', e)

try:
    import torch
    print('✅ PyTorch:', torch.__version__)
    print('  CUDA available:', torch.cuda.is_available())
    if torch.cuda.is_available():
        print('  CUDA devices:', torch.cuda.device_count())
except ImportError as e:
    print('❌ PyTorch failed:', e)

# Test PDF processing
try:
    import pdf2image
    print('✅ PDF2Image: Available')
except ImportError as e:
    print('❌ PDF2Image failed:', e)

try:
    import oemer
    print('✅ Oemer: Available')
except ImportError as e:
    print('❌ Oemer failed:', e)

# Test system monitoring
try:
    import psutil
    print('✅ PSUtil:', psutil.__version__)
except ImportError as e:
    print('❌ PSUtil failed:', e)

print()
print('📊 Installation Summary:')
print('========================')
"

# Test GPU manager
echo ""
echo "🖥️ Testing GPU Manager..."
python -c "
try:
    from gpu_manager import GPUManager
    gpu_manager = GPUManager()
    gpu_manager.print_status()
    print('✅ GPU Manager working correctly')
except Exception as e:
    print('❌ GPU Manager failed:', e)
"

# Test pipeline imports
echo ""
echo "🔧 Testing Pipeline Imports..."
python -c "
import sys
import os
sys.path.append('Temporal Alignment/Block_0_ScoreGraph')
sys.path.append('Temporal Alignment/Block_1_AMT') 
sys.path.append('Temporal Alignment/Block_2_SymbolicAlignment')

try:
    from build_scoregraph_with_repeats import build_scoregraph
    print('✅ Block 0 (ScoreGraph) import successful')
except Exception as e:
    print('❌ Block 0 import failed:', e)

try:
    from transcribe_audio_fixed import transcribe_audio_basic_pitch
    print('✅ Block 1 (AMT) import successful')
except Exception as e:
    print('❌ Block 1 import failed:', e)

try:
    from align_symbolic_enhanced import EnhancedSymbolicAligner
    print('✅ Block 2 (Alignment) import successful')
except Exception as e:
    print('❌ Block 2 import failed:', e)
"

echo ""
echo "🎯 Testing Main Script Syntax..."
python -c "
try:
    import main_v02_fixed
    print('✅ Main script syntax check passed')
except Exception as e:
    print('❌ Main script syntax error:', e)
"

echo ""
echo "=================================================="
echo "🏁 Installation Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Test with MusicXML: python main_v02_fixed.py --musicxml test.musicxml --audio twinkle_full.wav"
echo "2. For PDF support: Ensure you have the latest PDF files"
echo "3. For basic-pitch AMT: Consider using Python 3.11 environment"
echo ""
echo "Troubleshooting:"
echo "- If GPU not detected, that's normal for CPU-only systems"
echo "- TensorFlow warnings are normal and can be ignored"
echo "- For PDF conversion issues, check INSTALLATION_TROUBLESHOOTING_GUIDE.md"
echo ""
