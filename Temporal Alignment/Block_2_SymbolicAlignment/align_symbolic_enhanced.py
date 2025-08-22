#!/usr/bin/env python3
"""
Enhanced Symbolic Alignment (Block 2) - TuttiBot v0.2
======================================================

Improved version using pretty_midi + DTW for score-performance alignment
without dependency on partitura/parangonar.

Key Improvements:
- Uses pretty_midi for MIDI handling (lighter dependency)
- Implements DTW using scipy or librosa (standard libraries)
- CQT-based feature alignment for better musical alignment
- Robust error handling and fallback mechanisms
- Comprehensive time mapping and visualization

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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSymbolicAligner:
    """Enhanced symbolic alignment using pretty_midi + DTW"""
    
    def __init__(self, 
                 sr: int = 22050,
                 hop_length: int = 512,
                 n_bins: int = 84,
                 bins_per_octave: int = 12,
                 fmin: float = 55.0):
        """
        Initialize the enhanced symbolic aligner
        
        Args:
            sr: Audio sample rate
            hop_length: Hop length for feature extraction
            n_bins: Number of CQT bins
            bins_per_octave: Bins per octave for CQT
            fmin: Minimum frequency for CQT
        """
        self.sr = sr
        self.hop_length = hop_length
        self.n_bins = n_bins
        self.bins_per_octave = bins_per_octave
        self.fmin = fmin
        
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
            
            # Extract notes from score graph
            for node in score_graph.get('nodes', []):
                if 'pitch' in node and 'start_time' in node and 'duration' in node:
                    # Create note
                    note = pretty_midi.Note(
                        velocity=80,
                        pitch=int(node['pitch']),
                        start=float(node['start_time']),
                        end=float(node['start_time'] + node['duration'])
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
        
        # Normalize
        chroma = librosa.util.normalize(chroma, axis=0)
        
        return chroma
    
    def dtw_alignment(self, X: np.ndarray, Y: np.ndarray, 
                      metric: str = 'cosine') -> Tuple[np.ndarray, float]:
        """
        Perform DTW alignment using librosa
        
        Args:
            X: Score features [n_features, n_frames_score]
            Y: Performance features [n_features, n_frames_perf]
            metric: Distance metric for DTW
            
        Returns:
            wp: Warping path array [n_path, 2]
            distance: DTW distance
        """
        try:
            # Use librosa's DTW implementation
            D, wp = librosa.sequence.dtw(X=X.T, Y=Y.T, metric=metric)
            
            # Extract final distance
            distance = D[-1, -1]
            
            logger.info(f"DTW completed: path length={len(wp)}, distance={distance:.4f}")
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
    
    def enhanced_alignment(self, score_midi: pretty_midi.PrettyMIDI,
                          perf_midi: pretty_midi.PrettyMIDI) -> Dict:
        """
        Perform enhanced alignment with multiple feature types
        
        Args:
            score_midi: Score MIDI data
            perf_midi: Performance MIDI data
            
        Returns:
            Alignment results with time mapping and confidence scores
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
            
            # Perform DTW alignment
            wp, distance = self.dtw_alignment(score_chroma, perf_chroma)
            
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
                }
            }
            
            logger.info(f"Alignment completed: confidence={confidence:.3f}")
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
                               output_dir: str = "block_2_enhanced_output") -> Dict:
        """
        Main alignment pipeline
        
        Args:
            score_graph_path: Path to ScoreGraph JSON from Block 0
            performance_midi_path: Path to performance MIDI from Block 1
            output_dir: Output directory for results
            
        Returns:
            Complete alignment results
        """
        try:
            logger.info("=== Enhanced Symbolic Alignment (Block 2) ===")
            
            # Load inputs
            score_graph = self.load_score_graph(score_graph_path)
            perf_midi = self.load_performance_midi(performance_midi_path)
            
            # Convert score to MIDI
            score_midi = self.score_to_midi(score_graph)
            
            # Perform alignment
            alignment_results = self.enhanced_alignment(score_midi, perf_midi)
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
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
                    'performance_midi': performance_midi_path
                },
                'alignment': alignment_results,
                'metadata': {
                    'aligner_params': {
                        'sr': self.sr,
                        'hop_length': self.hop_length,
                        'n_bins': self.n_bins,
                        'bins_per_octave': self.bins_per_octave,
                        'fmin': self.fmin
                    }
                }
            }
            
            results_file = output_path / "enhanced_alignment_complete.json"
            with open(results_file, 'w') as f:
                json.dump(final_results, f, indent=2)
            
            logger.info(f"=== Alignment Complete! Results in {output_path} ===")
            return final_results
            
        except Exception as e:
            logger.error(f"Alignment pipeline failed: {e}")
            raise

def main():
    """Example usage of Enhanced Symbolic Aligner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Symbolic Alignment (Block 2)')
    parser.add_argument('score_graph', help='Path to ScoreGraph JSON from Block 0')
    parser.add_argument('performance_midi', help='Path to performance MIDI from Block 1')
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
            args.output
        )
        
        print(f"\n✅ Enhanced alignment completed successfully!")
        print(f"📊 Confidence: {results['alignment']['confidence']:.3f}")
        print(f"📏 DTW Distance: {results['alignment']['dtw_distance']:.4f}")
        print(f"⏱️  Score Duration: {results['alignment']['score_duration']:.2f}s")
        print(f"🎵 Performance Duration: {results['alignment']['perf_duration']:.2f}s")
        print(f"📁 Results saved to: {args.output}")
        
    except Exception as e:
        print(f"❌ Alignment failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
