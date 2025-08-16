# Audio-Music Processing Layer

A comprehensive Python processing layer that handles live audio performance files (WAV) and music sheet files (MIDI/XML) through noise reduction, normalization, segmentation, and feature extraction.

## Features

### Audio Processing
- **Noise Reduction**: Spectral gating algorithm for removing background noise
- **Normalization**: EBU R128 loudness normalization for consistent audio levels  
- **Segmentation**: Energy-based audio activity detection to identify musical segments

### Music Sheet Processing  
- **Note Extraction**: Parse MIDI/XML files to extract individual notes with timing
- **Musical Metadata**: Extract key signatures, time signatures, tempo, and tuning information
- **Instrument Detection**: Identify instruments used in the musical score

## Repository Dependencies & Algorithms

| Component | Repository | Algorithm Used |
|-----------|------------|----------------|
| **Noise Reduction** | [timsainb/noisereduce](https://github.com/timsainb/noisereduce) | Spectral gating with frequency-varying thresholds |
| **Normalization** | [slhck/ffmpeg-normalize](https://github.com/slhck/ffmpeg-normalize) | EBU R128 loudness normalization (two-pass) |
| **Segmentation** | [amsehili/auditok](https://github.com/amsehili/auditok) | Energy-based audio activity detection |
| **Music Parsing** | music21 | Comprehensive musical notation analysis |

## Algorithm Details

### 1. Noise Reduction (Spectral Gating)
- **Method**: Computes spectrogram and estimates noise threshold per frequency band
- **Process**: Creates frequency-varying gate mask to attenuate noise below threshold
- **Implementation**: Stationary noise reduction with 80% noise reduction proportion

### 2. Audio Normalization (EBU R128)
- **Method**: Two-pass EBU R128 loudness normalization procedure
- **Target**: -23 LUFS (Loudness Units relative to Full Scale)
- **Process**: First pass analyzes loudness, second pass applies correction

### 3. Audio Segmentation (Energy-based)
- **Method**: RMS energy calculation with adaptive thresholding
- **Parameters**: Min duration 200ms, max silence 500ms, energy threshold 55
- **Output**: Time-stamped audio segments with start/end boundaries

### 4. Music Feature Extraction
- **Method**: AST (Abstract Syntax Tree) parsing of music notation
- **Features**: Notes, rhythms, key/time signatures, tempo, instruments
- **Format**: Structured JSON output with pitch, duration, and timing data

## Installation

### Prerequisites
```bash
# Install ffmpeg (required for audio normalization)
# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Windows: Download from https://ffmpeg.org/download.html
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

### Additional Setup for music21
```bash
# Configure music21 (one-time setup)
python -c "import music21; music21.configure.run()"
```

## Usage

### Basic Usage
```python
from processing_layer import ProcessingLayer

# Initialize processor
processor = ProcessingLayer(output_dir="output")

# Process audio and music files
result = processor.process(
    audio_path="performance.wav",
    music_path="sheet_music.mid"
)

# Access results
print(f"Found {len(result.audio_segments)} audio segments")
print(f"Extracted {len(result.music_features.notes)} musical notes")
print(f"Key: {result.music_features.key_signature}")
print(f"Tempo: {result.music_features.tempo} BPM")
```

### Advanced Configuration
```python
from processing_layer import AudioProcessor, MusicProcessor, ProcessingLayer

# Custom audio processor settings
audio_proc = AudioProcessor(
    noise_reduction_threshold=0.3,  # Lower = more aggressive
    normalization_target=-16.0,     # Target loudness in LUFS
    segmentation_energy_threshold=45 # Lower = more sensitive
)

# Initialize with custom processor
processor = ProcessingLayer()
processor.audio_processor = audio_proc

result = processor.process("audio.wav", "music.xml")
```

### Output Structure
```python
# ProcessingResult contains:
result.audio_path              # Original audio file path
result.music_path              # Original music file path  
result.processed_audio_path    # Path to processed audio
result.audio_segments          # List of AudioSegment objects
result.music_features          # MusicFeatures object
result.processing_metadata     # Processing statistics

# Audio segments
for segment in result.audio_segments:
    print(f"Segment: {segment.start_time:.2f}s - {segment.end_time:.2f}s")

# Music features  
features = result.music_features
for note in features.notes[:5]:  # First 5 notes
    print(f"Note: {note['pitch']} (MIDI {note['midi_number']}) "
          f"Duration: {note['duration']} beats")
```

## File Format Support

### Audio Input
- **WAV**: Uncompressed audio (recommended)
- **MP3, OGG, FLAC**: Supported via librosa/soundfile
- **Sample rates**: 16kHz, 22kHz, 44.1kHz, 48kHz, 96kHz

### Music Notation Input
- **MIDI**: .mid, .midi files
- **MusicXML**: .xml, .musicxml, .mxl (compressed)
- **Other**: ABC notation, Humdrum **kern files

## Output Files

The processor creates several output files in the specified directory:

```
output/
├── audio_processed.wav          # Final processed audio
├── audio_denoised.wav          # After noise reduction (if applied)
├── audio_normalized.wav        # After normalization (if applied)  
└── audio_processing_result.json # Complete results in JSON format
```

## Performance Optimization

### Audio Quality Pre-check
The system automatically analyzes input audio to determine which processing steps are needed:
- **Noise Reduction**: Applied only if noise levels exceed threshold
- **Normalization**: Applied only if loudness deviates significantly from target
- **Segmentation**: Always applied for segment detection

### Processing Speed Tips
- Use WAV format for fastest audio loading
- For large files, consider pre-segmenting audio
- MIDI files process faster than MusicXML
- Disable unnecessary processing steps via quality check thresholds

## Error Handling

The system gracefully handles common issues:
- **Missing dependencies**: Clear installation instructions
- **Corrupted files**: Fallback to default values
- **Unsupported formats**: Automatic format detection and conversion
- **Processing failures**: Detailed error messages and partial results

## Example Applications

1. **Music Performance Analysis**: Compare live performance against sheet music
2. **Audio Preprocessing**: Prepare recordings for machine learning models
3. **Music Education**: Automated analysis of student performances
4. **Music Information Retrieval**: Extract features for music recommendation systems

## License & Citations

When using this processing layer, please cite the underlying repositories:

```bibtex
@software{noisereduce,
  author = {Tim Sainburg},
  title = {timsainb/noisereduce: v1.0},
  year = {2019},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.3243139}
}

@software{ffmpeg_normalize,
  author = {Werner Robitza},
  title = {slhck/ffmpeg-normalize},
  url = {https://github.com/slhck/ffmpeg-normalize}
}

@software{auditok,
  author = {Amine Sehili},
  title = {amsehili/auditok},
  url = {https://github.com/amsehili/auditok}
}

@software{music21,
  author = {Michael Scott Cuthbert and Christopher Ariza},
  title = {music21: A Toolkit for Computer-Aided Musicology},
  url = {https://web.mit.edu/music21/}
}
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   ```bash
   # Install ffmpeg and add to PATH
   # Verify installation: ffmpeg -version
   ```

2. **music21 configuration**  
   ```bash
   python -c "import music21; music21.configure.run()"
   ```

3. **PyAudio installation (optional)**
   ```bash
   # Ubuntu: sudo apt install portaudio19-dev
   # macOS: brew install portaudio  
   # Then: pip install pyaudio
   ```

4. **Memory issues with large files**
   - Process files in smaller chunks
   - Increase system memory or use streaming mode

For additional support, refer to the individual repository documentation linked above.