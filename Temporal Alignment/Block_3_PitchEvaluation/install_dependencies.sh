#!/bin/bash
#
# Quick Install Script for Pitch Evaluation System
# CPU-Optimized (No GPU required)
#

echo "========================================================================"
echo "🎵 Installing Pitch Evaluation System Dependencies"
echo "========================================================================"
echo ""
echo "This will install CPU-optimized packages for pitch evaluation:"
echo "  - music21 (score parsing)"
echo "  - librosa (audio pitch extraction)"
echo "  - numpy, scipy (numerical operations)"
echo "  - matplotlib, seaborn (visualizations)"
echo "  - soundfile, audioread (audio I/O)"
echo "  - mir_eval (evaluation metrics)"
echo ""
echo "⚡ No GPU required - Everything runs on CPU!"
echo ""

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ Error: pip is not installed"
    echo "Please install pip first: https://pip.pypa.io/en/stable/installation/"
    exit 1
fi

echo "📦 Installing dependencies..."
echo ""

# Install dependencies
pip install music21>=9.1.0 \
    librosa>=0.10.0 \
    numpy>=1.24.0 \
    scipy>=1.10.0 \
    matplotlib>=3.7.0 \
    seaborn>=0.12.0 \
    soundfile>=0.12.0 \
    audioread>=3.0.0 \
    resampy>=0.4.2 \
    numba>=0.57.0 \
    mir_eval>=0.7

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ Installation Complete!"
    echo "========================================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Test the system: python test_pitch_system.py"
    echo "  2. Run evaluation: python evaluate_pitch.py --score <file> --audio <file>"
    echo ""
    echo "For help: python evaluate_pitch.py --help"
    echo "For full documentation: cat README.md"
    echo ""
else
    echo ""
    echo "========================================================================"
    echo "❌ Installation Failed"
    echo "========================================================================"
    echo ""
    echo "Please check the error messages above and try again."
    echo ""
    echo "Common solutions:"
    echo "  - Update pip: pip install --upgrade pip"
    echo "  - Install system dependencies (Ubuntu): sudo apt-get install libsndfile1"
    echo "  - Install system dependencies (Mac): brew install libsndfile"
    echo ""
    exit 1
fi
