"""
Audio-Music Processing Layer
============================

This module processes audio files (WAV) and music notation files (MIDI/XML)
through noise reduction, normalization, segmentation, and feature extraction.

Repository Dependencies:
- timsainb/noisereduce: Spectral gating for noise reduction
- slhck/ffmpeg-normalize: EBU R128 loudness normalization 
- amsehili/auditok: Energy-based audio segmentation (chosen over ina-foss alternatives)
- music21: MIDI/XML parsing and feature extraction
"""

import os
import json
import warnings
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
import time
import psutil
import logging

# Setup detailed logging for memory and timing diagnostics
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def log_memory_usage(stage: str):
    """Log current memory usage for debugging"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_percent = process.memory_percent()
        logger.info(f"[MEMORY {stage}] RSS: {mem_info.rss / 1024 / 1024:.1f}MB | VMS: {mem_info.vms / 1024 / 1024:.1f}MB | %: {mem_percent:.1f}%")
    except ImportError:
        logger.warning("psutil not available for memory monitoring")
    except Exception as e:
        logger.warning(f"Could not get memory info: {e}")

# Audio processing imports
try:
    import noisereduce as nr
    from scipy.io import wavfile
    import librosa
    import librosa.onset
    import soundfile as sf
    from ffmpeg_normalize import FFmpegNormalize
    import auditok
    logger.info("All audio processing dependencies loaded successfully")
except ImportError as e:
    logger.error(f"Audio processing dependencies missing: {e}")
    logger.error("Install with: pip install noisereduce scipy librosa soundfile")

# FFmpeg normalization import
try:
    from ffmpeg_normalize import FFmpegNormalize
except ImportError as e:
    print(f"FFmpeg normalization missing: {e}")
    print("Install with: pip install ffmpeg-normalize")

# Audio segmentation import  
try:
    import auditok
except ImportError as e:
    print(f"Auditok missing: {e}")
    print("Install with: pip install auditok")

# Music notation processing import
try:
    from music21 import converter, corpus, interval, roman, key, meter, tempo, pitch, stream
    from music21.analysis import discrete
except ImportError as e:
    print(f"Music21 missing: {e}")
    print("Install with: pip install music21")


@dataclass
class AudioSegment:
    """Represents a detected audio segment"""
    start_time: float
    end_time: float
    duration: float
    confidence: float
    segment_type: str = "speech"  # speech, music, noise


@dataclass
class MusicFeatures:
    """Extracted musical features from MIDI/XML"""
    notes: List[Dict]
    key_signature: str
    time_signature: str
    tempo: float
    tuning_info: Dict
    total_duration: float
    instruments: List[str]


@dataclass
class ProcessingResult:
    """Complete processing result"""
    audio_path: str
    music_path: str
    processed_audio_path: str
    audio_segments: List[AudioSegment]
    music_features: MusicFeatures
    processing_metadata: Dict


class AudioProcessor:
    """Handles audio file processing: noise reduction, normalization, segmentation"""
    
    def __init__(self, 
                 noise_reduction_threshold: float = 0.5,
                 normalization_target: float = -23.0,
                 segmentation_energy_threshold: int = 55):
        self.noise_reduction_threshold = noise_reduction_threshold
        self.normalization_target = normalization_target
        self.segmentation_energy_threshold = segmentation_energy_threshold
        
    def check_audio_quality(self, audio_path: str) -> Dict[str, bool]:
        """Check if audio requires noise reduction, normalization, or segmentation"""
        try:
            log_memory_usage("BEFORE_LOAD_AUDIO")
            start_time = time.time()
            
            # Load audio for analysis with REDUCED sample rate to save memory
            logger.info(f"[AUDIO_CHECK] Loading {audio_path} with sr=22050 (memory-optimized)")
            data, sr = librosa.load(audio_path, sr=22050, dtype=np.float32)  # Reduced SR + float32 = 50% less RAM
            
            logger.info(f"[AUDIO_CHECK] Loaded {len(data)} samples at {sr}Hz")
            log_memory_usage("AFTER_LOAD_AUDIO")
            
            # Check noise levels (simple RMS-based approach)
            rms_values = librosa.feature.rms(y=data, frame_length=2048, hop_length=512)[0]
            noise_threshold = np.percentile(rms_values, 10)  # Bottom 10% as noise estimate
            needs_noise_reduction = noise_threshold > self.noise_reduction_threshold
            
            # Check loudness levels (simplified)
            max_amplitude = np.max(np.abs(data))
            db_level = 20 * np.log10(max_amplitude + 1e-10)
            needs_normalization = abs(db_level - self.normalization_target) > 3.0
            
            # Always check for segmentation opportunities
            needs_segmentation = True
            
            elapsed = time.time() - start_time
            logger.info(f"[AUDIO_CHECK] Completed in {elapsed:.2f}s | SR: {needs_noise_reduction} | Norm: {needs_normalization} | Seg: {needs_segmentation}")
            log_memory_usage("AFTER_AUDIO_CHECK")
            
            return {
                'needs_noise_reduction': needs_noise_reduction,
                'needs_normalization': needs_normalization, 
                'needs_segmentation': needs_segmentation,
                'current_db_level': db_level,
                'noise_estimate': noise_threshold
            }
        except Exception as e:
            logger.error(f"Error analyzing audio quality: {e}")
            return {
                'needs_noise_reduction': True,
                'needs_normalization': True,
                'needs_segmentation': True,
                'current_db_level': -40.0,
                'noise_estimate': 0.1
            }
    
    def reduce_noise(self, audio_path: str, output_path: str) -> bool:
        """Apply spectral gating noise reduction using noisereduce"""
        try:
            log_memory_usage("BEFORE_NOISE_REDUCTION")
            start_time = time.time()
            
            logger.info(f"[NOISE_REDUCE] Starting noise reduction on {audio_path}")
            # Load audio
            rate, data = wavfile.read(audio_path)
            logger.info(f"[NOISE_REDUCE] Loaded audio: {len(data)} samples at {rate}Hz, size: {data.nbytes / 1024 / 1024:.1f}MB")
            log_memory_usage("AFTER_LOAD_NOISE")
            
            # Apply noise reduction using stationary algorithm
            reduced_noise = nr.reduce_noise(
                y=data, 
                sr=rate,
                stationary=True,
                prop_decrease=0.8  # Reduce noise by 80%
            )
            
            log_memory_usage("AFTER_REDUCE_NOISE")
            
            # Save processed audio
            wavfile.write(output_path, rate, reduced_noise.astype(data.dtype))
            elapsed = time.time() - start_time
            logger.info(f"[NOISE_REDUCE] Completed in {elapsed:.2f}s: {output_path}")
            log_memory_usage("AFTER_SAVE_NOISE")
            return True
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            return False
    
    def normalize_audio(self, audio_path: str, output_path: str) -> bool:
        """Apply peak normalization using scipy (faster, no FFmpeg subprocess hang)"""
        try:
            from scipy.io import wavfile
            import numpy as np
            import shutil
            
            log_memory_usage("BEFORE_NORMALIZATION")
            start_time = time.time()
            
            try:
                logger.info(f"[NORMALIZE] Starting normalization on {audio_path}")
                # Load audio
                rate, data = wavfile.read(audio_path)
                logger.info(f"[NORMALIZE] Loaded audio: {len(data)} samples, {data.nbytes / 1024 / 1024:.1f}MB")
                log_memory_usage("AFTER_LOAD_NORM")
                
                # Simple peak normalization
                max_val = np.max(np.abs(data))
                if max_val > 0:
                    # Target -20dB (safe level)
                    target_db = -20.0
                    target_linear = 10 ** (target_db / 20.0)
                    normalized = data * (target_linear / (max_val / 32768.0))
                    normalized = np.clip(normalized, -32768, 32767).astype(data.dtype)
                else:
                    normalized = data
                
                log_memory_usage("AFTER_NORMALIZE")
                
                # Save normalized audio
                wavfile.write(output_path, rate, normalized)
                elapsed = time.time() - start_time
                logger.info(f"[NORMALIZE] Completed in {elapsed:.2f}s: {output_path}")
                log_memory_usage("AFTER_SAVE_NORM")
                return True
                
            except Exception as scipy_error:
                print(f"Scipy normalization failed, copying file: {scipy_error}")
                # Fallback: just copy the file
                shutil.copy2(audio_path, output_path)
                print(f"Audio file copied (no normalization): {output_path}")
                return True
            
        except Exception as e:
            print(f"Error in audio normalization: {e}")
            return False
    
    def segment_audio(self, audio_path: str) -> List[AudioSegment]:
        """Segment audio with graceful fallback to simple approach"""
        try:
            import tempfile
            import soundfile as sf
            import os
            from threading import Thread
            
            logger.info(f"[SEGMENT] 🚀 Starting audio segmentation for: {audio_path}")
            
            # Read audio
            logger.info(f"[SEGMENT] ▶️  Loading audio file with soundfile...")
            data, sr = sf.read(audio_path)
            duration = len(data) / sr
            logger.info(f"[SEGMENT] ✅ Loaded: {len(data)} samples at {sr}Hz, duration: {duration:.2f}s")
            
            # Create temp file with clean WAV format
            logger.info(f"[SEGMENT] ▶️  Creating temporary WAV file for auditok...")
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                sf.write(tmp_file.name, data, sr, format='WAV', subtype='PCM_16')
                clean_audio_path = tmp_file.name
            logger.info(f"[SEGMENT] ✅ Temp file created: {clean_audio_path}")
            
            audio_events = None
            try:
                # Try auditok segmentation with timeout using threading
                def run_auditok():
                    nonlocal audio_events
                    try:
                        logger.info(f"[SEGMENT] 🔧 Calling auditok.split() with 2s timeout...")
                        audio_events = auditok.split(
                            clean_audio_path,
                            min_dur=0.2, max_dur=10.0, max_silence=0.5,
                            energy_threshold=self.segmentation_energy_threshold
                        )
                        logger.info(f"[SEGMENT] ✅ auditok.split() succeeded: {len(list(audio_events)) if audio_events else 0} regions found")
                    except Exception as e:
                        logger.error(f"[SEGMENT] ❌ auditok.split() failed with exception: {e}")
                        audio_events = None
                
                auditok_thread = Thread(target=run_auditok, daemon=True)
                logger.info(f"[SEGMENT] Starting auditok thread...")
                auditok_thread.start()
                logger.info(f"[SEGMENT] Waiting for auditok thread with 2s timeout...")
                auditok_thread.join(timeout=2.0)  # REDUCED from 5s to 2s - fail fast if slow
                
                if auditok_thread.is_alive():
                    logger.warning(f"[SEGMENT] ⚠️  auditok thread still alive after 2s timeout - using fallback")
                    audio_events = None
                else:
                    logger.info(f"[SEGMENT] ✅ auditok thread completed within timeout")
                
                if audio_events is not None:
                    # Auditok succeeded
                    logger.info(f"[SEGMENT] Converting auditok regions to AudioSegment objects...")
                    segments = [AudioSegment(
                        start_time=region.meta.start,
                        end_time=region.meta.end,
                        duration=region.duration,
                        confidence=1.0,
                        segment_type="detected_audio"
                    ) for region in audio_events]
                    
                    os.unlink(clean_audio_path)
                    logger.info(f"[SEGMENT] ✅ Audio segmentation completed: {len(segments)} segments")
                    print(f"Audio segmentation completed: {len(segments)} segments")
                    return segments
                else:
                    logger.warning(f"[SEGMENT] ⚠️  audio_events is None, raising TimeoutError for fallback handling")
                    raise TimeoutError("Auditok segmentation timeout or failed")
                
            except Exception as auditok_err:
                logger.warning(f"[SEGMENT] ⚠️  auditok failed: {auditok_err}, using full audio as segment")
                print(f"Auditok failed: {auditok_err}, using full audio as segment")
                try:
                    os.unlink(clean_audio_path)
                except:
                    pass
                
                # Fallback: single segment for entire audio
                logger.info(f"[SEGMENT] Creating fallback: single segment for entire {duration:.2f}s audio")
                return [AudioSegment(
                    start_time=0.0, end_time=duration, duration=duration,
                    confidence=1.0, segment_type="full_audio"
                )]
            
        except Exception as e:
            logger.error(f"[SEGMENT] ❌ Critical error in audio segmentation: {e}")
            print(f"Error in audio segmentation: {e}")
            return []


class MusicProcessor:
    """Handles MIDI/XML file processing and feature extraction"""
    
    def __init__(self):
        pass
    
    def extract_features(self, music_path: str) -> MusicFeatures:
        """Extract musical features from MIDI/XML using music21 with timeout"""
        try:
            from threading import Thread
            import time
            
            score = None
            parse_error = None
            
            def parse_music():
                nonlocal score, parse_error
                try:
                    score = converter.parse(music_path)
                except Exception as e:
                    parse_error = e
            
            # Start parsing in thread with timeout
            parse_thread = Thread(target=parse_music, daemon=True)
            parse_thread.start()
            parse_thread.join(timeout=10.0)  # Wait max 10 seconds for parsing
            
            if parse_error:
                raise parse_error
            
            if score is None:
                raise TimeoutError("Music21 parsing timeout - music file took too long to parse")
            
            # Extract notes using the proper music21 method
            notes_list = []
            
            # Use the correct music21 approach to get all notes and rests
            # First, check if score has parts (multi-part score)
            if hasattr(score, 'parts') and len(score.parts) > 0:
                # Multi-part score - flatten each part and combine
                all_elements = []
                for part in score.parts:
                    part_elements = part.flat.notesAndRests
                    all_elements.extend(part_elements)
            else:
                # Single part score - use flat directly
                all_elements = score.flat.notesAndRests
            
            for element in all_elements:
                if hasattr(element, 'pitch'):  # It's a note
                    note_data = {
                        'pitch': element.pitch.name,
                        'midi_number': element.pitch.midi,
                        'octave': element.pitch.octave,
                        'duration': float(element.duration.quarterLength),
                        'offset': float(element.offset),
                        'velocity': getattr(element, 'velocity', 64) if hasattr(element, 'velocity') else 64
                    }
                elif hasattr(element, 'isRest') and element.isRest:  # It's a rest
                    note_data = {
                        'pitch': 'rest',
                        'midi_number': -1,
                        'octave': -1,
                        'duration': float(element.duration.quarterLength),
                        'offset': float(element.offset),
                        'velocity': 0
                    }
                else:
                    continue
                notes_list.append(note_data)
            
            # Extract key signature
            key_sig = "Unknown"
            try:
                key_analysis = score.analyze('key')
                key_sig = f"{key_analysis.name} {key_analysis.mode}"
            except:
                pass
            
            # Extract time signature  
            time_sig = "4/4"
            try:
                ts = score.getTimeSignatures()[0] if score.getTimeSignatures() else None
                if ts:
                    time_sig = f"{ts.numerator}/{ts.denominator}"
            except:
                pass
            
            # Extract tempo
            tempo_bpm = 120.0
            try:
                tempo_indications = score.flatten().getElementsByClass(tempo.TempoIndication)
                if tempo_indications:
                    tempo_bpm = float(tempo_indications[0].number)
            except:
                pass
            
            # Extract tuning information (concert pitch reference)
            tuning_info = {
                'concert_pitch': 440.0,  # Standard A4 frequency
                'tuning_system': 'equal_temperament'
            }
            
            # Get total duration
            total_duration = float(score.duration.quarterLength)
            
            # Extract instruments
            instruments = []
            try:
                for part in score.parts:
                    if hasattr(part, 'partName') and part.partName:
                        instruments.append(part.partName)
                    elif len(part.getElementsByClass('Instrument')) > 0:
                        instr = part.getElementsByClass('Instrument')[0]
                        instruments.append(instr.instrumentName)
                
                if not instruments:
                    instruments = ['Piano']  # Default assumption
            except:
                instruments = ['Unknown']
            
            music_features = MusicFeatures(
                notes=notes_list,
                key_signature=key_sig,
                time_signature=time_sig,
                tempo=tempo_bpm,
                tuning_info=tuning_info,
                total_duration=total_duration,
                instruments=instruments
            )
            
            print(f"Music feature extraction completed: {len(notes_list)} notes, {key_sig} key, {time_sig} time")
            return music_features
            
        except Exception as e:
            print(f"Error in music feature extraction: {e}")
            # Return empty features as fallback
            return MusicFeatures(
                notes=[],
                key_signature="Unknown",
                time_signature="4/4", 
                tempo=120.0,
                tuning_info={'concert_pitch': 440.0, 'tuning_system': 'equal_temperament'},
                total_duration=0.0,
                instruments=['Unknown']
            )


class ProcessingLayer:
    """Main processing layer coordinating audio and music processing"""
    
    def __init__(self, data_dir: str = "data", shared_output_dir: str = "../shared_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create shared output directory for inter-layer communication
        self.shared_output_dir = Path(shared_output_dir)
        self.shared_output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for organization
        self.original_dir = self.data_dir / "original"
        self.processed_dir = self.data_dir / "processed"
        self.original_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)
        
        # Create shared subdirectories
        self.shared_original_dir = self.shared_output_dir / "original"
        self.shared_processed_dir = self.shared_output_dir / "processed"
        self.shared_original_dir.mkdir(exist_ok=True)
        self.shared_processed_dir.mkdir(exist_ok=True)
        
        self.audio_processor = AudioProcessor()
        self.music_processor = MusicProcessor()
    
    def process(self, audio_path: str, music_path: str) -> ProcessingResult:
        """
        Process both audio and music files
        
        Args:
            audio_path: Path to WAV audio file (live performance)
            music_path: Path to MIDI/XML file (music sheet)
            
        Returns:
            ProcessingResult containing all extracted data
        """
        logger.info(f"[PROCESS] 🚀 PROCESS METHOD STARTED")
        start_time = time.time()
        logger.info(f"[PROCESS] Input: audio={audio_path}, music={music_path}")
        logger.info(f"[PROCESS] Starting processing for audio: {audio_path}, music: {music_path}")
        log_memory_usage("PROCESS_START")
        
        # Create organized directory structure and copy input files
        logger.info(f"[PROCESS] ▶️  Step 0a: Preparing directory structure...")
        audio_filename = Path(audio_path).name
        music_filename = Path(music_path).name
        logger.info(f"[PROCESS] Audio filename: {audio_filename}, Music filename: {music_filename}")
        
        # Copy input files to original data directory
        import shutil
        original_audio_path = self.original_dir / audio_filename
        original_music_path = self.original_dir / music_filename
        
        logger.info(f"[PROCESS] ▶️  Step 0b: Copying files...")
        if not original_audio_path.exists():
            shutil.copy2(audio_path, original_audio_path)
            logger.info(f"[PROCESS] ✅ Audio file copied to: {original_audio_path}")
        else:
            logger.info(f"[PROCESS] ⏭️  Audio file already exists at: {original_audio_path}")

        if not original_music_path.exists():
            shutil.copy2(music_path, original_music_path)
            logger.info(f"[PROCESS] ✅ Music file copied to: {original_music_path}")
        else:
            logger.info(f"[PROCESS] ⏭️  Music file already exists at: {original_music_path}")
        
        # Also copy to shared directory for other layers to access
        shared_audio_path = self.shared_original_dir / audio_filename
        shared_music_path = self.shared_original_dir / music_filename
        
        if not shared_audio_path.exists():
            shutil.copy2(audio_path, shared_audio_path)
            print(f"Audio file copied to shared directory: {shared_audio_path}")
        
        if not shared_music_path.exists():
            shutil.copy2(music_path, shared_music_path)
            print(f"Music file copied to shared directory: {shared_music_path}")
        
        # Validate input files
        logger.info(f"[PROCESS] ▶️  Step 0c: Validating input files...")
        if not original_audio_path.exists():
            logger.error(f"[PROCESS] ❌ Audio file not found: {original_audio_path}")
            raise FileNotFoundError(f"Audio file not found: {original_audio_path}")
        if not original_music_path.exists():
            logger.error(f"[PROCESS] ❌ Music file not found: {original_music_path}")
            raise FileNotFoundError(f"Music file not found: {original_music_path}")
        logger.info(f"[PROCESS] ✅ Both files validated successfully")
        
        # Check audio processing requirements
        logger.info(f"[PROCESS] ▶️  Step 0d: Analyzing audio quality...")
        logger.info(f"[PROCESS] About to call check_audio_quality on {original_audio_path}")
        audio_analysis = self.audio_processor.check_audio_quality(str(original_audio_path))
        logger.info(f"[PROCESS] ✅ Audio analysis completed: {audio_analysis}")
        print(f"Audio analysis: {audio_analysis}")
        
        # Prepare output paths (all in processed directory)
        base_name = Path(audio_path).stem
        processed_audio_path = self.processed_dir / f"{base_name}_processed.wav"
        current_audio_path = str(original_audio_path)
        
        # Track intermediate files for cleanup
        intermediate_files = []
        
        # Apply audio processing steps as needed
        elapsed_checkpoint = time.time()
        if audio_analysis['needs_noise_reduction']:
            logger.info(f"[PROCESS] ▶️ Step 1: Applying noise reduction...")
            noise_reduced_path = self.processed_dir / f"{base_name}_denoised.wav"
            if self.audio_processor.reduce_noise(current_audio_path, str(noise_reduced_path)):
                intermediate_files.append(str(noise_reduced_path))
                current_audio_path = str(noise_reduced_path)
                elapsed = time.time() - elapsed_checkpoint
                logger.info(f"[PROCESS] ✅ Noise reduction completed in {elapsed:.2f}s")
                elapsed_checkpoint = time.time()
        else:
            logger.info(f"[PROCESS] ⏭️  Skipping noise reduction (not needed)")
        
        if audio_analysis['needs_normalization']:
            logger.info(f"[PROCESS] ▶️ Step 2: Applying normalization...")
            normalized_path = self.processed_dir / f"{base_name}_normalized.wav"
            if self.audio_processor.normalize_audio(current_audio_path, str(normalized_path)):
                intermediate_files.append(str(normalized_path))
                current_audio_path = str(normalized_path)
                elapsed = time.time() - elapsed_checkpoint
                logger.info(f"[PROCESS] ✅ Normalization completed in {elapsed:.2f}s")
                elapsed_checkpoint = time.time()
        else:
            logger.info(f"[PROCESS] ⏭️  Skipping normalization (not needed)")
        
        # Always save the final processed audio with a consistent name
        logger.info(f"[PROCESS] ▶️ Step 3: Saving final processed audio...")
        final_processed_path = self.processed_dir / f"{base_name}_processed.wav"
        shared_processed_audio_path = self.shared_processed_dir / f"{base_name}_processed.wav"
        
        if current_audio_path != str(original_audio_path):
            # Audio was processed, copy to final location
            import shutil
            shutil.copy2(current_audio_path, final_processed_path)
            shutil.copy2(current_audio_path, shared_processed_audio_path)
            processed_audio_path = str(final_processed_path)
            logger.info(f"[PROCESS] ✅ Final processed audio saved to: {processed_audio_path}")
            logger.info(f"[PROCESS] ✅ Final processed audio saved to shared directory: {shared_processed_audio_path}")
        else:
            # No processing was needed, but still create a copy for consistency
            import shutil
            shutil.copy2(str(original_audio_path), final_processed_path)
            shutil.copy2(str(original_audio_path), shared_processed_audio_path)
            processed_audio_path = str(final_processed_path)
            logger.info(f"[PROCESS] ⏭️  Original audio copied (no processing needed): {processed_audio_path}")
            logger.info(f"[PROCESS] ✅ Original audio copied to shared directory: {shared_processed_audio_path}")
        
        # Clean up intermediate files automatically
        for intermediate_file in intermediate_files:
            try:
                os.remove(intermediate_file)
                logger.info(f"[PROCESS] 🗑️  Cleaned up intermediate file: {intermediate_file}")
            except Exception as e:
                logger.warning(f"[PROCESS] ⚠️  Could not remove intermediate file {intermediate_file}: {e}")
        
        # Segment audio using the final processed version
        logger.info(f"[PROCESS] ▶️ Step 4: Starting audio segmentation (auditok)...")
        segments_start = time.time()
        segments = []
        if audio_analysis['needs_segmentation']:
            logger.info(f"[PROCESS] Calling segment_audio({processed_audio_path})...")
            segments = self.audio_processor.segment_audio(processed_audio_path)
            segments_elapsed = time.time() - segments_start
            logger.info(f"[PROCESS] ✅ Segmentation completed in {segments_elapsed:.2f}s: {len(segments)} segments")
        else:
            logger.info(f"[PROCESS] ⏭️  Skipping segmentation (not needed)")
        
        # Extract music features
        logger.info(f"[PROCESS] ▶️ Step 5: Extracting music features from {Path(original_music_path).name}...")
        features_start = time.time()
        music_features = self.music_processor.extract_features(str(original_music_path))
        features_elapsed = time.time() - features_start
        logger.info(f"[PROCESS] ✅ Feature extraction completed in {features_elapsed:.2f}s: {len(music_features.notes)} notes extracted")
        
        # Create processing result
        result = ProcessingResult(
            audio_path=str(original_audio_path),
            music_path=str(original_music_path),
            processed_audio_path=str(processed_audio_path),
            audio_segments=segments,
            music_features=music_features,
            processing_metadata={
                'audio_analysis': audio_analysis,
                'processing_steps_applied': {
                    'noise_reduction': audio_analysis['needs_noise_reduction'],
                    'normalization': audio_analysis['needs_normalization'],
                    'segmentation': audio_analysis['needs_segmentation']
                },
                'segments_count': len(segments),
                'notes_count': len(music_features.notes)
            }
        )
        
        # Save results as separate JSON files
        logger.info(f"[PROCESS] ▶️ Step 6: Saving processing results...")
        self.save_results(result, base_name)
        
        elapsed_total = time.time() - start_time
        logger.info(f"[PROCESS] ✅ Processing completed successfully in {elapsed_total:.2f}s!")
        log_memory_usage("PROCESS_END")
        return result
    
    def save_results(self, result: ProcessingResult, base_name: str):
        """Save processing results to separate JSON files"""
        
        # Convert NumPy types to Python native types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        # 1. Save audio segments timing data
        segments_file = self.processed_dir / f"{base_name}_audio_segments.json"
        shared_segments_file = self.shared_processed_dir / f"{base_name}_audio_segments.json"
        segments_data = {
            "audio_path": result.audio_path,
            "processed_audio_path": result.processed_audio_path,
            "total_segments": len(result.audio_segments),
            "audio_segments": convert_numpy_types([asdict(segment) for segment in result.audio_segments]),
            "processing_metadata": {
                "audio_analysis": convert_numpy_types(result.processing_metadata['audio_analysis']),
                "processing_steps_applied": convert_numpy_types(result.processing_metadata['processing_steps_applied'])
            }
        }
        
        try:
            with open(segments_file, 'w', encoding='utf-8') as f:
                json.dump(segments_data, f, indent=2, ensure_ascii=False)
            with open(shared_segments_file, 'w', encoding='utf-8') as f:
                json.dump(segments_data, f, indent=2, ensure_ascii=False)
            print(f"Audio segments data saved to: {segments_file}")
            print(f"Audio segments data saved to shared directory: {shared_segments_file}")
        except Exception as e:
            print(f"Error saving segments data: {e}")
        
        # 2. Save music features data (from XML/MIDI)
        music_file = self.processed_dir / f"{base_name}_music_features.json"
        shared_music_file = self.shared_processed_dir / f"{base_name}_music_features.json"
        music_data = {
            "music_path": result.music_path,
            "music_features": asdict(result.music_features),
            "extraction_metadata": {
                "total_notes": len(result.music_features.notes),
                "key_signature": result.music_features.key_signature,
                "time_signature": result.music_features.time_signature,
                "tempo": result.music_features.tempo,
                "total_duration": result.music_features.total_duration,
                "instruments": result.music_features.instruments
            }
        }
        
        try:
            with open(music_file, 'w', encoding='utf-8') as f:
                json.dump(music_data, f, indent=2, ensure_ascii=False)
            with open(shared_music_file, 'w', encoding='utf-8') as f:
                json.dump(music_data, f, indent=2, ensure_ascii=False)
            print(f"Music features data saved to: {music_file}")
            print(f"Music features data saved to shared directory: {shared_music_file}")
        except Exception as e:
            print(f"Error saving music features data: {e}")


def main():
    """Example usage of the processing layer"""
    
    # Example file paths (replace with actual paths)
    audio_file = "input.wav"
    music_file = "xml_score.musicxml"  # or .xml
    
    if not os.path.exists(audio_file) or not os.path.exists(music_file):
        print("Example files not found. Please provide actual audio and music files.")
        print("\nUsage example:")
        print("processor = ProcessingLayer()")
        print("result = processor.process('path/to/audio.wav', 'path/to/music.mid')")
        return
    
    # Initialize processing layer
    processor = ProcessingLayer(data_dir="data")
    
    try:
        # Process files
        result = processor.process(audio_file, music_file)
        
        # Display summary
        # print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        # print("="*50)
        print(f"Audio segments found: {len(result.audio_segments)}")
        print(f"Musical notes extracted: {len(result.music_features.notes)}")
        print(f"Key signature: {result.music_features.key_signature}")
        print(f"Time signature: {result.music_features.time_signature}")
        print(f"Tempo: {result.music_features.tempo} BPM")
        print(f"Instruments: {', '.join(result.music_features.instruments)}")
        
        print("\nProcessing steps applied:")
        steps = result.processing_metadata['processing_steps_applied']
        for step, applied in steps.items():
            status = "Done" if applied else "Not Done"
            print(f"  {status} {step.replace('_', ' ').title()}")
        
        print("\nOutput files created:")
        print(f"  Processed audio: {Path(audio_file).stem}_processed.wav")
        print(f"  Audio segments: {Path(audio_file).stem}_audio_segments.json")
        print(f"  Music features: {Path(audio_file).stem}_music_features.json")
        print(f"  Data directory: data/")
        
        # Display audio segments info
        if result.audio_segments:
            print(f"\nAudio segments detected:")
            for i, segment in enumerate(result.audio_segments[:5]):  # Show first 5 segments
                print(f"  Segment {i+1}: {segment.start_time:.2f}s - {segment.end_time:.2f}s ({segment.duration:.2f}s)")
            if len(result.audio_segments) > 5:
                print(f"  ... and {len(result.audio_segments) - 5} more segments")
        
    except Exception as e:
        print(f"Processing failed: {e}")


if __name__ == "__main__":
    main()