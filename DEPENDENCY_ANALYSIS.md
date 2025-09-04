# TuttiBot v02 - Dependency Analysis & Compatibility Matrix

## Current Issues Identified

### 1. Basic Pitch Compatibility Issues
- **Basic Pitch 0.2.6**: Requires TensorFlow with Keras compatibility
- **Basic Pitch 0.4.0**: Requires TensorFlow 2.4.1-2.15.1, uses tflite-runtime
- **Current TensorFlow**: 2.20.0 (too new)
- **Error**: `'_UserObject' object has no attribute 'add_slot'` and Keras version mismatch

### 2. NumPy Compatibility Chain
- **TensorFlow 2.12**: Requires numpy>=1.22,<1.24
- **Current NumPy**: 2.2.6 (too new)
- **Jax**: Requires numpy>=1.26
- **Error**: "A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2.6"

### 3. Python Version Constraints
- **Current Python**: 3.13
- **TensorFlow 2.12**: Supports Python 3.8-3.11 only
- **Basic Pitch**: Works with Python 3.8-3.11

## Recommended Solution: Compatible Environment

### Python Version: 3.10
- Widely supported by all ML libraries
- Stable and well-tested
- Good balance between features and compatibility

### Core Dependencies Analysis

#### TensorFlow Stack
```
tensorflow==2.12.0          # Last stable version with good compatibility
tensorflow-io-gcs-filesystem>=0.23.1
keras==2.12.0               # Must match TensorFlow version
numpy>=1.22.0,<1.24.0       # TensorFlow 2.12 requirement
```

#### Basic Pitch Stack
```
basic-pitch==0.3.0          # More stable than 0.4.0, works with TF 2.12
librosa>=0.8.0,<0.11.0      # Audio processing
mir-eval>=0.6               # Music information retrieval
pretty-midi>=0.2.9          # MIDI handling
resampy>=0.2.2,<0.5.0       # Audio resampling
```

#### Other ML Dependencies
```
scikit-learn>=1.0.0,<1.4.0  # Machine learning
scipy>=1.7.0,<1.12.0        # Scientific computing
```

#### Audio Processing
```
soundfile>=0.12.1           # Audio I/O
librosa>=0.8.0,<0.11.0      # Audio analysis
```

#### PDF Processing (oemer)
```
onnxruntime>=1.10.0         # For oemer PDF conversion
opencv-python>=4.5.0        # Image processing for PDF
```

#### Other Dependencies
```
music21>=8.0.0              # Music notation
matplotlib>=3.5.0           # Plotting
pandas>=1.3.0               # Data handling
pathlib                     # Path handling (built-in Python 3.4+)
argparse                    # Command line parsing (built-in)
json                        # JSON handling (built-in)
```

## Environment Creation Steps

1. **Create isolated environment with Python 3.10**
2. **Install compatible TensorFlow + NumPy stack**
3. **Install Basic Pitch with compatible versions**
4. **Install remaining dependencies**
5. **Test each component individually**

## Testing Strategy

1. **Test TensorFlow GPU compatibility**
2. **Test Basic Pitch audio transcription**
3. **Test oemer PDF conversion**
4. **Test full pipeline integration**
