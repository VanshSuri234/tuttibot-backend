#!/usr/bin/env python3
"""
Music Performance Analysis System - Main Pipeline
==================================================

Complete pipeline from audio/score input to final performance grade.

Architecture:
    Layer 1: Input Standardization
    Layer 2: Processing (noise reduction, normalization, segmentation)
    Layer 3: Temporal Alignment (Blocks 0→1→4→Context→2)
    Layer 4: Extraction (performance + score features) [parallel]
    Layer 5: PQG-A2SA (onset/offset precision) [parallel]
    Layer 6: Inference Core (metric computation)
    Layer 7: Grading Layer (final grade)

Usage:
    python pipeline.py --audio audio.wav --score score.xml --output output_dir
    python pipeline.py --audio audio.wav --score score.xml --part 0 --output output_dir
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from datetime import datetime
import logging

# Add layers to path
LAYERS_DIR = Path(__file__).parent / "layers"
sys.path.insert(0, str(LAYERS_DIR))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MusicPerformancePipeline:
    """Complete music performance analysis pipeline orchestrator"""
    
    def __init__(self, audio_path, score_path, output_dir, config_path=None, score_part=None):
        self.audio_path = Path(audio_path).resolve()  # Convert to absolute path
        self.score_path = Path(score_path).resolve()  # Convert to absolute path
        self.output_dir = Path(output_dir).resolve()  # Convert to absolute path
        
        # Auto-detect part from audio filename if not specified
        if score_part is None:
            self.score_part = self._detect_score_part_from_audio()
        else:
            self.score_part = score_part
        
        # Load configuration
        if config_path:
            with open(config_path) as f:
                self.config = yaml.safe_load(f)
        else:
            # Use defaults
            default_config = Path(__file__).parent / "config.yaml"
            if default_config.exists():
                with open(default_config) as f:
                    self.config = yaml.safe_load(f)
            else:
                self.config = self._get_default_config()
        
        # Setup output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.setup_output_directories()
        
        # Get base directory
        self.base_dir = Path(__file__).parent
        self.layers_dir = self.base_dir / "layers"
        
        # Pipeline status
        self.status = {
            'input': False,
            'processing': False,
            'temporal_alignment': False,
            'extraction': False,
            'pqg_a2sa': False,
            'inference': False,
            'grading': False
        }
        
        # Results storage
        self.results = {}
    
    def _detect_score_part_from_audio(self):
        """
        Auto-detect which part of a multi-part score to use based on audio filename
        
        Returns:
            int: Part index (0-based) for SATB scores: 0=Soprano, 1=Alto, 2=Tenor, 3=Bass
        """
        filename_lower = self.audio_path.name.lower()
        print(f"DEBUG: Detecting part from filename: {filename_lower}")
        
        # Define instrument to part mapping for SATB scores
        # Part indices: 0=Soprano (highest), 1=Alto, 2=Tenor, 3=Bass (lowest)
        bass_instruments = ['bassoon', 'cello', 'bass', 'tuba', 'trombone', 'contrabass']
        tenor_instruments = ['saxophone', 'saxphone', 'tenor', 'euphonium']
        alto_instruments = ['clarinet', 'alto', 'horn', 'viola']
        soprano_instruments = ['violin', 'flute', 'oboe', 'soprano', 'trumpet']
        
        # Check for bass instruments (part 3 in SATB)
        for inst in bass_instruments:
            if inst in filename_lower:
                print(f"DEBUG: Detected bass instrument '{inst}' - selecting part 3 (Bass)")
                return 3
        
        # Check for tenor instruments (part 2 in SATB)
        for inst in tenor_instruments:
            if inst in filename_lower:
                logger.info(f"Detected tenor instrument '{inst}' - selecting part 2 (Tenor)")
                return 2
        
        # Check for alto instruments (part 1 in SATB)
        for inst in alto_instruments:
            if inst in filename_lower:
                logger.info(f"Detected alto instrument '{inst}' - selecting part 1 (Alto)")
                return 1
        
        # Check for soprano instruments (part 0 in SATB)
        for inst in soprano_instruments:
            if inst in filename_lower:
                logger.info(f"Detected soprano instrument '{inst}' - selecting part 0 (Soprano)")
                return 0
        
        # No instrument detected - default to part 0
        logger.info("No instrument detected in filename - defaulting to part 0 (Soprano/first part)")
        return 0
    
    def setup_output_directories(self):
        """Create output directory structure"""
        subdirs = self.config.get('output', {}).get('subdirs', {})
        
        self.input_dir = self.output_dir / subdirs.get('input', '01_input')
        self.processing_dir = self.output_dir / subdirs.get('processing', '02_processing')
        self.temporal_dir = self.output_dir / subdirs.get('temporal_alignment', '03_temporal_alignment')
        self.extraction_dir = self.output_dir / subdirs.get('extraction', '04_extraction')
        self.pqg_dir = self.output_dir / subdirs.get('pqg_a2sa', '05_pqg_a2sa')
        self.inference_dir = self.output_dir / subdirs.get('inference', '06_inference')
        self.grading_dir = self.output_dir / subdirs.get('grading', '07_grading')
        
        for d in [self.input_dir, self.processing_dir, self.temporal_dir,
                  self.extraction_dir, self.pqg_dir, self.inference_dir, self.grading_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def _get_default_config(self):
        """Get default configuration"""
        return {
            'temporal_alignment': {
                'block_0_scoregraph': {'enabled': True},
                'block_1_transcription': {'enabled': True},
                'block_2_dtw': {'enabled': True},
                'block_4_beats': {'enabled': True, 'optional': True},
                'context_aligner': {'enabled': True, 'optional': True}
            },
            'extraction': {'enabled': True},
            'pqg_a2sa': {'enabled': True, 'optional': True},
            'inference': {'enabled': True},
            'grading': {
                'enabled': True,
                'pqg_a2sa_weights': {
                    'pitch': 0.3,
                    'note_accuracy': 0.2,
                    'rhythm': 0.2,
                    'tempo': 0.15,
                    'articulation': 0.15
                }
            },
            'output': {
                'subdirs': {
                    'input': '01_input',
                    'processing': '02_processing',
                    'temporal_alignment': '03_temporal_alignment',
                    'extraction': '04_extraction',
                    'pqg_a2sa': '05_pqg_a2sa',
                    'inference': '06_inference',
                    'grading': '07_grading'
                }
            }
        }
    
    def run_input_layer(self):
        """
        Layer 1: Input Standardization
        Validates and standardizes audio and score inputs
        """
        logger.info("\n[Layer 1: Input Standardization]")
        
        try:
            # Import input layer
            sys.path.insert(0, str(self.layers_dir / "01_input"))
            from input_layer import MusicInputLayer
            
            # Process inputs
            input_layer = MusicInputLayer()
            result = input_layer.process_inputs(self.audio_path, self.score_path)
            
            if not result['overall_success']:
                logger.error("Input validation failed")
                if not result['audio']['success']:
                    logger.error(f"  Audio: {result['audio']['message']}")
                if not result['score']['success']:
                    logger.error(f"  Score: {result['score']['message']}")
                return False
            
            # Store standardized paths
            if result['audio']['converted']:
                self.audio_path = Path(result['audio']['output_path'])
                logger.info(f" Audio standardized: {self.audio_path.name}")
            else:
                logger.info(f" Audio validated: {self.audio_path.name}")
            
            if result['score']['converted']:
                self.score_path = Path(result['score']['output_path'])
                logger.info(f" Score standardized: {self.score_path.name}")
            else:
                logger.info(f" Score validated: {self.score_path.name}")
            
            self.status['input'] = True
            return True
            
        except Exception as e:
            logger.warning(f"Input layer error (continuing): {e}")
            # Continue even if input layer fails - files may already be in correct format
            return True
    
    def run_processing_layer(self):
        """
        Layer 2: Processing
        Noise reduction, normalization, and segmentation
        """
        logger.info("\n[Layer 2: Audio Processing]")
        
        try:
            # Import processing layer
            sys.path.insert(0, str(self.layers_dir / "02_processing"))
            from processing_layer import ProcessingLayer
            
            # Process audio and score
            processing_layer = ProcessingLayer(
                data_dir=str(self.processing_dir / "data"),
                shared_output_dir=str(self.processing_dir / "shared")
            )
            
            result = processing_layer.process(
                str(self.audio_path),
                str(self.score_path)
            )
            
            # Update audio path to processed version
            processed_audio = Path(result.processed_audio_path)
            if processed_audio.exists():
                self.audio_path = processed_audio
                logger.info(f"✓ Audio processed: {self.audio_path.name}")
            else:
                logger.info(f"✓ Audio processing skipped (not needed)")
            
            # Save processing metadata (convert numpy types)
            metadata_file = self.processing_dir / "processing_metadata.json"
            try:
                # Convert numpy types to Python types
                metadata_dict = result.processing_metadata
                if isinstance(metadata_dict, dict):
                    # Simple conversion of common numpy types
                    def convert_numpy(obj):
                        import numpy as np
                        if isinstance(obj, np.bool_):
                            return bool(obj)
                        elif isinstance(obj, (np.integer, np.floating)):
                            return float(obj) if isinstance(obj, np.floating) else int(obj)
                        elif isinstance(obj, np.ndarray):
                            return obj.tolist()
                        elif isinstance(obj, dict):
                            return {k: convert_numpy(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_numpy(item) for item in obj]
                        return obj
                    
                    metadata_dict = convert_numpy(metadata_dict)
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata_dict, f, indent=2)
            except Exception as e:
                logger.warning(f"Could not save processing metadata: {e}")
            
            self.results['processing_metadata'] = str(metadata_file)
            self.status['processing'] = True
            return True
            
        except Exception as e:
            logger.warning(f"Processing layer error (continuing): {e}")
            # Continue even if processing fails - use original audio
            return True
    
    def run_extraction_layer(self):
        """
        Layer 4: Feature Extraction
        Extracts performance and score features (runs in parallel with temporal alignment)
        """
        logger.info("\n[Layer 4: Feature Extraction]")
        
        try:
            # Import extraction layer
            sys.path.insert(0, str(self.layers_dir / "04_extraction"))
            from extraction_layer import ExtractionLayer
            
            # Create extraction layer
            extraction_layer = ExtractionLayer()
            
            # Get required inputs
            audio_file = str(self.audio_path)
            score_file = str(self.score_path)
            
            # Check if we have segments from processing layer
            segments_file = self.processing_dir / "shared" / "processed" / "audio_segments.json"
            if not segments_file.exists():
                # Create empty segments file
                segments_file.parent.mkdir(parents=True, exist_ok=True)
                with open(segments_file, 'w') as f:
                    json.dump({"segments": []}, f)
            
            # Check if we have score JSON
            score_json_file = self.processing_dir / "shared" / "processed" / "music_features.json"
            if not score_json_file.exists():
                # Create empty score JSON
                score_json_file.parent.mkdir(parents=True, exist_ok=True)
                with open(score_json_file, 'w') as f:
                    json.dump({"notes": []}, f)
            
            # Extract features
            outputs = extraction_layer.process_all(
                audio_file=audio_file,
                segments_file=str(segments_file),
                score_file=score_file,
                score_json_file=str(score_json_file),
                output_dir=str(self.extraction_dir)
            )
            
            self.results['extraction'] = outputs
            self.status['extraction'] = True
            logger.info(f" Feature extraction complete")
            return True
            
        except Exception as e:
            logger.warning(f"Extraction layer error (continuing): {e}")
            import traceback
            traceback.print_exc()
            # Continue even if extraction fails - may not be needed for grading
            return True
    
    def run_temporal_alignment(self):
        """
        Layer 3: Temporal Alignment
        Runs blocks in sequence: Block 0 → 1 → 4 → Context → 2
        """
        logger.info("\n[Layer 3: Temporal Alignment]")
        
        # Import the existing tuttibot_pipeline from TuttiBot_End_To_End
        # This already has all blocks integrated with Context Aligner and PQG-A2SA
        try:
            temporal_alignment_dir = self.layers_dir / "03_temporal_alignment"
            sys.path.insert(0, str(temporal_alignment_dir))
            
            # We'll use the integrated pipeline we already created
            # For now, use a simplified approach - call each block
            
            # Block 0: ScoreGraph
            success = self._run_block_0()
            if not success:
                logger.error("Block 0 failed - cannot continue temporal alignment")
                return False
            
            # Block 1: Transcription
            success = self._run_block_1()
            if not success:
                logger.error("Block 1 failed - cannot continue temporal alignment")
                return False
            
            # Block 4: Beat Detection (optional)
            if self.config['temporal_alignment']['block_4_beats']['enabled']:
                self._run_block_4()  # Continue even if fails
            
            # Context Aligner (optional)
            if self.config['temporal_alignment']['context_aligner']['enabled']:
                self._run_context_aligner()  # Continue even if fails
            
            # Block 2: DTW Alignment
            success = self._run_block_2()
            if not success:
                logger.error("Block 2 failed")
                return False
            
            self.status['temporal_alignment'] = True
            logger.info(" Temporal alignment complete")
            return True
            
        except Exception as e:
            logger.error(f"Temporal alignment error: {e}")
            return False
    
    def _run_block_0(self):
        """Block 0: ScoreGraph Generation"""
        logger.info("Block 0: ScoreGraph Generation")
        
        try:
            import subprocess
            
            # Create metadata
            meta_path = self.temporal_dir / "score_meta.json"
            meta = {
                "meter": "4/4",
                "key_signature": "C",
                "tuning_hz": 440,
                "tempo_marks": [{"beat": 0, "bpm": 120}],
                "fermatas": [],
                "cadences": []
            }
            with open(meta_path, 'w') as f:
                json.dump(meta, f, indent=2)
            
            # Run scoregraph script
            script = self.layers_dir / "03_temporal_alignment" / "block_0_scoregraph" / "build_scoregraph_with_notes.py"
            output_file = self.temporal_dir / "scoregraph.json"
            
            cmd = [
                sys.executable,
                str(script),
                "--score", str(self.score_path),
                "--meta", str(meta_path),
                "--part", str(self.score_part),
                "--output", str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_file.exists():
                logger.info(f" ScoreGraph saved: {output_file}")
                self.results['scoregraph'] = str(output_file)
                return True
            else:
                logger.error(f"ScoreGraph failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Block 0 error: {e}")
            return False
    
    def _run_block_1(self):
        """Block 1: Audio Transcription"""
        logger.info("Block 1: Audio Transcription")
        
        try:
            import subprocess
            import pretty_midi
            
            # Use the enhanced version with transposition and octave correction
            script = self.layers_dir / "03_temporal_alignment" / "block_1_transcription" / "transcribe_enhanced.py"
            output_midi = self.temporal_dir / "performance.mid"
            output_json = self.temporal_dir / "transcription.json"
            
            cmd = [
                sys.executable,
                str(script),
                "--audio", str(self.audio_path),
                "--output", str(output_midi)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_midi.exists():
                logger.info(f"✓ MIDI transcription saved: {output_midi}")
                
                # Convert MIDI to JSON format for downstream processing
                try:
                    midi = pretty_midi.PrettyMIDI(str(output_midi))
                    notes = []
                    for instrument in midi.instruments:
                        for note in instrument.notes:
                            notes.append({
                                'pitch': note.pitch,
                                'start': note.start,
                                'end': note.end,
                                'velocity': note.velocity
                            })
                    
                    # Save JSON
                    transcription_data = {
                        'notes': notes,
                        'total_notes': len(notes),
                        'duration': midi.get_end_time(),
                        'midi_file': str(output_midi)
                    }
                    
                    with open(output_json, 'w') as f:
                        json.dump(transcription_data, f, indent=2)
                    
                    logger.info(f"✓ JSON transcription saved: {output_json}")
                    self.results['transcription'] = str(output_json)
                    self.results['transcription_midi'] = str(output_midi)
                    return True
                    
                except Exception as e:
                    logger.error(f"MIDI to JSON conversion failed: {e}")
                    return False
            else:
                logger.error(f"Transcription failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Block 1 error: {e}")
            return False
    
    def _run_block_4(self):
        """Block 4: Beat Detection (optional)"""
        logger.info("Block 4: Beat Detection [optional]")
        
        try:
            import subprocess
            
            script = self.layers_dir / "03_temporal_alignment" / "block_4_beats" / "estimate_beats_beatnet.py"
            output_file = self.temporal_dir / "beats.json"
            
            cmd = [
                sys.executable,
                str(script),
                str(self.audio_path),
                str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and output_file.exists():
                logger.info(f"✓ Beat detection saved: {output_file}")
                self.results['beats'] = str(output_file)
                return True
            else:
                logger.warning(f"Beat detection failed (optional): {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"Block 4 error (optional): {e}")
            return False
    
    def _run_context_aligner(self):
        """Context Aligner: Structural path finding (optional)"""
        logger.info("Context Aligner: Structural path finding [optional]")
        
        try:
            # Import context aligner
            aligner_script = self.layers_dir / "03_temporal_alignment" / "context_aligner" / "context_aligner.py"
            
            if not aligner_script.exists():
                logger.warning("Context aligner not found, skipping")
                return False
            
            import importlib.util
            spec = importlib.util.spec_from_file_location("context_aligner", aligner_script)
            context_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(context_module)
            
            # Run alignment
            scoregraph_path = self.results.get('scoregraph')
            transcription_path = self.results.get('transcription')  # This is the JSON version
            
            if not scoregraph_path or not transcription_path:
                logger.warning("Missing scoregraph or transcription, skipping context aligner")
                return False
            
            aligner = context_module.ContextAligner(scoregraph_path)
            selected_path, alignment_score, pitch_matches = aligner.align(scoregraph_path, transcription_path)
            
            # Save results
            output_file = self.temporal_dir / "context_alignment.json"
            results = {
                'selected_path': selected_path,
                'alignment_score': float(alignment_score),
                'pitch_matches': pitch_matches
            }
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f" Context alignment saved: {output_file}")
            self.results['context_alignment'] = str(output_file)
            return True
            
        except Exception as e:
            logger.warning(f"Context aligner error (optional): {e}")
            return False
    
    def _run_block_2(self):
        """Block 2: DTW Temporal Alignment"""
        logger.info("Block 2: DTW Temporal Alignment")
        
        try:
            import subprocess
            import os
            
            script = self.layers_dir / "03_temporal_alignment" / "block_2_dtw" / "align_symbolic_enhanced_with_metrics.py"
            output_dir = self.temporal_dir / "alignment_output"
            
            scoregraph = self.results.get('scoregraph')
            transcription_midi = self.results.get('transcription_midi')  # Use MIDI, not JSON
            
            if not scoregraph or not transcription_midi:
                logger.error("Missing scoregraph or transcription MIDI for DTW")
                return False
            
            # Positional arguments: score_graph, performance_midi
            cmd = [
                sys.executable,
                str(script),
                scoregraph,  # Positional arg 1
                transcription_midi,  # Positional arg 2
                "--output", str(output_dir)
            ]
            
            # Add beats if available
            beats_file = self.results.get('beats')
            if beats_file:
                cmd.extend(["--beats", beats_file])
            
            # Pass config parameters as environment variables
            env = os.environ.copy()
            if 'grading' in self.config:
                env['PITCH_THRESHOLD'] = str(int(self.config['grading'].get('pitch_threshold', 50)))
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
            except subprocess.TimeoutExpired:
                logger.error("DTW alignment timeout (>5 minutes)")
                return False
            
            # Check for results file
            results_file = output_dir / "alignment_results.json"
            if result.returncode == 0 and results_file.exists():
                logger.info(f"✓ DTW alignment saved: {results_file}")
                self.results['alignment'] = str(results_file)
                return True
            else:
                logger.error(f"DTW alignment failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Block 2 error: {e}")
            return False
    
    def run_pqg_a2sa(self):
        """
        Layer 5: PQG-A2SA (Parallel with extraction)
        Precise onset/offset detection
        """
        logger.info("\n[Layer 5: PQG-A2SA]")
        
        if not self.config['pqg_a2sa']['enabled']:
            logger.info("PQG-A2SA disabled in config")
            return True
        
        try:
            # PQG-A2SA requires MIDI score
            # Check if original score is MIDI, otherwise use transcribed MIDI from Block 1
            score_midi = None
            
            if self.score_path.suffix.lower() in ['.mid', '.midi']:
                # Original score is MIDI - use it directly
                score_midi = self.score_path
                logger.info(f"Using original MIDI score: {score_midi.name}")
            elif 'transcription_midi' in self.results:
                # Use transcribed MIDI from temporal alignment (performance MIDI)
                # NOTE: This is the performance MIDI, not ideal for PQG-A2SA
                # TODO: Convert score MusicXML→MIDI in input layer
                score_midi = Path(self.results['transcription_midi'])
                logger.warning(f"Using performance MIDI as score (not ideal): {score_midi.name}")
                logger.warning("TODO: Add MusicXML→MIDI conversion in Layer 1 for proper score MIDI")
            else:
                logger.warning("No MIDI score available, skipping PQG-A2SA")
                return False
            
            # Import PQG-A2SA (using package import to handle relative imports correctly)
            pqg_dir = self.layers_dir / "05_pqg_a2sa"
            pqg_src_dir = str(pqg_dir / "src")
            
            # Add PQG src to path so we can import it as a package
            if pqg_src_dir not in sys.path:
                sys.path.insert(0, str(pqg_dir))
            
            # Import from the src package (which has proper __init__.py)
            import src as pqg_src
            PQGAligner = pqg_src.PQGAligner
            
            # Run PQG-A2SA
            aligner = PQGAligner()
            results = aligner.align(
                audio_path=str(self.audio_path),
                midi_path=str(score_midi),
                verbose=False
            )
            
            # Save results (handle numpy arrays)
            output_file = self.pqg_dir / "pqg_a2sa_results.json"
            
            def convert_numpy(obj):
                import numpy as np
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {k: convert_numpy(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy(item) for item in obj]
                return obj
            
            results_serializable = convert_numpy(results)
            
            with open(output_file, 'w') as f:
                json.dump(results_serializable, f, indent=2)
            
            logger.info(f" PQG-A2SA results saved: {output_file}")
            self.results['pqg_a2sa'] = str(output_file)
            self.status['pqg_a2sa'] = True
            return True
            
        except Exception as e:
            logger.warning(f"PQG-A2SA error (optional): {e}")
            return False
    
    def run_inference(self):
        """
        Layer 6: Inference Core
        Collect data from ALL layers and compute comprehensive metrics
        """
        logger.info("\n[Layer 6: Inference Core]")
        
        try:
            # Import inference core
            inference_dir = self.layers_dir / "06_inference"
            sys.path.insert(0, str(inference_dir))
            
            # Load alignment results (required)
            alignment_file = self.results.get('alignment')
            if not alignment_file:
                logger.error("No alignment results for inference")
                return False
            
            with open(alignment_file) as f:
                alignment_data = json.load(f)
            
            # Extract metrics from alignment results
            grading_metrics = alignment_data.get('grading_metrics', {})
            
            # Load extraction results (optional but recommended)
            extraction_results = {}
            if 'extraction' in self.results:
                logger.info("Loading extraction features...")
                try:
                    perf_features_file = self.results['extraction'].get('performance_features')
                    score_features_file = self.results['extraction'].get('score_features')
                    
                    if perf_features_file and Path(perf_features_file).exists():
                        with open(perf_features_file) as f:
                            extraction_results['performance'] = json.load(f)
                        logger.info(f"✓ Performance features loaded")
                    
                    if score_features_file and Path(score_features_file).exists():
                        with open(score_features_file) as f:
                            extraction_results['score'] = json.load(f)
                        logger.info(f"✓ Score features loaded")
                except Exception as e:
                    logger.warning(f"Could not load extraction features: {e}")
            
            # Load PQG-A2SA results (optional)
            pqg_results = {}
            if 'pqg_a2sa' in self.results:
                pqg_file = self.results['pqg_a2sa']
                if pqg_file and Path(pqg_file).exists():
                    try:
                        with open(pqg_file) as f:
                            pqg_results = json.load(f)
                        logger.info(f"✓ PQG-A2SA metrics loaded")
                    except Exception as e:
                        logger.warning(f"Could not load PQG-A2SA results: {e}")
            
            # Create comprehensive grading package with ALL metrics
            grading_package = {
                'timestamp': datetime.now().isoformat(),
                'audio_path': str(self.audio_path),
                'score_path': str(self.score_path),
                'alignment_metrics': grading_metrics,      # From Layer 3 (DTW)
                'extraction_features': extraction_results,  # From Layer 4 (NEW!)
                'pqg_a2sa_metrics': pqg_results,           # From Layer 5
                'temporal_alignment': self.results.get('alignment'),
                'context_alignment': self.results.get('context_alignment'),
                'scoregraph': self.results.get('scoregraph'),
                'transcription': self.results.get('transcription'),
                'beats': self.results.get('beats')
            }
            
            # Save grading package
            output_file = self.inference_dir / "grading_package_master.json"
            with open(output_file, 'w') as f:
                json.dump(grading_package, f, indent=2)
            
            logger.info(f" Inference package saved: {output_file}")
            self.results['grading_package'] = str(output_file)
            self.status['inference'] = True
            return True
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return False
    
    def run_grading(self):
        """
        Layer 7: Grading Layer
        Compute final grade from metrics
        """
        logger.info("\n[Layer 7: Grading Layer]")
        
        try:
            # Import grading layer
            grading_dir = self.layers_dir / "07_grading"
            sys.path.insert(0, str(grading_dir))
            
            # Load grading package
            package_file = self.results.get('grading_package')
            if not package_file:
                logger.error("No grading package for grading layer")
                return False
            
            with open(package_file) as f:
                package = json.load(f)
            
            # Extract metrics from the grading_metrics structure
            all_metrics = package.get('alignment_metrics', {})
            extraction_features = package.get('extraction_features', {})
            
            # Apply PQG-A2SA weights
            weights = self.config['grading']['pqg_a2sa_weights']
            
            # Compute weighted score
            score = 0.0
            components = {}
            
            # 1. PITCH ACCURACY (from alignment metrics)
            sound_quality = all_metrics.get('sound_quality', {})
            if 'pitch_accuracy_50c_percent' in sound_quality:
                pitch_accuracy = sound_quality['pitch_accuracy_50c_percent'] / 100.0  # Convert to 0-1
                components['pitch'] = pitch_accuracy * weights['pitch']
                score += components['pitch']
            
            # 2. NOTE ACCURACY (from alignment metrics)
            tech_virtuosity = all_metrics.get('technical_virtuosity', {})
            if 'note_accuracy_percent' in tech_virtuosity:
                note_accuracy = tech_virtuosity['note_accuracy_percent'] / 100.0  # Convert to 0-1
                components['note_accuracy'] = note_accuracy * weights['note_accuracy']
                score += components['note_accuracy']
            
            # 3. RHYTHM (from alignment metrics - IOI correlation)
            rhythm_tempo = all_metrics.get('rhythm_tempo', {})
            if 'ioi_correlation' in rhythm_tempo:
                rhythm_accuracy = rhythm_tempo['ioi_correlation']  # Already 0-1
                components['rhythm'] = rhythm_accuracy * weights['rhythm']
                score += components['rhythm']
            
            # 4. TEMPO ADHERENCE (from extraction features OR alignment)
            tempo_accuracy = None
            
            # Try to get tempo from extraction features first (more accurate)
            if extraction_features and 'performance' in extraction_features:
                perf = extraction_features['performance']
                if 'tempo_bpm' in perf and 'tempo_confidence' in perf:
                    detected_tempo = perf['tempo_bpm']
                    confidence = perf['tempo_confidence']
                    
                    # Get expected tempo from score or use default
                    expected_tempo = rhythm_tempo.get('expected_tempo_bpm', 120.0)
                    
                    # Only calculate if expected tempo is not default (120)
                    # or if we have high confidence in detected tempo
                    if expected_tempo != 120.0 or confidence > 0.7:
                        # Calculate tempo error as percentage deviation
                        tempo_error = abs(detected_tempo - expected_tempo) / expected_tempo
                        # Convert to accuracy (0-1), weight by confidence
                        tempo_accuracy = max(0, min(1, (1 - tempo_error))) * confidence
                        components['tempo'] = tempo_accuracy * weights['tempo']
                        score += components['tempo']
                        logger.info(f"  Tempo: detected={detected_tempo:.1f}, expected={expected_tempo:.1f}, accuracy={tempo_accuracy:.2%}")
            
            # Fallback: Use tempo consistency from rhythm_tempo if extraction not available
            if tempo_accuracy is None and 'tempo_cv_percent' in rhythm_tempo:
                # Lower CV = more consistent tempo = better score
                tempo_cv = rhythm_tempo['tempo_cv_percent']
                # Convert CV to score: 0% CV = 100%, 100% CV = 0%
                # Use sigmoid-like function for realistic grading
                tempo_consistency = max(0, min(1, 1 - (tempo_cv / 200)))  # Normalize to 0-1
                components['tempo'] = tempo_consistency * weights['tempo']
                score += components['tempo']
                logger.info(f"  Tempo (consistency): CV={tempo_cv:.1f}%, score={tempo_consistency:.2%}")
            
            # 5. ARTICULATION (from extraction features - spectral analysis)
            if extraction_features and 'performance' in extraction_features:
                perf = extraction_features['performance']
                
                # Check if we have spectral features
                if 'spectral_centroid' in perf and 'rms_energy' in perf:
                    import numpy as np
                    
                    spectral_centroid = np.array(perf['spectral_centroid'])
                    rms_energy = np.array(perf['rms_energy'])
                    
                    # Calculate articulation quality metrics
                    # 1. Spectral variation (timbre changes) - indicates clear note separation
                    if len(spectral_centroid) > 0 and np.mean(spectral_centroid) > 0:
                        spectral_variation = np.std(spectral_centroid) / np.mean(spectral_centroid)
                        spectral_variation = min(1.0, spectral_variation)  # Cap at 1.0
                    else:
                        spectral_variation = 0.0
                    
                    # 2. Dynamic range (loudness variation) - indicates expression and control
                    if len(rms_energy) > 0 and np.mean(rms_energy) > 0:
                        dynamic_range = np.std(rms_energy) / np.mean(rms_energy)
                        dynamic_range = min(1.0, dynamic_range)  # Cap at 1.0
                    else:
                        dynamic_range = 0.0
                    
                    # 3. Articulation precision from alignment (if available)
                    articulation_precision = 1.0  # Default
                    if 'articulation_precision_ms' in tech_virtuosity:
                        precision_ms = tech_virtuosity['articulation_precision_ms']
                        # Lower precision error = better articulation
                        # 0ms = 100%, 200ms = 0%
                        articulation_precision = max(0, min(1, 1 - (precision_ms / 200)))
                    
                    # Combine all three metrics (weighted average)
                    articulation_score = (
                        0.4 * spectral_variation +     # 40% - timbre variation
                        0.3 * dynamic_range +          # 30% - dynamic control
                        0.3 * articulation_precision   # 30% - timing precision
                    )
                    
                    components['articulation'] = articulation_score * weights['articulation']
                    score += components['articulation']
                    logger.info(f"  Articulation: spectral={spectral_variation:.2%}, dynamic={dynamic_range:.2%}, precision={articulation_precision:.2%}, total={articulation_score:.2%}")
            
            # Calculate which weights are being used
            used_weights = sum(weights[k] for k in components.keys())
            total_weight = sum(weights.values())
            
            # Normalize to 100-point scale based on USED weights
            # If all 5 components calculated, this will be the full score
            # If only 3 components, score is normalized to those 3
            final_score = (score / used_weights) * 100 if used_weights > 0 else 0.0
            
            # Store which components were calculated
            calculated_components = list(components.keys())
            missing_components = [k for k in weights.keys() if k not in components]
            
            # Create final grade with transparency about what was measured
            final_grade = {
                'overall_score': round(final_score, 2),
                'components': components,
                'weights': weights,
                'calculated_components': calculated_components,
                'missing_components': missing_components,
                'total_weight_used': used_weights,
                'total_weight_possible': total_weight,
                'note': 'Score based on available metrics only. Missing components require full pipeline integration.',
                'timestamp': datetime.now().isoformat()
            }
            
            # Save results
            output_file = self.grading_dir / "final_grade.json"
            with open(output_file, 'w') as f:
                json.dump(final_grade, f, indent=2)
            
            # Create text report
            report = self._generate_report(final_grade, all_metrics)
            report_file = self.grading_dir / "performance_report.txt"
            with open(report_file, 'w') as f:
                f.write(report)
            
            logger.info(f"✓ Final grade: {final_score:.1f}/100")
            logger.info(f"✓ Grade saved: {output_file}")
            logger.info(f"✓ Report saved: {report_file}")
            
            self.results['final_grade'] = str(output_file)
            self.status['grading'] = True
            return True
            
        except Exception as e:
            logger.error(f"Grading error: {e}")
            return False
    
    def _get_letter_grade(self, score):
        """Convert numeric score to letter grade"""
        thresholds = self.config['grading']['grade_thresholds']
        
        if score >= thresholds['A_plus']: return 'A+'
        elif score >= thresholds['A']: return 'A'
        elif score >= thresholds['A_minus']: return 'A-'
        elif score >= thresholds['B_plus']: return 'B+'
        elif score >= thresholds['B']: return 'B'
        elif score >= thresholds['B_minus']: return 'B-'
        elif score >= thresholds['C_plus']: return 'C+'
        elif score >= thresholds['C']: return 'C'
        elif score >= thresholds['C_minus']: return 'C-'
        elif score >= thresholds['D_plus']: return 'D+'
        elif score >= thresholds['D']: return 'D'
        elif score >= thresholds['D_minus']: return 'D-'
        else: return 'F'
    
    def _generate_report(self, grade, metrics):
        """Generate human-readable performance report"""
        report = []
        report.append("=" * 60)
        report.append("MUSIC PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Audio: {self.audio_path.name}")
        report.append(f"Score: {self.score_path.name}")
        report.append("")
        report.append("FINAL GRADE")
        report.append("-" * 60)
        report.append(f"Overall Score: {grade['overall_score']:.1f}/100")
        
        # Add transparency about what was measured
        if 'missing_components' in grade and grade['missing_components']:
            report.append("")
            report.append("NOTE: This score is based on available metrics only.")
            report.append(f"Calculated: {', '.join(grade.get('calculated_components', []))}")
            report.append(f"Missing: {', '.join(grade['missing_components'])}")
            report.append("(Missing components require full pipeline integration)")
        
        report.append("")
        report.append("COMPONENT SCORES")
        report.append("-" * 60)
        
        for component, value in grade['components'].items():
            weight = grade['weights'].get(component, 0) * 100
            contribution = value * 100  # Convert to percentage
            report.append(f"{component.replace('_', ' ').title()}: {contribution:.1f}% (weight: {weight:.0f}%)")
        
        # Show missing components
        if 'missing_components' in grade:
            for component in grade['missing_components']:
                weight = grade['weights'].get(component, 0) * 100
                report.append(f"{component.replace('_', ' ').title()}: Not calculated (weight: {weight:.0f}%)")
        
        report.append("")
        report.append("DETAILED METRICS")
        report.append("-" * 60)
        
        # Sound Quality
        if 'sound_quality' in metrics:
            sq = metrics['sound_quality']
            report.append("")
            report.append("Sound Quality:")
            if 'pitch_accuracy_50c_percent' in sq:
                report.append(f"  Pitch Accuracy (±50¢): {sq['pitch_accuracy_50c_percent']:.1f}%")
            if 'mean_pitch_error_cents' in sq:
                report.append(f"  Mean Pitch Error: {sq['mean_pitch_error_cents']:.1f} cents")
        
        # Technical Virtuosity
        if 'technical_virtuosity' in metrics:
            tv = metrics['technical_virtuosity']
            report.append("")
            report.append("Technical Virtuosity:")
            if 'note_accuracy_percent' in tv:
                report.append(f"  Note Accuracy: {tv['note_accuracy_percent']:.1f}%")
            if 'matched_notes' in tv:
                report.append(f"  Matched Notes: {tv['matched_notes']}/{tv.get('total_score_notes', '?')}")
            if 'extra_notes' in tv:
                report.append(f"  Extra Notes: {tv['extra_notes']}")
        
        # Rhythm & Tempo
        if 'rhythm_tempo' in metrics:
            rt = metrics['rhythm_tempo']
            report.append("")
            report.append("Rhythm & Tempo:")
            if 'ioi_correlation' in rt:
                report.append(f"  IOI Correlation: {rt['ioi_correlation']:.3f}")
            if 'mean_onset_error_ms' in rt:
                report.append(f"  Mean Onset Error: {rt['mean_onset_error_ms']:.1f} ms")
            if 'tempo_cv_percent' in rt:
                report.append(f"  Tempo Consistency: {rt['tempo_cv_percent']:.1f}% CV")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def run_pipeline(self):
        """Run complete pipeline"""
        logger.info("\n" + "="*70)
        logger.info("  MUSIC PERFORMANCE ANALYSIS PIPELINE")
        logger.info("="*70)
        logger.info(f"  Audio: {self.audio_path.name}")
        logger.info(f"  Score: {self.score_path.name}")
        logger.info(f"  Output: {self.output_dir.name}")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        # Layer 1 - Input Standardization
        if not self.run_input_layer():
            logger.warning("Input layer had issues (continuing)")
        
        # Layer 2 - Processing (noise reduction, normalization, segmentation)
        if not self.run_processing_layer():
            logger.warning("Processing layer had issues (continuing)")
        
        # Layer 3 - Temporal Alignment
        if not self.run_temporal_alignment():
            logger.error("Temporal alignment failed - stopping pipeline")
            return False
        
        # Layer 4 - Extraction (parallel with PQG-A2SA)
        # Note: In full implementation, this would run in parallel with Layer 3
        if not self.run_extraction_layer():
            logger.warning("Extraction layer had issues (continuing)")
        
        # Layer 5 - PQG-A2SA (optional, parallel with extraction)
        self.run_pqg_a2sa()  # Continue even if fails
        
        # Layer 6 - Inference Core
        if not self.run_inference():
            logger.error("Inference failed - stopping pipeline")
            return False
        
        # Layer 7 - Grading Layer
        if not self.run_grading():
            logger.error("Grading failed")
            return False
        
        # Create pipeline summary
        self._save_summary(start_time)
        
        logger.info("\n" + "="*70)
        logger.info("  ✓ PIPELINE COMPLETE")
        logger.info("="*70)
        
        return True
    
    def _save_summary(self, start_time):
        """Save pipeline summary"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'status': self.status,
            'results': self.results,
            'inputs': {
                'audio': str(self.audio_path),
                'score': str(self.score_path),
                'part': self.score_part
            },
            'output_directory': str(self.output_dir)
        }
        
        summary_file = self.output_dir / "pipeline_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Pipeline summary: {summary_file}")
        logger.info(f"Duration: {duration:.1f} seconds")


def main():
    parser = argparse.ArgumentParser(
        description="Music Performance Analysis Pipeline"
    )
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--score", required=True, help="Path to score file (MusicXML/MIDI)")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--part", type=int, default=None, help="Score part index (0-based, auto-detected if not specified)")
    parser.add_argument("--config", help="Path to config.yaml (optional)")
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = MusicPerformancePipeline(
        audio_path=args.audio,
        score_path=args.score,
        output_dir=args.output,
        config_path=args.config,
        score_part=args.part
    )
    
    success = pipeline.run_pipeline()
    
    if success:
        print("\n✓ Analysis complete!")
        print(f"Results: {args.output}")
        sys.exit(0)
    else:
        print("\n✗ Analysis failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
