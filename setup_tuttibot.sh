#!/bin/bash
set -e

echo "🎼 TuttiBot v02 Cross-System Setup Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2 || echo "none")
echo -e "${BLUE}Detected Python: $PYTHON_VERSION${NC}"

if [[ "$PYTHON_VERSION" == "none" ]]; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8-3.10${NC}"
    exit 1
fi

if [[ "$PYTHON_VERSION" == "3.11" || "$PYTHON_VERSION" == "3.12" ]]; then
    echo -e "${YELLOW}⚠️  Python $PYTHON_VERSION detected. This may cause dependency conflicts!${NC}"
    echo -e "${YELLOW}Recommended: Install Python 3.10 and rerun${NC}"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Install Python 3.10 for best compatibility."
        exit 1
    fi
fi

# Check if virtual environment exists
if [[ -d "tuttibot_env" ]]; then
    echo -e "${YELLOW}📁 Virtual environment 'tuttibot_env' already exists${NC}"
    read -p "Remove and recreate? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf tuttibot_env
    else
        echo "Using existing environment..."
        source tuttibot_env/bin/activate
        echo -e "${GREEN}✅ Environment activated${NC}"
        exit 0
    fi
fi

# Create virtual environment
echo -e "${BLUE}📦 Creating virtual environment...${NC}"
python3 -m venv tuttibot_env

# Activate environment
source tuttibot_env/bin/activate

# Upgrade pip
echo -e "${BLUE}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip

# Clear any existing packages
echo -e "${BLUE}🧹 Clearing pip cache...${NC}"
pip cache purge

echo -e "${BLUE}📥 Installing TuttiBot dependencies in specific order...${NC}"
echo ""

# Critical installation order to avoid conflicts
echo -e "${BLUE}Step 1/6: Installing core numerical libraries...${NC}"
pip install numpy==1.26.4 scipy==1.14.1

echo -e "${BLUE}Step 2/6: Installing TensorFlow...${NC}"
pip install tensorflow==2.15.0 tensorflow-estimator==2.15.0

echo -e "${BLUE}Step 3/6: Installing audio processing libraries...${NC}"
pip install librosa==0.10.2.post1 soundfile==0.12.1

echo -e "${BLUE}Step 4/6: Installing Basic Pitch (AMT)...${NC}"
pip install basic-pitch==0.4.0

echo -e "${BLUE}Step 5/6: Installing music processing libraries...${NC}"
pip install music21==5.7.2 pretty_midi==0.2.10

echo -e "${BLUE}Step 6/6: Installing remaining dependencies...${NC}"
pip install pandas==1.5.3 scikit-learn==1.5.0 matplotlib==3.6.2
pip install docker==7.1.0 oemer==0.1.8 requests==2.31.0
pip install tqdm==4.66.4 PyYAML==6.0.1

# Test critical imports
echo ""
echo -e "${BLUE}🧪 Testing critical imports...${NC}"

python3 -c "
import sys
try:
    import numpy as np
    print('✅ NumPy:', np.__version__)
except ImportError as e:
    print('❌ NumPy failed:', e)
    sys.exit(1)

try:
    import tensorflow as tf
    print('✅ TensorFlow:', tf.__version__)
except ImportError as e:
    print('❌ TensorFlow failed:', e)
    sys.exit(1)

try:
    import basic_pitch
    print('✅ Basic Pitch: OK')
except ImportError as e:
    print('❌ Basic Pitch failed:', e)
    sys.exit(1)

try:
    import librosa
    print('✅ Librosa:', librosa.__version__)
except ImportError as e:
    print('❌ Librosa failed:', e)
    sys.exit(1)

try:
    import music21
    print('✅ Music21:', music21.VERSION_STR)
except ImportError as e:
    print('❌ Music21 failed:', e)
    sys.exit(1)

try:
    import oemer
    print('✅ oemer: OK')
except ImportError as e:
    print('❌ oemer failed:', e)
    sys.exit(1)
"

if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
    echo ""
    echo -e "${GREEN}To use TuttiBot v02:${NC}"
    echo -e "${YELLOW}1. Activate environment: ${NC}source tuttibot_env/bin/activate"
    echo -e "${YELLOW}2. Run pipeline: ${NC}python3 main_v02_fixed.py --help"
    echo ""
    echo -e "${BLUE}Environment saved as: tuttibot_env/${NC}"
else
    echo -e "${RED}❌ Setup failed. Check error messages above.${NC}"
    exit 1
fi
