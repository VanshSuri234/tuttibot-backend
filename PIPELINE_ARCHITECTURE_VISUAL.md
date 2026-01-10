# TuttiBot Pipeline Architecture Visualization

## HIGH-LEVEL SYSTEM ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────────────┐
│                        TUTTIBOT WEB BACKEND                          │
│                      (Flask + Gunicorn on Render)                    │
└──────────────────────────────────────────────────────────────────────┘

                              ┌─ FRONTEND
                              │ (React on Vercel)
                              │ Polls /status every 2s
                              │
┌─────────────────────────────┼─────────────────────────────────────┐
│                             │                                     │
│  ┌───────────────────────────────────────────────────────┐        │
│  │         FLASK REST API (app.py - 608 lines)          │        │
│  ├───────────────────────────────────────────────────────┤        │
│  │ POST   /upload → Accept audio + score                │        │
│  │ GET    /status/{job_id} → Return progress            │        │
│  │ GET    /results/{job_id} → Return grade + report     │        │
│  │ POST   /chat → LLM-powered chat (optional)           │        │
│  └───────────────────────────────────────────────────────┘        │
│              ↓                                                      │
│  ┌───────────────────────────────────────────────────────┐        │
│  │         Background Thread Spawner (run_analysis)     │        │
│  │  - Create job_id                                     │        │
│  │  - Validate inputs                                   │        │
│  │  - Instantiate MusicPerformancePipeline              │        │
│  │  - Spawn background thread                           │        │
│  └───────────────────────────────────────────────────────┘        │
│              ↓                                                      │
│  ┌───────────────────────────────────────────────────────┐        │
│  │   MUSIC PERFORMANCE PIPELINE (pipeline.py - 1290)    │        │
│  │                                                       │        │
│  │  orchestrator that coordinates 7 analysis layers    │        │
│  └───────────────────────────────────────────────────────┘        │
│              ↓                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7-LAYER PIPELINE DETAILED FLOW

