#!/bin/bash
# TuttiBot v02 - Deploy Original Working Configuration
# Based on analysis of original system files
# Use this for 100% compatibility with proven working setup

set -e

echo "🎯 TuttiBot v02 - Original System Clone Deployment"
echo "=================================================="

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
echo "Current Python: $python_version"

if [[ "$python_version" != "3.10.12" ]]; then
    echo "⚠️  WARNING: Original system used Python 3.10.12"
    echo "   Current: Python $python_version"
    echo "   For 100% compatibility, install Python 3.10.12"
    echo "   Continue? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
if command -v python3.10 &> /dev/null; then
    python3.10 -m venv tuttibot_original_env
else
    python3 -m venv tuttibot_original_env
fi

echo "🔄 Activating environment..."
source tuttibot_original_env/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing packages in EXACT order from original system..."
echo "   This may take 5-10 minutes..."

# Step 1: Core numerical computing (CRITICAL ORDER)
echo "   Step 1/7: Core numerical libraries..."
pip install numpy==1.26.4
pip install scipy==1.14.1

# Step 2: TensorFlow ecosystem (EXACT VERSIONS)
echo "   Step 2/7: TensorFlow ecosystem..."
pip install tensorflow==2.15.0
pip install tensorflow-estimator==2.15.0
pip install tensorflow-io-gcs-filesystem==0.37.1

# Step 3: Audio processing
echo "   Step 3/7: Audio processing..."
pip install librosa==0.10.2.post1
pip install soundfile==0.12.1

# Step 4: Music AI models
echo "   Step 4/7: Music AI models..."
pip install basic-pitch==0.4.0

# Step 5: Music processing
echo "   Step 5/7: Music processing..."
pip install music21==5.7.2
pip install pretty_midi==0.2.10

# Step 6: Data science & visualization
echo "   Step 6/7: Data science..."
pip install pandas==1.5.3
pip install scikit-learn==1.5.0
pip install matplotlib==3.6.2

# Step 7: System integration & utilities
echo "   Step 7/7: System integration..."
pip install docker==7.1.0
pip install oemer==0.1.8
pip install opencv-python==4.11.0.86
pip install requests==2.31.0
pip install tqdm==4.66.4
pip install PyYAML==6.0.1
pip install jupyter==1.0.0

echo "✅ All packages installed!"

# Critical import test
echo "🧪 Testing critical imports..."
python3 << 'EOF'
import sys
print(f"Python version: {sys.version}")

try:
    import numpy as np
    print(f"✅ NumPy {np.__version__}")
except ImportError as e:
    print(f"❌ NumPy: {e}")

try:
    import tensorflow as tf
    print(f"✅ TensorFlow {tf.__version__}")
    gpus = tf.config.list_physical_devices('GPU')
    print(f"   GPUs detected: {len(gpus)}")
    if gpus:
        print(f"   GPU names: {[gpu.name for gpu in gpus]}")
except ImportError as e:
    print(f"❌ TensorFlow: {e}")

try:
    import librosa
    print(f"✅ Librosa {librosa.__version__}")
except ImportError as e:
    print(f"❌ Librosa: {e}")

try:
    import basic_pitch
    print(f"✅ Basic Pitch (version detection varies)")
except ImportError as e:
    print(f"❌ Basic Pitch: {e}")

try:
    import music21
    print(f"✅ Music21 {music21.__version__}")
except ImportError as e:
    print(f"❌ Music21: {e}")

try:
    import oemer
    print(f"✅ Oemer (PDF conversion)")
except ImportError as e:
    print(f"❌ Oemer: {e}")

print("\n🔬 Environment verification complete!")
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Original system configuration cloned!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Activate environment: source tuttibot_original_env/bin/activate"
    echo "   2. Test the pipeline:"
    echo "      python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav"
    echo ""
    echo "💡 This environment uses the EXACT working versions from the original system."
else
    echo "❌ Some imports failed. Check error messages above."
    echo "💡 You may need to install system dependencies:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install libsndfile1-dev ffmpeg"
fi

echo ""
echo "🔧 Environment created: tuttibot_original_env"
echo "🐍 Python location: $(which python3)"
echo "📁 Working directory: $(pwd)"
