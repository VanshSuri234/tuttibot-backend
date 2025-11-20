#!/usr/bin/env python3
"""
Batch Comparison Script for Bach10 Dataset

Automatically runs DTW vs PQG-A2SA comparison on all Bach10 pieces.
Saves results with corresponding filenames.
"""

import os
import sys
import glob
from pathlib import Path
import subprocess
import time

def find_bach10_pairs(dataset_dir):
    """
    Find all matching WAV and MIDI file pairs in Bach10 dataset.
    
    Returns:
        List of tuples: (wav_path, mid_path, output_name)
    """
    dataset_path = Path(dataset_dir)
    
    # Find all WAV files
    wav_files = sorted(dataset_path.glob("*.wav"))
    
    pairs = []
    for wav_file in wav_files:
        # Extract base name (e.g., "01-AchGottundHerr")
        wav_stem = wav_file.stem
        
        # Handle special case like "02-AchLiebenChristen(1).wav"
        # Try to find matching MIDI
        possible_midi_stems = [
            wav_stem,  # Exact match
            wav_stem.split('(')[0],  # Remove (1) suffix
        ]
        
        midi_file = None
        for stem in possible_midi_stems:
            candidate = dataset_path / f"{stem}.mid"
            if candidate.exists():
                midi_file = candidate
                break
        
        if midi_file:
            # Create clean output name
            output_name = wav_stem.replace('(', '').replace(')', '').replace(' ', '_')
            pairs.append((str(wav_file), str(midi_file), output_name))
        else:
            print(f"⚠️  Warning: No MIDI file found for {wav_file.name}")
    
    return pairs


def run_comparison(wav_path, midi_path, output_name, verbose=True):
    """
    Run comparison for a single audio/MIDI pair.
    
    Args:
        wav_path: Path to WAV audio file
        midi_path: Path to MIDI score file
        output_name: Name prefix for output files
        verbose: Print progress messages
    
    Returns:
        success: Boolean indicating if comparison succeeded
        elapsed_time: Time taken in seconds
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"Processing: {output_name}")
        print(f"  Audio: {Path(wav_path).name}")
        print(f"  Score: {Path(midi_path).name}")
        print(f"{'='*70}\n")
    
    start_time = time.time()
    
    try:
        # Run compare_algorithms.py
        cmd = [
            sys.executable,  # Use same Python interpreter
            "compare_algorithms.py",
            wav_path,
            midi_path,
            output_name
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per piece
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            if verbose:
                print(f"✅ Success! ({elapsed_time:.1f}s)")
            return True, elapsed_time
        else:
            if verbose:
                print(f"❌ Failed with return code {result.returncode}")
                print(f"Error output:\n{result.stderr}")
            return False, elapsed_time
            
    except subprocess.TimeoutExpired:
        elapsed_time = time.time() - start_time
        if verbose:
            print(f"⏱️  Timeout after {elapsed_time:.1f}s")
        return False, elapsed_time
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        if verbose:
            print(f"❌ Exception: {e}")
        return False, elapsed_time


def main():
    """Main batch processing function"""
    
    print("\n" + "="*70)
    print("BATCH COMPARISON: Bach10 Dataset")
    print("Baseline DTW vs PQG-A2SA")
    print("="*70 + "\n")
    
    # Find Bach10 dataset
    bach10_dir = Path("../Bach_10_Dataset")
    if not bach10_dir.exists():
        print(f"❌ Error: Bach10 dataset not found at {bach10_dir}")
        sys.exit(1)
    
    # Find all pairs
    pairs = find_bach10_pairs(bach10_dir)
    
    if not pairs:
        print("❌ Error: No matching WAV/MIDI pairs found!")
        sys.exit(1)
    
    print(f"📁 Found {len(pairs)} audio/score pairs to process:\n")
    for i, (wav, mid, name) in enumerate(pairs, 1):
        print(f"  {i}. {name}")
        print(f"     Audio: {Path(wav).name}")
        print(f"     Score: {Path(mid).name}")
    
    print(f"\n{'='*70}\n")
    
    # Process each pair
    results = []
    total_start = time.time()
    
    for i, (wav_path, midi_path, output_name) in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}] Processing {output_name}...")
        
        success, elapsed = run_comparison(wav_path, midi_path, output_name)
        results.append({
            'name': output_name,
            'wav': Path(wav_path).name,
            'midi': Path(midi_path).name,
            'success': success,
            'time': elapsed
        })
    
    total_elapsed = time.time() - total_start
    
    # Print summary
    print("\n" + "="*70)
    print("BATCH PROCESSING COMPLETE")
    print("="*70 + "\n")
    
    print("📊 Summary:\n")
    print(f"{'Piece':<30} {'Status':<12} {'Time':<10}")
    print("-" * 70)
    
    successful = 0
    for r in results:
        status = "✅ Success" if r['success'] else "❌ Failed"
        print(f"{r['name']:<30} {status:<12} {r['time']:>6.1f}s")
        if r['success']:
            successful += 1
    
    print("-" * 70)
    print(f"\nTotal: {successful}/{len(results)} successful")
    print(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    
    print(f"\n📁 All results saved to: comparison_results/")
    print("   Each piece has 7 output files:")
    print("   - *_dtw_cost_matrix.png")
    print("   - *_error_histograms.png")
    print("   - *_error_lines.png")
    print("   - *_alignment_scatter.png")
    print("   - *_alignment_rates.png")
    print("   - *_summary.png")
    print("   - *_summary.txt")
    
    print("\n" + "="*70 + "\n")
    
    # Create index file
    create_index_file(results)
    
    return successful == len(results)


def create_index_file(results):
    """Create an index file listing all processed pieces"""
    
    index_path = Path("comparison_results") / "INDEX.txt"
    
    with open(index_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("BACH10 COMPARISON RESULTS INDEX\n")
        f.write("Baseline DTW vs PQG-A2SA\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Total Pieces Processed: {len(results)}\n")
        f.write(f"Successful: {sum(1 for r in results if r['success'])}\n")
        f.write(f"Failed: {sum(1 for r in results if not r['success'])}\n\n")
        
        f.write("="*70 + "\n")
        f.write("FILE LISTING\n")
        f.write("="*70 + "\n\n")
        
        for r in results:
            status = "✅" if r['success'] else "❌"
            f.write(f"{status} {r['name']}\n")
            f.write(f"   Audio: {r['wav']}\n")
            f.write(f"   Score: {r['midi']}\n")
            
            if r['success']:
                f.write(f"   Output files:\n")
                f.write(f"     - {r['name']}_dtw_cost_matrix.png\n")
                f.write(f"     - {r['name']}_error_histograms.png\n")
                f.write(f"     - {r['name']}_error_lines.png\n")
                f.write(f"     - {r['name']}_alignment_scatter.png\n")
                f.write(f"     - {r['name']}_alignment_rates.png\n")
                f.write(f"     - {r['name']}_summary.png\n")
                f.write(f"     - {r['name']}_summary.txt\n")
            
            f.write(f"   Processing time: {r['time']:.1f}s\n\n")
    
    print(f"📄 Index file created: {index_path}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
