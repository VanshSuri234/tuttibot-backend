# Inference Core Layer - Design Specification

**Version**: 1.0  
**Date**: November 17, 2025  
**Purpose**: Bridge between feature extraction layers and Grading Layer

---

## Overview

The **Inference Core Layer** serves as the critical data integration and formatting layer that:

1. **Consumes** outputs from all upstream layers (INPUT3, PROCESSING, EXTRACTION, TEMPORAL_ALIGNMENT, PQG-A2SA)
2. **Extracts** relevant features and metrics for each grading dimension
3. **Formats** data into the exact structure required by the Grading Layer
4. **Validates** data completeness and quality
5. **Computes** intermediate metrics needed for grading

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UPSTREAM LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│  INPUT3 → PROCESSING → EXTRACTION                           │
│                    ↓                                         │
│              TEMPORAL_ALIGNMENT (Blocks 0,1,2,4)            │
│                    ↓                                         │
│                 PQG-A2SA                                     │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  INFERENCE CORE LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  Data Collection → Feature Extraction → Metric Computation  │
│       ↓                   ↓                    ↓             │
│  Validation → Formatting → Quality Assurance                │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    GRADING LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  Rhythm & Tempo (30%) | Sound Quality (20%)                 │
│  Technical Virtuosity (20%) | Phrasing & Diction (15%)      │
│  Communicativeness (15%)                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Grading Dimension to Layer Output Mapping

### 1. Rhythm & Tempo Mastery (30%)

**Required Metrics:**
- Onset timing accuracy
- Tempo stability
- Rhythmic deviation patterns
- Adherence to tempo markings

**Source Layer Outputs:**

| Metric | Source Layer | Specific Output | Data Path |
|--------|-------------|----------------|-----------|
| **Onset Timings (Score)** | Block 0 (ScoreGraph) | `scoregraph.json` → `musical_notes` → `onset_sec` | `nodes[].abs_beat` + tempo |
| **Onset Timings (Performance)** | Block 1 (AMT) | `transcription.json` → `notes` → `onset_time` | Direct |
| **Onset Alignment** | Block 2 (Alignment) | `alignment_results.json` → `time_map` | Score-perf pairs |
| **Note-level Alignment** | PQG-A2SA | Per-note onset/offset mappings | `τ_i(l_on_{n_{i,j}})` |
| **Beat Times (Score)** | Block 0 | `scoregraph.json` → `nodes` | Beat grid |
| **Beat Times (Performance)** | Block 4 (Beat Detection) | `beats.json` | Detected beats |
| **Tempo Curve** | EXTRACTION | `performance_features.json` → `tempo_bpm` | Continuous tempo |
| **IOI (Score)** | Block 0 | Computed from note onsets | `onset[i+1] - onset[i]` |
| **IOI (Performance)** | Block 1 + Block 2 | Computed from aligned onsets | Via time map |
| **Tempo Markings** | PROCESSING | `music_features.json` → `tempo` | Score tempo |

**Computed Metrics for Grading:**
```python
{
    "onset_accuracy": {
        "mean_absolute_error_ms": float,      # Average onset deviation
        "std_error_ms": float,                # Consistency of errors
        "max_error_ms": float,                # Worst case
        "percentage_within_50ms": float,      # Industry standard
        "percentage_within_100ms": float,
        "error_distribution": List[float]     # Per-note errors
    },
    "tempo_stability": {
        "mean_tempo_bpm": float,
        "std_tempo_bpm": float,
        "coefficient_of_variation": float,    # CV = std/mean
        "tempo_drift": float,                 # Linear trend
        "sudden_changes": int,                # Count of abrupt shifts
        "tempo_curve": List[float]            # Full tempo trajectory
    },
    "rhythmic_accuracy": {
        "ioi_correlation": float,             # Pearson r between score/perf IOI
        "rhythm_precision_score": float,      # Overall rhythm accuracy
        "rushed_notes_count": int,            # Notes played early
        "dragged_notes_count": int,           # Notes played late
        "syncopation_errors": int             # Incorrect rhythmic patterns
    },
    "tempo_marking_adherence": {
        "score_tempo_bpm": float,
        "performance_mean_tempo_bpm": float,
        "deviation_percentage": float,
        "interpretation": str                 # "faithful" | "rubato" | "deviated"
    }
}
```

---

### 2. Sound Quality (20%)

**Required Metrics:**
- Pitch accuracy (intonation)
- Tone clarity and stability
- Timbre matching to score markings

