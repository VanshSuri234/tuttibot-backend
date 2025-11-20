#!/usr/bin/env python3
"""
Before vs After Comparison Visualizations
==========================================
Shows the algorithm's improvements through each pipeline stage:
1. MIDI (Before) → VIDTW (After Stage 3)
2. VIDTW → IOI-GM (After Stage 4)  
3. IOI-GM → Articulation (After Stage 6)
4. Overall: MIDI → Final Alignment

This demonstrates the progressive refinement of the PQG-A2SA algorithm.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import seaborn as sns
import pretty_midi

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

def load_midi_timings(midi_path):
    """Extract original MIDI note timings (before algorithm)"""
    midi = pretty_midi.PrettyMIDI(midi_path)
    
    instruments = []
    for inst_idx, inst in enumerate(midi.instruments):
        notes = []
        for note in inst.notes:
            notes.append({
                'pitch': note.pitch,
                'onset': note.start,
                'offset': note.end,
                'velocity': note.velocity
            })
        instruments.append({
            'name': f'Instrument {inst_idx + 1}',
            'index': inst_idx,
            'notes': sorted(notes, key=lambda x: x['onset'])
        })
    
    return instruments

def load_alignment_results():
    """Load final alignment results"""
    with open('results/bach10_01_alignment.json', 'r') as f:
        return json.load(f)

def compute_onset_errors(midi_notes, aligned_notes):
    """Compare onset times between MIDI and aligned"""
    errors = []
    
    for midi_note in midi_notes:
        # Find matching aligned note
        for aligned_note in aligned_notes:
            if (abs(midi_note['pitch'] - aligned_note['pitch']) < 1 and
                abs(midi_note['onset'] - aligned_note['onset']) < 1.0):
                error_ms = abs(aligned_note['onset'] - midi_note['onset']) * 1000
                errors.append(error_ms)
                break
    
    return np.array(errors)

def compute_offset_errors(midi_notes, aligned_notes):
    """Compare offset times between MIDI and aligned"""
    errors = []
    
    for midi_note in midi_notes:
        # Find matching aligned note
        for aligned_note in aligned_notes:
            if (abs(midi_note['pitch'] - aligned_note['pitch']) < 1 and
                abs(midi_note['onset'] - aligned_note['onset']) < 1.0):
                error_ms = abs(aligned_note['offset'] - midi_note['offset']) * 1000
                errors.append(error_ms)
                break
    
    return np.array(errors)

def plot_1_onset_comparison(midi_insts, aligned_results):
    """Plot 1: MIDI Onsets vs Final Aligned Onsets"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()
    
    for idx in range(4):
        ax = axes[idx]
        
        midi_notes = midi_insts[idx]['notes']
        aligned_notes = aligned_results['instruments'][idx]['notes']
        
        # Extract onsets
        midi_onsets = [n['onset'] for n in midi_notes]
        aligned_onsets = [n['onset'] for n in aligned_notes]
        pitches = [n['pitch'] for n in midi_notes]
        
        # Plot
        ax.scatter(midi_onsets, pitches, c='red', marker='x', s=100, 
                  label='MIDI (Before)', alpha=0.7, linewidths=2)
        ax.scatter(aligned_onsets, pitches, c='blue', marker='o', s=50,
                  label='Aligned (After)', alpha=0.6, edgecolors='black', linewidths=0.5)
        
        # Connect with lines
        for midi_onset, aligned_onset, pitch in zip(midi_onsets, aligned_onsets, pitches):
            if abs(aligned_onset - midi_onset) > 0.001:  # Only show if different
                ax.plot([midi_onset, aligned_onset], [pitch, pitch], 
                       'gray', alpha=0.3, linewidth=1)
        
        ax.set_xlabel('Time (seconds)', fontsize=11)
        ax.set_ylabel('MIDI Pitch', fontsize=11)
        ax.set_title(f"Instrument {idx+1}: Onset Alignment", fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/before_after_01_onsets.png', dpi=150)
    print("✓ Saved: before_after_01_onsets.png")
    plt.close()

def plot_2_offset_comparison(midi_insts, aligned_results):
    """Plot 2: MIDI Offsets vs Final Aligned Offsets"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()
    
    for idx in range(4):
        ax = axes[idx]
        
        midi_notes = midi_insts[idx]['notes']
        aligned_notes = aligned_results['instruments'][idx]['notes']
        
        # Extract offsets
        midi_offsets = [n['offset'] for n in midi_notes]
        aligned_offsets = [n['offset'] for n in aligned_notes]
        pitches = [n['pitch'] for n in midi_notes]
        
        # Plot
        ax.scatter(midi_offsets, pitches, c='red', marker='x', s=100,
                  label='MIDI (Before)', alpha=0.7, linewidths=2)
        ax.scatter(aligned_offsets, pitches, c='green', marker='s', s=50,
                  label='Aligned (After)', alpha=0.6, edgecolors='black', linewidths=0.5)
        
        # Connect with lines
        for midi_off, aligned_off, pitch in zip(midi_offsets, aligned_offsets, pitches):
            if abs(aligned_off - midi_off) > 0.001:
                ax.plot([midi_off, aligned_off], [pitch, pitch],
                       'gray', alpha=0.3, linewidth=1)
        
        ax.set_xlabel('Time (seconds)', fontsize=11)
        ax.set_ylabel('MIDI Pitch', fontsize=11)
        ax.set_title(f"Instrument {idx+1}: Offset Refinement", fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/before_after_02_offsets.png', dpi=150)
    print("✓ Saved: before_after_02_offsets.png")
    plt.close()

def plot_3_duration_changes(midi_insts, aligned_results):
    """Plot 3: Note Duration Changes (MIDI vs Aligned)"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()
    
    for idx in range(4):
        ax = axes[idx]
        
        midi_notes = midi_insts[idx]['notes']
        aligned_notes = aligned_results['instruments'][idx]['notes']
        
        midi_durations = []
        aligned_durations = []
        colors = []
        
        color_map = {'staccato': '#ff6b6b', 'legato': '#4ecdc4', 'uncertain': '#ffe66d'}
        
        for midi_note in midi_notes:
            for aligned_note in aligned_notes:
                if (abs(midi_note['pitch'] - aligned_note['pitch']) < 1 and
                    abs(midi_note['onset'] - aligned_note['onset']) < 1.0):
                    midi_dur = (midi_note['offset'] - midi_note['onset']) * 1000
                    aligned_dur = (aligned_note['offset'] - aligned_note['onset']) * 1000
                    
                    midi_durations.append(midi_dur)
                    aligned_durations.append(aligned_dur)
                    colors.append(color_map.get(aligned_note.get('articulation', 'uncertain')))
                    break
        
        # Scatter plot: x=before, y=after
        ax.scatter(midi_durations, aligned_durations, c=colors, s=60,
                  alpha=0.7, edgecolors='black', linewidths=0.5)
        
        # Diagonal line (no change)
        max_dur = max(max(midi_durations), max(aligned_durations))
        ax.plot([0, max_dur], [0, max_dur], 'k--', alpha=0.5, linewidth=2,
               label='No change')
        
        ax.set_xlabel('MIDI Duration (ms)', fontsize=11)
        ax.set_ylabel('Aligned Duration (ms)', fontsize=11)
        ax.set_title(f"Instrument {idx+1}: Duration Changes", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # Add legend for articulation
        staccato_patch = mpatches.Patch(color='#ff6b6b', label='Staccato')
        legato_patch = mpatches.Patch(color='#4ecdc4', label='Legato')
        uncertain_patch = mpatches.Patch(color='#ffe66d', label='Uncertain')
        ax.legend(handles=[staccato_patch, legato_patch, uncertain_patch], fontsize=8)
    
    plt.tight_layout()
    plt.savefig('results/before_after_03_durations.png', dpi=150)
    print("✓ Saved: before_after_03_durations.png")
    plt.close()

def plot_4_error_reduction_bars(midi_insts, aligned_results):
    """Plot 4: Error Reduction Statistics (Bar Chart)"""
    
    onset_errors_before = []  # Always 0 (comparing MIDI to itself)
    offset_errors_before = []  # Always 0
    onset_errors_after = []
    offset_errors_after = []
    
    # For "before", we compare MIDI to MIDI (0 error)
    # For "after", we compare aligned to MIDI
    
    for idx in range(4):
        midi_notes = midi_insts[idx]['notes']
        aligned_notes = aligned_results['instruments'][idx]['notes']
        
        # Onset errors (should be ~0 since we don't refine onsets yet)
        onset_errs = compute_onset_errors(midi_notes, aligned_notes)
        onset_errors_after.extend(onset_errs)
        onset_errors_before.extend([0] * len(onset_errs))
        
        # Offset errors
        offset_errs = compute_offset_errors(midi_notes, aligned_notes)
        offset_errors_after.extend(offset_errs)
        offset_errors_before.extend([0] * len(offset_errs))
    
    onset_errors_before = np.array(onset_errors_before)
    onset_errors_after = np.array(onset_errors_after)
    offset_errors_before = np.array(offset_errors_before)
    offset_errors_after = np.array(offset_errors_after)
    
    # Create bar chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Onset errors
    ax1.bar(['MIDI\n(Before)', 'Aligned\n(After)'],
           [np.mean(onset_errors_before), np.mean(onset_errors_after)],
           color=['lightcoral', 'skyblue'], edgecolor='black', linewidth=2)
    ax1.set_ylabel('Mean Onset Error (ms)', fontsize=12)
    ax1.set_title('Onset Error: Before vs After', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    for i, val in enumerate([np.mean(onset_errors_before), np.mean(onset_errors_after)]):
        ax1.text(i, val + 0.5, f'{val:.2f}', ha='center', fontsize=11, fontweight='bold')
    
    # Offset errors
    ax2.bar(['MIDI\n(Before)', 'Aligned\n(After)'],
           [np.mean(offset_errors_before), np.mean(offset_errors_after)],
           color=['lightcoral', 'lightgreen'], edgecolor='black', linewidth=2)
    ax2.set_ylabel('Mean Offset Error (ms)', fontsize=12)
    ax2.set_title('Offset Error: Before vs After', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    for i, val in enumerate([np.mean(offset_errors_before), np.mean(offset_errors_after)]):
        ax2.text(i, val + 5, f'{val:.2f}', ha='center', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('results/before_after_04_error_bars.png', dpi=150)
    print("✓ Saved: before_after_04_error_bars.png")
    plt.close()

def plot_5_timeline_comparison(midi_insts, aligned_results):
    """Plot 5: Side-by-side Timeline (Before vs After)"""
    
    fig, axes = plt.subplots(4, 2, figsize=(16, 12), sharey='row', sharex=True)
    
    time_limit = 10.0
    color_map = {'staccato': '#ff6b6b', 'legato': '#4ecdc4', 'uncertain': '#ffe66d'}
    
    for inst_idx in range(4):
        # Left: MIDI (Before)
        ax_before = axes[inst_idx, 0]
        midi_notes = midi_insts[inst_idx]['notes']
        
        for note in midi_notes:
            if note['onset'] > time_limit:
                break
            onset = note['onset']
            offset = min(note['offset'], time_limit)
            duration = offset - onset
            pitch = note['pitch']
            
            rect = mpatches.Rectangle((onset, pitch - 0.4), duration, 0.8,
                                     facecolor='lightgray', edgecolor='black',
                                     linewidth=1, alpha=0.7)
            ax_before.add_patch(rect)
        
        ax_before.set_ylabel(f"Inst {inst_idx+1}", fontsize=11, fontweight='bold')
        ax_before.set_ylim([40, 80])
        ax_before.grid(True, alpha=0.3, axis='x')
        if inst_idx == 0:
            ax_before.set_title('MIDI (Before Algorithm)', fontsize=13, fontweight='bold')
        
        # Right: Aligned (After)
        ax_after = axes[inst_idx, 1]
        aligned_notes = aligned_results['instruments'][inst_idx]['notes']
        
        for note in aligned_notes:
            if note['onset'] > time_limit:
                break
            onset = note['onset']
            offset = min(note['offset'], time_limit)
            duration = offset - onset
            pitch = note['pitch']
            artic = note.get('articulation', 'uncertain')
            
            rect = mpatches.Rectangle((onset, pitch - 0.4), duration, 0.8,
                                     facecolor=color_map[artic], edgecolor='black',
                                     linewidth=1, alpha=0.7)
            ax_after.add_patch(rect)
        
        ax_after.set_ylim([40, 80])
        ax_after.grid(True, alpha=0.3, axis='x')
        if inst_idx == 0:
            ax_after.set_title('Aligned (After Algorithm)', fontsize=13, fontweight='bold')
    
    axes[-1, 0].set_xlabel('Time (seconds)', fontsize=12)
    axes[-1, 1].set_xlabel('Time (seconds)', fontsize=12)
    
    # Add legend
    staccato_patch = mpatches.Patch(color='#ff6b6b', label='Staccato')
    legato_patch = mpatches.Patch(color='#4ecdc4', label='Legato')
    uncertain_patch = mpatches.Patch(color='#ffe66d', label='Uncertain')
    fig.legend(handles=[staccato_patch, legato_patch, uncertain_patch],
              loc='upper right', fontsize=10, bbox_to_anchor=(0.99, 0.99))
    
    fig.suptitle('Timeline Comparison: MIDI vs Aligned (First 10 seconds)',
                fontsize=15, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    plt.savefig('results/before_after_05_timeline.png', dpi=150)
    print("✓ Saved: before_after_05_timeline.png")
    plt.close()

def plot_6_offset_delta_histogram(midi_insts, aligned_results):
    """Plot 6: Distribution of Offset Changes"""
    
    all_deltas = []
    staccato_deltas = []
    legato_deltas = []
    uncertain_deltas = []
    
    for idx in range(4):
        midi_notes = midi_insts[idx]['notes']
        aligned_notes = aligned_results['instruments'][idx]['notes']
        
        for midi_note in midi_notes:
            for aligned_note in aligned_notes:
                if (abs(midi_note['pitch'] - aligned_note['pitch']) < 1 and
                    abs(midi_note['onset'] - aligned_note['onset']) < 1.0):
                    
                    delta_ms = (aligned_note['offset'] - midi_note['offset']) * 1000
                    all_deltas.append(delta_ms)
                    
                    artic = aligned_note.get('articulation', 'uncertain')
                    if artic == 'staccato':
                        staccato_deltas.append(delta_ms)
                    elif artic == 'legato':
                        legato_deltas.append(delta_ms)
                    else:
                        uncertain_deltas.append(delta_ms)
                    break
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Overall distribution
    axes[0, 0].hist(all_deltas, bins=40, color='steelblue', edgecolor='black', alpha=0.7)
    axes[0, 0].axvline(0, color='red', linestyle='--', linewidth=2, label='No change')
    axes[0, 0].axvline(np.mean(all_deltas), color='green', linestyle='--', linewidth=2,
                      label=f'Mean: {np.mean(all_deltas):.1f}ms')
    axes[0, 0].set_xlabel('Offset Change (ms)', fontsize=11)
    axes[0, 0].set_ylabel('Frequency', fontsize=11)
    axes[0, 0].set_title('Overall Offset Changes', fontsize=12, fontweight='bold')
    axes[0, 0].legend(fontsize=10)
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # By articulation type
    axes[0, 1].hist([staccato_deltas, legato_deltas, uncertain_deltas],
                   bins=30, color=['#ff6b6b', '#4ecdc4', '#ffe66d'],
                   label=['Staccato', 'Legato', 'Uncertain'],
                   edgecolor='black', alpha=0.7)
    axes[0, 1].axvline(0, color='black', linestyle='--', linewidth=2)
    axes[0, 1].set_xlabel('Offset Change (ms)', fontsize=11)
    axes[0, 1].set_ylabel('Frequency', fontsize=11)
    axes[0, 1].set_title('Offset Changes by Articulation', fontsize=12, fontweight='bold')
    axes[0, 1].legend(fontsize=10)
    axes[0, 1].grid(axis='y', alpha=0.3)
    
    # Box plot comparison
    bp = axes[1, 0].boxplot([staccato_deltas, legato_deltas, uncertain_deltas],
                            labels=['Staccato', 'Legato', 'Uncertain'],
                            patch_artist=True, notch=True, showmeans=True)
    
    for patch, color in zip(bp['boxes'], ['#ff6b6b', '#4ecdc4', '#ffe66d']):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    axes[1, 0].axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    axes[1, 0].set_ylabel('Offset Change (ms)', fontsize=11)
    axes[1, 0].set_title('Statistical Comparison', fontsize=12, fontweight='bold')
    axes[1, 0].grid(axis='y', alpha=0.3)
    
    # Statistics table
    axes[1, 1].axis('off')
    stats_text = f"""
OFFSET CHANGE STATISTICS

Overall:
  Mean:   {np.mean(all_deltas):7.2f} ms
  Median: {np.median(all_deltas):7.2f} ms
  Std:    {np.std(all_deltas):7.2f} ms
  Range:  {np.min(all_deltas):7.2f} to {np.max(all_deltas):7.2f} ms

Staccato ({len(staccato_deltas)} notes):
  Mean:   {np.mean(staccato_deltas):7.2f} ms
  Median: {np.median(staccato_deltas):7.2f} ms

Legato ({len(legato_deltas)} notes):
  Mean:   {np.mean(legato_deltas):7.2f} ms
  Median: {np.median(legato_deltas):7.2f} ms

Uncertain ({len(uncertain_deltas)} notes):
  Mean:   {np.mean(uncertain_deltas):7.2f} ms
  Median: {np.median(uncertain_deltas):7.2f} ms

Interpretation:
• Negative values: Offset moved earlier
• Positive values: Offset moved later
• Zero: No change from MIDI
    """
    
    axes[1, 1].text(0.1, 0.95, stats_text, transform=axes[1, 1].transAxes,
                   fontsize=10, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    fig.suptitle('Offset Refinement Analysis: How Much Did Each Note Change?',
                fontsize=14, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    plt.savefig('results/before_after_06_offset_deltas.png', dpi=150)
    print("✓ Saved: before_after_06_offset_deltas.png")
    plt.close()

def create_summary_comparison(midi_insts, aligned_results):
    """Create comprehensive before/after summary"""
    
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Compute statistics
    all_offset_deltas = []
    for idx in range(4):
        midi_notes = midi_insts[idx]['notes']
        aligned_notes = aligned_results['instruments'][idx]['notes']
        
        for midi_note in midi_notes:
            for aligned_note in aligned_notes:
                if (abs(midi_note['pitch'] - aligned_note['pitch']) < 1 and
                    abs(midi_note['onset'] - aligned_note['onset']) < 1.0):
                    delta_ms = (aligned_note['offset'] - midi_note['offset']) * 1000
                    all_offset_deltas.append(delta_ms)
                    break
    
    offset_errors = compute_offset_errors(midi_insts[0]['notes'], 
                                         aligned_results['instruments'][0]['notes'])
    for idx in range(1, 4):
        offset_errors = np.concatenate([offset_errors,
                                       compute_offset_errors(midi_insts[idx]['notes'],
                                                            aligned_results['instruments'][idx]['notes'])])
    
    # 1. Before/After comparison bar
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.bar(['Before\n(MIDI)', 'After\n(Aligned)'],
           [0, np.mean(offset_errors)],
           color=['lightcoral', 'lightgreen'], edgecolor='black', linewidth=2)
    ax1.set_ylabel('Mean Offset Error (ms)', fontsize=11)
    ax1.set_title('Offset Refinement Impact', fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.text(1, np.mean(offset_errors) + 5, f'{np.mean(offset_errors):.1f}ms',
            ha='center', fontsize=10, fontweight='bold')
    
    # 2. Offset delta distribution
    ax2 = fig.add_subplot(gs[0, 1:])
    ax2.hist(all_offset_deltas, bins=40, color='steelblue', edgecolor='black', alpha=0.7)
    ax2.axvline(0, color='red', linestyle='--', linewidth=2)
    ax2.axvline(np.mean(all_offset_deltas), color='green', linestyle='--', linewidth=2,
               label=f'Mean: {np.mean(all_offset_deltas):.1f}ms')
    ax2.set_xlabel('Offset Change (ms)', fontsize=11)
    ax2.set_ylabel('Frequency', fontsize=11)
    ax2.set_title('Distribution of Offset Changes', fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. Timeline comparison (condensed)
    ax3 = fig.add_subplot(gs[1, :])
    color_map = {'staccato': '#ff6b6b', 'legato': '#4ecdc4', 'uncertain': '#ffe66d'}
    
    for inst_idx in range(4):
        y_base = inst_idx * 20
        
        # MIDI (gray)
        midi_notes = midi_insts[inst_idx]['notes']
        for note in midi_notes[:10]:
            onset = note['onset']
            duration = note['offset'] - note['onset']
            rect = mpatches.Rectangle((onset, y_base), duration, 7,
                                     facecolor='lightgray', edgecolor='black',
                                     linewidth=0.5, alpha=0.5)
            ax3.add_patch(rect)
        
        # Aligned (colored)
        aligned_notes = aligned_results['instruments'][inst_idx]['notes']
        for note in aligned_notes[:10]:
            onset = note['onset']
            duration = note['offset'] - note['onset']
            artic = note.get('articulation', 'uncertain')
            rect = mpatches.Rectangle((onset, y_base + 8), duration, 7,
                                     facecolor=color_map[artic], edgecolor='black',
                                     linewidth=0.5, alpha=0.7)
            ax3.add_patch(rect)
        
        ax3.text(-0.5, y_base + 7, f'Inst {inst_idx+1}', fontsize=9, ha='right', va='center')
    
    ax3.set_xlim([0, 12])
    ax3.set_ylim([-2, 82])
    ax3.set_xlabel('Time (seconds)', fontsize=11)
    ax3.set_title('Timeline: Gray=MIDI, Colored=Aligned (First 10 notes per instrument)',
                 fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')
    ax3.set_yticks([])
    
    # 4. Articulation statistics
    ax4 = fig.add_subplot(gs[2, 0])
    stats = aligned_results['statistics']
    sizes = [stats['total_staccato'], stats['total_legato'],
            stats['total_notes'] - stats['total_staccato'] - stats['total_legato']]
    ax4.pie(sizes, labels=['Staccato', 'Legato', 'Uncertain'],
           colors=['#ff6b6b', '#4ecdc4', '#ffe66d'],
           autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
    ax4.set_title('Articulation Detection', fontweight='bold')
    
    # 5. Per-instrument changes
    ax5 = fig.add_subplot(gs[2, 1])
    inst_means = []
    for idx in range(4):
        errors = compute_offset_errors(midi_insts[idx]['notes'],
                                       aligned_results['instruments'][idx]['notes'])
        inst_means.append(np.mean(errors))
    
    ax5.bar(range(4), inst_means, color=['#ff6b6b', '#4ecdc4', '#ffe66d', '#95e1d3'],
           edgecolor='black', linewidth=1.5)
    ax5.set_xticks(range(4))
    ax5.set_xticklabels([f'Inst {i+1}' for i in range(4)])
    ax5.set_ylabel('Mean Offset Error (ms)', fontsize=10)
    ax5.set_title('Per-Instrument Performance', fontweight='bold')
    ax5.grid(axis='y', alpha=0.3)
    
    # 6. Statistics table
    ax6 = fig.add_subplot(gs[2, 2])
    ax6.axis('off')
    
    stats_text = f"""
ALGORITHM IMPACT

Total Notes: {stats['total_notes']}
Total Chords: {stats['n_chords']}

OFFSET CHANGES:
  Mean:   {np.mean(all_offset_deltas):.1f} ms
  Median: {np.median(all_offset_deltas):.1f} ms
  Std:    {np.std(all_offset_deltas):.1f} ms

FINAL ERROR:
  Mean:   {np.mean(offset_errors):.1f} ms
  Median: {np.median(offset_errors):.1f} ms

DETECTION:
  Staccato: {stats['total_staccato']}
  Legato:   {stats['total_legato']}
  Uncertain: {stats['total_notes']-stats['total_staccato']-stats['total_legato']}

KEY IMPROVEMENTS:
✓ Articulation detected
✓ Offsets refined
✓ Duration adjusted
    """
    
    ax6.text(0.1, 0.95, stats_text, transform=ax6.transAxes,
            fontsize=9, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    fig.suptitle('PQG-A2SA Algorithm Impact: MIDI → Aligned Comparison',
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.savefig('results/before_after_00_summary.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: before_after_00_summary.png (COMPREHENSIVE COMPARISON)")
    plt.close()

def main():
    """Generate all before/after comparison plots"""
    print("\n" + "="*70)
    print("  PQG-A2SA BEFORE/AFTER COMPARISON GENERATOR")
    print("="*70)
    print("\nLoading data...")
    
    # Load MIDI (before algorithm)
    midi_path = "../Bach_10_Dataset/01-AchGottundHerr.mid"
    midi_insts = load_midi_timings(midi_path)
    print(f"✓ Loaded MIDI: {sum(len(inst['notes']) for inst in midi_insts)} notes")
    
    # Load alignment results (after algorithm)
    aligned_results = load_alignment_results()
    print(f"✓ Loaded aligned results: {aligned_results['statistics']['total_notes']} notes")
    
    print("\nGenerating comparison plots...")
    print("-" * 70)
    
    # Create all comparison plots
    create_summary_comparison(midi_insts, aligned_results)
    plot_1_onset_comparison(midi_insts, aligned_results)
    plot_2_offset_comparison(midi_insts, aligned_results)
    plot_3_duration_changes(midi_insts, aligned_results)
    plot_4_error_reduction_bars(midi_insts, aligned_results)
    plot_5_timeline_comparison(midi_insts, aligned_results)
    plot_6_offset_delta_histogram(midi_insts, aligned_results)
    
    print("-" * 70)
    print("\n✅ ALL BEFORE/AFTER COMPARISONS COMPLETE!")
    print(f"\n📊 Generated 7 comparison plots in results/ directory:")
    print("   • before_after_00_summary.png (Comprehensive comparison)")
    print("   • before_after_01_onsets.png (Onset alignment)")
    print("   • before_after_02_offsets.png (Offset refinement)")
    print("   • before_after_03_durations.png (Duration changes)")
    print("   • before_after_04_error_bars.png (Error statistics)")
    print("   • before_after_05_timeline.png (Side-by-side timeline)")
    print("   • before_after_06_offset_deltas.png (Change distribution)")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
