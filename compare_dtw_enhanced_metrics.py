#!/usr/bin/env python3
"""
DTW Comparison with Enhanced Metrics (Including Pitch and Beat Analysis)

Adds comprehensive pitch and beat metrics to the original comparison tool.
"""

import numpy as np
import pretty_midi
import librosa
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import logging
from typing import Dict, List, Tuple, Optional
from scipy.spatial.distance import cdist
from scipy.stats import pearsonr
import pandas as pd
from datetime import datetime
import copy

from instrument_extractor import InstrumentExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10


class PerformanceSimulator:
    """Simulate realistic performance variations from score"""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
    
    def add_performance_variations(self, score_midi: pretty_midi.PrettyMIDI,
                                  tempo_variation=0.15,
                                  rubato_strength=0.12,
                                  timing_jitter=0.03,
                                  pitch_errors_probability=0.0) -> pretty_midi.PrettyMIDI:
        """
        Create a synthetic performance with realistic variations
        
        Args:
            score_midi: Original score MIDI
            tempo_variation: Global tempo variation factor (0.15 = ±15%)
            rubato_strength: Local rubato strength (0.12 = 12%)
            timing_jitter: Random timing jitter in seconds (0.03 = ±30ms)
            pitch_errors_probability: Probability of pitch errors (0.0 = no errors)
        
        Returns:
            Modified MIDI simulating human performance
        """
        logger.info(f"Creating synthetic performance with variations...")
        logger.info(f"  Tempo variation: ±{tempo_variation*100:.0f}%")
        logger.info(f"  Rubato strength: {rubato_strength*100:.0f}%")
        logger.info(f"  Timing jitter: ±{timing_jitter*1000:.0f}ms")
        logger.info(f"  Pitch error probability: {pitch_errors_probability*100:.1f}%")
        
        perf_midi = pretty_midi.PrettyMIDI()
        
        # Global tempo change
        global_tempo_factor = 1.0 + np.random.uniform(-tempo_variation, tempo_variation)
        
        for instrument in score_midi.instruments:
            new_instrument = pretty_midi.Instrument(
                program=instrument.program,
                is_drum=instrument.is_drum,
                name=instrument.name
            )
            
            for note in instrument.notes:
                # Apply global tempo
                onset = note.start * global_tempo_factor
                offset = note.end * global_tempo_factor
                
                # Add local rubato (gradual tempo changes)
                rubato_factor = 1.0 + rubato_strength * np.sin(onset / 2.0)
                onset *= rubato_factor
                offset *= rubato_factor
                
                # Add random timing jitter
                onset += np.random.normal(0, timing_jitter)
                offset += np.random.normal(0, timing_jitter)
                
                # Ensure offset > onset
                if offset <= onset:
                    offset = onset + 0.1
                
                # Add velocity variation
                velocity = note.velocity + np.random.randint(-10, 10)
                velocity = max(20, min(127, velocity))
                
                # Optionally add pitch errors (for testing pitch metrics)
                pitch = note.pitch
                if pitch_errors_probability > 0 and np.random.random() < pitch_errors_probability:
                    pitch += np.random.choice([-1, 1])  # Half-step error
                    pitch = max(0, min(127, pitch))
                
                new_note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=pitch,
                    start=max(0, onset),
                    end=max(0.1, offset)
                )
                new_instrument.notes.append(new_note)
            
            perf_midi.instruments.append(new_instrument)
        
        return perf_midi


class EnhancedDTWAligner:
    """Enhanced DTW with Sakoe-Chiba band constraint"""
    
    def __init__(self, band_width=0.1):
        """
        Args:
            band_width: Width of Sakoe-Chiba band as fraction of sequence length
        """
        self.band_width = band_width
    
    def align(self, score_midi: pretty_midi.PrettyMIDI, 
              perf_midi: pretty_midi.PrettyMIDI) -> Dict:
        """Perform enhanced DTW alignment with constraints"""
        
        # Extract features (chromagrams)
        score_chroma = self._extract_chromagram(score_midi)
        perf_chroma = self._extract_chromagram(perf_midi)
        
        # Compute constrained DTW
        D, path = self._dtw_constrained(score_chroma.T, perf_chroma.T)
        
        # Create time mapping
        score_times = np.linspace(0, score_midi.get_end_time(), score_chroma.shape[1])
        perf_times = np.linspace(0, perf_midi.get_end_time(), perf_chroma.shape[1])
        
        time_mapping = []
        for i, j in path:
            time_mapping.append({
                'score_time': score_times[i],
                'perf_time': perf_times[j]
            })
        
        return {
            'time_mapping': time_mapping,
            'dtw_distance': D[-1, -1],
            'path': path,
            'score_chroma': score_chroma,
            'perf_chroma': perf_chroma
        }
    
    def _extract_chromagram(self, midi: pretty_midi.PrettyMIDI, 
                           sr=22050, hop_length=512) -> np.ndarray:
        """Extract chromagram from MIDI"""
        audio = midi.fluidsynth(fs=sr)
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr, hop_length=hop_length)
        return chroma
    
    def _dtw_constrained(self, X: np.ndarray, Y: np.ndarray) -> Tuple[np.ndarray, List]:
        """DTW with Sakoe-Chiba band constraint"""
        N, M = len(X), len(Y)
        
        # Compute band width
        band = max(int(self.band_width * max(N, M)), 5)
        
        # Cost matrix
        cost = cdist(X, Y, metric='cosine')
        
        # Accumulated cost matrix
        D = np.full((N, M), np.inf)
        D[0, 0] = cost[0, 0]
        
        # Fill with band constraint
        for i in range(N):
            for j in range(max(0, i - band), min(M, i + band + 1)):
                if i == 0 and j == 0:
                    continue
                
                candidates = []
                if i > 0 and j >= i - band:
                    candidates.append(D[i-1, j])
                if j > 0 and j <= i + band:
                    candidates.append(D[i, j-1])
                if i > 0 and j > 0:
                    candidates.append(D[i-1, j-1])
                
                if candidates:
                    D[i, j] = cost[i, j] + min(candidates)
        
        # Backtrack
        path = []
        i, j = N-1, M-1
        path.append((i, j))
        
        while i > 0 or j > 0:
            if i == 0:
                j -= 1
            elif j == 0:
                i -= 1
            else:
                candidates = []
                if D[i-1, j] != np.inf:
                    candidates.append((D[i-1, j], (-1, 0)))
                if D[i, j-1] != np.inf:
                    candidates.append((D[i, j-1], (0, -1)))
                if D[i-1, j-1] != np.inf:
                    candidates.append((D[i-1, j-1], (-1, -1)))
                
                if not candidates:
                    break
                
                _, (di, dj) = min(candidates)
                i += di
                j += dj
            
            path.append((i, j))
        
        path.reverse()
        return D, path


