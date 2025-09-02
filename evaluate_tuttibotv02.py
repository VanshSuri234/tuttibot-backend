#!/usr/bin/env python3
"""
TuttiBot v02 - Evaluation Suite
Standalone evaluation tool for temporal alignment results

This script provides comprehensive evaluation capabilities for TuttiBot v02 output:
- Custom TuttiBot metrics (MAE, tolerance analysis)
- Professional mir_eval metrics (precision, recall, f-measure)
- Quality assessment and recommendations
- Visualization generation
- Batch evaluation support

Usage:
    python3 evaluate_tuttibotv02.py path/to/tuttibotv02_results.json
    python3 evaluate_tuttibotv02.py --batch path/to/output/directory/
    python3 evaluate_tuttibotv02.py --help

Author: TuttiBot Team
Version: 1.0.0
"""

import os
import sys
import json
import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Try to import professional evaluation
try:
    from professional_evaluate_alignment import (
        load_tuttibotv02_alignment,
        compute_custom_metrics,
        evaluate_with_mir_eval,
        create_professional_visualizations,
        print_professional_report,
        save_professional_results
    )
    PROFESSIONAL_EVAL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Professional evaluation not available: {e}")
    PROFESSIONAL_EVAL_AVAILABLE = False

def find_tuttibotv02_results(directory: Path) -> List[Path]:
    """Find all TuttiBot v02 result files in a directory"""
    results = []
    
    # Look for tuttibotv02_results.json files
    for result_file in directory.rglob("tuttibotv02_results.json"):
        results.append(result_file)
    
    # Also look for final_output directories
    for final_output in directory.rglob("final_output"):
        if final_output.is_dir():
            result_file = final_output / "tuttibotv02_results.json"
            if result_file.exists() and result_file not in results:
                results.append(result_file)
    
    return sorted(results)

def evaluate_single_result(result_file: Path, output_prefix: Optional[str] = None) -> Dict:
    """Evaluate a single TuttiBot v02 result file"""
    
    if not PROFESSIONAL_EVAL_AVAILABLE:
        print("❌ Professional evaluation not available")
        return {'error': 'Professional evaluation not available'}
    
    print(f"\n🔍 Evaluating: {result_file}")
    print("=" * 60)
    
    # Load alignment data
    alignment_data, metadata, score_onsets, perf_onsets = load_tuttibotv02_alignment(str(result_file))
    
    if len(alignment_data) == 0:
        print(f"❌ No alignment data found in {result_file}")
        return {'error': 'No alignment data found'}
    
    # Calculate metrics
    custom_metrics = compute_custom_metrics(alignment_data)
    mir_metrics = evaluate_with_mir_eval(score_onsets, perf_onsets)
    
    # Set output prefix if not provided
    if output_prefix is None:
        output_prefix = result_file.parent / f"evaluation_{result_file.stem}"
    
    # Create visualizations
    errors_ms = (alignment_data[:, 1] - alignment_data[:, 0]) * 1000
    create_professional_visualizations(alignment_data, errors_ms, custom_metrics, mir_metrics, str(output_prefix))
    
    # Print report
    print_professional_report(custom_metrics, mir_metrics, metadata)
    
    # Save results
    save_professional_results(custom_metrics, mir_metrics, metadata, f"{output_prefix}_results.json")
    
    return {
        'file': str(result_file),
        'custom_metrics': custom_metrics,
        'mir_metrics': mir_metrics,
        'metadata': metadata
    }

