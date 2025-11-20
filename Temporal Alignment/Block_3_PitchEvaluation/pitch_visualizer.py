#!/usr/bin/env python3
"""
Pitch Visualizer - Create visualizations for pitch comparison

Generates plots showing:
- F0 curves (score vs audio)
- Pitch deviation over time
- Distribution histograms
- Accuracy statistics
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import warnings

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    warnings.warn("matplotlib/seaborn not available - visualization disabled")


class PitchVisualizer:
    """Visualize pitch comparison results"""
    
    def __init__(self, style: str = 'seaborn-v0_8-darkgrid', verbose: bool = True):
        """
        Initialize visualizer
        
        Args:
            style: Matplotlib style to use
            verbose: Whether to print progress messages (default: True)
        """
        self.verbose = verbose
        
        if not PLOTTING_AVAILABLE:
            raise ImportError("matplotlib and seaborn required for visualization")
        
        # Set style
        try:
            plt.style.use(style)
        except:
            plt.style.use('default')
        
        # Set seaborn theme
        sns.set_theme()
        sns.set_palette("husl")
        
        # Figure size
        self.figsize = (12, 8)
    
    def plot_pitch_curves(self, 
                         score_notes: List,
                         audio_frames: List,
                         output_path: str,
                         title: str = "Pitch Comparison: Score vs Performance"):
        """
        Plot score pitch as steps and audio F0 as continuous curve
        
        Args:
            score_notes: List of ScoreNote objects or dicts
            audio_frames: List of PitchFrame objects or dicts
            output_path: Path to save figure
            title: Plot title
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Convert to dicts if needed
        score_notes = [n.to_dict() if hasattr(n, 'to_dict') else n for n in score_notes]
        audio_frames = [f.to_dict() if hasattr(f, 'to_dict') else f for f in audio_frames]
        
        # Plot score pitches as step function
        for note in score_notes:
            onset = note['onset_time']
            offset = note['offset_time']
            freq = note['frequency_hz']
            
            ax.hlines(freq, onset, offset, colors='blue', linewidth=2, alpha=0.7, label='Score' if note == score_notes[0] else '')
        
        # Plot audio F0 as continuous line
        times = [f['time'] for f in audio_frames if f['is_voiced']]
        freqs = [f['frequency'] for f in audio_frames if f['is_voiced']]
        
        if times and freqs:
            ax.plot(times, freqs, 'r-', alpha=0.6, linewidth=1.5, label='Performance')
        
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Frequency (Hz)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        if self.verbose:
            print(f"Pitch curve plot saved to: {output_path}")
    
    def plot_cents_deviation(self,
                           comparisons: List,
                           output_path: str,
                           title: str = "Pitch Deviation Over Time"):
        """
        Plot cents deviation for each note over time
        
        Args:
            comparisons: List of NoteComparison objects or dicts
            output_path: Path to save figure
            title: Plot title
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Convert to dicts if needed
        comparisons = [c.to_dict() if hasattr(c, 'to_dict') else c for c in comparisons]
        
        # Filter measured notes
        measured = [c for c in comparisons if c.is_measured]
        
        if not measured:
            if self.verbose:
                print("No measured notes to plot")
            return
        
        # Extract data
        times = [c['score_note']['onset_time'] for c in measured]
        cents = [c['cents_error'] for c in measured]
        accurate = [c['is_accurate'] for c in measured]
        
        # Color by accuracy
        colors = ['green' if acc else 'red' for acc in accurate]
        
        # Scatter plot
        ax.scatter(times, cents, c=colors, alpha=0.6, s=50)
        
        # Add reference lines
        ax.axhline(0, color='blue', linestyle='--', linewidth=1, alpha=0.7, label='Perfect (0¢)')
        ax.axhline(25, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='±25¢')
        ax.axhline(-25, color='orange', linestyle='--', linewidth=1, alpha=0.5)
        ax.axhline(50, color='red', linestyle='--', linewidth=1, alpha=0.5, label='±50¢')
        ax.axhline(-50, color='red', linestyle='--', linewidth=1, alpha=0.5)
        
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Pitch Deviation (cents)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Add text with stats
        mean_cents = np.mean([abs(c) for c in cents])
        textstr = f'Mean Absolute Error: {mean_cents:.1f}¢'
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        if self.verbose:
            print(f"Deviation plot saved to: {output_path}")
    
    def plot_cents_histogram(self,
                           comparisons: List,
                           output_path: str,
                           bins: int = 30,
                           title: str = "Pitch Deviation Distribution"):
        """
        Plot histogram of cents deviations
        
        Args:
            comparisons: List of NoteComparison objects or dicts
            output_path: Path to save figure
            bins: Number of histogram bins
            title: Plot title
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Convert to dicts if needed
        comparisons = [c.to_dict() if hasattr(c, 'to_dict') else c for c in comparisons]
        
        # Filter measured notes
        measured = [c for c in comparisons if c['is_measured']]
        
        if not measured:
            if self.verbose:
                print("No measured notes to plot")
            return
        
        cents = [c['cents_error'] for c in measured]
        cents_abs = [abs(c) for c in cents]
        
        # Histogram 1: Signed deviation (sharp/flat)
        ax1.hist(cents, bins=bins, color='skyblue', edgecolor='black', alpha=0.7)
        ax1.axvline(0, color='red', linestyle='--', linewidth=2, label='Perfect pitch')
        ax1.axvline(np.mean(cents), color='green', linestyle='--', linewidth=2, label=f'Mean: {np.mean(cents):.1f}¢')
        ax1.set_xlabel('Pitch Deviation (cents)', fontsize=12)
        ax1.set_ylabel('Number of Notes', fontsize=12)
        ax1.set_title('Signed Deviation (Sharp/Flat)', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Histogram 2: Absolute deviation
        ax2.hist(cents_abs, bins=bins, color='coral', edgecolor='black', alpha=0.7)
        ax2.axvline(np.mean(cents_abs), color='blue', linestyle='--', linewidth=2, 
                   label=f'Mean: {np.mean(cents_abs):.1f}¢')
        ax2.axvline(np.median(cents_abs), color='green', linestyle='--', linewidth=2,
                   label=f'Median: {np.median(cents_abs):.1f}¢')
        ax2.set_xlabel('Absolute Pitch Deviation (cents)', fontsize=12)
        ax2.set_ylabel('Number of Notes', fontsize=12)
        ax2.set_title('Absolute Deviation (Accuracy)', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        if self.verbose:
            print(f"Histogram plot saved to: {output_path}")
    
    def plot_accuracy_breakdown(self,
                              metrics: Dict,
                              output_path: str,
                              title: str = "Pitch Accuracy Breakdown"):
        """
        Plot pie chart and bar chart of accuracy categories
        
        Args:
            metrics: Metrics dictionary from PitchComparator
            output_path: Path to save figure
            title: Plot title
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        breakdown = metrics.get('accuracy_breakdown', {})
        
        if not breakdown:
            if self.verbose:
                print("No accuracy breakdown to plot")
            return
        
        # Extract data
        categories = []
        percentages = []
        colors = []
        
        category_colors = {
            'perfect': '#2ecc71',     # Green
            'excellent': '#3498db',    # Blue
            'good': '#f39c12',         # Orange
            'poor': '#e74c3c'          # Red
        }
        
        for cat in ['perfect', 'excellent', 'good', 'poor']:
            if cat in breakdown:
                data = breakdown[cat]
                categories.append(f"{cat.title()}\n{data['threshold']}")
                percentages.append(data['percentage'])
                colors.append(category_colors[cat])
        
        # Pie chart
        ax1.pie(percentages, labels=categories, colors=colors, autopct='%1.1f%%',
               startangle=90, textprops={'fontsize': 10})
        ax1.set_title('Accuracy Distribution', fontsize=12, fontweight='bold')
        
        # Bar chart
        ax2.bar(range(len(categories)), percentages, color=colors, edgecolor='black', alpha=0.7)
        ax2.set_xticks(range(len(categories)))
        ax2.set_xticklabels([cat.split('\n')[0] for cat in categories], rotation=0)
        ax2.set_ylabel('Percentage of Notes (%)', fontsize=12)
        ax2.set_title('Accuracy Category Breakdown', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add percentage labels on bars
        for i, pct in enumerate(percentages):
            ax2.text(i, pct + 1, f'{pct:.1f}%', ha='center', fontsize=10)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        if self.verbose:
            print(f"Accuracy breakdown plot saved to: {output_path}")
    
    def create_comprehensive_report(self,
                                   score_notes: List,
                                   audio_frames: List,
                                   comparisons: List,
                                   metrics: Dict,
                                   grade: Dict,
                                   output_dir: str):
        """
        Create a comprehensive visualization report with multiple plots
        
        Args:
            score_notes: List of ScoreNote objects
            audio_frames: List of PitchFrame objects
            comparisons: List of NoteComparison objects
            metrics: Metrics dictionary
            grade: Grade dictionary
            output_dir: Directory to save plots
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.verbose:
            print("\nCreating comprehensive visualization report...")
        
        # 1. Pitch curves
        self.plot_pitch_curves(
            score_notes, 
            audio_frames,
            str(output_dir / "01_pitch_curves.png")
        )
        
        # 2. Deviation over time
        self.plot_cents_deviation(
            comparisons,
            str(output_dir / "02_deviation_over_time.png")
        )
        
        # 3. Histogram
        self.plot_cents_histogram(
            comparisons,
            str(output_dir / "03_deviation_histogram.png")
        )
        
        # 4. Accuracy breakdown
        self.plot_accuracy_breakdown(
            metrics,
            str(output_dir / "04_accuracy_breakdown.png")
        )
        
        # 5. Summary figure
        self._create_summary_figure(metrics, grade, str(output_dir / "00_summary.png"))
        
        if self.verbose:
            print(f"Visualization report complete: {output_dir}")
    
    def _create_summary_figure(self, metrics: Dict, grade: Dict, output_path: str):
        """Create a summary figure with key statistics"""
        fig = plt.figure(figsize=(14, 10))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # Title
        fig.suptitle('Pitch Accuracy Evaluation Summary', 
                    fontsize=16, fontweight='bold')
        
        # Large grade display
        ax_grade = fig.add_subplot(gs[0, :])
        ax_grade.axis('off')
        
        letter_grade = grade.get('letter_grade', 'N/A')
        numeric_score = grade.get('numeric_score', 0)
        quality = grade.get('quality_description', '')
        
        ax_grade.text(0.5, 0.6, letter_grade, ha='center', va='center',
                     fontsize=80, fontweight='bold', color='darkblue')
        ax_grade.text(0.5, 0.3, f"{numeric_score:.1f}/100", ha='center', va='center',
                     fontsize=30, color='darkgreen')
        ax_grade.text(0.5, 0.1, quality, ha='center', va='center',
                     fontsize=24, style='italic')
        
        # Key metrics (left)
        ax_metrics = fig.add_subplot(gs[1, 0])
        ax_metrics.axis('off')
        
        mace = metrics.get('mean_absolute_cents_error', 0)
        measured = metrics.get('measured_notes', 0)
        total = metrics.get('total_notes', 0)
        
        metrics_text = f"""
        Key Metrics:
        
        Mean Absolute Error: {mace:.1f} cents
        
        Measured Notes: {measured}/{total} ({measured/total*100:.0f}%)
        
        Within ±10 cents: {metrics.get('within_10_cents', 0):.1f}%
        Within ±25 cents: {metrics.get('within_25_cents', 0):.1f}%
        Within ±50 cents: {metrics.get('within_50_cents', 0):.1f}%
        """
        
        ax_metrics.text(0.1, 0.9, metrics_text, ha='left', va='top',
                       fontsize=12, family='monospace',
                       bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        # Accuracy breakdown (right)
        ax_breakdown = fig.add_subplot(gs[1, 1])
        
        breakdown = metrics.get('accuracy_breakdown', {})
        categories = ['Perfect', 'Excellent', 'Good', 'Poor']
        percentages = [
            breakdown.get('perfect', {}).get('percentage', 0),
            breakdown.get('excellent', {}).get('percentage', 0),
            breakdown.get('good', {}).get('percentage', 0),
            breakdown.get('poor', {}).get('percentage', 0)
        ]
        colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
        
        ax_breakdown.barh(categories, percentages, color=colors, alpha=0.7, edgecolor='black')
        ax_breakdown.set_xlabel('Percentage (%)', fontsize=10)
        ax_breakdown.set_title('Accuracy Categories', fontsize=12, fontweight='bold')
        ax_breakdown.grid(True, alpha=0.3, axis='x')
        
        # Strengths (bottom left)
        ax_strengths = fig.add_subplot(gs[2, 0])
        ax_strengths.axis('off')
        
        strengths = grade.get('strengths', [])[:3]  # Top 3
        strengths_text = "Strengths:\n\n" + "\n\n".join(f"• {s}" for s in strengths)
        
        ax_strengths.text(0.05, 0.95, strengths_text, ha='left', va='top',
                         fontsize=10, wrap=True,
                         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        
        # Improvements (bottom right)
        ax_improve = fig.add_subplot(gs[2, 1])
        ax_improve.axis('off')
        
        improvements = grade.get('areas_for_improvement', [])[:3]  # Top 3
        improve_text = "Areas for Improvement:\n\n" + "\n\n".join(f"• {i}" for i in improvements)
        
        ax_improve.text(0.05, 0.95, improve_text, ha='left', va='top',
                       fontsize=10, wrap=True,
                       bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
        
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        if self.verbose:
            print(f"Summary figure saved to: {output_path}")


def main():
    """Example usage"""
    print("Pitch Visualizer - use from pitch evaluation pipeline")
    print("See evaluate_pitch.py for complete workflow")


if __name__ == '__main__':
    main()