```
INPUT: audio.wav + score.musicxml/midi
OUTPUT: grade (0-100) + report.txt + chatbot_context.json

┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────────────────────────────────────────────────┐            │
│  │  LAYER 1: INPUT STANDARDIZATION                     │            │
│  │  (input_layer.py - 548 lines)                       │            │
│  ├─────────────────────────────────────────────────────┤            │
│  │                                                     │            │
│  │  ┌──────────────┐      ┌──────────────┐           │            │
│  │  │   AUDIO      │      │    SCORE     │           │            │
│  │  │ Processing   │      │  Processing  │           │            │
│  │  ├──────────────┤      ├──────────────┤           │            │
│  │  │ • Check format        • Check format           │            │
│  │  │ • Resample if needed  • Convert PDF→MXL        │            │
│  │  │ • Convert to 44.1kHz  • Handle MXL/MIDI        │            │
│  │  │ • Save as canonical   • Extract to std format  │            │
│  │  │   44.1kHz 16-bit WAV  • MIDI→MusicXML if req.  │            │
│  │  └──────────────┘      └──────────────┘           │            │
│  │        ↓                      ↓                    │            │
│  │  audio_standardized.wav  score_standardized.xml   │            │
│  │                                                     │            │
│  └─────────────────────────────────────────────────────┘            │
│                              ↓                                       │
│  ┌─────────────────────────────────────────────────────┐            │
│  │  LAYER 2: PROCESSING (AUDIO ENHANCEMENT)           │            │
│  │  (processing_layer.py - 764 lines)                 │            │
│  ├─────────────────────────────────────────────────────┤            │
│  │                                                     │            │
│  │  Step 1: Load Audio                                │            │
│  │  ┌─────────────────────────────────────┐           │            │
│  │  │ librosa.load(file, sr=22050)        │ ← OPTIMIZED│            │
│  │  │ • Downsample to 22050 Hz (50% RAM) │            │            │
│  │  │ • Use float32 dtype (50% RAM)      │            │            │
│  │  │ Expected memory: 150 MB             │            │            │
│  │  └─────────────────────────────────────┘           │            │
│  │                                                     │            │
│  │  Step 2: Noise Reduction                           │            │
│  │  ┌─────────────────────────────────────┐           │            │
│  │  │ noisereduce.reduce_noise()          │           │            │
│  │  │ • Spectral gating                   │           │            │
│  │  │ • Remove background noise           │           │            │
│  │  └─────────────────────────────────────┘           │            │
│  │                                                     │            │
│  │  Step 3: Peak Normalization                        │            │
│  │  ┌─────────────────────────────────────┐           │            │
│  │  │ Normalize peak to -3dB               │           │            │
│  │  │ • Preserves headroom                │           │            │
│  │  │ • Consistent level across files     │           │            │
│  │  └─────────────────────────────────────┘           │            │
│  │                                                     │            │
│  │  Step 4: Audio Segmentation                        │            │
│  │  ┌─────────────────────────────────────┐           │            │
│  │  │ Detect audio segments               │           │            │
│  │  │ • Energy-based (auditok removed)    │           │            │
│  │  │ • Fallback: full_audio (entire)     │           │            │
│  │  └─────────────────────────────────────┘           │            │
│  │                                                     │            │
│  │  Step 5: Score Feature Extraction                  │            │
│  │  ┌─────────────────────────────────────┐           │            │
│  │  │ music21.parse(score)                │           │            │
│  │  │ • Extract key signature             │           │            │
│  │  │ • Extract time signatures           │           │            │
│  │  │ • Extract tempos                    │           │            │
│  │  └─────────────────────────────────────┘           │            │
│  │                                                     │            │
│  │  DIAGNOSTIC LOGS:                                  │            │
│  │  [MEMORY AFTER_LOAD_AUDIO] → 150 MB                │            │
│  │  [AUDIO_CHECK] elapsed: 2.34s                      │            │
│  │  [NOISE_REDUCE] elapsed: 12.45s                    │            │
│  │  [NORMALIZE] elapsed: 3.21s                        │            │
│  │                                                     │            │
│  └─────────────────────────────────────────────────────┘            │
│              ↓                                                       │
│     ⚠️ RENDER HANGS HERE ⚠️                                          │
│     (Estimated: 30-60 seconds without hang)                         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────┐            │
│  │  LAYER 3: TEMPORAL ALIGNMENT (Score-Performance)   │            │
│  │  (pipeline.py - run_temporal_alignment)            │            │
│  ├─────────────────────────────────────────────────────┤            │
│  │                                                     │            │
│  │  ┌──────────────────────────────────────┐          │            │
│  │  │  BLOCK 0: ScoreGraph Generation     │          │            │
│  │  │  (build_scoregraph_with_notes.py)   │          │            │
│  │  ├──────────────────────────────────────┤          │            │
│  │  │ Input: score_standardized.xml        │          │            │
│  │  │                                       │          │            │
│  │  │ Process:                             │          │            │
│  │  │ 1. music21.parse() → score object    │          │            │
│  │  │ 2. Extract measures/beats            │          │            │
│  │  │ 3. Extract note info for each beat   │          │            │
│  │  │ 4. Build beat node graph             │          │            │
│  │  │                                       │          │            │
│  │  │ Output: scoregraph.json              │          │            │
│  │  │ {                                     │          │            │
│  │  │   "bars": [                          │          │            │
│  │  │     {                                │          │            │
│  │  │       "measure": 1,                 │          │            │
│  │  │       "beat_nodes": ["N0", "N1"],  │          │            │
│  │  │       "notes": [                    │          │            │
│  │  │         {"pitch": 60, "start": 0.0} │          │            │
│  │  │       ]                             │          │            │
│  │  │     }                                │          │            │
│  │  │   ]                                  │          │            │
│  │  │ }                                     │          │            │
│  │  │                                       │          │            │
│  │  │ Duration: 5-10 seconds              │          │            │
│  │  └──────────────────────────────────────┘          │            │
│  │                        ↓                           │            │
│  │  ┌──────────────────────────────────────┐          │            │
│  │  │  BLOCK 1: Audio Transcription       │          │            │
│  │  │  (transcribe_enhanced.py)           │          │            │
│  │  ├──────────────────────────────────────┤          │            │
│  │  │ Input: audio_processed.wav           │          │            │
│  │  │                                       │          │            │
│  │  │ Process:                             │          │            │
│  │  │ 1. Detect instrument from filename   │          │            │
│  │  │ 2. Run transcription model (BASIC    │          │            │
│  │  │    PITCH or similar) → MIDI notes    │          │            │
│  │  │ 3. Apply transposition corrections   │          │            │
│  │  │    (Bb clarinet = +2 semitones)      │          │            │
│  │  │ 4. Correct octave for bass instr.    │          │            │
│  │  │ 5. Convert to pretty_midi.PrettyMIDI│          │            │
│  │  │                                       │          │            │
│  │  │ Output: performance.mid              │          │            │
│  │  │                                       │          │            │
│  │  │ Duration: 20-40 seconds              │          │            │
│  │  └──────────────────────────────────────┘          │            │
│  │                        ↓                           │            │
│  │  ┌──────────────────────────────────────┐          │            │
│  │  │  BLOCK 4: Beat Detection [OPTIONAL] │          │            │
│  │  │  (estimate_beats_beatnet.py)        │          │            │
│  │  ├──────────────────────────────────────┤          │            │
│  │  │ Input: audio_processed.wav           │          │            │
│  │  │                                       │          │            │
│  │  │ Process:                             │          │            │
│  │  │ 1. Run BeatNet model                 │          │            │
│  │  │ 2. Detect downbeats                  │          │            │
│  │  │ 3. Extract beat times                │          │            │
│  │  │                                       │          │            │
│  │  │ Output: beats.json [optional]        │          │            │
│  │  │                                       │          │            │
│  │  │ Duration: 10-20 seconds              │          │            │
│  │  └──────────────────────────────────────┘          │            │
│  │                        ↓                           │            │
│  │  ┌──────────────────────────────────────┐          │            │
│  │  │ Context Aligner [OPTIONAL]          │          │            │
│  │  │ (context_aligner.py)                │          │            │
│  │  ├──────────────────────────────────────┤          │            │
│  │  │ Find optimal path considering       │          │            │
│  │  │ score structure (repeats, variants) │          │            │
│  │  │                                       │          │            │
│  │  │ Duration: 5-10 seconds              │          │            │
│  │  └──────────────────────────────────────┘          │            │
│  │                        ↓                           │            │
│  │  ┌──────────────────────────────────────┐          │            │
│  │  │  BLOCK 2: DTW Alignment (THE KEY)   │          │            │
│  │  │  (align_symbolic_enhanced_with_     │          │            │
│  │  │   metrics.py - 1411 lines)          │          │            │
│  │  ├──────────────────────────────────────┤          │            │
│  │  │ Input:                                │          │            │
│  │  │  • scoregraph.json (score structure) │          │            │
│  │  │  • performance.mid (performance)     │          │            │
│  │  │  • beats.json [optional]             │          │            │
│  │  │                                       │          │            │
│  │  │ Process:                             │          │            │
│  │  │ 1. Extract CQT features from score  │          │            │
│  │  │ 2. Extract CQT features from perf.  │          │            │
│  │  │ 3. Compute DTW cost matrix           │          │            │
│  │  │ 4. Find optimal alignment path       │          │            │
│  │  │ 5. Extract metrics:                  │          │            │
│  │  │    • Pitch accuracy (±50¢)           │          │            │
│  │  │    • Note accuracy (matched %)       │          │            │
│  │  │    • IOI correlation                 │          │            │
│  │  │    • Onset error (ms)                │          │            │
│  │  │    • Tempo CV (consistency)          │          │            │
│  │  │                                       │          │            │
│  │  │ Output: alignment_results.json       │          │            │
│  │  │ {                                     │          │            │
│  │  │   "grading_metrics": {               │          │            │
│  │  │     "sound_quality": {               │          │            │
│  │  │       "pitch_accuracy_50c_percent":85│          │            │
│  │  │     },                                │          │            │
│  │  │     "technical_virtuosity": {        │          │            │
│  │  │       "note_accuracy_percent": 92    │          │            │
│  │  │     },                                │          │            │
│  │  │     "rhythm_tempo": {                │          │            │
│  │  │       "ioi_correlation": 0.87        │          │            │
│  │  │     }                                 │          │            │
│  │  │   }                                   │          │            │
│  │  │ }                                     │          │            │
│  │  │                                       │          │            │
│  │  │ Duration: 30-60 seconds              │          │            │
│  │  └──────────────────────────────────────┘          │            │
│  │                                                     │            │
│  │  TOTAL LAYER 3: 90-140 seconds                    │            │
│  └─────────────────────────────────────────────────────┘            │
│                        ↓                                             │
│       ┌────────────────────────────────────┐                        │
│       │  LAYER 4 & 5 RUN IN PARALLEL      │                        │
│       └────────────────────────────────────┘                        │
│                        ↓                                             │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  LAYER 4: FEATURE EXTRACTION [PARALLEL with 5]      │           │
│  │  (extraction_layer.py - 920 lines)                  │           │
│  ├──────────────────────────────────────────────────────┤           │
│  │                                                      │           │
│  │  Part A: Performance Audio Features                 │           │
│  │  ┌──────────────────────────────────┐               │           │
│  │  │ Input: audio_processed.wav       │               │           │
│  │  │                                   │               │           │
│  │  │ Extractors:                       │               │           │
│  │  │ • Aubio (pitch tracking)          │               │           │
│  │  │ • Librosa (spectral features)     │               │           │
│  │  │ • Essentia (music analysis)       │               │           │
│  │  │                                   │               │           │
│  │  │ Features:                         │               │           │
│  │  │ • Pitch contour (frame-by-frame) │               │           │
│  │  │ • Onset times & strengths         │               │           │
│  │  │ • Tempo BPM & confidence          │               │           │
│  │  │ • Spectral centroid               │               │           │
│  │  │ • MFCC features                   │               │           │
│  │  │ • Chroma features                 │               │           │
│  │  │ • RMS energy                      │               │           │
│  │  │ • Harmonic/percussive separation │               │           │
│  │  │                                   │               │           │
│  │  │ Output: performance_features.json │               │           │
│  │  └──────────────────────────────────┘               │           │
│  │                                                      │           │
│  │  Part B: Score Features                            │           │
│  │  ┌──────────────────────────────────┐               │           │
│  │  │ Input: score_standardized.xml    │               │           │
│  │  │                                   │               │           │
│  │  │ Extractors:                       │               │           │
│  │  │ • music21 (score analysis)        │               │           │
│  │  │                                   │               │           │
│  │  │ Features:                         │               │           │
│  │  │ • Expected pitches (MIDI)         │               │           │
│  │  │ • Note onsets & durations         │               │           │
│  │  │ • Key signature                   │               │           │
│  │  │ • Time signatures                 │               │           │
│  │  │ • Chord progressions              │               │           │
│  │  │ • Phrase boundaries               │               │           │
│  │  │                                   │               │           │
│  │  │ Output: score_features.json       │               │           │
│  │  └──────────────────────────────────┘               │           │
│  │                                                      │           │
│  │  Duration: 10-30 seconds                           │           │
│  └──────────────────────────────────────────────────────┘           │
│                        ↓                                             │
│  ┌──────────────────────────────────────────────────────┐           │
│  │  LAYER 5: PQG-A2SA [OPTIONAL, PARALLEL with 4]     │           │
│  │  (05_pqg_a2sa/src/... - multiple files)            │           │
│  ├──────────────────────────────────────────────────────┤           │
│  │                                                      │           │
│  │  Input: audio + MIDI score                         │           │
│  │                                                      │           │
│  │  Process:                                          │           │
│  │  • Probabilistic alignment algorithm               │           │
│  │  • Precise onset/offset detection                  │           │
│  │                                                      │           │
│  │  Output: pqg_a2sa_results.json                    │           │
│  │  {precise timing information}                      │           │
│  │                                                      │           │
│  │  Duration: 5-15 seconds                            │           │
│  │  Status: May skip if MIDI score unavailable        │           │
│  │                                                      │           │
│  └──────────────────────────────────────────────────────┘           │
│                        ↓                                             │
│  ┌─────────────────────────────────────────────────────┐            │
│  │  LAYER 6: INFERENCE CORE                            │            │
│  │  (inference_core.py - 323 lines)                    │            │
│  ├─────────────────────────────────────────────────────┤            │
│  │                                                     │            │
│  │  Step 1: Collect ALL upstream data                 │            │
│  │  • alignment_results.json (from Block 2)           │            │
│  │  • performance_features.json (from Layer 4)        │            │
│  │  • score_features.json (from Layer 4)              │            │
│  │  • beats.json (optional, from Block 4)             │            │
│  │  • pqg_a2sa_results.json (optional, from Layer 5)  │            │
│  │                                                     │            │
│  │  Step 2: Extract grading metrics from Block 2      │            │
│  │  • sound_quality metrics                           │            │
│  │  • technical_virtuosity metrics                    │            │
│  │  • rhythm_tempo metrics                            │            │
│  │                                                     │            │
│  │  Step 3: Score all dimensions                      │            │
│  │  Convert raw metrics → 0-100 scores                │            │
│  │                                                     │            │
│  │  Step 4: Create grading package                    │            │
│  │  {                                                  │            │
│  │    "grading_dimensions": {                         │            │
│  │      "rhythm_tempo": {                             │            │
│  │        "weight": 0.30,                             │            │
│  │        "dimension_score": 82.5,                    │            │
│  │        "component_scores": {...}                   │            │
│  │      },                                            │            │
│  │      "sound_quality": {...},                       │            │
│  │      "technical_virtuosity": {...},                │            │
│  │      "phrasing_diction": {...},                    │            │
│  │      "communicativeness": {...}                    │            │
│  │    }                                               │            │
│  │  }                                                  │            │
│  │                                                     │            │
│  │  Output: grading_package_master.json              │            │
│  │  Duration: 2-5 seconds                            │            │
│  │                                                     │            │
│  └─────────────────────────────────────────────────────┘            │
│                              ↓                                       │
│  ┌─────────────────────────────────────────────────────┐            │
│  │  LAYER 7: GRADING                                   │            │
│  │  (grading_layer.py - 548 lines)                     │            │
│  ├─────────────────────────────────────────────────────┤            │
│  │                                                     │            │
│  │  Input: grading_package_master.json                │            │
│  │                                                     │            │
│  │  Process:                                          │            │
│  │  1. Apply PQG-A2SA weights:                        │            │
│  │     • Rhythm & Tempo: 30%                          │            │
│  │     • Sound Quality: 20%                           │            │
│  │     • Technical Virtuosity: 20%                    │            │
│  │     • Phrasing & Diction: 15%                      │            │
│  │     • Communicativeness: 15%                       │            │
│  │                                                     │            │
│  │  2. Calculate weighted score                       │            │
│  │     score = Σ(dimension_score × weight)            │            │
│  │                                                     │            │
│  │  3. Normalize to 0-100 scale                       │            │
│  │                                                     │            │
│  │  4. Determine letter grade:                        │            │
│  │     A+ (97+), A (93+), B+ (87+), ... F (0-59)      │            │
│  │                                                     │            │
│  │  5. Generate comprehensive report:                 │            │
│  │     • Overall score & letter grade                 │            │
│  │     • Component breakdowns                         │            │
│  │     • Detailed metrics (pitch, timing, etc.)       │            │
│  │     • Specific strengths & weaknesses              │            │
│  │     • Recommendations                              │            │
│  │                                                     │            │
│  │  Outputs:                                          │            │
│  │  • final_grade.json (structured data)             │            │
│  │  • performance_report.txt (human readable)        │            │
│  │                                                     │            │
│  │  Duration: 1-2 seconds                            │            │
│  │                                                     │            │
│  └─────────────────────────────────────────────────────┘            │
│                              ↓                                       │
│  ┌─────────────────────────────────────────────────────┐            │
│  │  FINAL: Chatbot Context Aggregation                │            │
│  │  (get_chatbot_context() in pipeline.py)            │            │
│  ├─────────────────────────────────────────────────────┤            │
│  │                                                     │            │
│  │  Aggregate ALL outputs from 7 layers into one file│            │
│  │  {                                                  │            │
│  │    "meta": {...},                                  │            │
│  │    "layers": {                                     │            │
│  │      "L1_Input": {...},                           │            │
│  │      "L2_Processing": {...},                      │            │
│  │      "L3_Temporal": {                             │            │
│  │        "block_0_scoregraph": {...},               │            │
│  │        "block_1_transcription": {...},            │            │
│  │        "block_2_dtw_alignment": {...},            │            │
│  │        "block_4_beats": {...},                    │            │
│  │        "context_aligner": {...}                   │            │
│  │      },                                            │            │
│  │      "L4_Extraction": {...},                      │            │
│  │      "L5_PQG": {...},                             │            │
│  │      "L6_Inference": {...},                       │            │
│  │      "L7_Grading": {...}                          │            │
│  │    }                                               │            │
│  │  }                                                  │            │
│  │                                                     │            │
│  │  Output: chatbot_context.json                     │            │
│  │  Duration: 1-2 seconds                            │            │
│  │                                                     │            │
│  │  This is fed to Groq AI for context-aware chat    │            │
│  │                                                     │            │
│  └─────────────────────────────────────────────────────┘            │
│                              ↓                                       │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
                      RETURN TO USER
                      ===============
                      • Grade: 0-100
                      • Letter Grade: A+ to F
                      • Report text: full assessment
                      • Components: breakdown
                      • Ready for chat interaction

TOTAL EXECUTION TIME: 150-250 seconds (2.5-4 minutes)
Render timeout: ~5 minutes
Current Render state: HANGS at Layer 2, killed before Layer 3
```