**Source Layer Outputs:**

| Metric | Source Layer | Specific Output | Data Path |
|--------|-------------|----------------|-----------|
| **Expected Pitches** | PROCESSING | `music_features.json` → `notes` → `pitch` | MIDI numbers |
| **Expected Pitches (Detailed)** | EXTRACTION | `score_features.json` → `expected_pitches` | Full list |
| **Performed Pitches** | Block 1 (AMT) | `transcription.json` → `notes` → `pitch_midi` | MIDI numbers |
| **Pitch Contour** | EXTRACTION | `performance_features.json` → `pitch_contour` | Hz values |
| **Pitch Confidence** | EXTRACTION | `performance_features.json` → `pitch_confidence` | Confidence scores |
| **F0 Trajectory** | EXTRACTION | `performance_features.json` → `fundamental_frequencies` | Hz over time |
| **Spectral Centroid** | EXTRACTION | `performance_features.json` → `spectral_centroid` | Brightness |
| **Spectral Bandwidth** | EXTRACTION | `performance_features.json` → `spectral_bandwidth` | Timbral spread |
| **MFCC Features** | EXTRACTION | `performance_features.json` → `mfcc_features` | Timbre descriptors |
| **Harmonic Content** | EXTRACTION | `performance_features.json` → `harmonic_content` | Tone purity |
| **Alignment (Pitch Matching)** | Block 2 | Pitch alignment from time map | Matched pitch pairs |

**Computed Metrics for Grading:**
```python
{
    "pitch_accuracy": {
        "mean_pitch_error_cents": float,      # Average pitch deviation
        "std_pitch_error_cents": float,       # Consistency
        "pitch_match_rate": float,            # Correct pitches %
        "out_of_tune_notes_count": int,       # > 50 cents off
        "pitch_stability": float,             # Vibrato/drift analysis
        "error_distribution": List[float]     # Per-note errors in cents
    },
    "tone_quality": {
        "harmonic_ratio_mean": float,         # Harmonic vs noise
        "harmonic_ratio_std": float,
        "spectral_centroid_mean": float,      # Average brightness
        "spectral_centroid_std": float,       # Timbral consistency
        "tone_clarity_score": float           # Composite measure
    },
    "timbre_control": {
        "mfcc_variance": float,               # Timbral consistency
        "spectral_flux_mean": float,          # Tone stability
        "dynamic_range_db": float,            # Control range
        "timbre_matching_score": float        # Match to score indications
    },
    "intonation_grade": {
        "overall_score": float,               # 0-100
        "interpretation": str                 # "excellent" | "good" | "fair" | "poor"
    }
}
```

---

### 3. Technical Virtuosity (20%)

**Required Metrics:**
- Smoothness and fluency
- Handling of difficult passages
- Confidence (lack of errors/hesitations)
- Control across technical elements

**Source Layer Outputs:**

| Metric | Source Layer | Specific Output | Data Path |
|--------|-------------|----------------|-----------|
| **Note Density** | PROCESSING | `music_features.json` → `notes` count | Difficulty indicator |
| **Tempo Variations** | EXTRACTION | `performance_features.json` → `tempo_bpm` | Stability under pressure |
| **Onset Strength** | EXTRACTION | `performance_features.json` → `onset_strengths` | Attack clarity |
| **Onset Detection** | EXTRACTION | `performance_features.json` → `onset_times` | Precision |
| **Velocity Markings (Score)** | PROCESSING | `music_features.json` → `notes` → `velocity` | Expected dynamics |
| **RMS Energy** | EXTRACTION | `performance_features.json` → `rms_energy` | Actual dynamics |
| **Zero Crossing Rate** | EXTRACTION | `performance_features.json` → `zero_crossing_rate` | Articulation clarity |
| **Spectral Rolloff** | EXTRACTION | `performance_features.json` → `spectral_rolloff` | Tone production |
| **Alignment Quality** | Block 2 | `alignment_results.json` → `metrics` → `dtw_distance` | Overall accuracy |
| **Segmentation** | PROCESSING | `audio_segments.json` → `segments` | Phrase continuity |
| **Articulation Detection** | PQG-A2SA | Staccato/legato classification | Per-note articulation |
| **Note Durations (Score)** | PROCESSING | `music_features.json` → `notes` → `duration` | Expected durations |
| **Note Durations (Performance)** | Block 1 | `transcription.json` → `notes` → `duration` | Actual durations |

