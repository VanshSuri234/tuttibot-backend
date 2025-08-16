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

# Audio processing imports
try:
    import noisereduce as nr
    from scipy.io import wavfile
    import librosa
    import soundfile as sf
except ImportError as e:
    print(f"Audio processing dependencies missing: {e}")
    print("Install with: pip install noisereduce scipy librosa soundfile")

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
            # Load audio for analysis
            data, sr = librosa.load(audio_path, sr=None)
            
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
            
            return {
                'needs_noise_reduction': needs_noise_reduction,
                'needs_normalization': needs_normalization, 
                'needs_segmentation': needs_segmentation,
                'current_db_level': db_level,
                'noise_estimate': noise_threshold
            }
        except Exception as e:
            print(f"Error analyzing audio quality: {e}")
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
            # Load audio
            rate, data = wavfile.read(audio_path)
            
            # Apply noise reduction using stationary algorithm
            reduced_noise = nr.reduce_noise(
                y=data, 
                sr=rate,
                stationary=True,
                prop_decrease=0.8  # Reduce noise by 80%
            )
            
            # Save processed audio
            wavfile.write(output_path, rate, reduced_noise.astype(data.dtype))
            print(f"Noise reduction completed: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error in noise reduction: {e}")
            return False
    
    def normalize_audio(self, audio_path: str, output_path: str) -> bool:
        """Apply EBU R128 loudness normalization using ffmpeg-normalize"""
        try:
            # Initialize FFmpeg normalizer
            normalizer = FFmpegNormalize(
                normalization_type="ebu",
                target_level=self.normalization_target,
                loudness_range_target=7.0,
                true_peak=-2.0
            )
            
            # Add media file for processing
            normalizer.add_media_file(audio_path, output_path)
            
            # Run normalization
            normalizer.run_normalization()
            print(f"Audio normalization completed: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error in audio normalization: {e}")
            return False
    
    def segment_audio(self, audio_path: str) -> List[AudioSegment]:
        """Segment audio using energy-based detection with auditok"""
        try:
            # Use auditok for audio activity detection
            audio_events = auditok.split(
                audio_path,
                min_dur=0.2,  # Minimum duration: 200ms
                max_dur=10.0,  # Maximum duration: 10s
                max_silence=0.5,  # Max silence within segment: 500ms
                energy_threshold=self.segmentation_energy_threshold
            )
            
            segments = []
            for i, region in enumerate(audio_events):
                segment = AudioSegment(
                    start_time=region.meta.start,
                    end_time=region.meta.end,
                    duration=region.duration,
                    confidence=1.0,  # auditok doesn't provide confidence scores
                    segment_type="detected_audio"
                )
                segments.append(segment)
            
            print(f"Audio segmentation completed: {len(segments)} segments found")
            return segments
            
        except Exception as e:
            print(f"Error in audio segmentation: {e}")
            return []


class MusicProcessor:
    """Handles MIDI/XML file processing and feature extraction"""
    
    def __init__(self):
        pass
    
    def extract_features(self, music_path: str) -> MusicFeatures:
        """Extract musical features from MIDI/XML using music21"""
        try:
            # Parse the music file
            score = converter.parse(music_path)
            
            # Extract notes
            notes_list = []
            for element in score.flatten().notesAndRests:
                if hasattr(element, 'pitch'):  # It's a note
                    note_data = {
                        'pitch': element.pitch.name,
                        'midi_number': element.pitch.midi,
                        'octave': element.pitch.octave,
                        'duration': float(element.duration.quarterLength),
                        'offset': float(element.offset),
                        'velocity': getattr(element, 'velocity', 64) if hasattr(element, 'velocity') else 64
                    }
                elif element.isRest:  # It's a rest
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
    
    def __init__(self, output_dir: str = "processed_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
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
        print(f"Starting processing for audio: {audio_path}, music: {music_path}")
        
        # Validate input files
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if not os.path.exists(music_path):
            raise FileNotFoundError(f"Music file not found: {music_path}")
        
        # Check audio processing requirements
        audio_analysis = self.audio_processor.check_audio_quality(audio_path)
        print(f"Audio analysis: {audio_analysis}")
        
        # Prepare output paths
        base_name = Path(audio_path).stem
        processed_audio_path = self.output_dir / f"{base_name}_processed.wav"
        current_audio_path = audio_path
        
        # Apply audio processing steps as needed
        if audio_analysis['needs_noise_reduction']:
            noise_reduced_path = self.output_dir / f"{base_name}_denoised.wav"
            if self.audio_processor.reduce_noise(current_audio_path, str(noise_reduced_path)):
                current_audio_path = str(noise_reduced_path)
        
        if audio_analysis['needs_normalization']:
            normalized_path = self.output_dir / f"{base_name}_normalized.wav"
            if self.audio_processor.normalize_audio(current_audio_path, str(normalized_path)):
                current_audio_path = str(normalized_path)
        
        # Copy final result to processed path if different
        if current_audio_path != audio_path:
            import shutil
            shutil.copy2(current_audio_path, processed_audio_path)
        else:
            processed_audio_path = audio_path
        
        # Segment audio
        segments = []
        if audio_analysis['needs_segmentation']:
            segments = self.audio_processor.segment_audio(str(processed_audio_path))
        
        # Extract music features
        music_features = self.music_processor.extract_features(music_path)
        
        # Create processing result
        result = ProcessingResult(
            audio_path=audio_path,
            music_path=music_path,
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
        
        # Save result as JSON
        self.save_result(result, base_name)
        
        print("Processing completed successfully!")
        return result
    
    def save_result(self, result: ProcessingResult, base_name: str):
        """Save processing result to JSON file"""
        output_file = self.output_dir / f"{base_name}_processing_result.json"
        
        # Convert result to dict for JSON serialization
        result_dict = asdict(result)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            print(f"Processing result saved to: {output_file}")
        except Exception as e:
            print(f"Error saving result: {e}")


def main():
    """Example usage of the processing layer"""
    
    # Example file paths (replace with actual paths)
    audio_file = "example_performance.wav"
    music_file = "example_sheet.mid"  # or .xml
    
    if not os.path.exists(audio_file) or not os.path.exists(music_file):
        print("Example files not found. Please provide actual audio and music files.")
        print("\nUsage example:")
        print("processor = ProcessingLayer()")
        print("result = processor.process('path/to/audio.wav', 'path/to/music.mid')")
        return
    
    # Initialize processing layer
    processor = ProcessingLayer(output_dir="processing_output")
    
    try:
        # Process files
        result = processor.process(audio_file, music_file)
        
        # Display summary
        print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        print("="*50)
        print(f"Audio segments found: {len(result.audio_segments)}")
        print(f"Musical notes extracted: {len(result.music_features.notes)}")
        print(f"Key signature: {result.music_features.key_signature}")
        print(f"Time signature: {result.music_features.time_signature}")
        print(f"Tempo: {result.music_features.tempo} BPM")
        print(f"Instruments: {', '.join(result.music_features.instruments)}")
        
        print("\nProcessing steps applied:")
        steps = result.processing_metadata['processing_steps_applied']
        for step, applied in steps.items():
            status = "✓" if applied else "✗"
            print(f"  {status} {step.replace('_', ' ').title()}")
        
    except Exception as e:
        print(f"Processing failed: {e}")


if __name__ == "__main__":
    main()