# Music Performance Analysis System

Automated music performance evaluation system with DTW-based and PQG-A2SA enhanced alignment.

## Overview

This system analyzes music performances by comparing audio recordings to musical scores, providing detailed grading across 5 dimensions:

- Rhythm & Tempo (30%)
- Sound Quality (20%)
- Technical Virtuosity (20%)
- Phrasing & Diction (15%)
- Communicativeness (15%)

## Features

Two analysis pipelines:

1. DTW-only Pipeline: Fast analysis (30-45 seconds per file) using Dynamic Time Warping
2. PQG-Enhanced Pipeline: Higher accuracy (2-3 minutes per file) using PQG-A2SA for precise onset/offset detection

Key capabilities:
- Automatic audio-to-MIDI transcription
- Score-to-performance alignment
- Note-level timing and pitch analysis
- Comprehensive performance grading
- Batch processing support
- Graceful fallback when components fail

## System Requirements

Python 3.10 or higher

Required dependencies:
- numpy, scipy, scikit-learn
- librosa, soundfile
- pretty_midi, music21
- torch, tensorflow
- basic-pitch (for AMT)
- See requirements.txt for complete list

Optional:
- CUDA-enabled GPU (recommended for faster processing)
- BeatNet (for beat detection)

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run single file analysis (DTW-only):

```bash
python3 MusicPerformanceAnalysis/pipeline.py \
  --audio Bach_10_Dataset/DieSonne/06-DieSonne-violin.wav \
  --score Bach_10_Dataset/DieSonne/06-DieSonne.xml \
  --output Output/my_analysis
```

Run with PQG enhancement:

```bash
python3 MusicPerformanceAnalysis/pipeline_with_pqg.py \
  --audio Bach_10_Dataset/DieSonne/06-DieSonne-violin.wav \
  --score Bach_10_Dataset/DieSonne/06-DieSonne.xml \
  --output Output/my_analysis_pqg
```

Batch processing:

```bash
./run_analysis.sh              # DTW-only
./run_analysis_with_pqg.sh     # PQG-enhanced
```

## Architecture

7-layer pipeline:

1. Input Standardization - Validate audio and score files
2. Audio Processing - Optional denoising and normalization
3. Temporal Alignment - DTW-based score-to-performance alignment
4. Feature Extraction - Extract performance and score features
5. PQG-A2SA Alignment - Enhanced onset/offset detection (PQG pipeline only)
6. Enhanced Inference - Compute grading metrics with optional PQG enhancement
7. Grading - Calculate final scores and generate reports

## Output Structure

```
Output/my_analysis/
  01_input/                     Validated inputs
  03_temporal_alignment/        DTW alignment results
    scoregraph.json
    transcription.json
    alignment_output/
      alignment_results.json
  04_extraction/                Extracted features
  05_pqg_a2sa/                 PQG alignment (enhanced pipeline only)
    pqg_a2sa_results.json
  05_inference_core/           Grading metrics
    grading_package.json
    grading_package_enhanced.json  (PQG pipeline)
    metric_sources.json            (PQG pipeline)
  07_grading/                  Final results
    final_grade.json
    performance_report.txt
  pipeline_summary.json
```

## Documentation

- run_help.txt - Quick command reference
- requirements.txt - Python dependencies
- ESSENTIAL_FILES_FOR_PRODUCTION.txt - File structure explanation
- docs/LAYER_ARCHITECTURE_AND_GRADING_FORMULAS.txt - Detailed architecture
- docs/PQG_INTEGRATION_SUCCESS.md - PQG enhancement documentation
- docs/LLM_FEEDBACK_DATA_REQUIREMENTS.txt - LLM feedback structure

## Example Results

DieSonne violin performance with PQG enhancement:
- Overall Score: 44.52/100
- Sound Quality: 84.39 (91.30% pitch accuracy)
- Technical Virtuosity: 60.84
- Rhythm & Tempo: 5.08 (timing challenges detected)

See docs/DieSonne_PQG_Results_Summary.txt for detailed example.

## Testing

Test dataset included: Bach_10_Dataset with 4 instruments per piece

Run quick test:

```bash
python3 MusicPerformanceAnalysis/pipeline.py \
  --audio Bach_10_Dataset/DieSonne/06-DieSonne-violin.wav \
  --score Bach_10_Dataset/DieSonne/06-DieSonne.xml \
  --output Output/test
```

Check results:

```bash
cat Output/test/pipeline_summary.json
cat Output/test/07_grading/performance_report.txt
```

## Known Issues

1. Final grade in final_grade.json may show 0.0 due to grading layer bug. Actual scores are in grading_package.json.

2. Layer numbering inconsistency (05_inference_core should be 06_inference_core). Does not affect functionality.

3. Beat detection may fail gracefully. Pipeline continues without beat information.

4. PQG-A2SA may not match all notes. System falls back to DTW for unmatched notes.

## Performance Expectations

DTW-only pipeline:
- Input validation: 1-2 seconds
- Audio transcription: 10-15 seconds
- DTW alignment: 15-20 seconds
- Feature extraction: 2-3 seconds
- Inference and grading: 1-2 seconds
- Total: 30-45 seconds per file

PQG-enhanced pipeline:
- All DTW steps: 30-45 seconds
- PQG-A2SA alignment: 90-120 seconds
- Enhanced inference: 1-2 seconds
- Total: 2-3 minutes per file

## Citation

If you use this system in your research, please cite:

PQG-A2SA Algorithm:
Lian, Cheng, Zhang (2023) - Performance-to-Score Alignment using PQG-A2SA

## Troubleshooting

CUDA out of memory:
- Reduce batch size in BasicPitch
- Run on CPU (slower but works)

Import errors:
- Verify Python version: python3 --version (must be 3.10+)
- Install dependencies: pip install -r requirements.txt

Pipeline fails at beat detection:
- This is normal and expected
- Pipeline continues without beat information

PQG takes too long:
- PQG processing takes 90-120 seconds per file by design
- Consider DTW-only pipeline for faster results

For more help, see run_help.txt