def evaluate_batch(directory: Path, output_dir: Optional[Path] = None) -> Dict:
    """Evaluate all TuttiBot v02 results in a directory"""
    
    print(f"\n🔍 Batch evaluation in: {directory}")
    print("=" * 60)
    
    # Find all result files
    result_files = find_tuttibotv02_results(directory)
    
    if not result_files:
        print(f"❌ No TuttiBot v02 result files found in {directory}")
        return {'error': 'No result files found'}
    
    print(f"📊 Found {len(result_files)} result files to evaluate")
    
    # Set up output directory
    if output_dir is None:
        output_dir = directory / "batch_evaluation"
    output_dir.mkdir(exist_ok=True)
    
    # Evaluate each file
    results = []
    summary_stats = {
        'total_files': len(result_files),
        'successful_evaluations': 0,
        'failed_evaluations': 0,
        'aggregate_metrics': {
            'mae_values': [],
            'f_measure_values': [],
            'alignment_counts': []
        }
    }
    
    for i, result_file in enumerate(result_files, 1):
        try:
            print(f"\n[{i}/{len(result_files)}] Processing: {result_file.name}")
            
            # Create individual output prefix
            output_prefix = output_dir / f"eval_{i:03d}_{result_file.parent.name}"
            
            # Evaluate
            result = evaluate_single_result(result_file, str(output_prefix))
            
            if 'error' not in result:
                results.append(result)
                summary_stats['successful_evaluations'] += 1
                
                # Collect aggregate statistics
                mae = result['custom_metrics'].get('mae_ms', 0)
                summary_stats['aggregate_metrics']['mae_values'].append(mae)
                summary_stats['aggregate_metrics']['alignment_counts'].append(
                    result['custom_metrics'].get('total_pairs', 0)
                )
                
                if 'tolerance_100ms' in result['mir_metrics']:
                    f_measure = result['mir_metrics']['tolerance_100ms'].get('f_measure', 0)
                    if isinstance(f_measure, (int, float)):
                        summary_stats['aggregate_metrics']['f_measure_values'].append(f_measure)
            else:
                summary_stats['failed_evaluations'] += 1
                print(f"❌ Failed to evaluate {result_file.name}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            summary_stats['failed_evaluations'] += 1
            print(f"❌ Error evaluating {result_file.name}: {e}")
    
    # Calculate aggregate statistics
    if summary_stats['aggregate_metrics']['mae_values']:
        mae_values = summary_stats['aggregate_metrics']['mae_values']
        f_measure_values = summary_stats['aggregate_metrics']['f_measure_values']
        
        summary_stats['aggregate_metrics']['mae_stats'] = {
            'mean': float(np.mean(mae_values)),
            'median': float(np.median(mae_values)),
            'std': float(np.std(mae_values)),
            'min': float(np.min(mae_values)),
            'max': float(np.max(mae_values))
        }
        
        if f_measure_values:
            summary_stats['aggregate_metrics']['f_measure_stats'] = {
                'mean': float(np.mean(f_measure_values)),
                'median': float(np.median(f_measure_values)),
                'std': float(np.std(f_measure_values)),
                'min': float(np.min(f_measure_values)),
                'max': float(np.max(f_measure_values))
            }
    
    # Save batch summary
    batch_summary_file = output_dir / "batch_summary.json"
    with open(batch_summary_file, 'w') as f:
        json.dump({
            'summary_stats': summary_stats,
            'individual_results': results
        }, f, indent=2)
    
    # Print batch summary
    print_batch_summary(summary_stats, output_dir)
    
    return {
        'summary_stats': summary_stats,
        'individual_results': results,
        'output_directory': str(output_dir)
    }

def print_batch_summary(summary_stats: Dict, output_dir: Path):
    """Print a summary of batch evaluation results"""
    
    print("\n" + "=" * 70)
    print("📊 BATCH EVALUATION SUMMARY")
    print("=" * 70)
    
    print(f"📁 Output Directory: {output_dir}")
    print(f"📊 Total Files: {summary_stats['total_files']}")
    print(f"✅ Successful: {summary_stats['successful_evaluations']}")
    print(f"❌ Failed: {summary_stats['failed_evaluations']}")
    
    agg = summary_stats['aggregate_metrics']
    if 'mae_stats' in agg:
        mae_stats = agg['mae_stats']
        print(f"\n📈 AGGREGATE MAE STATISTICS:")
        print(f"   • Mean: {mae_stats['mean']:.2f} ms")
        print(f"   • Median: {mae_stats['median']:.2f} ms")
        print(f"   • Std Dev: {mae_stats['std']:.2f} ms")
        print(f"   • Range: {mae_stats['min']:.2f} - {mae_stats['max']:.2f} ms")
        
    if 'f_measure_stats' in agg:
        f_stats = agg['f_measure_stats']
        print(f"\n🎯 AGGREGATE F-MEASURE STATISTICS:")
        print(f"   • Mean: {f_stats['mean']:.3f}")
        print(f"   • Median: {f_stats['median']:.3f}")
        print(f"   • Std Dev: {f_stats['std']:.3f}")
        print(f"   • Range: {f_stats['min']:.3f} - {f_stats['max']:.3f}")
    
    print(f"\n💾 Detailed results saved to: {output_dir}/batch_summary.json")
    print("=" * 70)

def main():
    """Main evaluation entry point"""
    
    parser = argparse.ArgumentParser(
        description="TuttiBot v02 Evaluation Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate single result file
  python3 evaluate_tuttibotv02.py Output/run1/final_output/tuttibotv02_results.json
  
  # Batch evaluate all results in a directory
  python3 evaluate_tuttibotv02.py --batch Output/
  
  # Specify custom output directory for batch evaluation
  python3 evaluate_tuttibotv02.py --batch Output/ --output evaluations/
        """
    )
    
    parser.add_argument('input', 
                       help='Path to TuttiBot v02 result file or directory for batch evaluation')
    parser.add_argument('--batch', action='store_true',
                       help='Perform batch evaluation on all result files in input directory')
    parser.add_argument('--output', type=str,
                       help='Output directory for evaluation results (default: auto-generated)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress detailed output (show only summary)')
    
    args = parser.parse_args()
    
    # Check if professional evaluation is available
    if not PROFESSIONAL_EVAL_AVAILABLE:
        print("❌ Professional evaluation module not available.")
        print("Make sure professional_evaluate_alignment.py is in the same directory.")
        sys.exit(1)
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"❌ Input path does not exist: {input_path}")
        sys.exit(1)
    
    try:
        if args.batch:
            # Batch evaluation
            if not input_path.is_dir():
                print(f"❌ Batch mode requires a directory, got: {input_path}")
                sys.exit(1)
            
            output_dir = Path(args.output) if args.output else None
            result = evaluate_batch(input_path, output_dir)
            
            if 'error' in result:
                print(f"❌ Batch evaluation failed: {result['error']}")
                sys.exit(1)
                
        else:
            # Single file evaluation
            if input_path.is_dir():
                # If directory provided, look for tuttibotv02_results.json
                result_file = input_path / "tuttibotv02_results.json"
                if not result_file.exists():
                    # Try final_output subdirectory
                    result_file = input_path / "final_output" / "tuttibotv02_results.json"
                    if not result_file.exists():
                        print(f"❌ No tuttibotv02_results.json found in {input_path}")
                        sys.exit(1)
                input_path = result_file
            
            output_prefix = args.output if args.output else None
            result = evaluate_single_result(input_path, output_prefix)
            
            if 'error' in result:
                print(f"❌ Evaluation failed: {result['error']}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⚠️  Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n✅ Evaluation completed successfully!")

if __name__ == '__main__':
    main()
