# TuttiBot v02 - Quick Setup Guide

## 🚀 One-Command Quick Start

If you already have the environment set up:
```bash
conda activate tuttibot_py311
python main_v02_fixed.py --pdf your_score.pdf --audio your_audio.wav
```

## 📋 Complete Fresh Installation

### Step 1: System Dependencies
```bash
# Ubuntu/Debian/WSL
sudo apt update && sudo apt install poppler-utils

# Verify installation
pdftoppm -h  # Should show help text
```

### Step 2: Python Environment
```bash
# Create isolated Python 3.11 environment
conda create -n tuttibot_py311 python=3.11 -y
conda activate tuttibot_py311
```

### Step 3: Install TuttiBot Dependencies
```bash
# Install all required packages
pip install -r requirement_v02_gpu.txt
```

### Step 4: Verify Installation
```bash
# Test all components (should show no errors)
python -c "import tensorflow as tf; print(f'TensorFlow {tf.__version__} ✅')"
python -c "import basic_pitch; print('Basic-pitch ✅')"
python -c "import oemer; print('Oemer ✅')"
```

### Step 5: Run Your First Analysis
```bash
# Example with provided test files
python main_v02_fixed.py --pdf Twinkle_pdf.pdf --audio twinkle_full.wav

# Your own files
python main_v02_fixed.py --pdf your_score.pdf --audio your_recording.wav
```

## 📁 Expected Results

After successful execution, you'll find:
```
Output/tuttibotv02_output_TIMESTAMP/
├── final_output/
│   ├── summary_report.txt      # Key metrics and results
│   └── tuttibotv02_results.json # Complete analysis data
├── block_2_alignment/
│   └── alignment_visualization.png # Visual alignment plot
└── [other analysis files...]
```

## 🎯 Success Metrics

Look for these indicators of successful processing:
- ✅ **Alignment confidence > 85%** (excellent results)
- ✅ **Processing completes without errors**
- ✅ **Summary report generated**
- ✅ **Visualization images created**

## 🔧 Troubleshooting

### Common Issues:

1. **"basic-pitch command not found"**
   ```bash
   # Solution: Ensure correct environment
   conda activate tuttibot_py311
   pip install basic-pitch==0.4.0
   ```

2. **"pdftoppm not found"**
   ```bash
   # Solution: Install system dependencies
   sudo apt install poppler-utils
   ```

3. **TensorFlow warnings**
   ```
   # These are normal on CPU systems, can be ignored:
   "Unable to register cuDNN factory..."
   "This TensorFlow binary is optimized..."
   ```

4. **Low alignment confidence (<70%)**
   - Check audio/score quality match
   - Ensure clear audio recording
   - Verify score notation clarity

### Performance Tips:
- **Use SSD storage** for faster I/O
- **16GB+ RAM recommended** for longer audio files
- **Close other applications** during processing
- **Use high-quality inputs** for best results

## 📊 Example Results

### Successful Run Output:
```
🎉 TuttiBot v02 Pipeline Completed Successfully!
📁 Results saved to: ./Output/tuttibotv02_output_20250904_011514
📊 Final results: ./Output/tuttibotv02_output_20250904_011514/final_output/tuttibotv02_results.json
⚡ Processing mode: CPU

SUMMARY:
  Score measures: 12
  Score beats: 48
  Detected notes: 36
  Alignment confidence: 0.946  ← Excellent!
  DTW distance: 7.057
  Status: SUCCESS
```

## 🎼 Supported Input Formats

### Score Inputs:
- ✅ **PDF**: Printed sheet music (single page recommended)
- ✅ **MusicXML**: Digital music notation
- ✅ **MIDI**: Symbolic music representation

### Audio Inputs:
- ✅ **WAV**: Uncompressed audio (recommended)
- ✅ **MP3**: Compressed audio (acceptable)
- ✅ **FLAC**: Lossless compressed audio

### Quality Recommendations:
- **Audio**: Clear, minimal background noise
- **PDF**: High-resolution scan, standard notation
- **Performance**: Solo instrument preferred for testing

## 🔄 Next Steps

After successful installation and testing:

1. **Process your own files**: Try different score/audio combinations
2. **Explore results**: Check visualization files and detailed JSON output
3. **Adjust parameters**: Experiment with different input qualities
4. **Scale up**: Process multiple files for comparative analysis

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify system requirements are met
3. Review the detailed technical logs
4. Ensure all dependencies are correctly installed

---
**Setup Guide Version**: 1.0  
**Compatible with**: TuttiBot v02.1  
**Last Updated**: September 4, 2025  
**Status**: ✅ Tested and Validated
