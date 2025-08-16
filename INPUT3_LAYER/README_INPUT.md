# Simple Installation Guide

Clean, straightforward setup using Audiveris directly without Docker or complex dependencies.

## 📋 Requirements

1. **Python 3.7+**
2. **Audiveris OMR Software** (separate installation)
3. **Basic Python packages** (librosa, soundfile)

## 🚀 Quick Setup

### Step 1: Install Audiveris

**Download Audiveris from official releases:**
https://github.com/Audiveris/audiveris/releases

**Choose your installer:**
- **Windows**: `Audiveris-<version>-windows-x86_64.msi`
- **macOS**: `Audiveris-<version>-macosx-x86_64.dmg` or `macosx-arm64.dmg`
- **Linux**: `Audiveris-<version>-linux-x86_64.deb`

**Install normally** - the installer includes everything (Java runtime, etc.)

### Step 2: Verify Audiveris CLI

Open terminal/command prompt and test:

```bash
# Windows
"C:\Program Files\Audiveris\bin\Audiveris.bat" -help

# macOS
/Applications/Audiveris.app/Contents/MacOS/Audiveris -help

# Linux  
/opt/audiveris/bin/Audiveris -help

# Or if it's in your PATH
audiveris -help
```

You should see Audiveris help text starting with "Audiveris Version: X.X.X"

### Step 3: Install Python Dependencies

```bash
# Create virtual environment
python -m venv music_eval_env

# Activate it
# Windows:
music_eval_env\Scripts\activate
# macOS/Linux:
source music_eval_env/bin/activate

# Install minimal requirements
pip install -r requirements_simple.txt
```

### Step 4: Test the System

```bash
python input_layer_simple.py test_audio.wav test_score.pdf
```

## 📁 File Structure

```
your-project/
├── music_eval_env/          # Virtual environment
├── input_layer_simple.py    # Main input layer code
├── requirements_simple.txt  # Minimal Python dependencies
├── INSTALL_SIMPLE.md        # This guide
└── your_files/              # Your audio and score files
```

## 🎯 Usage Examples

### Basic Usage
```bash
python input_layer_simple.py recording.wav sheet_music.pdf
```

### Different File Formats
```bash
# Audio conversion + PDF processing
python input_layer_simple.py song.mp3 score.pdf

# No conversion needed
python input_layer_simple.py audio.wav score.xml
python input_layer_simple.py performance.wav composition.mid
```

### Programmatic Usage
```python
from input_layer_simple import MusicInputLayer

# Initialize
input_layer = MusicInputLayer()

# Process files
results = input_layer.process_inputs("audio.wav", "score.pdf")

if results['overall_success']:
    print(f"Audio: {results['audio']['output_path']}")
    print(f"Score: {results['score']['output_path']}")
```

## ⚙️ How It Works

### Audio Processing
- Uses **librosa** for format detection and resampling
- Converts to 44.1kHz/16-bit WAV if needed
- Handles multi-channel audio (reduces to ≤5 channels)

### Score Processing  
- **MIDI/MusicXML**: Pass-through (no processing)
- **PDF**: Direct Audiveris CLI call:
  ```bash
  audiveris -batch -export -output output_dir input.pdf
  ```

### Audiveris Command Explained
- `-batch`: Run without GUI (headless mode)
- `-export`: Generate MusicXML output files
- `-output <dir>`: Specify output directory
- `<input.pdf>`: Input PDF file to process

## 🔧 Troubleshooting

### "Audiveris not found"
1. **Check installation**: Verify Audiveris is installed correctly
2. **Test manually**: Run audiveris command from terminal
3. **Check paths**: The code automatically searches common installation paths
4. **Add to PATH**: Add Audiveris bin directory to your system PATH

### Common Installation Paths
- **Windows**: `C:\Program Files\Audiveris\bin\Audiveris.bat`
- **macOS**: `/Applications/Audiveris.app/Contents/MacOS/Audiveris`  
- **Linux**: `/opt/audiveris/bin/Audiveris`

### Audio Processing Issues
```bash
# Test audio libraries
python -c "import librosa, soundfile; print('Audio libraries OK')"
```

### PDF Processing Issues
1. **Test Audiveris directly**:
   ```bash
   audiveris -batch -export -output test_output sample.pdf
   ```
2. **Check PDF quality**: Higher resolution PDFs work better
3. **Simpler scores**: Complex orchestral scores may have issues

## 🎵 Supported Formats

### Input
- **Audio**: WAV, MP3, FLAC, AAC, OGG
- **Score**: PDF (via Audiveris), MIDI (.mid, .midi), MusicXML (.xml, .musicxml, .mxl)

### Output  
- **Audio**: 44.1kHz 16-bit WAV
- **Score**: MusicXML (.xml)

## 💡 Why This Approach?

### ✅ Advantages
- **Simple**: Only 3 Python packages + Audiveris
- **Reliable**: Audiveris is enterprise-grade OMR software
- **No Docker**: Works on any system where Audiveris runs
- **Clean**: No complex dependency chains
- **Fast**: Direct CLI calls are efficient

### 📝 Notes
- **Audiveris Quality**: Professional-grade OMR, better than most alternatives
- **CLI Mode**: Audiveris has excellent command-line support with -batch and -export options
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **HPC Compatible**: No GUI dependencies, works on servers

## 🚀 For HPC/IIIT ADA

This version is perfect for HPC environments:

1. **No Docker required** - most HPC systems don't allow Docker
2. **Minimal dependencies** - just Python packages + Audiveris binary
3. **Headless operation** - uses Audiveris `-batch` mode
4. **CPU-based** - works without GPU (though Audiveris can use GPU if available)

### HPC Installation
```bash
# Load modules (adjust for your HPC)
module load python/3.9

# Install Audiveris (admin may need to install system-wide)
# Or download portable version to your home directory

# Install Python dependencies
pip install --user librosa soundfile numpy scipy

# Test
python input_layer_simple.py audio.wav score.pdf
```

This is exactly what you wanted - simple, direct, no fallbacks, just audio processing + Audiveris CLI for PDF to MusicXML conversion!