---

## FILE ORGANIZATION CHART

```
WORKSPACE/
│
├── app.py (608 lines)
│   ├── Imports: MusicPerformancePipeline
│   ├── Flask REST API
│   ├── run_analysis() ← Entry point for pipeline
│   └── Groq API integration
│
├── MusicPerformanceAnalysis/
│   │
│   ├── pipeline.py (1290 lines) ← ORCHESTRATOR
│   │   ├── MusicPerformancePipeline class
│   │   ├── run_pipeline() - Main orchestrator
│   │   └── Calls all 7 layers in sequence
│   │
│   └── layers/
│       │
│       ├── 01_input/
│       │   └── input_layer.py (548 lines)
│       │       ├── AudioInputProcessor
│       │       └── ScoreInputProcessor
│       │
│       ├── 02_processing/
│       │   └── processing_layer.py (764 lines)
│       │       ├── check_audio_quality()
│       │       ├── reduce_noise()
│       │       ├── normalize_audio()
│       │       ├── segment_audio()
│       │       └── extract_score_features()
│       │
│       ├── 03_temporal_alignment/
│       │   │
│       │   ├── block_0_scoregraph/
│       │   │   └── build_scoregraph_with_notes.py (285 lines)
│       │   │       └── Extracts score structure
│       │   │
│       │   ├── block_1_transcription/
│       │   │   └── transcribe_enhanced.py (245 lines)
│       │   │       └── Audio → MIDI with corrections
│       │   │
│       │   ├── block_2_dtw/
│       │   │   └── align_symbolic_enhanced_with_metrics.py (1411 lines)
│       │   │       └── DTW alignment + grading metrics
│       │   │
│       │   ├── block_4_beats/
│       │   │   └── estimate_beats_beatnet.py
│       │   │       └── Beat detection [optional]
│       │   │
│       │   └── context_aligner/
│       │       └── context_aligner.py
│       │           └── Structural path finding [optional]
│       │
│       ├── 04_extraction/
│       │   └── extraction_layer.py (920 lines)
│       │       ├── AudioFeatureExtractor
│       │       └── ScoreFeatureExtractor
│       │
│       ├── 05_pqg_a2sa/
│       │   └── src/
│       │       └── PQGAligner class
│       │
│       ├── 06_inference/
│       │   ├── inference_core.py (323 lines)
│       │   ├── data_collector.py
│       │   └── utils/
│       │
│       └── 07_grading/
│           ├── grading_layer.py (548 lines)
│           └── __init__.py
│
└── requirements.txt (WITH OPTIMIZATIONS)
    ├── librosa
    ├── scipy
    ├── noisereduce
    ├── music21
    ├── pretty_midi
    ├── aubio [optional]
    ├── essentia [optional]
    ├── flask
    ├── psutil ✓ ADDED FOR MONITORING
    └── groq [optional]
```

