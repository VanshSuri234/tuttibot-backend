#!/usr/bin/env python3
"""
Musician-Friendly Visualizer - Create intuitive plots for performers

Generates easy-to-understand visualizations:
- Pitch vs Time with note names (not just Hz)
- Note-by-note error bars
- Color-coded accuracy indicators
- Piano roll style visualization
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import warnings

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.ticker import FuncFormatter
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    warnings.warn("matplotlib/seaborn not available - visualization disabled")


def midi_to_note_name(midi_num: float) -> str:
    """
    Convert MIDI number to note name
    
    Args:
        midi_num: MIDI note number (e.g., 69 = A4)
        
    Returns:
        Note name string (e.g., "A4", "C#5")
    """
    if np.isnan(midi_num):
        return "?"
    
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    midi_int = int(round(midi_num))
    octave = (midi_int // 12) - 1
    note = notes[midi_int % 12]
    return f"{note}{octave}"


def freq_to_midi(freq_hz: float) -> float:
    """
    Convert frequency to MIDI note number
    
    Args:
        freq_hz: Frequency in Hz
        
    Returns:
        MIDI note number (69 = A4 = 440 Hz)
    """
    if freq_hz <= 0 or np.isnan(freq_hz):
        return np.nan
    
    return 69 + 12 * np.log2(freq_hz / 440.0)


def get_error_color(cents_error: float) -> str:
    """
    Get color based on cents error magnitude
    
    Args:
        cents_error: Error in cents
        
    Returns:
        Color string
    """
    abs_error = abs(cents_error)
    
    if abs_error < 10:
        return '#2ecc71'  # Green - Perfect
    elif abs_error < 25:
        return '#f39c12'  # Orange - Good
    elif abs_error < 50:
        return '#e67e22'  # Dark orange - Acceptable
    else:
        return '#e74c3c'  # Red - Poor


class MusicianVisualizer:
    """Create musician-friendly visualizations"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize visualizer
        
        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose
        
        if not PLOTTING_AVAILABLE:
            raise ImportError("matplotlib and seaborn required for visualization")
        
        # Use clean style
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette("husl")
        
        self.figsize_wide = (16, 6)
        self.figsize_tall = (12, 10)
        self.figsize_standard = (12, 8)
    
    def plot_pitch_vs_time_with_notes(self,
                                       score_notes: List,
                                       audio_frames: List,
                                       comparison_data: List,
                                       output_path: str):
        """
        Plot pitch over time with note names on Y-axis
        
        Shows expected (score) and actual (audio) pitches with note names
        instead of raw frequencies, making it intuitive for musicians.
        
        Args:
            score_notes: List of notes from score
            audio_frames: List of pitch frames from audio
            comparison_data: List of comparison results
            output_path: Where to save the plot
        """
        fig, ax = plt.subplots(figsize=self.figsize_wide)
        
        # Convert to dicts if needed
        score_notes = [n.to_dict() if hasattr(n, 'to_dict') else n for n in score_notes]
        audio_frames = [f.to_dict() if hasattr(f, 'to_dict') else f for f in audio_frames]
        comparison_data = [c.to_dict() if hasattr(c, 'to_dict') else c for c in comparison_data]
        
        # Plot score notes as horizontal bars (expected pitches)
        for note in score_notes:
            onset = note['onset_time']
            offset = note['offset_time']
            midi_num = freq_to_midi(note['frequency_hz'])
            
            # Draw bar for expected note
            ax.add_patch(patches.Rectangle(
                (onset, midi_num - 0.3),
                offset - onset,
                0.6,
                facecolor='blue',
                alpha=0.3,
                edgecolor='blue',
                linewidth=1.5,
                label='Expected (Score)' if note == score_notes[0] else ''
            ))
        
        # Plot audio F0 as line with color based on accuracy
        times = []
        midi_nums = []
        
        for frame in audio_frames:
            if frame['is_voiced'] and frame['frequency'] > 0:
                times.append(frame['time'])
                midi_nums.append(freq_to_midi(frame['frequency']))
        
        if times and midi_nums:
            ax.plot(times, midi_nums, 'r-', alpha=0.7, linewidth=2, 
                   label='Actual (Performance)', zorder=3)
        
        # Add markers for measured notes with color-coded accuracy
        for comp in comparison_data:
            is_measured = comp.get('is_measured', comp.get('measured', False))
            if is_measured:
                onset = comp['score_note']['onset_time']
                expected_freq = comp['score_note']['frequency_hz']
                measured_freq = comp.get('audio_frequency_median', comp.get('measured_frequency', 0))
                cents_error = comp['cents_error']
                
                color = get_error_color(cents_error)
                
                expected_midi = freq_to_midi(expected_freq)
                measured_midi = freq_to_midi(measured_freq)
                
                # Plot measured note as dot
                ax.plot(onset, measured_midi, 'o', color=color, 
                       markersize=8, zorder=4, alpha=0.8)
        
        # Set up Y-axis with note names
        if score_notes:
            all_freqs = [n['frequency_hz'] for n in score_notes]
            min_freq = min(all_freqs)
            max_freq = max(all_freqs)
            
            min_midi = freq_to_midi(min_freq) - 2
            max_midi = freq_to_midi(max_freq) + 2
            
            # Create tick positions for each semitone
            midi_ticks = np.arange(int(min_midi), int(max_midi) + 1, 1)
            note_labels = [midi_to_note_name(m) for m in midi_ticks]
            
            ax.set_yticks(midi_ticks)
            ax.set_yticklabels(note_labels, fontsize=9)
            ax.set_ylim(min_midi - 0.5, max_midi + 0.5)
        
        ax.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Musical Note', fontsize=12, fontweight='bold')
        ax.set_title('Pitch Over Time: Expected vs. Actual Performance', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Add legend
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
        
        # Add accuracy color legend
        legend_elements = [
            patches.Patch(facecolor='#2ecc71', label='Perfect (<10¢)'),
            patches.Patch(facecolor='#f39c12', label='Good (10-25¢)'),
            patches.Patch(facecolor='#e67e22', label='Acceptable (25-50¢)'),
            patches.Patch(facecolor='#e74c3c', label='Poor (≥50¢)')
        ]
        ax.legend(handles=legend_elements, loc='upper left', 
                 title='Accuracy', fontsize=9, framealpha=0.9)
        
        ax.grid(True, alpha=0.3, axis='x')
        ax.grid(True, alpha=0.2, axis='y', linestyle=':')
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        if self.verbose:
            print(f"Saved pitch vs time plot: {output_path}")
    
    def plot_note_by_note_errors(self,
                                  comparison_data: List,
                                  output_path: str,
                                  max_notes: int = 50):
        """
        Plot note-by-note error bars
        
        Shows each note's pitch error as a colored bar, making it easy
        to identify which specific notes need work.
        
        Args:
            comparison_data: List of comparison results
            output_path: Where to save the plot
            max_notes: Maximum number of notes to show (default: 50)
        """
        comparison_data = [c.to_dict() if hasattr(c, 'to_dict') else c for c in comparison_data]
        
        # Filter to only measured notes
        measured = [c for c in comparison_data if c.get('is_measured', c.get('measured', False))]
        
        if not measured:
            if self.verbose:
                print("No measured notes to plot")
            return
        
        # Limit to max_notes if there are too many
        if len(measured) > max_notes:
            step = len(measured) // max_notes
            measured = measured[::step]
        
        fig, ax = plt.subplots(figsize=self.figsize_wide)
        
        # Extract data
        note_indices = [c['note_index'] + 1 for c in measured]  # 1-indexed for display
        cents_errors = [c['cents_error'] for c in measured]
        
        # Get note names from score_note if available
        note_names = []
        for c in measured:
            if 'note_name' in c:
                note_names.append(c['note_name'])
            elif 'score_note' in c and 'note_name' in c['score_note']:
                note_names.append(c['score_note']['note_name'])
            else:
                # Generate from frequency
                freq = c.get('score_note', {}).get('frequency_hz', 440)
                note_names.append(midi_to_note_name(freq_to_midi(freq)))
        
        colors = [get_error_color(err) for err in cents_errors]
        
        # Create bar chart
        bars = ax.bar(range(len(note_indices)), cents_errors, color=colors, alpha=0.8)
        
        # Add zero line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.5)
        
        # Add threshold lines
        ax.axhline(y=10, color='green', linestyle='--', linewidth=1, alpha=0.3, label='±10¢ (Perfect)')
        ax.axhline(y=-10, color='green', linestyle='--', linewidth=1, alpha=0.3)
        ax.axhline(y=25, color='orange', linestyle='--', linewidth=1, alpha=0.3, label='±25¢ (Good)')
        ax.axhline(y=-25, color='orange', linestyle='--', linewidth=1, alpha=0.3)
        ax.axhline(y=50, color='red', linestyle='--', linewidth=1, alpha=0.3, label='±50¢ (Acceptable)')
        ax.axhline(y=-50, color='red', linestyle='--', linewidth=1, alpha=0.3)
        
        # Labels
        ax.set_xlabel('Note Number', fontsize=12, fontweight='bold')
        ax.set_ylabel('Pitch Error (cents)', fontsize=12, fontweight='bold')
        ax.set_title('Note-by-Note Pitch Accuracy\nPositive = Sharp (too high) | Negative = Flat (too low)', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Set x-ticks to show note names
        tick_positions = range(len(note_indices))
        tick_labels = [f"{name}\n#{idx}" for name, idx in zip(note_names, note_indices)]
        
        # Show every nth label if too many
        if len(tick_labels) > 20:
            show_every = len(tick_labels) // 20 + 1
            tick_labels = [label if i % show_every == 0 else '' for i, label in enumerate(tick_labels)]
        
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)
        
        ax.legend(fontsize=9, loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        if self.verbose:
            print(f"Saved note-by-note errors plot: {output_path}")
    
    def plot_accuracy_summary(self,
                             metrics: Dict,
                             output_path: str):
        """
        Create a visual summary of overall accuracy
        
        Shows pie chart of accuracy distribution and key statistics
        in a format easy for musicians to understand.
        
        Args:
            metrics: Dictionary of metrics
            output_path: Where to save the plot
        """
        fig = plt.figure(figsize=self.figsize_standard)
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Pie chart of accuracy breakdown
        ax1 = fig.add_subplot(gs[0, :])
        
        breakdown = metrics.get('accuracy_breakdown', {})
        perfect = breakdown.get('perfect', {}).get('count', 0)
        excellent = breakdown.get('excellent', {}).get('count', 0)
        good = breakdown.get('good', {}).get('count', 0)
        poor = breakdown.get('poor', {}).get('count', 0)
        
        sizes = [perfect, excellent, good, poor]
        labels = [
            f'Perfect (<10¢)\n{perfect} notes',
            f'Good (10-25¢)\n{excellent} notes',
            f'Acceptable (25-50¢)\n{good} notes',
            f'Poor (≥50¢)\n{poor} notes'
        ]
        colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
        explode = (0.05, 0.02, 0.02, 0.05)
        
        # Only show if we have data
        if sum(sizes) > 0:
            wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors,
                                                autopct='%1.1f%%', explode=explode,
                                                startangle=90, textprops={'fontsize': 10})
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        ax1.set_title('Pitch Accuracy Distribution', fontsize=14, fontweight='bold', pad=20)
        
        # Key statistics
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.axis('off')
        
        mace = metrics.get('mean_absolute_cents_error', 0)
        measurement_rate = metrics.get('measurement_rate', 0) * 100
        measured = metrics.get('measured_notes', 0)
        total = metrics.get('total_notes', 0)
        
        stats_text = f"""
KEY STATISTICS

Mean Error: {mace:.1f} cents

Measurement Rate: {measurement_rate:.1f}%
({measured} of {total} notes)

Within ±10¢: {metrics.get('within_10_cents', 0):.1f}%
Within ±25¢: {metrics.get('within_25_cents', 0):.1f}%
Within ±50¢: {metrics.get('within_50_cents', 0):.1f}%
        """
        
        ax2.text(0.1, 0.5, stats_text, fontsize=11, verticalalignment='center',
                family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # Interpretation guide
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.axis('off')
        
        if mace < 10:
            assessment = "EXCELLENT"
            desc = "Professional level\naccuracy"
            color = '#2ecc71'
        elif mace < 25:
            assessment = "VERY GOOD"
            desc = "Strong pitch\ncontrol"
            color = '#f39c12'
        elif mace < 50:
            assessment = "GOOD"
            desc = "Generally accurate\nwith some deviation"
            color = '#e67e22'
        elif mace < 100:
            assessment = "FAIR"
            desc = "Noticeable pitch\nissues"
            color = '#e67e22'
        else:
            assessment = "NEEDS WORK"
            desc = "Significant pitch\nproblems"
            color = '#e74c3c'
        
        interp_text = f"""
OVERALL ASSESSMENT

{assessment}

{desc}
        """
        
        ax3.text(0.1, 0.5, interp_text, fontsize=12, verticalalignment='center',
                fontweight='bold', bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
        
        plt.suptitle('Performance Summary', fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        if self.verbose:
            print(f"Saved accuracy summary plot: {output_path}")
    
    def plot_error_histogram(self,
                            comparison_data: List,
                            output_path: str):
        """
        Plot histogram of pitch errors
        
        Shows distribution of errors to identify patterns
        (e.g., normally distributed = random errors,
        skewed = systematic bias)
        
        Args:
            comparison_data: List of comparison results
            output_path: Where to save the plot
        """
        comparison_data = [c.to_dict() if hasattr(c, 'to_dict') else c for c in comparison_data]
        
        # Get measured errors
        errors = [c['cents_error'] for c in comparison_data if c.get('is_measured', c.get('measured', False))]
        
        if not errors:
            if self.verbose:
                print("No errors to plot histogram")
            return
        
        fig, ax = plt.subplots(figsize=self.figsize_standard)
        
        # Create histogram
        n, bins, patches = ax.hist(errors, bins=30, alpha=0.7, color='skyblue', 
                                   edgecolor='black', linewidth=0.5)
        
        # Color bars by error magnitude
        for i, patch in enumerate(patches):
            bin_center = (bins[i] + bins[i+1]) / 2
            patch.set_facecolor(get_error_color(bin_center))
        
        # Add mean and median lines
        mean_error = np.mean(errors)
        median_error = np.median(errors)
        
        ax.axvline(mean_error, color='red', linestyle='--', linewidth=2, 
                  label=f'Mean: {mean_error:+.1f}¢')
        ax.axvline(median_error, color='blue', linestyle='--', linewidth=2, 
                  label=f'Median: {median_error:+.1f}¢')
        ax.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.5)
        
        # Add threshold lines
        for thresh in [-50, -25, -10, 10, 25, 50]:
            ax.axvline(thresh, color='gray', linestyle=':', linewidth=1, alpha=0.3)
        
        ax.set_xlabel('Pitch Error (cents)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Notes', fontsize=12, fontweight='bold')
        ax.set_title('Distribution of Pitch Errors\nNegative = Flat | Positive = Sharp', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        if self.verbose:
            print(f"Saved error histogram: {output_path}")
    
    def create_musician_report(self,
                              score_notes: List,
                              audio_frames: List,
                              comparison_data: List,
                              metrics: Dict,
                              output_dir: str):
        """
        Generate all musician-friendly visualizations
        
        Args:
            score_notes: Notes from score
            audio_frames: Pitch frames from audio
            comparison_data: Comparison results
            metrics: Calculated metrics
            output_dir: Directory to save plots
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.verbose:
            print("\nGenerating musician-friendly visualizations...")
        
        # 1. Pitch vs Time with note names
        self.plot_pitch_vs_time_with_notes(
            score_notes,
            audio_frames,
            comparison_data,
            str(output_dir / "pitch_over_time.png")
        )
        
        # 2. Note-by-note error bars
        self.plot_note_by_note_errors(
            comparison_data,
            str(output_dir / "note_errors.png")
        )
        
        # 3. Accuracy summary
        self.plot_accuracy_summary(
            metrics,
            str(output_dir / "accuracy_summary.png")
        )
        
        # 4. Error histogram
        self.plot_error_histogram(
            comparison_data,
            str(output_dir / "error_distribution.png")
        )
        
        if self.verbose:
            print(f"\nAll visualizations saved to: {output_dir}")


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate musician-friendly visualizations')
    parser.add_argument('evaluation_dir', help='Path to evaluation results directory')
    
    args = parser.parse_args()
    
    eval_dir = Path(args.evaluation_dir)
    
    # Load data
    with open(eval_dir / 'data' / 'score_pitches.json', 'r') as f:
        score_data = json.load(f)
        score_notes = score_data['notes']
    
    with open(eval_dir / 'data' / 'audio_pitches.json', 'r') as f:
        audio_data = json.load(f)
        audio_frames = audio_data['frames']
    
    with open(eval_dir / 'data' / 'comparison_results.json', 'r') as f:
        comp_data = json.load(f)
        comparison_data = comp_data['comparisons']
        metrics = comp_data['metrics']
    
    # Generate visualizations
    visualizer = MusicianVisualizer()
    viz_dir = eval_dir / 'musician_visualizations'
    
    visualizer.create_musician_report(
        score_notes,
        audio_frames,
        comparison_data,
        metrics,
        str(viz_dir)
    )


if __name__ == '__main__':
    main()
