#!/usr/bin/env python3
"""
Pitch Comparator - Compare score pitches with audio pitches

Computes pitch deviation in cents and various accuracy metrics.
1 cent = 1/100 of a semitone
100 cents = 1 semitone
1200 cents = 1 octave
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

from score_pitch_extractor import ScoreNote, ScorePitchExtractor
from audio_pitch_extractor import AudioPitchExtractor


@dataclass
class NoteComparison:
    """Comparison result for a single note"""
    note_index: int
    score_note: ScoreNote
    
    # Audio measurements
    audio_frequency_median: Optional[float]
    audio_frequency_mean: Optional[float]
    audio_frequency_std: Optional[float]
    audio_confidence: float
    audio_voiced_ratio: float
    
    # Deviation metrics
    cents_error: Optional[float]  # Positive = sharp, negative = flat
    frequency_ratio: Optional[float]
    
    # Quality flags
    is_measured: bool
    is_accurate: bool  # Within threshold
    
    def to_dict(self):
        """Convert to dictionary with JSON-serializable values"""
        result = asdict(self)
        # Convert ScoreNote to dict
        result['score_note'] = self.score_note.to_dict()
        # Ensure all numeric values are JSON serializable
        result['audio_frequency_median'] = float(result['audio_frequency_median']) if result['audio_frequency_median'] is not None else None
        result['audio_frequency_mean'] = float(result['audio_frequency_mean']) if result['audio_frequency_mean'] is not None else None
        result['audio_frequency_std'] = float(result['audio_frequency_std']) if result['audio_frequency_std'] is not None else None
        result['audio_confidence'] = float(result['audio_confidence'])
        result['audio_voiced_ratio'] = float(result['audio_voiced_ratio'])
        result['cents_error'] = float(result['cents_error']) if result['cents_error'] is not None else None
        result['frequency_ratio'] = float(result['frequency_ratio']) if result['frequency_ratio'] is not None else None
        result['is_measured'] = bool(result['is_measured'])
        result['is_accurate'] = bool(result['is_accurate'])
        return result


class PitchComparator:
    """Compare pitches between score and audio performance"""
    
    def __init__(self, 
                 accuracy_threshold_cents: float = 50.0,
                 excellent_threshold_cents: float = 25.0,
                 good_threshold_cents: float = 10.0,
                 verbose: bool = True):
        """
        Initialize pitch comparator
        
        Args:
            accuracy_threshold_cents: Maximum deviation to consider "accurate"
            excellent_threshold_cents: Threshold for "excellent" accuracy
            good_threshold_cents: Threshold for "good" accuracy
            verbose: Whether to print progress messages (default: True)
        """
        self.accuracy_threshold = accuracy_threshold_cents
        self.excellent_threshold = excellent_threshold_cents
        self.good_threshold = good_threshold_cents
        self.verbose = verbose
        
        self.comparisons: List[NoteComparison] = []
    
    @staticmethod
    def cents_error(f_measured: float, f_reference: float) -> float:
        """
        Calculate pitch deviation in cents
        
        Args:
            f_measured: Measured frequency (Hz)
            f_reference: Reference frequency from score (Hz)
            
        Returns:
            Deviation in cents (positive = sharp, negative = flat)
        """
        if f_measured <= 0 or f_reference <= 0:
            return float('nan')
        
        return 1200.0 * np.log2(f_measured / f_reference)
    
    @staticmethod
    def frequency_ratio(f_measured: float, f_reference: float) -> float:
        """Calculate frequency ratio"""
        if f_reference <= 0:
            return float('nan')
        return f_measured / f_reference
    
    def compare_notes(self,
                     score_extractor: ScorePitchExtractor,
                     audio_extractor: AudioPitchExtractor,
                     min_voiced_ratio: float = 0.3) -> List[NoteComparison]:
        """
        Compare all notes between score and audio
        
        Args:
            score_extractor: ScorePitchExtractor with loaded score
            audio_extractor: AudioPitchExtractor with extracted pitch
            min_voiced_ratio: Minimum ratio of voiced frames to consider note measured
            
        Returns:
            List of NoteComparison objects
        """
        if not score_extractor.notes:
            raise ValueError("No notes in score. Extract notes first.")
        
        if not audio_extractor.pitch_frames:
            raise ValueError("No pitch extracted from audio. Extract pitch first.")
        
        if self.verbose:
            print(f"\nComparing {len(score_extractor.notes)} notes...")
        
        self.comparisons = []
        measured_count = 0
        
        for note in score_extractor.notes:
            # Get audio pitch in the note's time range
            audio_stats = audio_extractor.get_pitch_in_range(
                note.onset_time,
                note.offset_time
            )
            
            # Check if we have sufficient voiced frames
            is_measured = (
                audio_stats['median_frequency'] is not None and
                audio_stats['voiced_ratio'] >= min_voiced_ratio
            )
            
            if is_measured:
                measured_count += 1
                
                # Calculate deviation
                cents = self.cents_error(
                    audio_stats['median_frequency'],
                    note.frequency_hz
                )
                
                freq_ratio = self.frequency_ratio(
                    audio_stats['median_frequency'],
                    note.frequency_hz
                )
                
                # Check if accurate
                is_accurate = abs(cents) <= self.accuracy_threshold
                
            else:
                cents = None
                freq_ratio = None
                is_accurate = False
            
            # Create comparison result
            comparison = NoteComparison(
                note_index=note.note_index,
                score_note=note,
                audio_frequency_median=audio_stats['median_frequency'],
                audio_frequency_mean=audio_stats['mean_frequency'],
                audio_frequency_std=audio_stats['std_frequency'],
                audio_confidence=audio_stats['confidence_mean'],
                audio_voiced_ratio=audio_stats['voiced_ratio'],
                cents_error=cents,
                frequency_ratio=freq_ratio,
                is_measured=is_measured,
                is_accurate=is_accurate
            )
            
            self.comparisons.append(comparison)
        
        if self.verbose:
            print(f"Comparison complete: {measured_count}/{len(score_extractor.notes)} notes measured")
        
        return self.comparisons
    
    def get_metrics(self) -> Dict:
        """
        Calculate comprehensive pitch accuracy metrics
        
        Returns:
            Dictionary with various metrics
        """
        if not self.comparisons:
            return {}
        
        # Filter measured notes
        measured = [c for c in self.comparisons if c.is_measured]
        
        if not measured:
            return {
                'total_notes': len(self.comparisons),
                'measured_notes': 0,
                'measurement_rate': 0.0,
                'error': 'No notes could be measured from audio'
            }
        
        # Get cents errors
        cents_errors = [c.cents_error for c in measured if c.cents_error is not None]
        cents_errors_abs = [abs(c) for c in cents_errors]
        
        # Categorize notes by accuracy
        perfect = [c for c in measured if c.cents_error is not None and abs(c.cents_error) < self.good_threshold]
        excellent = [c for c in measured if c.cents_error is not None and self.good_threshold <= abs(c.cents_error) < self.excellent_threshold]
        good = [c for c in measured if c.cents_error is not None and self.excellent_threshold <= abs(c.cents_error) < self.accuracy_threshold]
        poor = [c for c in measured if c.cents_error is not None and abs(c.cents_error) >= self.accuracy_threshold]
        
        # Calculate percentages
        total_measured = len(measured)
        
        metrics = {
            'total_notes': len(self.comparisons),
            'measured_notes': total_measured,
            'measurement_rate': total_measured / len(self.comparisons),
            
            # Main accuracy metrics
            'mean_absolute_cents_error': float(np.mean(cents_errors_abs)) if cents_errors_abs else None,
            'mean_cents_error': float(np.mean(cents_errors)) if cents_errors else None,  # Shows if consistently sharp/flat
            'std_cents_error': float(np.std(cents_errors)) if cents_errors else None,
            'median_absolute_cents_error': float(np.median(cents_errors_abs)) if cents_errors_abs else None,
            
            # Range
            'max_sharp_cents': float(np.max([c for c in cents_errors if c > 0])) if any(c > 0 for c in cents_errors) else 0,
            'max_flat_cents': float(np.min([c for c in cents_errors if c < 0])) if any(c < 0 for c in cents_errors) else 0,
            
            # Accuracy categories
            'accuracy_breakdown': {
                'perfect': {
                    'count': len(perfect),
                    'percentage': len(perfect) / total_measured * 100,
                    'threshold': f'< {self.good_threshold} cents'
                },
                'excellent': {
                    'count': len(excellent),
                    'percentage': len(excellent) / total_measured * 100,
                    'threshold': f'{self.good_threshold}-{self.excellent_threshold} cents'
                },
                'good': {
                    'count': len(good),
                    'percentage': len(good) / total_measured * 100,
                    'threshold': f'{self.excellent_threshold}-{self.accuracy_threshold} cents'
                },
                'poor': {
                    'count': len(poor),
                    'percentage': len(poor) / total_measured * 100,
                    'threshold': f'≥ {self.accuracy_threshold} cents'
                }
            },
            
            # Pass rates at different thresholds
            'within_10_cents': len([c for c in cents_errors_abs if c < 10]) / total_measured * 100,
            'within_25_cents': len([c for c in cents_errors_abs if c < 25]) / total_measured * 100,
            'within_50_cents': len([c for c in cents_errors_abs if c < 50]) / total_measured * 100,
            
            # Audio quality metrics
            'average_confidence': float(np.mean([c.audio_confidence for c in measured])),
            'average_voiced_ratio': float(np.mean([c.audio_voiced_ratio for c in measured]))
        }
        
        return metrics
    
    def save_to_json(self, output_path: str) -> None:
        """
        Save comparison results to JSON
        
        Args:
            output_path: Path to output JSON file
        """
        output_data = {
            'metrics': self.get_metrics(),
            'thresholds': {
                'accuracy_threshold_cents': self.accuracy_threshold,
                'excellent_threshold_cents': self.excellent_threshold,
                'good_threshold_cents': self.good_threshold
            },
            'comparisons': [comp.to_dict() for comp in self.comparisons]
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        if self.verbose:
            print(f"Comparison results saved to: {output_path}")
    
    def save_to_csv(self, output_path: str) -> None:
        """
        Save comparison results to CSV for easy analysis
        
        Args:
            output_path: Path to output CSV file
        """
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Note_Index',
                'Onset_Time',
                'Duration',
                'Score_MIDI',
                'Score_Freq_Hz',
                'Score_Note_Name',
                'Audio_Freq_Hz',
                'Cents_Error',
                'Is_Measured',
                'Is_Accurate',
                'Voiced_Ratio',
                'Confidence'
            ])
            
            # Data rows
            for comp in self.comparisons:
                writer.writerow([
                    comp.note_index,
                    f"{comp.score_note.onset_time:.3f}",
                    f"{comp.score_note.duration:.3f}",
                    comp.score_note.midi_pitch,
                    f"{comp.score_note.frequency_hz:.2f}",
                    f"{comp.score_note.note_name}{comp.score_note.octave}",
                    f"{comp.audio_frequency_median:.2f}" if comp.audio_frequency_median else "N/A",
                    f"{comp.cents_error:.1f}" if comp.cents_error is not None else "N/A",
                    comp.is_measured,
                    comp.is_accurate,
                    f"{comp.audio_voiced_ratio:.2f}",
                    f"{comp.audio_confidence:.2f}"
                ])
        
        if self.verbose:
            print(f"CSV report saved to: {output_path}")


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare pitch between score and audio')
    parser.add_argument('--score', required=True, help='Path to score file')
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--output-json', help='Output JSON file')
    parser.add_argument('--output-csv', help='Output CSV file')
    parser.add_argument('--method', choices=['pyin', 'crepe'], default='pyin',
                       help='Pitch extraction method')
    
    args = parser.parse_args()
    
    # Extract score pitches
    print("=" * 60)
    print("EXTRACTING SCORE PITCHES")
    print("=" * 60)
    score_extractor = ScorePitchExtractor()
    score_extractor.load_score(args.score)
    score_extractor.extract_notes()
    
    # Extract audio pitches
    print("\n" + "=" * 60)
    print("EXTRACTING AUDIO PITCHES")
    print("=" * 60)
    audio_extractor = AudioPitchExtractor(method=args.method)
    audio_extractor.load_audio(args.audio)
    audio_extractor.extract_pitch()
    
    # Compare
    print("\n" + "=" * 60)
    print("COMPARING PITCHES")
    print("=" * 60)
    comparator = PitchComparator()
    comparator.compare_notes(score_extractor, audio_extractor)
    
    # Get and print metrics
    metrics = comparator.get_metrics()
    print("\nPITCH ACCURACY METRICS:")
    print(f"   Measured notes: {metrics['measured_notes']}/{metrics['total_notes']}")
    print(f"   Mean absolute error: {metrics['mean_absolute_cents_error']:.1f} cents")
    print(f"   Within ±10 cents: {metrics['within_10_cents']:.1f}%")
    print(f"   Within ±25 cents: {metrics['within_25_cents']:.1f}%")
    print(f"   Within ±50 cents: {metrics['within_50_cents']:.1f}%")
    
    # Save results
    if args.output_json:
        comparator.save_to_json(args.output_json)
    
    if args.output_csv:
        comparator.save_to_csv(args.output_csv)


if __name__ == '__main__':
    main()
