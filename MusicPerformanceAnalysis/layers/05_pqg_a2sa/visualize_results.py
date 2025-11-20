#!/usr/bin/env python3
"""
PQG-A2SA Visualization Script
============================
Creates comprehensive plots based on PQG-A2SA_Plots_and_Visualizations.txt

Implements:
1. Global Alignment Curve (Score vs Audio Time)
2. Error Distribution (MNE/MFE Histogram)
3. Offset Alignment Rates (Bar Chart)
4. Articulation Distribution (Pie Chart)
5. Per-Instrument Statistics (Grouped Bar)
6. Error Scatter Plot (Per-Note Errors)
7. Offset Error Box Plot (Per-Instrument)
8. Timeline Visualization (Notes with Articulation)

Additional plots:
9. Chord Onset Timeline
10. Duration Distribution by Articulation
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def load_data():
    """Load alignment and evaluation results"""
    results_dir = Path("results")
    
    with open(results_dir / "bach10_01_alignment.json", 'r') as f:
        alignment = json.load(f)
    
    with open(results_dir / "bach10_01_evaluation.json", 'r') as f:
        evaluation = json.load(f)
    
    return alignment, evaluation

def load_midi_reference():
    """Load original MIDI for comparison"""
    import pretty_midi
    midi = pretty_midi.PrettyMIDI("../Bach_10_Dataset/01-AchGottundHerr.mid")
    return midi

def plot_1_global_alignment_curve(alignment):
    """Plot 1: Global Alignment Curve (Chord Onsets)"""
    chord_onsets = alignment['chord_onsets']
    chord_indices = np.arange(len(chord_onsets))
    
    # Since we don't have "before" data, we'll simulate ideal linear tempo
    midi = load_midi_reference()
    audio_duration = chord_onsets[-1]
    
    # Ideal linear mapping
    ideal_onsets = np.linspace(0, audio_duration, len(chord_onsets))
    
    plt.figure(figsize=(12, 6))
    plt.plot(chord_indices, ideal_onsets, 'g--', linewidth=2, label='Ideal Linear Tempo', alpha=0.7)
    plt.plot(chord_indices, chord_onsets, 'b-', linewidth=2, label='PQG-A2SA Alignment')
    
    plt.xlabel('Chord Index', fontsize=12)
    plt.ylabel('Audio Time (seconds)', fontsize=12)
    plt.title('Global Alignment Curve: Score vs Audio Time', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('results/plot_01_global_alignment.png', dpi=150)
    print("✓ Saved: plot_01_global_alignment.png")
    plt.close()

def plot_2_error_distribution(alignment, evaluation):
    """Plot 2: MNE/MFE Error Distribution Histogram"""
    # Collect offset errors for each note
    midi = load_midi_reference()
    offset_errors = []
    
    for inst_data in alignment['instruments']:
        for note in inst_data['notes']:
            # Find corresponding MIDI note
            midi_inst = midi.instruments[inst_data['index']]
            for midi_note in midi_inst.notes:
                if abs(midi_note.pitch - note['pitch']) < 1 and abs(midi_note.start - note['onset']) < 0.1:
                    error_ms = abs(note['offset'] - midi_note.end) * 1000
                    offset_errors.append(error_ms)
                    break
    
    offset_errors = np.array(offset_errors)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # MNE (all zeros since onsets not refined)
    axes[0].bar(['MNE'], [evaluation['MNE_ms']], color='skyblue', edgecolor='navy', linewidth=2)
    axes[0].set_ylabel('Error (ms)', fontsize=12)
    axes[0].set_title('Mean Note Error (Onset)', fontsize=13, fontweight='bold')
    axes[0].set_ylim([0, 10])
    axes[0].text(0, evaluation['MNE_ms'] + 0.5, f"{evaluation['MNE_ms']:.2f} ms", 
                 ha='center', fontsize=11, fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)
    
    # MFE histogram
    axes[1].hist(offset_errors, bins=30, color='coral', edgecolor='darkred', alpha=0.7)
    axes[1].axvline(evaluation['MFE_ms'], color='red', linestyle='--', linewidth=2, 
                    label=f'Mean: {evaluation["MFE_ms"]:.2f} ms')
    axes[1].axvline(np.median(offset_errors), color='green', linestyle='--', linewidth=2,
                    label=f'Median: {np.median(offset_errors):.2f} ms')
    axes[1].set_xlabel('Offset Error (ms)', fontsize=12)
    axes[1].set_ylabel('Frequency', fontsize=12)
    axes[1].set_title('Frame Error Distribution (Offset)', fontsize=13, fontweight='bold')
    axes[1].legend(fontsize=10)
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/plot_02_error_distribution.png', dpi=150)
    print("✓ Saved: plot_02_error_distribution.png")
    plt.close()

def plot_3_alignment_rates(evaluation):
    """Plot 3: Offset Alignment Rates"""
    thresholds = [30, 60, 90, 120, 150, 180, 200]
    rates = [evaluation['offset_rates'][str(t)] for t in thresholds]
    
    plt.figure(figsize=(10, 6))
    colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(thresholds)))
    bars = plt.bar([f'≤{t}ms' for t in thresholds], rates, color=colors, 
                    edgecolor='black', linewidth=1.5)
    
    # Add percentage labels on bars
    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.xlabel('Error Threshold', fontsize=12)
    plt.ylabel('Alignment Rate (%)', fontsize=12)
    plt.title('Offset Alignment Rates at Different Thresholds', fontsize=14, fontweight='bold')
    plt.ylim([0, 105])
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('results/plot_03_alignment_rates.png', dpi=150)
    print("✓ Saved: plot_03_alignment_rates.png")
    plt.close()

def plot_4_articulation_distribution(alignment):
    """Plot 4: Articulation Distribution (Pie Chart)"""
    stats = alignment['statistics']
    total = stats['total_notes']
    staccato = stats['total_staccato']
    legato = stats['total_legato']
    uncertain = total - staccato - legato
    
    labels = ['Staccato', 'Legato', 'Uncertain']
    sizes = [staccato, legato, uncertain]
    colors = ['#ff6b6b', '#4ecdc4', '#ffe66d']
    explode = (0.05, 0.05, 0.05)
    
    plt.figure(figsize=(10, 7))
    wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                        startangle=90, explode=explode, shadow=True,
                                        textprops={'fontsize': 12, 'fontweight': 'bold'})
    
    # Add counts
    for i, (label, size) in enumerate(zip(labels, sizes)):
        angle = (wedges[i].theta2 + wedges[i].theta1) / 2
        texts[i].set_text(f'{label}\n({size} notes)')
    
    plt.title('Articulation Detection Distribution', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('results/plot_04_articulation_distribution.png', dpi=150)
    print("✓ Saved: plot_04_articulation_distribution.png")
    plt.close()

def plot_5_per_instrument_stats(alignment):
    """Plot 5: Per-Instrument Statistics (Grouped Bar)"""
    instruments = []
    staccato_counts = []
    legato_counts = []
    uncertain_counts = []
    
    for inst in alignment['instruments']:
        instruments.append(inst['name'])
        notes = inst['notes']
        staccato_counts.append(sum(1 for n in notes if n['articulation'] == 'staccato'))
        legato_counts.append(sum(1 for n in notes if n['articulation'] == 'legato'))
        uncertain_counts.append(sum(1 for n in notes if n['articulation'] == 'uncertain'))
    
    x = np.arange(len(instruments))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width, staccato_counts, width, label='Staccato', color='#ff6b6b', edgecolor='black')
    bars2 = ax.bar(x, legato_counts, width, label='Legato', color='#4ecdc4', edgecolor='black')
    bars3 = ax.bar(x + width, uncertain_counts, width, label='Uncertain', color='#ffe66d', edgecolor='black')
    
    # Add counts on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('Instrument', fontsize=12)
    ax.set_ylabel('Number of Notes', fontsize=12)
    ax.set_title('Articulation Detection by Instrument', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(instruments)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('results/plot_05_per_instrument_stats.png', dpi=150)
    print("✓ Saved: plot_05_per_instrument_stats.png")
    plt.close()

def plot_6_error_scatter(alignment):
    """Plot 6: Per-Note Offset Errors (Scatter)"""
    midi = load_midi_reference()
    
    note_indices = []
    offset_errors = []
    colors_by_artic = []
    
    color_map = {'staccato': '#ff6b6b', 'legato': '#4ecdc4', 'uncertain': '#ffe66d'}
    
    idx = 0
    for inst_data in alignment['instruments']:
        midi_inst = midi.instruments[inst_data['index']]
        for note in inst_data['notes']:
            for midi_note in midi_inst.notes:
                if abs(midi_note.pitch - note['pitch']) < 1 and abs(midi_note.start - note['onset']) < 0.1:
                    error_ms = abs(note['offset'] - midi_note.end) * 1000
                    note_indices.append(idx)
                    offset_errors.append(error_ms)
                    colors_by_artic.append(color_map[note['articulation']])
                    idx += 1
                    break
    
    plt.figure(figsize=(14, 6))
    plt.scatter(note_indices, offset_errors, c=colors_by_artic, s=50, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    # Add threshold lines
    plt.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='30ms threshold')
    plt.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='200ms threshold')
    plt.axhline(y=np.median(offset_errors), color='blue', linestyle='-', linewidth=2, 
                label=f'Median: {np.median(offset_errors):.1f}ms')
    
    # Create legend for articulation
    staccato_patch = mpatches.Patch(color='#ff6b6b', label='Staccato')
    legato_patch = mpatches.Patch(color='#4ecdc4', label='Legato')
    uncertain_patch = mpatches.Patch(color='#ffe66d', label='Uncertain')
    
    handles, labels = plt.gca().get_legend_handles_labels()
    handles.extend([staccato_patch, legato_patch, uncertain_patch])
    
    plt.xlabel('Note Index', fontsize=12)
    plt.ylabel('Offset Error (ms)', fontsize=12)
    plt.title('Per-Note Offset Errors (Colored by Articulation)', fontsize=14, fontweight='bold')
    plt.legend(handles=handles, fontsize=9, loc='upper right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('results/plot_06_error_scatter.png', dpi=150)
    print("✓ Saved: plot_06_error_scatter.png")
    plt.close()

def plot_7_error_boxplot(alignment):
    """Plot 7: Offset Error Distribution by Instrument (Box Plot)"""
    midi = load_midi_reference()
    
    data_by_instrument = {inst['name']: [] for inst in alignment['instruments']}
    
    for inst_data in alignment['instruments']:
        midi_inst = midi.instruments[inst_data['index']]
        for note in inst_data['notes']:
            for midi_note in midi_inst.notes:
                if abs(midi_note.pitch - note['pitch']) < 1 and abs(midi_note.start - note['onset']) < 0.1:
                    error_ms = abs(note['offset'] - midi_note.end) * 1000
                    data_by_instrument[inst_data['name']].append(error_ms)
                    break
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    positions = range(1, len(data_by_instrument) + 1)
    bp = ax.boxplot(data_by_instrument.values(), positions=positions, patch_artist=True,
                     notch=True, showmeans=True,
                     boxprops=dict(facecolor='lightblue', edgecolor='navy', linewidth=1.5),
                     medianprops=dict(color='red', linewidth=2),
                     meanprops=dict(marker='D', markerfacecolor='green', markersize=8),
                     whiskerprops=dict(linewidth=1.5),
                     capprops=dict(linewidth=1.5))
    
    ax.set_xticklabels(data_by_instrument.keys())
    ax.set_xlabel('Instrument', fontsize=12)
    ax.set_ylabel('Offset Error (ms)', fontsize=12)
    ax.set_title('Offset Error Distribution by Instrument', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add legend
    median_line = plt.Line2D([], [], color='red', linewidth=2, label='Median')
    mean_marker = plt.Line2D([], [], color='green', marker='D', linestyle='None', 
                            markersize=8, label='Mean')
    ax.legend(handles=[median_line, mean_marker], fontsize=10)
    
    plt.tight_layout()
    plt.savefig('results/plot_07_error_boxplot.png', dpi=150)
    print("✓ Saved: plot_07_error_boxplot.png")
    plt.close()

def plot_8_timeline_visualization(alignment):
    """Plot 8: Timeline Visualization (First 10 seconds)"""
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    
    time_limit = 10.0  # Show first 10 seconds
    color_map = {'staccato': '#ff6b6b', 'legato': '#4ecdc4', 'uncertain': '#ffe66d'}
    
    for idx, inst_data in enumerate(alignment['instruments']):
        ax = axes[idx]
        
        for note in inst_data['notes']:
            if note['onset'] > time_limit:
                break
            
            onset = note['onset']
            offset = min(note['offset'], time_limit)
            duration = offset - onset
            pitch = note['pitch']
            artic = note['articulation']
            
            # Draw rectangle for note
            rect = mpatches.Rectangle((onset, pitch - 0.4), duration, 0.8,
                                     facecolor=color_map[artic], edgecolor='black',
                                     linewidth=1, alpha=0.7)
            ax.add_patch(rect)
        
        ax.set_ylabel(inst_data['name'], fontsize=11, fontweight='bold')
        ax.set_ylim([40, 80])
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_yticks(range(40, 81, 10))
    
    axes[-1].set_xlabel('Time (seconds)', fontsize=12)
    fig.suptitle('Note Timeline Visualization (First 10 seconds)', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    # Create legend
    staccato_patch = mpatches.Patch(color='#ff6b6b', label='Staccato')
    legato_patch = mpatches.Patch(color='#4ecdc4', label='Legato')
    uncertain_patch = mpatches.Patch(color='#ffe66d', label='Uncertain')
    fig.legend(handles=[staccato_patch, legato_patch, uncertain_patch],
              loc='upper right', fontsize=10, bbox_to_anchor=(0.99, 0.99))
    
    plt.tight_layout()
    plt.savefig('results/plot_08_timeline_visualization.png', dpi=150)
    print("✓ Saved: plot_08_timeline_visualization.png")
    plt.close()

def plot_9_chord_onset_timeline(alignment):
    """Plot 9: Chord Onset Timeline"""
    chord_onsets = alignment['chord_onsets']
    
    plt.figure(figsize=(14, 6))
    plt.stem(range(len(chord_onsets)), chord_onsets, basefmt=' ', linefmt='b-', markerfmt='bo')
    
    plt.xlabel('Chord Index', fontsize=12)
    plt.ylabel('Audio Time (seconds)', fontsize=12)
    plt.title('Chord Onset Timeline', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('results/plot_09_chord_timeline.png', dpi=150)
    print("✓ Saved: plot_09_chord_timeline.png")
    plt.close()

def plot_10_duration_by_articulation(alignment):
    """Plot 10: Note Duration Distribution by Articulation"""
    durations_by_artic = {'staccato': [], 'legato': [], 'uncertain': []}
    
    for inst_data in alignment['instruments']:
        for note in inst_data['notes']:
            duration_ms = (note['offset'] - note['onset']) * 1000
            durations_by_artic[note['articulation']].append(duration_ms)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    positions = [1, 2, 3]
    labels = ['Staccato', 'Legato', 'Uncertain']
    colors = ['#ff6b6b', '#4ecdc4', '#ffe66d']
    
    bp = ax.boxplot([durations_by_artic['staccato'], 
                      durations_by_artic['legato'],
                      durations_by_artic['uncertain']],
                     positions=positions, patch_artist=True, notch=True,
                     showmeans=True,
                     medianprops=dict(color='red', linewidth=2),
                     meanprops=dict(marker='D', markerfacecolor='green', markersize=8))
    
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('black')
        patch.set_linewidth(1.5)
    
    ax.set_xticklabels(labels)
    ax.set_xlabel('Articulation Type', fontsize=12)
    ax.set_ylabel('Note Duration (ms)', fontsize=12)
    ax.set_title('Note Duration Distribution by Articulation', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add statistics
    for i, artic in enumerate(['staccato', 'legato', 'uncertain'], 1):
        median = np.median(durations_by_artic[artic])
        mean = np.mean(durations_by_artic[artic])
        ax.text(i, ax.get_ylim()[1] * 0.95, 
               f'Med: {median:.0f}ms\nMean: {mean:.0f}ms',
               ha='center', va='top', fontsize=9, 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('results/plot_10_duration_distribution.png', dpi=150)
    print("✓ Saved: plot_10_duration_distribution.png")
    plt.close()

def create_summary_figure(alignment, evaluation):
    """Create a single comprehensive summary figure"""
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. MNE/MFE bars
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.bar(['MNE', 'MFE'], [evaluation['MNE_ms'], evaluation['MFE_ms']], 
           color=['skyblue', 'coral'], edgecolor='black', linewidth=2)
    ax1.set_ylabel('Error (ms)', fontsize=10)
    ax1.set_title('Onset/Offset Errors', fontweight='bold', fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    for i, (label, val) in enumerate([('MNE', evaluation['MNE_ms']), ('MFE', evaluation['MFE_ms'])]):
        ax1.text(i, val + 5, f'{val:.1f}', ha='center', fontsize=9)
    
    # 2. Articulation pie
    ax2 = fig.add_subplot(gs[0, 1])
    stats = alignment['statistics']
    sizes = [stats['total_staccato'], stats['total_legato'], 
            stats['total_notes'] - stats['total_staccato'] - stats['total_legato']]
    colors = ['#ff6b6b', '#4ecdc4', '#ffe66d']
    ax2.pie(sizes, labels=['Staccato', 'Legato', 'Uncertain'], colors=colors,
           autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
    ax2.set_title('Articulation Distribution', fontweight='bold', fontsize=11)
    
    # 3. Alignment rates
    ax3 = fig.add_subplot(gs[0, 2])
    thresholds = [30, 60, 90, 120, 150, 200]
    rates = [evaluation['offset_rates'][str(t)] for t in thresholds]
    ax3.bar(range(len(thresholds)), rates, color=plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(thresholds))),
           edgecolor='black')
    ax3.set_xticks(range(len(thresholds)))
    ax3.set_xticklabels([f'{t}' for t in thresholds], fontsize=8)
    ax3.set_xlabel('Threshold (ms)', fontsize=9)
    ax3.set_ylabel('Rate (%)', fontsize=9)
    ax3.set_title('Offset Alignment Rates', fontweight='bold', fontsize=11)
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Timeline (condensed)
    ax4 = fig.add_subplot(gs[1, :])
    color_map = {'staccato': '#ff6b6b', 'legato': '#4ecdc4', 'uncertain': '#ffe66d'}
    for inst_idx, inst_data in enumerate(alignment['instruments']):
        y_base = inst_idx * 20
        for note in inst_data['notes'][:15]:  # First 15 notes only
            onset = note['onset']
            duration = note['offset'] - note['onset']
            rect = mpatches.Rectangle((onset, y_base), duration, 15,
                                     facecolor=color_map[note['articulation']],
                                     edgecolor='black', linewidth=0.5, alpha=0.7)
            ax4.add_patch(rect)
        ax4.text(-0.5, y_base + 7, inst_data['name'], fontsize=9, ha='right', va='center')
    
    ax4.set_xlim([0, 12])
    ax4.set_ylim([-5, 85])
    ax4.set_xlabel('Time (seconds)', fontsize=10)
    ax4.set_title('Note Timeline (First 12 seconds)', fontweight='bold', fontsize=11)
    ax4.grid(True, alpha=0.3, axis='x')
    ax4.set_yticks([])
    
    # 5. Error scatter
    ax5 = fig.add_subplot(gs[2, :2])
    midi = load_midi_reference()
    note_indices = []
    offset_errors = []
    colors_list = []
    
    idx = 0
    for inst_data in alignment['instruments']:
        midi_inst = midi.instruments[inst_data['index']]
        for note in inst_data['notes']:
            for midi_note in midi_inst.notes:
                if abs(midi_note.pitch - note['pitch']) < 1 and abs(midi_note.start - note['onset']) < 0.1:
                    error_ms = abs(note['offset'] - midi_note.end) * 1000
                    note_indices.append(idx)
                    offset_errors.append(error_ms)
                    colors_list.append(color_map[note['articulation']])
                    idx += 1
                    break
    
    ax5.scatter(note_indices, offset_errors, c=colors_list, s=30, alpha=0.6, edgecolors='black', linewidth=0.3)
    ax5.axhline(y=200, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax5.axhline(y=np.median(offset_errors), color='blue', linestyle='-', linewidth=1.5)
    ax5.set_xlabel('Note Index', fontsize=10)
    ax5.set_ylabel('Offset Error (ms)', fontsize=10)
    ax5.set_title('Per-Note Offset Errors', fontweight='bold', fontsize=11)
    ax5.grid(True, alpha=0.3)
    
    # 6. Statistics text
    ax6 = fig.add_subplot(gs[2, 2])
    ax6.axis('off')
    
    stats_text = f"""