---

## DEPENDENCY TREE (What Imports What)

```
app.py
├── MusicPerformancePipeline (pipeline.py)
│   ├── run_input_layer() → input_layer.py
│   │   ├── librosa
│   │   ├── soundfile
│   │   └── music21
│   │
│   ├── run_processing_layer() → processing_layer.py
│   │   ├── librosa
│   │   ├── scipy
│   │   ├── noisereduce
│   │   ├── soundfile
│   │   ├── music21
│   │   ├── ffmpeg_normalize
│   │   └── psutil ✓ DIAGNOSTIC
│   │
│   ├── run_temporal_alignment()
│   │   ├── run_block_0() → build_scoregraph_with_notes.py
│   │   │   └── music21
│   │   │
│   │   ├── run_block_1() → transcribe_enhanced.py
│   │   │   ├── librosa
│   │   │   ├── pretty_midi
│   │   │   └── transcription model
│   │   │
│   │   ├── run_block_4() → estimate_beats_beatnet.py
│   │   │   ├── librosa
│   │   │   └── beatnet model
│   │   │
│   │   ├── run_context_aligner() → context_aligner.py
│   │   │
│   │   └── run_block_2() → align_symbolic_enhanced_with_metrics.py
│   │       ├── numpy
│   │       ├── pretty_midi
│   │       ├── librosa
│   │       ├── scipy
│   │       └── gpu_manager [optional]
│   │
│   ├── run_extraction_layer() → extraction_layer.py
│   │   ├── aubio [optional]
│   │   ├── librosa
│   │   ├── essentia [optional]
│   │   └── music21
│   │
│   ├── run_pqg_a2sa() → 05_pqg_a2sa/src/...
│   │   └── Various PQG implementations
│   │
│   ├── run_inference() → inference_core.py
│   │   ├── data_collector.py
│   │   ├── utils/
│   │   └── Reads JSON from Layer 3-5
│   │
│   ├── run_grading() → grading_layer.py
│   │   └── Reads JSON from Layer 6
│   │
│   └── get_chatbot_context()
│       └── Aggregates all layer JSONs
│
├── llm_service (optional)
├── Groq API (optional)
└── psutil ✓ DIAGNOSTIC
```

