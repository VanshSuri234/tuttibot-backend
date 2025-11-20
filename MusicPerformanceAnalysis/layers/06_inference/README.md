# Inference Core Layer

## Overview

The **Inference Core Layer** bridges upstream analysis layers with the Grading Layer by collecting, analyzing, and formatting performance data according to the grading rubric dimensions.

### Position in Pipeline

```
INPUT3_LAYER → PROCESSING_LAYER → EXTRACTION_LAYER ↘
                                                     → INFERENCE_CORE → GRADING_LAYER
              TEMPORAL_ALIGNMENT → PQG-A2SA (opt.) ↗
```

### Purpose

1. **Collect** outputs from all upstream layers
2. **Analyze** performance across 5 grading dimensions
3. **Format** results for Grading Layer consumption
4. **Validate** data completeness and quality

---

## Architecture

### Components

```
INFERENCE_CORE/
├── inference_core.py          # Main orchestrator
├── data_collector.py          # Upstream data collection
├── analyzers/                 # Dimension-specific analyzers
│   ├── rhythm_tempo.py        # Dimension 1 (30% weight)
│   ├── sound_quality.py       # Dimension 2 (20% weight)
│   ├── technical_virtuosity.py # Dimension 3 (20% weight)
│   ├── phrasing_diction.py    # Dimension 4 (15% weight)
│   └── communicativeness.py   # Dimension 5 (15% weight)
└── utils/
    └── metric_utils.py        # Shared metric computation
```

### Data Flow

```
1. DataCollector reads JSON files from upstream layers
2. InferenceCore instantiates 5 dimension analyzers
3. Each analyzer computes metrics and scores
4. Results formatted into GradingInputPackage
5. Output: Master JSON + per-dimension JSONs
```

---

## Grading Dimensions

### 1. Rhythm & Tempo Mastery (30%)

**Metrics:**
- `onset_accuracy`: Timing precision of note onsets (ms error)
- `tempo_stability`: Consistency of tempo (CV%)
- `rhythmic_accuracy`: IOI correlation with reference
- `tempo_marking_adherence`: Compliance with tempo markings

**Data Sources:** TEMPORAL_ALIGNMENT, BEAT_DETECTION (optional)

### 2. Sound Quality (20%)

**Metrics:**
- `pitch_accuracy`: Pitch matching accuracy (%)
- `tone_quality`: Harmonic richness (harmonic ratio)
- `timbre_control`: Spectral stability (centroid CV)
- `intonation_grade`: Overall pitch correctness

**Data Sources:** TEMPORAL_ALIGNMENT, EXTRACTION_LAYER, PROCESSING_LAYER

### 3. Technical Virtuosity (20%)

**Metrics:**
- `fluency`: Note transition smoothness (IOI CV)
- `accuracy`: Note accuracy rate (%)
- `difficulty_mastery`: Handling of difficult passages
- `dynamic_control`: Dynamic range and contrast
- `articulation_precision`: Onset precision and consistency

**Data Sources:** TEMPORAL_ALIGNMENT, PROCESSING_LAYER

### 4. Phrasing & Diction (15%)

**Metrics:**
- `articulation_expression`: Rubato and timing variation
- `dynamic_shaping`: Dynamic contour smoothness
- `agogic_expression`: Appropriate tempo flexibility
- `phrase_clarity`: Clear phrase boundaries

**Data Sources:** TEMPORAL_ALIGNMENT, PROCESSING_LAYER, PQG-A2SA (optional)

### 5. Communicativeness (15%)

**Metrics:**
- `emotional_engagement`: Dynamic expression range
- `structural_coherence`: Section consistency
- `interpretive_consistency`: Timbral variation
- `musical_narrative`: Dramatic trajectory
- `overall_impact`: Climax building

**Data Sources:** PROCESSING_LAYER, EXTRACTION_LAYER, PQG-A2SA (optional)

---

## Usage

### Basic Usage

```python
from pathlib import Path
from INFERENCE_CORE import InferenceCore

# Initialize with output directory containing layer outputs
output_dir = Path('/path/to/output/tuttibot_session_timestamp/')
inference_core = InferenceCore(output_dir)

# Process and generate grading package
grading_package = inference_core.process()

# Results saved to: output_dir/05_inference_core/
```

### Command Line

```bash
# Run inference core on existing outputs
python -m INFERENCE_CORE.inference_core /path/to/output/session_dir

# Process without saving files
python -m INFERENCE_CORE.inference_core /path/to/output/session_dir --no-save
```

### Advanced Usage

```python
import logging
from INFERENCE_CORE import InferenceCore, DataCollector

# Custom logger
logger = logging.getLogger('MyApp')
logger.setLevel(logging.DEBUG)

# Initialize
inference_core = InferenceCore(output_dir, logger=logger)

# Access collected data
inference_core.inputs  # InferenceCoreInputs object

# Access individual analyzer results
rhythm_data = inference_core.grading_package['grading_dimensions']['rhythm_tempo']['data']
print(f"Rhythm score: {rhythm_data['overall_score']}/100")
```

---

## Output Format

### Directory Structure

```
05_inference_core/
├── grading_package_master.json       # Complete grading package
├── validation_report.json            # Data quality validation
├── inference_summary.txt             # Human-readable summary
└── dimensions/                       # Per-dimension outputs
    ├── rhythm_tempo.json
    ├── sound_quality.json
    ├── technical_virtuosity.json
    ├── phrasing_diction.json
    └── communicativeness.json
```

### Master Package Schema

