#!/usr/bin/env python3
"""
Music Performance Analysis - Extraction Layer

This layer extracts key features from both live performance audio and score data
for comparative analysis, error detection, and alignment.

Repository References:
- aubio (https://github.com/aubio/aubio): Pitch, onset, tempo detection
- essentia (https://github.com/MTG/essentia): Music analysis and feature extraction  
- librosa (https://github.com/bmcfee/librosa): Audio analysis and spectral features
- music21 (https://github.com/cuthbertLab/music21): Score analysis and music theory
- pretty_midi (https://github.com/craffel/pretty-midi): MIDI processing utilities
"""

import os
# Suppress TensorFlow warnings about GPU/CUDA
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=info, 2=warnings, 3=errors only

import json
import numpy as np
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict

# Suppress numpy deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Audio processing libraries
try:
    import aubio
except ImportError:
    aubio = None
    print("Warning: aubio not installed. Install with: pip install aubio")

try:
    import librosa
    import librosa.display
except ImportError:
    librosa = None
    print("Warning: librosa not installed. Install with: pip install librosa")

try:
    import essentia
    import essentia.standard as es
except ImportError:
    essentia = None
    print("Warning: essentia not installed. Install with: pip install essentia-tensorflow")

# Score processing libraries  
try:
    from music21 import converter, tempo, meter, key, note, chord, pitch, stream, analysis
except ImportError:
    print("Warning: music21 not installed. Install with: pip install music21")
    
try:
    import pretty_midi
except ImportError:
    pretty_midi = None
    print("Warning: pretty_midi not installed. Install with: pip install pretty_midi")

@dataclass
class PerformanceFeatures:
    """Features extracted from live performance audio"""
    # Pitch analysis
    pitch_contour: List[float]
    pitch_confidence: List[float] 
    fundamental_frequencies: List[float]
    
    # Timing analysis
    onset_times: List[float]
    onset_strengths: List[float]
    beat_times: List[float]
    tempo_bpm: float
    tempo_confidence: float
    
    # Spectral features
    spectral_centroid: List[float]
    spectral_rolloff: List[float]
    spectral_bandwidth: List[float]
    mfcc_features: List[List[float]]
    chroma_features: List[List[float]]
    
    # Energy and dynamics
    rms_energy: List[float]
    zero_crossing_rate: List[float]
    
    # Additional descriptors
    harmonic_content: List[float]
    percussive_content: List[float]
    
    # Metadata
    sample_rate: int
    duration: float
    frame_times: List[float]

@dataclass  
class ScoreFeatures:
    """Features extracted from musical score (MIDI/XML)"""
    # Pitch and harmony
    expected_pitches: List[int]
    pitch_classes: List[int]
    key_signature: str
    chord_progressions: List[str]
    intervals: List[int]
    
    # Rhythm and timing
    note_onsets: List[float]
    note_durations: List[float]
    time_signatures: List[str]
    tempo_markings: List[Dict]
    beat_positions: List[float]
    
    # Dynamics and articulation
    velocity_markings: List[int]
    dynamic_markings: List[str]
    articulation_symbols: List[str]
    
    # Structure
    phrase_boundaries: List[Tuple[float, float]]
    section_labels: List[str]
    meter_analysis: Dict
    
    # Metadata
    total_duration: float
    num_voices: int
    instrument_names: List[str]

