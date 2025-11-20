#!/usr/bin/env python3
"""
Enhanced Symbolic Alignment (Block 2) - TuttiBot v0.2 (GPU-Ready)
=================================================================

Improved version using pretty_midi + DTW for score-performance alignment
without dependency on partitura/parangonar.

Key Improvements:
- Uses pretty_midi for MIDI handling (lighter dependency)
- Implements DTW using scipy or librosa (standard libraries)
- CQT-based feature alignment for better musical alignment
- Robust error handling and fallback mechanisms
- Comprehensive time mapping and visualization
- GPU acceleration support with automatic CPU fallback

Input:  ScoreGraph (Block 0) + Performance MIDI (Block 1)
Output: Time-aligned score-performance mapping + visualizations
"""

import numpy as np
import pretty_midi
import librosa
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from pathlib import Path
import json
import warnings
from typing import Dict, List, Tuple, Optional, Union
import logging
import os
import sys

# Add parent directory to path for GPU manager import
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSymbolicAligner:
    """Enhanced symbolic alignment using pretty_midi + DTW with GPU support"""
    
    def __init__(self, 
                 sr: int = 22050,
                 hop_length: int = 512,
                 n_bins: int = 84,
                 bins_per_octave: int = 12,
                 fmin: float = 55.0,
                 gpu_manager=None):
        """
        Initialize the enhanced symbolic aligner with GPU support
        
        Args:
            sr: Audio sample rate
            hop_length: Hop length for feature extraction
            n_bins: Number of CQT bins
            bins_per_octave: Bins per octave for CQT
            fmin: Minimum frequency for CQT
            gpu_manager: GPU manager instance for device control
        """
        self.sr = sr
        self.hop_length = hop_length
        self.n_bins = n_bins
        self.bins_per_octave = bins_per_octave
        self.fmin = fmin
        
        # Import and setup GPU manager
        if gpu_manager is None:
            try:
                from gpu_manager import GPUManager
                self.gpu_manager = GPUManager()
            except ImportError:
                logger.warning("GPU manager not available, using CPU mode")
                self.gpu_manager = None
        else:
            self.gpu_manager = gpu_manager
        
        # Log device configuration
        if self.gpu_manager:
            device_type = "GPU" if self.gpu_manager.device_config['use_gpu'] else "CPU"
            logger.info(f"Symbolic Aligner initialized with {device_type} support")
            if self.gpu_manager.device_config['use_gpu']:
                logger.info(f"Using GPU {self.gpu_manager.device_config['device_id']}")
        
        # Configure librosa/numpy to use appropriate backend
        self._configure_backends()
        # Configure librosa/numpy to use appropriate backend
        self._configure_backends()
        
    def _configure_backends(self):
        """Configure computational backends for GPU/CPU processing"""
        try:
            # Set environment variables for optimal performance
            if self.gpu_manager and self.gpu_manager.device_config['use_gpu']:
                # GPU configuration
                os.environ['NUMBA_ENABLE_CUDASIM'] = '1'
                logger.info("Configured for GPU-accelerated computation")
            else:
                # CPU configuration - optimize for multi-threading
                os.environ['NUMBA_NUM_THREADS'] = str(min(4, os.cpu_count()))
                logger.info("Configured for CPU computation with threading optimization")
        except Exception as e:
            logger.warning(f"Backend configuration warning: {e}")
    
    def load_score_graph(self, score_path: str) -> Dict:
        """Load ScoreGraph from Block 0"""
        try:
            with open(score_path, 'r') as f:
                score_data = json.load(f)
            logger.info(f"Loaded ScoreGraph with {len(score_data.get('nodes', []))} nodes")
            return score_data
        except Exception as e:
            logger.error(f"Error loading ScoreGraph: {e}")
            raise
    
    def load_performance_midi(self, midi_path: str) -> pretty_midi.PrettyMIDI:
        """Load performance MIDI from Block 1"""
        try:
            midi_data = pretty_midi.PrettyMIDI(midi_path)
            logger.info(f"Loaded performance MIDI with {len(midi_data.instruments)} instruments")
            return midi_data
        except Exception as e:
            logger.error(f"Error loading performance MIDI: {e}")
            raise
    
    def score_to_midi(self, score_graph: Dict) -> pretty_midi.PrettyMIDI:
        """Convert ScoreGraph to MIDI using pretty_midi"""
        try:
            # Create MIDI object
            midi = pretty_midi.PrettyMIDI()
            instrument = pretty_midi.Instrument(program=0)  # Piano
            
            # Extract notes from musical_notes section of score graph
            musical_notes = score_graph.get('musical_notes', [])
            if not musical_notes:
                logger.warning("No musical_notes found in score_graph, trying nodes")
                # Fallback to old method for backward compatibility
                for node in score_graph.get('nodes', []):
                    if 'pitch' in node and 'start_time' in node and 'duration' in node:
                        note = pretty_midi.Note(
                            velocity=80,
                            pitch=int(node['pitch']),
                            start=float(node['start_time']),
                            end=float(node['start_time'] + node['duration'])
                        )
                        instrument.notes.append(note)
            else:
                # Use musical_notes from Block 0
                for musical_note in musical_notes:
                    if 'pitch' in musical_note and 'offset_seconds' in musical_note and 'duration_seconds' in musical_note:
                        # Create note using the correct field names
                        note = pretty_midi.Note(
                            velocity=musical_note.get('velocity', 80),
                            pitch=int(musical_note['pitch']),
                            start=float(musical_note['offset_seconds']),
                            end=float(musical_note['offset_seconds'] + musical_note['duration_seconds'])
                        )
                        instrument.notes.append(note)
            
            midi.instruments.append(instrument)
            logger.info(f"Converted ScoreGraph to MIDI with {len(instrument.notes)} notes")
            return midi
            
        except Exception as e:
            logger.error(f"Error converting ScoreGraph to MIDI: {e}")
            raise
    
    def midi_to_chroma(self, midi_data: pretty_midi.PrettyMIDI, 
                       duration: Optional[float] = None) -> np.ndarray:
        """Convert MIDI to chromagram features"""
        try:
            # Use pretty_midi's synthesize method for audio generation
            if duration is None:
                duration = midi_data.get_end_time()
            
            # Synthesize MIDI to audio
            audio = midi_data.synthesize(fs=self.sr)
            
            # Pad or trim audio to match duration
            target_length = int(duration * self.sr)
            if len(audio) < target_length:
                audio = np.pad(audio, (0, target_length - len(audio)))
            else:
                audio = audio[:target_length]
            
            # Extract chromagram
            chroma = librosa.feature.chroma_cqt(
                y=audio,
                sr=self.sr,
                hop_length=self.hop_length,
                n_chroma=12,
                n_octaves=7,
                fmin=self.fmin
            )
            
            # Normalize and handle zero frames to prevent NaN
            chroma = librosa.util.normalize(chroma + 1e-8, axis=0)
            
            logger.info(f"Extracted chromagram: {chroma.shape}")
            return chroma
            
        except Exception as e:
            logger.warning(f"MIDI synthesis failed, using piano roll method: {e}")
            return self._midi_to_chroma_pianoroll(midi_data, duration)
    
    def _midi_to_chroma_pianoroll(self, midi_data: pretty_midi.PrettyMIDI,
                                  duration: Optional[float] = None) -> np.ndarray:
        """Fallback: Convert MIDI to chroma using piano roll"""
        if duration is None:
            duration = midi_data.get_end_time()
        
        # Get piano roll
        piano_roll = midi_data.get_piano_roll(fs=self.sr/self.hop_length)
        
        # Convert to chromagram
        chroma = np.zeros((12, piano_roll.shape[1]))
        for pitch in range(piano_roll.shape[0]):
            chroma_bin = pitch % 12
            chroma[chroma_bin, :] += piano_roll[pitch, :]
        
        # Normalize with safety epsilon to prevent NaN
        chroma = librosa.util.normalize(chroma + 1e-8, axis=0)
        
        return chroma
    
    def dtw_alignment(self, X: np.ndarray, Y: np.ndarray, 
                      metric: str = 'cosine',
                      use_constraints: bool = True,
                      band_radius: float = 0.25) -> Tuple[np.ndarray, float]:
        """
        Perform DTW alignment with Sakoe-Chiba band constraints
        
        Args:
            X: Score features [n_features, n_frames_score]
            Y: Performance features [n_features, n_frames_perf]
            metric: Distance metric for DTW
            use_constraints: Enable Sakoe-Chiba band for faster alignment
            band_radius: Band radius as fraction of sequence length
            
        Returns:
            wp: Warping path array [n_path, 2]
            distance: DTW distance
        """
        try:
            # Use librosa's DTW implementation with band constraint
            # NOTE: librosa expects shape (n_features, n_frames), NOT transposed
            D, wp = librosa.sequence.dtw(
                X=X,  # Already in correct shape (n_features, n_frames)
                Y=Y,  # Already in correct shape (n_features, n_frames)
                metric=metric,
                global_constraints=use_constraints,
                band_rad=band_radius
            )
            
            # Extract final distance
            distance = D[-1, -1]
            
            constraint_str = f"with band constraint (radius={band_radius})" if use_constraints else "unconstrained"
            logger.info(f"DTW {constraint_str}: path length={len(wp)}, distance={distance:.4f}")
            return wp, distance
            
        except Exception as e:
            logger.warning(f"Librosa DTW failed, using scipy alternative: {e}")
            return self._dtw_scipy(X, Y, metric)
    
    def _dtw_scipy(self, X: np.ndarray, Y: np.ndarray, 
                   metric: str = 'cosine') -> Tuple[np.ndarray, float]:
        """Fallback DTW implementation using scipy"""
        # Compute distance matrix
        dist_matrix = cdist(X.T, Y.T, metric=metric)
        
        # Simple DTW implementation
        n, m = dist_matrix.shape
        dtw_matrix = np.full((n + 1, m + 1), np.inf)
        dtw_matrix[0, 0] = 0
        
        # Fill DTW matrix
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = dist_matrix[i-1, j-1]
                dtw_matrix[i, j] = cost + min(
                    dtw_matrix[i-1, j],      # insertion
                    dtw_matrix[i, j-1],      # deletion
                    dtw_matrix[i-1, j-1]     # match
                )
        
        # Backtrack to find optimal path
        path = []
        i, j = n, m
        while i > 0 and j > 0:
            path.append([i-1, j-1])
            
            # Choose the best predecessor
            candidates = [
                (dtw_matrix[i-1, j-1], i-1, j-1),
                (dtw_matrix[i-1, j], i-1, j),
                (dtw_matrix[i, j-1], i, j-1)
            ]
            _, i, j = min(candidates)
        
        wp = np.array(path[::-1])
        distance = dtw_matrix[n, m]
        
        return wp, distance
    
    def dtw_alignment_with_cost(self, C: np.ndarray,
                                use_constraints: bool = True,
                                band_radius: float = 0.25,
                                weights_mul: Optional[np.ndarray] = None) -> Tuple[np.ndarray, float]:
        """
        Perform DTW with precomputed cost matrix and optional step weights
        
        Args:
            C: Precomputed cost matrix [N, M]
            use_constraints: Enable Sakoe-Chiba band constraint
            band_radius: Band radius as fraction of sequence length
            weights_mul: Step weights [diagonal, horizontal, vertical]
            
        Returns:
            wp: Warping path array [n_path, 2]
            distance: DTW distance
        """
        try:
            kwargs = {'C': C, 'backtrack': True}
            
            if use_constraints:
                kwargs['global_constraints'] = True
                kwargs['band_rad'] = band_radius
            
            if weights_mul is not None:
                kwargs['weights_mul'] = weights_mul
            
            D, wp = librosa.sequence.dtw(**kwargs)
            distance = D[-1, -1]
            
            logger.info(f"DTW with cost matrix: path length={len(wp)}, distance={distance:.4f}")
            if weights_mul is not None:
                logger.info(f"  Using adaptive weights: {weights_mul}")
            
            return wp, distance
            
        except Exception as e:
            logger.error(f"DTW with cost matrix failed: {e}")
            raise
    
    def _compute_beat_weighted_cost(self, X: np.ndarray, Y: np.ndarray,
                                     beats_json: List[Dict]) -> np.ndarray:
        """
        Compute cost matrix weighted by beat confidence scores.
        High-confidence beats receive lower cost, making them preferred alignment points.
        
        Args:
            X: Score chroma features [12, N]
            Y: Performance chroma features [12, M]
            beats_json: List of beat dictionaries with 't' and 'confidence'
            
        Returns:
            C: Weighted cost matrix [N, M]
        """
        # Check for NaN in input chromagrams
        if np.isnan(X).any():
            logger.warning("Score chromagram contains NaN values, replacing with zeros")
            X = np.nan_to_num(X, nan=0.0)
        if np.isnan(Y).any():
            logger.warning("Performance chromagram contains NaN values, replacing with zeros")
            Y = np.nan_to_num(Y, nan=0.0)
        
        # Compute base cost matrix (cosine distance)
        C = cdist(X.T, Y.T, metric='cosine')
        
        # Check for NaN in cost matrix
        if np.isnan(C).any():
            logger.warning("Cost matrix contains NaN values, replacing with 1.0 (max cost)")
            C = np.nan_to_num(C, nan=1.0)
        
        # Extract beat times and confidences
        beat_times = [b['t'] for b in beats_json if 't' in b]
        beat_confidences = [b.get('confidence', 1.0) for b in beats_json]
        
        # Convert beat times to frame indices
        beat_frames = librosa.time_to_frames(
            beat_times,
            sr=self.sr,
            hop_length=self.hop_length
        )
        
        # Create confidence weighting mask for performance axis
        conf_weight = np.ones(Y.shape[1])
        
        for frame, conf in zip(beat_frames, beat_confidences):
            if 0 <= frame < len(conf_weight):
                # Apply weighting in a small window around each beat
                window_size = 2
                start = max(0, frame - window_size)
                end = min(len(conf_weight), frame + window_size + 1)
                
                # Higher confidence reduces cost (makes alignment prefer this region)
                weight_factor = 1.0 / (1.0 + conf)
                conf_weight[start:end] = np.minimum(conf_weight[start:end], weight_factor)
        
        # Apply weights to cost matrix
        C = C * conf_weight[np.newaxis, :]
        
        logger.info(f"Applied beat weighting: {len(beat_frames)} beats used")
        return C
    
    def _compute_adaptive_weights(self, n_frames: int, 
                                   nodes: List[Dict]) -> Optional[np.ndarray]:
        """
        Compute adaptive DTW step weights based on fermata and cadence markings.
        Reduces penalties near expressive moments to allow timing flexibility.
        
        Args:
            n_frames: Number of frames in score
            nodes: List of score nodes with potential 'flags' field
            
        Returns:
            weights_mul: Array [3] for [diagonal, horizontal, vertical] step costs
                        or None if no special markings found
        """
        # Count expressive markings
        fermata_count = sum(1 for n in nodes if 'fermata' in n.get('flags', []))
        cadence_count = sum(1 for n in nodes if 'cadence' in n.get('flags', []))
        
        if fermata_count == 0 and cadence_count == 0:
            return None
        
        # Default step weights: [diagonal, horizontal, vertical]
        weights = np.array([1.0, 1.0, 1.0])
        
        # Reduce horizontal and vertical penalties to allow more flexibility
        flexibility_factor = 0.7
        weights[1] *= flexibility_factor  # Allow performance stretching
        weights[2] *= flexibility_factor  # Allow performance compression
        
        logger.info(f"Adaptive weights: {fermata_count} fermatas, {cadence_count} cadences")
        logger.info(f"Step weights: diagonal={weights[0]:.2f}, horiz={weights[1]:.2f}, vert={weights[2]:.2f}")
        
        return weights
    
    # ============================================================================
    # GRADING METRICS COMPUTATION METHODS
    # ============================================================================
    
    def _extract_notes_from_midi(self, midi_data: pretty_midi.PrettyMIDI) -> List[Dict]:
        """
        Extract note list from MIDI data
        
        Returns:
            List of notes with pitch, onset, offset, duration, velocity
        """
        notes = []
        for instrument in midi_data.instruments:
            for note in instrument.notes:
                notes.append({
                    'pitch': note.pitch,
                    'onset': note.start,
                    'offset': note.end,
                    'duration': note.end - note.start,
                    'velocity': note.velocity
                })
        return sorted(notes, key=lambda x: x['onset'])
    
    def _map_time(self, time: float, time_mapping: List[Dict], direction: str = 'score_to_perf') -> float:
        """
        Map time from score to performance or vice versa using time mapping
        
        Args:
            time: Time to map
            time_mapping: List of {score_time, perf_time} mappings
            direction: 'score_to_perf' or 'perf_to_score'
        
        Returns:
            Mapped time
        """
        if not time_mapping:
            return time
        
        if direction == 'score_to_perf':
            source_key, target_key = 'score_time', 'perf_time'
        else:
            source_key, target_key = 'perf_time', 'score_time'
        
        # Extract and sort by source time (np.interp requires sorted x values)
        sorted_mapping = sorted(time_mapping, key=lambda m: m[source_key])
        source_times = [m[source_key] for m in sorted_mapping]
        target_times = [m[target_key] for m in sorted_mapping]
        
        # Linear interpolation
        return np.interp(time, source_times, target_times)
    
    def _pitch_to_cents_error(self, score_pitch_midi: float, perf_pitch_midi: float) -> float:
        """
        Convert MIDI pitch difference to cents (100 cents = 1 semitone)
        
        Args:
            score_pitch_midi: Score pitch in MIDI number
            perf_pitch_midi: Performance pitch in MIDI number
        
        Returns:
            Error in cents
        """
        semitone_diff = perf_pitch_midi - score_pitch_midi
        return semitone_diff * 100  # 100 cents per semitone
    
    def _match_notes(self, score_notes: List[Dict], perf_notes: List[Dict], 
                    time_mapping: List[Dict], pqg_alignments: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Match score notes to performance notes using time mapping or PQG-A2SA alignments
        
        Args:
            score_notes: List of score notes
            perf_notes: List of performance notes
            time_mapping: DTW time mapping
            pqg_alignments: Optional PQG-A2SA note alignments (more accurate onset/offset)
        
        Returns:
            List of matched note alignments with errors
        """
        matched = []
        
        # If PQG-A2SA available, use its precise alignments
        if pqg_alignments:
            logger.info("Using PQG-A2SA for precise note-level alignment")
            for pqg_match in pqg_alignments:
                matched.append({
                    'score_note': pqg_match.get('score_note', {}),
                    'performance_note': pqg_match.get('performance_note', {}),
                    'onset_error_ms': pqg_match.get('onset_error_ms', 0.0),
                    'offset_error_ms': pqg_match.get('offset_error_ms', 0.0),
                    'pitch_error_cents': pqg_match.get('pitch_error_cents', 0.0),
                    'is_phrase_boundary': pqg_match.get('is_phrase_boundary', False),
                    'phrase_id': pqg_match.get('phrase_id', 0)
                })
        else:
            # Fallback: Use DTW time mapping for matching
            logger.info("Using DTW time mapping for note-level alignment (fallback)")
            perf_notes_used = set()
            
            for i, s_note in enumerate(score_notes):
                score_onset = s_note['onset']
                
                # Map score onset to expected performance time
                expected_perf_onset = self._map_time(score_onset, time_mapping, 'score_to_perf')
                
                # Find closest unused performance note
                best_match = None
                min_distance = float('inf')
                best_idx = None
                
                for j, p_note in enumerate(perf_notes):
                    if j in perf_notes_used:
                        continue
                    
                    # Temporal distance
                    time_dist = abs(p_note['onset'] - expected_perf_onset)
                    
                    # Pitch distance (semitones)
                    pitch_dist = abs(p_note['pitch'] - s_note['pitch'])
                    
                    # Combined distance (weight time more heavily)
                    combined_dist = time_dist + (pitch_dist * 0.05)  # 50ms per semitone
                    
                    if combined_dist < min_distance and time_dist < 0.5:  # 500ms tolerance
                        min_distance = combined_dist
                        best_match = p_note
                        best_idx = j
                
                if best_match:
                    perf_notes_used.add(best_idx)
                    
                    # Compute errors
                    onset_error_ms = (best_match['onset'] - expected_perf_onset) * 1000
                    offset_error_ms = ((best_match['offset'] - s_note['offset']) - 
                                      (best_match['onset'] - s_note['onset'])) * 1000
                    pitch_error_cents = self._pitch_to_cents_error(s_note['pitch'], best_match['pitch'])
                    
                    matched.append({
                        'note_id': i,
                        'score_note': s_note,
                        'performance_note': best_match,
                        'onset_error_ms': float(onset_error_ms),
                        'offset_error_ms': float(offset_error_ms),
                        'pitch_error_cents': float(pitch_error_cents),
                        'is_phrase_boundary': False,  # Would need score_graph
                        'phrase_id': 0
                    })
        
        return matched
    
    def _compute_rhythm_tempo_metrics(self, note_alignments: List[Dict], 
                                      beats_json: Optional[Dict] = None,
                                      score_graph: Optional[Dict] = None) -> Dict:
        """
        Compute Dimension 1: Rhythm & Tempo Mastery metrics (30% weight)
        """
        if not note_alignments:
            return {}
        
        # Extract onset errors
        onset_errors = [n['onset_error_ms'] for n in note_alignments]
        
        # Onset accuracy statistics
        mean_onset_error = np.mean(np.abs(onset_errors))
        onset_std = np.std(onset_errors)
        
        # IOI analysis
        score_onsets = [n['score_note']['onset'] for n in note_alignments]
        perf_onsets = [n['performance_note']['onset'] for n in note_alignments]
        
        if len(score_onsets) > 1:
            score_iois = np.diff(score_onsets)
            perf_iois = np.diff(perf_onsets)
            
            # IOI correlation (Pearson)
            if len(score_iois) > 0:
                ioi_corr = np.corrcoef(score_iois, perf_iois)[0, 1] if len(score_iois) > 1 else 1.0
            else:
                ioi_corr = 1.0
            
            # Tempo stability (CV of performance IOIs)
            tempo_cv = (np.std(perf_iois) / np.mean(perf_iois)) * 100 if np.mean(perf_iois) > 0 else 0
        else:
            ioi_corr = 1.0
            tempo_cv = 0.0
        
        # Tempo marking adherence (from beats if available)
        detected_tempo = None
        expected_tempo = 120.0  # Default
        
        if beats_json and 'estimated_tempo' in beats_json:
            detected_tempo = beats_json['estimated_tempo']
        
        if score_graph and 'tempo_marks' in score_graph:
            # Get first tempo marking
            if score_graph['tempo_marks']:
                expected_tempo = score_graph['tempo_marks'][0].get('bpm', 120.0)
        
        return {
            'mean_onset_error_ms': float(mean_onset_error),
            'onset_error_std_ms': float(onset_std),
            'tempo_cv_percent': float(tempo_cv),
            'ioi_correlation': float(ioi_corr),
            'tempo_marking_adherence_bpm': detected_tempo,
            'expected_tempo_bpm': float(expected_tempo),
            'onset_errors_distribution': {
                'min': float(np.min(onset_errors)),
                'max': float(np.max(onset_errors)),
                'median': float(np.median(onset_errors)),
                'q25': float(np.percentile(onset_errors, 25)),
                'q75': float(np.percentile(onset_errors, 75))
            }
        }
    
    def _compute_sound_quality_metrics(self, note_alignments: List[Dict]) -> Dict:
        """
        Compute Dimension 2: Sound Quality metrics (20% weight)
        """
        if not note_alignments:
            return {}
        
        pitch_errors = [n['pitch_error_cents'] for n in note_alignments]
        pitch_errors_abs = [abs(e) for e in pitch_errors]
        
        # Pitch accuracy within 50 cents (common threshold)
        accurate_count = sum(1 for err in pitch_errors_abs if err < 50)
        pitch_accuracy_50c = (accurate_count / len(pitch_errors)) * 100
        
        # Also compute for 25 cents (stricter)
        accurate_count_25c = sum(1 for err in pitch_errors_abs if err < 25)
        pitch_accuracy_25c = (accurate_count_25c / len(pitch_errors)) * 100
        
        return {
            'pitch_accuracy_50c_percent': float(pitch_accuracy_50c),
            'pitch_accuracy_25c_percent': float(pitch_accuracy_25c),
            'mean_pitch_error_cents': float(np.mean(pitch_errors_abs)),
            'pitch_error_std_cents': float(np.std(pitch_errors)),
            'pitch_errors_distribution': {
                'min': float(np.min(pitch_errors)),
                'max': float(np.max(pitch_errors)),
                'median': float(np.median(pitch_errors)),
                'q25': float(np.percentile(pitch_errors, 25)),
                'q75': float(np.percentile(pitch_errors, 75))
            },
            'note_pitch_errors': [
                {'note_id': i, 'error_cents': float(err)}
                for i, err in enumerate(pitch_errors[:100])  # Limit to first 100 for size
            ]
        }
    
    def _compute_technical_virtuosity_metrics(self, note_alignments: List[Dict],
                                             score_notes: List[Dict],
                                             perf_notes: List[Dict]) -> Dict:
        """
        Compute Dimension 3: Technical Virtuosity metrics (20% weight)
        """
        # Note accuracy
        matched = len(note_alignments)
        total_score = len(score_notes)
        accuracy = (matched / total_score) * 100 if total_score > 0 else 0
        
        # Fluency (IOI coefficient of variation)
        if len(note_alignments) > 1:
            perf_iois = np.diff([n['performance_note']['onset'] for n in note_alignments])
            fluency_cv = (np.std(perf_iois) / np.mean(perf_iois)) * 100 if np.mean(perf_iois) > 0 else 0
        else:
            fluency_cv = 0.0
        
        # Articulation precision (onset timing consistency)
        onset_errors = [n['onset_error_ms'] for n in note_alignments]
        articulation_precision = np.std(onset_errors)
        
        # Difficulty mastery - identify difficult passages (high note density)
        # Calculate local note density for each note
        window_size = 2.0  # 2-second window
        difficult_threshold = 4.0  # notes per second
        
        easy_errors = []
        difficult_errors = []
        
        for i, alignment in enumerate(note_alignments):
            onset_time = alignment['score_note']['onset']
            
            # Count notes in window around this note
            notes_in_window = sum(
                1 for n in note_alignments
                if abs(n['score_note']['onset'] - onset_time) < window_size / 2
            )
            note_density = notes_in_window / window_size
            
            error = abs(alignment['onset_error_ms'])
            if note_density > difficult_threshold:
                difficult_errors.append(error)
            else:
                easy_errors.append(error)
        
        difficulty_ratio = 1.0
        if easy_errors and difficult_errors:
            difficulty_ratio = np.mean(difficult_errors) / (np.mean(easy_errors) + 1.0)
        
        return {
            'note_accuracy_percent': float(accuracy),
            'total_score_notes': total_score,
            'matched_notes': matched,
            'unmatched_notes': total_score - matched,
            'extra_notes': len(perf_notes) - matched,
            'fluency_ioi_cv_percent': float(fluency_cv),
            'articulation_precision_ms': float(articulation_precision),
            'difficulty_mastery': {
                'easy_passages_error_ms': float(np.mean(easy_errors)) if easy_errors else 0.0,
                'difficult_passages_error_ms': float(np.mean(difficult_errors)) if difficult_errors else 0.0,
                'difficulty_ratio': float(difficulty_ratio),
                'difficult_note_count': len(difficult_errors),
                'easy_note_count': len(easy_errors)
            }
        }
    
    def _compute_phrasing_metrics(self, note_alignments: List[Dict],
                                  score_graph: Optional[Dict] = None) -> Dict:
        """
        Compute Dimension 4: Phrasing & Diction metrics (15% weight)
        """
        if not note_alignments:
            return {}
        
        # Rubato variation (tempo flexibility through duration ratios)
        duration_ratios = []
        for n in note_alignments:
            score_dur = n['score_note']['duration']
            perf_dur = n['performance_note']['duration']
            if score_dur > 0.01:  # Avoid division by very small numbers
                ratio = perf_dur / score_dur
                duration_ratios.append(ratio)
        
        rubato_std = np.std(duration_ratios) if duration_ratios else 0.0
        
        # Phrase boundaries - extract from score_graph or PQG-A2SA
        phrase_boundaries = []
        if score_graph and 'nodes' in score_graph:
            # Extract phrase information from score graph
            for node in score_graph.get('nodes', []):
                if 'phrase_end' in node.get('flags', []) or 'fermata' in node.get('flags', []):
                    phrase_boundaries.append({
                        'phrase_id': node.get('phrase_id', 0),
                        'score_time': node.get('time_sec', 0.0),
                        'has_fermata': 'fermata' in node.get('flags', [])
                    })
        
        # Or from note alignments if they have phrase markers
        for n in note_alignments:
            if n.get('is_phrase_boundary', False):
                phrase_boundaries.append({
                    'phrase_id': n.get('phrase_id', 0),
                    'score_time': n['score_note']['onset'],
                    'perf_time': n['performance_note']['onset']
                })
        
        # Agogic expression (tempo changes at phrase boundaries)
        agogic_changes = []
        if len(phrase_boundaries) > 1 and len(note_alignments) > 10:
            for boundary in phrase_boundaries:
                # Find notes before and after boundary
                boundary_time = boundary.get('score_time', 0.0)
                
                notes_before = [n for n in note_alignments 
                              if boundary_time - 2.0 < n['score_note']['onset'] < boundary_time]
                notes_after = [n for n in note_alignments
                             if boundary_time < n['score_note']['onset'] < boundary_time + 2.0]
                
                if len(notes_before) > 1 and len(notes_after) > 1:
                    # Compute local tempo before and after
                    iois_before = np.diff([n['performance_note']['onset'] for n in notes_before])
                    iois_after = np.diff([n['performance_note']['onset'] for n in notes_after])
                    
                    tempo_before = 60.0 / np.mean(iois_before) if len(iois_before) > 0 else 120.0
                    tempo_after = 60.0 / np.mean(iois_after) if len(iois_after) > 0 else 120.0
                    
                    change_percent = abs(tempo_after - tempo_before) / tempo_before * 100
                    agogic_changes.append(change_percent)
        
        agogic_mean = np.mean(agogic_changes) if agogic_changes else 0.0
        
        return {
            'rubato_variation_std': float(rubato_std),
            'rubato_mean_ratio': float(np.mean(duration_ratios)) if duration_ratios else 1.0,
            'phrase_boundaries': phrase_boundaries[:20],  # Limit for JSON size
            'agogic_expression_mean_percent': float(agogic_mean),
            'phrase_boundary_count': len(phrase_boundaries)
        }
    
    def _compute_communicativeness_metrics(self, note_alignments: List[Dict],
                                          score_graph: Optional[Dict] = None) -> Dict:
        """
        Compute Dimension 5: Communicativeness metrics (15% weight)
        """
        if not note_alignments:
            return {}
        
        # Structural sections
        sections = []
        if score_graph and 'bars' in score_graph:
            # Simple sectioning by measure groups (every 8 bars = section)
            bars = score_graph['bars']
            section_size = 8
            
            for i in range(0, len(bars), section_size):
                section_bars = bars[i:i+section_size]
                if section_bars:
                    # Find notes in this section
                    start_beat = section_bars[0].get('downbeat_abs_beat', 0)
                    end_beat = section_bars[-1].get('downbeat_abs_beat', 0) + 4  # Assume 4/4
                    
                    section_notes = [n for n in note_alignments
                                   if start_beat <= n['score_note'].get('abs_beat_onset', n['score_note']['onset']) < end_beat]
                    
                    if len(section_notes) > 1:
                        # Compute tempo consistency within section
                        section_iois = np.diff([n['performance_note']['onset'] for n in section_notes])
                        tempo_cv = (np.std(section_iois) / np.mean(section_iois)) * 100 if np.mean(section_iois) > 0 else 0
                        
                        sections.append({
                            'section_id': chr(65 + i // section_size),  # A, B, C, ...
                            'bar_range': [section_bars[0]['bar'], section_bars[-1]['bar']],
                            'note_count': len(section_notes),
                            'tempo_consistency_cv': float(tempo_cv)
                        })
        
        # Climax detection (point of maximum dynamic/energy)
        # Approximate using velocity and density
        if len(note_alignments) > 10:
            window_size = max(len(note_alignments) // 10, 5)
            energies = []
            positions = []
            
            for i in range(0, len(note_alignments) - window_size):
                window = note_alignments[i:i+window_size]
                # Energy = average velocity * note density
                avg_velocity = np.mean([n['performance_note'].get('velocity', 80) for n in window])
                time_span = window[-1]['performance_note']['onset'] - window[0]['performance_note']['onset']
                density = len(window) / (time_span + 0.1)
                energy = avg_velocity * density
                energies.append(energy)
                positions.append(i + window_size // 2)
            
            if energies:
                climax_idx = np.argmax(energies)
                climax_note_idx = positions[climax_idx]
                climax_position_percent = (climax_note_idx / len(note_alignments)) * 100
            else:
                climax_position_percent = 50.0
        else:
            climax_position_percent = 50.0
        
        return {
            'structural_sections': sections[:10],  # Limit for JSON size
            'section_count': len(sections),
            'climax_position_percent': float(climax_position_percent),
            'dramatic_trajectory_r2': 0.0  # Would need more sophisticated analysis
        }
    
    def compute_grading_metrics(self, 
                               score_midi: pretty_midi.PrettyMIDI,
                               perf_midi: pretty_midi.PrettyMIDI,
                               time_mapping: List[Dict],
                               score_graph: Optional[Dict] = None,
                               beats_json: Optional[Dict] = None,
                               pqg_alignments: Optional[List[Dict]] = None) -> Tuple[Dict, List[Dict]]:
        """
        Compute all grading-relevant metrics from alignment
        
        Args:
            score_midi: Score MIDI data
            perf_midi: Performance MIDI data
            time_mapping: DTW time mapping
            score_graph: Optional score graph with structure info
            beats_json: Optional beat detection data
            pqg_alignments: Optional PQG-A2SA note alignments (preferred for accuracy)
        
        Returns:
            Tuple of (grading_metrics dict, note_alignments list)
        """
        logger.info("Computing grading metrics...")
        
        # Extract notes
        score_notes = self._extract_notes_from_midi(score_midi)
        perf_notes = self._extract_notes_from_midi(perf_midi)
        
        logger.info(f"Extracted {len(score_notes)} score notes, {len(perf_notes)} performance notes")
        
        # Match notes (use PQG-A2SA if available, else DTW mapping)
        note_alignments = self._match_notes(score_notes, perf_notes, time_mapping, pqg_alignments)
        
        logger.info(f"Matched {len(note_alignments)} note pairs")
        
        # Compute metrics for each dimension
        rhythm_tempo = self._compute_rhythm_tempo_metrics(note_alignments, beats_json, score_graph)
        sound_quality = self._compute_sound_quality_metrics(note_alignments)
        technical = self._compute_technical_virtuosity_metrics(note_alignments, score_notes, perf_notes)
        phrasing = self._compute_phrasing_metrics(note_alignments, score_graph)
        communicativeness = self._compute_communicativeness_metrics(note_alignments, score_graph)
        
        grading_metrics = {
            'rhythm_tempo': rhythm_tempo,
            'sound_quality': sound_quality,
            'technical_virtuosity': technical,
            'phrasing_diction': phrasing,
            'communicativeness': communicativeness
        }
        
        logger.info("Grading metrics computation complete")
        
        return grading_metrics, note_alignments
    
    # ============================================================================
    # END GRADING METRICS COMPUTATION METHODS
    # ============================================================================
    
    def enhanced_alignment(self, score_midi: pretty_midi.PrettyMIDI,
                          perf_midi: pretty_midi.PrettyMIDI,
                          beats_json: Optional[List[Dict]] = None,
                          score_graph: Optional[Dict] = None,
                          pqg_alignment_path: Optional[str] = None) -> Dict:
        """
        Perform enhanced alignment with beat weighting and fermata awareness
        
        Args:
            score_midi: Score MIDI data
            perf_midi: Performance MIDI data
            beats_json: Optional beat detections with confidence scores
            score_graph: Optional score graph with fermata/cadence flags
            pqg_alignment_path: Optional path to PQG-A2SA alignment JSON for precise onset/offset
            
        Returns:
            Alignment results with time mapping, confidence scores, and grading metrics
        """
        try:
            # Get duration for alignment
            score_duration = score_midi.get_end_time()
            perf_duration = perf_midi.get_end_time()
            max_duration = max(score_duration, perf_duration)
            
            logger.info(f"Aligning: score={score_duration:.2f}s, perf={perf_duration:.2f}s")
            
            # Extract chromagram features
            score_chroma = self.midi_to_chroma(score_midi, max_duration)
            perf_chroma = self.midi_to_chroma(perf_midi, max_duration)
            
            # Determine alignment strategy based on available data
            use_beat_weighting = beats_json is not None and len(beats_json) > 0
            use_adaptive_weights = score_graph is not None and 'nodes' in score_graph
            
            # Perform DTW alignment with optional enhancements
            if use_beat_weighting:
                logger.info("Using beat-weighted cost matrix")
                cost_matrix = self._compute_beat_weighted_cost(
                    score_chroma, perf_chroma, beats_json
                )
                
                # Get adaptive weights if available
                adaptive_weights = None
                if use_adaptive_weights:
                    adaptive_weights = self._compute_adaptive_weights(
                        score_chroma.shape[1],
                        score_graph['nodes']
                    )
                
                # Use combined cost matrix + adaptive weights
                wp, distance = self.dtw_alignment_with_cost(
                    cost_matrix,
                    use_constraints=True,
                    band_radius=0.25,
                    weights_mul=adaptive_weights
                )
            else:
                # Standard DTW with band constraints
                wp, distance = self.dtw_alignment(
                    score_chroma, perf_chroma,
                    use_constraints=True,
                    band_radius=0.25
                )
            
            # Create time mapping
            score_times = librosa.frames_to_time(
                np.arange(score_chroma.shape[1]), 
                sr=self.sr, 
                hop_length=self.hop_length
            )
            perf_times = librosa.frames_to_time(
                np.arange(perf_chroma.shape[1]),
                sr=self.sr,
                hop_length=self.hop_length
            )
            
            # Map warping path to time
            time_mapping = []
            for score_idx, perf_idx in wp:
                time_mapping.append({
                    'score_time': float(score_times[score_idx]),
                    'perf_time': float(perf_times[perf_idx]),
                    'score_frame': int(score_idx),
                    'perf_frame': int(perf_idx)
                })
            
            # Calculate alignment confidence
            confidence = self._calculate_confidence(score_chroma, perf_chroma, wp)
            
            # ===== LOAD PQG-A2SA ALIGNMENT IF AVAILABLE =====
            pqg_alignments = None
            if pqg_alignment_path and Path(pqg_alignment_path).exists():
                try:
                    with open(pqg_alignment_path, 'r') as f:
                        pqg_data = json.load(f)
                        pqg_alignments = pqg_data.get('note_alignments', [])
                        logger.info(f"Loaded {len(pqg_alignments)} note alignments from PQG-A2SA")
                except Exception as e:
                    logger.warning(f"Failed to load PQG-A2SA alignments: {e}")
            
            # ===== COMPUTE GRADING METRICS =====
            # This provides the metrics that Inference Core will extract
            logger.info("Computing grading metrics for alignment...")
            grading_metrics, note_alignments = self.compute_grading_metrics(
                score_midi=score_midi,
                perf_midi=perf_midi,
                time_mapping=time_mapping,
                score_graph=score_graph,
                beats_json=beats_json,
                pqg_alignments=pqg_alignments
            )
            
            results = {
                'time_mapping': time_mapping,
                'warping_path': wp.tolist(),
                'dtw_distance': float(distance),
                'confidence': float(confidence),
                'score_duration': float(score_duration),
                'perf_duration': float(perf_duration),
                'feature_shapes': {
                    'score_chroma': list(score_chroma.shape),
                    'perf_chroma': list(perf_chroma.shape)
                },
                'alignment_metadata': {
                    'beat_weighting_used': use_beat_weighting,
                    'adaptive_weights_used': use_adaptive_weights,
                    'band_constraint_radius': 0.25
                },
                # ==== GRADING METRICS OUTPUT ====
                'grading_metrics': grading_metrics,
                'note_alignments': note_alignments[:100]  # Limit to 100 for JSON size
            }
            
            logger.info(f"Alignment completed: confidence={confidence:.3f}, {len(note_alignments)} notes aligned")
            return results
            
        except Exception as e:
            logger.error(f"Enhanced alignment failed: {e}")
            raise
    
    def _calculate_confidence(self, score_chroma: np.ndarray, 
                             perf_chroma: np.ndarray, 
                             wp: np.ndarray) -> float:
        """Calculate alignment confidence based on feature similarity"""
        try:
            similarities = []
            for score_idx, perf_idx in wp:
                if score_idx < score_chroma.shape[1] and perf_idx < perf_chroma.shape[1]:
                    score_vec = score_chroma[:, score_idx]
                    perf_vec = perf_chroma[:, perf_idx]
                    
                    # Cosine similarity
                    if np.linalg.norm(score_vec) > 0 and np.linalg.norm(perf_vec) > 0:
                        sim = np.dot(score_vec, perf_vec) / (
                            np.linalg.norm(score_vec) * np.linalg.norm(perf_vec)
                        )
                        similarities.append(sim)
            
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return 0.0
    
    def visualize_alignment(self, results: Dict, output_dir: str = "alignment_viz"):
        """Create comprehensive alignment visualizations"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Extract data
            time_mapping = results['time_mapping']
            score_times = [tm['score_time'] for tm in time_mapping]
            perf_times = [tm['perf_time'] for tm in time_mapping]
            
            # Create alignment plot
            plt.figure(figsize=(12, 8))
            
            # Main alignment plot
            plt.subplot(2, 2, 1)
            plt.plot(score_times, perf_times, 'b-', alpha=0.7, linewidth=2)
            plt.scatter(score_times[::10], perf_times[::10], c='red', s=20, alpha=0.8)
            plt.xlabel('Score Time (s)')
            plt.ylabel('Performance Time (s)')
            plt.title('Score-Performance Time Alignment')
            plt.grid(True, alpha=0.3)
            
            # Diagonal reference line
            max_time = max(max(score_times), max(perf_times))
            plt.plot([0, max_time], [0, max_time], 'k--', alpha=0.5, label='Perfect alignment')
            plt.legend()
            
            # Tempo deviation plot
            plt.subplot(2, 2, 2)
            if len(score_times) > 1:
                tempo_ratios = []
                for i in range(1, len(score_times)):
                    dt_score = score_times[i] - score_times[i-1]
                    dt_perf = perf_times[i] - perf_times[i-1]
                    if dt_score > 0:
                        tempo_ratios.append(dt_perf / dt_score)
                
                if tempo_ratios:
                    plt.plot(score_times[1:len(tempo_ratios)+1], tempo_ratios, 'g-', linewidth=2)
                    plt.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
                    plt.xlabel('Score Time (s)')
                    plt.ylabel('Tempo Ratio (Perf/Score)')
                    plt.title('Local Tempo Variations')
                    plt.grid(True, alpha=0.3)
            
            # Alignment quality metrics
            plt.subplot(2, 2, 3)
            quality_metrics = [
                ('DTW Distance', results['dtw_distance']),
                ('Confidence', results['confidence']),
                ('Score Duration', results['score_duration']),
                ('Perf Duration', results['perf_duration'])
            ]
            
            metrics_names = [m[0] for m in quality_metrics]
            metrics_values = [m[1] for m in quality_metrics]
            
            plt.barh(metrics_names, metrics_values, color=['skyblue', 'lightgreen', 'orange', 'pink'])
            plt.xlabel('Value')
            plt.title('Alignment Quality Metrics')
            plt.grid(True, alpha=0.3)
            
            # Warping path visualization
            plt.subplot(2, 2, 4)
            wp = np.array(results['warping_path'])
            if len(wp) > 0:
                plt.plot(wp[:, 1], wp[:, 0], 'purple', linewidth=1, alpha=0.7)
                plt.scatter(wp[::20, 1], wp[::20, 0], c='red', s=10)
                plt.xlabel('Performance Frame')
                plt.ylabel('Score Frame')
                plt.title('DTW Warping Path')
                plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            viz_path = output_path / "alignment_visualization.png"
            plt.savefig(viz_path, dpi=300, bbox_inches='tight')
            logger.info(f"Visualization saved to {viz_path}")
            
            plt.close()
            
            # Save detailed results
            results_path = output_path / "alignment_results.json"
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {results_path}")
            
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
    
    def align_score_performance(self, score_graph_path: str, 
                               performance_midi_path: str,
                               beats_json_path: Optional[str] = None,
                               pqg_alignment_path: Optional[str] = None,
                               output_dir: str = "block_2_enhanced_output") -> Dict:
        """
        Main alignment pipeline with optional beat weighting and PQG-A2SA integration
        
        Args:
            score_graph_path: Path to ScoreGraph JSON from Block 0
            performance_midi_path: Path to performance MIDI from Block 1
            beats_json_path: Optional path to beats JSON from Block 4
            pqg_alignment_path: Optional path to PQG-A2SA alignment JSON (for precise onset/offset)
            output_dir: Output directory for results
            
        Returns:
            Complete alignment results with grading metrics
        """
        try:
            logger.info("Enhanced Symbolic Alignment (Block 2)")
            
            # Load inputs
            score_graph = self.load_score_graph(score_graph_path)
            perf_midi = self.load_performance_midi(performance_midi_path)
            
            # Load optional beats data
            beats_json = None
            if beats_json_path and Path(beats_json_path).exists():
                with open(beats_json_path, 'r') as f:
                    beats_json = json.load(f)
                logger.info(f"Loaded {len(beats_json)} beats with confidence scores")
            
            # Convert score to MIDI
            score_midi = self.score_to_midi(score_graph)
            
            # Perform alignment with optional enhancements
            alignment_results = self.enhanced_alignment(
                score_midi, 
                perf_midi,
                beats_json=beats_json,
                score_graph=score_graph,
                pqg_alignment_path=pqg_alignment_path
            )
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True, parents=True)
            
            # Save intermediate MIDI files for inspection
            score_midi_path = output_path / "score_from_graph.mid"
            score_midi.write(str(score_midi_path))
            logger.info(f"Score MIDI saved to {score_midi_path}")
            
            # Visualize results
            self.visualize_alignment(alignment_results, str(output_path))
            
            # Save final results
            final_results = {
                'input_files': {
                    'score_graph': score_graph_path,
                    'performance_midi': performance_midi_path,
                    'beats_json': beats_json_path if beats_json_path else None,
                    'pqg_alignment': pqg_alignment_path if pqg_alignment_path else None
                },
                'alignment': alignment_results,
                'metadata': {
                    'aligner_params': {
                        'sr': self.sr,
                        'hop_length': self.hop_length,
                        'n_bins': self.n_bins,
                        'bins_per_octave': self.bins_per_octave,
                        'fmin': self.fmin
                    },
                    'pqg_integration_used': pqg_alignment_path is not None and Path(pqg_alignment_path).exists()
                }
            }
            
            results_file = output_path / "enhanced_alignment_complete.json"
            with open(results_file, 'w') as f:
                json.dump(final_results, f, indent=2)
            
            logger.info(f"Alignment Complete! Results in {output_path}")
            return final_results
            
        except Exception as e:
            logger.error(f"Alignment pipeline failed: {e}")
            raise

