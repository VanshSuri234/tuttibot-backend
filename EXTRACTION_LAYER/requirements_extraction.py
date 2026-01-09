# Music Performance Analysis - Extraction Layer Requirements

# Core audio/music analysis libraries
librosa>=0.8
music21>=7.0
pretty-midi>=0.2
aubio>=0.4

# Note: essentia can be tricky to install, try different approaches
essentia>=2

# Scientific computing and data handling
numpy>=1.19
scipy>=1.6
pandas>=1.2

# Audio file handling
soundfile>=0.10
audioread>=2.1

# Data structures and utilities
typing-extensions>=3.7

# JSON and file I/O
jsonschema>=3.2

# Optional visualization dependencies
matplotlib>=3.3
plotly>=4.14
seaborn>=0.11

# Progress and logging
tqdm>=4.50

# Development and testing (optional)
pytest>=6.0
pytest-cov>=2.10
black>=20
flake8>=3.8

# Platform-specific audio backends (optional - not required for server deployments)
# Windows (uncomment if you need microphone input on Windows)
# pyaudio>=0.2; sys_platform=="win32"

# macOS (uncomment if needed)
# pyobjc-framework-CoreAudio>=7.0; sys_platform=="darwin"

# Linux (uncomment if native rtaudio support is required)
# python-rtaudio>=1.1; sys_platform=="linux"

# Alternative essentia installation
# Uncomment if regular essentia fails:
# essentia-tensorflow>=2.1b5

# MIDI and MusicXML parsing alternatives
mido>=1.2
python-rtmidi>=1.1

# Additional music analysis tools
madmom>=0.16
mir-eval>=0.6