class BaselineDTWAligner:
    """Vanilla DTW alignment (no optimizations)"""
    
    def align(self, score_midi: pretty_midi.PrettyMIDI, 
              perf_midi: pretty_midi.PrettyMIDI) -> Dict:
        """Perform basic DTW alignment"""
        
        # Extract features (chromagrams)
        score_chroma = self._extract_chromagram(score_midi)
        perf_chroma = self._extract_chromagram(perf_midi)
        
        # Compute DTW
        D, path = self._dtw(score_chroma.T, perf_chroma.T)
        
        # Create time mapping
        score_times = np.linspace(0, score_midi.get_end_time(), score_chroma.shape[1])
        perf_times = np.linspace(0, perf_midi.get_end_time(), perf_chroma.shape[1])
        
        time_mapping = []
        for i, j in path:
            time_mapping.append({
                'score_time': score_times[i],
                'perf_time': perf_times[j]
            })
        
        return {
            'time_mapping': time_mapping,
            'dtw_distance': D[-1, -1],
            'path': path,
            'score_chroma': score_chroma,
            'perf_chroma': perf_chroma
        }
    
    def _extract_chromagram(self, midi: pretty_midi.PrettyMIDI, 
                           sr=22050, hop_length=512) -> np.ndarray:
        """Extract chromagram from MIDI"""
        audio = midi.fluidsynth(fs=sr)
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr, hop_length=hop_length)
        return chroma
    
    def _dtw(self, X: np.ndarray, Y: np.ndarray) -> Tuple[np.ndarray, List]:
        """Basic DTW implementation"""
        N, M = len(X), len(Y)
        
        # Cost matrix
        cost = cdist(X, Y, metric='cosine')
        
        # Accumulated cost matrix
        D = np.full((N, M), np.inf)
        D[0, 0] = cost[0, 0]
        
        # Fill first row and column
        for i in range(1, N):
            D[i, 0] = D[i-1, 0] + cost[i, 0]
        for j in range(1, M):
            D[0, j] = D[0, j-1] + cost[0, j]
        
        # Fill rest of matrix
        for i in range(1, N):
            for j in range(1, M):
                D[i, j] = cost[i, j] + min(D[i-1, j], D[i, j-1], D[i-1, j-1])
        
        # Backtrack to find path
        path = []
        i, j = N-1, M-1
        path.append((i, j))
        
        while i > 0 or j > 0:
            if i == 0:
                j -= 1
            elif j == 0:
                i -= 1
            else:
                candidates = [D[i-1, j], D[i, j-1], D[i-1, j-1]]
                argmin = np.argmin(candidates)
                if argmin == 0:
                    i -= 1
                elif argmin == 1:
                    j -= 1
                else:
                    i -= 1
                    j -= 1
            path.append((i, j))
        
        path.reverse()
        return D, path


