# TuttiBot - Music Analysis Pipeline

TuttiBot is a complete music analysis system that processes both audio recordings and musical scores to extract comprehensive features for music performance evaluation and analysis.

## What TuttiBot Does

The pipeline takes two inputs:
- **Audio file**: Your music recording (WAV, MP3, FLAC, etc.)
- **Score file**: The musical score (PDF, MusicXML, or MIDI)

And produces:
- Cleaned and segmented audio
- Extracted musical features from both audio and score
- Performance analysis and comparison data
- Organized output with all intermediate results

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd TuttiBot

# Install Python dependencies
pip install -r requirements.txt

# Install Audiveris (for PDF processing)
# See installation section below

# Run the pipeline
python main.py your_audio.wav your_score.pdf
```

## Installation Guide

### 1. Python Dependencies

First, install all Python packages:

```bash
pip install -r requirements.txt
```

**Important**: If you encounter NumPy version conflicts with essentia-tensorflow, run:
```bash
pip install numpy==1.26.4
```

### 2. System Dependencies

#### FFmpeg (Required)
TuttiBot uses FFmpeg for audio processing:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH

#### Audiveris (Required for PDF processing)

Audiveris converts PDF sheet music to MusicXML. This is the trickiest part but essential for PDF support.

**Download and Install:**
1. Go to https://github.com/Audiveris/audiveris/releases
2. Download the latest release (we tested with v5.6.2)
3. Extract to `/opt/audiveris/` (Linux/Mac) or `C:\Program Files\Audiveris\` (Windows)

**Linux Installation:**
```bash
# Download Audiveris
wget https://github.com/Audiveris/audiveris/releases/download/5.6.2/Audiveris-5.6.2.tar.gz
tar -xzf Audiveris-5.6.2.tar.gz
sudo mv Audiveris-5.6.2 /opt/audiveris

# Make executable
sudo chmod +x /opt/audiveris/bin/Audiveris

# Test installation
/opt/audiveris/bin/Audiveris -help
```

**Troubleshooting Audiveris:**
- If you see "Audiveris not found" errors, check that `/opt/audiveris/bin/Audiveris` exists
- The pipeline automatically detects Audiveris in standard locations
- PDF processing will be skipped if Audiveris isn't found (MusicXML and MIDI will still work)

## Usage

### Basic Usage

```bash
python main.py <audio_file> <score_file>
```

### Supported Formats

**Audio formats:**
- WAV (recommended)
- MP3
- FLAC
- AAC
- OGG

**Score formats:**
- PDF (requires Audiveris)
- MusicXML (.xml, .musicxml)
- Compressed MusicXML (.mxl)
- MIDI (.mid, .midi)

### Examples

```bash
# With PDF score
python main.py recording.wav sheet_music.pdf

# With MusicXML score
python main.py performance.mp3 composition.musicxml

# With MIDI file
python main.py audio.wav song.mid
```

## Understanding the Output

TuttiBot creates a timestamped output directory with organized results:

```
tuttibot_output_20250816_123456/
├── 01_input_layer/          # Standardized inputs
│   ├── standardized_audio.wav
│   ├── standardized_score.xml
│   └── input_metadata.json
├── 02_processing_layer/     # Audio processing results
│   ├── processed/
│   │   ├── *_processed.wav
│   │   ├── *_audio_segments.json
│   │   └── *_music_features.json
│   └── processing_metadata.json
├── 03_extraction_layer/     # Feature extraction
│   ├── audio_features.json  # ~4-5MB of audio features
│   ├── score_features.json  # Score analysis features
│   └── extraction_metadata.json
└── 04_final_results/        # Key outputs for easy access
    ├── final_audio.wav
    ├── final_score.xml
    ├── final_audio_features.json
    ├── final_score_features.json
    └── pipeline_summary.json
```

## Common Issues and Solutions

### 1. "Audiveris not found" Error
**Problem**: PDF files can't be processed
**Solution**: 
- Install Audiveris as described above
- Ensure it's in `/opt/audiveris/bin/Audiveris` (Linux/Mac)
- Test with: `/opt/audiveris/bin/Audiveris -help`
- Use MusicXML files as a workaround

### 2. NumPy Version Conflicts
**Problem**: Import errors with essentia-tensorflow
**Solution**: 
```bash
pip install numpy==1.26.4
```

### 3. FFmpeg Not Found
**Problem**: Audio processing fails
**Solution**: Install FFmpeg system-wide (see installation section)

### 4. Memory Issues with Large Files
**Problem**: Pipeline crashes with large audio files
**Solution**: 
- Use shorter audio clips for testing
- Ensure sufficient RAM (8GB+ recommended)
- Convert audio to WAV format first

### 5. Permission Errors
**Problem**: Can't write to output directory
**Solution**: Run from a writable directory, not system folders

## Performance Notes

- **Typical processing time**: 1-2 minutes for a 3-4 minute song
- **Memory usage**: 2-4GB peak during processing
- **PDF processing**: Adds 30-60 seconds depending on PDF complexity
- **Output size**: ~5-10MB total for a typical song

## Development Tips

### Testing with Sample Files
We recommend testing with these file combinations:
1. Short audio file (30-60 seconds) + simple PDF
2. Full song + MusicXML file
3. Instrumental recording + MIDI file

### Debugging
If something goes wrong:
1. Check the console output for specific error messages
2. Look at the intermediate files in the output directory
3. Test each input file type separately
4. Verify all dependencies are installed

### Adding New Features
The pipeline is modular:
- `INPUT3_LAYER/`: Input standardization
- `PROCESSING_LAYER/`: Audio cleaning and music analysis
- `EXTRACTION_LAYER/`: Advanced feature extraction

## System Requirements

- **Python**: 3.8+ (tested with 3.10)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 1GB free space for dependencies, ~50MB per analysis
- **OS**: Linux (primary), macOS, Windows (with some limitations)

## Getting Help

If you're stuck:
1. Check this README thoroughly
2. Verify all dependencies are correctly installed
3. Try with a simple test case first
4. Check the output logs for specific error messages

The most common issue is Audiveris installation, so focus on that first if you're having PDF problems.

## Architecture Overview

TuttiBot uses a three-layer architecture:

1. **INPUT3_LAYER**: Standardizes audio (44.1kHz WAV) and converts scores to MusicXML
2. **PROCESSING_LAYER**: Cleans audio, segments it, and extracts basic music features
3. **EXTRACTION_LAYER**: Performs advanced feature analysis on both audio and score

Each layer produces intermediate results, making the pipeline debuggable and the outputs reusable for other projects.
