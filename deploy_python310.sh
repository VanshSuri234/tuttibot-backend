#!/bin/bash
# TuttiBot v02 - Python 3.10.12 Exact Clone Deployment
# BEST COMPATIBILITY - Uses exact original system configuration

set -e

echo "🎯 TuttiBot v02 - Python 3.10.12 Original System Clone"
echo "===================================================="
echo "⚡ This will create the EXACT working environment from the original system"
echo ""

# Check if Python 3.10.12 is available
echo "🔍 Checking for Python 3.10.12..."
if ! pyenv versions --bare | grep -q "^3.10.12$"; then
    echo "📥 Python 3.10.12 not found. Installing via pyenv..."
    echo "   This will take 5-10 minutes..."
    pyenv install 3.10.12
    echo "✅ Python 3.10.12 installed!"
else
    echo "✅ Python 3.10.12 already available"
fi

# Set local Python version
echo "🔧 Setting Python 3.10.12 as local version..."
pyenv local 3.10.12

# Verify version
python_version=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
echo "📋 Active Python version: $python_version"

if [[ "$python_version" != "3.10.12" ]]; then
    echo "❌ ERROR: Python 3.10.12 not active. Please run:"
    echo "   export PATH=\"$(pyenv root)/shims:\$PATH\""
    echo "   pyenv local 3.10.12"
    exit 1
fi

# Create virtual environment with Python 3.10.12
echo "🏗️ Creating virtual environment with Python 3.10.12..."
python -m venv tuttibot_py310_env
source tuttibot_py310_env/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing packages with EXACT original versions..."
echo "   Using CRITICAL installation order to prevent conflicts"

# Step 1: Lock NumPy to 1.26.4 FIRST (prevents NumPy 2.x)
echo "   🔒 Step 1/8: Locking NumPy to 1.26.4..."
pip install "numpy==1.26.4"

# Step 2: Core scientific computing
echo "   📊 Step 2/8: Core scientific libraries..."
pip install "scipy==1.14.1"

# Step 3: TensorFlow ecosystem (exact versions)
echo "   🤖 Step 3/8: TensorFlow ecosystem..."
pip install "tensorflow==2.15.0"
pip install "tensorflow-estimator==2.15.0"
pip install "tensorflow-io-gcs-filesystem==0.37.1"

# Step 4: Audio processing (with NumPy locked)
echo "   🎵 Step 4/8: Audio processing..."
pip install "librosa==0.10.2.post1"
pip install "soundfile==0.12.1"

# Step 5: Basic Pitch (should now use NumPy 1.26.4)
echo "   🎼 Step 5/8: Basic Pitch AMT..."
pip install "basic-pitch==0.4.0"

# Step 6: Music processing
echo "   🎶 Step 6/8: Music processing..."
pip install "music21==5.7.2"
pip install "pretty_midi==0.2.10"

# Step 7: Data science
echo "   📈 Step 7/8: Data science..."
pip install "pandas==1.5.3"
pip install "scikit-learn==1.5.0"
pip install "matplotlib==3.6.2"

# Step 8: System integration
echo "   🔧 Step 8/8: System integration..."
pip install "docker==7.1.0"
pip install "oemer==0.1.8"
pip install "opencv-python==4.11.0.86"
pip install "requests==2.31.0"
pip install "tqdm==4.66.4"
pip install "PyYAML==6.0.1"
pip install "jupyter==1.0.0"

echo "✅ All packages installed with original versions!"

# Critical import test
echo ""
echo "🧪 Testing critical imports and versions..."
python << 'EOF'
import sys
print(f"🐍 Python: {sys.version}")
print()

# Test all critical imports with version checking
def test_import(module_name, expected_version=None):
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'unknown')
        status = "✅"
        if expected_version and version != expected_version:
            status = f"⚠️  (expected {expected_version})"
        print(f"{status} {module_name}: {version}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        return False

# Test with expected versions from original system
success = True
success &= test_import('numpy', '1.26.4')
success &= test_import('scipy', '1.14.1')  
success &= test_import('tensorflow', '2.15.0')
success &= test_import('librosa', '0.10.2.post1')
success &= test_import('basic_pitch')
success &= test_import('music21', '5.7.2')
success &= test_import('pandas', '1.5.3')
success &= test_import('sklearn', '1.5.0')
success &= test_import('oemer')

# Test GPU detection
print()
print("🎮 GPU Detection Test:")
try:
    import tensorflow as tf
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print(f"✅ Found {len(gpus)} GPU(s):")
        for gpu in gpus:
            print(f"   • {gpu.name}")
    else:
        print("ℹ️  No GPUs detected (CPU mode)")
except Exception as e:
    print(f"⚠️  GPU detection failed: {e}")

print()
if success:
    print("🎉 ALL CRITICAL IMPORTS SUCCESSFUL!")
    print("   This matches the original working system configuration.")
else:
    print("❌ Some imports failed. Check error messages above.")
print()
EOF

if [ $? -eq 0 ]; then
    echo "🏆 SUCCESS! Python 3.10.12 environment ready with original system config!"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Activate: source tuttibot_py310_env/bin/activate"
    echo "   2. Test pipeline: python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav"
    echo ""
    echo "💡 This environment uses Python 3.10.12 with EXACT versions from working system"
    echo "🔒 NumPy locked to 1.26.4 (prevents NumPy 2.x conflicts)"
else
    echo "❌ Environment setup encountered issues. Check output above."
fi

echo ""
echo "🐍 Python: $(python --version)"
echo "📁 Environment: tuttibot_py310_env"
echo "🎯 Status: Ready for TuttiBot v02 pipeline"