class EnhancedMetricsComputer:
    """Compute enhanced metrics including pitch and beat analysis"""
    
    def __init__(self):
        pass
    
    def compute_pitch_metrics(self, score_midi: pretty_midi.PrettyMIDI,
                            perf_midi: pretty_midi.PrettyMIDI,
                            alignment_map: List[Dict]) -> Dict:
        """
        Compute pitch-based alignment metrics
        
        Args:
            score_midi: Score MIDI file
            perf_midi: Performance MIDI file
            alignment_map: List of {'score_time': t1, 'perf_time': t2} mappings
        
        Returns:
            Dictionary with pitch metrics
        """
        if not score_midi.instruments or not perf_midi.instruments:
            return self._empty_pitch_metrics()
        
        score_notes = sorted(score_midi.instruments[0].notes, key=lambda n: n.start)
        perf_notes = sorted(perf_midi.instruments[0].notes, key=lambda n: n.start)
        
        if not score_notes or not perf_notes:
            return self._empty_pitch_metrics()
        
        # Match notes based on alignment
        matched_pairs = []
        for score_note in score_notes:
            score_time = score_note.start
            
            # Find corresponding performance time in alignment
            perf_time = self._find_aligned_time(score_time, alignment_map, 'score_to_perf')
            
            # Find nearest performance note
            perf_note = self._find_nearest_note(perf_time, perf_notes)
            
            if perf_note:
                matched_pairs.append((score_note, perf_note))
        
        # Calculate pitch metrics
        pitch_matches = 0
        chromatic_errors = []
        
        for score_note, perf_note in matched_pairs:
            if score_note.pitch == perf_note.pitch:
                pitch_matches += 1
            
            chromatic_error = abs(score_note.pitch - perf_note.pitch)
            chromatic_errors.append(chromatic_error)
        
        total_notes = len(matched_pairs)
        
        return {
            'pitch_accuracy': pitch_matches / total_notes if total_notes > 0 else 0.0,
            'mean_chromatic_error': np.mean(chromatic_errors) if chromatic_errors else 0.0,
            'max_chromatic_error': np.max(chromatic_errors) if chromatic_errors else 0.0,
            'std_chromatic_error': np.std(chromatic_errors) if chromatic_errors else 0.0,
            'total_notes_matched': total_notes,
            'perfect_pitch_matches': pitch_matches,
            'chromatic_error_distribution': np.bincount(chromatic_errors) if chromatic_errors else []
        }
    
    def compute_beat_metrics(self, score_midi: pretty_midi.PrettyMIDI,
                           perf_midi: pretty_midi.PrettyMIDI,
                           alignment_map: List[Dict],
                           sr=22050) -> Dict:
        """
        Compute beat-based alignment metrics
        
        Args:
            score_midi: Score MIDI file
            perf_midi: Performance MIDI file
            alignment_map: Alignment mapping
            sr: Sample rate for beat detection
        
        Returns:
            Dictionary with beat metrics
        """
        # Extract beats from audio
        score_audio = score_midi.fluidsynth(fs=sr)
        perf_audio = perf_midi.fluidsynth(fs=sr)
        
        # Detect beats
        _, score_beats = librosa.beat.beat_track(y=score_audio, sr=sr)
        _, perf_beats = librosa.beat.beat_track(y=perf_audio, sr=sr)
        
        # Convert beat frames to time
        score_beat_times = librosa.frames_to_time(score_beats, sr=sr)
        perf_beat_times = librosa.frames_to_time(perf_beats, sr=sr)
        
        if len(score_beat_times) == 0 or len(perf_beat_times) == 0:
            return self._empty_beat_metrics()
        
        # Calculate beat alignment errors
        beat_errors = []
        
        for score_beat_time in score_beat_times:
            # Find aligned performance time
            aligned_perf_time = self._find_aligned_time(score_beat_time, alignment_map, 'score_to_perf')
            
            # Find nearest actual performance beat
            nearest_perf_beat = self._find_nearest_beat(aligned_perf_time, perf_beat_times)
            
            if nearest_perf_beat is not None:
                error = abs(aligned_perf_time - nearest_perf_beat) * 1000  # Convert to ms
                beat_errors.append(error)
        
        # Downbeat detection (every 4th beat typically)
        score_downbeats = score_beat_times[::4] if len(score_beat_times) >= 4 else score_beat_times[:1]
        perf_downbeats = perf_beat_times[::4] if len(perf_beat_times) >= 4 else perf_beat_times[:1]
        
        downbeat_stats = self._compute_downbeat_accuracy(
            score_downbeats, perf_downbeats, alignment_map
        )
        
        return {
            'beat_mae': np.mean(beat_errors) if beat_errors else 0.0,
            'beat_rmse': np.sqrt(np.mean(np.array(beat_errors)**2)) if beat_errors else 0.0,
            'beat_max_error': np.max(beat_errors) if beat_errors else 0.0,
            'beat_std_error': np.std(beat_errors) if beat_errors else 0.0,
            'num_beats_evaluated': len(beat_errors),
            'downbeat_precision': downbeat_stats['precision'],
            'downbeat_recall': downbeat_stats['recall'],
            'downbeat_f1': downbeat_stats['f1'],
            'total_score_beats': len(score_beat_times),
            'total_perf_beats': len(perf_beat_times)
        }
    
    def compute_harmonic_consistency(self, score_chroma: np.ndarray,
                                    perf_chroma: np.ndarray,
                                    path: List[Tuple[int, int]]) -> Dict:
        """
        Compute harmonic consistency between aligned frames
        
        Args:
            score_chroma: Score chromagram (12 x T1)
            perf_chroma: Performance chromagram (12 x T2)
            path: DTW path [(i, j), ...]
        
        Returns:
            Dictionary with harmonic metrics
        """
        similarities = []
        
        for i, j in path:
            if i < score_chroma.shape[1] and j < perf_chroma.shape[1]:
                score_vec = score_chroma[:, i]
                perf_vec = perf_chroma[:, j]
                
                # Cosine similarity
                norm_score = np.linalg.norm(score_vec)
                norm_perf = np.linalg.norm(perf_vec)
                
                if norm_score > 0 and norm_perf > 0:
                    similarity = np.dot(score_vec, perf_vec) / (norm_score * norm_perf)
                    similarities.append(similarity)
        
        return {
            'mean_harmonic_similarity': np.mean(similarities) if similarities else 0.0,
            'min_harmonic_similarity': np.min(similarities) if similarities else 0.0,
            'std_harmonic_similarity': np.std(similarities) if similarities else 0.0,
            'num_frames_evaluated': len(similarities)
        }
    
    def _find_aligned_time(self, query_time: float, alignment_map: List[Dict], 
                          direction: str = 'score_to_perf') -> float:
        """Find aligned time using linear interpolation"""
        if direction == 'score_to_perf':
            times_from = [m['score_time'] for m in alignment_map]
            times_to = [m['perf_time'] for m in alignment_map]
        else:
            times_from = [m['perf_time'] for m in alignment_map]
            times_to = [m['score_time'] for m in alignment_map]
        
        return np.interp(query_time, times_from, times_to)
    
    def _find_nearest_note(self, time: float, notes: List, tolerance: float = 0.5):
        """Find nearest note to given time"""
        min_dist = float('inf')
        nearest = None
        
        for note in notes:
            dist = abs(note.start - time)
            if dist < min_dist and dist < tolerance:
                min_dist = dist
                nearest = note
        
        return nearest
    
    def _find_nearest_beat(self, time: float, beats: np.ndarray, 
                          tolerance: float = 0.5) -> Optional[float]:
        """Find nearest beat to given time"""
        if len(beats) == 0:
            return None
        
        diffs = np.abs(beats - time)
        min_idx = np.argmin(diffs)
        
        if diffs[min_idx] < tolerance:
            return beats[min_idx]
        return None
    
    def _compute_downbeat_accuracy(self, score_downbeats: np.ndarray,
                                  perf_downbeats: np.ndarray,
                                  alignment_map: List[Dict],
                                  tolerance: float = 0.05) -> Dict:
        """Compute downbeat detection precision/recall/F1"""
        true_positives = 0
        matched_perf = set()
        
        for score_db in score_downbeats:
            aligned_time = self._find_aligned_time(score_db, alignment_map, 'score_to_perf')
            nearest_perf_db = self._find_nearest_beat(aligned_time, perf_downbeats, tolerance)
            
            if nearest_perf_db is not None:
                true_positives += 1
                matched_perf.add(nearest_perf_db)
        
        false_positives = len(perf_downbeats) - len(matched_perf)
        false_negatives = len(score_downbeats) - true_positives
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {'precision': precision, 'recall': recall, 'f1': f1}
    
    def _empty_pitch_metrics(self) -> Dict:
        """Return empty pitch metrics"""
        return {
            'pitch_accuracy': 0.0,
            'mean_chromatic_error': 0.0,
            'max_chromatic_error': 0.0,
            'std_chromatic_error': 0.0,
            'total_notes_matched': 0,
            'perfect_pitch_matches': 0,
            'chromatic_error_distribution': []
        }
    
    def _empty_beat_metrics(self) -> Dict:
        """Return empty beat metrics"""
        return {
            'beat_mae': 0.0,
            'beat_rmse': 0.0,
            'beat_max_error': 0.0,
            'beat_std_error': 0.0,
            'num_beats_evaluated': 0,
            'downbeat_precision': 0.0,
            'downbeat_recall': 0.0,
            'downbeat_f1': 0.0,
            'total_score_beats': 0,
            'total_perf_beats': 0
        }


