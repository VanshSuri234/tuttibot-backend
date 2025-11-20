#!/usr/bin/env python3
"""
Paper-Style Plot Generator for PQG-A2SA
======================================
Simple command-line tool that takes audio + MIDI and generates
publication-ready plots similar to those in the paper.

Usage:
    python3 generate_paper_plots.py <audio_file> <midi_file> [output_prefix]

Example:
    python3 generate_paper_plots.py song.wav song.mid my_results

Generates plots matching the paper's style and format.
"""

import sys
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.pipeline import PQGAligner
from src.config import PQGConfig
import pretty_midi

# Set publication style
plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.2)
plt.rcParams['figure.dpi'] = 300  # High quality
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']

def print_usage():
    """Print usage information"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         PQG-A2SA Paper-Style Plot Generator                   ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
    python3 generate_paper_plots.py <audio_file> <midi_file> [output_prefix]

Arguments:
    audio_file      Path to audio file (.wav, .mp3, etc.)
    midi_file       Path to MIDI score file (.mid, .midi)
    output_prefix   Optional output name (default: 'results')

Example:
    python3 generate_paper_plots.py Bach10/01.wav Bach10/01.mid bach01

Generates:
    • {prefix}_fig1_alignment_curve.png
    • {prefix}_fig2_error_histogram.png
    • {prefix}_fig3_alignment_rates.png
    • {prefix}_fig4_articulation_pie.png
    • {prefix}_fig5_timeline.png
    • {prefix}_summary_table.txt

All plots match the paper's publication style and format.
""")

def run_alignment(audio_file, midi_file):
    """Run PQG-A2SA alignment"""
    print("\n" + "="*70)
    print("RUNNING PQG-A2SA ALIGNMENT")
    print("="*70)
    
    config = PQGConfig()
    aligner = PQGAligner(config)
    
    print(f"\n📁 Input files:")
    print(f"   Audio: {audio_file}")
    print(f"   MIDI:  {midi_file}")
    
    # Run alignment
    print("\n🔄 Processing...")
    results = aligner.align(str(audio_file), str(midi_file), verbose=True)
    
    # Evaluate - load MIDI as reference
    print("\n📊 Evaluating...")
    midi = pretty_midi.PrettyMIDI(str(midi_file))
    reference_notes = {}
    for idx, inst in enumerate(midi.instruments):
        inst_notes = [{'onset': n.start, 'offset': n.end, 'pitch': n.pitch} for n in inst.notes]
        reference_notes[idx] = inst_notes
    
    eval_results = aligner.evaluate(results, reference_notes)
    
    # Add compatibility fields for plotting
    results['chord_onsets'] = results.get('chord_onsets_refined', [])
    total_notes = sum(len(inst['notes']) for inst in results['instruments'])
    results['statistics'] = {
        'total_notes': total_notes,
        'total_staccato': sum(sum(1 for n in inst['notes'] if n.get('articulation') == 'staccato') 
                            for inst in results['instruments']),
        'total_legato': sum(sum(1 for n in inst['notes'] if n.get('articulation') == 'legato') 
                          for inst in results['instruments']),
        'n_chords': len(results.get('chord_onsets_refined', []))
    }
    
    print("\n✅ Alignment complete!")
    print(f"   Total notes: {total_notes}")
    print(f"   MNE: {eval_results['overall']['MNE']*1000:.2f} ms")
    print(f"   MFE: {eval_results['overall']['MFE']*1000:.2f} ms")
    
    return results, eval_results
    
    return results, eval_results

