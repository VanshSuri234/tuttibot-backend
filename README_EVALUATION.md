# TuttiBot v02 - Evaluation Suite

This directory contains standalone evaluation tools for TuttiBot v02 temporal alignment results, completely separate from the main alignment pipeline.

## Overview

The evaluation suite provides comprehensive quality assessment using both custom TuttiBot metrics and industry-standard mir_eval professional metrics for temporal alignment results.

## Files

### Main Evaluation Scripts

- **`evaluate_tuttibotv02.py`** - Main evaluation suite with single file and batch processing
- **`professional_evaluate_alignment.py`** - Core professional evaluation functions with mir_eval integration

### Legacy Evaluation Tools

- **`evaluate_alignment.py`** - Custom TuttiBot evaluation metrics (original version)

## Quick Start

### Single File Evaluation

```bash
# Evaluate a single TuttiBot v02 result file
python3 evaluate_tuttibotv02.py Output/run1/final_output/tuttibotv02_results.json

# Or just provide the output directory (will find tuttibotv02_results.json automatically)
python3 evaluate_tuttibotv02.py Output/run1/final_output/
```

### Batch Evaluation

```bash
# Evaluate all result files in a directory
python3 evaluate_tuttibotv02.py --batch Output/

# Specify custom output directory for batch results
python3 evaluate_tuttibotv02.py --batch Output/ --output my_evaluations/
```

## Evaluation Metrics

### Custom TuttiBot Metrics
- **Mean Absolute Error (MAE)** - Average timing error in milliseconds
- **Median Absolute Error** - Robust center measure
- **Standard Deviation** - Error spread
- **Tolerance Analysis** - Percentage within 50ms, 100ms, 250ms windows
- **Quality Assessment** - Overall rating and recommendations

### Professional mir_eval Metrics
- **Precision** - How many detected onsets are correct
- **Recall** - How many actual onsets were detected
- **F-measure** - Harmonic mean of precision and recall
- **Multi-tolerance evaluation** - Standard MIR evaluation protocols

## Output Files

### Single Evaluation
- `evaluation_results.json` - Detailed metrics in JSON format
- `evaluation_professional_scatter.png` - Alignment scatter plot
- `evaluation_professional_histogram.png` - Error distribution histogram

### Batch Evaluation
- `batch_summary.json` - Aggregate statistics and individual results
- `eval_NNN_*_results.json` - Individual evaluation results
- `eval_NNN_*_professional_*.png` - Individual visualizations per result

## Requirements

```bash
pip install numpy matplotlib mir_eval
```

## Example Results

Perfect alignment typically shows:
- **MAE**: 0.0 ms
- **Tolerance Analysis**: 100% within all windows
- **mir_eval F-measure**: 1.000 (perfect score)
- **Quality Rating**: 🟢 Excellent

## Pipeline Integration

The evaluation tools are **completely separate** from the main temporal alignment pipeline (`main_v02_fixed.py`). This design ensures:

1. **Clean separation** - Alignment pipeline focuses purely on temporal alignment
2. **Flexible evaluation** - Can evaluate results from any run, anytime
3. **Batch processing** - Can compare multiple runs and analyze trends
4. **Professional standards** - Uses peer-reviewed mir_eval library

## Usage Notes

- Evaluation works with TuttiBot v02 output format automatically
- Supports both legacy and current result file structures  
- Generates publication-ready visualizations
- Provides machine-readable JSON output for further analysis
- Safe to run repeatedly (won't affect original alignment results)

## Help

```bash
python3 evaluate_tuttibotv02.py --help
```

For detailed metrics and visualization examples, see the generated output files from any evaluation run.
