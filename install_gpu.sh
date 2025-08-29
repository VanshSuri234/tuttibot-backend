#!/bin/bash
"""
TuttiBot v02 GPU-Ready Installation Script
==========================================

Automatic installation script that works on both local systems and HPC environments.
Detects SLURM/HPC setup and configures appropriate GPU support.

Usage:
  ./install_gpu.sh                    # Auto-detect and install
  ./install_gpu.sh --cpu-only         # Force CPU-only installation
  ./install_gpu.sh --gpu              # Force GPU installation
  ./install_gpu.sh --hpc              # HPC-specific installation

Author: TuttiBot Team
Version: 2.0.1
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FORCE_CPU=false
FORCE_GPU=false
FORCE_HPC=false
PYTHON_CMD="python3"
PIP_CMD="pip3"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --cpu-only)
            FORCE_CPU=true
            shift
            ;;
        --gpu)
            FORCE_GPU=true
            shift
            ;;
        --hpc)
            FORCE_HPC=true
            shift
            ;;
        --python)
            PYTHON_CMD="$2"
            shift 2
            ;;
        --pip)
            PIP_CMD="$2"
            shift 2
            ;;
        -h|--help)
            echo "TuttiBot v02 GPU-Ready Installation Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --cpu-only     Force CPU-only installation"
            echo "  --gpu          Force GPU installation"
            echo "  --hpc          HPC-specific installation"
            echo "  --python CMD   Python command to use (default: python3)"
            echo "  --pip CMD      Pip command to use (default: pip3)"
            echo "  -h, --help     Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🎼 TuttiBot v02 GPU-Ready Installation${NC}"
echo -e "${BLUE}================================================${NC}"

# Detect environment
detect_environment() {
    echo -e "${YELLOW}🔍 Detecting environment...${NC}"
    
    # Check for SLURM
    if [[ -n "${SLURM_JOB_ID}" ]] || [[ -n "${SLURM_NODELIST}" ]]; then
        echo -e "${GREEN}   ✅ SLURM/HPC environment detected${NC}"
        echo -e "      Job ID: ${SLURM_JOB_ID:-N/A}"
        echo -e "      Node: ${SLURM_NODELIST:-N/A}"
        IS_HPC=true
    else
        echo -e "${GREEN}   🏠 Local system detected${NC}"
        IS_HPC=false
    fi
    
    # Check for GPU
    if command -v nvidia-smi &> /dev/null; then
        GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader,nounits | head -1)
        echo -e "${GREEN}   🎮 GPU(s) detected: $GPU_COUNT${NC}"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | while read line; do
            echo -e "      $line"
        done
        HAS_GPU=true
    else
        echo -e "${YELLOW}   ⚠️  No GPU detected${NC}"
        HAS_GPU=false
    fi
    
    # Check Python
    if command -v $PYTHON_CMD &> /dev/null; then
        PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
        echo -e "${GREEN}   🐍 Python: $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}   ❌ Python not found: $PYTHON_CMD${NC}"
        exit 1
    fi
    
    # Check pip
    if command -v $PIP_CMD &> /dev/null; then
        PIP_VERSION=$($PIP_CMD --version 2>&1)
        echo -e "${GREEN}   📦 Pip: $PIP_VERSION${NC}"
    else
        echo -e "${RED}   ❌ Pip not found: $PIP_CMD${NC}"
        exit 1
    fi
}

# Setup virtual environment if needed
setup_venv() {
    echo -e "${YELLOW}🔧 Setting up Python environment...${NC}"
    
    if [[ ! -d "tuttibotv02_env" ]]; then
        echo -e "   Creating virtual environment..."
        $PYTHON_CMD -m venv tuttibotv02_env
    fi
    
    echo -e "   Activating virtual environment..."
    source tuttibotv02_env/bin/activate
    
    # Update pip
    echo -e "   Updating pip..."
    python -m pip install --upgrade pip
}

# Install basic requirements
install_basic_requirements() {
    echo -e "${YELLOW}📚 Installing basic requirements...${NC}"
    
    # Core dependencies that work everywhere
    cat > requirements_basic.txt << EOF
numpy>=1.21.0
scipy>=1.7.0
pandas>=1.3.0
librosa>=0.9.0
soundfile>=0.10.0
audioread>=2.1.0
music21>=8.0.0
pretty_midi>=0.2.9
mido>=1.2.0
matplotlib>=3.5.0
seaborn>=0.11.0
psutil>=5.8.0
tqdm>=4.62.0
numba>=0.56.0
basic-pitch>=0.4.0
EOF
    
    pip install -r requirements_basic.txt
}

# Install GPU-specific packages
install_gpu_packages() {
    echo -e "${YELLOW}🎮 Installing GPU packages...${NC}"
    
    if [[ "$IS_HPC" == true ]]; then
        echo -e "   HPC GPU installation..."
        # For HPC systems, often need specific CUDA versions
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
        pip install tensorflow>=2.8.0
    else
        echo -e "   Local GPU installation..."
        # For local systems, use standard GPU packages
        pip install torch torchaudio
        pip install tensorflow>=2.8.0
    fi
}

# Install CPU-only packages
install_cpu_packages() {
    echo -e "${YELLOW}💻 Installing CPU-only packages...${NC}"
    
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    pip install tensorflow-cpu>=2.8.0
}

# Test installation
test_installation() {
    echo -e "${YELLOW}🧪 Testing installation...${NC}"
    
    # Test GPU manager
    if python -c "from gpu_manager import GPUManager; gm = GPUManager(); gm.print_status()" 2>/dev/null; then
        echo -e "${GREEN}   ✅ GPU Manager test passed${NC}"
    else
        echo -e "${YELLOW}   ⚠️  GPU Manager test failed (may be normal)${NC}"
    fi
    
    # Test basic imports
    python -c "
import numpy as np
import scipy
import librosa
import pretty_midi
import tensorflow as tf
import torch
print('✅ All basic imports successful')
"
    
    echo -e "${GREEN}   ✅ Installation test completed${NC}"
}

# Main installation flow
main() {
    detect_environment
    
    # Determine installation type
    if [[ "$FORCE_CPU" == true ]]; then
        INSTALL_TYPE="cpu"
        echo -e "${YELLOW}   🔧 Forced CPU-only installation${NC}"
    elif [[ "$FORCE_GPU" == true ]]; then
        INSTALL_TYPE="gpu"
        echo -e "${YELLOW}   🔧 Forced GPU installation${NC}"
    elif [[ "$HAS_GPU" == true ]]; then
        INSTALL_TYPE="gpu"
        echo -e "${YELLOW}   🔧 Auto-detected GPU installation${NC}"
    else
        INSTALL_TYPE="cpu"
        echo -e "${YELLOW}   🔧 Auto-detected CPU installation${NC}"
    fi
    
    echo ""
    
    # Setup environment
    setup_venv
    
    # Install packages
    install_basic_requirements
    
    if [[ "$INSTALL_TYPE" == "gpu" ]]; then
        install_gpu_packages
    else
        install_cpu_packages
    fi
    
    # Test installation
    test_installation
    
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}🎉 TuttiBot v02 Installation Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo -e "${BLUE}To use TuttiBot v02:${NC}"
    echo -e "  1. Activate the environment:"
    echo -e "     ${YELLOW}source tuttibotv02_env/bin/activate${NC}"
    echo ""
    echo -e "  2. Run the pipeline:"
    echo -e "     ${YELLOW}python main_v02_fixed.py --pdf score.pdf --audio audio.wav${NC}"
    echo ""
    echo -e "  3. GPU options:"
    echo -e "     ${YELLOW}python main_v02_fixed.py --pdf score.pdf --audio audio.wav --gpu-id 0${NC}"
    echo -e "     ${YELLOW}python main_v02_fixed.py --pdf score.pdf --audio audio.wav --cpu-only${NC}"
    echo ""
    echo -e "${BLUE}Environment: ${NC}$([[ "$IS_HPC" == true ]] && echo "HPC/SLURM" || echo "Local")"
    echo -e "${BLUE}Installation: ${NC}$([[ "$INSTALL_TYPE" == "gpu" ]] && echo "GPU-enabled" || echo "CPU-only")"
}

# Run main function
main

echo -e "${GREEN}Installation script completed successfully!${NC}"
