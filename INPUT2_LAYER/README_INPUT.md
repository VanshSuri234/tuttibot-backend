# Music Performance Evaluation System - Input Layer (Updated)

This module implements the input layer of a music performance evaluation system that compares live performances against their corresponding music scores. **Updated to address PDF conversion issues with multiple reliable methods.**

## Overview

The input layer handles two types of inputs:

1. **Audio Input**: WAV files containing live performance recordings
2. **Score Sheet Input**: Music notation in PDF, MIDI, or MusicXML formats

## Features

### Audio Processing
- **Format Validation**: Checks for 44.1 kHz sample rate, 16-bit depth, up to 5 channels
- **Automatic Conversion**: Attempts resampling and format conversion when needed
- **Multi-format Support**: Accepts WAV, FLAC, MP3, AAC, and OGG files
- **Channel Management**: Reduces multi-channel audio to maximum 5 channels

### Score Processing (Improved PDF Handling)
- **Multi-format Support**: Handles PDF, MIDI (.mid, .midi), and MusicXML (.xml, .musicxml, .mxl)
- **Multiple PDF Conversion Methods**:
  1. **Docker + Audiveris** (Primary - Most Reliable)
  2. **pdf2image + oemer** (Fallback)
- **Automatic Method Selection**: Detects available tools and uses the best method
- **MusicXML Validation**: Uses music21 to validate output files
- **Page-by-Page Processing**: Handles multi-page PDFs properly

## Installation

### Required Dependencies

```bash
pip install -r requirements.txt
```

### Individual Package Installation

```bash
# Core dependencies
pip install librosa soundfile pdf2image music21 docker

# PDF processing tools
pip install oemer

# System dependencies for pdf2image:
# Ubuntu/Debian:
sudo apt-get install poppler-utils

# macOS:
brew install poppler

# Windows: Download poppler binaries and add to PATH
```

### Docker Setup (Recommended for Best PDF Conversion)

```bash
# Install Docker Desktop first, then:
docker pull toprock/audiveris
```

## Usage

### Command Line Usage

```bash
python input_layer.py <audio_file> <score_file>
```

**Examples:**
```bash
# Process with PDF (will auto-select best conversion method)
python input_layer.py recording.wav sheet_music.pdf

# Process with MusicXML (no conversion needed)
python input_layer.py performance.mp3 score.musicxml

# Process with MIDI
python input_layer.py song.wav composition.mid
```

### Programmatic Usage

```python
from input_layer import MusicInputLayer

# Initialize the input layer (will detect available PDF methods)
input_layer = MusicInputLayer()

# Process both inputs
results = input_layer.process_inputs("audio.wav", "score.pdf")

if results['overall_success']:
    print(f"Audio ready: {results['audio']['output_path']}")
    print(f"Score ready: {results['score']['output_path']}")
    print(f"PDF method used: {results['score']['method_used']}")
else:
    print("Processing failed - check individual results")
```

## PDF Conversion Methods

### Method 1: Docker + Audiveris (Recommended)

**Best for**: High-quality, production use
- Uses Audiveris OMR engine - industry-standard with excellent recognition efficiency
- Handles complex scores and multi-page documents
- Most reliable results
- Requires Docker installation

**Setup:**
```bash
# Install Docker Desktop
# Pull the Audiveris image
docker pull toprock/audiveris
```

### Method 2: pdf2image + oemer (Fallback)

**Best for**: When Docker is not available
- Converts PDF pages to high-resolution images (300 DPI)
- Processes each page with oemer OMR
- Good for simpler scores
- Requires pdf2image and oemer packages

**Setup:**
```bash
pip install pdf2image oemer
# Plus system poppler installation (see above)
```

## Technical Details

### Audio Processing Algorithm

1. **Format Detection**: Uses librosa to analyze sample rate, channels, and bit depth
2. **Validation**: Checks against target format (44.1kHz/16-bit WAV, ≤5 channels)
3. **Resampling**: Uses librosa.resample() for sample rate conversion
4. **Channel Reduction**: Keeps first N channels if exceeding maximum
5. **Format Conversion**: Outputs 16-bit PCM WAV using soundfile

### PDF Processing Algorithm

#### Docker + Audiveris Method
1. **Container Setup**: Uses toprock/audiveris Docker image
2. **File Transfer**: Copies PDF to container input volume
3. **Processing**: Audiveris processes PDF with enterprise-grade OMR
4. **Output Retrieval**: Extracts MusicXML/MXL files from container
5. **Cleanup**: Automatically removes temporary files

#### pdf2image + oemer Method
1. **PDF to Images**: Converts each PDF page to 300 DPI PNG images
2. **Page Processing**: Runs oemer on each image individually
3. **Symbol Recognition**: Uses deep learning models for staff/note detection
4. **MusicXML Generation**: Outputs standard MusicXML for each page
5. **Multi-page Handling**: Combines or selects primary page result

### Audiveris vs oemer Comparison

| Feature | Audiveris (Docker) | oemer (Fallback) |
|---------|-------------------|------------------|
| **Accuracy** | Excellent | Good |
| **Speed** | Fast | Moderate |
| **Complex Scores** | Excellent | Limited |
| **Multi-page PDFs** | Native support | Page-by-page |
| **Setup Complexity** | Docker required | Simple pip install |
| **Memory Usage** | Containerized | Python process |
| **Reliability** | Enterprise-grade | Research-level |

