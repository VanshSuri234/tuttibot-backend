#!/usr/bin/env python3
"""
Run PQG-A2SA on Bach10 dataset example
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

# Import PQG-A2SA modules
from src import PQGAligner, PQGConfig

def main():
    """Run alignment on Bach10 01-AchGottundHerr"""
    
    print("=" * 80)
    print("PQG-A2SA: Bach10 Dataset Test")
    print("=" * 80)
    
    # Paths
    dataset_dir = Path("../Bach_10_Dataset")
    audio_path = dataset_dir / "01-AchGottundHerr.wav"
    midi_path = dataset_dir / "01-AchGottundHerr.mid"
    
    # Verify files exist
    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    if not midi_path.exists():
        print(f"❌ MIDI file not found: {midi_path}")
        return
    
    print(f"\n✓ Audio: {audio_path}")
    print(f"✓ MIDI:  {midi_path}")
    
    # Initialize aligner with default config
    print("\nInitializing PQG-A2SA aligner...")
    config = PQGConfig()
    aligner = PQGAligner(config)
    
    print("\nConfiguration:")
    print(f"  HOP_LENGTH: {config.HOP_LENGTH} (~{config.frames_to_ms(1):.1f}ms)")
    print(f"  K_CL: {config.K_CL} (clusters per chord)")
    print(f"  IOI_DELTA: {config.IOI_DELTA} (±chords)")
    print(f"  NMF_ITERATIONS: {config.NMF_ITERATIONS}")
    
    # Run alignment
    print("\n" + "=" * 80)
    print("Running alignment pipeline...")
    print("=" * 80)
    
    try:
        results = aligner.align(
            str(audio_path),
            str(midi_path),
            verbose=True
        )
        
        print("\n" + "=" * 80)
        print("ALIGNMENT RESULTS")
        print("=" * 80)
        
        # Summary statistics
        total_notes = 0
        total_staccato = 0
        total_legato = 0
        
        for inst in results['instruments']:
            n_notes = len(inst['notes'])
            total_notes += n_notes
            
            n_staccato = sum(1 for n in inst['notes'] if n.get('articulation') == 'staccato')
            n_legato = sum(1 for n in inst['notes'] if n.get('articulation') == 'legato')
            
            total_staccato += n_staccato
            total_legato += n_legato
            
            print(f"\n{inst['name']}:")
            print(f"  Total notes: {n_notes}")
            print(f"  Staccato: {n_staccato} ({100*n_staccato/n_notes:.1f}%)")
            print(f"  Legato: {n_legato} ({100*n_legato/n_notes:.1f}%)")
            
            # Show first 5 notes as sample
            print(f"  Sample notes (first 5):")
            for i, note in enumerate(inst['notes'][:5]):
                duration = note['offset'] - note['onset']
                print(f"    {i+1}. Pitch {note['pitch']:3d}: "
                      f"{note['onset']:7.3f}s → {note['offset']:7.3f}s "
                      f"({duration*1000:6.1f}ms, {note.get('articulation', 'N/A')})")
        
        print(f"\n{'=' * 80}")
        print(f"OVERALL STATISTICS")
        print(f"{'=' * 80}")
        print(f"Total notes: {total_notes}")
        print(f"Staccato: {total_staccato} ({100*total_staccato/total_notes:.1f}%)")
        print(f"Legato: {total_legato} ({100*total_legato/total_notes:.1f}%)")
        print(f"Chords: {len(results['chord_onsets_refined'])}")
        
        # Save results
        output_dir = Path("results")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "bach10_01_alignment.json"
        
        # Prepare JSON-serializable output
        output_data = {
            'metadata': {
                'audio_file': str(audio_path),
                'midi_file': str(midi_path),
                'config': {
                    'HOP_LENGTH': config.HOP_LENGTH,
                    'K_CL': config.K_CL,
                    'IOI_DELTA': config.IOI_DELTA,
                    'NMF_ITERATIONS': config.NMF_ITERATIONS
                }
            },
            'instruments': [],
            'chord_onsets': results['chord_onsets_refined'].tolist(),
            'statistics': {
                'total_notes': total_notes,
                'total_staccato': total_staccato,
                'total_legato': total_legato,
                'n_chords': len(results['chord_onsets_refined'])
            }
        }
        
        for inst in results['instruments']:
            inst_data = {
                'name': inst['name'],
                'index': inst['index'],
                'notes': inst['notes']
            }
            output_data['instruments'].append(inst_data)
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
        
        # Create a simple timing comparison file
        comparison_file = output_dir / "bach10_01_timing_comparison.txt"
        with open(comparison_file, 'w') as f:
            f.write("Bach10 01-AchGottundHerr - Note Timing Comparison\n")
            f.write("=" * 80 + "\n\n")
            
            for inst in results['instruments']:
                f.write(f"\n{inst['name']}:\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Note':<6} {'Pitch':<6} {'Onset (s)':<12} {'Offset (s)':<12} "
                       f"{'Duration (ms)':<15} {'Articulation':<15}\n")
                f.write("-" * 80 + "\n")
                
                for i, note in enumerate(inst['notes'], 1):
                    duration_ms = (note['offset'] - note['onset']) * 1000
                    f.write(f"{i:<6} {note['pitch']:<6} {note['onset']:<12.3f} "
                           f"{note['offset']:<12.3f} {duration_ms:<15.1f} "
                           f"{note.get('articulation', 'N/A'):<15}\n")
        
        print(f"✓ Timing comparison saved to: {comparison_file}")
        
        print("\n" + "=" * 80)
        print("✅ ALIGNMENT COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during alignment: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
