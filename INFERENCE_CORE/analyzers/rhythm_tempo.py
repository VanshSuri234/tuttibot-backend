#!/usr/bin/env python3
"""
Rhythm & Tempo Analyzer - Dimension 1 (30% weight)
==================================================

Analyzes rhythmic precision and tempo consistency.

Metrics computed:
- Onset timing accuracy
- Tempo stability
- Rhythmic deviation patterns
- Adherence to tempo markings
"""

import numpy as np
import logging
from typing import Dict, Any, List, Optional
from ..data_collector import InferenceCoreInputs
from ..utils.metric_utils import (
    compute_onset_errors,
    compute_ioi_correlation,
    compute_tempo_stability,
    normalize_to_percent,
    interpret_score
)


class RhythmTempoAnalyzer:
    """Analyzes Rhythm & Tempo Mastery (30%)"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(self, inputs: InferenceCoreInputs) -> Dict[str, Any]:
        """
        Perform complete rhythm and tempo analysis
        
        Args:
            inputs: All upstream layer data
            
        Returns:
            Dictionary with all rhythm & tempo metrics
        """
        self.logger.info("📊 Analyzing Rhythm & Tempo Mastery...")
        
        results = {
            'onset_accuracy': {},
            'tempo_stability': {},
            'rhythmic_accuracy': {},
            'tempo_marking_adherence': {},
            'overall_score': None,
            'interpretation': None
        }
        
        # Extract onset data
        score_onsets = self._extract_score_onsets(inputs)
        perf_onsets = self._extract_performance_onsets(inputs)
        time_map = inputs.time_map
        
        # 1. Onset Accuracy
        if score_onsets and perf_onsets:
            results['onset_accuracy'] = compute_onset_errors(
                score_onsets, perf_onsets, time_map
            )
            self.logger.info(f"  ✓ Onset accuracy: {results['onset_accuracy']['mean_absolute_error_ms']:.1f} ms MAE")
        else:
            self.logger.warning("  ⚠ Insufficient onset data for accuracy computation")
        
        # 2. Tempo Stability
        tempo_curve = self._extract_tempo_curve(inputs)
        if tempo_curve:
            results['tempo_stability'] = compute_tempo_stability(tempo_curve)
            results['tempo_stability']['tempo_curve'] = tempo_curve
            self.logger.info(f"  ✓ Tempo stability: CV = {results['tempo_stability']['coefficient_of_variation']:.3f}")
        else:
            self.logger.warning("  ⚠ No tempo curve available")
        
        # 3. Rhythmic Accuracy (IOI correlation)
        if score_onsets and perf_onsets and len(score_onsets) > 2:
            ioi_corr = compute_ioi_correlation(score_onsets, perf_onsets)
            
            # Count rhythmic errors
            rushed, dragged, syncopation = self._analyze_rhythmic_patterns(
                score_onsets, perf_onsets, time_map
            )
            
            results['rhythmic_accuracy'] = {
                'ioi_correlation': ioi_corr,
                'rhythm_precision_score': self._compute_rhythm_precision(ioi_corr),
                'rushed_notes_count': rushed,
                'dragged_notes_count': dragged,
                'syncopation_errors': syncopation
            }
            self.logger.info(f"  ✓ IOI correlation: {ioi_corr:.3f}")
        else:
            self.logger.warning("  ⚠ Insufficient data for rhythmic accuracy")
        
        # 4. Tempo Marking Adherence
        score_tempo = self._extract_score_tempo(inputs)
        perf_tempo = results['tempo_stability'].get('mean_tempo_bpm')
        
        if score_tempo and perf_tempo:
            deviation = abs(perf_tempo - score_tempo) / score_tempo * 100
            
            results['tempo_marking_adherence'] = {
                'score_tempo_bpm': score_tempo,
                'performance_mean_tempo_bpm': perf_tempo,
                'deviation_percentage': deviation,
                'interpretation': self._interpret_tempo_adherence(deviation)
            }
            self.logger.info(f"  ✓ Tempo adherence: {deviation:.1f}% deviation")
        else:
            self.logger.warning("  ⚠ Tempo marking data incomplete")
        
        # Compute overall score
        results['overall_score'] = self._compute_overall_score(results)
        results['interpretation'] = interpret_score(
            results['overall_score'],
            {
                'excellent': (90, 100),
                'good': (75, 90),
                'fair': (60, 75),
                'poor': (0, 60)
            }
        )
        
        self.logger.info(f"  → Overall Rhythm & Tempo Score: {results['overall_score']:.1f}/100 ({results['interpretation']})")
        
        return results
    
    def _extract_score_onsets(self, inputs: InferenceCoreInputs) -> List[float]:
        """Extract expected onset times from score"""
        onsets = []
        
        # Try ScoreGraph first
        if inputs.scoregraph and 'musical_notes' in inputs.scoregraph:
            for note in inputs.scoregraph['musical_notes']:
                onset = note.get('onset_sec', note.get('onset_time'))
                if onset is not None:
                    onsets.append(float(onset))
        
        # Fallback to music_features
        elif inputs.music_features and 'music_features' in inputs.music_features:
            features = inputs.music_features['music_features']
            if 'notes' in features:
                for note in features['notes']:
                    onset = note.get('offset', 0)  # Music21 uses 'offset' for time
                    if onset is not None:
                        onsets.append(float(onset))
        
        # Fallback to score_features
        elif inputs.score_features and 'note_onsets' in inputs.score_features:
            onsets = [float(o) for o in inputs.score_features['note_onsets']]
        
        return sorted(onsets)
    
    def _extract_performance_onsets(self, inputs: InferenceCoreInputs) -> List[float]:
        """Extract performed onset times"""
        onsets = []
        
        # Try transcription first
        if inputs.transcription and 'notes' in inputs.transcription:
            for note in inputs.transcription['notes']:
                onset = note.get('onset_time', note.get('start'))
                if onset is not None:
                    onsets.append(float(onset))
        
        # Fallback to performance_features
        elif inputs.performance_features and 'onset_times' in inputs.performance_features:
            onsets = [float(o) for o in inputs.performance_features['onset_times']]
        
        return sorted(onsets)
    
    def _extract_tempo_curve(self, inputs: InferenceCoreInputs) -> List[float]:
        """Extract tempo curve from performance"""
        if inputs.performance_features and 'tempo_bpm' in inputs.performance_features:
            tempo = inputs.performance_features['tempo_bpm']
            if isinstance(tempo, (int, float)):
                return [float(tempo)]
            elif isinstance(tempo, list):
                return [float(t) for t in tempo]
        
        return None
    
    def _extract_score_tempo(self, inputs: InferenceCoreInputs) -> Optional[float]:
        """Extract tempo marking from score"""
        # Try music_features
        if inputs.music_features:
            if isinstance(inputs.music_features.get('tempo'), (int, float)):
                return float(inputs.music_features['tempo'])
            elif 'music_features' in inputs.music_features:
                tempo = inputs.music_features['music_features'].get('tempo')
                if isinstance(tempo, (int, float)):
                    return float(tempo)
        
        # Try scoregraph
        if inputs.scoregraph and 'tempo_marks' in inputs.scoregraph:
            if inputs.scoregraph['tempo_marks']:
                return float(inputs.scoregraph['tempo_marks'][0].get('bpm', 120))
        
        return None
    
    def _analyze_rhythmic_patterns(self, score_onsets: List[float],
                                   perf_onsets: List[float],
                                   time_map: Optional[List[Dict]]) -> tuple:
        """
        Analyze rhythmic error patterns
        
        Returns:
            (rushed_count, dragged_count, syncopation_errors)
        """
        if not score_onsets or not perf_onsets:
            return (0, 0, 0)
        
        errors = []
        min_len = min(len(score_onsets), len(perf_onsets))
        
        for i in range(min_len):
            error = (perf_onsets[i] - score_onsets[i]) * 1000  # ms
            errors.append(error)
        
        # Count rushed (negative) and dragged (positive)
        rushed = sum(1 for e in errors if e < -30)  # > 30ms early
        dragged = sum(1 for e in errors if e > 30)   # > 30ms late
        
        # Syncopation errors (large IOI deviations)
        if len(errors) > 2:
            ioi_errors = np.diff(errors)
            syncopation = sum(1 for ie in ioi_errors if abs(ie) > 50)
        else:
            syncopation = 0
        
        return (rushed, dragged, syncopation)
    
    def _compute_rhythm_precision(self, ioi_correlation: Optional[float]) -> Optional[float]:
        """Compute rhythm precision score from IOI correlation"""
        if ioi_correlation is None:
            return None
        
        # Convert correlation (0-1) to score (0-100)
        # Higher correlation = better rhythm precision
        return normalize_to_percent(ioi_correlation, 0.5, 1.0, invert=False)
    
    def _interpret_tempo_adherence(self, deviation_pct: float) -> str:
        """Interpret tempo deviation percentage"""
        if deviation_pct < 5:
            return "faithful"
        elif deviation_pct < 15:
            return "moderate rubato"
        elif deviation_pct < 30:
            return "significant rubato"
        else:
            return "deviated"
    
    def _compute_overall_score(self, results: Dict) -> float:
        """Compute overall rhythm & tempo score (0-100)"""
        scores = []
        weights = []
        
        # Onset accuracy (40% weight within this dimension)
        if results['onset_accuracy'].get('percentage_within_50ms') is not None:
            score = results['onset_accuracy']['percentage_within_50ms']
            scores.append(score)
            weights.append(0.40)
        
        # Tempo stability (30% weight)
        if results['tempo_stability'].get('coefficient_of_variation') is not None:
            cv = results['tempo_stability']['coefficient_of_variation']
            # Lower CV is better; normalize: CV of 0.05 = 100, CV of 0.30 = 0
            score = normalize_to_percent(cv, 0.0, 0.30, invert=True)
            scores.append(score)
            weights.append(0.30)
        
        # Rhythmic accuracy (20% weight)
        if results['rhythmic_accuracy'].get('rhythm_precision_score') is not None:
            scores.append(results['rhythmic_accuracy']['rhythm_precision_score'])
            weights.append(0.20)
        
        # Tempo adherence (10% weight)
        if results['tempo_marking_adherence'].get('deviation_percentage') is not None:
            dev = results['tempo_marking_adherence']['deviation_percentage']
            # Lower deviation is better; normalize: 0% = 100, 50% = 0
            score = normalize_to_percent(dev, 0.0, 50.0, invert=True)
            scores.append(score)
            weights.append(0.10)
        
        if not scores:
            return 0.0
        
        # Weighted average
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return float(weighted_sum / total_weight)
