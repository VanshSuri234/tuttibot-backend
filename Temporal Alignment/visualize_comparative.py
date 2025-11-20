"""
Enhanced Comparative Visualizations for Temporal Alignment
Shows clear "Expected vs Actual" comparisons with proper x/y axis plots
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import pretty_midi


class ComparativeVisualizer:
    """Generate comparative visualizations showing score vs performance"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data (will be set by load_data method)
        self.score_midi = None
        self.perf_midi = None
        self.scoregraph = None
        self.beats = None
        self.context = None
        self.alignment = None
        
    def load_data(self,
                  score_midi_path: str,
                  perf_midi_path: str,
                  scoregraph_path: str,
                  beats_path: str,
                  context_path: str,
                  alignment_path: str):
        """Load all required data files"""
        
        # Load MIDI files
        self.score_midi = pretty_midi.PrettyMIDI(score_midi_path)
        self.perf_midi = pretty_midi.PrettyMIDI(perf_midi_path)
        
        # Load JSON files
        with open(scoregraph_path, 'r') as f:
            self.scoregraph = json.load(f)
        with open(beats_path, 'r') as f:
            self.beats = json.load(f)
        with open(context_path, 'r') as f:
            self.context = json.load(f)
        with open(alignment_path, 'r') as f:
            self.alignment = json.load(f)
    
    def plot_pitch_roll_comparison(self, save_name: str = "comp_1_pitch_roll.png"):
        """
        Plot pitch trajectory comparison with continuous lines OVERLAID
        Shows both melodies on the same plot for direct comparison
        """
        # Get score notes
        score_notes = []
        for instrument in self.score_midi.instruments:
            for note in instrument.notes:
                score_notes.append({
                    'start': note.start,
                    'end': note.end,
                    'pitch': note.pitch,
                    'velocity': note.velocity
                })
        
        # Get performance notes
        perf_notes = []
        for instrument in self.perf_midi.instruments:
            for note in instrument.notes:
                perf_notes.append({
                    'start': note.start,
                    'end': note.end,
                    'pitch': note.pitch,
                    'velocity': note.velocity
                })
        
        # Sort notes by start time
        score_notes.sort(key=lambda x: x['start'])
        perf_notes.sort(key=lambda x: x['start'])
        
        # Create continuous pitch trajectory
        def create_pitch_trajectory(notes, resolution=0.01):
            """Create continuous pitch values at regular time intervals"""
            if not notes:
                return [], []
            
            max_time = max(n['end'] for n in notes)
            time_points = np.arange(0, max_time, resolution)
            pitch_values = np.zeros(len(time_points))
            
            for i, t in enumerate(time_points):
                # Find all notes active at this time
                active_pitches = [n['pitch'] for n in notes if n['start'] <= t < n['end']]
                if active_pitches:
                    # Use average pitch if multiple notes (chord)
                    pitch_values[i] = np.mean(active_pitches)
                else:
                    pitch_values[i] = np.nan  # No note at this time
            
            return time_points, pitch_values
        
        # Generate trajectories
        score_times, score_pitches = create_pitch_trajectory(score_notes)
        perf_times, perf_pitches = create_pitch_trajectory(perf_notes)
        
        # Create single figure with OVERLAID plots
        fig, ax = plt.subplots(1, 1, figsize=(16, 8))
        
        # Get pitch range
        all_pitches = np.concatenate([score_pitches[~np.isnan(score_pitches)], 
                                      perf_pitches[~np.isnan(perf_pitches)]])
        if len(all_pitches) > 0:
            min_pitch = np.min(all_pitches) - 3
            max_pitch = np.max(all_pitches) + 3
        else:
            min_pitch, max_pitch = 60, 80
        
        # Plot SCORE trajectory (thicker, behind, with shading)
        ax.fill_between(score_times, min_pitch, score_pitches, 
                        where=~np.isnan(score_pitches),
                        color='dodgerblue', alpha=0.15, label='_nolegend_')
        
        ax.plot(score_times, score_pitches, color='blue', linewidth=3.5, 
                alpha=0.7, label='Score (Expected)', zorder=2)
        
        # Plot PERFORMANCE trajectory (thinner, on top, with shading)
        ax.fill_between(perf_times, min_pitch, perf_pitches,
                        where=~np.isnan(perf_pitches),
                        color='orangered', alpha=0.15, label='_nolegend_')
        
        ax.plot(perf_times, perf_pitches, color='red', linewidth=2.5, 
                alpha=0.85, label='Performance (Actual)', zorder=3)
        
        # Add markers for clarity
        ax.scatter(score_times[::100], score_pitches[::100], color='darkblue', 
                   s=30, alpha=0.6, zorder=4, edgecolors='white', linewidths=0.5)
        ax.scatter(perf_times[::100], perf_pitches[::100], color='darkred', 
                   s=20, alpha=0.7, zorder=5, edgecolors='white', linewidths=0.5)
        
        # Styling
        ax.set_ylim(min_pitch, max_pitch)
        ax.set_xlabel('Time (seconds)', fontsize=13, fontweight='bold')
        ax.set_ylabel('MIDI Pitch (Note Height)', fontsize=13, fontweight='bold')
        ax.set_title('Pitch Trajectory Comparison: Score vs Performance', 
                     fontsize=15, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        ax.set_facecolor('#fafafa')
        
        # Add pitch labels (note names) on y-axis
        pitch_names = {60: 'C4', 62: 'D4', 64: 'E4', 65: 'F4', 67: 'G4', 69: 'A4', 71: 'B4',
                      72: 'C5', 74: 'D5', 76: 'E5', 77: 'F5', 79: 'G5', 81: 'A5', 83: 'B5',
                      84: 'C6', 86: 'D6', 88: 'E6', 90: 'F6'}
        
        y_ticks = [p for p in range(int(min_pitch), int(max_pitch)+1) if p % 2 == 0]
        ax.set_yticks(y_ticks)
        y_labels = [pitch_names.get(p, str(p)) for p in y_ticks]
        ax.set_yticklabels(y_labels, fontsize=10)
        
        # Legend
        ax.legend(loc='upper right', fontsize=12, framealpha=0.95, 
                 edgecolor='gray', fancybox=True)
        # Legend
        ax.legend(loc='upper right', fontsize=12, framealpha=0.95, 
                 edgecolor='gray', fancybox=True)
        
        # Add statistics box
        stats_text = (
            f'Score notes: {len(score_notes)}\n'
            f'Performance notes: {len(perf_notes)}\n'
            f'Ratio: {len(perf_notes)/len(score_notes):.2f}x\n'
            f'(>1 = harmonics detected)'
        )
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, 
                         edgecolor='orange', linewidth=1.5))
        
        # Add interpretation guide
        interpretation = (
            "HOW TO READ:\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Blue Line = What score says\n"
            "Red Line = What was played\n\n"
            "• Lines overlap = Good match!\n"
            "• Lines diverge = Pitch error\n"
            "• Red more complex = Harmonics\n"
            "• Gaps = Silence\n"
            "• Up/Down = Pitch higher/lower"
        )
        
        ax.text(0.98, 0.02, interpretation, transform=ax.transAxes, fontsize=10,
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.95, 
                         edgecolor='brown', linewidth=1.5),
                family='monospace')
        
        plt.tight_layout()
        output_path = self.output_dir / save_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {save_name}")
    
    def plot_beat_alignment_scatter(self, save_name: str = "comp_2_beat_alignment.png"):
        """
        Scatter plot of score beats vs performance beats
        X-axis: Score beat time (seconds)
        Y-axis: Performance beat time (seconds)
        Diagonal line = perfect tempo match
        """
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Get time mapping
        time_mapping = self.alignment.get('time_mapping', [])
        if not time_mapping:
            print("Warning: No time mapping available")
            return
        
        # Extract score and performance times
        score_times = [m['score_time'] for m in time_mapping]
        perf_times = [m['perf_time'] for m in time_mapping]
        
        # Plot diagonal reference line (perfect tempo)
        max_time = max(max(score_times), max(perf_times))
        ax.plot([0, max_time], [0, max_time], 'k--', linewidth=2, alpha=0.5, label='Perfect tempo (1:1)')
        
        # Plot alignment points
        ax.scatter(score_times, perf_times, c='blue', alpha=0.3, s=10, label='Alignment points')
        
        # Overlay detected beats if available
        if self.beats and 'beats' in self.beats:
            beat_times = [b['t'] for b in self.beats['beats']]
            beat_confs = [b.get('confidence', 0.8) for b in self.beats['beats']]
            
            # Map beat times through alignment (find closest perf time for each beat)
            beat_score_times = []
            for bt in beat_times:
                # Find closest performance time in mapping
                closest_idx = min(range(len(perf_times)), key=lambda i: abs(perf_times[i] - bt))
                beat_score_times.append(score_times[closest_idx])
            
            # Plot beats with size by confidence
            sizes = [c * 100 for c in beat_confs]
            ax.scatter(beat_score_times, beat_times, c='red', alpha=0.6, s=sizes, 
                      edgecolors='darkred', linewidths=1, label='Detected beats', zorder=3)
        
        # Set axis properties
        ax.set_xlim(0, max_time)
        ax.set_ylim(0, max_time)
        ax.set_xlabel('Score Time (seconds)', fontsize=12)
        ax.set_ylabel('Performance Time (seconds)', fontsize=12)
        ax.set_title('Beat Alignment: Score Time vs Performance Time', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        ax.set_aspect('equal')
        
        # Add interpretation text
        textstr = 'Points above diagonal = performer ahead (faster)\n'
        textstr += 'Points below diagonal = performer behind (slower)\n'
        textstr += 'Points on diagonal = matching score tempo'
        ax.text(0.98, 0.02, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = self.output_dir / save_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {save_name}")
    
    def plot_tempo_curve_comparison(self, save_name: str = "comp_3_tempo_curve.png"):
        """
        Tempo curve comparison: expected BPM vs actual BPM
        X-axis: Time (seconds)
        Y-axis: Tempo (BPM)
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Get beats
        if not self.beats or 'beats' not in self.beats:
            print("Warning: No beats available")
            return
        
        beat_times = [b['t'] for b in self.beats['beats']]
        if len(beat_times) < 2:
            print("Warning: Not enough beats for tempo calculation")
            return
        
        # Calculate instantaneous tempo from beat intervals
        tempos = []
        tempo_times = []
        for i in range(len(beat_times) - 1):
            dt = beat_times[i+1] - beat_times[i]
            if dt > 0:
                bpm = 60.0 / dt
                tempos.append(bpm)
                tempo_times.append((beat_times[i] + beat_times[i+1]) / 2)
        
        # Get expected tempo from score metadata or assume constant
        expected_bpm = 120  # Default
        if self.scoregraph and 'metadata' in self.scoregraph:
            # Try to get tempo from metadata
            expected_bpm = self.scoregraph['metadata'].get('tempo_bpm', 120)
        
        # Plot expected tempo (constant line)
        max_time = max(beat_times) if beat_times else 10
        ax.plot([0, max_time], [expected_bpm, expected_bpm], 'b-', linewidth=2, 
                label=f'Expected tempo ({expected_bpm:.0f} BPM)', alpha=0.7)
        
        # Plot actual tempo curve
        if tempo_times and tempos:
            ax.plot(tempo_times, tempos, 'r-', linewidth=2, label='Performance tempo', alpha=0.7)
            
            # Fill areas where faster/slower
            ax.fill_between(tempo_times, expected_bpm, tempos, 
                           where=np.array(tempos) > expected_bpm,
                           color='lightcoral', alpha=0.3, label='Faster than score')
            ax.fill_between(tempo_times, expected_bpm, tempos,
                           where=np.array(tempos) <= expected_bpm,
                           color='lightblue', alpha=0.3, label='Slower than score')
        
        # Set axis properties
        ax.set_xlim(0, max_time)
        if tempos:
            y_min = min(min(tempos), expected_bpm * 0.8)
            y_max = max(max(tempos), expected_bpm * 1.2)
            ax.set_ylim(y_min, y_max)
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Tempo (BPM)', fontsize=12)
        ax.set_title('Tempo Comparison: Expected vs Actual Performance', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        
        # Add statistics
        if tempos:
            avg_tempo = np.mean(tempos)
            std_tempo = np.std(tempos)
            textstr = f'Avg performance tempo: {avg_tempo:.1f} BPM\n'
            textstr += f'Tempo variation (std): {std_tempo:.1f} BPM\n'
            textstr += f'Expected: {expected_bpm:.0f} BPM'
            ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = self.output_dir / save_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {save_name}")
    
    def plot_cost_matrix_debug(self, 
                               score_midi_path: str,
                               perf_midi_path: str,
                               save_name: str = "comp_4_cost_matrix.png"):
        """
        Debug visualization of DTW cost matrix with path overlay
        X-axis: Score frames
        Y-axis: Performance frames
        Shows why alignment chose that path
        """
        import librosa
        from scipy.spatial.distance import cdist
        
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Recompute chroma features (same as in alignment)
        score_midi_obj = pretty_midi.PrettyMIDI(score_midi_path)
        perf_midi_obj = pretty_midi.PrettyMIDI(perf_midi_path)
        
        # Synthesize and get chroma
        sr = 22050
        hop_length = 512
        
        # Score chroma
        score_audio = score_midi_obj.synthesize(fs=sr)
        score_chroma = librosa.feature.chroma_cqt(y=score_audio, sr=sr, hop_length=hop_length)
        score_chroma = librosa.util.normalize(score_chroma + 1e-8, axis=0)
        
        # Performance chroma
        perf_audio = perf_midi_obj.synthesize(fs=sr)
        perf_chroma = librosa.feature.chroma_cqt(y=perf_audio, sr=sr, hop_length=hop_length)
        perf_chroma = librosa.util.normalize(perf_chroma + 1e-8, axis=0)
        
        # Compute cost matrix (downsample if too large)
        max_frames = 500
        if score_chroma.shape[1] > max_frames:
            score_chroma = score_chroma[:, ::score_chroma.shape[1]//max_frames]
        if perf_chroma.shape[1] > max_frames:
            perf_chroma = perf_chroma[:, ::perf_chroma.shape[1]//max_frames]
        
        C = cdist(score_chroma.T, perf_chroma.T, metric='cosine')
        C = np.nan_to_num(C, nan=1.0)
        
        # Plot cost matrix
        im = ax.imshow(C.T, origin='lower', cmap='hot', aspect='auto', interpolation='nearest')
        
        # Overlay DTW path if available
        if self.alignment and 'time_mapping' in self.alignment:
            time_mapping = self.alignment['time_mapping']
            score_frames = [m['score_frame'] for m in time_mapping]
            perf_frames = [m['perf_frame'] for m in time_mapping]
            
            # Downsample path to match matrix
            if score_chroma.shape[1] < max(score_frames):
                scale_x = score_chroma.shape[1] / (max(score_frames) + 1)
                scale_y = perf_chroma.shape[1] / (max(perf_frames) + 1)
                score_frames = [int(f * scale_x) for f in score_frames]
                perf_frames = [int(f * scale_y) for f in perf_frames]
            
            # Plot with thicker line and outline for better visibility
            ax.plot(score_frames, perf_frames, color='cyan', linewidth=3, alpha=0.9, 
                   label='DTW Alignment Path', zorder=10)
            # Add white outline for contrast
            ax.plot(score_frames, perf_frames, color='white', linewidth=5, alpha=0.4, zorder=9)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Cosine Distance (cost)', rotation=270, labelpad=20)
        
        # Set axis properties
        ax.set_xlabel('Score Frame Index', fontsize=12)
        ax.set_ylabel('Performance Frame Index', fontsize=12)
        ax.set_title('DTW Cost Matrix with Alignment Path', fontsize=14, fontweight='bold')
        
        # Add interpretation text
        textstr = 'Dark = low cost (similar)\n'
        textstr += 'Light = high cost (different)\n'
        textstr += 'Cyan path = chosen alignment\n'
        textstr += f'Matrix size: {C.shape[1]} x {C.shape[0]}'
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', color='white',
                bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        
        plt.tight_layout()
        output_path = self.output_dir / save_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {save_name}")
    
    def plot_pitch_accuracy_by_section(self, save_name: str = "comp_5_accuracy_by_section.png"):
        """
        Bar chart showing pitch accuracy per measure/section
        X-axis: Measure number
        Y-axis: Pitch accuracy percentage
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Get score notes grouped by measure
        musical_notes = self.scoregraph.get('musical_notes', [])
        bars = self.scoregraph.get('bars', [])
        
        if not musical_notes or not bars:
            print("Warning: No musical notes or bars available")
            return
            
        # Check if we have alignment for time mapping
        if not self.alignment or not self.alignment.get('time_mapping'):
            print("Warning: No alignment data available for time-based accuracy calculation")
            # Fall back to simple beat-based grouping
            self._plot_accuracy_by_beat_groups(ax, musical_notes, bars, save_name)
            return
        
        # Group notes by measure using proper time alignment
        notes_by_measure = {}
        time_mapping = self.alignment['time_mapping']
        
        # Create beat-to-time lookup from alignment
        beat_to_time = {}
        for mapping in time_mapping:
            if 'score_time' in mapping and 'perf_time' in mapping:
                # Convert score time to beats (assuming 120 BPM default)
                score_beat = mapping['score_time'] * 2.0  # 120 BPM = 2 beats per second
                beat_to_time[score_beat] = mapping['perf_time']
        
        for i, bar in enumerate(bars):
            measure_start_beat = bar.get('downbeat_abs_beat', i * 4.0)
            measure_end_beat = measure_start_beat + 4.0  # Assume 4/4 time
            
            # Get time boundaries for this measure using alignment
            measure_start_time = self._beat_to_performance_time(measure_start_beat, beat_to_time)
            measure_end_time = self._beat_to_performance_time(measure_end_beat, beat_to_time)
            
            notes_by_measure[i] = []
            
            # Group score notes by their beat position
            for note in musical_notes:
                note_beat = note.get('offset_beats', 0)
                if measure_start_beat <= note_beat < measure_end_beat:
                    notes_by_measure[i].append({
                        'pitch': note.get('pitch', 60),
                        'time': note.get('offset_seconds', 0),
                        'beat': note_beat
                    })
        
        # Calculate accuracy per measure using time-aligned comparison
        measures = sorted(notes_by_measure.keys())
        accuracies = []
        
        for measure_idx in measures:
            if not notes_by_measure[measure_idx]:
                accuracies.append(0)
                continue
            
            # Get time boundaries for this measure
            bar = bars[measure_idx]
            measure_start_beat = bar.get('downbeat_abs_beat', measure_idx * 4.0)
            measure_end_beat = measure_start_beat + 4.0
            
            measure_start_time = self._beat_to_performance_time(measure_start_beat, beat_to_time)
            measure_end_time = self._beat_to_performance_time(measure_end_beat, beat_to_time)
            
            # Get performance notes in this time window
            perf_notes_in_measure = []
            for instrument in self.perf_midi.instruments:
                for note in instrument.notes:
                    if measure_start_time <= note.start < measure_end_time:
                        perf_notes_in_measure.append({
                            'pitch': note.pitch,
                            'start': note.start,
                            'end': note.end
                        })
            
            # Calculate note-by-note accuracy
            score_notes = notes_by_measure[measure_idx]
            correct_notes = 0
            
            for score_note in score_notes:
                # Find if this score note has a matching performance note
                score_pitch = score_note['pitch']
                found_match = False
                
                for perf_note in perf_notes_in_measure:
                    # Allow pitch tolerance (±1 semitone for slight tuning issues)
                    if abs(perf_note['pitch'] - score_pitch) <= 1:
                        found_match = True
                        break
                
                if found_match:
                    correct_notes += 1
            
            # Calculate accuracy percentage
            total_expected = len(score_notes)
            accuracy = (correct_notes / total_expected * 100) if total_expected > 0 else 0
            accuracies.append(min(accuracy, 100))  # Cap at 100%
        
        # Color bars by accuracy
        colors = ['green' if a >= 80 else 'orange' if a >= 60 else 'red' for a in accuracies]
        
        # Plot bars
        bars_plot = ax.bar(measures, accuracies, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
        
        # Add value labels on bars
        for i, (measure, acc) in enumerate(zip(measures, accuracies)):
            ax.text(measure, acc + 2, f'{acc:.0f}%', ha='center', va='bottom', fontsize=9)
        
        # Set axis properties
        ax.set_xlabel('Measure Number', fontsize=12)
        ax.set_ylabel('Pitch Accuracy (%)', fontsize=12)
        ax.set_title('Pitch Accuracy by Measure', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 110)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_xticks(measures)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='green', alpha=0.7, label='Good (≥80%)'),
            Patch(facecolor='orange', alpha=0.7, label='Fair (60-80%)'),
            Patch(facecolor='red', alpha=0.7, label='Needs Work (<60%)')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Add overall accuracy
        overall_acc = np.mean(accuracies)
        textstr = f'Overall accuracy: {overall_acc:.1f}%'
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = self.output_dir / save_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {save_name}")
    
    def _beat_to_performance_time(self, target_beat, beat_to_time_map):
        """Convert beat position to performance time using alignment mapping"""
        if not beat_to_time_map:
            # Fallback: assume 120 BPM (0.5 seconds per beat)
            return target_beat * 0.5
        
        # Find closest beat in mapping
        available_beats = sorted(beat_to_time_map.keys())
        if not available_beats:
            return target_beat * 0.5
        
        # Linear interpolation between closest beats
        if target_beat <= available_beats[0]:
            return beat_to_time_map[available_beats[0]]
        if target_beat >= available_beats[-1]:
            return beat_to_time_map[available_beats[-1]]
        
        # Find surrounding beats for interpolation
        for i in range(len(available_beats) - 1):
            beat1, beat2 = available_beats[i], available_beats[i + 1]
            if beat1 <= target_beat <= beat2:
                time1, time2 = beat_to_time_map[beat1], beat_to_time_map[beat2]
                # Linear interpolation
                ratio = (target_beat - beat1) / (beat2 - beat1) if beat2 != beat1 else 0
                return time1 + ratio * (time2 - time1)
        
        return target_beat * 0.5  # Fallback
    
    def _plot_accuracy_by_beat_groups(self, ax, musical_notes, bars, save_name):
        """Fallback method when no alignment data is available"""
        # Group notes by their beat positions instead of time
        notes_by_measure = {}
        
        for i, bar in enumerate(bars):
            measure_start_beat = bar.get('downbeat_abs_beat', i * 4.0)
            measure_end_beat = measure_start_beat + 4.0
            notes_by_measure[i] = []
            
            for note in musical_notes:
                note_beat = note.get('offset_beats', 0)
                if measure_start_beat <= note_beat < measure_end_beat:
                    notes_by_measure[i].append(note.get('pitch', 60))
        
        # Simple pitch set comparison (still flawed but better than before)
        measures = sorted(notes_by_measure.keys())
        accuracies = []
        
        # Get all unique performance pitches
        perf_pitches = set()
        for instrument in self.perf_midi.instruments:
            for note in instrument.notes:
                perf_pitches.add(note.pitch)
        
        for measure in measures:
            if not notes_by_measure[measure]:
                accuracies.append(0)
                continue
            
            score_pitches = set(notes_by_measure[measure])
            # Check what fraction of score pitches appear in performance
            matches = len(score_pitches.intersection(perf_pitches))
            total = len(score_pitches)
            accuracy = (matches / total * 100) if total > 0 else 0
            accuracies.append(accuracy)
        
        # Plot with warning
        colors = ['orange' for _ in accuracies]  # All orange to indicate approximate results
        bars_plot = ax.bar(measures, accuracies, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
        
        # Add value labels on bars
        for i, (measure, acc) in enumerate(zip(measures, accuracies)):
            ax.text(measure, acc + 2, f'{acc:.0f}%', ha='center', va='bottom', fontsize=9)
        
        # Set axis properties
        ax.set_xlabel('Measure Number', fontsize=12)
        ax.set_ylabel('Pitch Accuracy (%) - APPROXIMATE', fontsize=12)
        ax.set_title('Pitch Accuracy by Measure (No Timing Alignment)', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 110)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_xticks(measures)
        
        # Add warning
        warning_text = "WARNING: No alignment data available.\nShowing pitch set overlap only (not timing-accurate)"
        ax.text(0.02, 0.98, warning_text, transform=ax.transAxes, fontsize=10, fontweight='bold',
                verticalalignment='top', color='red',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8, edgecolor='red'))
        
        plt.tight_layout()
        output_path = self.output_dir / save_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {save_name} (approximate - no timing alignment)")
    
    def plot_note_density_timeline(self, save_name: str = "comp_6_note_density.png"):
        """
        Timeline showing note density (notes per second) for score vs performance
        X-axis: Time (seconds)
        Y-axis: Notes per second
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Get score notes
        score_notes = []
        for instrument in self.score_midi.instruments:
            for note in instrument.notes:
                score_notes.append((note.start, note.end))
        
        # Get performance notes
        perf_notes = []
        for instrument in self.perf_midi.instruments:
            for note in instrument.notes:
                perf_notes.append((note.start, note.end))
        
        # Calculate density in time windows
        window_size = 1.0  # 1 second windows
        max_time = max(
            max([n[1] for n in score_notes]) if score_notes else 0,
            max([n[1] for n in perf_notes]) if perf_notes else 0
        )
        
        time_points = np.arange(0, max_time, window_size)
        score_density = []
        perf_density = []
        
        for t in time_points:
            # Count notes active in this window
            score_count = sum(1 for start, end in score_notes if start <= t < end or t <= start < t + window_size)
            perf_count = sum(1 for start, end in perf_notes if start <= t < end or t <= start < t + window_size)
            
            score_density.append(score_count / window_size)
            perf_density.append(perf_count / window_size)
        
        # Plot density curves
        ax.plot(time_points, score_density, 'b-', linewidth=2, label='Score density', alpha=0.7)
        ax.plot(time_points, perf_density, 'r-', linewidth=2, label='Performance density', alpha=0.7)
        
        # Fill areas
        ax.fill_between(time_points, 0, score_density, color='blue', alpha=0.2)
        ax.fill_between(time_points, 0, perf_density, color='red', alpha=0.2)
        
        # Set axis properties
        ax.set_xlim(0, max_time)
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Notes per Second (density)', fontsize=12)
        ax.set_title('Note Density Timeline: Score vs Performance', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        
        # Add statistics
        avg_score_density = np.mean(score_density) if score_density else 0
        avg_perf_density = np.mean(perf_density) if perf_density else 0
        textstr = f'Avg score density: {avg_score_density:.2f} notes/s\n'
        textstr += f'Avg performance density: {avg_perf_density:.2f} notes/s'
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = self.output_dir / save_name
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {save_name}")
    
    def generate_all_comparative_plots(self,
                                      score_midi_path: str,
                                      perf_midi_path: str,
                                      scoregraph_path: str,
                                      beats_path: str,
                                      context_path: str,
                                      alignment_path: str):
        """Generate all comparative visualizations"""
        
        print("\nGenerating comparative visualizations...")
        print(f"Output directory: {self.output_dir}")
        print()
        
        # Load data
        self.load_data(score_midi_path, perf_midi_path, scoregraph_path,
                      beats_path, context_path, alignment_path)
        
        # Generate plots
        try:
            self.plot_pitch_roll_comparison()
        except Exception as e:
            print(f"Error in pitch roll: {e}")
        
        try:
            self.plot_beat_alignment_scatter()
        except Exception as e:
            print(f"Error in beat alignment scatter: {e}")
        
        try:
            self.plot_tempo_curve_comparison()
        except Exception as e:
            print(f"Error in tempo curve: {e}")
        
        try:
            self.plot_cost_matrix_debug(score_midi_path, perf_midi_path)
        except Exception as e:
            print(f"Error in cost matrix: {e}")
        
        try:
            self.plot_pitch_accuracy_by_section()
        except Exception as e:
            print(f"Error in pitch accuracy by section: {e}")
        
        try:
            self.plot_note_density_timeline()
        except Exception as e:
            print(f"Error in note density: {e}")
        
        print(f"\nAll comparative visualizations saved to: {self.output_dir}")
