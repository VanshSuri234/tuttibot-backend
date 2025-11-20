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

## Mathematical Formulation

This section documents the core formulas underpinning the processing steps. Symbols use standard DSP notation.

### RMS Energy and Noise Heuristic

- Frame-level RMS (frame length $N$, hop $H$):

$$
E_{\text{rms}}[m] = \sqrt{\frac{1}{N} \sum_{n=0}^{N-1} x[n + mH]^2}
$$

- Noise baseline (used as a heuristic trigger for spectral denoising):

$$
T_{\text{noise}} = \operatorname{Percentile}_{10\%}\big( E_{\text{rms}}[m] \big)
$$

- Apply noise reduction if $T_{\text{noise}} > \tau$, with default $\tau = 0.5$.

### Peak Level Heuristic (for normalization decision)

- Peak level estimate:

$$
L_{\text{peak}} = 20 \log_{10}\big(\max_n |x[n]| + \varepsilon\big), \quad \varepsilon \approx 10^{-10}
$$

- Normalization is requested if $\big|L_{\text{peak}} - L_{\text{target}}\big| > 3\,\mathrm{dB}$. Here $L_{\text{target}}$ is the target loudness (we use $-23\,\mathrm{LUFS}$ as the pipeline target). Note: LUFS is not identical to sample peak; this heuristic only decides whether to normalize, the actual gain below follows EBU R128.

### Spectral Gating Noise Reduction (Stationary)

- Short-time Fourier transform (STFT):

$$
X(k,m) = \sum_{n} x[n]\, w[n-mH] e^{-j2\pi kn/N}
$$

- Stationary noise magnitude estimate $\hat N(k)$ (estimated from low-energy frames or running minima by the library).

- Gain mask with reduction proportion $p \in [0,1]$ (default $p=0.8$):

$$
M(k,m) = \max\left( 1 - p\, \frac{\hat N(k)}{|X(k,m)| + \delta},\, 0 \right), \quad \delta \ll 1
$$

- Apply mask and invert:

$$
Y(k,m) = M(k,m)\, X(k,m), \quad y[n] = \operatorname{iSTFT}\{Y(k,m)\}
$$

This formulation captures the essence of the spectral gating used by the underlying library (noisereduce) in stationary mode.

### EBU R128 Loudness Normalization (Gain Application)

- ffmpeg-normalize computes integrated loudness $L_I$ (via K-weighting and gating per EBU R128). We apply a broadband gain $G$ in dB to reach target $L_T$ (default $-23\,\mathrm{LUFS}$):

$$
G = L_T - L_I, \qquad y[n] = 10^{G/20}\, x[n]
$$

Note: The full computation of $L_I$ involves K-weighting filters and relative/absolute gating as per EBU R128; this layer delegates that to ffmpeg-normalize.

### Energy-based Segmentation

Let $E_{\text{rms}}[m]$ be the frame energy as above and $\theta$ the energy threshold (auditok parameter). Define the activity indicator:

$$
B[m] = \begin{cases}
1, & E_{\text{rms}}[m] \ge \theta \\
0, & \text{otherwise}
\end{cases}
$$

Segments are maximal contiguous regions where $B[m]=1$, subject to constraints:

$$
  ext{min\_dur} \le (m_{\text{end}}-m_{\text{start}})\frac{H}{f_s} \le \text{max\_dur}, \quad \text{and} \quad \text{max\_silence within a segment} \le S_{\max}.
$$

In our defaults: min_dur = 0.2 s, max_dur = 10 s, max_silence = 0.5 s, and an energy threshold corresponding to `energy_threshold=55` in auditok.

### Optional: MIDI Pitch and Duration Relations

- MIDI to frequency:

$$
f(\text{MIDI}) = 440\,\cdot\, 2^{(\text{MIDI}-69)/12}
$$

- Quarter-length to seconds (given tempo $\text{BPM}$ approximating quarter-notes per minute):

$$
t_{\text{sec}} = \frac{\text{quarterLength}}{\text{BPM}} \times 60
$$

These relations are useful for downstream time-mapping; this layer primarily parses symbolic data via music21 without re-synthesizing timing.

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
pip install -r requirements_processing.txt
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
processor = ProcessingLayer()

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

### Integration with the Hybrid Pipeline

When running via `main_hybrid_v02.py`, the processing layer is instantiated with the pipeline’s shared output directory:

```python
from processing_layer import ProcessingLayer

processing_output_dir = os.path.join(output_dir, '02_processing_layer')
processor = ProcessingLayer(shared_output_dir=processing_output_dir)
result = processor.process(audio_path, score_path)
```

This yields a consistent folder structure under `02_processing_layer/` with both `original/` and `processed/` subfolders, and mirrored copies in the shared directory for downstream layers.

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
data/
├── original/
│   ├── <input_audio>                 # Original audio
│   └── <input_music>                 # Original MIDI/XML
└── processed/
  ├── <base>_processed.wav          # Final processed audio (always created)
  ├── <base>_denoised.wav           # Intermediate (if noise reduction applied)
  ├── <base>_normalized.wav         # Intermediate (if normalization applied)  
  ├── <base>_audio_segments.json    # Segmentation output
  └── <base>_music_features.json    # Music features output

shared_output_dir/
└── processed/                         # Mirrored JSON/audio for other layers
  ├── <base>_processed.wav
  ├── <base>_audio_segments.json
  └── <base>_music_features.json
```

Notes:
- Intermediate files are cleaned automatically; the denoised/normalized files above may be transient.
- The final processed audio is always created for consistency, even if no processing was needed.

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

### Audio Quality Check Heuristics
- Noise estimate: bottom 10% of RMS frame energies provides a baseline; flagged if above `noise_reduction_threshold` (default 0.5)
- Normalization: peak dB compared to `normalization_target` (default -23 LUFS) with ±3 dB tolerance
- Segmentation: currently always enabled to produce timing regions for downstream alignment

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

3. **Requirements file name**
  - Use `requirements_processing.txt` in this folder to install dependencies.

4. **PyAudio installation (optional)**
   ```bash
   # Ubuntu: sudo apt install portaudio19-dev
   # macOS: brew install portaudio  
   # Then: pip install pyaudio
   ```

5. **Memory issues with large files**
   - Process files in smaller chunks
   - Increase system memory or use streaming mode

For additional support, refer to the individual repository documentation linked above.