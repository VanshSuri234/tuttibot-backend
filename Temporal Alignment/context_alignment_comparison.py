#!/usr/bin/env python3
"""
Context Alignment Comparison: Note-Level vs Phrase-Level

This script demonstrates the differences between:
1. Original note-by-note context alignment
2. New phrase-level context alignment

Shows how phrase detection works and what insights each approach provides.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os

# Add the Temporal Alignment directory to path
sys.path.append(str(Path(__file__).parent))

from context_aligner import ContextAligner
from phrase_context_aligner import PhraseContextAligner


def compare_alignment_approaches(score_graph_path: str, transcription_path: str, 
                               output_dir: str = "alignment_comparison"):
    """
    Compare note-level vs phrase-level context alignment approaches
    
    Args:
        score_graph_path: Path to ScoreGraph JSON
        transcription_path: Path to transcription JSON
        output_dir: Directory to save comparison results
    """
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print("🎵 Context Alignment Comparison: Note-Level vs Phrase-Level")
    print("=" * 60)
    
    # 1. Run original note-level alignment
    print("\n1️⃣  Running Note-Level Context Alignment...")
    note_aligner = ContextAligner()
    note_results = note_aligner.align(
        score_graph_path=score_graph_path,
        transcription_path=transcription_path,
        output_path=str(output_path / "note_level_alignment.json")
    )
    
    # 2. Run new phrase-level alignment
    print("\n2️⃣  Running Phrase-Level Context Alignment...")
    phrase_aligner = PhraseContextAligner()
    phrase_results = phrase_aligner.align(
        score_graph_path=score_graph_path,
        transcription_path=transcription_path,
        output_path=str(output_path / "phrase_level_alignment.json"),
        visualize=True
    )
    
    # 3. Create comparison visualization
    print("\n3️⃣  Creating Comparison Visualization...")
    create_comparison_visualization(note_results, phrase_results, output_path)
    
    # 4. Generate comparison report
    print("\n4️⃣  Generating Comparison Report...")
    create_comparison_report(note_results, phrase_results, output_path)
    
    print(f"\n✅ Comparison complete! Results saved to: {output_path}")
    
    return note_results, phrase_results


def create_comparison_visualization(note_results: dict, phrase_results: dict, 
                                  output_path: Path):
    """Create side-by-side visualization comparing both approaches"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Match Percentages Comparison
    ax1 = axes[0, 0]
    methods = ['Note-Level', 'Phrase-Level']
    note_match_pct = note_results.get('pitch_matches', {}).get('match_percentage', 0)
    phrase_match_pct = phrase_results.get('phrase_matches', {}).get('match_percentage', 0)
    
    match_percentages = [note_match_pct, phrase_match_pct]
    colors = ['skyblue', 'lightgreen']
    
    bars = ax1.bar(methods, match_percentages, color=colors, alpha=0.8)
    ax1.set_ylabel('Match Percentage (%)')
    ax1.set_title('Alignment Quality Comparison')
    ax1.set_ylim(0, 100)
    
    # Add value labels on bars
    for bar, value in zip(bars, match_percentages):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 2. Resolution Comparison
    ax2 = axes[0, 1]
    note_units = note_results.get('pitch_matches', {}).get('total_score_notes', 0)
    phrase_units = len(phrase_results.get('score_phrases', []))
    
    units = [note_units, phrase_units]
    ax2.bar(methods, units, color=colors, alpha=0.8)
    ax2.set_ylabel('Number of Units Analyzed')
    ax2.set_title('Analysis Granularity')
    
    for i, (method, unit_count) in enumerate(zip(methods, units)):
        ax2.text(i, unit_count + max(units)*0.02, str(unit_count), 
                ha='center', va='bottom', fontweight='bold')
    
    # 3. Phrase Structure (if available)
    ax3 = axes[1, 0]
    if 'score_phrases' in phrase_results:
        phrases = phrase_results['score_phrases']
        phrase_durations = [p['duration'] for p in phrases]
        phrase_types = [p['phrase_type'] for p in phrases]
        
        # Count phrase types
        type_counts = {}
        for ptype in phrase_types:
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
        
        if type_counts:
            ax3.pie(type_counts.values(), labels=type_counts.keys(), autopct='%1.1f%%')
            ax3.set_title('Detected Phrase Types')
    else:
        ax3.text(0.5, 0.5, 'No phrase structure\n(Note-level only)', 
                ha='center', va='center', transform=ax3.transAxes, fontsize=12)
        ax3.set_title('Phrase Structure Analysis')
    
    # 4. Alignment Scores
    ax4 = axes[1, 1]
    note_score = note_results.get('alignment_score', 0)
    phrase_score = phrase_results.get('alignment_score', 0)
    
    scores = [note_score, phrase_score]
    ax4.bar(methods, scores, color=colors, alpha=0.8)
    ax4.set_ylabel('Alignment Score')
    ax4.set_title('Raw Alignment Scores')
    
    for i, (method, score) in enumerate(zip(methods, scores)):
        ax4.text(i, score + max(scores)*0.02, f'{score:.1f}', 
                ha='center', va='bottom', fontweight='bold')
    
    plt.suptitle('Context Alignment: Note-Level vs Phrase-Level Comparison', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    viz_path = output_path / "alignment_comparison.png"
    plt.savefig(viz_path, dpi=300, bbox_inches='tight')
    print(f"  Comparison visualization saved: {viz_path}")
    plt.close()


def create_comparison_report(note_results: dict, phrase_results: dict, 
                           output_path: Path):
    """Generate detailed comparison report"""
    
    report_lines = [
        "# Context Alignment Comparison Report",
        "=" * 50,
        "",
        "## Executive Summary",
        "",
        "This report compares two approaches to context alignment:",
        "1. **Note-Level**: Aligns individual pitches using Needleman-Wunsch",
        "2. **Phrase-Level**: Groups notes into musical phrases, then aligns phrases",
        "",
        "## Results Overview",
        ""
    ]
    
    # Note-level results
    note_matches = note_results.get('pitch_matches', {})
    note_match_pct = note_matches.get('match_percentage', 0)
    note_total = note_matches.get('total_score_notes', 0)
    note_score = note_results.get('alignment_score', 0)
    
    report_lines.extend([
        "### Note-Level Analysis",
        f"- **Total Notes**: {note_total}",
        f"- **Match Percentage**: {note_match_pct:.1f}%",
        f"- **Alignment Score**: {note_score:.2f}",
        f"- **Granularity**: Individual pitch matches",
        f"- **Best For**: Precise pitch accuracy, note-by-note comparison",
        ""
    ])
    
    # Phrase-level results (if available)
    if 'phrase_matches' in phrase_results:
        phrase_matches = phrase_results.get('phrase_matches', {})
        phrase_match_pct = phrase_matches.get('match_percentage', 0)
        phrase_total = phrase_matches.get('total_score_phrases', 0)
        phrase_score = phrase_results.get('alignment_score', 0)
        
        score_phrases = phrase_results.get('score_phrases', [])
        perf_phrases = phrase_results.get('performance_phrases', [])
        
        report_lines.extend([
            "### Phrase-Level Analysis",
            f"- **Total Score Phrases**: {len(score_phrases)}",
            f"- **Total Performance Phrases**: {len(perf_phrases)}",
            f"- **Match Percentage**: {phrase_match_pct:.1f}%",
            f"- **Alignment Score**: {phrase_score:.2f}",
            f"- **Granularity**: Musical phrase segments",
            f"- **Best For**: Structural understanding, musical expression",
            ""
        ])
        
        # Phrase statistics
        if score_phrases:
            durations = [p['duration'] for p in score_phrases]
            note_counts = [p['note_count'] for p in score_phrases]
            
            report_lines.extend([
                "### Phrase Structure Details",
                f"- **Average Phrase Duration**: {np.mean(durations):.2f} beats",
                f"- **Phrase Duration Range**: {min(durations):.1f} - {max(durations):.1f} beats",
                f"- **Average Notes per Phrase**: {np.mean(note_counts):.1f}",
                f"- **Phrase Boundaries Detected**: {len(phrase_results.get('phrase_boundaries', []))}",
                ""
            ])
            
            # Phrase types
            phrase_types = [p['phrase_type'] for p in score_phrases]
            type_counts = {}
            for ptype in phrase_types:
                type_counts[ptype] = type_counts.get(ptype, 0) + 1
            
            report_lines.extend([
                "### Phrase Type Distribution",
                ""
            ])
            for ptype, count in type_counts.items():
                report_lines.append(f"- **{ptype.title()}**: {count} phrases")
            report_lines.append("")
    
    # Comparison insights
    report_lines.extend([
        "## Key Insights",
        "",
        "### When to Use Note-Level Analysis:",
        "- Precise pitch accuracy measurement",
        "- Detailed error detection (wrong notes, timing)",
        "- Student performance evaluation",
        "- Transcription quality assessment",
        "",
        "### When to Use Phrase-Level Analysis:",
        "- Musical structure understanding", 
        "- Expression and interpretation analysis",
        "- Large-scale form recognition",
        "- Stylistic pattern detection",
        "",
        "### Technical Differences:",
        "",
        "| Aspect | Note-Level | Phrase-Level |",
        "|--------|------------|--------------|",
        f"| Units Analyzed | {note_total} notes | {len(phrase_results.get('score_phrases', []))} phrases |",
        f"| Match Rate | {note_match_pct:.1f}% | {phrase_results.get('phrase_matches', {}).get('match_percentage', 0):.1f}% |",
        "| Resolution | Individual pitches | Musical segments |",
        "| Context | Local note comparison | Global phrase structure |",
        "| Musical Insight | Accuracy focused | Expression focused |",
        "",
        "## Recommendations",
        "",
        "**For Performance Analysis**: Use both approaches complementarily",
        "- Start with phrase-level to understand overall structure",
        "- Use note-level for detailed accuracy assessment",
        "",
        "**For Different Use Cases**:",
        "- **Music Education**: Note-level for error detection",
        "- **Performance Studies**: Phrase-level for interpretation analysis", 
        "- **Musicological Research**: Both for comprehensive analysis",
        "",
        f"Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ])
    
    # Write report
    report_path = output_path / "comparison_report.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"  Comparison report saved: {report_path}")


def demonstrate_phrase_detection(score_graph_path: str, output_path: str = "phrase_detection_demo.png"):
    """Create visualization showing how phrase boundaries are detected"""
    
    # Load score graph
    with open(score_graph_path, 'r') as f:
        score_graph = json.load(f)
    
    # Create phrase aligner and detect boundaries
    aligner = PhraseContextAligner()
    boundaries = aligner.detect_phrase_boundaries(score_graph)
    phrases = aligner.create_phrases_from_boundaries(score_graph, boundaries)
    
    # Create visualization
    fig, axes = plt.subplots(3, 1, figsize=(15, 10))
    
    # 1. Note timeline
    ax1 = axes[0]
    musical_notes = score_graph.get('musical_notes', [])
    if musical_notes:
        notes_sorted = sorted(musical_notes, key=lambda n: n['offset_beats'])
        
        for note in notes_sorted:
            start = note['offset_beats']
            duration = note.get('duration_beats', 0.5)
            pitch = note['pitch']
            
            # Plot as horizontal line with pitch as color
            ax1.barh(0, duration, left=start, height=0.8, 
                    color=plt.cm.viridis(pitch / 127), alpha=0.7)
    
    ax1.set_ylabel('All Notes')
    ax1.set_title('Musical Notes Timeline')
    ax1.grid(True, alpha=0.3)
    
    # 2. Phrase boundaries
    ax2 = axes[1]
    for i, boundary in enumerate(boundaries):
        ax2.axvline(x=boundary, color='red', linestyle='--', alpha=0.7)
        ax2.text(boundary, 0.5, f'B{i}', rotation=90, ha='right', va='center')
    
    ax2.set_ylabel('Boundaries')
    ax2.set_title(f'Detected Phrase Boundaries ({len(boundaries)-1} segments)')
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3)
    
    # 3. Detected phrases
    ax3 = axes[2]
    colors = ['skyblue', 'lightgreen', 'orange', 'pink', 'lightcoral']
    
    for i, phrase in enumerate(phrases):
        color = colors[i % len(colors)]
        ax3.barh(i, phrase.duration, left=phrase.start_beat, height=0.8,
                color=color, alpha=0.8, edgecolor='black')
        
        # Add phrase info
        ax3.text(phrase.start_beat + phrase.duration/2, i,
                f'{phrase.id}\n{len(phrase.notes)} notes\n{phrase.phrase_type}',
                ha='center', va='center', fontsize=8, fontweight='bold')
    
    ax3.set_ylabel('Detected Phrases')
    ax3.set_xlabel('Time (beats)')
    ax3.set_title(f'Musical Phrases ({len(phrases)} detected)')
    ax3.grid(True, alpha=0.3)
    
    plt.suptitle('Phrase Detection Process', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Phrase detection visualization saved: {output_path}")
    plt.close()


def main():
    """Run comparison demonstration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare Note-Level vs Phrase-Level Context Alignment')
    parser.add_argument('score_graph', help='Path to score_graph.json')
    parser.add_argument('transcription', help='Path to transcription.json')
    parser.add_argument('--output-dir', '-o', default='alignment_comparison',
                       help='Output directory for comparison results')
    
    args = parser.parse_args()
    
    # Run comparison
    note_results, phrase_results = compare_alignment_approaches(
        score_graph_path=args.score_graph,
        transcription_path=args.transcription,
        output_dir=args.output_dir
    )
    
    # Create phrase detection demo
    demo_path = Path(args.output_dir) / "phrase_detection_process.png"
    demonstrate_phrase_detection(args.score_graph, str(demo_path))
    
    print(f"\n🎯 Comparison Summary:")
    print(f"Note-level match rate: {note_results.get('pitch_matches', {}).get('match_percentage', 0):.1f}%")
    if 'phrase_matches' in phrase_results:
        print(f"Phrase-level match rate: {phrase_results.get('phrase_matches', {}).get('match_percentage', 0):.1f}%")
    print(f"Results directory: {args.output_dir}")


if __name__ == "__main__":
    main()