def generate_fig1_alignment_curve(results, output_file):
    """
    Figure 1: Global Alignment Curve (Score vs Audio Time)
    Paper style: Clean line plot showing chord onset progression
    """
    print("\n📊 Generating Figure 1: Alignment Curve...")
    
    chord_onsets = results['chord_onsets']
    chord_indices = np.arange(len(chord_onsets))
    
    # Ideal linear tempo
    ideal = np.linspace(0, chord_onsets[-1], len(chord_onsets))
    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Plot lines
    ax.plot(chord_indices, ideal, 'k--', linewidth=1.5, 
            label='Constant Tempo', alpha=0.6)
    ax.plot(chord_indices, chord_onsets, 'b-', linewidth=2, 
            label='PQG-A2SA Alignment', marker='o', markersize=3, markevery=5)
    
    # Styling
    ax.set_xlabel('Chord Index', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time (s)', fontsize=12, fontweight='bold')
    ax.set_title('Score-to-Audio Alignment', fontsize=13, fontweight='bold')
    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    print(f"   ✓ Saved: {output_file}")
    plt.close()

def generate_fig2_error_histogram(results, eval_results, midi_file, output_file):
    """
    Figure 2: Error Distribution Histogram
    Paper style: Dual histogram showing onset/offset errors
    """
    print("\n📊 Generating Figure 2: Error Distribution...")
    
    # Collect errors
    midi = pretty_midi.PrettyMIDI(str(midi_file))
    onset_errors = []
    offset_errors = []
    
    for inst_data in results['instruments']:
        midi_inst = midi.instruments[inst_data['index']]
        for note in inst_data['notes']:
            for midi_note in midi_inst.notes:
                if (abs(midi_note.pitch - note['pitch']) < 1 and 
                    abs(midi_note.start - note['onset']) < 0.1):
                    onset_err = abs(note['onset'] - midi_note.start) * 1000
                    offset_err = abs(note['offset'] - midi_note.end) * 1000
                    onset_errors.append(onset_err)
                    offset_errors.append(offset_err)
                    break
    
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
    
    # Onset errors
    axes[0].hist(onset_errors, bins=20, color='steelblue', 
                edgecolor='navy', alpha=0.8)
    axes[0].axvline(np.mean(onset_errors), color='red', linestyle='--',
                   linewidth=2, label=f'Mean: {np.mean(onset_errors):.1f} ms')
    axes[0].set_xlabel('Onset Error (ms)', fontsize=11, fontweight='bold')
    axes[0].set_ylabel('Frequency', fontsize=11, fontweight='bold')
    axes[0].set_title('Note Error (NE)', fontsize=12, fontweight='bold')
    axes[0].legend(fontsize=9)
    axes[0].grid(axis='y', alpha=0.3)
    
    # Offset errors
    axes[1].hist(offset_errors, bins=20, color='coral', 
                edgecolor='darkred', alpha=0.8)
    axes[1].axvline(np.mean(offset_errors), color='red', linestyle='--',
                   linewidth=2, label=f'Mean: {np.mean(offset_errors):.1f} ms')
    axes[1].set_xlabel('Offset Error (ms)', fontsize=11, fontweight='bold')
    axes[1].set_ylabel('Frequency', fontsize=11, fontweight='bold')
    axes[1].set_title('Frame Error (FE)', fontsize=12, fontweight='bold')
    axes[1].legend(fontsize=9)
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    print(f"   ✓ Saved: {output_file}")
    plt.close()

def generate_fig3_alignment_rates(eval_results, output_file):
    """
    Figure 3: Alignment Rate Bar Chart
    Paper style: Bar chart showing cumulative alignment rates
    """
    print("\n📊 Generating Figure 3: Alignment Rates...")
    
    overall = eval_results['overall']
    thresholds = [30, 60, 90, 120, 150, 200]
    onset_rates = [overall['onset_alignment_rates'].get(t, 0.0) for t in thresholds]
    offset_rates = [overall['offset_alignment_rates'].get(t, 0.0) for t in thresholds]
    
    x = np.arange(len(thresholds))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(7, 4))
    
    bars1 = ax.bar(x - width/2, onset_rates, width, label='Onset',
                   color='steelblue', edgecolor='navy', linewidth=1.5)
    bars2 = ax.bar(x + width/2, offset_rates, width, label='Offset',
                   color='coral', edgecolor='darkred', linewidth=1.5)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}%', ha='center', va='bottom', 
                   fontsize=8, fontweight='bold')
    
    ax.set_xlabel('Error Threshold (ms)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Alignment Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Alignment Performance at Different Thresholds', 
                fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'≤{t}' for t in thresholds])
    ax.legend(frameon=True, fancybox=True, shadow=True)
    ax.set_ylim([0, 105])
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    print(f"   ✓ Saved: {output_file}")
    plt.close()