class DTWComparator:
    """Compare Baseline DTW vs Enhanced DTW with comprehensive metrics"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.baseline_aligner = BaselineDTWAligner()
        self.enhanced_aligner = EnhancedDTWAligner(band_width=0.1)
        self.metrics_computer = EnhancedMetricsComputer()
        self.simulator = PerformanceSimulator()
        
        self.results = []
    
    def compare_on_instrument(self, score_midi_path: Path, instrument_name: str):
        """Run comparison for a specific instrument"""
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing: {instrument_name}")
        logger.info(f"{'='*70}")
        
        # Extract instrument
        extractor = InstrumentExtractor()
        instrument_midi = extractor.extract_instrument_midi(str(score_midi_path), instrument_name)
        
        if not instrument_midi or not instrument_midi.instruments:
            logger.warning(f"Could not extract {instrument_name}")
            return
        
        # Create synthetic performance
        perf_midi = self.simulator.add_performance_variations(
            instrument_midi,
            tempo_variation=0.15,
            rubato_strength=0.12,
            timing_jitter=0.03
        )
        
        # Save MIDI files
        inst_dir = self.output_dir / instrument_name
        inst_dir.mkdir(exist_ok=True)
        
        score_path = inst_dir / f"{instrument_name}_score.mid"
        perf_path = inst_dir / f"{instrument_name}_performance.mid"
        
        instrument_midi.write(str(score_path))
        perf_midi.write(str(perf_path))
        
        logger.info(f"Saved score: {score_path}")
        logger.info(f"Saved performance: {perf_path}")
        
        # Run alignments
        logger.info("Running Baseline DTW...")
        baseline_result = self.baseline_aligner.align(instrument_midi, perf_midi)
        
        logger.info("Running Enhanced DTW...")
        enhanced_result = self.enhanced_aligner.align(instrument_midi, perf_midi)
        
        # Compute metrics
        metrics = self._compute_comprehensive_metrics(
            baseline_result, enhanced_result, instrument_name,
            instrument_midi, perf_midi
        )
        
        # Save results
        self._save_results(metrics, instrument_name)
        
        # Generate plots
        self._generate_comprehensive_plots(
            baseline_result, enhanced_result, metrics, instrument_name
        )
        
        self.results.append(metrics)
        
        logger.info(f"✓ Completed {instrument_name}")
    
    def _compute_comprehensive_metrics(self, baseline: Dict, enhanced: Dict, 
                                       instrument: str,
                                       score_midi: pretty_midi.PrettyMIDI,
                                       perf_midi: pretty_midi.PrettyMIDI) -> Dict:
        """Compute ALL metrics including pitch and beat"""
        
        logger.info(f"Computing comprehensive metrics for {instrument}...")
        
        metrics = {
            'instrument': instrument,
            'timestamp': datetime.now().isoformat(),
            'ground_truth': {
                'score_duration': score_midi.get_end_time(),
                'perf_duration': perf_midi.get_end_time(),
                'tempo_ratio': perf_midi.get_end_time() / score_midi.get_end_time(),
                'num_notes': len(score_midi.instruments[0].notes) if score_midi.instruments else 0
            },
            'baseline': {},
            'enhanced': {},
            'improvement': {}
        }
        
        # Extract time mappings
        baseline_map = baseline['time_mapping']
        enhanced_map = enhanced['time_mapping']
        
        base_score = np.array([m['score_time'] for m in baseline_map])
        base_perf = np.array([m['perf_time'] for m in baseline_map])
        enh_score = np.array([m['score_time'] for m in enhanced_map])
        enh_perf = np.array([m['perf_time'] for m in enhanced_map])
        
        # 1. DTW Distance
        metrics['baseline']['dtw_distance'] = baseline['dtw_distance']
        metrics['enhanced']['dtw_distance'] = enhanced.get('dtw_distance', 0)
        
        # 2. Path characteristics
        metrics['baseline']['path_length'] = len(baseline_map)
        metrics['enhanced']['path_length'] = len(enhanced_map)
        
        # 3. Timing errors
        true_tempo = perf_midi.get_end_time() / score_midi.get_end_time()
        
        base_timing = self._compute_timing_errors(base_score, base_perf, true_tempo)
        enh_timing = self._compute_timing_errors(enh_score, enh_perf, true_tempo)
        
        metrics['baseline'].update(base_timing)
        metrics['enhanced'].update(enh_timing)
        
        # 4. Smoothness
        base_smooth = self._compute_smoothness(base_score, base_perf)
        enh_smooth = self._compute_smoothness(enh_score, enh_perf)
        
        metrics['baseline'].update(base_smooth)
        metrics['enhanced'].update(enh_smooth)
        
        # 5. Correlation
        base_corr, _ = pearsonr(base_score, base_perf)
        enh_corr, _ = pearsonr(enh_score, enh_perf)
        
        metrics['baseline']['correlation'] = base_corr
        metrics['enhanced']['correlation'] = enh_corr
        
        # 6. NEW: Pitch Metrics
        logger.info("  Computing pitch metrics...")
        base_pitch = self.metrics_computer.compute_pitch_metrics(
            score_midi, perf_midi, baseline_map
        )
        enh_pitch = self.metrics_computer.compute_pitch_metrics(
            score_midi, perf_midi, enhanced_map
        )
        
        metrics['baseline']['pitch_metrics'] = base_pitch
        metrics['enhanced']['pitch_metrics'] = enh_pitch
        
        # 7. NEW: Beat Metrics
        logger.info("  Computing beat metrics...")
        base_beat = self.metrics_computer.compute_beat_metrics(
            score_midi, perf_midi, baseline_map
        )
        enh_beat = self.metrics_computer.compute_beat_metrics(
            score_midi, perf_midi, enhanced_map
        )
        
        metrics['baseline']['beat_metrics'] = base_beat
        metrics['enhanced']['beat_metrics'] = enh_beat
        
        # 8. NEW: Harmonic Consistency
        logger.info("  Computing harmonic consistency...")
        base_harmonic = self.metrics_computer.compute_harmonic_consistency(
            baseline['score_chroma'], baseline['perf_chroma'], baseline['path']
        )
        enh_harmonic = self.metrics_computer.compute_harmonic_consistency(
            baseline['score_chroma'], baseline['perf_chroma'], 
            enhanced.get('path', baseline['path'])
        )
        
        metrics['baseline']['harmonic_metrics'] = base_harmonic
        metrics['enhanced']['harmonic_metrics'] = enh_harmonic
        
        # 9. Calculate improvements
        self._compute_improvements(metrics)
        
        return metrics
    
    def _compute_timing_errors(self, score_times: np.ndarray, 
                              perf_times: np.ndarray,
                              true_tempo: float) -> Dict:
        """Compute timing error metrics"""
        expected_perf = score_times * true_tempo
        errors = perf_times - expected_perf
        
        return {
            'mae': float(np.mean(np.abs(errors)) * 1000),  # Convert to ms
            'rmse': float(np.sqrt(np.mean(errors**2)) * 1000),
            'max_error': float(np.max(np.abs(errors)) * 1000),
            'std_error': float(np.std(errors) * 1000)
        }
    
    def _compute_smoothness(self, score_times: np.ndarray,
                           perf_times: np.ndarray) -> Dict:
        """Compute smoothness metrics"""
        if len(score_times) < 3:
            return {'smoothness_score': 0.0, 'tempo_variance': 0.0}
        
        score_diff = np.diff(score_times)
        perf_diff = np.diff(perf_times)
        
        valid = score_diff > 1e-6
        if not np.any(valid):
            return {'smoothness_score': 0.0, 'tempo_variance': 0.0}
        
        local_tempo = perf_diff[valid] / score_diff[valid]
        tempo_var = np.var(local_tempo)
        smoothness = 1.0 / (1.0 + tempo_var)
        
        return {
            'smoothness_score': float(smoothness),
            'tempo_variance': float(tempo_var)
        }
    
    def _compute_improvements(self, metrics: Dict):
        """Calculate improvement percentages"""
        base = metrics['baseline']
        enh = metrics['enhanced']
        imp = metrics['improvement']
        
        # Timing improvements
        if base.get('mae', 0) > 0:
            imp['mae_reduction'] = 100 * (base['mae'] - enh['mae']) / base['mae']
        
        if base.get('rmse', 0) > 0:
            imp['rmse_reduction'] = 100 * (base['rmse'] - enh['rmse']) / base['rmse']
        
        # Pitch improvements
        base_pitch_acc = base.get('pitch_metrics', {}).get('pitch_accuracy', 0)
        enh_pitch_acc = enh.get('pitch_metrics', {}).get('pitch_accuracy', 0)
        
        if base_pitch_acc > 0:
            imp['pitch_accuracy_improvement'] = 100 * (enh_pitch_acc - base_pitch_acc) / base_pitch_acc
        else:
            imp['pitch_accuracy_improvement'] = 0
        
        # Beat improvements
        base_beat_mae = base.get('beat_metrics', {}).get('beat_mae', 0)
        enh_beat_mae = enh.get('beat_metrics', {}).get('beat_mae', 0)
        
        if base_beat_mae > 0:
            imp['beat_mae_reduction'] = 100 * (base_beat_mae - enh_beat_mae) / base_beat_mae
        else:
            imp['beat_mae_reduction'] = 0
        
        # Harmonic improvements
        base_harmonic = base.get('harmonic_metrics', {}).get('mean_harmonic_similarity', 0)
        enh_harmonic = enh.get('harmonic_metrics', {}).get('mean_harmonic_similarity', 0)
        
        if base_harmonic > 0:
            imp['harmonic_similarity_improvement'] = 100 * (enh_harmonic - base_harmonic) / base_harmonic
        else:
            imp['harmonic_similarity_improvement'] = 0
    
    def _save_results(self, metrics: Dict, instrument: str):
        """Save metrics to JSON"""
        inst_dir = self.output_dir / instrument
        results_path = inst_dir / f"{instrument}_metrics.json"
        
        with open(results_path, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        logger.info(f"Saved metrics: {results_path}")
    
    def _generate_comprehensive_plots(self, baseline: Dict, enhanced: Dict,
                                      metrics: Dict, instrument: str):
        """Generate enhanced visualizations"""
        logger.info(f"Generating comprehensive plots for {instrument}...")
        
        inst_dir = self.output_dir / instrument
        
        # Extract data
        base_map = baseline['time_mapping']
        enh_map = enhanced['time_mapping']
        
        base_score = np.array([m['score_time'] for m in base_map])
        base_perf = np.array([m['perf_time'] for m in base_map])
        enh_score = np.array([m['score_time'] for m in enh_map])
        enh_perf = np.array([m['perf_time'] for m in enh_map])
        
        true_tempo = metrics['ground_truth']['tempo_ratio']
        
        # Create comprehensive figure
        fig = plt.figure(figsize=(24, 16))
        
        # Plot 1: Alignment Paths
        ax1 = plt.subplot(4, 4, 1)
        ax1.plot(base_score, base_perf, 'b-', alpha=0.5, linewidth=1.5, label='Baseline')
        ax1.plot(enh_score, enh_perf, 'r-', alpha=0.7, linewidth=2, label='Enhanced')
        max_score = max(base_score[-1], enh_score[-1])
        ax1.plot([0, max_score], [0, max_score * true_tempo], 'g--', 
                alpha=0.4, linewidth=2, label='Ground Truth')
        ax1.set_xlabel('Score Time (s)')
        ax1.set_ylabel('Performance Time (s)')
        ax1.set_title(f'{instrument.title()} - Alignment Paths', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Timing Errors
        ax2 = plt.subplot(4, 4, 2)
        base_errors = (base_perf - base_score * true_tempo) * 1000
        enh_errors = (enh_perf - enh_score * true_tempo) * 1000
        ax2.plot(base_score, base_errors, 'b-', alpha=0.5, label='Baseline')
        ax2.plot(enh_score, enh_errors, 'r-', alpha=0.7, label='Enhanced')
        ax2.axhline(0, color='g', linestyle='--', alpha=0.4)
        ax2.set_xlabel('Score Time (s)')
        ax2.set_ylabel('Error (ms)')
        ax2.set_title('Timing Errors Over Time', fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Error Distribution
        ax3 = plt.subplot(4, 4, 3)
        ax3.hist(np.abs(base_errors), bins=30, alpha=0.5, label='Baseline', color='blue')
        ax3.hist(np.abs(enh_errors), bins=30, alpha=0.7, label='Enhanced', color='red')
        ax3.set_xlabel('Absolute Error (ms)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Error Distribution', fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Cumulative Error
        ax4 = plt.subplot(4, 4, 4)
        ax4.plot(base_score, np.cumsum(np.abs(base_errors)), 'b-', label='Baseline')
        ax4.plot(enh_score, np.cumsum(np.abs(enh_errors)), 'r-', label='Enhanced')
        ax4.set_xlabel('Score Time (s)')
        ax4.set_ylabel('Cumulative Abs Error (ms)')
        ax4.set_title('Cumulative Error', fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Plot 5-8: NEW - Pitch and Beat Metrics
        self._plot_pitch_metrics(fig, metrics, 5)
        self._plot_beat_metrics(fig, metrics, 9)
        self._plot_harmonic_metrics(fig, metrics, baseline, 13)
        
        # Plot 9-12: Summary metrics
        self._plot_summary_metrics(fig, metrics, [6, 7, 8, 10, 11, 12, 14, 15, 16])
        
        plt.tight_layout()
        
        plot_path = inst_dir / f"{instrument}_comprehensive_comparison.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved plot: {plot_path}")
    
    def _plot_pitch_metrics(self, fig, metrics: Dict, start_pos: int):
        """Plot pitch-related metrics"""
        ax = plt.subplot(4, 4, start_pos)
        
        base_pitch = metrics['baseline']['pitch_metrics']
        enh_pitch = metrics['enhanced']['pitch_metrics']
        
        categories = ['Pitch\nAccuracy', 'Mean\nChromatic\nError']
        baseline_vals = [
            base_pitch['pitch_accuracy'] * 100,
            base_pitch['mean_chromatic_error']
        ]
        enhanced_vals = [
            enh_pitch['pitch_accuracy'] * 100,
            enh_pitch['mean_chromatic_error']
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        ax.bar(x - width/2, baseline_vals, width, label='Baseline', alpha=0.7, color='blue')
        ax.bar(x + width/2, enhanced_vals, width, label='Enhanced', alpha=0.7, color='red')
        
        ax.set_ylabel('Value')
        ax.set_title('Pitch Metrics', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=8)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_beat_metrics(self, fig, metrics: Dict, start_pos: int):
        """Plot beat-related metrics"""
        ax = plt.subplot(4, 4, start_pos)
        
        base_beat = metrics['baseline']['beat_metrics']
        enh_beat = metrics['enhanced']['beat_metrics']
        
        categories = ['Beat MAE\n(ms)', 'Downbeat\nF1']
        baseline_vals = [
            base_beat['beat_mae'],
            base_beat['downbeat_f1'] * 100
        ]
        enhanced_vals = [
            enh_beat['beat_mae'],
            enh_beat['downbeat_f1'] * 100
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        ax.bar(x - width/2, baseline_vals, width, label='Baseline', alpha=0.7, color='blue')
        ax.bar(x + width/2, enhanced_vals, width, label='Enhanced', alpha=0.7, color='red')
        
        ax.set_ylabel('Value')
        ax.set_title('Beat Metrics', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=8)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_harmonic_metrics(self, fig, metrics: Dict, baseline: Dict, start_pos: int):
        """Plot harmonic consistency"""
        ax = plt.subplot(4, 4, start_pos)
        
        base_harm = metrics['baseline']['harmonic_metrics']
        enh_harm = metrics['enhanced']['harmonic_metrics']
        
        values = [base_harm['mean_harmonic_similarity'], enh_harm['mean_harmonic_similarity']]
        labels = ['Baseline', 'Enhanced']
        colors = ['blue', 'red']
        
        ax.bar(labels, values, alpha=0.7, color=colors)
        ax.set_ylabel('Similarity Score')
        ax.set_title('Harmonic Consistency', fontweight='bold')
        ax.set_ylim([0, 1])
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_summary_metrics(self, fig, metrics: Dict, positions: List[int]):
        """Plot summary comparison metrics"""
        # Timing comparison
        ax1 = plt.subplot(4, 4, positions[0])
        timing_categories = ['MAE', 'RMSE', 'Max Error']
        baseline_timing = [
            metrics['baseline']['mae'],
            metrics['baseline']['rmse'],
            metrics['baseline']['max_error']
        ]
        enhanced_timing = [
            metrics['enhanced']['mae'],
            metrics['enhanced']['rmse'],
            metrics['enhanced']['max_error']
        ]
        
        x = np.arange(len(timing_categories))
        width = 0.35
        ax1.bar(x - width/2, baseline_timing, width, label='Baseline', alpha=0.7, color='blue')
        ax1.bar(x + width/2, enhanced_timing, width, label='Enhanced', alpha=0.7, color='red')
        ax1.set_ylabel('Error (ms)')
        ax1.set_title('Timing Error Comparison', fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(timing_categories, fontsize=9)
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Improvement percentages
        ax2 = plt.subplot(4, 4, positions[1])
        imp = metrics['improvement']
        improvements = [
            imp.get('mae_reduction', 0),
            imp.get('beat_mae_reduction', 0),
            imp.get('pitch_accuracy_improvement', 0)
        ]
        imp_labels = ['Timing\nMAE', 'Beat\nMAE', 'Pitch\nAccuracy']
        colors_imp = ['green' if x > 0 else 'red' for x in improvements]
        
        ax2.bar(imp_labels, improvements, alpha=0.7, color=colors_imp)
        ax2.axhline(0, color='black', linewidth=0.5)
        ax2.set_ylabel('Improvement (%)')
        ax2.set_title('Overall Improvements', fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Overall summary table
        ax3 = plt.subplot(4, 4, positions[2])
        ax3.axis('tight')
        ax3.axis('off')
        
        table_data = [
            ['Metric', 'Baseline', 'Enhanced', 'Improv.'],
            ['MAE (ms)', f"{metrics['baseline']['mae']:.1f}", 
             f"{metrics['enhanced']['mae']:.1f}", 
             f"{imp.get('mae_reduction', 0):.1f}%"],
            ['Pitch Acc', f"{metrics['baseline']['pitch_metrics']['pitch_accuracy']:.1%}",
             f"{metrics['enhanced']['pitch_metrics']['pitch_accuracy']:.1%}",
             f"{imp.get('pitch_accuracy_improvement', 0):.1f}%"],
            ['Beat MAE (ms)', f"{metrics['baseline']['beat_metrics']['beat_mae']:.1f}",
             f"{metrics['enhanced']['beat_metrics']['beat_mae']:.1f}",
             f"{imp.get('beat_mae_reduction', 0):.1f}%"]
        ]
        
        table = ax3.table(cellText=table_data, loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2)
        
        # Style header row
        for i in range(4):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        ax3.set_title('Summary Comparison', fontweight='bold', pad=20)
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        logger.info("\n" + "="*70)
        logger.info("GENERATING SUMMARY REPORT")
        logger.info("="*70)
        
        if not self.results:
            logger.warning("No results to summarize")
            return
        
        # Create summary dataframe
        summary_data = []
        for result in self.results:
            summary_data.append({
                'Instrument': result['instrument'],
                'Baseline MAE (ms)': result['baseline']['mae'],
                'Enhanced MAE (ms)': result['enhanced']['mae'],
                'MAE Reduction (%)': result['improvement'].get('mae_reduction', 0),
                'Baseline Pitch Acc (%)': result['baseline']['pitch_metrics']['pitch_accuracy'] * 100,
                'Enhanced Pitch Acc (%)': result['enhanced']['pitch_metrics']['pitch_accuracy'] * 100,
                'Pitch Improvement (%)': result['improvement'].get('pitch_accuracy_improvement', 0),
                'Baseline Beat MAE (ms)': result['baseline']['beat_metrics']['beat_mae'],
                'Enhanced Beat MAE (ms)': result['enhanced']['beat_metrics']['beat_mae'],
                'Beat MAE Reduction (%)': result['improvement'].get('beat_mae_reduction', 0)
            })
        
        df = pd.DataFrame(summary_data)
        
        # Save CSV
        csv_path = self.output_dir / 'comprehensive_summary.csv'
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved summary CSV: {csv_path}")
        
        # Print summary
        print("\n" + "="*100)
        print("COMPREHENSIVE COMPARISON SUMMARY")
        print("="*100)
        print(df.to_string(index=False))
        print("="*100)
        
        # Calculate averages
        print("\nAVERAGE IMPROVEMENTS:")
        print(f"  Timing MAE Reduction:      {df['MAE Reduction (%)'].mean():>6.2f}%")
        print(f"  Beat MAE Reduction:        {df['Beat MAE Reduction (%)'].mean():>6.2f}%")
        print(f"  Pitch Accuracy Improvement: {df['Pitch Improvement (%)'].mean():>6.2f}%")
        print("="*100)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare DTW algorithms with enhanced metrics')
    parser.add_argument('--score', type=str, required=True, help='Path to score MIDI file')
    parser.add_argument('--instruments', nargs='+', default=['violin', 'clarinet', 'saxophone', 'bassoon'],
                       help='Instruments to process')
    parser.add_argument('--output', type=str, default='Output/DTW_Comparison_Enhanced',
                       help='Output directory')
    
    args = parser.parse_args()
    
    # Initialize comparator
    comparator = DTWComparator(Path(args.output))
    
    # Process each instrument
    for instrument in args.instruments:
        try:
            comparator.compare_on_instrument(Path(args.score), instrument)
        except Exception as e:
            logger.error(f"Error processing {instrument}: {e}", exc_info=True)
    
    # Generate summary
    comparator.generate_summary_report()
    
    logger.info(f"\n✓ All processing complete! Results in: {args.output}")


if __name__ == '__main__':
    main()