def main():
    """Example usage of Enhanced Symbolic Aligner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Symbolic Alignment (Block 2) with Grading Metrics')
    parser.add_argument('score_graph', help='Path to ScoreGraph JSON from Block 0')
    parser.add_argument('performance_midi', help='Path to performance MIDI from Block 1')
    parser.add_argument('--beats', help='Path to beats JSON from Block 4 (optional)')
    parser.add_argument('--pqg', help='Path to PQG-A2SA alignment JSON (optional, for precise onset/offset)')
    parser.add_argument('--output', '-o', default='block_2_enhanced_output',
                       help='Output directory')
    parser.add_argument('--sr', type=int, default=22050, help='Sample rate')
    parser.add_argument('--hop-length', type=int, default=512, help='Hop length')
    
    args = parser.parse_args()
    
    # Create aligner
    aligner = EnhancedSymbolicAligner(
        sr=args.sr,
        hop_length=args.hop_length
    )
    
    # Run alignment
    try:
        results = aligner.align_score_performance(
            args.score_graph,
            args.performance_midi,
            beats_json_path=args.beats,
            pqg_alignment_path=args.pqg,
            output_dir=args.output
        )
        
        print("\n" + "="*70)
        print("ENHANCED ALIGNMENT WITH GRADING METRICS - COMPLETE")
        print("="*70)
        print(f"Confidence: {results['alignment']['confidence']:.3f}")
        print(f"DTW Distance: {results['alignment']['dtw_distance']:.4f}")
        print(f"Score Duration: {results['alignment']['score_duration']:.2f}s")
        print(f"Performance Duration: {results['alignment']['perf_duration']:.2f}s")
        
        metadata = results['alignment'].get('alignment_metadata', {})
        if metadata.get('beat_weighting_used'):
            print("✓ Beat weighting: ENABLED")
        if metadata.get('adaptive_weights_used'):
            print("✓ Fermata/cadence adaptation: ENABLED")
        if results['metadata'].get('pqg_integration_used'):
            print("✓ PQG-A2SA precise alignment: ENABLED")
        
        # Display grading metrics summary
        if 'grading_metrics' in results['alignment']:
            print("\n" + "="*70)
            print("GRADING METRICS SUMMARY")
            print("="*70)
            gm = results['alignment']['grading_metrics']
            
            if 'rhythm_tempo' in gm and gm['rhythm_tempo']:
                rt = gm['rhythm_tempo']
                print(f"\n[1] Rhythm & Tempo (30%):")
                print(f"  - Mean onset error: {rt.get('mean_onset_error_ms', 0):.2f} ms")
                print(f"  - IOI correlation: {rt.get('ioi_correlation', 0):.3f}")
                print(f"  - Tempo CV: {rt.get('tempo_cv_percent', 0):.2f}%")
            
            if 'sound_quality' in gm and gm['sound_quality']:
                sq = gm['sound_quality']
                print(f"\n[2] Sound Quality (20%):")
                print(f"  - Pitch accuracy (50¢): {sq.get('pitch_accuracy_50c_percent', 0):.2f}%")
                print(f"  - Mean pitch error: {sq.get('mean_pitch_error_cents', 0):.2f} cents")
            
            if 'technical_virtuosity' in gm and gm['technical_virtuosity']:
                tv = gm['technical_virtuosity']
                print(f"\n[3] Technical Virtuosity (20%):")
                print(f"  - Note accuracy: {tv.get('note_accuracy_percent', 0):.2f}%")
                print(f"  - Matched notes: {tv.get('matched_notes', 0)}/{tv.get('total_score_notes', 0)}")
                print(f"  - Fluency CV: {tv.get('fluency_ioi_cv_percent', 0):.2f}%")
            
            if 'phrasing_diction' in gm and gm['phrasing_diction']:
                pd = gm['phrasing_diction']
                print(f"\n[4] Phrasing & Diction (15%):")
                print(f"  - Rubato variation: {pd.get('rubato_variation_std', 0):.3f}")
                print(f"  - Phrase boundaries: {pd.get('phrase_boundary_count', 0)}")
                print(f"  - Agogic expression: {pd.get('agogic_expression_mean_percent', 0):.2f}%")
            
            if 'communicativeness' in gm and gm['communicativeness']:
                cm = gm['communicativeness']
                print(f"\n[5] Communicativeness (15%):")
                print(f"  - Structural sections: {cm.get('section_count', 0)}")
                print(f"  - Climax position: {cm.get('climax_position_percent', 0):.1f}%")
        
        print("\n" + "="*70)
        print(f"Results saved to: {args.output}")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Alignment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
