#!/usr/bin/env python3
"""
PQG-A2SA Metrics Recomputer
============================

This module recomputes grading metrics using PQG-A2SA's precise onset/offset alignments
to override DTW-based metrics from Block 2 when PQG-A2SA results are available.

This implements the "Two-Pass Approach":
1. Block 2 computes grading metrics using DTW alignment (first pass)
2. Inference Core recomputes metrics using PQG-A2SA alignments if available (second pass)
3. PQG-A2SA metrics override DTW metrics for better accuracy

Author: TuttiBot Team
Date: November 2025
Version: 1.0
"""

import json
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class PQGMetricsRecomputer:
    """
    Recomputes grading metrics using PQG-A2SA alignment results
    
    This class takes PQG-A2SA's precise note-level alignments and recomputes
    the same grading metrics that Block 2 computes, but with higher accuracy
    due to PQG-A2SA's superior onset/offset detection.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the recomputer
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('PQGMetricsRecomputer')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def load_pqg_results(self, pqg_results_path: Path) -> Optional[Dict]:
        """
        Load PQG-A2SA results from JSON file
        
        Args:
            pqg_results_path: Path to pqg_a2sa_results.json
            
        Returns:
            PQG-A2SA results dictionary or None if loading fails
        """
        try:
            if not pqg_results_path.exists():
                self.logger.warning(f"PQG-A2SA results not found: {pqg_results_path}")
                return None
            
            with open(pqg_results_path, 'r') as f:
                pqg_results = json.load(f)
            
            self.logger.info(f"✓ Loaded PQG-A2SA results: {pqg_results_path.name}")
            return pqg_results
            
        except Exception as e:
            self.logger.error(f"Failed to load PQG-A2SA results: {e}")
            return None
    
    def extract_pqg_performance_notes(self, pqg_results: Dict) -> List[Dict]:
        """
        Extract performance notes from PQG-A2SA results
        
        Args:
            pqg_results: PQG-A2SA results dictionary
            
        Returns:
            List of performance note dictionaries with refined timings
        """
        if 'instruments' in pqg_results and len(pqg_results['instruments']) > 0:
            # PQG-A2SA format: extract notes from first instrument
            instrument_data = pqg_results['instruments'][0]
            if 'notes' in instrument_data:
                perf_notes = instrument_data['notes']
                self.logger.info(f"  Extracted {len(perf_notes)} performance notes from PQG-A2SA")
                return perf_notes
            else:
                self.logger.warning("No notes found in PQG-A2SA instrument data")
                return []
        else:
            self.logger.warning("No instruments found in PQG-A2SA results")
            return []
    
    def merge_pqg_with_dtw_alignment(
        self,
        dtw_note_alignments: List[Dict],
        pqg_perf_notes: List[Dict]
    ) -> List[Dict]:
        """
        Merge PQG-A2SA's refined performance timings with DTW's note matching
        
        Strategy:
        - DTW provides score-to-performance note matching (which notes correspond)
        - PQG-A2SA provides refined performance note timings (more accurate onset/offset)
        - We replace DTW's performance timings with PQG's refined timings
        - Then recompute onset/offset errors based on PQG timings
        
        Args:
            dtw_note_alignments: DTW note alignments with score matching
            pqg_perf_notes: PQG-A2SA refined performance notes
            
        Returns:
            Enhanced note alignments with PQG timings
        """
        if not dtw_note_alignments or not pqg_perf_notes:
            self.logger.warning("Missing DTW or PQG data for merging")
            return dtw_note_alignments
        
        self.logger.info(f"  Merging {len(pqg_perf_notes)} PQG notes with {len(dtw_note_alignments)} DTW alignments")
        
        # Create pitch-onset index for PQG notes (for matching)
        pqg_by_pitch = {}
        for pqg_note in pqg_perf_notes:
            pitch = pqg_note['pitch']
            if pitch not in pqg_by_pitch:
                pqg_by_pitch[pitch] = []
            pqg_by_pitch[pitch].append(pqg_note)
        
        # Match DTW alignments with PQG refined timings
        enhanced_alignments = []
        pqg_matched = set()
        
        for dtw_align in dtw_note_alignments:
            perf_note = dtw_align.get('performance_note', {})
            score_note = dtw_align.get('score_note', {})
            
            if not perf_note or not score_note:
                # Keep original if missing data
                enhanced_alignments.append(dtw_align.copy())
                continue
            
            pitch = perf_note.get('pitch')
            dtw_onset = perf_note.get('onset', 0)
            
            # Find closest matching PQG note by pitch and onset time
            best_match = None
            best_onset_diff = float('inf')
            
            if pitch in pqg_by_pitch:
                for idx, pqg_note in enumerate(pqg_by_pitch[pitch]):
                    pqg_idx = (pitch, idx)
                    if pqg_idx in pqg_matched:
                        continue
                    
                    onset_diff = abs(pqg_note['onset'] - dtw_onset)
                    if onset_diff < best_onset_diff:
                        best_onset_diff = onset_diff
                        best_match = (pqg_note, pqg_idx)
            
            # Use PQG timing if good match found (within 100ms)
            if best_match and best_onset_diff < 0.1:
                pqg_note, pqg_idx = best_match
                pqg_matched.add(pqg_idx)
                
                # Create enhanced alignment with PQG timings
                enhanced_align = dtw_align.copy()
                
                # Update performance note with PQG refined timings
                enhanced_perf = perf_note.copy()
                enhanced_perf['onset'] = pqg_note['onset']
                enhanced_perf['offset'] = pqg_note['offset']
                enhanced_perf['duration'] = pqg_note['offset'] - pqg_note['onset']
                if 'velocity' in pqg_note:
                    enhanced_perf['velocity'] = pqg_note['velocity']
                
                enhanced_align['performance_note'] = enhanced_perf
                
                # Recompute errors with PQG timings
                score_onset = score_note.get('onset', 0)
                score_offset = score_note.get('offset', 0)
                
                enhanced_align['onset_error_ms'] = (pqg_note['onset'] - score_onset) * 1000
                enhanced_align['offset_error_ms'] = (pqg_note['offset'] - score_offset) * 1000
                
                # Pitch error stays the same (from DTW)
                # Other metadata stays the same
                
                enhanced_alignments.append(enhanced_align)
            else:
                # No good PQG match, keep DTW timing
                enhanced_alignments.append(dtw_align.copy())
        
        matched_count = len(pqg_matched)
        self.logger.info(f"  ✓ Matched {matched_count}/{len(pqg_perf_notes)} PQG notes to DTW alignments")
        
        return enhanced_alignments
    
    def recompute_rhythm_tempo_metrics(self, enhanced_alignments: List[Dict]) -> Dict[str, Any]:
        """
        Recompute Rhythm & Tempo metrics using PQG-enhanced alignments
        
        This replicates Block 2's rhythm/tempo metrics but uses PQG-A2SA's
        more accurate onset/offset times (merged with DTW's note matching).
        
        Args:
            enhanced_alignments: Note alignments with PQG-refined timings
            
        Returns:
            Dictionary with rhythm/tempo metrics
        """
        if not enhanced_alignments:
            return {}
        
        self.logger.info("  Recomputing rhythm/tempo metrics from PQG-enhanced alignments...")
        
        # Extract onset errors (ms) - now computed from PQG timings
        onset_errors = []
        for align in enhanced_alignments:
            if 'onset_error_ms' in align:
                onset_errors.append(align['onset_error_ms'])
        
        if not onset_errors:
            self.logger.warning("    No onset errors found in alignments")
            return {}
        
        # Onset accuracy statistics
        onset_errors_arr = np.array(onset_errors)
        mean_onset_error = float(np.mean(np.abs(onset_errors_arr)))
        onset_std = float(np.std(onset_errors_arr))
        
        self.logger.info(f"    Mean onset error: {mean_onset_error:.2f} ms (PQG-enhanced)")
        
        # Extract onset times for IOI analysis
        score_onsets = []
        perf_onsets = []
        
        for align in enhanced_alignments:
            # Try different possible key structures
            if 'score_note' in align and 'performance_note' in align:
                score_onsets.append(align['score_note'].get('onset', align['score_note'].get('start', 0)))
                perf_onsets.append(align['performance_note'].get('onset', align['performance_note'].get('start', 0)))
            elif 'score_onset' in align and 'perf_onset' in align:
                score_onsets.append(align['score_onset'])
                perf_onsets.append(align['perf_onset'])
            elif 'expected_onset' in align and 'performed_onset' in align:
                score_onsets.append(align['expected_onset'])
                perf_onsets.append(align['performed_onset'])
        
        # IOI correlation
        ioi_corr = 1.0
        tempo_cv = 0.0
        
        if len(score_onsets) > 1:
            score_iois = np.diff(score_onsets)
            perf_iois = np.diff(perf_onsets)
            
            if len(score_iois) > 1:
                # Pearson correlation
                corr_matrix = np.corrcoef(score_iois, perf_iois)
                ioi_corr = float(corr_matrix[0, 1]) if not np.isnan(corr_matrix[0, 1]) else 1.0
            
            # Tempo stability (coefficient of variation)
            if np.mean(perf_iois) > 0:
                tempo_cv = float((np.std(perf_iois) / np.mean(perf_iois)) * 100)
        
        metrics = {
            'mean_onset_error_ms': mean_onset_error,
            'onset_std_ms': onset_std,
            'ioi_correlation': ioi_corr,
            'tempo_cv_percent': tempo_cv,
            'onset_error_distribution': {
                'min': float(np.min(onset_errors_arr)),
                'max': float(np.max(onset_errors_arr)),
                'median': float(np.median(onset_errors_arr)),
                'q25': float(np.percentile(onset_errors_arr, 25)),
                'q75': float(np.percentile(onset_errors_arr, 75))
            },
            'source': 'PQG-A2SA',  # Mark that this came from PQG-A2SA
            'pqg_enhanced': True
        }
        
        self.logger.info(f"    ✓ IOI correlation: {ioi_corr:.3f}")
        self.logger.info(f"    ✓ Mean onset error: {mean_onset_error:.2f} ms")
        
        return metrics
    
    def recompute_sound_quality_metrics(self, enhanced_alignments: List[Dict]) -> Dict[str, Any]:
        """
        Recompute Sound Quality metrics using PQG-enhanced alignments
        
        Note: Pitch errors come from DTW (unchanged), but we keep the same
        structure for consistency.
        
        Args:
            enhanced_alignments: Note alignments with PQG-refined timings
            
        Returns:
            Dictionary with sound quality metrics
        """
        if not enhanced_alignments:
            return {}
        
        self.logger.info("  Recomputing sound quality metrics from PQG-enhanced alignments...")
        
        # Extract pitch errors (cents) - these come from DTW, unchanged
        pitch_errors = []
        for align in enhanced_alignments:
            if 'pitch_error_cents' in align:
                pitch_errors.append(align['pitch_error_cents'])
        
        if not pitch_errors:
            self.logger.warning("    No pitch errors found in alignments")
            return {}
        
        pitch_errors_arr = np.array(pitch_errors)
        pitch_errors_abs = np.abs(pitch_errors_arr)
        
        # Pitch accuracy - threshold from env or default 50 cents
        import os as _os
        pitch_threshold = int(_os.environ.get("PITCH_THRESHOLD", 50))
        
        # Main threshold (configurable)
        accurate_50c = sum(1 for err in pitch_errors_abs if err < pitch_threshold)
        # Also compute for 25 cents (stricter reference)
        accurate_25c = sum(1 for err in pitch_errors_abs if err < 25)
        
        pitch_accuracy_50c = (accurate_50c / len(pitch_errors)) * 100
        pitch_accuracy_25c = (accurate_25c / len(pitch_errors)) * 100
        
        metrics = {
            'pitch_accuracy_50c_percent': float(pitch_accuracy_50c),
            'pitch_accuracy_25c_percent': float(pitch_accuracy_25c),
            'mean_pitch_error_cents': float(np.mean(pitch_errors_abs)),
            'pitch_error_std_cents': float(np.std(pitch_errors_arr)),
            'pitch_errors_distribution': {
                'min': float(np.min(pitch_errors_arr)),
                'max': float(np.max(pitch_errors_arr)),
                'median': float(np.median(pitch_errors_arr)),
                'q25': float(np.percentile(pitch_errors_arr, 25)),
                'q75': float(np.percentile(pitch_errors_arr, 75))
            },
            'note_pitch_errors': [float(e) for e in pitch_errors],
            'source': 'DTW (pitch unchanged)',
            'pqg_enhanced': False  # Pitch comes from DTW
        }
        
        self.logger.info(f"    Pitch accuracy (50¢): {pitch_accuracy_50c:.2f}%")
        
        return metrics
    
    def recompute_technical_virtuosity_metrics(
        self,
        enhanced_alignments: List[Dict],
        score_note_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recompute Technical Virtuosity metrics using PQG-enhanced alignments
        
        Args:
            enhanced_alignments: Note alignments with PQG-refined timings
            score_note_count: Total number of notes in score (if known)
            
        Returns:
            Dictionary with technical virtuosity metrics
        """
        if not enhanced_alignments:
            return {}
        
        self.logger.info("  Recomputing technical virtuosity metrics from PQG-enhanced alignments...")
        
        # Note accuracy
        matched_notes = len(enhanced_alignments)
        
        # Try to get total score notes from alignments or use parameter
        if score_note_count is None:
            # Try to infer from alignments
            score_note_count = matched_notes  # Conservative estimate
        
        note_accuracy = (matched_notes / score_note_count) * 100 if score_note_count > 0 else 0
        
        # Fluency (IOI CV) - uses PQG-refined performance timings
        fluency_cv = 0.0
        if len(enhanced_alignments) > 1:
            perf_onsets = []
            for align in enhanced_alignments:
                if 'performance_note' in align and 'onset' in align['performance_note']:
                    perf_onsets.append(align['performance_note']['onset'])
            
            if len(perf_onsets) > 1:
                perf_iois = np.diff(perf_onsets)
                if np.mean(perf_iois) > 0:
                    fluency_cv = float((np.std(perf_iois) / np.mean(perf_iois)) * 100)
        
        # Articulation precision - uses PQG-refined onset errors
        onset_errors = []
        for align in enhanced_alignments:
            if 'onset_error_ms' in align:
                onset_errors.append(align['onset_error_ms'])
            elif 'onset_error' in align:
                onset_errors.append(align['onset_error'] * 1000)
        
        articulation_precision = float(np.std(onset_errors)) if onset_errors else 0.0
        
        metrics = {
            'note_accuracy_percent': float(note_accuracy),
            'matched_notes': matched_notes,
            'total_score_notes': score_note_count,
            'unmatched_notes': max(0, score_note_count - matched_notes),
            'fluency_ioi_cv_percent': fluency_cv,
            'articulation_precision_ms': articulation_precision,
            'source': 'PQG-A2SA',
            'pqg_enhanced': True
        }
        
        self.logger.info(f"    ✓ Note accuracy: {note_accuracy:.2f}%")
        
        return metrics
    
    def recompute_all_metrics(
        self,
        pqg_results: Dict,
        dtw_note_alignments: List[Dict],
        score_note_count: Optional[int] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Recompute all grading metrics using PQG-A2SA results merged with DTW alignments
        
        Strategy:
        1. Extract PQG performance notes (refined timings)
        2. Merge with DTW alignments (provides score matching)
        3. Recompute metrics from enhanced alignments
        
        Args:
            pqg_results: PQG-A2SA results dictionary
            dtw_note_alignments: DTW note alignments (for score matching)
            score_note_count: Total number of notes in score (optional)
            
        Returns:
            Dictionary with all recomputed metrics organized by dimension
        """
        self.logger.info("\n" + "=" * 70)
        self.logger.info("RECOMPUTING METRICS FROM PQG-A2SA")
        self.logger.info("=" * 70)
        
        # Extract PQG performance notes
        pqg_perf_notes = self.extract_pqg_performance_notes(pqg_results)
        
        if not pqg_perf_notes:
            self.logger.warning("No PQG performance notes available - cannot recompute metrics")
            return {}
        
        if not dtw_note_alignments:
            self.logger.warning("No DTW alignments available - cannot match score notes")
            return {}
        
        # Merge PQG timings with DTW matching
        enhanced_alignments = self.merge_pqg_with_dtw_alignment(
            dtw_note_alignments,
            pqg_perf_notes
        )
        
        if not enhanced_alignments:
            self.logger.warning("Failed to create enhanced alignments")
            return {}
        
        # Recompute each dimension
        recomputed_metrics = {}
        
        # Dimension 1: Rhythm & Tempo
        rhythm_tempo = self.recompute_rhythm_tempo_metrics(enhanced_alignments)
        if rhythm_tempo:
            recomputed_metrics['rhythm_tempo'] = rhythm_tempo
        
        # Dimension 2: Sound Quality
        sound_quality = self.recompute_sound_quality_metrics(enhanced_alignments)
        if sound_quality:
            recomputed_metrics['sound_quality'] = sound_quality
        
        # Dimension 3: Technical Virtuosity
        technical = self.recompute_technical_virtuosity_metrics(enhanced_alignments, score_note_count)
        if technical:
            recomputed_metrics['technical_virtuosity'] = technical
        
        # Note: Phrasing and Communicativeness would require additional score structure info
        # For now, we leave those as DTW-based since PQG-A2SA focuses on note-level alignment
        
        self.logger.info("\n✓ Recomputed metrics for {} dimensions using PQG-A2SA".format(
            len(recomputed_metrics)
        ))
        self.logger.info("=" * 70 + "\n")
        
        return recomputed_metrics
    
    def merge_metrics(self, dtw_metrics: Dict[str, Any],
                     pqg_metrics: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Merge DTW and PQG-A2SA metrics, with PQG-A2SA overriding when available
        
        Args:
            dtw_metrics: Original metrics from Block 2 DTW
            pqg_metrics: Recomputed metrics from PQG-A2SA
            
        Returns:
            Tuple of (merged_metrics, source_map)
            - merged_metrics: Combined metrics with PQG-A2SA overrides
            - source_map: Dictionary tracking which metrics came from which source
        """
        self.logger.info("Merging DTW and PQG-A2SA metrics...")
        
        merged = dtw_metrics.copy()
        source_map = {}
        
        # Track what got overridden
        overridden_count = 0
        
        for dimension, pqg_dim_metrics in pqg_metrics.items():
            if dimension in merged:
                # Override with PQG-A2SA metrics
                merged[dimension] = pqg_dim_metrics
                source_map[dimension] = 'PQG-A2SA'
                overridden_count += 1
                self.logger.info(f"  ✓ Overridden '{dimension}' with PQG-A2SA metrics")
            else:
                # Add new dimension (shouldn't happen usually)
                merged[dimension] = pqg_dim_metrics
                source_map[dimension] = 'PQG-A2SA'
        
        # Mark dimensions that remain from DTW
        for dimension in merged:
            if dimension not in source_map:
                source_map[dimension] = 'DTW (Block 2)'
        
        self.logger.info(f"\n✓ Merged metrics: {overridden_count} dimensions from PQG-A2SA, "
                        f"{len(merged) - overridden_count} from DTW")
        
        return merged, source_map


def test_recomputer():
    """Test function for the recomputer"""
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python pqg_metrics_recomputer.py <path_to_pqg_results.json>")
        sys.exit(1)
    
    pqg_path = Path(sys.argv[1])
    
    recomputer = PQGMetricsRecomputer()
    
    # Load PQG results
    pqg_results = recomputer.load_pqg_results(pqg_path)
    
    if pqg_results:
        # Recompute metrics
        metrics = recomputer.recompute_all_metrics(pqg_results)
        
        # Print results
        print("\n" + "=" * 70)
        print("RECOMPUTED METRICS")
        print("=" * 70)
        for dim, dim_metrics in metrics.items():
            print(f"\n{dim}:")
            for key, value in dim_metrics.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")


if __name__ == "__main__":
    test_recomputer()
