# TuttiBot v02 Dependencies Report

**Generated:** September 4, 2025  
**System:** Linux (CPU mode)  
**Total Packages:** 343 installed  

## 🐍 Core Environment
```
Python: 3.10.12
Docker: 28.3.3, build 980b856
NVIDIA: Not available (CPU mode)
```

## 🎵 Music Processing Libraries
| Library | Installed | Required | Status | Purpose |
|---------|-----------|-----------|--------|---------|
| `music21` | **5.7.2** | >=9.1.0 | ⚠️ **OUTDATED** | Score processing, MusicXML |
| `librosa` | **0.10.2.post1** | >=0.10.0 | ✅ OK | Audio analysis |
| `pretty_midi` | **0.2.10** | >=0.2.9 | ✅ OK | MIDI processing |
| `basic-pitch` | **0.4.0** | N/A | ✅ OK | AMT transcription |
| `oemer` | **0.1.8** | N/A | ✅ OK | PDF → MusicXML OMR |

## 🤖 Machine Learning Frameworks
| Library | Installed | Required | Status | Purpose |
|---------|-----------|-----------|--------|---------|
| `tensorflow` | **2.15.0** | >=2.12.0,<2.16.0 | ✅ OK | Neural networks |
| `torch` | **2.5.1** | N/A | ✅ OK | PyTorch (Basic Pitch) |
| `torchaudio` | **2.5.1** | N/A | ✅ OK | Audio processing |
| `torchvision` | **0.20.1** | N/A | ✅ OK | Vision models |
| `essentia-tensorflow` | **2.1b6.dev1389** | >=2.1b6.dev1034 | ✅ OK | Audio features |

## 📊 Scientific Computing
| Library | Installed | Required | Status | Purpose |
|---------|-----------|-----------|--------|---------|
| `numpy` | **1.26.4** | ==1.26.4 | ✅ OK | Array operations |
| `scipy` | **1.14.1** | >=1.10.0 | ✅ OK | Scientific computing |
| `scikit-learn` | **1.5.0** | >=1.3.0 | ✅ OK | ML utilities |
| `pandas` | **1.5.3** | >=2.0.0 | ⚠️ **OUTDATED** | Data handling |
| `matplotlib` | **3.6.2** | N/A | ✅ OK | Visualization |

## 🛠️ Development & System
| Library | Installed | Required | Status | Purpose |
|---------|-----------|-----------|--------|---------|
| `docker` | **7.1.0** | N/A | ✅ OK | Container management |
| `opencv-python` | **4.11.0.86** | N/A | ✅ OK | Image processing |
| `requests` | **2.31.0** | N/A | ✅ OK | HTTP requests |
| `jupyter*` | **Multiple** | N/A | ✅ OK | Development environment |

## ⚠️ Critical Issues Found

### 1. **music21 Version Mismatch**
- **Installed:** 5.7.2
- **Required:** >=9.1.0
- **Impact:** May cause compatibility issues with newer MusicXML features
- **Fix:** `pip install music21>=9.1.0`

### 2. **pandas Version Behind**
- **Installed:** 1.5.3  
- **Required:** >=2.0.0
- **Impact:** Missing newer DataFrame features, potential deprecation warnings
- **Fix:** `pip install pandas>=2.0.0`

## 🔧 Missing Dependencies (From requirements.txt)
```bash
# Not currently installed but listed in requirements:
soundfile>=0.12.0         # Audio file I/O
ffmpeg-python>=0.2.0      # Audio format conversion  
aubio>=0.4.9              # Audio analysis
pathlib2>=2.3.0          # Path utilities (Python 3.10 has built-in pathlib)
click>=8.0.0              # CLI utilities
tqdm>=4.64.0              # Progress bars
PyYAML>=6.0               # YAML parsing
pytest>=7.0.0             # Testing framework
pytest-cov>=4.0.0        # Test coverage
```

## 🏗️ Pipeline-Specific Components
- **Custom Modules:** `gpu_manager`, `build_scoregraph_with_repeats`, `transcribe_audio_fixed`, `align_symbolic_enhanced`
- **Docker Images:** `toprock/audiveris:latest` (1.21GB)
- **Standard Library:** `os`, `sys`, `json`, `argparse`, `logging`, `traceback`, `shutil`, `glob`, `pathlib`, `datetime`, `tempfile`

## 📋 Recommended Actions

### 🚨 Immediate (Critical)
```bash
pip install music21>=9.1.0 pandas>=2.0.0
```

### 🔧 Optional (Enhancement)
```bash
pip install soundfile ffmpeg-python aubio tqdm PyYAML
```

### 🧪 Testing (Development)
```bash
pip install pytest pytest-cov
```

## ✅ System Status
- **Core Pipeline:** ✅ Functional with current versions
- **PDF Processing:** ✅ Working (Docker + oemer fallback)  
- **Audio Transcription:** ✅ Working (Basic Pitch)
- **Alignment:** ✅ Working (99.7% confidence achieved)
- **GPU Support:** ⚠️ CPU-only mode (no NVIDIA drivers detected)

**Note:** Despite version mismatches, the pipeline is currently functional. Updates recommended for long-term stability and access to latest features.
