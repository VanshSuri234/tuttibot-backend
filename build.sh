#!/bin/bash
# Render.com Build Script for TuttiBot Backend
# This script installs system dependencies and Python packages

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