**Computed Metrics for Grading:**
```python
{
    "fluency": {
        "note_transition_smoothness": float,  # Onset regularity
        "phrase_continuity_score": float,     # Segment connections
        "hesitation_count": int,              # Pauses/breaks
        "tempo_consistency_in_runs": float    # Stability in fast passages
    },
    "accuracy": {
        "note_accuracy_rate": float,          # % correct notes
        "missed_notes_count": int,
        "extra_notes_count": int,
        "wrong_notes_count": int,
        "clean_execution_score": float        # Overall cleanliness
    },
    "difficulty_mastery": {
        "score_difficulty_level": float,      # Based on note density, tempo
        "performance_vs_difficulty": float,   # Quality relative to difficulty
        "difficult_passage_handling": Dict,   # Per-passage analysis
        "ornament_execution_score": float     # Trills, grace notes, etc.
    },
    "dynamic_control": {
        "dynamic_range_utilized_db": float,
        "dynamic_accuracy": float,            # Match to score markings
        "dynamic_smoothness": float,          # Gradual vs abrupt changes
        "dynamic_contrast_score": float       # Effective use of dynamics
    },
    "articulation_precision": {
        "articulation_match_rate": float,     # % correct articulations
        "staccato_clarity": float,
        "legato_smoothness": float,
        "accent_accuracy": float,
        "articulation_consistency": float
    }
}
```

---

### 4. Phrasing & Diction (15%)

**Required Metrics:**
- Articulation faithfulness
- Dynamic shaping
- Expressive timing variations
- Musical sentence clarity

**Source Layer Outputs:**

| Metric | Source Layer | Specific Output | Data Path |
|--------|-------------|----------------|-----------|
| **Articulation Symbols (Score)** | EXTRACTION | `score_features.json` → `articulation_symbols` | Expected articulations |
| **Dynamic Markings (Score)** | EXTRACTION | `score_features.json` → `dynamic_markings` | Expected dynamics |
| **Phrase Boundaries (Score)** | EXTRACTION | `score_features.json` → `phrase_boundaries` | Phrase structure |
| **Articulation Detection (Perf)** | PQG-A2SA | Staccato/legato per note | Actual articulations |
| **RMS Energy Trajectory** | EXTRACTION | `performance_features.json` → `rms_energy` | Dynamic curve |
| **Tempo Micro-variations** | Block 2 + EXTRACTION | Local tempo ratios | Agogic accents |
| **Segment Boundaries** | PROCESSING | `audio_segments.json` → `segments` | Performed phrases |
| **Chroma Features** | EXTRACTION | `performance_features.json` → `chroma_features` | Harmonic clarity |
| **Note Duration Ratios** | Block 1 + Block 0 | Comparison of durations | Expressive timing |
| **Beat Alignment** | Block 4 + Block 2 | Beat deviation patterns | Rubato detection |

**Computed Metrics for Grading:**
```python
{
    "articulation_expression": {
        "articulation_match_rate": float,     # % faithful to score
        "staccato_execution_quality": float,
        "legato_execution_quality": float,
        "accent_placement_accuracy": float,
        "articulation_variety_score": float   # Expressive range
    },
    "dynamic_shaping": {
        "dynamic_arc_correlation": float,     # Match to score crescendo/dim
        "dynamic_contrast_effective": float,  # Effective use of dynamics
        "dynamic_smoothness": float,          # Gradual vs jerky
        "phrase_dynamic_planning": float,     # Structural awareness
        "dynamic_expression_score": float     # Overall dynamic musicality
    },
    "agogic_expression": {
        "rubato_appropriateness": float,      # Tasteful tempo flexibility
        "phrase_ending_ritardandi": float,    # Natural phrase endings
        "structural_tempo_shaping": float,    # Larger-scale tempo plan
        "micro_timing_expression": float,     # Note-level timing nuances
        "agogic_coherence": float             # Consistency of approach
    },
    "phrase_clarity": {
        "phrase_boundary_definition": float,  # Clear phrase separation
        "breath_point_placement": float,      # Musical punctuation
        "structural_hierarchy": float,        # Sub-phrase vs main phrase
        "narrative_flow": float,              # Sentence-like logic
        "musical_grammar_score": float        # Overall phrase coherence
    }
}
```

---

### 5. Communicativeness (15%)

**Required Metrics:**
- Emotional engagement
- Structural coherence
- Musical narrative
- Interpretive impact

**Source Layer Outputs:**

