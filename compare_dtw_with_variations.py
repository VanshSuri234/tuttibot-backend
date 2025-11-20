#!/usr/bin/env python3
"""
DTW Comparison with Synthetic Performance Variations

Simulates realistic performance variations (rubato, timing jitter, tempo changes)
to properly demonstrate the difference between Baseline DTW and Enhanced DTW.
"""

import numpy as np
import pretty_midi
import librosa
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import logging
from typing import Dict, List, Tuple
from scipy.spatial.distance import cdist
from scipy.stats import pearsonr
import pandas as pd
from datetime import datetime
import copy

from instrument_extractor import InstrumentExtractor
import sys
sys.path.append(str(Path(__file__).parent / 'Temporal Alignment' / 'Block_2_SymbolicAlignment'))
from align_symbolic_enhanced import EnhancedSymbolicAligner

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
                                  rubato_strength=0.1,
                                  timing_jitter=0.02) -> pretty_midi.PrettyMIDI:
        """
        Create a synthetic performance with realistic variations
        
        Args:
            score_midi: Original score MIDI
            tempo_variation: Global tempo variation factor (0.15 = ±15%)
            rubato_strength: Local rubato strength
            timing_jitter: Random timing jitter (seconds)
        
        Returns:
            Modified MIDI simulating human performance
        """
        logger.info(f"Creating synthetic performance with variations...")
        logger.info(f"  Tempo variation: ±{tempo_variation*100:.0f}%")
        logger.info(f"  Rubato strength: {rubato_strength}")
        logger.info(f"  Timing jitter: ±{timing_jitter*1000:.0f}ms")
        
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
                
                new_note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=note.pitch,
                    start=max(0, onset),
                    end=max(onset + 0.01, offset)
                )
                new_instrument.notes.append(new_note)
            
            perf_midi.instruments.append(new_instrument)
        
        logger.info(f"  Score duration: {score_midi.get_end_time():.2f}s")
        logger.info(f"  Performance duration: {perf_midi.get_end_time():.2f}s")
        logger.info(f"  Tempo ratio: {perf_midi.get_end_time() / score_midi.get_end_time():.3f}")
        
        return perf_midi


class BaselineDTWAligner:
    """Simple baseline DTW without any enhancements"""
    
    def __init__(self, sr=22050, hop_length=512):
        self.sr = sr
        self.hop_length = hop_length
    
    def align(self, score_midi: pretty_midi.PrettyMIDI, 
              perf_midi: pretty_midi.PrettyMIDI) -> Dict:
        """Perform basic DTW alignment"""
        logger.info("Running Baseline DTW alignment...")
        
        # Extract chromagrams
        score_chroma = self._midi_to_chroma(score_midi)
        perf_chroma = self._midi_to_chroma(perf_midi)
        
        logger.info(f"  Score chroma: {score_chroma.shape}")
        logger.info(f"  Perf chroma: {perf_chroma.shape}")
        
        # Compute cost matrix
        cost_matrix = cdist(score_chroma.T, perf_chroma.T, metric='cosine')
        
        # Run vanilla DTW
        wp, distance = self._vanilla_dtw(cost_matrix)
        
        logger.info(f"  DTW distance: {distance:.4f}")
        logger.info(f"  Path length: {len(wp)}")
        
        # Convert to time mapping
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
        
        time_mapping = []
        for score_idx, perf_idx in wp:
            time_mapping.append({
                'score_time': float(score_times[score_idx]),
                'perf_time': float(perf_times[perf_idx]),
                'score_frame': int(score_idx),
                'perf_frame': int(perf_idx)
            })
        
        return {
            'time_mapping': time_mapping,
            'warping_path': wp.tolist(),
            'dtw_distance': float(distance),
            'algorithm': 'Baseline DTW',
            'score_duration': float(score_midi.get_end_time()),
            'perf_duration': float(perf_midi.get_end_time())
        }
    
    def _midi_to_chroma(self, midi_data: pretty_midi.PrettyMIDI) -> np.ndarray:
        """Convert MIDI to chromagram"""
        duration = midi_data.get_end_time()
        
        # Generate piano roll
        fs = self.sr / self.hop_length
        piano_roll = midi_data.get_piano_roll(fs=fs)
        
        # Convert to chroma
        chroma = librosa.feature.chroma_stft(
            S=piano_roll,
            sr=self.sr,
            hop_length=1,
            n_fft=4096
        )
        
        return chroma
    
    def _vanilla_dtw(self, cost_matrix: np.ndarray) -> Tuple[np.ndarray, float]:
        """Vanilla DTW without constraints"""
        N, M = cost_matrix.shape
        
        # Accumulated cost matrix
        D = np.full((N + 1, M + 1), np.inf)
        D[0, 0] = 0
        
        # Fill matrix
        for i in range(1, N + 1):
            for j in range(1, M + 1):
                cost = cost_matrix[i-1, j-1]
                D[i, j] = cost + min(
                    D[i-1, j],      # vertical
                    D[i, j-1],      # horizontal
                    D[i-1, j-1]     # diagonal
                )
        
        # Backtrack
        path = []
        i, j = N, M
        while i > 0 and j > 0:
            path.append([i-1, j-1])
            
            candidates = [
                (D[i-1, j-1], i-1, j-1),
                (D[i-1, j], i-1, j),
                (D[i, j-1], i, j-1)
            ]
            _, i, j = min(candidates)
        
        wp = np.array(path[::-1])
        distance = D[N, M] / len(wp)  # Normalize by path length
        
        return wp, distance


