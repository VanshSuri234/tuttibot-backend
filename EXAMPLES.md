# TuttiBot Quick Start Examples

## Test the Installation

```bash
# 1. Test with existing files (if available)
python main.py INPUT_LAYER/audio.wav data/original/standardized_score.xml

# 2. Check if Audiveris is working
/opt/audiveris/bin/Audiveris -help

# 3. Test Python imports
python3 -c "import librosa, music21, aubio; print('All imports OK')"
```

## Common Commands

```bash
# Run the automatic installation script
./install.sh

# Install just Python dependencies
pip install -r requirements.txt

# Fix NumPy compatibility if needed
pip install numpy==1.26.4

# Test with different file types
python main.py song.wav score.pdf          # PDF + audio
python main.py recording.mp3 sheet.xml     # MusicXML + audio
python main.py audio.flac composition.mid  # MIDI + audio
```

## Troubleshooting Commands

```bash
# Check Python version
python3 --version

# Check installed packages
pip list | grep -E "(librosa|music21|aubio|essentia)"

# Test FFmpeg
ffmpeg -version

# Check Audiveris
ls -la /opt/audiveris/bin/

# Check TuttiBot modules
python3 -c "from INPUT3_LAYER.input_layer import MusicInputLayer; print('INPUT3_LAYER OK')"
python3 -c "from PROCESSING_LAYER.processing_layer import ProcessingLayer; print('PROCESSING_LAYER OK')"
python3 -c "from EXTRACTION_LAYER.extraction_layer import AudioFeatureExtractor; print('EXTRACTION_LAYER OK')"
```

## Expected Output Structure

After running `python main.py audio.wav score.pdf`, you should see:

```
tuttibot_output_YYYYMMDD_HHMMSS/
├── 01_input_layer/
├── 02_processing_layer/
├── 03_extraction_layer/
└── 04_final_results/
```

## Quick Validation

Run this to validate everything is working:

```bash
# Should show all green checkmarks
./install.sh

# Should complete without errors (use small test files)
python main.py INPUT_LAYER/audio.wav data/original/standardized_score.xml
```
