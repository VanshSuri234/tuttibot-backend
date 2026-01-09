#!/bin/bash
# Render.com Build Script for TuttiBot Backend
# This script installs system dependencies and Python packages
# 
# IMPORTANT: For this script to run, you MUST set it in Render Dashboard:
# 1. Go to your Render Service Dashboard
# 2. Click "Settings"
# 3. Under "Build & Deploy", set Build Command to: ./build.sh
# 4. Redeploy the service
#
# Alternatively, you can manually run this locally for testing:
#   bash build.sh

set -e  # Exit on error

echo "==> Installing system dependencies..."
apt-get update
apt-get install -y \
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev

echo "==> Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "==> Installing Python requirements..."
pip install -r requirements.txt

echo "==> Build completed successfully!"
