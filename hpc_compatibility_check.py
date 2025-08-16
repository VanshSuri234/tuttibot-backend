#!/usr/bin/env python3
"""
HPC Compatibility Check for TuttiBot
====================================

Run this script on ADA HPC to check environment compatibility
"""

import sys
import subprocess
import importlib
import os
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version compatible")
        return True
    else:
        print("❌ Python version too old. Requires Python 3.8+")
        return False

def check_system_info():
    """Check system information"""
    print("\n" + "="*50)
    print("SYSTEM INFORMATION")
    print("="*50)
    
    # Check OS
    print(f"Operating System: {os.name}")
    
    # Check if we're on a GPU node
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPU detected - CUDA warnings should be minimal")
            print("GPU Info:")
            lines = result.stdout.split('\n')
            for line in lines[8:12]:  # GPU info lines
                if line.strip():
                    print(f"  {line.strip()}")
        else:
            print("⚠️  No NVIDIA GPU detected - will use CPU (expect CUDA warnings)")
    except FileNotFoundError:
        print("⚠️  nvidia-smi not found - likely CPU-only node")
    
    # Check available memory
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal'):
                    memory_kb = int(line.split()[1])
                    memory_gb = memory_kb / (1024 * 1024)
                    print(f"Available RAM: {memory_gb:.1f} GB")
                    if memory_gb >= 8:
                        print("✅ Sufficient RAM for audio processing")
                    else:
                        print("⚠️  Limited RAM - may need to process smaller files")
                    break
    except:
        print("Could not determine memory information")

def check_dependencies():
    """Check required dependencies"""
    print("\n" + "="*50)
    print("DEPENDENCY CHECK")
    print("="*50)
    
    required_packages = [
        'numpy',
        'scipy',
        'librosa',
        'soundfile',
        'noisereduce',
        'auditok',
        'music21',
        'aubio',
        'essentia',
        'pretty_midi',
        'ffmpeg_normalize'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'ffmpeg_normalize':
                importlib.import_module('ffmpeg_normalize')
            else:
                importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    return missing_packages

def check_audio_codecs():
    """Check audio codec support"""
    print("\n" + "="*50)
    print("AUDIO CODEC CHECK")
    print("="*50)
    
    # Check ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg available")
            # Get version info
            version_line = result.stdout.split('\n')[0]
            print(f"  {version_line}")
        else:
            print("❌ FFmpeg not available")
    except FileNotFoundError:
        print("❌ FFmpeg not found - audio normalization may fail")
    
    # Check if we can import soundfile
    try:
        import soundfile as sf
        print("✅ SoundFile library available")
    except ImportError:
        print("❌ SoundFile library missing")

def check_file_permissions():
    """Check file system permissions"""
    print("\n" + "="*50)
    print("FILE SYSTEM CHECK")
    print("="*50)
    
    # Check current directory permissions
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    if os.access(current_dir, os.W_OK):
        print("✅ Write permissions in current directory")
    else:
        print("❌ No write permissions in current directory")
    
    # Check if we can create test directories
    try:
        test_dir = current_dir / "test_permissions"
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "test.txt"
        test_file.write_text("test")
        test_file.unlink()
        test_dir.rmdir()
        print("✅ Can create and delete files/directories")
    except Exception as e:
        print(f"❌ File operation failed: {e}")

def generate_hpc_setup_script():
    """Generate setup script for HPC environment"""
    setup_script = """#!/bin/bash
# TuttiBot HPC Setup Script for ADA
# Run this with: bash hpc_setup.sh

echo "Setting up TuttiBot on ADA HPC..."

# Load required modules (adjust based on ADA's available modules)
module load python/3.10
module load gcc/9.3.0
module load cuda/11.8  # If available and you want GPU support

# Create virtual environment
python -m venv tuttibot_env
source tuttibot_env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install numpy scipy librosa soundfile
pip install noisereduce auditok music21
pip install aubio pretty-midi
pip install ffmpeg-normalize

# For GPU support (if CUDA available)
pip install essentia-tensorflow

echo "Setup complete! Activate environment with:"
echo "source tuttibot_env/bin/activate"
"""
    
    with open('hpc_setup.sh', 'w') as f:
        f.write(setup_script)
    
    print("\n" + "="*50)
    print("HPC SETUP SCRIPT GENERATED")
    print("="*50)
    print("Created 'hpc_setup.sh' - run with: bash hpc_setup.sh")

def main():
    """Run complete compatibility check"""
    print("🔍 ADA HPC COMPATIBILITY CHECK FOR TUTTIBOT")
    print("=" * 60)
    
    # Basic checks
    python_ok = check_python_version()
    check_system_info()
    missing_deps = check_dependencies()
    check_audio_codecs()
    check_file_permissions()
    
    # Summary
    print("\n" + "="*60)
    print("COMPATIBILITY SUMMARY")
    print("="*60)
    
    if python_ok and not missing_deps:
        print("🎉 FULLY COMPATIBLE - TuttiBot should run perfectly!")
    elif python_ok:
        print("⚠️  PARTIALLY COMPATIBLE - install missing dependencies:")
        for dep in missing_deps:
            print(f"   pip install {dep}")
    else:
        print("❌ INCOMPATIBLE - Python version too old")
    
    generate_hpc_setup_script()
    
    print("\nNext steps:")
    print("1. If missing dependencies, run: bash hpc_setup.sh")
    print("2. Copy your TuttiBot code to the HPC")
    print("3. Run your processing pipeline")
    print("4. GPU nodes will be faster, CPU nodes will work fine")

if __name__ == "__main__":
    main()
