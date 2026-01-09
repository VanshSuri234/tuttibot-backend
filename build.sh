#!/bin/bash
# Render.com Build Script for TuttiBot Backend
# 
# This script is executed by Render during the build phase
# It installs dependencies in the correct order to avoid
# compilation errors from packages with optional C dependencies
#
# Key strategy:
# 1. Use --prefer-binary flag to prioritize pre-built wheels
# 2. Install packages in dependency order
# 3. Avoid building pyaudio (microphone recording - not needed)

set -e  # Exit on error

echo "==> TuttiBot Backend Build Script"
echo "==> Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "==> Installing Python requirements with binary preference..."
# Key flag: --prefer-binary tells pip to use pre-built wheels when available
# This avoids C compilation for packages like auditok
pip install --prefer-binary -r requirements.txt

echo "==> Verifying critical packages..."
python3 -c "import flask; import librosa; import music21; print('✓ All critical packages imported successfully')"

echo "==> Build completed successfully!"
echo "==> Application ready to start with gunicorn"
