#!/usr/bin/env python3
"""
Evaluate PQG-A2SA alignment results using MIDI as ground truth reference
Computes MNE (Mean Note Error) and MFE (Mean Frame/Offset Error)
"""

import sys
import json
import numpy as np
from pathlib import Path

from src import PQGAligner, Evaluator
from src.score_parser import ScoreParser


def load_ground_truth_from_midi(midi_path):
    """
    Load ground truth note timings from MIDI
    
    In Bach10, the MIDI is the score (not aligned to performance),
    so this serves as a reference baseline rather than true ground truth.
    """
    parser = ScoreParser()
    midi_obj = parser.load_midi(str(midi_path))
    instruments = parser.extract_instrument_notes(midi_obj)
    
    ground_truth = {}
    for inst in instruments:
        inst_idx = inst['index']
        ground_truth[inst_idx] = inst['notes']
    
    return ground_truth


def evaluate_alignment(results_json_path, midi_path):
    """
    Evaluate alignment results against MIDI reference
    """
    print("=" * 80)
    print("PQG-A2SA EVALUATION")
    print("=" * 80)
    
    # Load results
    with open(results_json_path, 'r') as f:
        results = json.load(f)
    
    print(f"\nResults file: {results_json_path}")
    print(f"MIDI reference: {midi_path}")
    
    # Load ground truth
    ground_truth = load_ground_truth_from_midi(midi_path)
    
    # Initialize evaluator
    evaluator = Evaluator()
    
    # Evaluate per instrument
    print("\n" + "=" * 80)
    print("PER-INSTRUMENT METRICS")
    print("=" * 80)
    
    all_onset_errors = []
    all_offset_errors = []
    
    for inst_data in results['instruments']:
        inst_idx = inst_data['index']
        inst_name = inst_data['name']
        
        if inst_idx not in ground_truth:
            print(f"\n⚠ {inst_name}: No ground truth found")
            continue
        
        predicted_notes = inst_data['notes']
        gt_notes = ground_truth[inst_idx]
        
        # Match notes (assume same order and count)
        if len(predicted_notes) != len(gt_notes):
            print(f"\n⚠ {inst_name}: Note count mismatch "
                  f"(predicted: {len(predicted_notes)}, GT: {len(gt_notes)})")
            # Truncate to shorter length
            min_len = min(len(predicted_notes), len(gt_notes))
            predicted_notes = predicted_notes[:min_len]
            gt_notes = gt_notes[:min_len]
        
        if len(predicted_notes) == 0:
            continue
        
        # Extract onset and offset times
        pred_onsets = np.array([n['onset'] for n in predicted_notes])
        pred_offsets = np.array([n['offset'] for n in predicted_notes])
        gt_onsets = np.array([n['onset'] for n in gt_notes])
        gt_offsets = np.array([n['offset'] for n in gt_notes])
        
        # Compute errors
        onset_errors = np.abs(pred_onsets - gt_onsets)
        offset_errors = np.abs(pred_offsets - gt_offsets)
        
        all_onset_errors.extend(onset_errors)
        all_offset_errors.extend(offset_errors)
        
        # Per-instrument statistics
        MNE_inst = np.mean(onset_errors)
        MFE_inst = np.mean(offset_errors)
        
        print(f"\n{inst_name} ({len(predicted_notes)} notes):")
        print(f"  MNE (Mean Note Error):   {MNE_inst*1000:7.2f} ms")
        print(f"  MFE (Mean Frame Error):  {MFE_inst*1000:7.2f} ms")
        print(f"  Onset error range:       {onset_errors.min()*1000:7.2f} - {onset_errors.max()*1000:7.2f} ms")
        print(f"  Offset error range:      {offset_errors.min()*1000:7.2f} - {offset_errors.max()*1000:7.2f} ms")
        
        # Alignment rates for this instrument
        onset_rates = evaluator.compute_alignment_rates(onset_errors)
        offset_rates = evaluator.compute_alignment_rates(offset_errors)
        
        print(f"  Onset alignment rates:")
        for threshold in [30, 60, 90, 120, 150, 200]:
            if threshold in onset_rates:
                print(f"    ≤{threshold:3d} ms: {onset_rates[threshold]:6.2f}%")
        
        print(f"  Offset alignment rates:")
        for threshold in [30, 60, 90, 120, 150, 200]:
            if threshold in offset_rates:
                print(f"    ≤{threshold:3d} ms: {offset_rates[threshold]:6.2f}%")
    
    # Overall statistics
    print("\n" + "=" * 80)
    print("OVERALL METRICS (All Instruments Combined)")
    print("=" * 80)
    
    all_onset_errors = np.array(all_onset_errors)
    all_offset_errors = np.array(all_offset_errors)
    
    overall_MNE = np.mean(all_onset_errors)
    overall_MFE = np.mean(all_offset_errors)
    overall_NE = np.sum(all_onset_errors)  # Total Note Error
    overall_FE = np.sum(all_offset_errors)  # Total Frame Error
    
    print(f"\nTotal notes evaluated: {len(all_onset_errors)}")
    print(f"\nNote Errors (Onset):")
    print(f"  NE  (Total Note Error):  {overall_NE:.3f} s = {overall_NE*1000:.1f} ms")
    print(f"  MNE (Mean Note Error):   {overall_MNE*1000:.2f} ms")
    print(f"  Std deviation:           {np.std(all_onset_errors)*1000:.2f} ms")
    print(f"  Min error:               {all_onset_errors.min()*1000:.2f} ms")
    print(f"  Max error:               {all_onset_errors.max()*1000:.2f} ms")
    print(f"  Median error:            {np.median(all_onset_errors)*1000:.2f} ms")
    
    print(f"\nFrame Errors (Offset):")
    print(f"  FE  (Total Frame Error): {overall_FE:.3f} s = {overall_FE*1000:.1f} ms")
    print(f"  MFE (Mean Frame Error):  {overall_MFE*1000:.2f} ms")
    print(f"  Std deviation:           {np.std(all_offset_errors)*1000:.2f} ms")
    print(f"  Min error:               {all_offset_errors.min()*1000:.2f} ms")
    print(f"  Max error:               {all_offset_errors.max()*1000:.2f} ms")
    print(f"  Median error:            {np.median(all_offset_errors)*1000:.2f} ms")
    
    # Overall alignment rates
    onset_rates = evaluator.compute_alignment_rates(all_onset_errors)
    offset_rates = evaluator.compute_alignment_rates(all_offset_errors)
    
    print(f"\nOnset Alignment Rates:")
    for threshold in [30, 60, 90, 120, 150, 200]:
        if threshold in onset_rates:
            print(f"  ≤{threshold:3d} ms: {onset_rates[threshold]:6.2f}%")
    
    print(f"\nOffset Alignment Rates:")
    for threshold in [30, 60, 90, 120, 150, 200]:
        if threshold in offset_rates:
            print(f"  ≤{threshold:3d} ms: {offset_rates[threshold]:6.2f}%")
    
    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print("""
NOTE: The MIDI file represents the musical score, not the actual performance.
Therefore, these metrics show how much the refined alignment differs from
the score timing (which includes tempo variations, articulation, etc.).

Expected results:
- MNE typically increases after alignment (score is rigid, performance varies)
- MFE should improve with articulation modeling
- Low errors suggest the performance closely follows the score
- High errors suggest significant tempo/expression variations

For true evaluation, we would need manually annotated ground truth timings
from the actual performance (not available in Bach10 standard dataset).
    """)
    
    return {
        'MNE': overall_MNE,
        'MFE': overall_MFE,
        'NE': overall_NE,
        'FE': overall_FE,
        'n_notes': len(all_onset_errors),
        'onset_errors': all_onset_errors,
        'offset_errors': all_offset_errors,
        'onset_rates': onset_rates,
        'offset_rates': offset_rates
    }


def main():
    results_json = Path("results/bach10_01_alignment.json")
    midi_path = Path("../Bach_10_Dataset/01-AchGottundHerr.mid")
    
    if not results_json.exists():
        print(f"❌ Results file not found: {results_json}")
        print("Run: python3 run_bach10.py first")
        return 1
    
    if not midi_path.exists():
        print(f"❌ MIDI file not found: {midi_path}")
        return 1
    
    metrics = evaluate_alignment(results_json, midi_path)
    
    # Save evaluation results
    eval_output = Path("results/bach10_01_evaluation.json")
    with open(eval_output, 'w') as f:
        # Convert numpy arrays to lists for JSON
        output_data = {
            'MNE_ms': metrics['MNE'] * 1000,
            'MFE_ms': metrics['MFE'] * 1000,
            'NE_s': metrics['NE'],
            'FE_s': metrics['FE'],
            'n_notes': metrics['n_notes'],
            'onset_rates': metrics['onset_rates'],
            'offset_rates': metrics['offset_rates']
        }
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Evaluation metrics saved to: {eval_output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
