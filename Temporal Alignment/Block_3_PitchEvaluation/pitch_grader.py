#!/usr/bin/env python3
"""
Pitch Grader - Generate grades based on pitch accuracy metrics

Converts pitch deviation metrics into letter grades and quality scores.
"""

import json
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class PitchGrade:
    """Pitch accuracy evaluation result - Technical metrics only"""
    
    # Primary accuracy score (0-100, computed from MACE)
    accuracy_score: float  # Exponential decay: 100 * exp(-MACE/25)
    
    # Core statistical metrics
    mean_absolute_cents_error: float  # MACE - primary metric
    mean_cents_error: float  # Signed error (positive=sharp, negative=flat)
    std_cents_error: float  # Standard deviation of cents error
    median_cents_error: float  # Median cents error
    
    # Error distribution (percentages)
    perfect_percentage: float  # <10¢ deviation
    excellent_percentage: float  # 10-25¢ deviation
    good_percentage: float  # 25-50¢ deviation
    poor_percentage: float  # ≥50¢ deviation
    
    # Precision thresholds (percentage within tolerance)
    within_10_cents: float  # % notes with |error| < 10¢
    within_25_cents: float  # % notes with |error| < 25¢
    within_50_cents: float  # % notes with |error| < 50¢
    
    # Detection metrics
    measurement_rate: float  # Proportion of notes successfully measured
    total_notes: int  # Total notes in score
    measured_notes: int  # Notes with pitch extracted from audio
    
    # Systematic bias detection
    systematic_bias_detected: bool  # True if |mean_error| > 10¢
    bias_direction: str  # "sharp", "flat", or "neutral"
    bias_magnitude_cents: float  # Absolute value of mean error
    
    def to_dict(self):
        return asdict(self)


