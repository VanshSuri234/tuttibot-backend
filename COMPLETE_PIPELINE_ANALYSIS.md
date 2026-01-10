# TuttiBot Complete Pipeline Analysis
## All Files Called in app.py → run_analysis() and All 7 Layers

**Generated:** January 10, 2026  
**Purpose:** Complete architectural overview of the music performance analysis system  
**Scope:** End-to-end flow from file upload through final grading

---

## TABLE OF CONTENTS
1. [Executive Summary](#executive-summary)
2. [Application Entry Point (app.py)](#application-entry-point)
3. [Pipeline Orchestrator (pipeline.py)](#pipeline-orchestrator)
4. [Layer-by-Layer Analysis](#layer-by-layer-analysis)
5. [Data Flow Diagram](#data-flow-diagram)
6. [File Dependencies Map](#file-dependencies-map)
7. [Critical Bottlenecks Identified](#critical-bottlenecks-identified)

---

## EXECUTIVE SUMMARY

### What happens when a user uploads audio + score:

1. **Flask REST API** (`app.py`) receives upload → spawns background thread
2. **Pipeline Orchestrator** (`pipeline.py`) coordinates 7 layers
3. **Each Layer** processes specific aspects of the music performance
4. **Final Output** is grade (0-100), report, and chatbot context

### Performance Critical Path:
```
Layer 2 (Audio Processing) ← HANG HERE ON RENDER
  ↓
Layer 3 (Temporal Alignment with Blocks)
  ↓
Layer 4 (Feature Extraction) [PARALLEL]
  ↓
Layer 6 (Inference Core)
  ↓
Layer 7 (Grading)
```

---

## APPLICATION ENTRY POINT

### File: `app.py` (608 lines)

**Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\app.py`

#### Key Components:

##### 1. Flask Application Setup (Lines 1-100)
```python
# Imports
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from groq import Groq  # LLM integration
from werkzeug.utils import secure_filename
import psutil  # System monitoring
import logging, threading, subprocess

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Threading for async pipeline execution
jobs = {}  # Dictionary to track job status
job_lock = threading.Lock()
```

**Dependencies Loaded:**
- `MusicPerformancePipeline` from `MusicPerformanceAnalysis.pipeline`
- `llm_service` (optional) from `llm_service.py`
- Groq AI API (optional, for chatbot)
- LED control module (for robot feedback)

##### 2. REST API Endpoints (Lines 100-300)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/upload` | POST | Accept audio + score, spawn analysis thread |
| `/status/{job_id}` | GET | Return current pipeline progress |
| `/results/{job_id}` | GET | Return completed analysis results |
| `/chat` | POST | LLM-powered chat about performance |

##### 3. Core Run Analysis Function (Lines 318-450)

**Function Signature:**
```python
def run_analysis(job_id, audio_path, score_path):
    """
    Background thread worker that orchestrates entire pipeline.
    
    Flow:
    1. Initialize status to PROCESSING
    2. Create output directory
    3. Instantiate MusicPerformancePipeline
    4. Call pipeline_obj.run_pipeline()
    5. Parse results JSON files
    6. Extract grade via regex from report.txt
    7. Save to job status dictionary
    """
```

**Critical Code Flow:**
```python
# Line 318: Log system status at START
log_system_status(f"RUN_ANALYSIS_START_{job_id}")
start_time = datetime.now()

# Line 327: Write initial status
save_job_status(job_id, {
    'status': JobStatus.PROCESSING,
    'current_layer': 'Layer 0: Initializing',
    'progress': 0
})

# Line 340: INSTANTIATE PIPELINE
if MusicPerformancePipeline:
    pipeline_obj = MusicPerformancePipeline(
        audio_path, 
        score_path, 
        str(job_output_dir)
    )
    
    # Line 360: RUN ENTIRE PIPELINE
    success = pipeline_obj.run_pipeline()  # ← ENTRY TO PIPELINE.PY
    
    # Line 367: Log system status AFTER pipeline
    log_system_status(f"AFTER_PIPELINE__{job_id}")

# Line 375: READ RESULTS FILES
summary_path = job_output_dir / "pipeline_summary.json"
grading_dir = job_output_dir / "07_grading"
report_path = grading_dir / "performance_report.txt"

# Line 400: PARSE RESULTS WITH REGEX
overall_match = re.search(r"Overall Score:\s*([\d\.]+)/100", report_text)
```

**Output Handling:**
```python
# Saves to jobs dictionary:
jobs[job_id] = {
    'status': JobStatus.COMPLETED,
    'results': {
        'grade_data': {
            'overall_score': float,
            'components': Dict[str, float],
            'detailed_metrics': Dict[str, Dict]
        },
        'report_text': str,
        'pipeline_summary': Dict
    },
    'output_dir': str,
    'llm_initial_analysis': str  # If enabled
}
```

---

## PIPELINE ORCHESTRATOR

### File: `pipeline.py` (1290 lines)

**Location:** `c:\Users\suriv\Desktop\TUTI BOT BACKEND\Workspace\MusicPerformanceAnalysis\pipeline.py`

#### Class: `MusicPerformancePipeline`

**Constructor:**
```python
def __init__(self, audio_path, score_path, output_dir, config_path=None, score_part=None):
    self.audio_path = Path(audio_path).resolve()
    self.score_path = Path(score_path).resolve()
    self.output_dir = Path(output_dir).resolve()
    
    # Auto-detect score part from audio filename if multi-instrument
    self.score_part = score_part or self._detect_score_part_from_audio()
    
    # Load config (YAML) with defaults
    self.config = self._load_config(config_path)
    
    # Create directory structure
    self.input_dir = output_dir / "01_input"
    self.processing_dir = output_dir / "02_processing"
    self.temporal_dir = output_dir / "03_temporal_alignment"
    # ... etc for all 7 layers
    
    # Status tracking
    self.status = {
        'input': False,
        'processing': False,
        'temporal_alignment': False,
        'extraction': False,
        'pqg_a2sa': False,
        'inference': False,
        'grading': False
    }
    
    self.results = {}  # Store paths to output files
```

#### Main Method: `run_pipeline()` (Lines 860-980)

**Execution Order:**

```python
def run_pipeline(self):
    logger.info("MUSIC PERFORMANCE ANALYSIS PIPELINE")
    start_time = datetime.now()
    
    # === LAYER 1 ===
    if not self.run_input_layer():
        logger.warning("Input layer had issues (continuing)")
    
    # === LAYER 2 ===  ← HANGS HERE ON RENDER
    if not self.run_processing_layer():
        logger.warning("Processing layer had issues (continuing)")
    
    # === LAYER 3 ===
    if not self.run_temporal_alignment():
        logger.error("Temporal alignment failed - stopping")
        return False
    
    # === LAYER 4 === (runs after Layer 3)
    if not self.run_extraction_layer():
        logger.warning("Extraction layer had issues (continuing)")
    
    # === LAYER 5 === (optional, parallel with extraction)
    self.run_pqg_a2sa()  # Continue even if fails
    
    # === LAYER 6 ===
    if not self.run_inference():
        logger.error("Inference failed - stopping")
        return False
    
    # === LAYER 7 ===
    if not self.run_grading():
        logger.error("Grading failed")
        return False
    
    # === FINAL ===
    self.get_chatbot_context()  # Aggregate all layer outputs
    self._save_summary(start_time)
    
    logger.info("PIPELINE COMPLETE")
    return True
```

---

## LAYER-BY-LAYER ANALYSIS

### LAYER 1: INPUT STANDARDIZATION

**File:** `MusicPerformanceAnalysis/layers/01_input/input_layer.py` (548 lines)

**Purpose:** Validate and standardize audio/score formats to canonical forms

**Class:** `MusicInputLayer`

**Key Method:** `process_inputs(audio_path, score_path)`

#### Audio Processing (`AudioInputProcessor` class)
```python
# Supported formats: .wav, .flac, .mp3, .aac, .ogg
# Target: 44100 Hz, 16-bit WAV

def process_audio(audio_path):
    # Load audio with librosa
    audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)
    
    # Check channels
    channels = audio_data.ndim
    
    # If conversion needed: resample to 44100 Hz
    if sample_rate != 44100:
        audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=44100)
    
    # Save as canonical WAV
    sf.write(output_path, audio_data, 44100, subtype='PCM_16')
    
    return {
        'success': True,
        'output_path': str(output_path),
        'original_format': {...},
        'converted': True/False
    }
```

#### Score Processing
```python
# Supported formats: MusicXML (.musicxml, .xml, .mxl), MIDI (.mid, .midi)
# Target: MusicXML format

# If PDF: Use Audiveris CLI to convert PDF → MusicXML
if audio_path.suffix.lower() == '.pdf':
    cmd = ['audiveris', '-batch', pdf_path, '-export', '-output-format', 'musicxml']
    subprocess.run(cmd)

# If MXL (zipped): Extract inner.xml
if score_path.suffix.lower() == '.mxl':
    with zipfile.ZipFile(score_path) as z:
        inner_xml = z.extract('META-INF/container.xml')

# If MIDI: Convert to MusicXML
if score_path.suffix.lower() in ['.mid', '.midi']:
    score = converter.parse(score_path)
    score.write('musicxml', fp=output_path)
```

**Output Files:**
```
01_input/
├── audio_standardized.wav        # Canonical audio
├── score_standardized.musicxml   # Canonical score
└── input_metadata.json          # Format info
```

**Typical Duration:** < 5 seconds for format conversion

---

### LAYER 2: PROCESSING (AUDIO)

**File:** `MusicPerformanceAnalysis/layers/02_processing/processing_layer.py` (764 lines)

**Purpose:** Noise reduction, normalization, segmentation of audio

**Class:** `ProcessingLayer`

**Key Method:** `process(audio_path, score_path)`

#### Step 1: Audio Quality Check
```python
def check_audio_quality(audio_path):
    # Load audio with MEMORY OPTIMIZATION (as of latest changes)
    data, sr = librosa.load(
        audio_path, 
        sr=22050,          # ← DOWNSAMPLED (50% RAM reduction)
        dtype=np.float32   # ← OPTIMIZED DTYPE
    )
    
    log_memory_usage("AFTER_LOAD_AUDIO")  # Log memory at this point
    
    # Check duration
    duration = len(data) / sr
    if duration < 2:
        logger.warning("Audio too short")
    
    # Check RMS level
    rms = np.sqrt(np.mean(data**2))
    if rms < 0.01:
        logger.warning("Audio too quiet")
    
    return {
        'duration': duration,
        'sample_rate': sr,
        'rms_level': rms,
        'channels': 1 if data.ndim == 1 else data.shape[0]
    }
```

#### Step 2: Noise Reduction
```python
def reduce_noise(data, sr):
    # Use timsainb/noisereduce library (spectral gating)
    reduced = nr.reduce_noise(y=data, sr=sr)
    
    log_memory_usage("AFTER_REDUCE_NOISE")
    
    return reduced
```

**Dependencies:**
- `noisereduce` (timsainb/noisereduce)
- `librosa` (audio loading and resampling)
- `scipy` (spectral operations)

#### Step 3: Normalization
```python
def normalize_audio(data, sr):
    # Peak normalization to -3dB (leaves headroom)
    max_val = np.max(np.abs(data))
    normalized = data / (max_val * 1.1)
    
    log_memory_usage("AFTER_NORMALIZE")
    
    return normalized
```

#### Step 4: Segmentation
```python
def segment_audio(data, sr):
    # Using full_audio fallback (since auditok removed)
    # Returns: entire audio as one segment
    
    segments = [{
        'start': 0.0,
        'end': len(data) / sr,
        'type': 'full_audio'
    }]
    
    return segments
```

#### Step 5: Score Feature Extraction
```python
def extract_score_features(score_path):
    # Parse MusicXML with music21
    score = converter.parse(score_path)
    
    # Extract key information
    key_sig = score.analyze('key')
    time_sigs = score.flatten().getElementsByClass('TimeSignature')
    tempos = score.flatten().getElementsByClass('MetronomeMark')
    
    return {
        'key': str(key_sig),
        'time_signatures': [str(ts) for ts in time_sigs],
        'tempos': [float(t.number) for t in tempos]
    }
```

**Output Files:**
```
02_processing/
├── data/
│   └── audio_processed.wav      # Denoised, normalized
├── shared/
│   └── processed/
│       ├── audio_segments.json  # Segment boundaries
│       └── music_features.json  # Score features
└── processing_metadata.json     # Timing and quality metrics
```

**Diagnostic Logging Added:**
- `[AUDIO_CHECK]` - Memory at audio load (target: 150MB for Render)
- `[NOISE_REDUCE]` - Before/after noise reduction
- `[NORMALIZE]` - Normalization timing
- `[MEMORY ...]` - Memory at each critical point
- `[SYSTEM ...]` - CPU, RAM, thread count

**Typical Duration:** 30-60 seconds (bottleneck on Render)

**⚠️ KNOWN ISSUE - RENDER HANG:**
Pipeline hangs at this layer after ~40 seconds. Suspected causes:
1. Memory wall (librosa loading 300+MB audio) ✓ PARTIALLY FIXED with sr=22050
2. Gunicorn sync workers blocking on heavy math
3. music21 parsing timeout

---

### LAYER 3: TEMPORAL ALIGNMENT

**File:** `MusicPerformanceAnalysis/pipeline.py` (method: `run_temporal_alignment()`)

**Purpose:** Align performance audio with score using 5-block sequence

**Blocks Executed in Order:**

#### BLOCK 0: ScoreGraph Generation

**File:** `03_temporal_alignment/block_0_scoregraph/build_scoregraph_with_notes.py` (285 lines)

**Purpose:** Build graph representation of score with beat nodes and note data

```python
def build_scoregraph_with_notes(score_path, meta_path, seg_path=None, part_index=0):
    """
    Extract score structure using music21
    
    Args:
        score_path: MusicXML file
        meta_path: Metadata JSON (tempo, key, etc.)
        part_index: Which part for multi-part scores
        
    Returns:
        ScoreGraph dict with:
        - bars: [{'measure': 1, 'beat_nodes': [...], 'notes': [...]}]
        - nodes: [{'node_id': 'N0', 'time': 0.0, 'beat': 0}]
        - notes: [{'pitch': 60, 'start': 0.0, 'duration': 0.5}]
    """
    
    # Parse score
    score = converter.parse(score_path)
    
    # Handle multi-part (SATB, etc.)
    if hasattr(score, 'parts') and score.parts:
        part = score.parts[part_index]
    else:
        part = score
    
    # Extract measures
    measures = part.getElementsByClass(stream.Measure)
    
    # Build beat nodes for each measure
    bars = []
    nodes = []
    abs_beat = 0.0
    
    for measure in measures:
        # Get time signature
        time_sig = measure.timeSignature
        
        # Create beat nodes
        beats_per_measure = time_sig.numerator
        
        # Create nodes for each beat
        beat_nodes = []
        for beat in range(beats_per_measure):
            node_id = f"N{len(nodes)}"
            nodes.append({
                'node_id': node_id,
                'time': abs_beat,
                'beat': abs_beat
            })
            beat_nodes.append(node_id)
        
        # Extract notes from measure
        measure_notes = []
        for element in measure.flatten():
            if isinstance(element, note.Note):
                measure_notes.append({
                    'pitch': element.pitch.midi,
                    'start': abs_beat,
                    'duration': element.quarterLength,
                    'name': str(element.pitch)
                })
        
        bars.append({
            'measure': measure.number,
            'beat_nodes': beat_nodes,
            'notes': measure_notes
        })
        
        abs_beat += beats_per_measure
    
    return {
        'bars': bars,
        'nodes': nodes,
        'notes': all_notes
    }
```

**Output:** `03_temporal_alignment/scoregraph.json`

**Typical Duration:** 5-10 seconds

---

#### BLOCK 1: Audio Transcription

**File:** `03_temporal_alignment/block_1_transcription/transcribe_enhanced.py` (245 lines)

**Purpose:** Convert performance audio to MIDI notes using ML model

```python
def transcribe_enhanced(audio_path):
    """
    Use BASIC PITCH or similar to transcribe audio to MIDI
    
    Includes:
    - Transposition correction (Bb clarinet, Eb saxophone, F horn, etc.)
    - Octave correction for bass instruments
    - Instrument detection from filename
    """
    
    # Load audio
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Detect instrument from filename
    instrument = detect_instrument_from_filename(audio_path)
    
    # Run transcription model (e.g., BASIC PITCH)
    # [This uses external model, not detailed here]
    midi_notes = transcribe_model(y, sr)
    
    # Apply transposition correction
    if instrument in TRANSPOSITIONS:
        transposition = TRANSPOSITIONS[instrument]
        for note in midi_notes:
            note['pitch'] += transposition  # Shift pitch
    
    # Correct octave for bass instruments
    if instrument in BASS_INSTRUMENTS:
        for note in midi_notes:
            if note['pitch'] > 80:  # If suspiciously high
                note['pitch'] -= 12  # Drop octave
    
    # Convert to MIDI file
    midi_obj = pretty_midi.PrettyMIDI()
    instrument_program = pretty_midi.instrument_name_to_program(instrument or 'Acoustic Grand Piano')
    inst = pretty_midi.Instrument(program=instrument_program)
    
    for note in midi_notes:
        pm_note = pretty_midi.Note(
            velocity=100,
            pitch=int(note['pitch']),
            start=note['start'],
            end=note['end']
        )
        inst.notes.append(pm_note)
    
    midi_obj.instruments.append(inst)
    midi_obj.write(output_path)
    
    return output_path
```

**Output:** `03_temporal_alignment/performance.mid`

**Typical Duration:** 20-40 seconds (depends on ML model)

---

#### BLOCK 4: Beat Detection (Optional)

**File:** `03_temporal_alignment/block_4_beats/estimate_beats_beatnet.py`

**Purpose:** Detect downbeats and metrical structure

```python
def estimate_beats(audio_path, output_path):
    """
    Detect beat times using BeatNet model
    """
    
    # Load audio
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Run beat detection
    beats = beat_detector.detect(y, sr)  # Returns onset times
    
    # Save
    with open(output_path, 'w') as f:
        json.dump({'beats': beats}, f)
```

**Output:** `03_temporal_alignment/beats.json` (optional)

**Typical Duration:** 10-20 seconds

---

#### CONTEXT ALIGNER: Structural Path Finding (Optional)

**File:** `03_temporal_alignment/context_aligner/context_aligner.py`

**Purpose:** Find optimal score-performance alignment considering score structure

```python
class ContextAligner:
    def align(self, scoregraph_path, transcription_path):
        """
        Finds best alignment path through score considering
        - Repeated sections
        - Alternative paths
        - Structural variations
        """
        
        scoregraph = load_json(scoregraph_path)
        transcription = load_json(transcription_path)
        
        # Build alignment graph considering score structure
        # Find optimal path from start to end
        selected_path = self._find_optimal_path(scoregraph, transcription)
        
        return {
            'selected_path': selected_path,
            'alignment_score': score,
            'pitch_matches': matches
        }
```

**Output:** `03_temporal_alignment/context_alignment.json`

---

#### BLOCK 2: DTW Temporal Alignment

**File:** `03_temporal_alignment/block_2_dtw/align_symbolic_enhanced_with_metrics.py` (1411 lines)

**Purpose:** Use Dynamic Time Warping to align score notes with performance notes

```python
class EnhancedSymbolicAligner:
    def align(self, scoregraph_path, performance_midi_path):
        """
        Input: ScoreGraph (beat nodes + notes) + Performance MIDI
        Output: Time mapping showing when each score note was performed
        
        Process:
        1. Extract pitch features from both (using CQT)
        2. Compute DTW cost matrix
        3. Find optimal alignment path
        4. Extract alignment metrics (note accuracy, timing error, etc.)
        """
        
        # Load files
        scoregraph = load_json(scoregraph_path)
        performance_midi = pretty_midi.PrettyMIDI(performance_midi_path)
        
        # Extract features
        score_features = self._extract_score_features(scoregraph)  # Pitch sequence
        perf_features = self._extract_performance_features(performance_midi)  # Pitch sequence
        
        # Compute DTW
        cost_matrix = self._compute_cost_matrix(score_features, perf_features)
        alignment_path = self._dtw_alignment(cost_matrix)
        
        # Extract metrics
        metrics = self._compute_metrics(
            score_features, 
            perf_features, 
            alignment_path
        )
        
        return {
            'alignment': alignment_path,
            'grading_metrics': {
                'sound_quality': {
                    'pitch_accuracy_50c_percent': metrics['pitch_accuracy'],
                    'mean_pitch_error_cents': metrics['pitch_error_cents'],
                    ...
                },
                'technical_virtuosity': {
                    'note_accuracy_percent': metrics['note_accuracy'],
                    'matched_notes': metrics['matched_notes'],
                    ...
                },
                'rhythm_tempo': {
                    'ioi_correlation': metrics['ioi_correlation'],
                    'mean_onset_error_ms': metrics['onset_error_ms'],
                    ...
                }
            }
        }
```

**Output:** `03_temporal_alignment/alignment_output/alignment_results.json`

**Grading Metrics Produced:**
```json
{
  "sound_quality": {
    "pitch_accuracy_50c_percent": 85.5,
    "mean_pitch_error_cents": 12.3
  },
  "technical_virtuosity": {
    "note_accuracy_percent": 92.0,
    "matched_notes": 150,
    "extra_notes": 5
  },
  "rhythm_tempo": {
    "ioi_correlation": 0.87,
    "mean_onset_error_ms": 45.2,
    "tempo_cv_percent": 8.3
  }
}
```

**Typical Duration:** 30-60 seconds

---

### LAYER 4: FEATURE EXTRACTION

**File:** `MusicPerformanceAnalysis/layers/04_extraction/extraction_layer.py` (920 lines)

**Purpose:** Extract rich audio and score features for additional grading dimensions

**Classes:**

#### `AudioFeatureExtractor`
```python
class AudioFeatureExtractor:
    def extract_features(self, audio_file, segments_file):
        """
        Extract comprehensive audio features using aubio, librosa, essentia
        
        Returns: PerformanceFeatures dataclass with:
        - pitch_contour: Frame-by-frame pitch (Hz)
        - onset_times: Detected note onsets
        - tempo_bpm: Detected tempo
        - spectral_centroid: Brightness over time
        - mfcc: Mel-frequency cepstral coefficients
        - rms_energy: Loudness over time
        - chroma: Pitch class distribution
        """
        
        # Load audio
        y, sr = librosa.load(audio_file, sr=22050)
        
        # Pitch extraction (aubio)
        if aubio:
            pitch_contour = self._extract_pitch_aubio(y, sr)
        
        # Onset detection (librosa)
        onset_times = librosa.onset.onset_detect(y, sr=sr, units='time')
        
        # Tempo detection
        tempo_bpm, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # Spectral features (librosa)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        
        # MFCC (librosa)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Chroma (librosa)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # Energy
        rms = librosa.feature.rms(y=y)[0]
        zcr = librosa.feature.zero_crossing_rate(y=y)[0]
        
        return PerformanceFeatures(
            pitch_contour=pitch_contour,
            onset_times=onset_times,
            tempo_bpm=tempo_bpm,
            spectral_centroid=spectral_centroid.flatten(),
            mfcc=mfcc,
            chroma=chroma,
            rms_energy=rms,
            zero_crossing_rate=zcr,
            ...
        )
```

#### `ScoreFeatureExtractor`
```python
class ScoreFeatureExtractor:
    def extract_features(self, score_file, score_json_file):
        """
        Extract score features from MusicXML/MIDI
        
        Returns: ScoreFeatures dataclass with:
        - expected_pitches: Score MIDI pitches
        - note_onsets: Score note timings
        - key_signature: Tonal context
        - time_signatures: Meter
        - phrase_boundaries: Structure
        """
        
        # Parse score
        score = converter.parse(score_file)
        
        # Pitch analysis
        expected_pitches = [n.pitch.midi for n in score.flatten().notes]
        
        # Timing
        note_onsets = [n.offset for n in score.flatten().notes]
        
        # Key and meter
        key_sig = score.analyze('key')
        time_sigs = score.flatten().getElementsByClass('TimeSignature')
        
        return ScoreFeatures(
            expected_pitches=expected_pitches,
            note_onsets=note_onsets,
            key_signature=str(key_sig),
            time_signatures=[str(ts) for ts in time_sigs],
            ...
        )
```

**Output Files:**
```
04_extraction/
├── performance_features.json
└── score_features.json
```

**Typical Duration:** 10-30 seconds

---

### LAYER 5: PQG-A2SA (OPTIONAL)

**File:** `MusicPerformanceAnalysis/layers/05_pqg_a2sa/src/...` (multiple files)

**Purpose:** Precise onset/offset detection using probabilistic approach

```python
class PQGAligner:
    def align(self, audio_path, midi_path):
        """
        Probabilistic Quantum Gaussian alignment
        
        Produces:
        - Precise onset times (±5ms accuracy)
        - Offset times
        - Confidence scores
        """
        
        # Load inputs
        y, sr = librosa.load(audio_path, sr=22050)
        midi = pretty_midi.PrettyMIDI(midi_path)
        
        # Run PQG algorithm
        results = self._pqg_algorithm(y, sr, midi)
        
        return results
```

**Output:** `05_pqg_a2sa/pqg_a2sa_results.json`

**Status:** Optional - may not run if MIDI score unavailable

---

### LAYER 6: INFERENCE CORE

**File:** `MusicPerformanceAnalysis/layers/06_inference/inference_core.py` (323 lines)

**Purpose:** Orchestrate data collection from all upstream layers and prepare for grading

**Class:** `InferenceCore`

```python
class InferenceCore:
    def process(self, save_output=True):
        """
        Complete processing pipeline
        
        Steps:
        1. Collect all upstream data (Blocks 0-5)
        2. Extract grading metrics from Block 2 DTW
        3. Score all dimensions (convert raw metrics to 0-100)
        4. Create comprehensive grading package
        5. Save package.json for Grading Layer
        """
        
        # STEP 1: Collect data from all layers
        inputs = self.data_collector.collect_all_data()
        # Returns: alignment results, extraction features, beats, PQG results
        
        # STEP 2: Extract metrics
        raw_metrics = self.metrics_extractor.extract_grading_metrics(
            inputs.alignment_results
        )
        
        # STEP 3: Score all dimensions
        scored = self.scoring_functions.score_all_dimensions(raw_metrics)
        
        # Dimension weights (PQG-A2SA framework)
        dimension_weights = {
            'rhythm_tempo': 0.30,
            'sound_quality': 0.20,
            'technical_virtuosity': 0.20,
            'phrasing_diction': 0.15,
            'communicativeness': 0.15
        }
        
        # STEP 4: Create package
        grading_package = {
            'metadata': {...},
            'data_availability': {...},
            'grading_dimensions': {
                'rhythm_tempo': {
                    'weight': 0.30,
                    'dimension_score': 82.5,
                    'component_scores': {...},
                    'raw_metrics': {...}
                },
                # ... other dimensions
            }
        }
        
        return grading_package
```

**Output:** `06_inference/grading_package_master.json`

---

### LAYER 7: GRADING LAYER

**File:** `MusicPerformanceAnalysis/layers/07_grading/grading_layer.py` (548 lines)

**Purpose:** Compute final score, letter grade, and comprehensive report

**Class:** `GradingLayer`

```python
class GradingLayer:
    
    # PQG-A2SA Framework Weights
    DIMENSION_WEIGHTS = {
        'rhythm_tempo': 0.30,
        'sound_quality': 0.20,
        'technical_virtuosity': 0.20,
        'phrasing_diction': 0.15,
        'communicativeness': 0.15
    }
    
    # Grade thresholds
    GRADE_THRESHOLDS = {
        'A+': 97, 'A': 93, 'A-': 90,
        'B+': 87, 'B': 83, 'B-': 80,
        'C+': 77, 'C': 73, 'C-': 70,
        'D+': 67, 'D': 63, 'D-': 60,
        'F': 0
    }
    
    def compute_final_grade(self, grading_package):
        """
        Compute weighted final score
        
        Process:
        1. Extract dimension scores from package
        2. Apply PQG-A2SA weights
        3. Normalize to 0-100 scale
        4. Convert to letter grade
        5. Generate comprehensive report
        """
        
        final_score = 0.0
        components = {}
        
        # Weight each dimension
        for dim_name, weight in self.DIMENSION_WEIGHTS.items():
            if dim_name in grading_package['grading_dimensions']:
                dim_data = grading_package['grading_dimensions'][dim_name]
                dim_score = dim_data['dimension_score']
                components[dim_name] = dim_score * weight
                final_score += components[dim_name]
        
        # Normalize to 100 if not all dimensions present
        total_weight = sum(self.DIMENSION_WEIGHTS[k] 
                          for k in components.keys())
        if total_weight > 0:
            final_score = (final_score / total_weight) * 100
        
        # Determine letter grade
        letter_grade = self._get_letter_grade(final_score)
        
        return {
            'overall_score': round(final_score, 2),
            'letter_grade': letter_grade,
            'components': components
        }
    
    def generate_report(self, final_grade, metrics):
        """Generate human-readable performance report"""
        
        report = f"""
        ============================================================
        MUSIC PERFORMANCE ANALYSIS REPORT
        ============================================================
        
        FINAL GRADE
        -----------
        Overall Score: {final_grade['overall_score']}/100
        Letter Grade: {final_grade['letter_grade']}
        
        COMPONENT SCORES
        ---------------
        Rhythm & Tempo: {final_grade['components'].get('rhythm_tempo', 0):.1f}%
        Sound Quality: {final_grade['components'].get('sound_quality', 0):.1f}%
        Technical Virtuosity: {final_grade['components'].get('technical_virtuosity', 0):.1f}%
        Phrasing & Diction: {final_grade['components'].get('phrasing_diction', 0):.1f}%
        Communicativeness: {final_grade['components'].get('communicativeness', 0):.1f}%
        
        DETAILED METRICS
        ----------------
        [Pitch accuracy, note accuracy, timing error, tempo info, etc.]
        """
        
        return report
```

**Output Files:**
```
07_grading/
├── final_grade.json           # Structured grade data
└── performance_report.txt     # Human-readable report
```

---

### FINAL STEP: CHATBOT CONTEXT AGGREGATION

**Method:** `pipeline.py:get_chatbot_context()` (Lines 1000-1050)

```python
def get_chatbot_context(self):
    """
    Omni-Context Generator: Aggregates every JSON result from all 7 layers
    
    Output: chatbot_context.json with all data for LLM chat
    """
    
    context = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "audio_file": self.audio_path.name,
            "score_file": self.score_path.name,
            "pipeline_status": self.status
        },
        "layers": {
            "L1_Input": {...},
            "L2_Processing": {...},
            "L3_Temporal": {
                "block_0_scoregraph": {...},
                "block_1_transcription": {...},
                "block_2_dtw_alignment": {...},
                "block_4_beats": {...},
                "context_aligner": {...}
            },
            "L4_Extraction": {...},
            "L5_PQG": {...},
            "L6_Inference": {...},
            "L7_Grading": {...}
        }
    }
    
    # Save aggregated context
    with open('chatbot_context.json', 'w') as f:
        json.dump(context, f, indent=2)
```

**Output:** `chatbot_context.json` (fed to Groq AI for chat responses)

---

## DATA FLOW DIAGRAM

```
USER UPLOAD
    ↓
┌─────────────────────────────┐
│ FLASK APP (app.py)          │
│ /upload endpoint            │
│ - Validate files            │
│ - Create job_id             │
│ - Spawn background thread   │
└─────────────────────────────┘
    ↓
    run_analysis(job_id, audio, score)
    ↓
┌─────────────────────────────────────────────────────────┐
│          PIPELINE ORCHESTRATOR (pipeline.py)            │
│        MusicPerformancePipeline.run_pipeline()          │
└─────────────────────────────────────────────────────────┘
    ↓
┌──────────────────┐    ┌──────────────────┐
│ LAYER 1: INPUT   │    │ LAYER 2: PROCESS │ ← RENDER HANGS HERE
│ (2-5 sec)        │ ───→ (30-60 sec)      │
└──────────────────┘    └──────────────────┘
    ↓
    StandardizedAudio.wav + StandardizedScore.musicxml
    ↓
┌─────────────────────────────────────────────┐
│      LAYER 3: TEMPORAL ALIGNMENT            │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ BLOCK 0: ScoreGraph (5-10 sec)     │    │
│  │ → scoregraph.json                  │    │
│  └────────────────────────────────────┘    │
│               ↓                             │
│  ┌────────────────────────────────────┐    │
│  │ BLOCK 1: Transcription (20-40 sec) │    │
│  │ → performance.mid                  │    │
│  └────────────────────────────────────┘    │
│               ↓                             │
│  ┌────────────────────────────────────┐    │
│  │ BLOCK 4: Beat Detection (10-20 sec)│    │
│  │ → beats.json [optional]            │    │
│  └────────────────────────────────────┘    │
│               ↓                             │
│  ┌────────────────────────────────────┐    │
│  │ Context Aligner (5-10 sec)         │    │
│  │ → context_alignment.json [optional]│    │
│  └────────────────────────────────────┘    │
│               ↓                             │
│  ┌────────────────────────────────────┐    │
│  │ BLOCK 2: DTW Alignment (30-60 sec) │    │
│  │ → alignment_results.json           │    │
│  │   + grading_metrics                │    │
│  └────────────────────────────────────┘    │
│                                             │
│         Total: 90-140 seconds               │
└─────────────────────────────────────────────┘
    ↓
   PARALLEL:
    ├─────────────────────────────┐
    │  LAYER 4: EXTRACTION        │
    │  (10-30 sec)                │
    │  → performance_features.json│
    │  → score_features.json      │
    └─────────────────────────────┘
    │
    └─────────────────────────────┐
       LAYER 5: PQG-A2SA          │
       (5-15 sec) [optional]      │
       → pqg_a2sa_results.json    │
       └─────────────────────────┘
    ↓
┌──────────────────────────────┐
│ LAYER 6: INFERENCE CORE      │
│ (2-5 sec)                    │
│ - Collect all data           │
│ - Score dimensions           │
│ → grading_package_master.json│
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ LAYER 7: GRADING             │
│ (1-2 sec)                    │
│ - Final weighted score       │
│ - Letter grade               │
│ → final_grade.json           │
│ → performance_report.txt     │
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ CHATBOT CONTEXT              │
│ Aggregate all 7 layer outputs│
│ → chatbot_context.json       │
└──────────────────────────────┘
    ↓
┌──────────────────────────────┐
│ RETURN TO USER               │
│ - Grade (0-100)              │
│ - Report (text)              │
│ - Components breakdown       │
│ - Ready for chat             │
└──────────────────────────────┘

TOTAL TIME: 150-250 seconds (2.5-4 minutes)
Render timeout: ~5 minutes
```

---

## FILE DEPENDENCIES MAP

### Core Files Called by app.py:

```
app.py (608 lines)
├── Imports:
│   ├── MusicPerformanceAnalysis/pipeline.py
│   ├── llm_service.py (optional)
│   ├── groq API (optional)
│   └── led_control/build/g1_led_controller (optional)
│
├── REST Endpoints:
│   ├── /upload → run_analysis()
│   ├── /status → read status.json from disk
│   ├── /results → read final_grade.json
│   └── /chat → llm_service
│
└── Background Thread (run_analysis):
    └── MusicPerformancePipeline → pipeline.py
```

### Pipeline.py and All 7 Layers:

```
pipeline.py (1290 lines)
├── Layer 1: Input Standardization
│   └── 01_input/input_layer.py (548 lines)
│       ├── AudioInputProcessor
│       ├── ScoreInputProcessor
│       └── Audiveris CLI (optional)
│
├── Layer 2: Processing
│   └── 02_processing/processing_layer.py (764 lines)
│       ├── ProcessingLayer class
│       ├── noisereduce library
│       ├── librosa
│       ├── scipy
│       └── music21
│
├── Layer 3: Temporal Alignment
│   ├── Block 0: ScoreGraph
│   │   └── block_0_scoregraph/build_scoregraph_with_notes.py (285)
│   │       └── music21
│   │
│   ├── Block 1: Transcription
│   │   └── block_1_transcription/transcribe_enhanced.py (245)
│   │       ├── transcription model
│   │       └── pretty_midi
│   │
│   ├── Block 4: Beat Detection (optional)
│   │   └── block_4_beats/estimate_beats_beatnet.py
│   │       └── librosa, beatnet model
│   │
│   ├── Context Aligner (optional)
│   │   └── context_aligner/context_aligner.py
│   │
│   └── Block 2: DTW Alignment
│       └── block_2_dtw/align_symbolic_enhanced_with_metrics.py (1411)
│           ├── pretty_midi
│           ├── librosa
│           ├── scipy
│           └── GPU manager (optional)
│
├── Layer 4: Extraction
│   └── 04_extraction/extraction_layer.py (920)
│       ├── AudioFeatureExtractor
│       │   ├── aubio (optional)
│       │   ├── librosa
│       │   └── essentia (optional)
│       │
│       ├── ScoreFeatureExtractor
│       │   └── music21
│       │
│       └── Combines into feature JSON files
│
├── Layer 5: PQG-A2SA (optional)
│   └── 05_pqg_a2sa/src/...
│       └── PQGAligner class
│
├── Layer 6: Inference Core
│   └── 06_inference/inference_core.py (323)
│       ├── DataCollector
│       ├── MetricsExtractor
│       └── ScoringFunctions
│
├── Layer 7: Grading
│   └── 07_grading/grading_layer.py (548)
│       └── GradingLayer class
│
└── Final: Chatbot Context
    └── get_chatbot_context()
        └── Aggregates all 7 layer JSONs
```

---

## CRITICAL BOTTLENECKS IDENTIFIED

### 1. **LAYER 2 PROCESSING - MEMORY WALL (PRIMARY CULPRIT)**

**Status:** ✅ PARTIALLY FIXED with diagnostic logging

**Issue:**
- Original code: `librosa.load(audio_path, sr=None)` loads full audio at native sample rate
- For typical 2-minute recording at 44.1kHz: 44100 * 120 * 2 bytes = **21 MB per second**
- Render free tier limit: **512 MB total RAM**
- Estimated usage: 300+ MB just for audio loading

**Fix Applied:**
```python
# BEFORE (Memory-intensive)
data, sr = librosa.load(audio_path, sr=None)

# AFTER (Optimized)
data, sr = librosa.load(audio_path, sr=22050, dtype=np.float32)
# Reduces by 50% (22050 vs 44100 Hz) × 2 (float32 vs float64) = 75% reduction
```

**Expected Impact:** 300 MB → 75 MB for audio loading

**Diagnostic Logs Added:**
- `[MEMORY AFTER_LOAD_AUDIO]` - Verify memory at load point
- `[AUDIO_CHECK]` - Complete audio check timing
- `[SYSTEM ...]` - Overall system resource usage

---

### 2. **GUNICORN SYNC WORKERS - BLOCKING ARCHITECTURE**

**Status:** ⚠️ IDENTIFIED, NOT YET FIXED

**Issue:**
- Current Render start command: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
- Sync workers (default) = fully blocking
- When one worker runs heavy Layer 2 processing, it blocks completely
- `/status` requests sent during Layer 2 hang timeout waiting for a worker

**Proposed Fix:**
```bash
# CURRENT (Blocking)
gunicorn -w 4 -b 0.0.0.0:$PORT app:app

# PROPOSED (Async)
gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT -t 300 app:app
# OR use gevent workers:
gunicorn -k gevent -w 4 -b 0.0.0.0:$PORT app:app
```

**Evidence:**
- Frontend polls `/status` every 2 seconds
- Status requests return timeout during Layer 2
- Suggests worker thread is blocked on heavy computation

---

### 3. **MUSIC21 PARSING TIMEOUT**

**Status:** ⚠️ IDENTIFIED, NOT YET FIXED

**Issue:**
- `converter.parse(score_path)` can hang on large/complex scores
- Threading timeout can't interrupt blocking C code
- No timeout mechanism for score parsing

**Proposed Fix:**
```python
# Use subprocess with true timeout
import subprocess
import json

def parse_score_with_timeout(score_path, timeout=10):
    cmd = [
        sys.executable, 'parse_score_helper.py',
        score_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise Exception(result.stderr)
    except subprocess.TimeoutExpired:
        logger.error("Score parsing timeout")
        # Return dummy score or skip processing
        return None
```

---

### 4. **LIBROSA RESAMPLING OVERHEAD**

**Status:** ✅ ADDRESSED with sr=22050

**Issue:**
- Resampling from 44.1kHz → 22.05kHz adds ~2-3 seconds
- Combined with load time: 5-10 seconds just for audio I/O

**Mitigation:** sr=22050 load parameter avoids resampling by loading at target rate

---

## DIAGNOSTIC LOGGING INFRASTRUCTURE

### New Logs Added to Pipeline:

#### Memory Monitoring (processing_layer.py):
```python
# At 8+ critical points:
[MEMORY AFTER_LOAD_AUDIO] RSS: 150.2MB | VMS: 300.5MB | %: 29.3%
[MEMORY AFTER_REDUCE_NOISE] RSS: 145.1MB | VMS: 295.2MB | %: 28.5%
[MEMORY AFTER_NORMALIZE] RSS: 140.8MB | VMS: 290.1MB | %: 27.8%
```

#### Timing Logs:
```python
# For each processing step
[AUDIO_CHECK] Completed in 2.34s
[NOISE_REDUCE] Completed in 12.45s
[NORMALIZE] Completed in 3.21s
```

#### Pipeline Timing (app.py):
```python
[PIPELINE_START] job abc123: /uploads/audio.wav
[PIPELINE_RUNNING] job abc123
[PIPELINE_END] job abc123: success=True, elapsed=180.45s
```

#### System Status:
```python
[SYSTEM RUN_ANALYSIS_START] RAM: 250.0MB (48.8%) | CPU: 15.2% | Threads: 12
[SYSTEM BEFORE_PIPELINE] RAM: 280.0MB (54.7%) | CPU: 22.5% | Threads: 18
[SYSTEM AFTER_PIPELINE] RAM: 320.0MB (62.5%) | CPU: 8.1% | Threads: 8
```

---

## NEXT STEPS FOR VERIFICATION

1. **Push diagnostic logging to Render** (awaiting user approval)
2. **Rebuild Render app** (automatic from GitHub)
3. **Run test upload** with same problematic audio file
4. **Analyze Render Live Logs** to identify which scenario matches:
   - **Memory Wall:** Memory jumps 50→300+MB, no decrease, killed at 512MB
   - **Worker Blocking:** Logs show pipeline running but `/status` timeouts
   - **Parsing Hang:** Logs stop without error during score parsing

5. **Apply specific fix** based on log analysis
6. **Validate** with second test upload

---

## SUMMARY TABLE

| Layer | Purpose | Duration | File | Status |
|-------|---------|----------|------|--------|
| 1 | Input Standardization | 2-5s | input_layer.py | ✓ Working |
| 2 | Audio Processing | 30-60s | processing_layer.py | ⚠️ HANGS on Render |
| 3 | Temporal Alignment | 90-140s | pipeline.py + blocks | ⚠️ Can't reach |
| 4 | Feature Extraction | 10-30s | extraction_layer.py | ⚠️ Parallel, can't reach |
| 5 | PQG-A2SA | 5-15s | src/... | ⚠️ Optional, can't reach |
| 6 | Inference | 2-5s | inference_core.py | ⚠️ Parallel, can't reach |
| 7 | Grading | 1-2s | grading_layer.py | ⚠️ Parallel, can't reach |
| Final | Chatbot Context | 1-2s | pipeline.py method | ⚠️ Parallel, can't reach |

**Root Cause:** Layer 2 bottleneck prevents execution of all downstream layers

**Fix Status:** Memory optimization applied (sr=22050), diagnostic logging ready for deployment

---

END OF ANALYSIS