class AudioFeatureExtractor:
    """Extract features from performance audio using multiple libraries"""
    
    def __init__(self, sample_rate: int = 22050, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.win_length = 2048
        
    def extract_features(self, audio_file: str, segments_file: str) -> PerformanceFeatures:
        """Extract comprehensive features from performance audio"""
        
        # Load audio and segmentation data
        if librosa is None:
            raise ImportError("librosa is required for audio feature extraction")
            
        y, sr = librosa.load(audio_file, sr=self.sample_rate)
        
        with open(segments_file, 'r') as f:
            segments_data = json.load(f)
        
        print(f"Loaded {len(segments_data.get('audio_segments', []))} audio segments from JSON")
        
        # Extract features using multiple methods
        features = {}
        
        # Use segmentation data to focus analysis on active regions
        features.update(self._extract_segment_aware_features(y, sr, segments_data))
        
        # Pitch analysis (aubio + librosa)
        features.update(self._extract_pitch_features(y, sr, segments_data))
        
        # Onset detection (aubio + librosa)  
        features.update(self._extract_onset_features(y, sr, segments_data))
        
        # Tempo analysis (librosa + essentia)
        features.update(self._extract_tempo_features(y, sr, segments_data))
        
        # Spectral features (librosa + essentia)
        features.update(self._extract_spectral_features(y, sr, segments_data))
        
        # Harmonic/percussive separation (librosa)
        features.update(self._extract_harmonic_percussive(y, sr))
        
        # Frame timing
        frame_times = librosa.frames_to_time(
            np.arange(len(features['spectral_centroid'])), 
            sr=sr, hop_length=self.hop_length
        )
        
        return PerformanceFeatures(
            pitch_contour=features['pitch_contour'],
            pitch_confidence=features['pitch_confidence'],
            fundamental_frequencies=features['f0'],
            onset_times=features['onset_times'],
            onset_strengths=features['onset_strengths'],
            beat_times=features['beat_times'],
            tempo_bpm=features['tempo_bpm'],
            tempo_confidence=features['tempo_confidence'],
            spectral_centroid=features['spectral_centroid'].tolist(),
            spectral_rolloff=features['spectral_rolloff'].tolist(),
            spectral_bandwidth=features['spectral_bandwidth'].tolist(),
            mfcc_features=features['mfcc'].T.tolist(),
            chroma_features=features['chroma'].T.tolist(),
            rms_energy=features['rms'].flatten().tolist(),
            zero_crossing_rate=features['zcr'].flatten().tolist(),
            harmonic_content=features['harmonic_energy'].tolist(),
            percussive_content=features['percussive_energy'].tolist(),
            sample_rate=sr,
            duration=len(y) / sr,
            frame_times=frame_times.tolist()
        )
    
    def _extract_segment_aware_features(self, y: np.ndarray, sr: int, segments_data: Dict) -> Dict:
        """Extract features using segmentation information from JSON"""
        features = {}
        
        segments = segments_data.get('audio_segments', [])
        
        # Extract segment-specific features
        segment_features = []
        active_regions = []
        
        for i, segment in enumerate(segments):
            start_time = segment.get('start', 0)
            end_time = segment.get('end', len(y) / sr)
            confidence = segment.get('confidence', 1.0)
            
            # Convert to sample indices
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            if end_sample > len(y):
                end_sample = len(y)
            
            # Extract segment audio
            segment_audio = y[start_sample:end_sample]
            
            if len(segment_audio) > 0:
                # Calculate segment-level features
                segment_rms = np.sqrt(np.mean(segment_audio**2))
                segment_energy = np.sum(segment_audio**2)
                segment_duration = (end_sample - start_sample) / sr
                
                segment_info = {
                    'segment_id': i,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': segment_duration,
                    'confidence': confidence,
                    'rms_energy': float(segment_rms),
                    'total_energy': float(segment_energy),
                    'activity_level': 'active' if segment_rms > 0.01 else 'quiet'
                }
                
                segment_features.append(segment_info)
                
                # Mark as active region if above threshold
                if segment_rms > 0.01:
                    active_regions.append((start_time, end_time))
        
        features['segment_analysis'] = segment_features
        features['active_regions'] = active_regions
        features['num_segments'] = len(segments)
        features['total_active_duration'] = sum(end - start for start, end in active_regions)
        
        print(f"Identified {len(active_regions)} active regions from {len(segments)} segments")
        
        return features
    
    def _extract_pitch_features(self, y: np.ndarray, sr: int, segments_data: Dict = None) -> Dict:
        """Extract pitch-related features"""
        features = {}
        
        # Librosa pitch tracking
        f0 = librosa.yin(y, fmin=librosa.note_to_hz('C2'), 
                        fmax=librosa.note_to_hz('C7'))
        features['f0'] = f0.tolist()
        
        # Aubio pitch detection (if available)
        if aubio is not None:
            # Setup aubio pitch detector
            pitch_detector = aubio.pitch("default", self.win_length, 
                                       self.hop_length, sr)
            pitch_detector.set_unit("Hz")
            pitch_detector.set_silence(-40)
            
            pitches = []
            confidences = []
            
            # Process audio in chunks
            for i in range(0, len(y) - self.hop_length, self.hop_length):
                samples = y[i:i+self.hop_length].astype(np.float32)
                pitch_val = pitch_detector(samples)[0]
                confidence = pitch_detector.get_confidence()
                
                pitches.append(pitch_val)
                confidences.append(confidence)
            
            features['pitch_contour'] = pitches
            features['pitch_confidence'] = confidences
        else:
            # Fallback to librosa
            features['pitch_contour'] = f0.tolist()
            features['pitch_confidence'] = [1.0] * len(f0)
            
        return features
    
    def _extract_onset_features(self, y: np.ndarray, sr: int, segments_data: Dict = None) -> Dict:
        """Extract onset-related features"""
        features = {}
        
        # Librosa onset detection
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, 
                                                 hop_length=self.hop_length)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, 
                                           hop_length=self.hop_length)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr,
                                               hop_length=self.hop_length)
        
        features['onset_times'] = onset_times.tolist()
        features['onset_strengths'] = onset_env.tolist()
        
        # Aubio onset detection (if available)
        if aubio is not None:
            onset_detector = aubio.onset("default", self.win_length,
                                       self.hop_length, sr)
            
            aubio_onsets = []
            for i in range(0, len(y) - self.hop_length, self.hop_length):
                samples = y[i:i+self.hop_length].astype(np.float32)
                if onset_detector(samples):
                    aubio_onsets.append(i / sr)
            
            # Combine with librosa results
            if aubio_onsets:
                features['onset_times_aubio'] = aubio_onsets
        
        return features
    
    def _extract_tempo_features(self, y: np.ndarray, sr: int, segments_data: Dict = None) -> Dict:
        """Extract tempo and beat-related features"""
        features = {}
        
        # Librosa tempo estimation
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, 
                                              hop_length=self.hop_length)
        beat_times = librosa.frames_to_time(beats, sr=sr,
                                          hop_length=self.hop_length)
        
        features['tempo_bpm'] = float(tempo.item() if hasattr(tempo, 'item') else tempo)
        features['beat_times'] = beat_times.tolist()
        features['tempo_confidence'] = 1.0  # librosa doesn't provide confidence
        
        # Essentia tempo estimation (if available)
        if essentia is not None:
            try:
                rhythm_extractor = es.RhythmExtractor2013()
                result = rhythm_extractor(y.astype(np.float32))
                
                # Handle different return formats from essentia
                if len(result) >= 2:
                    bpm = result[0]
                    beats_es = result[1]
                    
                    # Use essentia if confidence is higher (simple heuristic)
                    if abs(bpm - tempo) < 20:  # Similar tempos
                        features['tempo_bpm'] = float(bpm)
                        features['tempo_confidence'] = 0.9
                    
            except Exception as e:
                print(f"Essentia tempo extraction failed: {e}")
        
        return features
    
    def _extract_spectral_features(self, y: np.ndarray, sr: int, segments_data: Dict = None) -> Dict:
        """Extract spectral features"""
        features = {}
        
        # Librosa spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr,
                                                             hop_length=self.hop_length)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr,
                                                           hop_length=self.hop_length)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr,
                                                              hop_length=self.hop_length)[0]
        
        # MFCC features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13,
                                   hop_length=self.hop_length)
        
        # Chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr,
                                           hop_length=self.hop_length)
        
        # Energy features
        rms = librosa.feature.rms(y=y, hop_length=self.hop_length)
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=self.hop_length)
        
        features.update({
            'spectral_centroid': spectral_centroids,
            'spectral_rolloff': spectral_rolloff,
            'spectral_bandwidth': spectral_bandwidth,
            'mfcc': mfccs,
            'chroma': chroma,
            'rms': rms,
            'zcr': zcr
        })
        
        return features
    
    def _extract_harmonic_percussive(self, y: np.ndarray, sr: int) -> Dict:
        """Extract harmonic and percussive components"""
        features = {}
        
        # Separate harmonic and percussive components
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        # Calculate energy in each component
        harmonic_energy = librosa.feature.rms(y=y_harmonic, 
                                            hop_length=self.hop_length)[0]
        percussive_energy = librosa.feature.rms(y=y_percussive,
                                              hop_length=self.hop_length)[0]
        
        features.update({
            'harmonic_energy': harmonic_energy,
            'percussive_energy': percussive_energy
        })
        
        return features