| Metric | Source Layer | Specific Output | Data Path |
|--------|-------------|----------------|-----------|
| **Overall Alignment Quality** | Block 2 | `alignment_results.json` → `metrics` | Interpretation coherence |
| **Tempo Curve** | EXTRACTION | `performance_features.json` → `tempo_bpm` | Structural shaping |
| **Dynamic Curve** | EXTRACTION | `performance_features.json` → `rms_energy` | Emotional arc |
| **Spectral Features** | EXTRACTION | All spectral features | Timbral expression |
| **Section Labels (Score)** | EXTRACTION | `score_features.json` → `section_labels` | Structural awareness |
| **Key Signature** | PROCESSING | `music_features.json` → `key_signature` | Harmonic context |
| **Phrase Structure** | EXTRACTION | `score_features.json` → `phrase_boundaries` | Musical architecture |
| **Segmentation** | PROCESSING | `audio_segments.json` | Performance structure |
| **Harmonic/Percussive Content** | EXTRACTION | `harmonic_content`, `percussive_content` | Expressive texture |
| **Chroma Variance** | EXTRACTION | `chroma_features` analysis | Harmonic color |
| **MFCC Trajectory** | EXTRACTION | `mfcc_features` | Timbral journey |

**Computed Metrics for Grading:**
```python
{
    "emotional_engagement": {
        "dynamic_expression_range": float,    # Emotional breadth
        "timbral_variation": float,           # Expressive color palette
        "intensity_curve_shape": float,       # Narrative arc
        "emotional_commitment_score": float   # Overall conviction
    },
    "structural_coherence": {
        "section_differentiation": float,     # Clear section contrasts
        "phrase_hierarchy_clarity": float,    # Structural levels
        "formal_awareness_score": float,      # Large-scale planning
        "architectural_logic": float          # Overall structural sense
    },
    "interpretive_consistency": {
        "tempo_philosophy_coherence": float,  # Consistent tempo approach
        "dynamic_strategy_coherence": float,  # Consistent dynamic plan
        "articulation_style_coherence": float,# Consistent articulation
        "interpretive_identity": float        # Unique but coherent vision
    },
    "musical_narrative": {
        "dramatic_trajectory": float,         # Story arc
        "climax_building": float,             # Tension/release
        "character_portrayal": float,         # Musical personality
        "communicative_clarity": float        # Message transmission
    },
    "overall_impact": {
        "performance_conviction": float,      # Confidence and commitment
        "artistic_maturity": float,           # Sophistication
        "audience_engagement_potential": float,# Projected impact
        "interpretive_originality": float     # Unique insights
    }
}
```

---

## Inference Core Data Structure

### Input Data Collection

```python
@dataclass
class InferenceCoreInputs:
    """Complete collection of upstream layer outputs"""
    
    # Paths to upstream outputs
    input3_outputs: Dict[str, Path]
    processing_outputs: Dict[str, Path]
    extraction_outputs: Dict[str, Path]
    temporal_alignment_outputs: Dict[str, Path]
    pqg_a2sa_outputs: Optional[Dict[str, Path]]
    
    # Loaded data
    scoregraph: Dict
    music_features: Dict
    audio_segments: Dict
    performance_features: Dict
    score_features: Dict
    transcription: Dict
    alignment_results: Dict
    time_map: Dict
    beats: Optional[Dict]
    pqg_alignment: Optional[Dict]
```

### Output Data Structure (for Grading Layer)

```python
@dataclass
class GradingInputPackage:
    """Formatted data package for Grading Layer"""
    
    # Dimension 1: Rhythm & Tempo Mastery (30%)
    rhythm_tempo_data: Dict[str, Any] = field(default_factory=dict)
    
    # Dimension 2: Sound Quality (20%)
    sound_quality_data: Dict[str, Any] = field(default_factory=dict)
    
    # Dimension 3: Technical Virtuosity (20%)
    technical_virtuosity_data: Dict[str, Any] = field(default_factory=dict)
    
    # Dimension 4: Phrasing & Diction (15%)
    phrasing_diction_data: Dict[str, Any] = field(default_factory=dict)
    
    # Dimension 5: Communicativeness (15%)
    communicativeness_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Validation status
    validation_report: Dict[str, Any] = field(default_factory=dict)
```

---

## Processing Pipeline

### Stage 1: Data Collection
```python
def collect_upstream_data(output_dir: Path) -> InferenceCoreInputs:
    """
    Locate and load all upstream layer outputs
    - Validate file existence
    - Load JSON files
    - Parse data structures
    - Handle missing optional data
    """
```

