#!/usr/bin/env python3
"""
Professional Alignment Evaluation using mir_eval + Custom Metrics
=================================================================

Combines TuttiBot custom evaluation with industry-standard mir_eval metrics.
Provides comprehensive alignment quality assessment using peer-reviewed algorithms.

Features:
- Standard mir_eval onset evaluation
- Custom TuttiBot metrics  
- MIREX-compliant evaluation protocols
- Professional visualization and reporting

Usage:
    python professional_evaluate_alignment.py alignment_results.json [--output results]

Author: TuttiBot Team (Enhanced with mir_eval)
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings

# Import mir_eval for professional evaluation
try:
    import mir_eval
    MIR_EVAL_AVAILABLE = True
    print("✅ mir_eval available - using professional evaluation metrics")
except ImportError:
    MIR_EVAL_AVAILABLE = False
    print("⚠️  mir_eval not available - using custom metrics only")

def load_tuttibotv02_alignment(alignment_path: str) -> Tuple[np.ndarray, Dict, np.ndarray, np.ndarray]:
    """Load alignment results and extract score/performance onsets"""
    try:
        with open(alignment_path, 'r') as f:
            data = json.load(f)
        
        # Extract alignment pairs - look for different possible structures
        alignment_pairs = []
        
        if 'alignment_pairs' in data:
            alignment_pairs = data['alignment_pairs']
        elif 'alignment' in data and 'pairs' in data['alignment']:
            alignment_pairs = data['alignment']['pairs']
        elif 'alignment' in data and 'alignment' in data['alignment'] and 'time_mapping' in data['alignment']['alignment']:
            # TuttiBot v02 format - older structure
            time_mapping = data['alignment']['alignment']['time_mapping']
            alignment_pairs = [{'score_time': item['score_time'], 'performance_time': item['perf_time']} 
                             for item in time_mapping]
        elif 'alignment_results' in data and 'alignment' in data['alignment_results'] and 'time_mapping' in data['alignment_results']['alignment']:
            # TuttiBot v02 format - newer structure
            time_mapping = data['alignment_results']['alignment']['time_mapping']
            alignment_pairs = [{'score_time': item['score_time'], 'performance_time': item['perf_time']} 
                             for item in time_mapping]
        elif 'results' in data and 'alignment_pairs' in data['results']:
            alignment_pairs = data['results']['alignment_pairs']
        
        if not alignment_pairs:
            print(f"⚠️  Warning: No meaningful alignment found in {alignment_path}")
            print(f"Available keys: {list(data.keys())}")
            if 'alignment' in data:
                print(f"Alignment keys: {list(data['alignment'].keys())}")
            return np.empty((0, 2)), {}, np.empty(0), np.empty(0)
        
        # Convert to arrays for processing
        alignment_data = np.array([[pair['score_time'], pair['performance_time']] 
                                 for pair in alignment_pairs])
        
        # Extract separate onset arrays
        score_onsets = alignment_data[:, 0]
        perf_onsets = alignment_data[:, 1]
        
        # Calculate metadata
        metadata = {
            'total_pairs': len(alignment_pairs),
            'score_duration': float(np.max(score_onsets) - np.min(score_onsets)) if len(score_onsets) > 0 else 0,
            'perf_duration': float(np.max(perf_onsets) - np.min(perf_onsets)) if len(perf_onsets) > 0 else 0,
            'file_path': alignment_path
        }
        
        return alignment_data, metadata, score_onsets, perf_onsets
        
    except Exception as e:
        print(f"❌ Error loading alignment file: {e}")
        return np.empty((0, 2)), {}, np.empty(0), np.empty(0)

def evaluate_with_mir_eval(score_onsets: np.ndarray, perf_onsets: np.ndarray) -> Dict:
    """Evaluate alignment using professional mir_eval metrics"""
    
    if not MIR_EVAL_AVAILABLE:
        return {'error': 'mir_eval not available'}
    
    if len(score_onsets) == 0 or len(perf_onsets) == 0:
        return {'error': 'No onsets to evaluate'}
    
    try:
        # Sort onsets to ensure they're in increasing order (required by mir_eval)
        score_onsets = np.sort(score_onsets)
        perf_onsets = np.sort(perf_onsets)
        
        # Use mir_eval onset evaluation with multiple tolerance windows
        tolerances = [0.05, 0.1, 0.25]  # 50ms, 100ms, 250ms
        mir_results = {}
        
        for tol in tolerances:
            # mir_eval.onset.evaluate returns an OrderedDict with keys: F-measure, Precision, Recall
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = mir_eval.onset.evaluate(score_onsets, perf_onsets, window=tol)
                
                # Extract values from OrderedDict
                precision = result.get('Precision', 0.0)
                recall = result.get('Recall', 0.0)
                f_measure = result.get('F-measure', 0.0)
                avg_error = None  # mir_eval onset evaluation doesn't return average error
            
            mir_results[f'tolerance_{int(tol*1000)}ms'] = {
                'precision': precision,
                'recall': recall,
                'f_measure': f_measure,
                'average_error': avg_error if avg_error is not None else 'N/A'
            }
        
        print(f"✅ mir_eval evaluation completed for {len(tolerances)} tolerance windows")
        return mir_results
        
    except Exception as e:
        print(f"⚠️  mir_eval evaluation failed: {e}")
        return {'error': str(e)}

def compute_custom_metrics(pairs: np.ndarray, tolerances: List[float] = [0.05, 0.1, 0.25]) -> Dict:
    """Compute custom TuttiBot alignment metrics"""
    
    if pairs.size == 0:
        return {'error': 'No alignment pairs found', 'num_pairs': 0}
    
    # Compute onset errors (performance - score) in milliseconds
    errors_sec = pairs[:, 1] - pairs[:, 0]  # perf_time - score_time
    errors_ms = errors_sec * 1000.0
    
    # Basic statistics
    mae_ms = np.mean(np.abs(errors_ms))
    median_ms = np.median(np.abs(errors_ms))
    std_ms = np.std(errors_ms)
    
    # Tolerance analysis
    tolerance_results = {}
    for tol in tolerances:
        tol_ms = tol * 1000
        within_tolerance = np.mean(np.abs(errors_ms) <= tol_ms) * 100
        tolerance_results[f'within_{int(tol_ms)}ms'] = within_tolerance
    
    # Additional metrics
    metrics = {
        'num_pairs': len(pairs),
        'mae_ms': mae_ms,
        'median_abs_error_ms': median_ms,
        'std_error_ms': std_ms,
        'mean_error_ms': np.mean(errors_ms),  # signed error (bias)
        'min_error_ms': np.min(errors_ms),
        'max_error_ms': np.max(errors_ms),
        'tolerance_analysis': tolerance_results
    }
    
    return metrics

def print_professional_report(custom_metrics: Dict, mir_metrics: Dict, alignment_data: Dict):
    """Print comprehensive professional evaluation report"""
    
    print("\n" + "="*80)
    print("🎼 PROFESSIONAL ALIGNMENT EVALUATION REPORT")
    print("="*80)
    
    if 'error' in custom_metrics:
        print(f"❌ {custom_metrics['error']}")
        return
    
    # TuttiBot Custom Metrics
    print(f"\n📊 TUTTIBO CUSTOM METRICS:")
    print(f"   • Number of aligned pairs: {custom_metrics['num_pairs']}")
    print(f"   • Mean Absolute Error (MAE): {custom_metrics['mae_ms']:.1f} ms")
    print(f"   • Median Absolute Error: {custom_metrics['median_abs_error_ms']:.1f} ms")
    print(f"   • Standard Deviation: {custom_metrics['std_error_ms']:.1f} ms")
    print(f"   • Mean Signed Error (bias): {custom_metrics['mean_error_ms']:.1f} ms")
    
    print(f"\n🎯 TUTTIBO TOLERANCE ANALYSIS:")
    for tolerance, percentage in custom_metrics['tolerance_analysis'].items():
        print(f"   • {tolerance}: {percentage:.1f}%")
    
    # mir_eval Professional Metrics
    if MIR_EVAL_AVAILABLE and 'error' not in mir_metrics:
        print(f"\n🏆 MIR_EVAL PROFESSIONAL METRICS:")
        for tolerance, results in mir_metrics.items():
            print(f"   • {tolerance}:")
            
            # Handle precision
            precision = results['precision']
            if isinstance(precision, (int, float)):
                print(f"     - Precision: {precision:.3f}")
            else:
                print(f"     - Precision: {precision}")
                
            # Handle recall
            recall = results['recall']
            if isinstance(recall, (int, float)):
                print(f"     - Recall: {recall:.3f}")
            else:
                print(f"     - Recall: {recall}")
                
            # Handle f_measure
            f_measure = results['f_measure']
            if isinstance(f_measure, (int, float)):
                print(f"     - F-measure: {f_measure:.3f}")
            else:
                print(f"     - F-measure: {f_measure}")
                
            # Handle average_error
            avg_error = results['average_error']
            if isinstance(avg_error, (int, float)):
                print(f"     - Average Error: {avg_error:.3f}s")
            else:
                print(f"     - Average Error: {avg_error}")
                
    elif MIR_EVAL_AVAILABLE:
        print(f"\n⚠️  MIR_EVAL METRICS: {mir_metrics.get('error', 'Unknown error')}")
    else:
        print(f"\n⚠️  MIR_EVAL METRICS: Not available (install with: pip install mir_eval)")
    
    # Quality assessment
    mae = custom_metrics['mae_ms']
    within_100ms = custom_metrics['tolerance_analysis'].get('within_100ms', 0)
    
    print(f"\n⭐ OVERALL QUALITY ASSESSMENT:")
    if mae < 50:
        quality = "Excellent"
        emoji = "🟢"
    elif mae < 100:
        quality = "Good"  
        emoji = "🟡"
    elif mae < 250:
        quality = "Fair"
        emoji = "🟠"
    else:
        quality = "Poor"
        emoji = "🔴"
    
    print(f"   {emoji} Overall Quality: {quality}")
    print(f"   📈 TuttiBot Recommendation: {'Suitable for most applications' if mae < 100 else 'May need improvement for precise timing'}")
    
    # Add mir_eval quality assessment
    if MIR_EVAL_AVAILABLE and 'error' not in mir_metrics and 'tolerance_100ms' in mir_metrics:
        f_measure_100ms = mir_metrics['tolerance_100ms']['f_measure']
        if isinstance(f_measure_100ms, (int, float)):
            print(f"   🏆 mir_eval F-measure (100ms): {f_measure_100ms:.3f}")
            if f_measure_100ms > 0.8:
                print("   📈 mir_eval Assessment: Excellent alignment quality")
            elif f_measure_100ms > 0.6:
                print("   📈 mir_eval Assessment: Good alignment quality")
            else:
                print("   📈 mir_eval Assessment: Fair alignment quality")
        else:
            print(f"   🏆 mir_eval F-measure (100ms): {f_measure_100ms}")
            print("   📈 mir_eval Assessment: Unable to assess (invalid f-measure)")
    
    # Algorithm details
    if alignment_data:
        alignment_info = alignment_data.get('alignment', {})
        confidence = alignment_info.get('confidence', 0)
        dtw_distance = alignment_info.get('dtw_distance', 'N/A')
        
        print(f"\n🔧 ALGORITHM DETAILS:")
        print(f"   • TuttiBot Alignment Confidence: {confidence:.3f}")
        print(f"   • DTW Distance: {dtw_distance}")
        
        if confidence < 0.1:
            print(f"   ⚠️  Low confidence - check input quality and preprocessing")

def create_professional_visualizations(pairs: np.ndarray, errors_ms: np.ndarray, 
                                     custom_metrics: Dict, mir_metrics: Dict, 
                                     output_prefix: str):
    """Create professional-grade visualizations"""
    
    if pairs.size == 0:
        print("⚠️  No data to visualize")
        return
    
    # Enhanced scatter plot with mir_eval info
    plt.figure(figsize=(12, 8))
    plt.scatter(pairs[:, 0], pairs[:, 1], alpha=0.7, s=30, c='blue', edgecolors='black', linewidth=0.5)
    
    # Add ideal diagonal line
    min_time = min(pairs[:, 0].min(), pairs[:, 1].min())
    max_time = max(pairs[:, 0].max(), pairs[:, 1].max())
    plt.plot([min_time, max_time], [min_time, max_time], 'r--', linewidth=2, label='Perfect alignment')
    
    plt.xlabel('Score Time (seconds)', fontsize=14)
    plt.ylabel('Performance Time (seconds)', fontsize=14)
    plt.title('Professional Score-Performance Temporal Alignment\n(TuttiBot + mir_eval)', fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add text box with key metrics
    mae = custom_metrics.get('mae_ms', 0)
    textstr = f'MAE: {mae:.1f}ms\\n'
    textstr += f'Pairs: {len(pairs)}\\n'
    if MIR_EVAL_AVAILABLE and 'error' not in mir_metrics and 'tolerance_100ms' in mir_metrics:
        f_measure = mir_metrics['tolerance_100ms']['f_measure']
        if isinstance(f_measure, (int, float)):
            textstr += f'mir_eval F-measure: {f_measure:.3f}'
        else:
            textstr += f'mir_eval F-measure: {f_measure}'
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_professional_scatter.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    # Professional error analysis
    plt.figure(figsize=(12, 6))
    plt.hist(errors_ms, bins=30, alpha=0.7, edgecolor='black', color='skyblue')
    plt.axvline(0, color='red', linestyle='--', linewidth=2, label='Perfect alignment')
    plt.axvline(np.median(errors_ms), color='orange', linestyle='-', linewidth=2, 
                label=f'Median: {np.median(errors_ms):.1f}ms')
    plt.xlabel('Onset Error (ms)', fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    plt.title('Professional Error Distribution Analysis\\n(TuttiBot + mir_eval)', fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add statistics text
    textstr = f'Mean: {np.mean(errors_ms):.1f}ms\\n'
    textstr += f'Std: {np.std(errors_ms):.1f}ms\\n'
    textstr += f'Range: [{np.min(errors_ms):.1f}, {np.max(errors_ms):.1f}]ms'
    
    props = dict(boxstyle='round', facecolor='lightgreen', alpha=0.8)
    plt.text(0.98, 0.98, textstr, transform=plt.gca().transAxes, fontsize=11,
            verticalalignment='top', horizontalalignment='right', bbox=props)
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_professional_histogram.png', dpi=200, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Professional visualizations saved:")
    print(f"   • {output_prefix}_professional_scatter.png")
    print(f"   • {output_prefix}_professional_histogram.png")

def save_professional_results(custom_metrics: Dict, mir_metrics: Dict, metadata: Dict, output_file: str):
    """Save professional evaluation results to JSON file"""
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'evaluation_version': '1.0.0',
        'custom_metrics': custom_metrics,
        'mir_eval_metrics': mir_metrics,
        'metadata': metadata
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Professional evaluation results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Professional TuttiBot alignment evaluation with mir_eval')
    parser.add_argument('alignment_file', help='Path to alignment_results.json')
    parser.add_argument('--output', default='professional_eval', help='Output prefix')
    parser.add_argument('--tolerances', nargs='+', type=float, default=[0.05, 0.1, 0.25], 
                        help='Tolerance thresholds in seconds')
    
    args = parser.parse_args()
    
    # Load alignment data
    pairs, alignment_data, score_onsets, perf_onsets = load_tuttibotv02_alignment(args.alignment_file)
    
    # Compute custom metrics
    custom_metrics = compute_custom_metrics(pairs, args.tolerances)
    
    # Compute mir_eval metrics
    mir_metrics = evaluate_with_mir_eval(score_onsets, perf_onsets)
    
    # Print comprehensive report
    print_professional_report(custom_metrics, mir_metrics, alignment_data)
    
    # Create professional visualizations
    if pairs.size > 0:
        errors_ms = (pairs[:, 1] - pairs[:, 0]) * 1000
        create_professional_visualizations(pairs, errors_ms, custom_metrics, mir_metrics, args.output)
    
    # Save detailed results
    output_file = f"{args.output}_professional_results.json"
    results = {
        'tuttibo_custom_metrics': custom_metrics,
        'mir_eval_professional_metrics': mir_metrics,
        'original_alignment_data': alignment_data,
        'evaluation_params': {
            'tolerances_sec': args.tolerances,
            'input_file': args.alignment_file,
            'mir_eval_available': MIR_EVAL_AVAILABLE
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Professional evaluation results saved to: {output_file}")
    print("="*80)

if __name__ == '__main__':
    main()
