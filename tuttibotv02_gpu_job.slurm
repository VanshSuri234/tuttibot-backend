#!/bin/bash
#SBATCH --job-name=tuttibotv02
#SBATCH --output=tuttibotv02_%j.out
#SBATCH --error=tuttibotv02_%j.err
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

# GPU configuration (uncomment for GPU nodes)
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu

# Email notifications (optional)
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=your.email@example.com

"""
TuttiBot v02 GPU-Ready SLURM Job Script
========================================

This script runs TuttiBot v02 on HPC systems with automatic GPU detection.
Works on systems like IIIT-H Ada and other SLURM-based clusters.

Usage:
  1. Edit the input file paths below
  2. Submit with: sbatch tuttibotv02_gpu_job.slurm
  3. Monitor with: squeue -u $USER

Features:
- Automatic GPU detection and allocation
- CPU fallback if no GPU available
- Module loading for HPC environments
- Comprehensive logging and monitoring

Author: TuttiBot Team
Version: 2.0.1
"""

echo "============================================================="
echo "🎼 TuttiBot v02 GPU-Ready SLURM Job"
echo "============================================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "Start time: $(date)"
echo "============================================================="

# ===========================
# CONFIGURATION SECTION
# ===========================

# Input files (MODIFY THESE PATHS)
PDF_FILE="INPUT_LAYER/score.pdf"
AUDIO_FILE="INPUT_LAYER/audio.wav"
OUTPUT_DIR="./Output"

# GPU configuration
FORCE_CPU_ONLY=false  # Set to true to force CPU-only mode
SPECIFIC_GPU_ID=""    # Set to specific GPU ID (0, 1, 2, etc.) or leave empty for auto-select

# Python environment (modify if needed)
PYTHON_ENV="tuttibotv02_env"
PYTHON_CMD="python"

# ===========================
# ENVIRONMENT SETUP
# ===========================

# Function to load HPC modules
load_hpc_modules() {
    echo "🔧 Loading HPC modules..."
    
    # Common module loading patterns for different HPC systems
    # Uncomment and modify as needed for your specific HPC system
    
    # For IIIT-H Ada or similar systems:
    # module load python/3.9.0
    # module load cuda/11.8
    # module load cudnn/8.2.0
    
    # For generic SLURM systems:
    # module load Python/3.9.6-GCCcore-11.2.0
    # module load CUDA/11.7.0
    
    # Alternative: Try to auto-detect and load common modules
    if command -v module &> /dev/null; then
        # Try to load Python
        if module avail python 2>&1 | grep -i python &> /dev/null; then
            module load $(module avail python 2>&1 | grep -i python | head -1 | awk '{print $1}') 2>/dev/null || true
        fi
        
        # Try to load CUDA
        if module avail cuda 2>&1 | grep -i cuda &> /dev/null; then
            module load $(module avail cuda 2>&1 | grep -i cuda | head -1 | awk '{print $1}') 2>/dev/null || true
        fi
        
        echo "✅ Loaded modules:"
        module list 2>&1 | head -10
    else
        echo "⚠️  Module system not available"
    fi
}

# Function to setup Python environment
setup_python_env() {
    echo "🐍 Setting up Python environment..."
    
    # Check if virtual environment exists
    if [[ -d "$PYTHON_ENV" ]]; then
        echo "   Activating existing environment: $PYTHON_ENV"
        source $PYTHON_ENV/bin/activate
    else
        echo "   ⚠️  Virtual environment not found: $PYTHON_ENV"
        echo "   Please run install_gpu.sh first or create the environment"
        exit 1
    fi
    
    # Verify Python and packages
    echo "   Python version: $($PYTHON_CMD --version)"
    echo "   Python path: $(which $PYTHON_CMD)"
    
    # Test critical imports
    $PYTHON_CMD -c "
import sys
print(f'Python executable: {sys.executable}')
try:
    import torch
    print(f'PyTorch: {torch.__version__}')
    print(f'CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'CUDA devices: {torch.cuda.device_count()}')
except ImportError:
    print('PyTorch not available')

try:
    import tensorflow as tf
    print(f'TensorFlow: {tf.__version__}')
    gpus = tf.config.list_physical_devices('GPU')
    print(f'TF GPUs: {len(gpus)}')
except ImportError:
    print('TensorFlow not available')
"
}

# Function to check system resources
check_resources() {
    echo "🔍 Checking system resources..."
    
    echo "   CPUs: $(nproc)"
    echo "   Memory: $(free -h | grep '^Mem:' | awk '{print $2}')"
    echo "   Disk space: $(df -h . | tail -1 | awk '{print $4}') available"
    
    # Check GPU status
    if command -v nvidia-smi &> /dev/null; then
        echo "   GPU status:"
        nvidia-smi --query-gpu=index,name,memory.total,memory.free,utilization.gpu --format=csv,noheader
    else
        echo "   No GPU tools available"
    fi
}

# ===========================
# MAIN EXECUTION
# ===========================

main() {
    # Setup environment
    load_hpc_modules
    setup_python_env
    check_resources
    
    echo ""
    echo "============================================================="
    echo "🚀 Starting TuttiBot v02 Pipeline"
    echo "============================================================="
    
    # Validate input files
    if [[ ! -f "$PDF_FILE" ]]; then
        echo "❌ Error: PDF file not found: $PDF_FILE"
        exit 1
    fi
    
    if [[ ! -f "$AUDIO_FILE" ]]; then
        echo "❌ Error: Audio file not found: $AUDIO_FILE"
        exit 1
    fi
    
    echo "📄 PDF Input: $PDF_FILE"
    echo "🎵 Audio Input: $AUDIO_FILE"
    echo "📁 Output Directory: $OUTPUT_DIR"
    
    # Build command
    CMD="$PYTHON_CMD main_v02_fixed.py --pdf '$PDF_FILE' --audio '$AUDIO_FILE' --output '$OUTPUT_DIR'"
    
    # Add GPU/CPU options
    if [[ "$FORCE_CPU_ONLY" == true ]]; then
        CMD="$CMD --cpu-only"
        echo "💻 Mode: CPU-only (forced)"
    elif [[ -n "$SPECIFIC_GPU_ID" ]]; then
        CMD="$CMD --gpu-id $SPECIFIC_GPU_ID"
        echo "🎮 Mode: GPU $SPECIFIC_GPU_ID"
    else
        echo "🔄 Mode: Auto-detect"
    fi
    
    echo ""
    echo "Executing command:"
    echo "$CMD"
    echo ""
    
    # Execute the pipeline
    start_time=$(date +%s)
    
    eval $CMD
    exit_code=$?
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo ""
    echo "============================================================="
    if [[ $exit_code -eq 0 ]]; then
        echo "🎉 TuttiBot v02 Pipeline Completed Successfully!"
    else
        echo "❌ TuttiBot v02 Pipeline Failed (exit code: $exit_code)"
    fi
    echo "============================================================="
    echo "Duration: $duration seconds"
    echo "End time: $(date)"
    echo "============================================================="
    
    # Cleanup
    if command -v nvidia-smi &> /dev/null; then
        echo "Final GPU status:"
        nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader
    fi
    
    exit $exit_code
}

# Error handling
set -e
trap 'echo "❌ Job failed at line $LINENO"; exit 1' ERR

# Run main function
main

echo "Job completed at $(date)"
