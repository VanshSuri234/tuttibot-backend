#!/usr/bin/env python3
"""
Algorithm Comparison: Baseline DTW vs PQG-A2SA

Implements the comparison plan to evaluate PQG-A2SA against standard DTW.
Generates comprehensive comparison plots and metrics.

Usage:
    python3 compare_algorithms.py audio.wav score.mid output_name
    
Example:
    python3 compare_algorithms.py data/bach10/01-AchGottundHerr/01-AchGottundHerr.wav \\
                                   data/bach10/01-AchGottundHerr/01-AchGottundHerr.mid \\
                                   bach01_comparison
"""

import sys
import os
import numpy as np
import librosa
import pretty_midi
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Import our modules
from src.features import AudioFeatures
from src.score_parser import ScoreParser
from src.pipeline import PQGAligner
from src.baseline_dtw import BaselineDTWAligner, extract_note_times
from src.evaluation import Evaluator


class AlgorithmComparison:
    """
    Compare Baseline DTW vs PQG-A2SA alignment algorithms.
    """
    
    def __init__(self, audio_path, score_path, output_prefix):
        """
        Initialize comparison.
        
        Args:
            audio_path: Path to audio file
            score_path: Path to MIDI/MusicXML score
            output_prefix: Prefix for output files
        """
        self.audio_path = audio_path
        self.score_path = score_path
        self.output_prefix = output_prefix
        
        # Create output directory
        self.output_dir = Path("comparison_results")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.audio_features = AudioFeatures()
        self.score_parser = ScoreParser()
        self.baseline_aligner = BaselineDTWAligner()
        self.pqg_aligner = PQGAligner()
        self.evaluator = Evaluator()
        
        # Storage
        self.audio_chroma = None
        self.score_chroma = None
        self.score_notes = None
        self.ground_truth = None
        self.baseline_results = None
        self.pqg_results = None
        
    def run_comparison(self):
        """
        Run complete comparison pipeline.
        """
        print("\n" + "="*70)
        print("ALGORITHM COMPARISON: Baseline DTW vs PQG-A2SA")
        print("="*70)
        
        # Step 1: Load and extract features
        print("\n[Step 1/6] Feature Extraction")
        self._extract_features()
        
        # Step 2: Run baseline DTW
        print("\n[Step 2/6] Running Baseline DTW")
        self._run_baseline()
        
        # Step 3: Run PQG-A2SA
        print("\n[Step 3/6] Running PQG-A2SA")
        self._run_pqg()
        
        # Step 4: Compute metrics
        print("\n[Step 4/6] Computing Evaluation Metrics")
        self.metrics = self._compute_metrics()
        
        # Step 5: Generate plots
        print("\n[Step 5/6] Generating Comparison Plots")
        self._generate_plots()
        
        # Step 6: Save summary
        print("\n[Step 6/6] Saving Summary Report")
        self._save_summary(self.metrics)
        
        print("\n" + "="*70)
        print("COMPARISON COMPLETE!")
        print(f"Results saved to: {self.output_dir}/")
        print("="*70 + "\n")
        
        return self.metrics
    
    def _extract_features(self):
        """
        Extract features from audio and score (same for both methods).
        """
        print(f"  Loading audio: {self.audio_path}")
        y, sr = librosa.load(self.audio_path, sr=22050)
        print(f"  Audio: {len(y)/sr:.2f}s, sr={sr}")
        
        print(f"  Loading score: {self.score_path}")
        midi = pretty_midi.PrettyMIDI(self.score_path)
        print(f"  Score: {len(midi.instruments)} instruments")
        
        # Extract audio chroma
        print("  Extracting audio chroma...")
        chroma, times = self.audio_features.extract_chroma_frames(y, sr)
        self.audio_chroma = chroma.T  # Transpose to (frames × 12)
        print(f"    Audio chroma: {self.audio_chroma.shape}")
        
        # Extract score chroma and notes
        print("  Extracting score features...")
        chords = self.score_parser.extract_chords(midi)
        instruments_data = self.score_parser.extract_instrument_notes(midi)
        
        # Convert to dict format for compatibility
        self.score_notes = {}
        for inst in instruments_data:
            inst_name = inst['name']
            # Rename 'onset'/'offset' to 'onset_time'/'offset_time' for compatibility
            notes = []
            for n in inst['notes']:
                notes.append({
                    'pitch': n['pitch'],
                    'onset_time': n['onset'],
                    'offset_time': n['offset'],
                    'velocity': n['velocity'],
                    'duration': n['duration']
                })
            self.score_notes[inst_name] = notes
        
        # Build score chroma from chords
        self.score_chroma = np.zeros((len(chords), 12))
        for i, chord in enumerate(chords):
            for pitch in chord['pitches']:
                self.score_chroma[i, pitch % 12] += 1
        # Normalize
        row_sums = self.score_chroma.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        self.score_chroma = self.score_chroma / row_sums
        
        print(f"    Score chroma: {self.score_chroma.shape}")
        
        # Add score indices to notes
        event_idx = 0
        for inst_notes in self.score_notes.values():
            for note in inst_notes:
                note['score_index'] = event_idx
                event_idx += 1
        
        # Prepare ground truth (from MIDI)
        self.ground_truth = {}
        for inst_name, notes in self.score_notes.items():
            self.ground_truth[inst_name] = [
                {
                    'pitch': n['pitch'],
                    'onset_time': n['onset_time'],
                    'offset_time': n['offset_time']
                }
                for n in notes
            ]
        
        print("  Feature extraction complete!")
    
    def _run_baseline(self):
        """
        Run baseline DTW alignment.
        """
        # Flatten score notes for baseline
        all_score_notes = []
        for inst_notes in self.score_notes.values():
            all_score_notes.extend(inst_notes)
        all_score_notes.sort(key=lambda x: x['onset_time'])
        
        # Run baseline alignment
        self.baseline_results = self.baseline_aligner.align(
            self.audio_chroma,
            self.score_chroma,
            all_score_notes
        )
        
        # Count aligned notes
        total_notes = sum(
            len(notes) for inst, notes in self.baseline_results.items()
            if inst not in ['dtw_cost_matrix', 'dtw_path']
        )
        print(f"  Aligned {total_notes} notes")
    
    def _run_pqg(self):
        """
        Run PQG-A2SA alignment.
        """
        self.pqg_results = self.pqg_aligner.align(
            self.audio_path,
            self.score_path
        )
        
        # Count aligned notes
        total_notes = sum(len(notes) for notes in self.pqg_results.values())
        print(f"  Aligned {total_notes} notes")
    
    def _compute_metrics(self):
        """
        Compute evaluation metrics for both methods.
        
        Returns:
            metrics: Dictionary with comparison metrics
        """
        # Extract note timings
        baseline_onsets, baseline_offsets = extract_note_times(self.baseline_results)
        pqg_onsets, pqg_offsets = extract_note_times(self.pqg_results)
        gt_onsets, gt_offsets = extract_note_times(self.ground_truth)
        
        # Ensure arrays are same length (match by number)
        min_len = min(len(baseline_onsets), len(pqg_onsets), len(gt_onsets))
        baseline_onsets = baseline_onsets[:min_len]
        baseline_offsets = baseline_offsets[:min_len]
        pqg_onsets = pqg_onsets[:min_len]
        pqg_offsets = pqg_offsets[:min_len]
        gt_onsets = gt_onsets[:min_len]
        gt_offsets = gt_offsets[:min_len]
        
        # Compute errors for baseline
        baseline_onset_errors = np.abs(baseline_onsets - gt_onsets)
        baseline_offset_errors = np.abs(baseline_offsets - gt_offsets)
        baseline_mne = np.mean(baseline_onset_errors)
        baseline_mfe = np.mean(baseline_offset_errors)
        
        # Compute errors for PQG-A2SA
        pqg_onset_errors = np.abs(pqg_onsets - gt_onsets)
        pqg_offset_errors = np.abs(pqg_offsets - gt_offsets)
        pqg_mne = np.mean(pqg_onset_errors)
        pqg_mfe = np.mean(pqg_offset_errors)
        
        # Compute improvement
        onset_improvement = ((baseline_mne - pqg_mne) / baseline_mne * 100) if baseline_mne > 0 else 0
        offset_improvement = ((baseline_mfe - pqg_mfe) / baseline_mfe * 100) if baseline_mfe > 0 else 0
        
        # Compute alignment rates
        thresholds = [0.03, 0.06, 0.09, 0.12, 0.15, 0.18, 0.20]  # 30-200ms
        baseline_onset_rates = [
            np.mean(baseline_onset_errors <= t) * 100 for t in thresholds
        ]
        baseline_offset_rates = [
            np.mean(baseline_offset_errors <= t) * 100 for t in thresholds
        ]
        pqg_onset_rates = [
            np.mean(pqg_onset_errors <= t) * 100 for t in thresholds
        ]
        pqg_offset_rates = [
            np.mean(pqg_offset_errors <= t) * 100 for t in thresholds
        ]
        
        metrics = {
            'baseline': {
                'MNE': baseline_mne,
                'MFE': baseline_mfe,
                'onset_errors': baseline_onset_errors,
                'offset_errors': baseline_offset_errors,
                'onset_rates': baseline_onset_rates,
                'offset_rates': baseline_offset_rates,
                'onsets': baseline_onsets,
                'offsets': baseline_offsets
            },
            'pqg': {
                'MNE': pqg_mne,
                'MFE': pqg_mfe,
                'onset_errors': pqg_onset_errors,
                'offset_errors': pqg_offset_errors,
                'onset_rates': pqg_onset_rates,
                'offset_rates': pqg_offset_rates,
                'onsets': pqg_onsets,
                'offsets': pqg_offsets
            },
            'ground_truth': {
                'onsets': gt_onsets,
                'offsets': gt_offsets
            },
            'improvement': {
                'onset': onset_improvement,
                'offset': offset_improvement
            },
            'thresholds': thresholds,
            'n_notes': min_len
        }
        
        print(f"\n  Baseline DTW:")
        print(f"    MNE: {baseline_mne*1000:.2f} ms")
        print(f"    MFE: {baseline_mfe*1000:.2f} ms")
        print(f"\n  PQG-A2SA:")
        print(f"    MNE: {pqg_mne*1000:.2f} ms")
        print(f"    MFE: {pqg_mfe*1000:.2f} ms")
        print(f"\n  Improvement:")
        print(f"    Onset: {onset_improvement:+.1f}%")
        print(f"    Offset: {offset_improvement:+.1f}%")
        
        return metrics
    
    def _generate_plots(self):
        """
        Generate all comparison plots.
        """
        # Set publication style
        plt.style.use('seaborn-v0_8-paper')
        sns.set_palette("husl")
        
        # Generate each plot
        self._plot_dtw_cost_matrix()
        self._plot_error_histograms()
        self._plot_error_line_plots()
        self._plot_alignment_scatter()
        self._plot_alignment_rates()
        self._plot_summary_comparison()
        
        print(f"  Generated 6 comparison plots")
    
    def _plot_dtw_cost_matrix(self):
        """
        Plot DTW cost matrix with both alignment paths.
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Get cost matrix from baseline
        D = self.baseline_results.get('dtw_cost_matrix')
        wp_base = self.baseline_results.get('dtw_path')
        
        if D is not None and wp_base is not None:
            # Plot cost matrix
            im = ax.imshow(D, origin='lower', cmap='gray_r', aspect='auto')
            plt.colorbar(im, ax=ax, label='Cost')
            
            # Extract path coordinates
            base_i = [p[0] for p in wp_base]
            base_j = [p[1] for p in wp_base]
            
            # Plot baseline path
            ax.plot(base_j, base_i, 'r-', linewidth=2, alpha=0.7, label='Baseline DTW')
            
            # Note: PQG-A2SA doesn't store full DTW path, so we show only baseline
            # In a full implementation, we'd extract PQG's alignment path
            
            ax.set_xlabel('Audio Frames', fontsize=12)
            ax.set_ylabel('Score Events', fontsize=12)
            ax.set_title('DTW Cost Matrix and Alignment Path', fontsize=14, fontweight='bold')
            ax.legend(loc='upper left', fontsize=10)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / f"{self.output_prefix}_dtw_cost_matrix.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_error_histograms(self):
        """
        Plot onset and offset error histograms.
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Get errors from stored metrics
        baseline_onset_errors = self.metrics['baseline']['onset_errors'] * 1000  # Convert to ms
        baseline_offset_errors = self.metrics['baseline']['offset_errors'] * 1000
        pqg_onset_errors = self.metrics['pqg']['onset_errors'] * 1000
        pqg_offset_errors = self.metrics['pqg']['offset_errors'] * 1000
        
        # Onset errors - overlaid
        axes[0, 0].hist(baseline_onset_errors, bins=50, alpha=0.6, 
                       color='red', label='Baseline DTW', edgecolor='black')
        axes[0, 0].hist(pqg_onset_errors, bins=50, alpha=0.6,
                       color='blue', label='PQG-A2SA', edgecolor='black')
        axes[0, 0].axvline(np.mean(baseline_onset_errors), color='red', 
                          linestyle='--', linewidth=2, label=f'Baseline Mean: {np.mean(baseline_onset_errors):.1f}ms')
        axes[0, 0].axvline(np.mean(pqg_onset_errors), color='blue',
                          linestyle='--', linewidth=2, label=f'PQG Mean: {np.mean(pqg_onset_errors):.1f}ms')
        axes[0, 0].set_xlabel('Onset Error (ms)', fontsize=11)
        axes[0, 0].set_ylabel('Count', fontsize=11)
        axes[0, 0].set_title('Onset Error Distribution (Overlaid)', fontsize=12, fontweight='bold')
        axes[0, 0].legend(fontsize=9)
        axes[0, 0].grid(True, alpha=0.3)
        
        # Offset errors - overlaid
        axes[0, 1].hist(baseline_offset_errors, bins=50, alpha=0.6,
                       color='red', label='Baseline DTW', edgecolor='black')
        axes[0, 1].hist(pqg_offset_errors, bins=50, alpha=0.6,
                       color='blue', label='PQG-A2SA', edgecolor='black')
        axes[0, 1].axvline(np.mean(baseline_offset_errors), color='red',
                          linestyle='--', linewidth=2, label=f'Baseline Mean: {np.mean(baseline_offset_errors):.1f}ms')
        axes[0, 1].axvline(np.mean(pqg_offset_errors), color='blue',
                          linestyle='--', linewidth=2, label=f'PQG Mean: {np.mean(pqg_offset_errors):.1f}ms')
        axes[0, 1].set_xlabel('Offset Error (ms)', fontsize=11)
        axes[0, 1].set_ylabel('Count', fontsize=11)
        axes[0, 1].set_title('Offset Error Distribution (Overlaid)', fontsize=12, fontweight='bold')
        axes[0, 1].legend(fontsize=9)
        axes[0, 1].grid(True, alpha=0.3)
        
        # Onset errors - side by side
        axes[1, 0].hist(baseline_onset_errors, bins=40, alpha=0.8,
                       color='red', label='Baseline DTW', edgecolor='black')
        axes[1, 0].set_xlabel('Onset Error (ms)', fontsize=11)
        axes[1, 0].set_ylabel('Count', fontsize=11)
        axes[1, 0].set_title('Baseline DTW - Onset Errors', fontsize=12, fontweight='bold')
        axes[1, 0].legend(fontsize=9)
        axes[1, 0].grid(True, alpha=0.3)
        
        ax_twin = axes[1, 0].twinx()
        ax_twin.hist(pqg_onset_errors, bins=40, alpha=0.8,
                    color='blue', label='PQG-A2SA', edgecolor='black')
        ax_twin.set_ylabel('Count (PQG-A2SA)', fontsize=11)
        ax_twin.legend(fontsize=9, loc='upper right')
        
        # Offset errors - side by side
        axes[1, 1].hist(baseline_offset_errors, bins=40, alpha=0.8,
                       color='red', label='Baseline DTW', edgecolor='black')
        axes[1, 1].set_xlabel('Offset Error (ms)', fontsize=11)
        axes[1, 1].set_ylabel('Count', fontsize=11)
        axes[1, 1].set_title('Baseline DTW - Offset Errors', fontsize=12, fontweight='bold')
        axes[1, 1].legend(fontsize=9)
        axes[1, 1].grid(True, alpha=0.3)
        
        ax_twin2 = axes[1, 1].twinx()
        ax_twin2.hist(pqg_offset_errors, bins=40, alpha=0.8,
                     color='blue', label='PQG-A2SA', edgecolor='black')
        ax_twin2.set_ylabel('Count (PQG-A2SA)', fontsize=11)
        ax_twin2.legend(fontsize=9, loc='upper right')
        
        plt.tight_layout()
        output_path = self.output_dir / f"{self.output_prefix}_error_histograms.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_error_line_plots(self):
        """
        Plot per-note error line plots.
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        baseline_onset_errors = self.metrics['baseline']['onset_errors'] * 1000
        baseline_offset_errors = self.metrics['baseline']['offset_errors'] * 1000
        pqg_onset_errors = self.metrics['pqg']['onset_errors'] * 1000
        pqg_offset_errors = self.metrics['pqg']['offset_errors'] * 1000
        
        note_indices = np.arange(len(baseline_onset_errors))
        
        # Onset errors
        axes[0].plot(note_indices, baseline_onset_errors, 'r--', 
                    linewidth=1.5, alpha=0.7, label='Baseline DTW', marker='o', markersize=3)
        axes[0].plot(note_indices, pqg_onset_errors, 'b-',
                    linewidth=1.5, alpha=0.7, label='PQG-A2SA', marker='s', markersize=3)
        axes[0].set_xlabel('Note Index', fontsize=12)
        axes[0].set_ylabel('Onset Error (ms)', fontsize=12)
        axes[0].set_title('Per-Note Onset Errors', fontsize=14, fontweight='bold')
        axes[0].legend(fontsize=10)
        axes[0].grid(True, alpha=0.3)
        
        # Offset errors
        axes[1].plot(note_indices, baseline_offset_errors, 'r--',
                    linewidth=1.5, alpha=0.7, label='Baseline DTW', marker='o', markersize=3)
        axes[1].plot(note_indices, pqg_offset_errors, 'b-',
                    linewidth=1.5, alpha=0.7, label='PQG-A2SA', marker='s', markersize=3)
        axes[1].set_xlabel('Note Index', fontsize=12)
        axes[1].set_ylabel('Offset Error (ms)', fontsize=12)
        axes[1].set_title('Per-Note Offset Errors', fontsize=14, fontweight='bold')
        axes[1].legend(fontsize=10)
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / f"{self.output_prefix}_error_lines.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_alignment_scatter(self):
        """
        Plot alignment scatter plots (predicted vs ground truth).
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        
        gt_onsets = self.metrics['ground_truth']['onsets']
        gt_offsets = self.metrics['ground_truth']['offsets']
        baseline_onsets = self.metrics['baseline']['onsets']
        baseline_offsets = self.metrics['baseline']['offsets']
        pqg_onsets = self.metrics['pqg']['onsets']
        pqg_offsets = self.metrics['pqg']['offsets']
        
        # Baseline - Onsets
        axes[0, 0].scatter(gt_onsets, baseline_onsets, c='red', alpha=0.6, s=30, edgecolor='black', linewidth=0.5)
        axes[0, 0].plot([gt_onsets.min(), gt_onsets.max()], 
                       [gt_onsets.min(), gt_onsets.max()], 
                       'k--', linewidth=2, label='Ideal (y=x)')
        axes[0, 0].set_xlabel('Ground Truth Onset (s)', fontsize=11)
        axes[0, 0].set_ylabel('Predicted Onset (s)', fontsize=11)
        axes[0, 0].set_title('Baseline DTW - Onset Alignment', fontsize=12, fontweight='bold')
        axes[0, 0].legend(fontsize=9)
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_aspect('equal', adjustable='box')
        
        # Baseline - Offsets
        axes[0, 1].scatter(gt_offsets, baseline_offsets, c='red', alpha=0.6, s=30, edgecolor='black', linewidth=0.5)
        axes[0, 1].plot([gt_offsets.min(), gt_offsets.max()],
                       [gt_offsets.min(), gt_offsets.max()],
                       'k--', linewidth=2, label='Ideal (y=x)')
        axes[0, 1].set_xlabel('Ground Truth Offset (s)', fontsize=11)
        axes[0, 1].set_ylabel('Predicted Offset (s)', fontsize=11)
        axes[0, 1].set_title('Baseline DTW - Offset Alignment', fontsize=12, fontweight='bold')
        axes[0, 1].legend(fontsize=9)
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_aspect('equal', adjustable='box')
        
        # PQG-A2SA - Onsets
        axes[1, 0].scatter(gt_onsets, pqg_onsets, c='blue', alpha=0.6, s=30, edgecolor='black', linewidth=0.5)
        axes[1, 0].plot([gt_onsets.min(), gt_onsets.max()],
                       [gt_onsets.min(), gt_onsets.max()],
                       'k--', linewidth=2, label='Ideal (y=x)')
        axes[1, 0].set_xlabel('Ground Truth Onset (s)', fontsize=11)
        axes[1, 0].set_ylabel('Predicted Onset (s)', fontsize=11)
        axes[1, 0].set_title('PQG-A2SA - Onset Alignment', fontsize=12, fontweight='bold')
        axes[1, 0].legend(fontsize=9)
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_aspect('equal', adjustable='box')
        
        # PQG-A2SA - Offsets
        axes[1, 1].scatter(gt_offsets, pqg_offsets, c='blue', alpha=0.6, s=30, edgecolor='black', linewidth=0.5)
        axes[1, 1].plot([gt_offsets.min(), gt_offsets.max()],
                       [gt_offsets.min(), gt_offsets.max()],
                       'k--', linewidth=2, label='Ideal (y=x)')
        axes[1, 1].set_xlabel('Ground Truth Offset (s)', fontsize=11)
        axes[1, 1].set_ylabel('Predicted Offset (s)', fontsize=11)
        axes[1, 1].set_title('PQG-A2SA - Offset Alignment', fontsize=12, fontweight='bold')
        axes[1, 1].legend(fontsize=9)
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_aspect('equal', adjustable='box')
        
        plt.tight_layout()
        output_path = self.output_dir / f"{self.output_prefix}_alignment_scatter.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_alignment_rates(self):
        """
        Plot alignment rates at different thresholds.
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        thresholds_ms = [t * 1000 for t in self.metrics['thresholds']]
        baseline_onset_rates = self.metrics['baseline']['onset_rates']
        baseline_offset_rates = self.metrics['baseline']['offset_rates']
        pqg_onset_rates = self.metrics['pqg']['onset_rates']
        pqg_offset_rates = self.metrics['pqg']['offset_rates']
        
        x = np.arange(len(thresholds_ms))
        width = 0.35
        
        # Onset rates
        axes[0].bar(x - width/2, baseline_onset_rates, width, 
                   label='Baseline DTW', color='red', alpha=0.7, edgecolor='black')
        axes[0].bar(x + width/2, pqg_onset_rates, width,
                   label='PQG-A2SA', color='blue', alpha=0.7, edgecolor='black')
        axes[0].set_xlabel('Error Threshold (ms)', fontsize=12)
        axes[0].set_ylabel('Alignment Rate (%)', fontsize=12)
        axes[0].set_title('Onset Alignment Rates', fontsize=14, fontweight='bold')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels([f'{int(t)}' for t in thresholds_ms])
        axes[0].legend(fontsize=10)
        axes[0].grid(True, alpha=0.3, axis='y')
        axes[0].set_ylim([0, 105])
        
        # Offset rates
        axes[1].bar(x - width/2, baseline_offset_rates, width,
                   label='Baseline DTW', color='red', alpha=0.7, edgecolor='black')
        axes[1].bar(x + width/2, pqg_offset_rates, width,
                   label='PQG-A2SA', color='blue', alpha=0.7, edgecolor='black')
        axes[1].set_xlabel('Error Threshold (ms)', fontsize=12)
        axes[1].set_ylabel('Alignment Rate (%)', fontsize=12)
        axes[1].set_title('Offset Alignment Rates', fontsize=14, fontweight='bold')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels([f'{int(t)}' for t in thresholds_ms])
        axes[1].legend(fontsize=10)
        axes[1].grid(True, alpha=0.3, axis='y')
        axes[1].set_ylim([0, 105])
        
        plt.tight_layout()
        output_path = self.output_dir / f"{self.output_prefix}_alignment_rates.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_summary_comparison(self):
        """
        Plot summary comparison bar chart.
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        baseline_mne = self.metrics['baseline']['MNE'] * 1000
        baseline_mfe = self.metrics['baseline']['MFE'] * 1000
        pqg_mne = self.metrics['pqg']['MNE'] * 1000
        pqg_mfe = self.metrics['pqg']['MFE'] * 1000
        
        # MNE and MFE comparison
        methods = ['Baseline\nDTW', 'PQG-A2SA']
        mne_values = [baseline_mne, pqg_mne]
        mfe_values = [baseline_mfe, pqg_mfe]
        
        x = np.arange(len(methods))
        width = 0.35
        
        axes[0].bar(x - width/2, mne_values, width, label='MNE (Onset)', 
                   color='orange', alpha=0.8, edgecolor='black', linewidth=1.5)
        axes[0].bar(x + width/2, mfe_values, width, label='MFE (Offset)',
                   color='purple', alpha=0.8, edgecolor='black', linewidth=1.5)
        axes[0].set_ylabel('Mean Error (ms)', fontsize=12)
        axes[0].set_title('Mean Note/Frame Errors', fontsize=14, fontweight='bold')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(methods, fontsize=11)
        axes[0].legend(fontsize=10)
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for i, (mne, mfe) in enumerate(zip(mne_values, mfe_values)):
            axes[0].text(i - width/2, mne + 5, f'{mne:.1f}', 
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
            axes[0].text(i + width/2, mfe + 5, f'{mfe:.1f}',
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Improvement percentages
        onset_improvement = self.metrics['improvement']['onset']
        offset_improvement = self.metrics['improvement']['offset']
        
        improvements = [onset_improvement, offset_improvement]
        labels = ['Onset\nImprovement', 'Offset\nImprovement']
        colors = ['green' if x > 0 else 'red' for x in improvements]
        
        axes[1].bar(labels, improvements, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        axes[1].set_ylabel('Improvement (%)', fontsize=12)
        axes[1].set_title('PQG-A2SA Improvement over Baseline', fontsize=14, fontweight='bold')
        axes[1].axhline(y=0, color='black', linestyle='-', linewidth=1)
        axes[1].grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for i, imp in enumerate(improvements):
            axes[1].text(i, imp + (2 if imp > 0 else -2), f'{imp:+.1f}%',
                        ha='center', va='bottom' if imp > 0 else 'top',
                        fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        output_path = self.output_dir / f"{self.output_prefix}_summary.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _save_summary(self, metrics):
        """
        Save text summary of comparison.
        
        Args:
            metrics: Computed metrics dictionary
        """
        output_path = self.output_dir / f"{self.output_prefix}_summary.txt"
        
        with open(output_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("ALGORITHM COMPARISON SUMMARY\n")
            f.write("Baseline DTW vs PQG-A2SA\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Audio: {self.audio_path}\n")
            f.write(f"Score: {self.score_path}\n")
            f.write(f"Total Notes: {metrics['n_notes']}\n\n")
            
            f.write("-"*70 + "\n")
            f.write("MEAN ERRORS\n")
            f.write("-"*70 + "\n\n")
            
            baseline_mne = metrics['baseline']['MNE'] * 1000
            baseline_mfe = metrics['baseline']['MFE'] * 1000
            pqg_mne = metrics['pqg']['MNE'] * 1000
            pqg_mfe = metrics['pqg']['MFE'] * 1000
            
            f.write(f"Baseline DTW:\n")
            f.write(f"  Mean Note Error (MNE):  {baseline_mne:8.2f} ms\n")
            f.write(f"  Mean Frame Error (MFE): {baseline_mfe:8.2f} ms\n\n")
            
            f.write(f"PQG-A2SA:\n")
            f.write(f"  Mean Note Error (MNE):  {pqg_mne:8.2f} ms\n")
            f.write(f"  Mean Frame Error (MFE): {pqg_mfe:8.2f} ms\n\n")
            
            onset_imp = metrics['improvement']['onset']
            offset_imp = metrics['improvement']['offset']
            
            f.write(f"Improvement (PQG-A2SA over Baseline):\n")
            f.write(f"  Onset Error:  {onset_imp:+7.2f}%\n")
            f.write(f"  Offset Error: {offset_imp:+7.2f}%\n\n")
            
            f.write("-"*70 + "\n")
            f.write("ALIGNMENT RATES\n")
            f.write("-"*70 + "\n\n")
            
            thresholds_ms = [t * 1000 for t in metrics['thresholds']]
            
            f.write("Onset Alignment Rates:\n")
            f.write(f"{'Threshold':<12} {'Baseline DTW':<15} {'PQG-A2SA':<15} {'Difference':<12}\n")
            f.write("-"*60 + "\n")
            for t, b_rate, p_rate in zip(thresholds_ms, 
                                         metrics['baseline']['onset_rates'],
                                         metrics['pqg']['onset_rates']):
                diff = p_rate - b_rate
                f.write(f"≤ {t:5.0f} ms   {b_rate:6.2f}%         {p_rate:6.2f}%         {diff:+6.2f}%\n")
            
            f.write("\n")
            f.write("Offset Alignment Rates:\n")
            f.write(f"{'Threshold':<12} {'Baseline DTW':<15} {'PQG-A2SA':<15} {'Difference':<12}\n")
            f.write("-"*60 + "\n")
            for t, b_rate, p_rate in zip(thresholds_ms,
                                         metrics['baseline']['offset_rates'],
                                         metrics['pqg']['offset_rates']):
                diff = p_rate - b_rate
                f.write(f"≤ {t:5.0f} ms   {b_rate:6.2f}%         {p_rate:6.2f}%         {diff:+6.2f}%\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("INTERPRETATION\n")
            f.write("="*70 + "\n\n")
            
            if onset_imp > 0:
                f.write("✓ PQG-A2SA shows improved onset alignment over baseline DTW.\n")
            else:
                f.write("✗ Baseline DTW performs better for onset alignment.\n")
            
            if offset_imp > 0:
                f.write("✓ PQG-A2SA shows improved offset alignment over baseline DTW.\n")
            else:
                f.write("✗ Baseline DTW performs better for offset alignment.\n")
            
            f.write("\nKey advantages of PQG-A2SA:\n")
            f.write("- Variable-interval DTW handles tempo variations better\n")
            f.write("- IOI-guided refinement improves local alignment\n")
            f.write("- Articulation detection refines note boundaries\n")
            f.write("- NMF-based source separation handles polyphonic music\n\n")
            
            f.write("="*70 + "\n")
        
        print(f"  Summary saved to: {output_path}")


def main():
    """Main entry point."""
    if len(sys.argv) != 4:
        print("Usage: python3 compare_algorithms.py <audio.wav> <score.mid> <output_name>")
        print("\nExample:")
        print("  python3 compare_algorithms.py data/bach10/01/audio.wav data/bach10/01/score.mid bach01")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    score_path = sys.argv[2]
    output_prefix = sys.argv[3]
    
    # Verify files exist
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found: {audio_path}")
        sys.exit(1)
    if not os.path.exists(score_path):
        print(f"Error: Score file not found: {score_path}")
        sys.exit(1)
    
    # Run comparison
    comparison = AlgorithmComparison(audio_path, score_path, output_prefix)
    comparison.metrics = {}  # Initialize for plot methods
    metrics = comparison.run_comparison()
    comparison.metrics = metrics  # Store for plotting
    
    print("\n✅ Comparison complete!")
    print(f"\nGenerated files in comparison_results/:")
    print(f"  - {output_prefix}_dtw_cost_matrix.png")
    print(f"  - {output_prefix}_error_histograms.png")
    print(f"  - {output_prefix}_error_lines.png")
    print(f"  - {output_prefix}_alignment_scatter.png")
    print(f"  - {output_prefix}_alignment_rates.png")
    print(f"  - {output_prefix}_summary.png")
    print(f"  - {output_prefix}_summary.txt")


if __name__ == "__main__":
    main()
