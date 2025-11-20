#!/usr/bin/env python3
"""
Generate musician-friendly report from pitch evaluation results
"""

import json
import sys
from pathlib import Path


def generate_musician_report(evaluation_dir: str, output_file: str):
    """
    Generate a simple text report for musicians
    
    Args:
        evaluation_dir: Directory containing evaluation results
        output_file: Path to output text file
    """
    eval_path = Path(evaluation_dir)
    
    # Load evaluation data
    eval_json = eval_path / "reports" / "pitch_evaluation.json"
    summary_json = eval_path / "evaluation_summary.json"
    
    if not eval_json.exists() or not summary_json.exists():
        print(f"ERROR: Could not find evaluation files in {evaluation_dir}")
        sys.exit(1)
    
    with open(eval_json, 'r') as f:
        evaluation = json.load(f)
    
    with open(summary_json, 'r') as f:
        summary = json.load(f)
    
    # Extract key information
    score_file = Path(summary['input_files']['score']).name
    audio_file = Path(summary['input_files']['audio']).name
    
    # Create report
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PITCH ACCURACY ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Score File: {score_file}\n")
        f.write(f"Audio File: {audio_file}\n")
        f.write(f"Analysis Date: {summary['timestamp'][:10]}\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("WHAT WAS MEASURED\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("This analysis compares the pitches in the musical score with the pitches\n")
        f.write("actually played in the audio recording. The system:\n\n")
        f.write(f"1. Read {evaluation['total_notes']} notes from the score\n")
        f.write(f"2. Extracted pitch frequencies from the audio recording\n")
        f.write(f"3. Measured {evaluation['measured_notes']} notes ({evaluation['measurement_rate']*100:.1f}%)\n\n")
        
        if evaluation['measurement_rate'] < 0.5:
            f.write("NOTE: Less than half of the notes were measured. This usually means:\n")
            f.write("      - The audio is mostly silent or very quiet\n")
            f.write("      - The audio recording does not match this score\n")
            f.write("      - The recording quality is poor\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("PITCH ACCURACY RESULTS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Accuracy Score: {:.1f} out of 100\n\n".format(evaluation['accuracy_score']))
        
        f.write("Average Pitch Error: {:.1f} cents\n".format(evaluation['mean_absolute_cents_error']))
        f.write("(For reference: 100 cents = 1 semitone, 50 cents = quarter tone)\n\n")
        
        # Interpret the results
        mace = evaluation['mean_absolute_cents_error']
        if mace < 10:
            quality = "Excellent - Professional level accuracy"
        elif mace < 25:
            quality = "Very Good - Strong pitch control"
        elif mace < 50:
            quality = "Good - Generally accurate with some deviation"
        elif mace < 100:
            quality = "Fair - Noticeable pitch issues"
        elif mace < 500:
            quality = "Poor - Significant pitch problems"
        else:
            quality = "Very Poor - Major issues detected"
        
        f.write(f"Overall Assessment: {quality}\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("DETAILED BREAKDOWN\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("How many notes fell within different accuracy ranges:\n\n")
        f.write(f"  Perfect (within 10 cents):        {evaluation['perfect_percentage']:5.1f}%\n")
        f.write(f"  Very Good (within 10-25 cents):   {evaluation['excellent_percentage']:5.1f}%\n")
        f.write(f"  Acceptable (within 25-50 cents):  {evaluation['good_percentage']:5.1f}%\n")
        f.write(f"  Problematic (more than 50 cents): {evaluation['poor_percentage']:5.1f}%\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("PITCH TENDENCY\n")
        f.write("=" * 80 + "\n\n")
        
        if evaluation['systematic_bias_detected']:
            direction = "sharp (too high)" if evaluation['bias_direction'] == "sharp" else "flat (too low)"
            f.write(f"The recording tends to be {direction}.\n")
            f.write(f"Average deviation: {evaluation['bias_magnitude_cents']:.1f} cents {evaluation['bias_direction']}\n\n")
            
            if evaluation['bias_direction'] == "sharp":
                f.write("This means the played pitches are consistently higher than written.\n")
            else:
                f.write("This means the played pitches are consistently lower than written.\n")
        else:
            f.write("No consistent sharp or flat tendency detected.\n")
            f.write("The pitches are generally centered around the correct values.\n")
        
        f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("STATISTICS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Mean Pitch Error:       {evaluation['mean_cents_error']:+.1f} cents\n")
        f.write(f"Standard Deviation:     {evaluation['std_cents_error']:.1f} cents\n")
        f.write(f"Median Error:           {evaluation['median_cents_error']:+.1f} cents\n\n")
        
        f.write("Consistency: ")
        if evaluation['std_cents_error'] < 20:
            f.write("Very consistent pitch across notes\n")
        elif evaluation['std_cents_error'] < 40:
            f.write("Reasonably consistent\n")
        else:
            f.write("Variable pitch - some notes accurate, others less so\n")
        
        f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("NOTES FOR THE MUSICIAN\n")
        f.write("=" * 80 + "\n\n")
        
        # Give context-aware notes
        if evaluation['measurement_rate'] < 0.3:
            f.write("IMPORTANT: Only {:.0f}% of notes were measured from the audio.\n".format(
                evaluation['measurement_rate'] * 100))
            f.write("This typically means:\n")
            f.write("  - The audio file may not match this score\n")
            f.write("  - The recording is mostly silent\n")
            f.write("  - The audio quality is very poor\n\n")
            f.write("Please verify that the correct audio file was analyzed.\n\n")
        
        elif mace > 1000:
            f.write("The average pitch error is very high (over 10 semitones).\n")
            f.write("This suggests:\n")
            f.write("  - The audio may be the wrong recording for this score\n")
            f.write("  - There may be a transposition issue\n")
            f.write("  - The instrument may be severely out of tune\n\n")
        
        elif mace > 100:
            f.write("The pitch accuracy shows significant deviation (over 1 semitone average).\n")
            f.write("Consider:\n")
            f.write("  - Checking if the instrument is properly tuned\n")
            f.write("  - Verifying the score matches the recording\n")
            f.write("  - Reviewing sections with large pitch errors\n\n")
        
        elif mace < 50:
            f.write("The pitch accuracy is within acceptable range for most notes.\n")
            if evaluation['systematic_bias_detected']:
                f.write(f"There is a consistent {evaluation['bias_direction']} tendency that could be addressed.\n\n")
            else:
                f.write("No major systematic issues detected.\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("TECHNICAL REFERENCE\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Cents: A unit for measuring pitch intervals\n")
        f.write("  - 100 cents = 1 semitone (e.g., C to C#)\n")
        f.write("  - 50 cents = quarter tone\n")
        f.write("  - 10 cents = just noticeable to most listeners\n")
        f.write("  - 5 cents or less = imperceptible to most\n\n")
        
        f.write("Measurement Rate: Percentage of score notes where pitch was detected\n")
        f.write("  in the audio. Low rates suggest audio quality or matching issues.\n\n")
        
        f.write("Systematic Bias: Consistent tendency to play sharp or flat across\n")
        f.write("  all notes (detected when average error exceeds 10 cents).\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("DETAILED DATA\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("For note-by-note analysis, see:\n")
        f.write("  - note_by_note_comparison.csv (spreadsheet with all measurements)\n")
        f.write("  - comparison_results.json (complete technical data)\n\n")
        
        f.write("=" * 80 + "\n")
    
    print(f"Musician report generated: {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate musician-friendly report')
    parser.add_argument('evaluation_dir', help='Path to evaluation results directory')
    parser.add_argument('--output', default='MUSICIAN_REPORT.txt',
                       help='Output filename (default: MUSICIAN_REPORT.txt)')
    
    args = parser.parse_args()
    
    output_path = Path(args.evaluation_dir) / args.output
    generate_musician_report(args.evaluation_dir, str(output_path))


if __name__ == '__main__':
    main()
