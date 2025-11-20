#!/usr/bin/env python3
"""
Pitch Evaluation Pipeline - Complete workflow

Evaluates pitch accuracy between musical score and audio performance.
Generates grades, metrics, and visualizations.

Usage:
    python evaluate_pitch.py --score score.xml --audio performance.wav --output results/
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from score_pitch_extractor import ScorePitchExtractor
from audio_pitch_extractor import AudioPitchExtractor
from pitch_comparator import PitchComparator
from pitch_grader import PitchGrader
from pitch_visualizer import PitchVisualizer


def create_output_structure(base_output_dir: str) -> Path:
    """Create output directory structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(base_output_dir) / f"pitch_evaluation_{timestamp}"
    
    # Create subdirectories
    (output_dir / "data").mkdir(parents=True, exist_ok=True)
    (output_dir / "visualizations").mkdir(parents=True, exist_ok=True)
    (output_dir / "reports").mkdir(parents=True, exist_ok=True)
    
    return output_dir


def evaluate_pitch(score_path: str,
                  audio_path: str,
                  output_dir: str,
                  method: str = 'pyin',
                  reference_freq: float = 440.0,
                  create_visualizations: bool = True) -> dict:
    """
    Complete pitch evaluation pipeline
    
    Args:
        score_path: Path to score file (MusicXML/MIDI)
        audio_path: Path to audio file (WAV/MP3)
        output_dir: Output directory for results
        method: Pitch extraction method ('pyin' or 'crepe')
        reference_freq: Reference frequency for A4 (Hz)
        create_visualizations: Whether to generate plots
        
    Returns:
        Dictionary with all results
    """
    
    output_dir = create_output_structure(output_dir)
    
    print("\n" + "=" * 70)
    print("PITCH EVALUATION PIPELINE")
    print("=" * 70)
    print(f"Score: {score_path}")
    print(f"Audio: {audio_path}")
    print(f"Output: {output_dir}")
    print(f"Method: {method.upper()}")
    print("=" * 70 + "\n")
    
    # ========================================================================
    # STEP 1: Extract Score Pitches
    # ========================================================================
    print("=" * 70)
    print("STEP 1: EXTRACTING SCORE PITCHES")
    print("=" * 70)
    
    score_extractor = ScorePitchExtractor(reference_frequency=reference_freq)
    score_extractor.load_score(score_path)
    score_notes = score_extractor.extract_notes()
    
    # Save score data
    score_json = output_dir / "data" / "score_pitches.json"
    score_extractor.save_to_json(str(score_json))
    
    # ========================================================================
    # STEP 2: Extract Audio Pitches
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 2: EXTRACTING AUDIO PITCHES")
    print("=" * 70)
    
    audio_extractor = AudioPitchExtractor(method=method)
    audio_extractor.load_audio(audio_path)
    
    # Optionally estimate tuning
    try:
        tuning_offset = audio_extractor.estimate_tuning()
        print(f"   Detected tuning: {tuning_offset:+.2f} semitones")
        
        # Adjust reference frequency if significant tuning difference
        if abs(tuning_offset) > 0.25:  # More than quarter tone
            print(f"   WARNING: Significant tuning deviation detected!")
            print(f"   Consider adjusting reference frequency or re-tuning instrument")
    except Exception as e:
        print(f"   WARNING: Could not estimate tuning: {e}")
    
    audio_frames = audio_extractor.extract_pitch()
    
    # Save audio data
    audio_json = output_dir / "data" / "audio_pitches.json"
    audio_extractor.save_to_json(str(audio_json))
    
    # ========================================================================
    # STEP 3: Compare Pitches
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 3: COMPARING PITCHES")
    print("=" * 70)
    
    comparator = PitchComparator(
        accuracy_threshold_cents=50.0,
        excellent_threshold_cents=25.0,
        good_threshold_cents=10.0
    )
    
    comparisons = comparator.compare_notes(score_extractor, audio_extractor)
    metrics = comparator.get_metrics()
    
    # Save comparison data
    comparison_json = output_dir / "data" / "comparison_results.json"
    comparator.save_to_json(str(comparison_json))
    
    comparison_csv = output_dir / "reports" / "note_by_note_comparison.csv"
    comparator.save_to_csv(str(comparison_csv))
    
    # Print metrics summary
    print("\nComparison Metrics:")
    print(f"   Total notes: {metrics['total_notes']}")
    print(f"   Measured notes: {metrics['measured_notes']}")
    print(f"   Mean absolute error: {metrics['mean_absolute_cents_error']:.1f} cents")
    
    # ========================================================================
    # STEP 4: Calculate Technical Metrics
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 4: CALCULATING TECHNICAL METRICS")
    print("=" * 70)
    
    grader = PitchGrader()
    evaluation = grader.evaluate_performance(metrics)
    
    # Save evaluation
    evaluation_json = output_dir / "reports" / "pitch_evaluation.json"
    grader.save_evaluation_report(evaluation, str(evaluation_json))
    
    # Print evaluation report
    grader.print_evaluation_report(evaluation)
    
    # ========================================================================
    # STEP 5: Create Visualizations
    # ========================================================================
    if create_visualizations:
        print("\n" + "=" * 70)
        print("STEP 5: CREATING VISUALIZATIONS")
        print("=" * 70)
        
        try:
            visualizer = PitchVisualizer()
            viz_dir = output_dir / "visualizations"
            
            visualizer.create_comprehensive_report(
                score_notes,
                audio_frames,
                comparisons,
                metrics,
                evaluation.to_dict(),
                str(viz_dir)
            )
            
            print(f"Visualizations saved to: {viz_dir}")
            
        except Exception as e:
            print(f"WARNING: Visualization failed: {e}")
            print("   Continuing without visualizations...")
    
    # ========================================================================
    # STEP 6: Create Summary Report
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 6: CREATING SUMMARY REPORT")
    print("=" * 70)
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'input_files': {
            'score': str(score_path),
            'audio': str(audio_path)
        },
        'configuration': {
            'method': method,
            'reference_frequency': reference_freq
        },
        'evaluation': evaluation.to_dict(),
        'metrics': metrics,
        'output_files': {
            'score_pitches': str(score_json),
            'audio_pitches': str(audio_json),
            'comparison_results': str(comparison_json),
            'comparison_csv': str(comparison_csv),
            'evaluation_report': str(evaluation_json),
            'visualizations': str(output_dir / "visualizations") if create_visualizations else None
        }
    }
    
    summary_json = output_dir / "evaluation_summary.json"
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create text summary
    summary_txt = output_dir / "EVALUATION_SUMMARY.txt"
    with open(summary_txt, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PITCH ACCURACY EVALUATION - TECHNICAL SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Timestamp:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Score File:   {Path(score_path).name}\n")
        f.write(f"Audio File:   {Path(audio_path).name}\n")
        f.write(f"Method:       {method.upper()}\n")
        f.write(f"Reference:    A4 = {reference_freq:.1f} Hz\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("METRIC CALCULATION PIPELINE\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("1. SCORE PITCH EXTRACTION\n")
        f.write("   - Parse MusicXML/MIDI using music21 library\n")
        f.write("   - Extract note pitch (MIDI number) and timing (onset, duration)\n")
        f.write("   - Convert MIDI pitch to frequency: f = 440 × 2^((midi-69)/12)\n")
        f.write(f"   - Total notes extracted: {metrics['total_notes']}\n\n")
        
        f.write("2. AUDIO PITCH EXTRACTION\n")
        f.write(f"   - Method: {method.upper()}\n")
        if method == 'pyin':
            f.write("   - Algorithm: Probabilistic YIN (pYIN)\n")
            f.write("   - Process: librosa.pyin() - frame-by-frame F0 estimation\n")
        else:
            f.write("   - Algorithm: CREPE (Convolutional REPresentation for Pitch Estimation)\n")
        f.write("   - Output: Time-series of fundamental frequency (F0) in Hz\n")
        f.write("   - Voicing detection: Confidence threshold to filter non-pitched frames\n\n")
        
        f.write("3. TEMPORAL ALIGNMENT & COMPARISON\n")
        f.write("   - Match score notes to audio frames based on onset times\n")
        f.write("   - For each note: extract median F0 from corresponding audio segment\n")
        f.write("   - Calculate cents deviation: Δ¢ = 1200 × log₂(f_audio / f_score)\n")
        f.write(f"   - Notes successfully measured: {metrics['measured_notes']}/{metrics['total_notes']} ({metrics['measurement_rate']*100:.1f}%)\n\n")
        
        f.write("4. STATISTICAL ANALYSIS\n")
        f.write("   - MACE (Mean Absolute Cents Error) = mean(|Δ¢|) for all notes\n")
        f.write("   - Mean Signed Error = mean(Δ¢) - detects systematic bias\n")
        f.write("   - Standard Deviation = std(Δ¢) - measures consistency\n")
        f.write("   - Percentiles and thresholds (±10¢, ±25¢, ±50¢)\n\n")
        
        f.write("5. ACCURACY SCORE COMPUTATION\n")
        f.write("   - Formula: Score = 100 × exp(-MACE / 25)\n")
        f.write("   - Exponential decay: MACE=0¢ → 100, MACE=25¢ → 36.8, MACE=50¢ → 13.5\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("EVALUATION RESULTS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"ACCURACY SCORE: {evaluation.accuracy_score:.2f}/100\n\n")
        
        f.write("STATISTICAL METRICS (Cents Deviation)\n")
        f.write("-" * 80 + "\n")
        f.write(f"Mean Absolute Error (MACE):   {evaluation.mean_absolute_cents_error:7.2f}¢\n")
        f.write(f"Mean Signed Error:            {evaluation.mean_cents_error:+7.2f}¢\n")
        f.write(f"Standard Deviation:           {evaluation.std_cents_error:7.2f}¢\n")
        f.write(f"Median Error:                 {evaluation.median_cents_error:+7.2f}¢\n\n")
        
        f.write("ERROR DISTRIBUTION\n")
        f.write("-" * 80 + "\n")
        breakdown = metrics['accuracy_breakdown']
        f.write(f"Perfect (<10¢):      {evaluation.perfect_percentage:6.2f}%  ({breakdown['perfect']['count']} notes)\n")
        f.write(f"Excellent (10-25¢):  {evaluation.excellent_percentage:6.2f}%  ({breakdown['excellent']['count']} notes)\n")
        f.write(f"Good (25-50¢):       {evaluation.good_percentage:6.2f}%  ({breakdown['good']['count']} notes)\n")
        f.write(f"Poor (≥50¢):         {evaluation.poor_percentage:6.2f}%  ({breakdown['poor']['count']} notes)\n\n")
        
        f.write("PRECISION THRESHOLDS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Within ±10¢: {evaluation.within_10_cents:6.2f}%\n")
        f.write(f"Within ±25¢: {evaluation.within_25_cents:6.2f}%\n")
        f.write(f"Within ±50¢: {evaluation.within_50_cents:6.2f}%\n\n")
        
        f.write("DETECTION METRICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Measurement Rate:    {evaluation.measurement_rate*100:.2f}%\n")
        f.write(f"Total Notes:         {evaluation.total_notes}\n")
        f.write(f"Measured Notes:      {evaluation.measured_notes}\n")
        f.write(f"Unmeasured Notes:    {evaluation.total_notes - evaluation.measured_notes}\n\n")
        
        f.write("SYSTEMATIC BIAS ANALYSIS\n")
        f.write("-" * 80 + "\n")
        if evaluation.systematic_bias_detected:
            f.write(f"Bias Detected:   YES\n")
            f.write(f"Direction:       {evaluation.bias_direction.upper()}\n")
            f.write(f"Magnitude:       {evaluation.bias_magnitude_cents:.2f}¢\n")
            sign = "+" if evaluation.bias_direction == "sharp" else "-"
            f.write(f"Interpretation:  Audio pitches are consistently {sign}{evaluation.bias_magnitude_cents:.2f}¢ relative to score\n")
        else:
            f.write(f"Bias Detected:   NO\n")
            f.write(f"Direction:       {evaluation.bias_direction}\n")
            f.write(f"Magnitude:       {evaluation.bias_magnitude_cents:.2f}¢\n")
            f.write(f"Interpretation:  No systematic sharp/flat tendency (|mean error| < 10¢)\n")
        f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("DETAILED DATA FILES\n")
        f.write("=" * 80 + "\n")
        f.write(f"JSON Summary:        {summary_json.name}\n")
        f.write(f"Per-Note CSV:        reports/{comparison_csv.name}\n")
        f.write(f"Score Pitches:       data/score_pitches.json\n")
        f.write(f"Audio Pitches:       data/audio_pitches.json\n")
        f.write(f"Comparison Data:     data/comparison_results.json\n")
        f.write(f"Evaluation Report:   reports/pitch_evaluation.json\n")
        if create_visualizations:
            f.write(f"Visualizations:      visualizations/\n")
        f.write("=" * 80 + "\n")
    
    print(f"Summary saved to: {summary_txt}")
    
    # ========================================================================
    # Final Summary
    # ========================================================================
    print("\n" + "=" * 70)
    print("PITCH EVALUATION COMPLETE!")
    print("=" * 70)
    print(f"All results saved to: {output_dir}")
    print(f"Accuracy Score: {evaluation.accuracy_score:.2f}/100")
    print(f"MACE: {metrics['mean_absolute_cents_error']:.2f} cents")
    print(f"Read {summary_txt.name} for complete technical report")
    print("=" * 70 + "\n")
    
    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate pitch accuracy between score and audio performance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic evaluation with pYIN (fast, CPU-friendly)
  python evaluate_pitch.py --score sheet.xml --audio performance.wav --output results/

  # Use CREPE for potentially better accuracy (slower on CPU)
  python evaluate_pitch.py --score sheet.xml --audio performance.wav --method crepe

  # Custom reference frequency (e.g., Baroque pitch)
  python evaluate_pitch.py --score sheet.xml --audio performance.wav --reference-freq 415.0

  # Skip visualizations for faster processing
  python evaluate_pitch.py --score sheet.xml --audio performance.wav --no-viz
        """
    )
    
    parser.add_argument('--score', required=True,
                       help='Path to score file (MusicXML .xml/.mxl or MIDI .mid)')
    parser.add_argument('--audio', required=True,
                       help='Path to audio file (WAV, MP3, etc.)')
    parser.add_argument('--output', default='./pitch_evaluation_output',
                       help='Output directory (default: ./pitch_evaluation_output)')
    
    parser.add_argument('--method', choices=['pyin', 'crepe'], default='pyin',
                       help='Pitch extraction method (default: pyin - faster for CPU)')
    parser.add_argument('--reference-freq', type=float, default=440.0,
                       help='Reference frequency for A4 in Hz (default: 440.0)')
    
    parser.add_argument('--no-viz', action='store_true',
                       help='Skip visualization generation (faster)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.score).exists():
        print(f"ERROR: Score file not found: {args.score}")
        sys.exit(1)
    
    if not Path(args.audio).exists():
        print(f"ERROR: Audio file not found: {args.audio}")
        sys.exit(1)
    
    # Run evaluation
    try:
        summary = evaluate_pitch(
            score_path=args.score,
            audio_path=args.audio,
            output_dir=args.output,
            method=args.method,
            reference_freq=args.reference_freq,
            create_visualizations=not args.no_viz
        )
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\nEvaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
