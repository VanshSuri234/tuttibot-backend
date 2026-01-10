#!/bin/bash
# Render.com Build Script for TuttiBot Backend
# 
# This script is executed by Render during the build phase
# It installs dependencies with strategies to avoid compilation errors
#
# Key strategy:
# 1. Use --prefer-binary flag to prioritize pre-built wheels
# 2. Create pip.conf to force binary-only installation where possible
# 3. Avoid building pyaudio (audio playback - not needed for file processing)

set -e  # Exit on error

echo "==> TuttiBot Backend Build Script"
echo "==> Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Create pip configuration to prevent building from source
mkdir -p ~/.config/pip
cat > ~/.config/pip/pip.conf << 'EOF'
[global]
prefer-binary = True
no-cache-dir = False
EOF

echo "==> Installing Python requirements with binary preference..."
# The --prefer-binary flag ensures:
# 1. All available pre-built wheels are used (faster, no compilation)
# 2. PyAudio is NOT required - it's used by pydub for playback only
# 3. The pipeline only READS audio files, doesn't play them
echo "==> Using pip configuration with prefer-binary = True"

# Install with maximum compatibility flags
pip install --prefer-binary --upgrade --upgrade-strategy eager -r requirements.txt

echo "==> Verifying critical packages..."
python3 -c "import flask; import librosa; import music21; print('✓ All critical packages imported successfully')"

echo "==> Build completed successfully!"
echo "==> Application ready to start with gunicorn"