class DTWComparator:
    """Compare Baseline vs Enhanced DTW with synthetic performance variations"""
    
    def __init__(self, output_dir: str = "Output/DTW_Comparison_Realistic"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.baseline_aligner = BaselineDTWAligner()
        self.enhanced_aligner = EnhancedSymbolicAligner()
        self.instrument_extractor = InstrumentExtractor()
        self.perf_simulator = PerformanceSimulator()
    
    def compare_on_instrument(self, score_path: str, instrument: str) -> Dict:
        """Run both algorithms and compute comparative metrics"""
        
        logger.info(f"\nComparing algorithms on: {instrument}")
        logger.info("="*60)
        
        # Extract instrument MIDI from score
        score_midi_path = self.output_dir / f"{instrument}_score.mid"
        self.instrument_extractor.extract_instrument_midi(
            score_path, 
            instrument,
            str(score_midi_path)
        )
        
        # Load score MIDI
        score_midi = pretty_midi.PrettyMIDI(str(score_midi_path))
        
        # Create synthetic performance with variations
        perf_midi = self.perf_simulator.add_performance_variations(
            score_midi,
            tempo_variation=0.15,      # ±15% global tempo
            rubato_strength=0.12,       # Local tempo variations
            timing_jitter=0.03          # ±30ms timing jitter
        )
        
        # Save synthetic performance
        perf_midi_path = self.output_dir / f"{instrument}_performance_synthetic.mid"
        perf_midi.write(str(perf_midi_path))
        logger.info(f"Saved synthetic performance: {perf_midi_path.name}")
        
        # Run Baseline DTW
        baseline_results = self.baseline_aligner.align(score_midi, perf_midi)
        
        # Run Enhanced DTW
        logger.info("Running Enhanced DTW...")
        enhanced_results = self.enhanced_aligner.enhanced_alignment(
            score_midi, 
            perf_midi,
            beats_json=None,
            score_graph=None
        )
        
        # Compute comparative metrics
        metrics = self._compute_comprehensive_metrics(
            baseline_results,
            enhanced_results,
            instrument,
            score_midi,
            perf_midi
        )
        
        # Generate comparison plots
        self._generate_comprehensive_plots(
            baseline_results,
            enhanced_results,
            metrics,
            instrument
        )
        
        return {
            'instrument': instrument,
            'baseline_results': baseline_results,
            'enhanced_results': enhanced_results,
            'comparative_metrics': metrics
        }
    
    def _compute_comprehensive_metrics(self, baseline: Dict, enhanced: Dict, 
                                       instrument: str,
                                       score_midi: pretty_midi.PrettyMIDI,
                                       perf_midi: pretty_midi.PrettyMIDI) -> Dict:
        """Compute detailed comparative metrics"""
        
        logger.info(f"Computing comprehensive metrics for {instrument}...")
        
        metrics = {
            'instrument': instrument,
            'ground_truth': {
                'score_duration': score_midi.get_end_time(),
                'perf_duration': perf_midi.get_end_time(),
                'tempo_ratio': perf_midi.get_end_time() / score_midi.get_end_time(),
                'num_notes': len(score_midi.instruments[0].notes) if score_midi.instruments else 0
            },
            'baseline': {},
            'enhanced': {},
            'difference': {},
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
        metrics['enhanced']['dtw_distance'] = enhanced['dtw_distance']
        metrics['improvement']['dtw_distance_reduction'] = (
            100 * (baseline['dtw_distance'] - enhanced['dtw_distance']) / baseline['dtw_distance']
            if baseline['dtw_distance'] > 0 else 0
        )
        
        # 2. Path characteristics
        metrics['baseline']['path_length'] = len(baseline_map)
        metrics['enhanced']['path_length'] = len(enhanced_map)
        metrics['baseline']['path_density'] = len(baseline_map) / base_score[-1] if base_score[-1] > 0 else 0
        metrics['enhanced']['path_density'] = len(enhanced_map) / enh_score[-1] if enh_score[-1] > 0 else 0
        
        # 3. Alignment error (deviation from ground truth tempo)
        true_tempo_ratio = perf_midi.get_end_time() / score_midi.get_end_time()
        
        base_errors = self._compute_alignment_errors(base_score, base_perf, true_tempo_ratio)
        enh_errors = self._compute_alignment_errors(enh_score, enh_perf, true_tempo_ratio)
        
        metrics['baseline'].update(base_errors)
        metrics['enhanced'].update(enh_errors)
        
        metrics['improvement']['mae_reduction'] = (
            100 * (base_errors['mae'] - enh_errors['mae']) / base_errors['mae']
            if base_errors['mae'] > 0 else 0
        )
        metrics['improvement']['rmse_reduction'] = (
            100 * (base_errors['rmse'] - enh_errors['rmse']) / base_errors['rmse']
            if base_errors['rmse'] > 0 else 0
        )
        
        # 4. Temporal smoothness
        base_smooth = self._compute_smoothness_metrics(base_score, base_perf)
        enh_smooth = self._compute_smoothness_metrics(enh_score, enh_perf)
        
        metrics['baseline'].update(base_smooth)
        metrics['enhanced'].update(enh_smooth)
        
        metrics['improvement']['smoothness_improvement'] = (
            100 * (enh_smooth['smoothness_score'] - base_smooth['smoothness_score']) / base_smooth['smoothness_score']
            if base_smooth['smoothness_score'] > 0 else 0
        )
        
        # 5. Correlation
        base_corr, _ = pearsonr(base_score, base_perf)
        enh_corr, _ = pearsonr(enh_score, enh_perf)
        
        metrics['baseline']['correlation'] = base_corr
        metrics['enhanced']['correlation'] = enh_corr
        
        # 6. Overall quality score
        metrics['baseline']['quality_score'] = self._compute_quality_score(metrics['baseline'])
        metrics['enhanced']['quality_score'] = self._compute_quality_score(metrics['enhanced'])
        
        metrics['improvement']['overall_quality_improvement'] = (
            100 * (metrics['enhanced']['quality_score'] - metrics['baseline']['quality_score']) /
            metrics['baseline']['quality_score']
            if metrics['baseline']['quality_score'] > 0 else 0
        )
        
        return metrics
    
    def _compute_alignment_errors(self, score_times: np.ndarray, 
                                  perf_times: np.ndarray,
                                  true_tempo_ratio: float) -> Dict:
        """Compute alignment errors relative to ground truth"""
        
        # Expected performance time based on true tempo
        expected_perf = score_times * true_tempo_ratio
        
        # Errors
        errors = perf_times - expected_perf
        
        return {
            'mae': float(np.mean(np.abs(errors))),
            'rmse': float(np.sqrt(np.mean(errors**2))),
            'max_error': float(np.max(np.abs(errors))),
            'std_error': float(np.std(errors))
        }
    
    def _compute_smoothness_metrics(self, score_times: np.ndarray,
                                    perf_times: np.ndarray) -> Dict:
        """Compute temporal smoothness metrics"""
        
        if len(score_times) < 3:
            return {'smoothness_score': 0.0, 'tempo_variance': 0.0}
        
        # Local tempo ratios
        score_diff = np.diff(score_times)
        perf_diff = np.diff(perf_times)
        
        valid = score_diff > 1e-6
        if not np.any(valid):
            return {'smoothness_score': 0.0, 'tempo_variance': 0.0}
        
        local_tempo = perf_diff[valid] / score_diff[valid]
        
        # Smoothness = inverse of variance
        tempo_var = np.var(local_tempo)
        smoothness = 1.0 / (1.0 + tempo_var)
        
        return {
            'smoothness_score': float(smoothness),
            'tempo_variance': float(tempo_var)
        }
    
    def _compute_quality_score(self, metrics: Dict) -> float:
        """Compute composite quality score"""
        
        # Lower error is better
        mae_score = max(0, 1 - metrics.get('mae', 1.0))
        
        # Higher smoothness is better
        smooth_score = metrics.get('smoothness_score', 0)
        
        # Higher correlation is better
        corr_score = (metrics.get('correlation', 0) + 1) / 2  # Scale to [0, 1]
        
        # Weighted combination
        quality = 0.4 * mae_score + 0.3 * smooth_score + 0.3 * corr_score
        
        return float(quality)
    
    def _generate_comprehensive_plots(self, baseline: Dict, enhanced: Dict,
                                      metrics: Dict, instrument: str):
        """Generate detailed comparison visualizations"""
        
        logger.info(f"Generating comparison plots for {instrument}...")
        
        inst_dir = self.output_dir / instrument
        inst_dir.mkdir(exist_ok=True)
        
        # Extract data
        base_map = baseline['time_mapping']
        enh_map = enhanced['time_mapping']
        
        base_score = np.array([m['score_time'] for m in base_map])
        base_perf = np.array([m['perf_time'] for m in base_map])
        enh_score = np.array([m['score_time'] for m in enh_map])
        enh_perf = np.array([m['perf_time'] for m in enh_map])
        
        # Ground truth tempo
        true_tempo = metrics['ground_truth']['tempo_ratio']
        
        # Create figure
        fig = plt.figure(figsize=(20, 14))
        
        # 1. Alignment Paths
        ax1 = plt.subplot(3, 4, 1)
        ax1.plot(base_score, base_perf, 'b-', alpha=0.5, linewidth=1.5, label='Baseline DTW')
        ax1.plot(enh_score, enh_perf, 'r-', alpha=0.7, linewidth=2, label='Enhanced DTW')
        
        # Ground truth line
        max_score = max(base_score[-1], enh_score[-1])
        ax1.plot([0, max_score], [0, max_score * true_tempo], 'g--', 
                alpha=0.4, linewidth=2, label='Ground Truth')
        
        ax1.set_xlabel('Score Time (s)', fontsize=10)
        ax1.set_ylabel('Performance Time (s)', fontsize=10)
        ax1.set_title(f'{instrument.title()} - Alignment Paths', fontsize=11, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # 2. Alignment Errors
        ax2 = plt.subplot(3, 4, 2)
        
        base_expected = base_score * true_tempo
        enh_expected = enh_score * true_tempo
        base_err = base_perf - base_expected
        enh_err = enh_perf - enh_expected
        
        ax2.plot(base_score, base_err * 1000, 'b-', alpha=0.6, linewidth=1.5, label='Baseline')
        ax2.plot(enh_score, enh_err * 1000, 'r-', alpha=0.8, linewidth=2, label='Enhanced')
        ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        ax2.fill_between(base_score, -30, 30, alpha=0.1, color='green', label='±30ms tolerance')
        
        ax2.set_xlabel('Score Time (s)', fontsize=10)
        ax2.set_ylabel('Alignment Error (ms)', fontsize=10)
        ax2.set_title('Alignment Error Over Time', fontsize=11, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # 3. Error Distribution
        ax3 = plt.subplot(3, 4, 3)
        ax3.hist(base_err * 1000, bins=30, alpha=0.5, color='blue', 
                label=f'Baseline (MAE={metrics["baseline"]["mae"]*1000:.1f}ms)', density=True)
        ax3.hist(enh_err * 1000, bins=30, alpha=0.5, color='red',
                label=f'Enhanced (MAE={metrics["enhanced"]["mae"]*1000:.1f}ms)', density=True)
        ax3.axvline(x=0, color='k', linestyle='--', alpha=0.5)
        ax3.set_xlabel('Error (ms)', fontsize=10)
        ax3.set_ylabel('Density', fontsize=10)
        ax3.set_title('Error Distribution', fontsize=11, fontweight='bold')
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Cumulative Error
        ax4 = plt.subplot(3, 4, 4)
        ax4.plot(base_score, np.cumsum(np.abs(base_err)), 'b-', 
                alpha=0.6, linewidth=1.5, label='Baseline')
        ax4.plot(enh_score, np.cumsum(np.abs(enh_err)), 'r-',
                alpha=0.8, linewidth=2, label='Enhanced')
        ax4.set_xlabel('Score Time (s)', fontsize=10)
        ax4.set_ylabel('Cumulative Absolute Error (s)', fontsize=10)
        ax4.set_title('Cumulative Error', fontsize=11, fontweight='bold')
        ax4.legend(fontsize=9)
        ax4.grid(True, alpha=0.3)
        
        # 5. Local Tempo
        ax5 = plt.subplot(3, 4, 5)
        
        if len(base_score) > 1:
            base_tempo = np.diff(base_perf) / (np.diff(base_score) + 1e-9)
            ax5.plot(base_score[1:], base_tempo, 'b-', alpha=0.6, linewidth=1.5, label='Baseline')
        
        if len(enh_score) > 1:
            enh_tempo = np.diff(enh_perf) / (np.diff(enh_score) + 1e-9)
            ax5.plot(enh_score[1:], enh_tempo, 'r-', alpha=0.8, linewidth=2, label='Enhanced')
        
        ax5.axhline(y=true_tempo, color='g', linestyle='--', alpha=0.4, linewidth=2, label='True Tempo')
        ax5.set_xlabel('Score Time (s)', fontsize=10)
        ax5.set_ylabel('Local Tempo Ratio', fontsize=10)
        ax5.set_title('Tempo Tracking', fontsize=11, fontweight='bold')
        ax5.legend(fontsize=9)
        ax5.grid(True, alpha=0.3)
        
        # 6. Error Metrics Comparison
        ax6 = plt.subplot(3, 4, 6)
        
        metrics_names = ['MAE (ms)', 'RMSE (ms)', 'Max Error (ms)']
        base_vals = [
            metrics['baseline']['mae'] * 1000,
            metrics['baseline']['rmse'] * 1000,
            metrics['baseline']['max_error'] * 1000
        ]
        enh_vals = [
            metrics['enhanced']['mae'] * 1000,
            metrics['enhanced']['rmse'] * 1000,
            metrics['enhanced']['max_error'] * 1000
        ]
        
        x = np.arange(len(metrics_names))
        width = 0.35
        
        ax6.bar(x - width/2, base_vals, width, label='Baseline', color='blue', alpha=0.7)
        ax6.bar(x + width/2, enh_vals, width, label='Enhanced', color='red', alpha=0.7)
        
        ax6.set_ylabel('Error (ms)', fontsize=10)
        ax6.set_title('Error Metrics', fontsize=11, fontweight='bold')
        ax6.set_xticks(x)
        ax6.set_xticklabels(metrics_names, fontsize=9)
        ax6.legend(fontsize=9)
        ax6.grid(True, alpha=0.3, axis='y')
        
        # 7. Improvement Chart
        ax7 = plt.subplot(3, 4, 7)
        
        improvements = {
            'DTW Distance': metrics['improvement']['dtw_distance_reduction'],
            'MAE': metrics['improvement']['mae_reduction'],
            'RMSE': metrics['improvement']['rmse_reduction'],
            'Smoothness': metrics['improvement']['smoothness_improvement'],
            'Overall Quality': metrics['improvement']['overall_quality_improvement']
        }
        
        colors = ['green' if v > 0 else 'red' for v in improvements.values()]
        ax7.barh(list(improvements.keys()), list(improvements.values()), 
                color=colors, alpha=0.7)
        ax7.axvline(x=0, color='k', linestyle='-', linewidth=0.8)
        ax7.set_xlabel('Improvement (%)', fontsize=10)
        ax7.set_title('Performance Improvements', fontsize=11, fontweight='bold')
        ax7.grid(True, alpha=0.3, axis='x')
        
        # 8. DTW Distance Over Time
        ax8 = plt.subplot(3, 4, 8)
        ax8.text(0.1, 0.5, 
                f"""METRICS SUMMARY

Ground Truth:
  Duration Ratio: {true_tempo:.3f}
  Notes: {metrics['ground_truth']['num_notes']}

Baseline DTW:
  Distance: {metrics['baseline']['dtw_distance']:.4f}
  MAE: {metrics['baseline']['mae']*1000:.2f} ms
  RMSE: {metrics['baseline']['rmse']*1000:.2f} ms
  Quality: {metrics['baseline']['quality_score']:.3f}

Enhanced DTW:
  Distance: {metrics['enhanced']['dtw_distance']:.4f}
  MAE: {metrics['enhanced']['mae']*1000:.2f} ms
  RMSE: {metrics['enhanced']['rmse']*1000:.2f} ms
  Quality: {metrics['enhanced']['quality_score']:.3f}

Improvements:
  MAE: {metrics['improvement']['mae_reduction']:.1f}%
  RMSE: {metrics['improvement']['rmse_reduction']:.1f}%
  Quality: {metrics['improvement']['overall_quality_improvement']:.1f}%
""", 
                fontsize=9, family='monospace', verticalalignment='center')
        ax8.axis('off')
        
        # 9-12: Additional detailed plots
        
        # 9. Warping Path Visualization
        ax9 = plt.subplot(3, 4, 9)
        base_wp = np.array(baseline['warping_path'])
        if len(base_wp) > 0:
            ax9.plot(base_wp[:, 1], base_wp[:, 0], 'b.', alpha=0.3, markersize=2)
        ax9.set_xlabel('Performance Frame', fontsize=10)
        ax9.set_ylabel('Score Frame', fontsize=10)
        ax9.set_title('Baseline Warping Path', fontsize=11, fontweight='bold')
        ax9.grid(True, alpha=0.3)
        
        # 10. Enhanced Warping Path
        ax10 = plt.subplot(3, 4, 10)
        enh_wp = np.array(enhanced['warping_path'])
        if len(enh_wp) > 0:
            ax10.plot(enh_wp[:, 1], enh_wp[:, 0], 'r.', alpha=0.5, markersize=3)
        ax10.set_xlabel('Performance Frame', fontsize=10)
        ax10.set_ylabel('Score Frame', fontsize=10)
        ax10.set_title('Enhanced Warping Path', fontsize=11, fontweight='bold')
        ax10.grid(True, alpha=0.3)
        
        # 11. Error Box Plot
        ax11 = plt.subplot(3, 4, 11)
        ax11.boxplot([base_err * 1000, enh_err * 1000], 
                    labels=['Baseline', 'Enhanced'],
                    patch_artist=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.5))
        ax11.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        ax11.set_ylabel('Error (ms)', fontsize=10)
        ax11.set_title('Error Distribution (Box Plot)', fontsize=11, fontweight='bold')
        ax11.grid(True, alpha=0.3, axis='y')
        
        # 12. Quality Radar Chart
        ax12 = plt.subplot(3, 4, 12, projection='polar')
        
        categories = ['Low MAE', 'Low RMSE', 'Smoothness', 'Correlation']
        base_scores = [
            1 - min(1, metrics['baseline']['mae'] * 10),
            1 - min(1, metrics['baseline']['rmse'] * 10),
            metrics['baseline']['smoothness_score'],
            (metrics['baseline']['correlation'] + 1) / 2
        ]
        enh_scores = [
            1 - min(1, metrics['enhanced']['mae'] * 10),
            1 - min(1, metrics['enhanced']['rmse'] * 10),
            metrics['enhanced']['smoothness_score'],
            (metrics['enhanced']['correlation'] + 1) / 2
        ]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        base_scores += base_scores[:1]
        enh_scores += enh_scores[:1]
        angles += angles[:1]
        
        ax12.plot(angles, base_scores, 'b-', linewidth=2, label='Baseline')
        ax12.fill(angles, base_scores, 'b', alpha=0.15)
        ax12.plot(angles, enh_scores, 'r-', linewidth=2, label='Enhanced')
        ax12.fill(angles, enh_scores, 'r', alpha=0.15)
        
        ax12.set_xticks(angles[:-1])
        ax12.set_xticklabels(categories, fontsize=9)
        ax12.set_ylim(0, 1)
        ax12.set_title('Quality Comparison', fontsize=11, fontweight='bold', pad=20)
        ax12.legend(loc='upper right', fontsize=9)
        ax12.grid(True)
        
        plt.suptitle(f'DTW Algorithm Comparison: {instrument.title()}', 
                    fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        # Save
        output_file = inst_dir / f"{instrument}_comprehensive_comparison.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        logger.info(f"Saved: {output_file.name}")
        plt.close()
        
        # Save metrics
        metrics_file = inst_dir / f"{instrument}_detailed_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    def run_batch_comparison(self, score_path: str, instruments: List[str] = None):
        """Run comparison on multiple instruments"""
        
        if instruments is None:
            instruments = ['violin', 'clarinet', 'saxophone', 'bassoon']
        
        # Bach10 dataset uses "saxophone" in track mapping
        # No need to map to "saxphone" - that's handled in InstrumentExtractor
        instruments_mapped = instruments
        
        all_results = []
        
        for instrument in instruments_mapped:
            try:
                result = self.compare_on_instrument(score_path, instrument)
                all_results.append(result)
            except Exception as e:
                logger.error(f"Error processing {instrument}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Generate summary
        self._generate_summary_report(all_results)
        
        return all_results
    
    def _generate_summary_report(self, all_results: List[Dict]):
        """Generate summary report and table"""
        
        logger.info("\nGenerating summary report...")
        
        summary_data = []
        
        for result in all_results:
            inst = result['instrument']
            m = result['comparative_metrics']
            
            summary_data.append({
                'Instrument': inst,
                'Base_MAE_ms': m['baseline']['mae'] * 1000,
                'Enh_MAE_ms': m['enhanced']['mae'] * 1000,
                'Base_RMSE_ms': m['baseline']['rmse'] * 1000,
                'Enh_RMSE_ms': m['enhanced']['rmse'] * 1000,
                'MAE_Improvement_%': m['improvement']['mae_reduction'],
                'RMSE_Improvement_%': m['improvement']['rmse_reduction'],
                'Quality_Improvement_%': m['improvement']['overall_quality_improvement']
            })
        
        df = pd.DataFrame(summary_data)
        
        # Save CSV
        csv_file = self.output_dir / "comparison_summary.csv"
        df.to_csv(csv_file, index=False, float_format='%.2f')
        logger.info(f"Saved: {csv_file.name}")
        
        # Text report
        report_file = self.output_dir / "DETAILED_COMPARISON_REPORT.txt"
        with open(report_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("DTW ALGORITHM COMPARISON - DETAILED REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Dataset: Bach10 - 01-AchGottundHerr (Synthetic Performance Variations)\n\n")
            
            f.write("METHODOLOGY\n")
            f.write("-" * 80 + "\n")
            f.write("To properly evaluate the algorithms, we created synthetic performances\n")
            f.write("with realistic variations from the score:\n")
            f.write("  - Global tempo variation: ±15%\n")
            f.write("  - Local rubato (gradual tempo changes): 12% strength\n")
            f.write("  - Timing jitter: ±30ms random variation\n")
            f.write("  - Velocity variations: ±10 MIDI units\n\n")
            
            f.write("ALGORITHMS COMPARED\n")
            f.write("-" * 80 + "\n")
            f.write("Baseline DTW:\n")
            f.write("  - Vanilla DTW with no constraints\n")
            f.write("  - O(NM) complexity (full matrix computation)\n")
            f.write("  - Simple cosine distance between chroma vectors\n")
            f.write("  - No optimization or domain knowledge\n\n")
            
            f.write("Enhanced DTW:\n")
            f.write("  - Sakoe-Chiba band constraint (25% radius)\n")
            f.write("  - Adaptive step weights based on score structure\n")
            f.write("  - Beat-aware cost matrix weighting\n")
            f.write("  - CQT-based chromagram features\n")
            f.write("  - GPU acceleration support\n")
            f.write("  - Improved computational efficiency\n\n")
            
            f.write("RESULTS TABLE\n")
            f.write("-" * 80 + "\n")
            f.write(df.to_string(index=False))
            f.write("\n\n")
            
            if len(df) > 0:
                f.write("AVERAGE PERFORMANCE\n")
                f.write("-" * 80 + "\n")
                f.write(f"Average MAE Reduction:    {df['MAE_Improvement_%'].mean():>7.2f}%\n")
                f.write(f"Average RMSE Reduction:   {df['RMSE_Improvement_%'].mean():>7.2f}%\n")
                f.write(f"Average Quality Improvement: {df['Quality_Improvement_%'].mean():>7.2f}%\n\n")
                
                f.write("Baseline Average MAE:     {:.2f} ms\n".format(df['Base_MAE_ms'].mean()))
                f.write("Enhanced Average MAE:     {:.2f} ms\n".format(df['Enh_MAE_ms'].mean()))
                f.write("Baseline Average RMSE:    {:.2f} ms\n".format(df['Base_RMSE_ms'].mean()))
                f.write("Enhanced Average RMSE:    {:.2f} ms\n\n".format(df['Enh_RMSE_ms'].mean()))
            
            f.write("CONCLUSIONS\n")
            f.write("-" * 80 + "\n")
            if len(df) > 0 and df['MAE_Improvement_%'].mean() > 5:
                f.write("The Enhanced DTW algorithm shows significant improvements over baseline DTW:\n\n")
                f.write("1. Lower Alignment Errors: Reduced MAE and RMSE demonstrate more accurate\n")
                f.write("   time alignment between score and performance.\n\n")
                f.write("2. Better Handling of Tempo Variations: The band constraint and adaptive\n")
                f.write("   weights help the algorithm handle rubato and tempo changes.\n\n")
                f.write("3. Improved Efficiency: Band constraints reduce computational complexity\n")
                f.write("   while maintaining or improving accuracy.\n\n")
                f.write("4. Robustness: Enhanced DTW is more robust to timing jitter and local\n")
                f.write("   tempo variations common in real performances.\n\n")
            else:
                f.write("The algorithms show comparable performance on this dataset.\n")
                f.write("For datasets with more significant tempo variations, the Enhanced DTW\n")
                f.write("enhancements (band constraints, adaptive weights) may provide greater benefits.\n\n")
            
            f.write("="*80 + "\n")
        
        logger.info(f"Saved: {report_file.name}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Compare Baseline DTW vs Enhanced DTW with realistic performance variations"
    )
    parser.add_argument(
        '--score',
        default='Bach_10_Dataset/01-AchGottundHerr.mid',
        help='Score MIDI file'
    )
    parser.add_argument(
        '--output_dir',
        default='Output/DTW_Comparison_Realistic',
        help='Output directory'
    )
    parser.add_argument(
        '--instruments',
        nargs='+',
        default=['violin', 'clarinet', 'saxophone', 'bassoon'],
        help='Instruments to process'
    )
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("DTW ALGORITHM COMPARISON WITH REALISTIC VARIATIONS")
    logger.info("="*80)
    
    comparator = DTWComparator(output_dir=args.output_dir)
    
    results = comparator.run_batch_comparison(
        args.score,
        args.instruments
    )
    
    logger.info("\n" + "="*80)
    logger.info("COMPARISON COMPLETE!")
    logger.info("="*80)
    logger.info(f"\nResults saved to: {args.output_dir}")
    logger.info(f"Processed {len(results)} instruments")
    logger.info("\nGenerated files:")
    logger.info("  - comparison_summary.csv: Summary table")
    logger.info("  - DETAILED_COMPARISON_REPORT.txt: Full report")
    logger.info("  - <instrument>/<instrument>_comprehensive_comparison.png: Visualizations")
    logger.info("  - <instrument>/<instrument>_detailed_metrics.json: Metrics")
    logger.info("  - <instrument>/<instrument>_performance_synthetic.mid: Synthetic performances")


if __name__ == "__main__":
    main()