---

## PERFORMANCE TIMELINE (Typical Run)

```
BEST CASE (Local, optimal conditions): 150 seconds
TYPICAL CASE (Render, with hang): TIMEOUT at ~300 seconds

Timeline:
0s    └─ Upload started
0-5s  └─ Layer 1: Input validation
5-60s └─ Layer 2: Audio processing ⚠️ HANGS HERE ON RENDER
60-200s └─ Layer 3: Temporal alignment (unreachable on Render)
200-230s└─ Layer 4: Extraction (parallel, unreachable)
230-245s└─ Layer 5: PQG (parallel, unreachable)
245-250s└─ Layer 6-7: Grading + Chatbot context (unreachable)
250s  └─ Complete (unreachable on Render)

RENDER ACTUAL TIMELINE:
0s    └─ Upload started
0-40s └─ Layer 2: Processing starts and gets stuck
40-300s └─ HANG: Layer 2 blocked, Render waiting
300s  └─ TIMEOUT: Service killed by Render
       └─ Error returned to user
```

---

## CURRENT DIAGNOSTICS INSTALLED

```
Memory Monitoring Points (processing_layer.py):
✓ [MEMORY AFTER_LOAD_AUDIO] - Check if 150MB or 300MB+
✓ [MEMORY AFTER_REDUCE_NOISE] - Check if decreased
✓ [MEMORY AFTER_NORMALIZE] - Check sustained level

Timing Logs (processing_layer.py):
✓ [AUDIO_CHECK] elapsed: X.XXs
✓ [NOISE_REDUCE] elapsed: X.XXs
✓ [NORMALIZE] elapsed: X.XXs

Pipeline Logs (app.py):
✓ [PIPELINE_START] job_id
✓ [PIPELINE_RUNNING] job_id
✓ [PIPELINE_END] job_id: elapsed=X.XXs
✓ [SYSTEM ...] RAM/CPU/Thread counts

System Resource Logs:
✓ [SYSTEM RUN_ANALYSIS_START] at beginning
✓ [SYSTEM BEFORE_PIPELINE] before run_pipeline()
✓ [SYSTEM AFTER_PIPELINE] after run_pipeline()
✓ [SYSTEM AFTER_PIPELINE_ERROR] on exception
```

---

END OF ARCHITECTURE VISUALIZATION