class PitchGrader:
    """Calculate technical pitch accuracy metrics from comparison data"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize pitch grader
        
        Args:
            verbose: Whether to print progress messages (default: True)
        """
        self.verbose = verbose
    
    def calculate_accuracy_score(self, mace: float) -> float:
        """
        Calculate accuracy score (0-100) from Mean Absolute Cents Error
        
        Formula: score = 100 * exp(-MACE / 25)
        
        This exponential decay provides:
        - MACE = 0¢  → score = 100.0
        - MACE = 25¢ → score = 36.8
        - MACE = 50¢ → score = 13.5
        
        Args:
            mace: Mean absolute cents error
            
        Returns:
            Numeric score from 0-100
        """
        if mace < 0:
            return 100.0
        
        score = 100.0 * np.exp(-mace / 25.0)
        return float(max(0.0, min(100.0, score)))
    
    def detect_systematic_bias(self, mean_error: float) -> tuple:
        """
        Detect if there's systematic sharp/flat bias
        
        Args:
            mean_error: Mean signed cents error
            
        Returns:
            Tuple of (bias_detected, direction, magnitude)
        """
        threshold = 10.0  # cents
        magnitude = abs(mean_error)
        
        if magnitude > threshold:
            direction = "sharp" if mean_error > 0 else "flat"
            return (True, direction, magnitude)
        else:
            return (False, "neutral", magnitude)
    
    def evaluate_performance(self, metrics: Dict) -> PitchGrade:
        """
        Calculate technical pitch accuracy metrics
        
        Args:
            metrics: Dictionary of metrics from PitchComparator
            
        Returns:
            PitchGrade object with technical evaluation
        """
        # Extract key metrics
        mace = metrics.get('mean_absolute_cents_error')
        
        if mace is None:
            # No measurements available
            return PitchGrade(
                accuracy_score=0.0,
                mean_absolute_cents_error=float('inf'),
                mean_cents_error=0.0,
                std_cents_error=0.0,
                median_cents_error=0.0,
                perfect_percentage=0.0,
                excellent_percentage=0.0,
                good_percentage=0.0,
                poor_percentage=0.0,
                within_10_cents=0.0,
                within_25_cents=0.0,
                within_50_cents=0.0,
                measurement_rate=metrics.get('measurement_rate', 0.0),
                total_notes=metrics.get('total_notes', 0),
                measured_notes=metrics.get('measured_notes', 0),
                systematic_bias_detected=False,
                bias_direction='unknown',
                bias_magnitude_cents=0.0
            )
        
        # Calculate accuracy score
        accuracy_score = self.calculate_accuracy_score(mace)
        
        # Extract statistical metrics
        mean_error = metrics.get('mean_cents_error', 0.0)
        std_error = metrics.get('std_cents_error', 0.0)
        median_error = metrics.get('median_cents_error', 0.0)
        
        # Extract percentages
        breakdown = metrics.get('accuracy_breakdown', {})
        perfect_pct = breakdown.get('perfect', {}).get('percentage', 0.0)
        excellent_pct = breakdown.get('excellent', {}).get('percentage', 0.0)
        good_pct = breakdown.get('good', {}).get('percentage', 0.0)
        poor_pct = breakdown.get('poor', {}).get('percentage', 0.0)
        
        # Detect systematic bias
        bias_detected, bias_dir, bias_mag = self.detect_systematic_bias(mean_error)
        
        return PitchGrade(
            accuracy_score=accuracy_score,
            mean_absolute_cents_error=mace,
            mean_cents_error=mean_error,
            std_cents_error=std_error,
            median_cents_error=median_error,
            perfect_percentage=perfect_pct,
            excellent_percentage=excellent_pct,
            good_percentage=good_pct,
            poor_percentage=poor_pct,
            within_10_cents=metrics.get('within_10_cents', 0.0),
            within_25_cents=metrics.get('within_25_cents', 0.0),
            within_50_cents=metrics.get('within_50_cents', 0.0),
            measurement_rate=metrics.get('measurement_rate', 0.0),
            total_notes=metrics.get('total_notes', 0),
            measured_notes=metrics.get('measured_notes', 0),
            systematic_bias_detected=bias_detected,
            bias_direction=bias_dir,
            bias_magnitude_cents=bias_mag
        )
    
    def save_evaluation_report(self, grade: PitchGrade, output_path: str) -> None:
        """
        Save evaluation report to JSON file
        
        Args:
            grade: PitchGrade object
            output_path: Path to output JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(grade.to_dict(), f, indent=2)
        
        if self.verbose:
            print(f"Evaluation report saved to: {output_path}")
    
    def print_evaluation_report(self, grade: PitchGrade) -> None:
        """Print formatted evaluation report to console"""
        print("\n" + "=" * 80)
        print("PITCH ACCURACY EVALUATION - TECHNICAL METRICS")
        print("=" * 80)
        
        print(f"\nACCURACY SCORE: {grade.accuracy_score:.2f}/100")
        print(f"   Formula: 100 × exp(-MACE / 25)")
        print(f"   Where MACE = Mean Absolute Cents Error = {grade.mean_absolute_cents_error:.2f}¢")
        
        print(f"\nSTATISTICAL METRICS (Cents Error):")
        print(f"   Mean Absolute Error (MACE):  {grade.mean_absolute_cents_error:7.2f}¢")
        print(f"   Mean Signed Error:            {grade.mean_cents_error:+7.2f}¢")
        print(f"   Standard Deviation:           {grade.std_cents_error:7.2f}¢")
        print(f"   Median Error:                 {grade.median_cents_error:+7.2f}¢")
        
        print(f"\nERROR DISTRIBUTION:")
        print(f"   Perfect (<10¢):      {grade.perfect_percentage:6.2f}%")
        print(f"   Excellent (10-25¢):  {grade.excellent_percentage:6.2f}%")
        print(f"   Good (25-50¢):       {grade.good_percentage:6.2f}%")
        print(f"   Poor (≥50¢):         {grade.poor_percentage:6.2f}%")
        
        print(f"\nPRECISION THRESHOLDS:")
        print(f"   Within ±10¢: {grade.within_10_cents:6.2f}%")
        print(f"   Within ±25¢: {grade.within_25_cents:6.2f}%")
        print(f"   Within ±50¢: {grade.within_50_cents:6.2f}%")
        
        print(f"\nDETECTION METRICS:")
        print(f"   Measurement Rate: {grade.measurement_rate*100:.2f}%")
        print(f"   Total Notes:      {grade.total_notes}")
        print(f"   Measured Notes:   {grade.measured_notes}")
        print(f"   Unmeasured:       {grade.total_notes - grade.measured_notes}")
        
        print(f"\nSYSTEMATIC BIAS ANALYSIS:")
        if grade.systematic_bias_detected:
            print(f"   Bias Detected:  YES")
            print(f"   Direction:      {grade.bias_direction.upper()}")
            print(f"   Magnitude:      {grade.bias_magnitude_cents:.2f}¢")
            sign = "+" if grade.bias_direction == "sharp" else "-"
            print(f"   Interpretation: Audio pitches are systematically {sign}{grade.bias_magnitude_cents:.2f}¢")
        else:
            print(f"   Bias Detected:  NO")
            print(f"   Direction:      {grade.bias_direction}")
            print(f"   Magnitude:      {grade.bias_magnitude_cents:.2f}¢")
            print(f"   Interpretation: No systematic sharp/flat tendency (|mean error| < 10¢)")
        
        print("\n" + "=" * 80)


def main():
    """Example usage with sample metrics"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate pitch accuracy from comparison metrics')
    parser.add_argument('--metrics-json', required=True, help='Path to metrics JSON from pitch comparator')
    parser.add_argument('--output', help='Output evaluation report JSON file')
    
    args = parser.parse_args()
    
    # Load metrics
    with open(args.metrics_json, 'r') as f:
        data = json.load(f)
        metrics = data.get('metrics', {})
    
    # Evaluate performance
    grader = PitchGrader()
    evaluation = grader.evaluate_performance(metrics)
    
    # Print report
    grader.print_evaluation_report(evaluation)
    
    # Save if requested
    if args.output:
        grader.save_evaluation_report(evaluation, args.output)


if __name__ == '__main__':
    main()