def generate_fig4_articulation_pie(results, output_file):
    """
    Figure 4: Articulation Detection Pie Chart
    Paper style: Clean pie chart with percentage labels
    """
    print("\n📊 Generating Figure 4: Articulation Distribution...")
    
    stats = results['statistics']
    total = stats['total_notes']
    staccato = stats['total_staccato']
    legato = stats['total_legato']
    uncertain = total - staccato - legato
    
    sizes = [staccato, legato, uncertain]
    labels = ['Staccato', 'Legato', 'Uncertain']
    colors = ['#E74C3C', '#3498DB', '#F39C12']  # Red, Blue, Orange
    explode = (0.05, 0.05, 0.05)
    
    fig, ax = plt.subplots(figsize=(6, 6))
    
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels,
                                       colors=colors, autopct='%1.1f%%',
                                       shadow=True, startangle=90,
                                       textprops={'fontsize': 11, 'fontweight': 'bold'})
    
    # Enhance text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')
    
    ax.set_title('Articulation Type Distribution', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Add counts as subtitle
    subtitle = f'Total Notes: {total} (Staccato: {staccato}, Legato: {legato}, Uncertain: {uncertain})'
    fig.text(0.5, 0.02, subtitle, ha='center', fontsize=9, style='italic')
    
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    print(f"   ✓ Saved: {output_file}")
    plt.close()

def generate_fig5_timeline(results, output_file, time_window=10.0):
    """
    Figure 5: Piano Roll Timeline with Articulation
    Paper style: Multi-track piano roll showing notes colored by articulation
    """
    print("\n📊 Generating Figure 5: Note Timeline...")
    
    n_instruments = len(results['instruments'])
    fig, axes = plt.subplots(n_instruments, 1, figsize=(10, 2*n_instruments), 
                             sharex=True)
    
    if n_instruments == 1:
        axes = [axes]
    
    colors = {'staccato': '#E74C3C', 'legato': '#3498DB', 'uncertain': '#95A5A6'}
    
    for idx, (ax, inst_data) in enumerate(zip(axes, results['instruments'])):
        # Plot notes as rectangles
        for note in inst_data['notes']:
            if note['onset'] > time_window:
                break
            
            onset = note['onset']
            offset = min(note['offset'], time_window)
            duration = offset - onset
            pitch = note['pitch']
            color = colors[note['articulation']]
            
            # Draw note rectangle
            rect = plt.Rectangle((onset, pitch - 0.4), duration, 0.8,
                                facecolor=color, edgecolor='black',
                                linewidth=0.8, alpha=0.85)
            ax.add_patch(rect)
        
        # Styling
        ax.set_ylabel(f"Inst. {idx+1}\nPitch", fontsize=10, fontweight='bold')
        ax.set_ylim([40, 85])
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_yticks(range(48, 85, 12))
        
        # Instrument name
        ax.text(0.01, 0.95, inst_data['name'], transform=ax.transAxes,
               fontsize=9, verticalalignment='top', fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    axes[-1].set_xlabel('Time (s)', fontsize=12, fontweight='bold')
    axes[-1].set_xlim([0, time_window])
    
    # Title
    fig.suptitle(f'Note Timeline (First {time_window:.0f} seconds)', 
                fontsize=14, fontweight='bold', y=0.995)
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#E74C3C', edgecolor='black', label='Staccato'),
        Patch(facecolor='#3498DB', edgecolor='black', label='Legato'),
        Patch(facecolor='#95A5A6', edgecolor='black', label='Uncertain')
    ]
    fig.legend(handles=legend_elements, loc='upper right', 
              fontsize=10, frameon=True, fancybox=True, shadow=True,
              bbox_to_anchor=(0.98, 0.98))
    
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    print(f"   ✓ Saved: {output_file}")
    plt.close()

def generate_summary_table(results, eval_results, output_file):
    """
    Generate a text summary table (like in papers)
    """
    print("\n📊 Generating Summary Table...")
    
    stats = results['statistics']
    overall = eval_results['overall']
    
    summary = f"""
╔═══════════════════════════════════════════════════════════════╗
║              PQG-A2SA ALIGNMENT RESULTS SUMMARY               ║
╚═══════════════════════════════════════════════════════════════╝

DATASET INFORMATION
───────────────────────────────────────────────────────────────
Total Notes:              {stats['total_notes']}
Total Chords:             {stats['n_chords']}
Number of Instruments:    {len(results['instruments'])}
Audio Duration:           {results['chord_onsets'][-1]:.2f} seconds

ALIGNMENT METRICS
───────────────────────────────────────────────────────────────
Mean Note Error (MNE):    {overall['MNE']*1000:.2f} ms
Mean Frame Error (MFE):   {overall['MFE']*1000:.2f} ms

Total Notes Evaluated:    {overall['n_notes']}

ARTICULATION DETECTION
───────────────────────────────────────────────────────────────
Staccato:                 {stats['total_staccato']:3d} notes ({stats['total_staccato']/stats['total_notes']*100:5.1f}%)
Legato:                   {stats['total_legato']:3d} notes ({stats['total_legato']/stats['total_notes']*100:5.1f}%)
Uncertain:                {stats['total_notes']-stats['total_staccato']-stats['total_legato']:3d} notes ({(stats['total_notes']-stats['total_staccato']-stats['total_legato'])/stats['total_notes']*100:5.1f}%)

ONSET ALIGNMENT RATES (at different thresholds)
───────────────────────────────────────────────────────────────
  ≤  30 ms:  {overall['onset_alignment_rates'].get(30, 0.0):6.2f}%
  ≤  60 ms:  {overall['onset_alignment_rates'].get(60, 0.0):6.2f}%
  ≤  90 ms:  {overall['onset_alignment_rates'].get(90, 0.0):6.2f}%
  ≤ 120 ms:  {overall['onset_alignment_rates'].get(120, 0.0):6.2f}%
  ≤ 150 ms:  {overall['onset_alignment_rates'].get(150, 0.0):6.2f}%
  ≤ 200 ms:  {overall['onset_alignment_rates'].get(200, 0.0):6.2f}%

OFFSET ALIGNMENT RATES (at different thresholds)
───────────────────────────────────────────────────────────────
  ≤  30 ms:  {overall['offset_alignment_rates'].get(30, 0.0):6.2f}%
  ≤  60 ms:  {overall['offset_alignment_rates'].get(60, 0.0):6.2f}%
  ≤  90 ms:  {overall['offset_alignment_rates'].get(90, 0.0):6.2f}%
  ≤ 120 ms:  {overall['offset_alignment_rates'].get(120, 0.0):6.2f}%
  ≤ 150 ms:  {overall['offset_alignment_rates'].get(150, 0.0):6.2f}%
  ≤ 200 ms:  {overall['offset_alignment_rates'].get(200, 0.0):6.2f}%

PER-INSTRUMENT BREAKDOWN
───────────────────────────────────────────────────────────────
"""
    
    for inst in results['instruments']:
        notes = inst['notes']
        staccato = sum(1 for n in notes if n['articulation'] == 'staccato')
        legato = sum(1 for n in notes if n['articulation'] == 'legato')
        uncertain = len(notes) - staccato - legato
        
        summary += f"""
{inst['name']:20s}  {len(notes):3d} notes  (S:{staccato:2d} L:{legato:2d} U:{uncertain:2d})"""
    
    summary += """

CONFIGURATION PARAMETERS
───────────────────────────────────────────────────────────────
"""
    if 'metadata' in results and 'config' in results['metadata']:
        config_info = results['metadata']['config']
        for key, val in config_info.items():
            summary += f"{key:25s} = {val}\n"
    else:
        summary += "HOP_LENGTH                = 1024\n"
        summary += "K_CL                      = 10\n"
        summary += "IOI_DELTA                 = 4\n"
        summary += "NMF_ITERATIONS            = 150\n"
    
    summary += """
═══════════════════════════════════════════════════════════════

Generated by PQG-A2SA Implementation
Algorithm: Lian, Cheng & Zhang (2023)
"""
    
    with open(output_file, 'w') as f:
        f.write(summary)
    
    print(f"   ✓ Saved: {output_file}")

def main():
    """Main execution"""
    
    # Check arguments
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    audio_file = Path(sys.argv[1])
    midi_file = Path(sys.argv[2])
    output_prefix = sys.argv[3] if len(sys.argv) > 3 else 'results'
    
    # Validate files
    if not audio_file.exists():
        print(f"❌ Error: Audio file not found: {audio_file}")
        sys.exit(1)
    
    if not midi_file.exists():
        print(f"❌ Error: MIDI file not found: {midi_file}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path("paper_plots")
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*70)
    print("         PQG-A2SA PAPER-STYLE PLOT GENERATOR")
    print("="*70)
    print(f"\n📂 Output directory: {output_dir}/")
    print(f"📝 Output prefix: {output_prefix}")
    
    # Run alignment
    results, eval_results = run_alignment(audio_file, midi_file)
    
    # Generate all plots
    print("\n" + "="*70)
    print("GENERATING PAPER-STYLE PLOTS")
    print("="*70)
    
    generate_fig1_alignment_curve(
        results, 
        output_dir / f"{output_prefix}_fig1_alignment_curve.png"
    )
    
    generate_fig2_error_histogram(
        results, eval_results, midi_file,
        output_dir / f"{output_prefix}_fig2_error_histogram.png"
    )
    
    generate_fig3_alignment_rates(
        eval_results,
        output_dir / f"{output_prefix}_fig3_alignment_rates.png"
    )
    
    generate_fig4_articulation_pie(
        results,
        output_dir / f"{output_prefix}_fig4_articulation_pie.png"
    )
    
    generate_fig5_timeline(
        results,
        output_dir / f"{output_prefix}_fig5_timeline.png",
        time_window=10.0
    )
    
    generate_summary_table(
        results, eval_results,
        output_dir / f"{output_prefix}_summary_table.txt"
    )
    
    # Final summary
    print("\n" + "="*70)
    print("✅ ALL PLOTS GENERATED SUCCESSFULLY!")
    print("="*70)
    print(f"\n📁 Output files in: {output_dir}/")
    print(f"\n📊 Generated plots:")
    print(f"   • {output_prefix}_fig1_alignment_curve.png")
    print(f"   • {output_prefix}_fig2_error_histogram.png")
    print(f"   • {output_prefix}_fig3_alignment_rates.png")
    print(f"   • {output_prefix}_fig4_articulation_pie.png")
    print(f"   • {output_prefix}_fig5_timeline.png")
    print(f"   • {output_prefix}_summary_table.txt")
    
    print(f"\n📈 Key Results:")
    overall = eval_results['overall']
    print(f"   MNE: {overall['MNE']*1000:.2f} ms")
    print(f"   MFE: {overall['MFE']*1000:.2f} ms")
    print(f"   Offset alignment ≤200ms: {overall['offset_alignment_rates'].get(200, 0.0):.1f}%")
    print(f"   Articulation detected: {results['statistics']['total_staccato']+results['statistics']['total_legato']}/{results['statistics']['total_notes']} notes")
    
    print("\n" + "="*70)
    print("🎉 Done! Your paper-quality plots are ready.")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