class ScoreFeatureExtractor:
    """Extract features from musical scores (MIDI/XML)"""
    
    def __init__(self, audio_filename: str = None):
        """
        Initialize score feature extractor
        
        Args:
            audio_filename: Name of audio file being analyzed (used for part selection in multi-part scores)
        """
        self.audio_filename = audio_filename
    
    def extract_features(self, score_file: str, score_json_file: str) -> ScoreFeatures:
        """Extract comprehensive features from musical score"""
        
        # Load existing score features
        with open(score_json_file, 'r') as f:
            existing_features = json.load(f)
        
        # Determine file type and extract accordingly
        if score_file.endswith('.mid') or score_file.endswith('.midi'):
            return self._extract_from_midi(score_file, existing_features)
        elif score_file.endswith('.xml') or score_file.endswith('.musicxml'):
            return self._extract_from_xml(score_file, existing_features)
        else:
            raise ValueError(f"Unsupported score format: {score_file}")
    
    def _extract_from_midi(self, midi_file: str, existing_features: Dict) -> ScoreFeatures:
        """Extract features from MIDI file"""
        features = {}
        
        # Use pretty_midi for robust MIDI processing
        if pretty_midi is not None:
            midi_data = pretty_midi.PrettyMIDI(midi_file)
            features.update(self._extract_pretty_midi_features(midi_data))
        
        # Use music21 for music theory analysis
        try:
            score = converter.parse(midi_file)
            features.update(self._extract_music21_features(score))
        except Exception as e:
            print(f"Music21 MIDI parsing failed: {e}")
        
        return self._build_score_features(features, existing_features)
    
    def _extract_from_xml(self, xml_file: str, existing_features: Dict) -> ScoreFeatures:
        """Extract features from MusicXML file"""
        features = {}
        
        # Use music21 for XML processing
        try:
            score = converter.parse(xml_file)
            features.update(self._extract_music21_features(score))
        except Exception as e:
            print(f"Music21 XML parsing failed: {e}")
            
        return self._build_score_features(features, existing_features)
    
    def _extract_pretty_midi_features(self, midi_data) -> Dict:
        """Extract features using pretty_midi"""
        features = {}
        
        # Tempo analysis
        tempo_changes = midi_data.get_tempo_changes()
        features['tempo_changes'] = {
            'times': tempo_changes[0].tolist(),
            'tempos': tempo_changes[1].tolist()
        }
        
        # Extract notes from all instruments
        all_notes = []
        instrument_names = []
        
        for instrument in midi_data.instruments:
            if not instrument.is_drum:
                instrument_names.append(instrument.name)
                for note in instrument.notes:
                    all_notes.append({
                        'pitch': note.pitch,
                        'start': note.start,
                        'end': note.end,
                        'velocity': note.velocity
                    })
        
        # Sort notes by start time
        all_notes.sort(key=lambda x: x['start'])
        
        features.update({
            'midi_notes': all_notes,
            'instrument_names': instrument_names,
            'total_duration': midi_data.get_end_time(),
            'num_instruments': len([i for i in midi_data.instruments if not i.is_drum])
        })
        
        return features
    
    def _select_part_for_instrument(self, score: stream.Stream) -> int:
        """
        Select which part of a multi-part score to extract based on instrument type
        
        Args:
            score: Music21 score with multiple parts
            
        Returns:
            Part index (0-based) or None if no match
        """
        if not self.audio_filename:
            return None
        
        filename_lower = self.audio_filename.lower()
        
        # Define instrument to part mapping for SATB scores
        # Part indices: 0=Soprano (highest), 1=Alto, 2=Tenor, 3=Bass (lowest)
        bass_instruments = ['bassoon', 'cello', 'bass', 'tuba', 'trombone', 'contrabass']
        tenor_instruments = ['saxophone', 'saxphone', 'tenor', 'euphonium']
        alto_instruments = ['clarinet', 'alto', 'horn', 'viola']
        soprano_instruments = ['violin', 'flute', 'oboe', 'soprano', 'trumpet']
        
        # Check for bass instruments (use lowest part - typically part 3 in SATB)
        for inst in bass_instruments:
            if inst in filename_lower:
                return min(3, len(score.parts) - 1)  # Part 3 (or last part if <4 parts)
        
        # Check for tenor instruments (use part 2 in SATB)
        for inst in tenor_instruments:
            if inst in filename_lower:
                return min(2, len(score.parts) - 1)
        
        # Check for alto instruments (use part 1 in SATB)
        for inst in alto_instruments:
            if inst in filename_lower:
                return min(1, len(score.parts) - 1)
        
        # Check for soprano instruments (use highest part - part 0)
        for inst in soprano_instruments:
            if inst in filename_lower:
                return 0
        
        # No instrument detected - return None to use all parts
        return None
    
    def _extract_music21_features(self, score: stream.Stream) -> Dict:
        """Extract features using music21"""
        features = {}
        
        # Check if score has multiple parts
        num_parts = len(score.parts) if hasattr(score, 'parts') and score.parts else 0
        
        # Select the appropriate part if this is a multi-part score
        if num_parts > 1:
            selected_part = self._select_part_for_instrument(score)
            if selected_part is not None:
                print(f"Multi-part score detected ({num_parts} parts) - selected part {selected_part + 1} for analysis")
                flat_score = score.parts[selected_part].flatten()
            else:
                print(f"Multi-part score ({num_parts} parts) - using all parts (no instrument detected)")
                flat_score = score.flat
        else:
            # Single part or no parts - flatten the whole score
            flat_score = score.flat
        
        # Key analysis
        key_obj = flat_score.analyze('key')
        features['key_signature'] = str(key_obj)
        
        # Time signature analysis
        time_sigs = []
        for ts in flat_score.getElementsByClass(meter.TimeSignature):
            time_sigs.append({
                'time': float(ts.offset),
                'numerator': ts.numerator,
                'denominator': ts.denominator,
                'signature': str(ts)
            })
        features['time_signatures'] = time_sigs
        
        # Tempo markings
        tempo_marks = []
        for tempo_mark in flat_score.getElementsByClass(tempo.TempoIndication):
            tempo_marks.append({
                'time': float(tempo_mark.offset),
                'bpm': getattr(tempo_mark, 'number', None),
                'text': str(tempo_mark)
            })
        features['tempo_markings'] = tempo_marks
        
        # Note analysis
        notes_and_chords = flat_score.notes
        note_data = []
        pitch_classes = []
        intervals = []
        
        prev_pitch = None
        for element in notes_and_chords:
            if isinstance(element, note.Note):
                note_data.append({
                    'pitch': element.pitch.midi,
                    'onset': float(element.offset),
                    'duration': float(element.duration.quarterLength),
                    'name': element.name
                })
                pitch_classes.append(element.pitch.pitchClass)
                
                if prev_pitch is not None:
                    interval = element.pitch.midi - prev_pitch
                    intervals.append(interval)
                prev_pitch = element.pitch.midi
                
            elif isinstance(element, chord.Chord):
                # Handle chords
                for chord_note in element.notes:
                    note_data.append({
                        'pitch': chord_note.pitch.midi,
                        'onset': float(element.offset),
                        'duration': float(element.duration.quarterLength),
                        'name': chord_note.name
                    })
                    pitch_classes.append(chord_note.pitch.pitchClass)
        
        features.update({
            'notes': note_data,
            'pitch_classes': pitch_classes,
            'intervals': intervals,
            'num_voices': len(score.parts) if hasattr(score, 'parts') else 1
        })
        
        # Chord analysis
        try:
            chord_symbols = []
            for chord_sym in flat_score.getElementsByClass('ChordSymbol'):
                chord_symbols.append({
                    'time': float(chord_sym.offset),
                    'symbol': str(chord_sym)
                })
            features['chord_progressions'] = chord_symbols
        except:
            features['chord_progressions'] = []
        
        return features
    
    def _build_score_features(self, extracted: Dict, existing: Dict) -> ScoreFeatures:
        """Build ScoreFeatures object from extracted data and existing JSON"""
        
        print("Integrating extracted features with existing JSON data...")
        
        # Prioritize existing JSON data (from processing layer) as it's already processed
        # Use extracted features to supplement or validate
        
        # Start with existing JSON features
        existing_notes = existing.get('notes', [])
        existing_metadata = existing.get('metadata', {})
        
        # Get extracted features as backup/supplement
        extracted_notes = extracted.get('notes', [])
        midi_notes = extracted.get('midi_notes', [])
        
        print(f"Found {len(existing_notes)} notes in JSON, {len(extracted_notes)} from music21, {len(midi_notes)} from MIDI")
        
        # Choose best source for note data (prioritize existing JSON)
        if existing_notes:
            source_notes = existing_notes
            print("Using notes from existing JSON (processing layer)")
        elif midi_notes:
            source_notes = midi_notes  
            print("Using notes from MIDI extraction")
        else:
            source_notes = extracted_notes
            print("Using notes from music21 extraction")
        
        # Extract comprehensive note information
        expected_pitches = []
        note_onsets = []
        note_durations = []
        velocity_markings = []
        pitch_classes = []
        
        for note_info in source_notes:
            if isinstance(note_info, dict):
                # Handle different note formats from JSON vs extraction
                pitch = note_info.get('pitch', note_info.get('midi', 60))
                onset = note_info.get('onset', note_info.get('start', 0))
                duration = note_info.get('duration', 0.5)
                velocity = note_info.get('velocity', 64)
                
                # Handle duration calculation for MIDI notes
                if 'end' in note_info and 'start' in note_info:
                    duration = note_info['end'] - note_info['start']
                
                expected_pitches.append(pitch)
                note_onsets.append(onset)
                note_durations.append(duration)
                velocity_markings.append(velocity)
                pitch_classes.append(pitch % 12)
        
        # Extract timing information (prioritize JSON)
        tempo_info = existing_metadata.get('tempo', extracted.get('tempo_markings', []))
        if isinstance(tempo_info, (int, float)):
            tempo_markings = [{'time': 0, 'bpm': tempo_info, 'text': f'{tempo_info} BPM'}]
        elif isinstance(tempo_info, list):
            tempo_markings = tempo_info
        else:
            tempo_markings = extracted.get('tempo_markings', [])
            
        # Extract key information (prioritize JSON)
        key_info = existing_metadata.get('key', extracted.get('key_signature', 'C major'))
        
        # Extract time signature (prioritize JSON)  
        time_sig_info = existing_metadata.get('time_signature', '4/4')
        if isinstance(time_sig_info, str):
            time_signatures = [time_sig_info]
        else:
            time_signatures = [ts.get('signature', '4/4') for ts in 
                             extracted.get('time_signatures', [{'signature': '4/4'}])]
        
        # Extract chord progressions
        chord_progressions = []
        if 'chords' in existing:
            chord_progressions = [c.get('symbol', c.get('name', '')) for c in existing['chords']]
        else:
            chord_progressions = [c.get('symbol', '') for c in 
                                extracted.get('chord_progressions', [])]
        
        # Calculate intervals
        intervals = []
        if len(expected_pitches) > 1:
            for i in range(1, len(expected_pitches)):
                intervals.append(expected_pitches[i] - expected_pitches[i-1])
        
        # Extract duration and metadata
        total_duration = existing_metadata.get('duration', 
                                             extracted.get('total_duration', 
                                                         max(note_onsets) + max(note_durations) if note_onsets and note_durations else 0))
        
        instrument_names = existing_metadata.get('instruments', 
                                               extracted.get('instrument_names', ['Piano']))
        if isinstance(instrument_names, str):
            instrument_names = [instrument_names]
            
        num_voices = existing_metadata.get('voices', 
                                         extracted.get('num_voices', 1))
        
        print(f"Built score features: {len(expected_pitches)} notes, {len(chord_progressions)} chords, key: {key_info}")
        
        return ScoreFeatures(
            expected_pitches=expected_pitches,
            pitch_classes=pitch_classes,
            key_signature=str(key_info),
            chord_progressions=chord_progressions,
            intervals=intervals,
            note_onsets=note_onsets,
            note_durations=note_durations,
            time_signatures=time_signatures,
            tempo_markings=tempo_markings,
            beat_positions=[],  # Would need beat tracking from score
            velocity_markings=velocity_markings,
            dynamic_markings=existing_metadata.get('dynamics', []),
            articulation_symbols=existing_metadata.get('articulations', []),
            phrase_boundaries=existing_metadata.get('phrases', []),
            section_labels=existing_metadata.get('sections', []),
            meter_analysis=existing_metadata.get('meter_analysis', {}),
            total_duration=float(total_duration),
            num_voices=int(num_voices),
            instrument_names=instrument_names
        )