```json
{
  "metadata": {
    "timestamp": "2025-11-17T10:30:00",
    "inference_core_version": "1.0",
    "output_base_dir": "/path/to/output",
    "audio_path": "/path/to/audio.wav",
    "score_path": "/path/to/score.musicxml"
  },
  "data_availability": {
    "processing_layer": true,
    "extraction_layer": true,
    "temporal_alignment": true,
    "beat_detection": false,
    "pqg_a2sa": false
  },
  "grading_dimensions": {
    "rhythm_tempo": {
      "weight": 0.30,
      "data": {
        "overall_score": 85.5,
        "interpretation": "Proficient",
        "metrics": { ... },
        "sub_scores": { ... }
      }
    },
    ...
  },
  "validation": {
    "is_complete": true,
    "missing_dimensions": [],
    "warnings": [],
    "errors": []
  }
}
```

### Dimension File Schema

```json
{
  "dimension": "rhythm_tempo",
  "weight": 0.30,
  "timestamp": "2025-11-17T10:30:00",
  "data": {
    "overall_score": 85.5,
    "interpretation": "Proficient",
    "metrics": {
      "onset_accuracy": 45.2,
      "tempo_stability": 3.1,
      "rhythmic_accuracy": 0.92,
      "tempo_marking_adherence": 5.3
    },
    "sub_scores": {
      "onset_accuracy_score": 88.0,
      "tempo_stability_score": 85.0,
      "rhythmic_accuracy_score": 92.0,
      "tempo_marking_score": 82.0
    },
    "weights": { ... }
  }
}
```

---

## Score Interpretation

All scores use 0-100 scale with interpretation:

- **90-100**: Excellent - Professional-level mastery
- **80-89**: Proficient - Advanced performance
- **70-79**: Competent - Solid fundamentals
- **60-69**: Developing - Room for improvement
- **<60**: Needs Work - Significant issues

---

## Data Requirements

### Critical (Must Have)

- **TEMPORAL_ALIGNMENT**: Required for rhythm, pitch, timing analysis
  - `alignment_results.json`
  - Onset times, pitch values, durations

### Important (Highly Recommended)

- **PROCESSING_LAYER**: Needed for dynamics, timbre, spectral analysis
  - `processing_summary.json`
  - RMS energy, spectral features
  
- **EXTRACTION_LAYER**: Provides pitch detection and note segmentation
  - `extraction_summary.json`
  - Pitch contours, note events

### Optional (Enhanced Analysis)

- **BEAT_DETECTION**: Improves tempo and rhythm analysis
  - `beat_tracking_results.json`
  
- **PQG-A2SA**: Enables ensemble/phrasing analysis
  - `alignment_summary.json`

### Graceful Degradation

Missing optional data results in:
- Reduced metric availability
- Lower confidence scores
- Warnings in validation report
- Partial dimension scores

---

## Validation

### Automatic Checks

1. **File Existence**: Verifies all expected JSON files exist
2. **Data Completeness**: Checks for required fields
3. **Value Ranges**: Validates metric values are reasonable
4. **Dependencies**: Ensures critical data sources available

### Validation Report

Located at `05_inference_core/validation_report.json`:

```json
{
  "is_complete": true,
  "missing_dimensions": [],
  "warnings": [
    "PQG-A2SA data missing (some metrics unavailable)"
  ],
  "errors": []
}
```

---

## Integration with Grading Layer

The Inference Core produces a **Grading Input Package** consumed by the Grading Layer:

```python
# Grading Layer usage
from GRADING_LAYER import GradingEngine

grading_engine = GradingEngine()
final_grade = grading_engine.compute_grade(grading_package)
```

The Grading Layer:
1. Reads `grading_package_master.json`
2. Applies dimension weights (30%, 20%, 20%, 15%, 15%)
3. Computes weighted final score
4. Generates grading report

---

## Error Handling

### Common Issues

**Missing temporal alignment:**
```
❌ INFERENCE CORE ERROR: Critical data missing: temporal_alignment
```
**Solution:** Ensure TEMPORAL_ALIGNMENT layer ran successfully

**Invalid JSON format:**
```
❌ Failed to load processing_layer data: JSONDecodeError
```
**Solution:** Check upstream layer outputs for valid JSON

**Missing metrics:**
```
⚠ Warning: Beat detection data not found, using fallback for tempo analysis
```
**Solution:** Optional - run beat detection if available, otherwise continues with reduced metrics

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

inference_core = InferenceCore(output_dir)
inference_core.process()  # Will show detailed debug logs
```

---

## Performance Considerations

- **Typical runtime:** 2-5 seconds for complete analysis
- **Memory usage:** ~100-200 MB for typical performance
- **I/O operations:** Reads 5-8 JSON files, writes 7 output files

---

## Development

### Adding New Metrics

1. **Update analyzer class** (`analyzers/dimension_name.py`):
   ```python
   def _analyze_new_metric(self, inputs: InferenceCoreInputs) -> float:
       # Compute metric
       return score
   ```

2. **Update `analyze()` method** to include new metric
3. **Update weights** if rebalancing sub-metrics
4. **Document** in analyzer docstring and this README

### Testing

```bash
# Unit tests
pytest tests/test_inference_core.py

# Integration test with sample data
python -m INFERENCE_CORE.inference_core tests/sample_output/
```

---

## References

- **Grading Rubric:** See `Grading_Rubric.md` for dimension definitions
- **Layer Architecture:** See `COMPLETE_LAYER_ARCHITECTURE_ANALYSIS.md`
- **Design Specification:** See `INFERENCE_CORE/DESIGN_SPECIFICATION.md`
- **Metric Utilities:** See `utils/metric_utils.py` for computation details

---

## Version History

- **v1.0** (2025-11-17): Initial implementation
  - 5 dimension analyzers
  - Complete grading package generation
  - Validation and error handling

---

## Contact

TuttiBot Development Team
