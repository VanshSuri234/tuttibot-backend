# Music Performance Analysis - Extraction Layer

This extraction layer processes both live performance audio and musical score data to extract comprehensive features for performance analysis, error detection, and alignment.

## Overview

The extraction layer serves as the critical bridge between raw input data and analysis, extracting:

**From Performance Audio:**
- Pitch detection and fundamental frequency tracking
- Onset detection and timing analysis  
- Tempo estimation and beat tracking
- Spectral features (MFCC, chroma, spectral centroid, etc.)
- Harmonic/percussive separation
- Energy and dynamics analysis

**From Musical Scores (MIDI/XML):**
- Expected pitches and rhythmic patterns
- Tempo markings and time signatures
- Key signatures and chord progressions
- Dynamic markings and articulation symbols
- Structural analysis and phrase boundaries

## Repository References

This implementation leverages several high-quality open-source libraries:

- **[aubio](https://github.com/aubio/aubio)** - Real-time audio analysis with onset detection, pitch tracking, and tempo estimation
- **[essentia](https://github.com/MTG/essentia)** - Comprehensive music analysis and feature extraction toolkit  
- **[librosa](https://github.com/bmcfee/librosa)** - Python library for audio and music signal analysis
- **[music21](https://github.com/cuthbertLab/music21)** - Toolkit for computer-aided musicology and score analysis
- **[pretty_midi](https://github.com/craffel/pretty-midi)** - Utility functions for handling MIDI data

## Installation

### Prerequisites

- **Python 3.7 or higher** (Python 3.8+ recommended)
- **Git** (for cloning repositories)
- **Audio system libraries** (platform-dependent)

### Quick Installation

```bash
# Clone or download the extraction layer code
# Create virtual environment
python -m venv extraction_env
source extraction_env/bin/activate  # On Windows: extraction_env\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### Manual Installation (Alternative)

If you prefer to install packages individually:

```bash
# Core dependencies
pip install librosa>=0.10.0 music21>=9.1.0 pretty-midi>=0.2.10
pip install aubio>=0.4.9 essentia-tensorflow>=2.1b6.dev1034
pip install numpy>=1.21.0 scipy>=1.7.0 pandas>=1.3.0

# Additional utilities
pip install soundfile audioread tqdm jsonschema
```

### Platform-Specific Installation Notes

**Windows:**
```bash
# Install Visual Studio Build Tools if needed for aubio
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Alternative for aubio:
conda install -c conda-forge aubio

# For essentia issues:
conda install -c MTG essentia
```

**macOS:**
```bash
# Install system audio libraries via Homebrew
brew install portaudio libsndfile

# Then install Python packages
pip install -r requirements.txt
```

**Linux (Ubuntu/Debian):**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev
sudo apt-get install libsndfile1-dev libfftw3-dev libavcodec-dev libavformat-dev

# Install Python packages
pip install -r requirements.txt
```

### Troubleshooting Installation

**Common Issues:**

1. **aubio fails to install:**
   ```bash
   # Try conda instead
   conda install -c conda-forge aubio
   
   # Or system package manager
   # Ubuntu: sudo apt-get install python3-aubio
   # macOS: brew install aubio
   ```

2. **essentia-tensorflow fails:**
   ```bash
   # Try regular essentia
   pip install essentia
   
   # Or conda
   conda install -c MTG essentia
   ```

3. **music21 configuration needed:**
   ```python
   import music21
   music21.configure.run()  # Follow setup prompts
   ```

### Verification

Test your installation:

```bash
python -c "
import librosa, music21, pretty_midi, aubio, essentia
print('All core libraries installed successfully!')
"
```

## Input File Structure

The extraction layer expects the following input files from the processing layer:

```
data/
├── processed/
│   ├── input_processed.wav           # Clean, normalized audio (11MB)
│   ├── input_audio_segments.json     # Temporal segmentation (2.4KB)
│   └── input_music_features.json     # Score-derived features (406KB)
└── original/
    └── xml_score.musicxml            # Original score file (1.3MB)
    # OR: score.mid                   # MIDI alternative
```

## Usage

### Basic Usage

```python
from extraction_layer import ExtractionLayer

# Initialize the extraction layer
extractor = ExtractionLayer()

# Define input files
audio_file = "data/processed/input_processed.wav"
segments_file = "data/processed/input_audio_segments.json"  
score_file = "data/original/xml_score.musicxml"
score_json_file = "data/processed/input_music_features.json"

# Extract all features
summary = extractor.process_all(
    audio_file=audio_file,
    segments_file=segments_file,
    score_file=score_file,
    score_json_file=score_json_file,
    output_dir="data/extracted"
)
```

### Command Line Usage

```bash
# Run the extraction layer
python extraction_layer.py

# The script will automatically look for files in:
# - data/processed/input_processed.wav
# - data/processed/input_audio_segments.json  
# - data/original/xml_score.musicxml
# - data/processed/input_music_features.json
```

### Advanced Usage

```python
# Process only performance audio
performance_output = extractor.process_performance_data(
    audio_file="data/processed/input_processed.wav",
    segments_file="data/processed/input_audio_segments.json",
    output_dir="data/extracted"
)

# Process only score data  
score_output = extractor.process_score_data(
    score_file="data/original/xml_score.musicxml",
    score_json_file="data/processed/input_music_features.json", 
    output_dir="data/extracted"
)

# Custom configuration
extractor = ExtractionLayer(
    sample_rate=44100,  # Higher sample rate for better pitch resolution
    hop_length=256      # Smaller hop for finer time resolution
)

# Access segment-aware features
performance_features = extractor.audio_extractor.extract_features(
    audio_file, segments_file
)
print(f"Found {performance_features.num_segments} audio segments")
print(f"Total active duration: {performance_features.total_active_duration:.2f}s")
```

### JSON Data Integration

The extraction layer **prioritizes and fully utilizes** the preprocessed JSON files:

**Audio Segments JSON (`input_audio_segments.json`):**
- **12 segments** spanning 4.65s–124.65s with confidence scores
- **Active region detection** - focuses analysis on musical content
- **Segment-level features** - tempo, energy, spectral analysis per segment
- **Silence filtering** - excludes quiet regions from feature extraction

**Score Features JSON (`input_music_features.json`):**
- **2517 notes** with pitch, timing, velocity from score analysis
- **Musical metadata** - G major, 2/4 time, 120 BPM, piano
- **Structural information** - phrases, sections, dynamics
- **Harmony data** - chord progressions, key changes

**Smart Data Prioritization:**
1. **Primary**: JSON files (preprocessed, cleaned data)
2. **Secondary**: Direct extraction (validation and supplementation)  
3. **Fallback**: Default values (robustness)

```python
# Example of JSON integration in action
extractor = ExtractionLayer()

# The extractor automatically:
# 1. Loads segment boundaries from JSON
# 2. Focuses pitch detection on active regions
# 3. Uses existing note data as ground truth
# 4. Supplements with additional feature extraction
# 5. Validates consistency between sources

features = extractor.process_all(audio_file, segments_file, score_file, score_json_file)
```

## Output Structure

The extraction layer generates structured JSON files containing features for analysis:

```
data/extracted/
├── performance_features.json        # Live performance features
├── score_features.json             # Musical score features  
└── extraction_summary.json         # Processing summary
```

### Performance Features Output

```json
{
  "pitch_contour": [440.0, 442.1, 443.8, ...],
  "pitch_confidence": [0.95, 0.92, 0.88, ...],
  "onset_times": [0.5, 1.2, 2.1, 2.8, ...],
  "tempo_bpm": 120.5,
  "tempo_confidence": 0.91,
  "spectral_centroid": [1500.2, 1520.8, 1485.3, ...],
  "mfcc_features": [
    [-15.2, 8.3, -2.1, 4.7, ...],  // Frame 1 MFCCs
    [-14.8, 8.9, -1.8, 4.2, ...],  // Frame 2 MFCCs
    ...
  ],
  "chroma_features": [
    [0.8, 0.1, 0.3, 0.2, ...],     // Frame 1 chroma (C, C#, D, ...)
    [0.7, 0.2, 0.4, 0.1, ...],     // Frame 2 chroma
    ...
  ],
  "rms_energy": [0.05, 0.08, 0.12, 0.09, ...],
  "harmonic_content": [0.6, 0.7, 0.65, 0.8, ...],
  "percussive_content": [0.3, 0.2, 0.25, 0.1, ...],
  "segment_analysis": [
    {
      "segment_id": 0,
      "start_time": 4.65,
      "end_time": 15.32,
      "confidence": 0.95,
      "activity_level": "active",
      "rms_energy": 0.08
    },
    ...
  ],
  "active_regions": [[4.65, 15.32], [18.44, 35.12], ...],
  "num_segments": 12,
  "total_active_duration": 98.7,
  "duration": 125.4,
  "sample_rate": 22050
}
```

### Score Features Output

```json
{
  "expected_pitches": [60, 64, 67, 72, 69, ...],    // MIDI note numbers
  "pitch_classes": [0, 4, 7, 0, 9, ...],           // C, E, G, C, A, ...
  "key_signature": "G major", 
  "tempo_markings": [
    {"time": 0, "bpm": 120, "text": "Allegro moderato"}
  ],
  "time_signatures": ["2/4", "2/4", "2/4", ...],
  "chord_progressions": ["G", "Em", "C", "D", "G", ...],
  "note_onsets": [0.0, 0.5, 1.0, 1.5, 2.0, ...],
  "note_durations": [0.5, 0.5, 0.5, 0.5, 1.0, ...],
  "velocity_markings": [80, 75, 90, 85, 70, ...],
  "intervals": [4, 3, 5, -3, -2, ...],              // Semitone intervals
  "dynamic_markings": ["mf", "f", "mp", ...],
  "articulation_symbols": ["staccato", "legato", ...],
  "total_duration": 125.0,
  "num_voices": 1,
  "instrument_names": ["Piano"]
}
```

## Feature Descriptions

### Audio Features

| Feature | Description | Library | Use Case |
|---------|-------------|---------|----------|
| `pitch_contour` | Fundamental frequency over time | aubio/librosa | Pitch accuracy analysis |
| `onset_times` | Note onset timestamps | aubio/librosa | Timing analysis |
| `tempo_bpm` | Estimated tempo | librosa/essentia | Tempo consistency |
| `spectral_centroid` | Brightness of sound | librosa | Timbre analysis |
| `mfcc_features` | Mel-frequency coefficients | librosa | Timbre matching |
| `chroma_features` | Pitch class profiles | librosa | Harmonic analysis |
| `harmonic_content` | Harmonic vs percussive energy | librosa | Playing technique |
| `segment_analysis` | Per-segment feature statistics | Custom | Region-based analysis |
| `active_regions` | Time ranges with musical content | JSON integration | Focus analysis scope |

### Score Features

| Feature | Description | Library | Use Case |
|---------|-------------|---------|----------|
| `expected_pitches` | MIDI note numbers from score | music21/pretty_midi | Pitch error detection |
| `key_signature` | Musical key | music21 | Harmonic context |
| `tempo_markings` | Composer's tempo indications | music21 | Reference tempo |
| `chord_progressions` | Harmonic progression | music21 | Harmony analysis |
| `note_durations` | Expected note lengths | music21/pretty_midi | Rhythm analysis |
| `dynamic_markings` | Volume indications (f, p, etc.) | music21 | Expression analysis |

## Troubleshooting

### Common Installation Issues

**aubio installation fails:**
```bash
# Try conda instead of pip
conda install -c conda-forge aubio

# Or install system dependencies first (Ubuntu/Debian)
sudo apt-get install libaubio-dev aubio-tools
```

**essentia installation fails:**
```bash  
# Use conda-forge channel
conda install -c conda-forge essentia

# Or try the TensorFlow version
pip install essentia-tensorflow
```

**music21 configuration:**
```python
# First run may require configuration
import music21
music21.configure.run()  # Follow prompts for external software
```

### Common Runtime Issues

**File not found errors:**
- Ensure all input files exist and paths are correct
- Check that the processing layer has completed successfully
- Verify file permissions and directory structure

**Memory issues with large files:**
```python
# Use lower sample rate for large audio files
extractor = ExtractionLayer(sample_rate=16000)

# Process segments individually for very large files
segments_data = json.load(open(segments_file))
for segment in segments_data['segments']:
    # Process each segment separately
    pass
```

**JSON parsing errors:**
```python
# Validate JSON files before processing
import json
try:
    with open('input_audio_segments.json') as f:
        segments = json.load(f)
    print(f"Loaded {len(segments.get('segments', []))} segments")
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
```

**Missing features in output:**
- Some features require specific libraries (aubio, essentia)
- Install optional dependencies for complete feature extraction
- Check console output for library availability warnings
- Verify JSON files contain expected data structure

**Inconsistent feature dimensions:**
- Audio and score features may have different time scales
- Use frame_times in performance features for alignment
- Consider resampling or interpolation for matching

### Performance Optimization

**For faster processing:**
```python
# Lower sample rate (reduces computation)
extractor = ExtractionLayer(sample_rate=16000)

# Larger hop length (less time resolution, faster)
extractor = ExtractionLayer(hop_length=1024)

# Process only active segments
segments_data = json.load(open(segments_file))
active_segments = [s for s in segments_data['segments'] 
                  if s.get('confidence', 0) > 0.8]
```

**For higher accuracy:**
```python
# Higher sample rate (better frequency resolution)
extractor = ExtractionLayer(sample_rate=44100)

# Smaller hop length (better time resolution)
extractor = ExtractionLayer(hop_length=256)

# Use multiple extraction methods for validation
features = extractor.extract_features(audio_file, segments_file)
# Cross-validate aubio vs librosa results
```

**Memory-efficient processing:**
```python
# Process segments sequentially instead of entire file
def process_segments_individually(audio_file, segments_file):
    y, sr = librosa.load(audio_file)
    segments_data = json.load(open(segments_file))
    
    segment_features = []
    for segment in segments_data['segments']:
        start_sample = int(segment['start'] * sr)
        end_sample = int(segment['end'] * sr)
        segment_audio = y[start_sample:end_sample]
        
        # Process individual segment
        segment_feature = extract_segment_features(segment_audio, sr)
        segment_features.append(segment_feature)
    
    return segment_features
```

## Integration with Analysis Pipeline

The extracted features are designed for direct input to:

1. **Temporal Alignment Layer** - Maps audio segments to score positions
2. **Performance Analysis Layer** - Compares performed vs intended content  
3. **Error Detection Systems** - Identifies pitch, timing, and dynamic errors
4. **Real-time Applications** - Provides features for live performance feedback

## Contributing

When extending this extraction layer:

1. **Add new audio features** in `AudioFeatureExtractor._extract_*_features()` methods
2. **Add new score features** in `ScoreFeatureExtractor._extract_*_features()` methods  
3. **Update dataclasses** (`PerformanceFeatures`, `ScoreFeatures`) with new fields
4. **Add tests** for new functionality
5. **Update documentation** with feature descriptions

## Citation

If using this extraction layer in research, please cite the relevant libraries:

```bibtex
@inproceedings{librosa2015,
  title={librosa: Audio and Music Signal Analysis in Python},
  author={McFee, Brian and Raffel, Colin and Liang, Dawen and Ellis, Daniel PW and McVicar, Matt and Battenberg, Eric and Nieto, Oriol},
  booktitle={Proceedings of the 14th Python in Science Conference},
  year={2015}
}

@inproceedings{aubio2013,
  title={aubio, a library for audio and music analysis},
  author={Brossier, Paul M},
  booktitle={Proceedings of the 21st ACM international conference on Multimedia},
  year={2013}
}

@article{essentia2013,
  title={Essentia: An audio analysis library for music information retrieval},
  author={Bogdanov, Dmitry and Wack, Nicolas and G{\'o}mez, Emilia and Gulati, Sankalp and Herrera, Perfecto and Mayor, Oscar and Roma, Gerard and Salamon, Justin and Zapata, Jos{\'e} R and Serra, Xavier},
  journal={International Society for Music Information Retrieval Conference},
  year={2013}
}
```

## License

This code is provided for educational and research purposes. Please respect the licenses of the underlying libraries (aubio: GPL, essentia: AGPL, librosa: ISC, music21: LGPL, pretty_midi: MIT).