### Stage 2: Feature Extraction
```python
def extract_grading_features(inputs: InferenceCoreInputs) -> Dict:
    """
    Extract specific features needed for each grading dimension
    - Map data to grading requirements
    - Compute derived metrics
    - Handle edge cases
    """
```

### Stage 3: Metric Computation
```python
def compute_grading_metrics(features: Dict) -> GradingInputPackage:
    """
    Calculate all intermediate metrics needed by Grading Layer
    - Onset accuracy metrics
    - Pitch deviation metrics
    - Fluency metrics
    - Expression metrics
    - Coherence metrics
    """
```

### Stage 4: Validation
```python
def validate_grading_package(package: GradingInputPackage) -> ValidationReport:
    """
    Ensure all required data is present and valid
    - Check completeness
    - Validate ranges
    - Flag anomalies
    - Report quality
    """
```

### Stage 5: Formatting & Export
```python
def export_grading_package(package: GradingInputPackage, output_path: Path):
    """
    Save formatted package for Grading Layer
    - JSON export
    - Structured format
    - Human-readable
    - Version control
    """
```

---

## Error Handling & Edge Cases

### Missing Data Strategies

1. **Required Data Missing**: Raise exception with clear error message
2. **Optional Data Missing**: Use defaults, flag in validation report
3. **Partial Data**: Compute what's possible, mark incomplete dimensions

### Data Quality Issues

1. **Alignment Failure**: Fall back to simpler metrics, reduce confidence
2. **Transcription Errors**: Use pitch contour analysis as backup
3. **Empty Segments**: Mark as silence, handle gracefully
4. **Invalid Ranges**: Clip values, log warnings

### Validation Criteria

```python
validation_rules = {
    "onset_times": {
        "min": 0.0,
        "max": audio_duration,
        "required": True
    },
    "pitch_midi": {
        "min": 0,
        "max": 127,
        "required": True
    },
    "tempo_bpm": {
        "min": 20,
        "max": 300,
        "required": True
    },
    "confidence_scores": {
        "min": 0.0,
        "max": 1.0,
        "required": False
    }
}
```

---

## Implementation Classes

### Core Classes

1. **`InferenceCore`**: Main orchestrator
2. **`DataCollector`**: Upstream data gathering
3. **`RhythmTempoAnalyzer`**: Dimension 1 metrics
4. **`SoundQualityAnalyzer`**: Dimension 2 metrics
5. **`TechnicalVirtuosityAnalyzer`**: Dimension 3 metrics
6. **`PhrasingDictionAnalyzer`**: Dimension 4 metrics
7. **`CommunicativenessAnalyzer`**: Dimension 5 metrics
8. **`GradingPackageFormatter`**: Output structuring
9. **`ValidationEngine`**: Data quality checks

---

## File Structure

```
INFERENCE_CORE/
├── __init__.py
├── inference_core.py              # Main InferenceCore class
├── data_collector.py              # Upstream data collection
├── analyzers/
│   ├── __init__.py
│   ├── rhythm_tempo.py           # Rhythm & Tempo analysis
│   ├── sound_quality.py          # Sound Quality analysis
│   ├── technical_virtuosity.py   # Technical Virtuosity analysis
│   ├── phrasing_diction.py       # Phrasing & Diction analysis
│   └── communicativeness.py      # Communicativeness analysis
├── formatters/
│   ├── __init__.py
│   └── grading_package.py        # Output formatting
├── validators/
│   ├── __init__.py
│   └── data_validator.py         # Validation logic
├── utils/
│   ├── __init__.py
│   ├── metric_utils.py           # Common metric computations
│   └── data_utils.py             # Data processing utilities
├── tests/
│   ├── test_inference_core.py
│   └── test_analyzers.py
└── README.md
```

---

## Dependencies

- `numpy`: Numerical computations
- `scipy`: Statistical analysis, signal processing
- `pandas`: Data manipulation
- `json`: Data I/O
- `pathlib`: File handling
- `dataclasses`: Data structures
- `typing`: Type hints
- `librosa`: Audio analysis utilities (optional)
- `pretty_midi`: MIDI utilities (optional)

---

## Next Steps

1. Implement core data collection and validation
2. Build analyzer classes for each dimension
3. Create comprehensive test suite
4. Document API and usage examples
5. Integration testing with upstream layers
6. Performance optimization
7. Error handling refinement

---

**End of Design Specification**
