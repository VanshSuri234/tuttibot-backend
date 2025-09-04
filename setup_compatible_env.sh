#!/bin/bash

# TuttiBot v02 - Compatible Environment Setup Script
# This script creates a Python 3.10 virtual environment with compatible dependencies

set -e  # Exit on any error

echo "========================================================================"
echo "🎼 TuttiBot v02 - Compatible Environment Setup"
echo "========================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python 3.12 availability
echo -e "${BLUE}📋 Checking Python 3.12 availability...${NC}"
if ! command -v python3.12 &> /dev/null; then
    echo -e "${RED}❌ Python 3.12 not found!${NC}"
    echo -e "${YELLOW}Please install Python 3.12:${NC}"
    echo "   Ubuntu/Debian: sudo apt update && sudo apt install python3.12 python3.12-venv python3.12-dev"
    echo "   CentOS/RHEL: sudo yum install python312 python312-devel"
    echo "   Or download from: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3.12 --version)
echo -e "${GREEN}✅ Found ${PYTHON_VERSION}${NC}"

# Environment name
ENV_NAME="tuttibot_compatible_env"
ENV_PATH="$HOME/$ENV_NAME"

# Remove existing environment if it exists
if [ -d "$ENV_PATH" ]; then
    echo -e "${YELLOW}⚠️  Existing environment found. Removing...${NC}"
    rm -rf "$ENV_PATH"
fi

# Create virtual environment
echo -e "${BLUE}🏗️  Creating Python 3.12 virtual environment...${NC}"
python3.12 -m venv "$ENV_PATH"

# Activate environment
echo -e "${BLUE}🔄 Activating environment...${NC}"
source "$ENV_PATH/bin/activate"

# Upgrade pip
echo -e "${BLUE}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "${BLUE}📚 Installing compatible requirements...${NC}"
pip install -r requirements_compatible.txt

# Verify critical installations
echo -e "${BLUE}🔍 Verifying installations...${NC}"

# Test TensorFlow
echo -e "${YELLOW}Testing TensorFlow...${NC}"
python -c "import tensorflow as tf; print(f'TensorFlow: {tf.__version__}'); print(f'GPU Available: {tf.config.list_physical_devices(\"GPU\")}')" || {
    echo -e "${RED}❌ TensorFlow test failed${NC}"
    exit 1
}

# Test Basic Pitch
echo -e "${YELLOW}Testing Basic Pitch...${NC}"
python -c "import basic_pitch; print('Basic Pitch: OK')" || {
    echo -e "${RED}❌ Basic Pitch test failed${NC}"
    exit 1
}

# Test ONNX Runtime
echo -e "${YELLOW}Testing ONNX Runtime...${NC}"
python -c "import onnxruntime; print(f'ONNX Runtime: {onnxruntime.__version__}')" || {
    echo -e "${RED}❌ ONNX Runtime test failed${NC}"
    exit 1
}

# Test music21
echo -e "${YELLOW}Testing music21...${NC}"
python -c "import music21; print('music21: OK')" || {
    echo -e "${RED}❌ music21 test failed${NC}"
    exit 1
}

echo -e "${GREEN}✅ All critical components verified!${NC}"

# Create activation script
ACTIVATE_SCRIPT="activate_tuttibot_env.sh"
cat > "$ACTIVATE_SCRIPT" << EOF
#!/bin/bash
# TuttiBot v02 Environment Activation Script
source "$ENV_PATH/bin/activate"
echo "🎼 TuttiBot v02 environment activated!"
echo "Python: \$(python --version)"
echo "Environment: $ENV_PATH"
echo ""
echo "To run TuttiBot:"
echo "  python main_v02_fixed.py --pdf <pdf_file> --audio <audio_file>"
echo ""
echo "To deactivate: deactivate"
EOF

chmod +x "$ACTIVATE_SCRIPT"

echo ""
echo -e "${GREEN}========================================================================"
echo -e "🎉 TuttiBot v02 Compatible Environment Setup Complete!"
echo -e "========================================================================${NC}"
echo ""
echo -e "${BLUE}Environment Details:${NC}"
echo "  📁 Location: $ENV_PATH"
echo "  🐍 Python: $(python --version)"
echo "  📦 Packages: $(pip list | wc -l) installed"
echo ""
echo -e "${BLUE}To use TuttiBot:${NC}"
echo "  1. Activate environment: source $ACTIVATE_SCRIPT"
echo "  2. Run TuttiBot: python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav"
echo ""
echo -e "${BLUE}To manually activate anytime:${NC}"
echo "  source $ENV_PATH/bin/activate"
echo ""
echo -e "${GREEN}🚀 Ready to run TuttiBot v02!${NC}"