SUMMARY STATISTICS
──────────────────
Total Notes: {evaluation['n_notes']}
Total Chords: {stats['n_chords']}

ARTICULATION:
  Staccato:  {stats['total_staccato']} ({stats['total_staccato']/evaluation['n_notes']*100:.1f}%)
  Legato:    {stats['total_legato']} ({stats['total_legato']/evaluation['n_notes']*100:.1f}%)
  Uncertain: {evaluation['n_notes']-stats['total_staccato']-stats['total_legato']} ({(evaluation['n_notes']-stats['total_staccato']-stats['total_legato'])/evaluation['n_notes']*100:.1f}%)

ALIGNMENT:
  MNE: {evaluation['MNE_ms']:.2f} ms
  MFE: {evaluation['MFE_ms']:.2f} ms
  
  Median Error: {np.median(offset_errors):.1f} ms
  
OFFSET RATES:
  ≤30ms:  {evaluation['offset_rates']['30']:.1f}%
  ≤200ms: {evaluation['offset_rates']['200']:.1f}%
    """
    
    ax6.text(0.1, 0.95, stats_text, transform=ax6.transAxes,
            fontsize=9, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    fig.suptitle('PQG-A2SA Results Summary - Bach10 01-AchGottundHerr', 
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.savefig('results/plot_00_summary.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: plot_00_summary.png (COMPREHENSIVE SUMMARY)")
    plt.close()

def main():
    """Generate all visualizations"""
    print("\n" + "="*70)
    print("  PQG-A2SA VISUALIZATION GENERATOR")
    print("="*70)
    print("\nLoading data...")
    
    alignment, evaluation = load_data()
    
    print(f"✓ Loaded alignment data: {alignment['statistics']['total_notes']} notes")
    print(f"✓ Loaded evaluation data: MNE={evaluation['MNE_ms']:.2f}ms, MFE={evaluation['MFE_ms']:.2f}ms")
    
    print("\nGenerating plots...")
    print("-" * 70)
    
    # Create summary first
    create_summary_figure(alignment, evaluation)
    
    # Individual plots
    plot_1_global_alignment_curve(alignment)
    plot_2_error_distribution(alignment, evaluation)
    plot_3_alignment_rates(evaluation)
    plot_4_articulation_distribution(alignment)
    plot_5_per_instrument_stats(alignment)
    plot_6_error_scatter(alignment)
    plot_7_error_boxplot(alignment)
    plot_8_timeline_visualization(alignment)
    plot_9_chord_onset_timeline(alignment)
    plot_10_duration_by_articulation(alignment)
    
    print("-" * 70)
    print("\n✅ ALL VISUALIZATIONS COMPLETE!")
    print(f"\n📊 Generated 11 plots in results/ directory:")
    print("   • plot_00_summary.png (Comprehensive overview)")
    print("   • plot_01_global_alignment.png")
    print("   • plot_02_error_distribution.png")
    print("   • plot_03_alignment_rates.png")
    print("   • plot_04_articulation_distribution.png")
    print("   • plot_05_per_instrument_stats.png")
    print("   • plot_06_error_scatter.png")
    print("   • plot_07_error_boxplot.png")
    print("   • plot_08_timeline_visualization.png")
    print("   • plot_09_chord_timeline.png")
    print("   • plot_10_duration_distribution.png")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