## Output Formats

### Audio Output
- **Format**: 44.1 kHz, 16-bit PCM WAV
- **Channels**: 1-5 channels (reduced from original if necessary)
- **Location**: Same directory as input (with `_converted` suffix if converted)

### Score Output
- **MIDI/MusicXML**: Original file unchanged
- **PDF (Docker)**: Converted to MXL/XML in original directory
- **PDF (pdf2image)**: Converted to XML in `<filename>_pdf2image_output/` directory

## Error Handling and Troubleshooting

### Common Issues and Solutions

1. **"No PDF conversion methods available"**
   ```bash
   # Install Docker and pull Audiveris image
   docker pull toprock/audiveris
   
   # OR install fallback method
   pip install pdf2image oemer
   sudo apt-get install poppler-utils  # Linux
   brew install poppler                # macOS
   ```

2. **Docker permission errors**
   ```bash
   # Add user to docker group (Linux)
   sudo usermod -aG docker $USER
   # Restart terminal/session
   ```

3. **pdf2image "poppler not found"**
   - **Linux**: `sudo apt-get install poppler-utils`
   - **macOS**: `brew install poppler`
   - **Windows**: Download poppler binaries and add to PATH

4. **oemer timeout/memory errors**
   - Try smaller PDF files or single pages
   - Use `--without-deskew` flag if image alignment is good
   - Consider using Docker + Audiveris instead

5. **MusicXML validation errors**
   - Check if generated file is valid XML
   - Some complex scores may need manual correction
   - Use music notation software to verify output

### Performance Tips

- **Best Results**: Use Docker + Audiveris for production workflows
- **Speed**: Docker method is typically faster for multi-page documents
- **Memory**: Close other applications when processing large PDFs
- **Quality**: Higher DPI PDFs generally produce better OMR results

## Supported File Formats

### Input Formats
- **Audio**: WAV, MP3, FLAC, AAC, OGG
- **Score**: PDF, MIDI (.mid, .midi), MusicXML (.xml, .musicxml, .mxl)

### Output Formats
- **Audio**: 44.1kHz 16-bit WAV
- **Score**: MusicXML (.xml) or compressed MusicXML (.mxl)

## System Requirements

### Minimum Requirements
- Python 3.7+
- 4GB RAM
- 1GB free disk space

### Recommended for PDF Processing
- Docker Desktop installed
- 8GB RAM
- GPU support (for faster oemer processing)
- SSD storage

## API Reference

### MusicInputLayer Class

```python
class MusicInputLayer:
    def __init__(self):
        """Initialize with auto-detection of available PDF methods."""
        
    def process_inputs(self, audio_path, score_path):
        """
        Process both audio and score inputs.
        
        Returns:
            Dict with 'audio', 'score', and 'overall_success' keys
        """
```

### Return Value Structure

```python
{
    'audio': {
        'success': bool,
        'output_path': Path,
        'original_format': dict,
        'converted': bool,
        'message': str
    },
    'score': {
        'success': bool,
        'output_path': Path,
        'original_format': str,
        'converted': bool,
        'message': str,
        'method_used': str  # 'docker_audiveris' or 'pdf2image_oemer'
    },
    'overall_success': bool
}
```

## Integration with Processing Layer

This input layer produces standardized outputs ready for the next processing stages:

1. **Audio Output**: 44.1kHz WAV files for consistent audio analysis
2. **Score Output**: MusicXML format for symbolic music processing
3. **Metadata**: Processing information for debugging and optimization

### Next Steps Integration

```python
# Example integration with processing layer
results = input_layer.process_inputs("performance.wav", "score.pdf")

if results['overall_success']:
    audio_file = results['audio']['output_path']
    score_file = results['score']['output_path']
    
    # Pass to processing layer
    # processing_layer.analyze(audio_file, score_file)
```

## Changelog

### Version 2.0 (Current)
- Added Docker + Audiveris support for superior PDF conversion
- Implemented pdf2image + oemer fallback method
- Added automatic method detection and selection
- Improved multi-page PDF handling
- Added MusicXML validation with music21
- Enhanced error handling and user feedback

### Version 1.0
- Basic oemer-only PDF conversion
- Audio format validation and conversion
- MIDI/MusicXML pass-through processing

## Contributing

When contributing improvements:

1. Test with both PDF conversion methods
2. Ensure Docker and non-Docker environments work
3. Add appropriate error handling
4. Update documentation for new features
5. Test with various PDF qualities and types

## License and Credits

- **Audiveris**: Open-source OMR engine by Hervé Bitteur
- **oemer**: End-to-end OMR by BreezeWhite
- **music21**: MIT's computational musicology toolkit
- **Docker**: Containerization platform

## Support

For issues with:
- **Docker setup**: Check Docker Desktop installation and permissions
- **PDF conversion quality**: Try different PDF sources or preprocessing
- **Audio processing**: Verify input file integrity and supported formats
- **Installation**: Check system dependencies and Python version compatibility