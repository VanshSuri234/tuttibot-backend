#!/usr/bin/env python3
"""
Simple Visualization Generator for Alignment Results

Creates separate PNG images for each result type:
1. Beat confidence plot
2. Alignment path with band constraint
3. Pitch matching visualization
4. Beat-weighted alignment
5. Tempo variation curve
6. Performance summary

Plus a simple text summary file.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib.patches as mpatches


class AlignmentVisualizer:
    """Generate simple, clear visualizations for musicians"""
    
    def __init__(self, output_dir: str = "visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Set clean style
        plt.style.use('seaborn-v0_8-darkgrid')
        
    def load_data(self, 
                  beats_path: Optional[str] = None,
                  context_path: Optional[str] = None,
                  alignment_path: Optional[str] = None,
                  scoregraph_path: Optional[str] = None):
        """Load all result files"""
        
        self.beats = None
        self.context = None
        self.alignment = None
        self.scoregraph = None
        
        if beats_path and Path(beats_path).exists():
            with open(beats_path, 'r') as f:
                self.beats = json.load(f)
                
        if context_path and Path(context_path).exists():
            with open(context_path, 'r') as f:
                self.context = json.load(f)
                
        if alignment_path and Path(alignment_path).exists():
            with open(alignment_path, 'r') as f:
                self.alignment = json.load(f)
                
        if scoregraph_path and Path(scoregraph_path).exists():
            with open(scoregraph_path, 'r') as f:
                self.scoregraph = json.load(f)
    
    def plot_beat_confidence(self, save_name: str = "1_beat_confidence.png"):
        """
        Plot 1: Beat Confidence Timeline
        Shows detected beats with confidence levels
        """
        if not self.beats:
            print("Skipping beat confidence plot: no data")
            return
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Extract beat data
        if isinstance(self.beats, dict) and 'beats' in self.beats:
            beats_list = self.beats['beats']
        else:
            beats_list = self.beats
        
        times = [b['t'] for b in beats_list]
        confidences = [b.get('confidence', 1.0) for b in beats_list]
        is_downbeat = [b.get('downbeat', 0) for b in beats_list]
        
        # Plot beats with color by confidence
        for t, conf, down in zip(times, confidences, is_downbeat):
            # Color based on confidence
            if conf >= 0.8:
                color = 'green'
                label = 'High confidence'
            elif conf >= 0.5:
                color = 'orange'
                label = 'Medium confidence'
            else:
                color = 'red'
                label = 'Low confidence'
            
            # Width based on downbeat
            width = 3 if down else 1
            alpha = 0.9 if down else 0.6
            
            ax.axvline(x=t, color=color, linewidth=width, alpha=alpha)
        
        # Add legend
        high_patch = mpatches.Patch(color='green', label='High confidence (≥0.8)')
        med_patch = mpatches.Patch(color='orange', label='Medium confidence (0.5-0.8)')
        low_patch = mpatches.Patch(color='red', label='Low confidence (<0.5)')
        ax.legend(handles=[high_patch, med_patch, low_patch], loc='upper right')
        
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Beat Events', fontsize=12)
        ax.set_title('Beat Detection with Confidence Levels\n(Thick lines = downbeats)', 
                    fontsize=14, fontweight='bold')
        ax.set_ylim(-0.5, 1)
        ax.set_yticks([])
        ax.grid(True, alpha=0.3)
        
        # Add text summary
        avg_conf = np.mean(confidences)
        total_beats = len(times)
        downbeats = sum(is_downbeat)
        
        summary_text = f"Total beats: {total_beats}\nDownbeats: {downbeats}\nAvg confidence: {avg_conf:.2f}"
        ax.text(0.02, 0.98, summary_text, transform=ax.transAxes,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
               fontsize=10)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {save_name}")
    
    def plot_alignment_path(self, save_name: str = "2_alignment_path.png"):
        """
        Plot 2: DTW Alignment Path with Band Constraint
        Shows how score time maps to performance time
        """
        if not self.alignment or 'time_mapping' not in self.alignment:
            print("Skipping alignment path plot: no data")
            return
        
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Extract time mapping
        time_mapping = self.alignment['time_mapping']
        score_times = [m['score_time'] for m in time_mapping]
        perf_times = [m['perf_time'] for m in time_mapping]
        
        # Plot alignment path
        ax.plot(perf_times, score_times, 'b-', linewidth=2, label='Alignment path')
        
        # Plot diagonal (perfect tempo match)
        max_time = max(max(score_times), max(perf_times))
        ax.plot([0, max_time], [0, max_time], 'k--', alpha=0.3, label='Perfect tempo match')
        
        # Show band constraint (±25% tempo deviation)
        band_upper = [t * 1.25 for t in perf_times]
        band_lower = [t * 0.75 for t in perf_times]
        ax.fill_between(perf_times, band_lower, band_upper, alpha=0.2, color='gray', 
                        label='Allowed tempo band (±25%)')
        
        ax.set_xlabel('Performance Time (seconds)', fontsize=12)
        ax.set_ylabel('Score Time (seconds)', fontsize=12)
        ax.set_title('Score-Performance Time Alignment\n(Blue line shows your tempo)', 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # Add interpretation guide
        guide_text = (
            "How to read:\n"
            "• Line on diagonal = matched tempo\n"
            "• Steeper = you played slower\n"
            "• Flatter = you played faster"
        )
        ax.text(0.98, 0.02, guide_text, transform=ax.transAxes,
               verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
               fontsize=9)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {save_name}")
    
    def plot_pitch_matching(self, save_name: str = "3_pitch_matching.png"):
        """
        Plot 3: Pitch Matching Accuracy
        Shows which notes were played correctly
        """
        if not self.context or 'pitch_matches' not in self.context:
            print("Skipping pitch matching plot: no data")
            return
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        matches = self.context['pitch_matches']
        
        # Create bar chart
        categories = ['Correct\nNotes', 'Total Score\nNotes', 'Total Performance\nNotes']
        values = [matches['matches'], matches['total_score_notes'], matches['total_perf_notes']]
        colors = ['green', 'blue', 'orange']
        
        bars = ax.bar(categories, values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val}',
                   ha='center', va='bottom', fontsize=14, fontweight='bold')
        
        # Add percentage
        match_pct = matches['match_percentage']
        
        ax.set_ylabel('Number of Notes', fontsize=12)
        ax.set_title(f'Pitch Accuracy: {match_pct:.1f}% Correct\n'
                    f'({matches["matches"]} out of {matches["total_score_notes"]} notes)',
                    fontsize=14, fontweight='bold')
        ax.grid(True, axis='y', alpha=0.3)
        
        # Color-code the accuracy
        if match_pct >= 90:
            grade_color = 'green'
            grade = 'Excellent'
        elif match_pct >= 80:
            grade_color = 'lightgreen'
            grade = 'Good'
        elif match_pct >= 70:
            grade_color = 'orange'
            grade = 'Fair'
        else:
            grade_color = 'red'
            grade = 'Needs Work'
        
        ax.text(0.5, 0.95, f'Grade: {grade}', transform=ax.transAxes,
               ha='center', va='top',
               bbox=dict(boxstyle='round', facecolor=grade_color, alpha=0.8),
               fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {save_name}")
    
    def plot_tempo_variation(self, save_name: str = "4_tempo_variation.png"):
        """
        Plot 4: Tempo Variation Over Time
        Shows where performer sped up or slowed down
        """
        if not self.alignment or 'time_mapping' not in self.alignment:
            print("Skipping tempo variation plot: no data")
            return
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Calculate local tempo ratio
        time_mapping = self.alignment['time_mapping']
        tempo_ratios = []
        avg_times = []
        
        for i in range(1, len(time_mapping)):
            dt_score = time_mapping[i]['score_time'] - time_mapping[i-1]['score_time']
            dt_perf = time_mapping[i]['perf_time'] - time_mapping[i-1]['perf_time']
            
            if dt_perf > 0:
                ratio = dt_score / dt_perf
                tempo_ratios.append(ratio)
                avg_times.append((time_mapping[i]['perf_time'] + time_mapping[i-1]['perf_time']) / 2)
        
        # Plot tempo ratio
        ax.plot(avg_times, tempo_ratios, 'b-', linewidth=2, alpha=0.7)
        ax.axhline(y=1.0, color='black', linestyle='--', linewidth=1, label='Perfect tempo match')
        
        # Color regions
        ax.fill_between(avg_times, 1.0, tempo_ratios, 
                       where=np.array(tempo_ratios) >= 1.0,
                       color='red', alpha=0.3, label='Slower than score')
        ax.fill_between(avg_times, tempo_ratios, 1.0,
                       where=np.array(tempo_ratios) < 1.0,
                       color='blue', alpha=0.3, label='Faster than score')
        
        ax.set_xlabel('Performance Time (seconds)', fontsize=12)
        ax.set_ylabel('Tempo Ratio (Score/Performance)', fontsize=12)
        ax.set_title('Tempo Variation Throughout Performance\n'
                    '(Above 1.0 = slower, Below 1.0 = faster)',
                    fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Add statistics
        avg_ratio = np.mean(tempo_ratios)
        std_ratio = np.std(tempo_ratios)
        
        stats_text = f"Average tempo ratio: {avg_ratio:.3f}\nVariation (std): {std_ratio:.3f}"
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
               fontsize=10)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {save_name}")
    
    def plot_beat_alignment(self, save_name: str = "5_beat_alignment.png"):
        """
        Plot 5: Beat Alignment Quality
        Shows how well beats match between score and performance
        """
        if not self.beats or not self.alignment:
            print("Skipping beat alignment plot: no data")
            return
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Extract beat data
        if isinstance(self.beats, dict) and 'beats' in self.beats:
            beats_list = self.beats['beats']
        else:
            beats_list = self.beats
        
        beat_times = [b['t'] for b in beats_list]
        beat_confs = [b.get('confidence', 1.0) for b in beats_list]
        
        # Scatter plot of beats with size by confidence
        sizes = [100 * conf for conf in beat_confs]
        colors = ['green' if c >= 0.8 else 'orange' if c >= 0.5 else 'red' for c in beat_confs]
        
        ax.scatter(beat_times, [1]*len(beat_times), s=sizes, c=colors, alpha=0.6, edgecolors='black')
        
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Beat Events', fontsize=12)
        ax.set_title('Beat Alignment with Confidence Weighting\n'
                    '(Larger circles = higher confidence, more weight in alignment)',
                    fontsize=14, fontweight='bold')
        ax.set_ylim(0.5, 1.5)
        ax.set_yticks([])
        ax.grid(True, alpha=0.3)
        
        # Legend
        high_patch = mpatches.Patch(color='green', label='High confidence (≥0.8)')
        med_patch = mpatches.Patch(color='orange', label='Medium confidence (0.5-0.8)')
        low_patch = mpatches.Patch(color='red', label='Low confidence (<0.5)')
        ax.legend(handles=[high_patch, med_patch, low_patch], loc='upper right')
        
        # Add interpretation
        interp_text = (
            "Beat weighting in action:\n"
            "• Bigger circles = more trusted\n"
            "• Alignment prefers matching\n"
            "  to high-confidence beats"
        )
        ax.text(0.02, 0.98, interp_text, transform=ax.transAxes,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
               fontsize=9)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {save_name}")
    
    def plot_summary_dashboard(self, save_name: str = "6_summary_dashboard.png"):
        """
        Plot 6: Performance Summary Dashboard
        Overall performance metrics with traffic light colors
        """
        if not self.context and not self.alignment:
            print("Skipping summary dashboard: no data")
            return
        
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.axis('off')
        
        # Collect metrics
        metrics = []
        
        if self.context and 'pitch_matches' in self.context:
            pitch_pct = self.context['pitch_matches']['match_percentage']
            pitch_color = 'green' if pitch_pct >= 85 else 'orange' if pitch_pct >= 70 else 'red'
            metrics.append({
                'name': 'Pitch Accuracy',
                'value': f"{pitch_pct:.1f}%",
                'color': pitch_color,
                'detail': f"({self.context['pitch_matches']['matches']}/{self.context['pitch_matches']['total_score_notes']} notes)"
            })
        
        if self.alignment and 'time_mapping' in self.alignment:
            # Calculate timing consistency (stays within band)
            time_mapping = self.alignment['time_mapping']
            in_band = 0
            for m in time_mapping:
                ratio = m['score_time'] / m['perf_time'] if m['perf_time'] > 0 else 1.0
                if 0.75 <= ratio <= 1.25:
                    in_band += 1
            
            timing_pct = (in_band / len(time_mapping)) * 100 if time_mapping else 0
            timing_color = 'green' if timing_pct >= 85 else 'orange' if timing_pct >= 70 else 'red'
            metrics.append({
                'name': 'Timing Consistency',
                'value': f"{timing_pct:.1f}%",
                'color': timing_color,
                'detail': f"(stayed within tempo band)"
            })
        
        if self.beats:
            if isinstance(self.beats, dict) and 'beats' in self.beats:
                beats_list = self.beats['beats']
            else:
                beats_list = self.beats
            
            avg_conf = np.mean([b.get('confidence', 1.0) for b in beats_list]) * 100
            beat_color = 'green' if avg_conf >= 80 else 'orange' if avg_conf >= 60 else 'red'
            metrics.append({
                'name': 'Beat Detection Quality',
                'value': f"{avg_conf:.1f}%",
                'color': beat_color,
                'detail': f"(average beat confidence)"
            })
        
        if self.scoregraph and 'nodes' in self.scoregraph:
            fermata_count = sum(1 for n in self.scoregraph['nodes'] 
                               if 'fermata' in n.get('flags', []))
            if fermata_count > 0:
                metrics.append({
                    'name': 'Fermata Handling',
                    'value': 'Detected',
                    'color': 'lightblue',
                    'detail': f"({fermata_count} fermatas in score)"
                })
        
        # Draw dashboard
        y_pos = 0.9
        
        # Title
        ax.text(0.5, 0.95, 'PERFORMANCE SUMMARY', 
               ha='center', va='top', fontsize=20, fontweight='bold',
               transform=ax.transAxes)
        
        # Draw each metric
        for metric in metrics:
            # Box for metric
            rect = plt.Rectangle((0.1, y_pos - 0.15), 0.8, 0.12,
                                facecolor=metric['color'], alpha=0.3,
                                edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            
            # Metric name
            ax.text(0.15, y_pos - 0.05, metric['name'],
                   fontsize=14, fontweight='bold', va='top')
            
            # Value
            ax.text(0.75, y_pos - 0.05, metric['value'],
                   fontsize=16, fontweight='bold', va='top', ha='right')
            
            # Detail
            ax.text(0.15, y_pos - 0.12, metric['detail'],
                   fontsize=10, va='top', style='italic')
            
            y_pos -= 0.18
        
        # Legend
        y_pos -= 0.05
        ax.text(0.5, y_pos, 'Color Guide:', ha='center', fontsize=12, fontweight='bold')
        y_pos -= 0.05
        legend_items = [
            ('green', 'Excellent (≥85%)'),
            ('orange', 'Good (70-85%)'),
            ('red', 'Needs Work (<70%)')
        ]
        for color, label in legend_items:
            rect = plt.Rectangle((0.25, y_pos - 0.03), 0.08, 0.02,
                                facecolor=color, alpha=0.5, edgecolor='black')
            ax.add_patch(rect)
            ax.text(0.35, y_pos - 0.02, label, fontsize=10, va='center')
            y_pos -= 0.05
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {save_name}")
    
    def generate_text_summary(self, save_name: str = "performance_summary.txt"):
        """Generate simple text summary file"""
        
        lines = []
        lines.append("PERFORMANCE ANALYSIS SUMMARY")
        lines.append("")
        
        # Context alignment results
        if self.context:
            lines.append("PITCH ACCURACY")
            lines.append("")
            matches = self.context['pitch_matches']
            lines.append(f"  Correct notes: {matches['matches']}")
            lines.append(f"  Total score notes: {matches['total_score_notes']}")
            lines.append(f"  Total performance notes: {matches['total_perf_notes']}")
            lines.append(f"  Accuracy: {matches['match_percentage']:.1f}%")
            
            if matches['match_percentage'] >= 90:
                lines.append(f"  Grade: EXCELLENT")
            elif matches['match_percentage'] >= 80:
                lines.append(f"  Grade: GOOD")
            elif matches['match_percentage'] >= 70:
                lines.append(f"  Grade: FAIR")
            else:
                lines.append(f"  Grade: NEEDS WORK")
            lines.append("")
        
        # Beat detection results
        if self.beats:
            lines.append("BEAT DETECTION")
            lines.append("")
            if isinstance(self.beats, dict) and 'beats' in self.beats:
                beats_list = self.beats['beats']
                if 'statistics' in self.beats:
                    stats = self.beats['statistics']
                    lines.append(f"  Total beats: {stats.get('total_beats', len(beats_list))}")
                    lines.append(f"  Downbeats: {stats.get('total_downbeats', 0)}")
                    lines.append(f"  Average confidence: {stats.get('avg_confidence', 0):.3f}")
            else:
                beats_list = self.beats
                lines.append(f"  Total beats: {len(beats_list)}")
                avg_conf = np.mean([b.get('confidence', 1.0) for b in beats_list])
                lines.append(f"  Average confidence: {avg_conf:.3f}")
            lines.append("")
        
        # Alignment results
        if self.alignment and 'time_mapping' in self.alignment:
            lines.append("TEMPORAL ALIGNMENT")
            lines.append("")
            time_mapping = self.alignment['time_mapping']
            lines.append(f"  Alignment points: {len(time_mapping)}")
            
            # Calculate tempo statistics
            tempo_ratios = []
            for i in range(1, len(time_mapping)):
                dt_score = time_mapping[i]['score_time'] - time_mapping[i-1]['score_time']
                dt_perf = time_mapping[i]['perf_time'] - time_mapping[i-1]['perf_time']
                if dt_perf > 0:
                    tempo_ratios.append(dt_score / dt_perf)
            
            if tempo_ratios:
                avg_ratio = np.mean(tempo_ratios)
                lines.append(f"  Average tempo ratio: {avg_ratio:.3f}")
                if avg_ratio > 1.05:
                    lines.append(f"  Overall: SLOWER than score")
                elif avg_ratio < 0.95:
                    lines.append(f"  Overall: FASTER than score")
                else:
                    lines.append(f"  Overall: MATCHED score tempo")
            
            # Count points within band
            in_band = sum(1 for m in time_mapping 
                         if 0.75 <= (m['score_time'] / m['perf_time'] if m['perf_time'] > 0 else 1.0) <= 1.25)
            timing_pct = (in_band / len(time_mapping)) * 100
            lines.append(f"  Timing consistency: {timing_pct:.1f}%")
            lines.append("")
        
        # Score features
        if self.scoregraph:
            lines.append("SCORE FEATURES")
            lines.append("")
            nodes = self.scoregraph.get('nodes', [])
            fermata_count = sum(1 for n in nodes if 'fermata' in n.get('flags', []))
            cadence_count = sum(1 for n in nodes if 'cadence' in n.get('flags', []))
            
            lines.append(f"  Total beats in score: {len(nodes)}")
            lines.append(f"  Fermatas detected: {fermata_count}")
            lines.append(f"  Cadences detected: {cadence_count}")
            
            if fermata_count > 0 or cadence_count > 0:
                lines.append(f"  Adaptive timing: ENABLED")
            lines.append("")
        
        lines.append("INTERPRETATION GUIDE")
        lines.append("")
        lines.append("Pitch Accuracy:")
        lines.append("  >90% = Excellent - You played the right notes")
        lines.append("  80-90% = Good - Minor mistakes")
        lines.append("  70-80% = Fair - Several wrong notes")
        lines.append("  <70% = Needs work - Practice more")
        lines.append("")
        lines.append("Timing Consistency:")
        lines.append("  >85% = Excellent - Steady tempo")
        lines.append("  70-85% = Good - Some variation")
        lines.append("  <70% = Needs work - Tempo unstable")
        
        # Write to file
        output_path = self.output_dir / save_name
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"Saved: {save_name}")
        
        # Also print to console
        print("\n" + '\n'.join(lines))
    
    def generate_all(self,
                    beats_path: Optional[str] = None,
                    context_path: Optional[str] = None,
                    alignment_path: Optional[str] = None,
                    scoregraph_path: Optional[str] = None):
        """Generate all visualizations and summary"""
        
        print("\nGenerating visualizations...")
        print(f"Output directory: {self.output_dir}")
        print()
        
        # Load data
        self.load_data(beats_path, context_path, alignment_path, scoregraph_path)
        
        # Generate each plot
        self.plot_beat_confidence()
        self.plot_alignment_path()
        self.plot_pitch_matching()
        self.plot_tempo_variation()
        self.plot_beat_alignment()
        self.plot_summary_dashboard()
        
        # Generate text summary
        self.generate_text_summary()
        
        print(f"\nAll visualizations saved to: {self.output_dir}")
        print("\nFiles created:")
        print("  1_beat_confidence.png - Beat detection with confidence")
        print("  2_alignment_path.png - Score/performance time mapping")
        print("  3_pitch_matching.png - Note accuracy")
        print("  4_tempo_variation.png - Speed changes over time")
        print("  5_beat_alignment.png - Beat weighting visualization")
        print("  6_summary_dashboard.png - Overall performance summary")
        print("  performance_summary.txt - Text summary of results")


def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate simple visualizations for alignment results'
    )
    parser.add_argument('--beats', help='Path to beats.json')
    parser.add_argument('--context', help='Path to context_alignment.json')
    parser.add_argument('--alignment', help='Path to alignment_results.json')
    parser.add_argument('--scoregraph', help='Path to scoregraph.json')
    parser.add_argument('--output', '-o', default='visualizations',
                       help='Output directory for visualizations')
    
    args = parser.parse_args()
    
    # Create visualizer
    viz = AlignmentVisualizer(output_dir=args.output)
    
    # Generate all visualizations
    viz.generate_all(
        beats_path=args.beats,
        context_path=args.context,
        alignment_path=args.alignment,
        scoregraph_path=args.scoregraph
    )
    
    print("\nVisualization complete!")
    return 0


if __name__ == "__main__":
    exit(main())
