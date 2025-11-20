"""
Evaluation metrics module
- Mean Note Error (MNE)
- Mean Frame Error (MFE)  
- Alignment rates at various thresholds
"""

import numpy as np
import mir_eval


class Evaluator:
    """Evaluation metrics for audio-to-score alignment"""
    
    def __init__(self, thresholds_ms=None):
        """
        Args:
            thresholds_ms: list of thresholds in milliseconds for alignment rate
        """
        self.thresholds_ms = thresholds_ms or [30, 60, 90, 120, 150, 180, 200]
    
    def compute_note_errors(self, predicted_onsets, ground_truth_onsets):
        """
        Compute onset errors
        
        Args:
            predicted_onsets: (N,) array of predicted onset times
            ground_truth_onsets: (N,) array of ground truth onset times
        
        Returns:
            errors: (N,) array of absolute errors
            MNE: mean note error
        """
        predicted_onsets = np.array(predicted_onsets)
        ground_truth_onsets = np.array(ground_truth_onsets)
        
        errors = np.abs(predicted_onsets - ground_truth_onsets)
        MNE = np.mean(errors)
        
        return errors, MNE
    
    def compute_frame_errors(self, predicted_offsets, ground_truth_offsets):
        """
        Compute offset errors (frame = offset in paper terminology)
        
        Args:
            predicted_offsets: (N,) array of predicted offset times
            ground_truth_offsets: (N,) array of ground truth offset times
        
        Returns:
            errors: (N,) array of absolute errors
            MFE: mean frame error
        """
        predicted_offsets = np.array(predicted_offsets)
        ground_truth_offsets = np.array(ground_truth_offsets)
        
        errors = np.abs(predicted_offsets - ground_truth_offsets)
        MFE = np.mean(errors)
        
        return errors, MFE
    
    def compute_alignment_rates(self, errors):
        """
        Compute alignment rate at each threshold
        
        Args:
            errors: (N,) array of errors in seconds
        
        Returns:
            rates: dict mapping threshold_ms -> alignment_rate (0-100%)
        """
        errors_ms = errors * 1000  # Convert to ms
        
        rates = {}
        for threshold_ms in self.thresholds_ms:
            n_aligned = np.sum(errors_ms <= threshold_ms)
            rate = 100.0 * n_aligned / len(errors) if len(errors) > 0 else 0.0
            rates[threshold_ms] = rate
        
        return rates
    
    def evaluate_full(self, predicted_notes, ground_truth_notes):
        """
        Full evaluation: onset + offset errors and alignment rates
        
        Args:
            predicted_notes: list of dicts with 'onset' and 'offset'
            ground_truth_notes: list of dicts with 'onset' and 'offset'
        
        Returns:
            results: dict with all metrics
        """
        # Extract arrays
        pred_onsets = np.array([n['onset'] for n in predicted_notes])
        pred_offsets = np.array([n['offset'] for n in predicted_notes])
        gt_onsets = np.array([n['onset'] for n in ground_truth_notes])
        gt_offsets = np.array([n['offset'] for n in ground_truth_notes])
        
        # Onset errors
        onset_errors, MNE = self.compute_note_errors(pred_onsets, gt_onsets)
        onset_rates = self.compute_alignment_rates(onset_errors)
        
        # Offset errors
        offset_errors, MFE = self.compute_frame_errors(pred_offsets, gt_offsets)
        offset_rates = self.compute_alignment_rates(offset_errors)
        
        results = {
            'MNE': MNE,
            'MFE': MFE,
            'onset_errors': onset_errors,
            'offset_errors': offset_errors,
            'onset_alignment_rates': onset_rates,
            'offset_alignment_rates': offset_rates,
            'n_notes': len(predicted_notes)
        }
        
        return results
    
    def print_results(self, results):
        """Pretty print evaluation results"""
        print(f"\n{'='*60}")
        print(f"PQG-A2SA Evaluation Results")
        print(f"{'='*60}")
        print(f"Total notes: {results['n_notes']}")
        print(f"\nMean Note Error (MNE):  {results['MNE']*1000:.2f} ms")
        print(f"Mean Frame Error (MFE): {results['MFE']*1000:.2f} ms")
        
        print(f"\nOnset Alignment Rates:")
        for threshold_ms, rate in sorted(results['onset_alignment_rates'].items()):
            print(f"  ≤{threshold_ms:3d} ms: {rate:6.2f}%")
        
        print(f"\nOffset Alignment Rates:")
        for threshold_ms, rate in sorted(results['offset_alignment_rates'].items()):
            print(f"  ≤{threshold_ms:3d} ms: {rate:6.2f}%")
        
        print(f"{'='*60}\n")
    
    def use_mir_eval(self, predicted_onsets, ground_truth_onsets, tolerance=0.05):
        """
        Use mir_eval for standard onset detection metrics
        
        Args:
            predicted_onsets: (N,) array
            ground_truth_onsets: (M,) array
            tolerance: tolerance window in seconds
        
        Returns:
            scores: dict with precision, recall, F-measure
        """
        predicted_onsets = np.array(predicted_onsets)
        ground_truth_onsets = np.array(ground_truth_onsets)
        
        scores = mir_eval.onset.evaluate(
            ground_truth_onsets,
            predicted_onsets,
            window=tolerance
        )
        
        return {
            'precision': scores['Precision'],
            'recall': scores['Recall'],
            'f_measure': scores['F-measure']
        }
