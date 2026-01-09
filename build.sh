#!/bin/bash
# Render.com Build Script for TuttiBot Backend
# 
# NOTE: Render's build environment is read-only and doesn't support apt-get
# This script uses pre-built wheels only (no C compilation)
#
# If set as Build Command in Render Dashboard:
# 1. Go to Render Service Dashboard → Settings → Build & Deploy
# 2. Set Build Command to: pip install -r requirements.txt
#
# This script runs locally for testing:
#   bash build.sh

set -e  # Exit on error

echo "==> Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "==> Installing Python requirements (pre-built wheels)..."
pip install -r requirements.txt

echo "==> Build completed successfully!"
echo "==> Note: System packages (libsndfile1, ffmpeg, portaudio) are provided by Render base image"