class ExtractionLayer:
    """Main extraction layer class"""
    
    def __init__(self, sample_rate: int = 22050, hop_length: int = 512):
        self.audio_extractor = AudioFeatureExtractor(sample_rate, hop_length)
        self.score_extractor = None  # Will be initialized with audio filename
        self.audio_filename = None
        
    def _convert_numpy_types(self, obj):
        """Convert numpy types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        return obj
        
    def process_performance_data(self, audio_file: str, segments_file: str,
                               output_dir: str = "data/extracted") -> str:
        """Process live performance data and extract features"""
        
        print("Extracting performance features from audio...")
        performance_features = self.audio_extractor.extract_features(
            audio_file, segments_file)
        
        # Save performance features
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        performance_file = output_path / "performance_features.json"
        
        with open(performance_file, 'w') as f:
            json.dump(self._convert_numpy_types(asdict(performance_features)), f, indent=2)
        
        print(f"Performance features saved to: {performance_file}")
        return str(performance_file)
    
    def process_score_data(self, score_file: str, score_json_file: str,
                          output_dir: str = "data/extracted") -> str:
        """Process score data and extract features"""
        
        print("Extracting score features...")
        score_features = self.score_extractor.extract_features(
            score_file, score_json_file)
        
        # Save score features
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        score_file_out = output_path / "score_features.json"
        with open(score_file_out, 'w') as f:
            json.dump(self._convert_numpy_types(asdict(score_features)), f, indent=2)
        
        print(f"Score features saved to: {score_file_out}")
        return str(score_file_out)
    
    def process_all(self, audio_file: str, segments_file: str,
                   score_file: str, score_json_file: str,
                   output_dir: str = "data/extracted") -> Dict[str, str]:
        """Process both performance and score data"""
        
        print("=" * 60)
        print("MUSIC PERFORMANCE ANALYSIS - EXTRACTION LAYER")
        print("=" * 60)
        
        # Initialize score extractor with audio filename for part selection
        from pathlib import Path
        self.audio_filename = Path(audio_file).name
        self.score_extractor = ScoreFeatureExtractor(audio_filename=self.audio_filename)
        
        # Process performance data
        performance_output = self.process_performance_data(
            audio_file, segments_file, output_dir)
        
        # Process score data  
        score_output = self.process_score_data(
            score_file, score_json_file, output_dir)
        
        # Create summary
        summary = {
            'performance_features': performance_output,
            'score_features': score_output,
            'extraction_complete': True
        }
        
        summary_file = Path(output_dir) / "extraction_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("=" * 60)
        print("EXTRACTION COMPLETE")
        print(f"Performance features: {performance_output}")
        print(f"Score features: {score_output}")
        print(f"Summary: {summary_file}")
        print("=" * 60)
        
        return summary

def main():
    """Example usage of the extraction layer"""
    
    # Use shared data directory that all layers can access
    audio_file = "../shared_data/processed/input_processed.wav"
    segments_file = "../shared_data/processed/input_audio_segments.json"
    score_file = "../shared_data/original/xml_score.musicxml"  # or .mid file
    score_json_file = "../shared_data/processed/input_music_features.json"
    
    # Initialize extraction layer
    extractor = ExtractionLayer()
    
    # Process all data
    try:
        summary = extractor.process_all(
            audio_file, segments_file, score_file, score_json_file)
        print("Extraction layer completed successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        print("Please ensure all input files exist:")
        print(f"  Audio: {audio_file}")
        print(f"  Segments: {segments_file}")
        print(f"  Score: {score_file}")
        print(f"  Score JSON: {score_json_file}")
        
    except Exception as e:
        print(f"Error during extraction: {e}")

if __name__ == "__main__":
    main()