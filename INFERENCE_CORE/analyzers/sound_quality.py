#!/usr/bin/env python3
"""
Sound Quality Analyzer - Dimension 2 (20% weight)
=================================================

Analyzes pitch accuracy and tone quality.

Metrics computed:
- Pitch accuracy (intonation)
- Tone clarity and stability
- Timbre control and matching
"""

import numpy as np
import logging
from typing import Dict, Any, List, Optional
from ..data_collector import InferenceCoreInputs
from ..utils.metric_utils import (
    compute_pitch_errors,
    compute_spectral_stability,
    compute_dynamic_range,
    normalize_to_percent,
    interpret_score
)


class SoundQualityAnalyzer:
    """Analyzes Sound Quality (20%)"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(self, inputs: InferenceCoreInputs) -> Dict[str, Any]:
        """
        Perform complete sound quality analysis
        
        Args:
            inputs: All upstream layer data
            
        Returns:
            Dictionary with all sound quality metrics
        """
        self.logger.info("📊 Analyzing Sound Quality...")
        
        results = {
            'pitch_accuracy': {},
            'tone_quality': {},
            'timbre_control': {},
            'intonation_grade': {},
            'overall_score': None,
            'interpretation': None
        }
        
        # Extract pitch data
        score_pitches = self._extract_score_pitches(inputs)
        perf_pitches = self._extract_performance_pitches(inputs)
        
        # 1. Pitch Accuracy
        if score_pitches and perf_pitches:
            pitch_metrics = compute_pitch_errors(score_pitches, perf_pitches)
            results['pitch_accuracy'] = pitch_metrics
            
            # Add pitch stability from F0 analysis
            if inputs.performance_features:
                pitch_contour = inputs.performance_features.get('fundamental_frequencies', [])
                pitch_confidence = inputs.performance_features.get('pitch_confidence', [])
                
                if pitch_contour:
                    stability = self._compute_pitch_stability(pitch_contour, pitch_confidence)
                    results['pitch_accuracy']['pitch_stability'] = stability
            
            self.logger.info(f"  ✓ Pitch accuracy: {pitch_metrics['pitch_match_rate']:.1f}% correct")
        else:
            self.logger.warning("  ⚠ Insufficient pitch data")
        
        # 2. Tone Quality
        if inputs.performance_features:
            results['tone_quality'] = self._analyze_tone_quality(inputs.performance_features)
            self.logger.info(f"  ✓ Tone quality analyzed")
        else:
            self.logger.warning("  ⚠ No performance features for tone analysis")
        
        # 3. Timbre Control
        if inputs.performance_features:
            results['timbre_control'] = self._analyze_timbre_control(inputs.performance_features)
            self.logger.info(f"  ✓ Timbre control analyzed")
        else:
            self.logger.warning("  ⚠ No performance features for timbre analysis")
        
        # 4. Overall Intonation Grade
        results['intonation_grade'] = self._compute_intonation_grade(results)
        
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
        
        self.logger.info(f"  → Overall Sound Quality Score: {results['overall_score']:.1f}/100 ({results['interpretation']})")
        
        return results
    
    def _extract_score_pitches(self, inputs: InferenceCoreInputs) -> List[int]:
        """Extract expected MIDI pitches from score"""
        pitches = []
        
        # Try score_features first
        if inputs.score_features and 'expected_pitches' in inputs.score_features:
            pitches = [int(p) for p in inputs.score_features['expected_pitches']]
        
        # Fallback to music_features
        elif inputs.music_features:
            if 'music_features' in inputs.music_features:
                features = inputs.music_features['music_features']
                if 'notes' in features:
                    for note in features['notes']:
                        midi = note.get('midi_number', note.get('pitch'))
                        if midi is not None and midi >= 0:
                            pitches.append(int(midi))
        
        # Fallback to scoregraph
        elif inputs.scoregraph and 'musical_notes' in inputs.scoregraph:
            for note in inputs.scoregraph['musical_notes']:
                pitch = note.get('pitch', note.get('midi'))
                if pitch is not None and pitch >= 0:
                    pitches.append(int(pitch))
        
        return pitches
    
    def _extract_performance_pitches(self, inputs: InferenceCoreInputs) -> List[int]:
        """Extract performed MIDI pitches"""
        pitches = []
        
        # Try transcription
        if inputs.transcription and 'notes' in inputs.transcription:
            for note in inputs.transcription['notes']:
                pitch = note.get('pitch_midi', note.get('pitch'))
                if pitch is not None:
                    pitches.append(int(pitch))
        
        return pitches
    
    def _compute_pitch_stability(self, pitch_contour: List[float],
                                 confidence: List[float]) -> float:
        """
        Compute pitch stability from F0 contour
        
        Returns:
            Stability score (0-1, higher is more stable)
        """
        if not pitch_contour or len(pitch_contour) < 10:
            return None
        
        # Filter out low-confidence and zero values
        valid_pitches = []
        for i, (pitch, conf) in enumerate(zip(pitch_contour, confidence)):
            if pitch > 0 and (not confidence or conf > 0.5):
                valid_pitches.append(pitch)
        
        if len(valid_pitches) < 10:
            return None
        
        # Compute coefficient of variation
        mean_pitch = np.mean(valid_pitches)
        std_pitch = np.std(valid_pitches)
        
        if mean_pitch == 0:
            return None
        
        cv = std_pitch / mean_pitch
        
        # Convert to stability score (lower CV = higher stability)
        # Typical good CV: < 0.05, poor CV: > 0.20
        stability = 1.0 - min(cv / 0.20, 1.0)
        
        return float(stability)
    
    def _analyze_tone_quality(self, perf_features: Dict) -> Dict:
        """Analyze tone quality from spectral features"""
        results = {}
        
        # Harmonic vs noise ratio
        harmonic = perf_features.get('harmonic_content', [])
        rms = perf_features.get('rms_energy', [])
        
        if harmonic and rms:
            harmonic_array = np.array(harmonic)
            rms_array = np.array(rms)
            
            # Filter non-zero values
            valid_mask = rms_array > 0
            if np.sum(valid_mask) > 0:
                harmonic_ratio = harmonic_array[valid_mask] / rms_array[valid_mask]
                results['harmonic_ratio_mean'] = float(np.mean(harmonic_ratio))
                results['harmonic_ratio_std'] = float(np.std(harmonic_ratio))
        
        # Spectral centroid (brightness)
        spectral_centroid = perf_features.get('spectral_centroid', [])
        if spectral_centroid:
            results['spectral_centroid_mean'] = float(np.mean(spectral_centroid))
            results['spectral_centroid_std'] = float(np.std(spectral_centroid))
        
        # Tone clarity score (composite)
        if 'harmonic_ratio_mean' in results:
            # Higher harmonic ratio = clearer tone
            # Typical good value: > 0.6, poor: < 0.3
            clarity = normalize_to_percent(results['harmonic_ratio_mean'], 0.2, 0.8, invert=False)
            results['tone_clarity_score'] = clarity
        
        return results
    
    def _analyze_timbre_control(self, perf_features: Dict) -> Dict:
        """Analyze timbre control and consistency"""
        results = {}
        
        # MFCC variance (timbre consistency)
        mfcc = perf_features.get('mfcc_features', [])
        if mfcc and len(mfcc) > 0:
            mfcc_array = np.array(mfcc)
            # Compute variance across time for each MFCC coefficient
            if len(mfcc_array.shape) == 2:
                mfcc_var = np.mean(np.var(mfcc_array, axis=0))
                results['mfcc_variance'] = float(mfcc_var)
        
        # Spectral flux (tone stability)
        spectral_centroid = perf_features.get('spectral_centroid', [])
        if spectral_centroid and len(spectral_centroid) > 1:
            flux = np.mean(np.abs(np.diff(spectral_centroid)))
            results['spectral_flux_mean'] = float(flux)
        
        # Dynamic range
        rms = perf_features.get('rms_energy', [])
        if rms:
            dynamic_range = compute_dynamic_range(rms)
            if dynamic_range:
                results['dynamic_range_db'] = dynamic_range
        
        # Timbre matching score (placeholder - would need score markings)
        # For now, use spectral consistency as proxy
        if spectral_centroid:
            consistency = compute_spectral_stability(spectral_centroid)
            if consistency:
                # Lower variance = better consistency
                # Typical good CV: < 0.15, poor: > 0.40
                matching_score = normalize_to_percent(consistency, 0.0, 0.40, invert=True)
                results['timbre_matching_score'] = matching_score
        
        return results
    
    def _compute_intonation_grade(self, results: Dict) -> Dict:
        """Compute overall intonation grade"""
        pitch_match = results['pitch_accuracy'].get('pitch_match_rate')
        
        if pitch_match is None:
            return {
                'overall_score': None,
                'interpretation': 'unknown'
            }
        
        # Interpret pitch match rate
        if pitch_match >= 95:
            interpretation = 'excellent'
        elif pitch_match >= 85:
            interpretation = 'good'
        elif pitch_match >= 70:
            interpretation = 'fair'
        else:
            interpretation = 'poor'
        
        return {
            'overall_score': pitch_match,
            'interpretation': interpretation
        }
    
    def _compute_overall_score(self, results: Dict) -> float:
        """Compute overall sound quality score (0-100)"""
        scores = []
        weights = []
        
        # Pitch accuracy (50% weight within this dimension)
        if results['pitch_accuracy'].get('pitch_match_rate') is not None:
            scores.append(results['pitch_accuracy']['pitch_match_rate'])
            weights.append(0.50)
        
        # Tone quality (30% weight)
        if results['tone_quality'].get('tone_clarity_score') is not None:
            scores.append(results['tone_quality']['tone_clarity_score'])
            weights.append(0.30)
        
        # Timbre control (20% weight)
        if results['timbre_control'].get('timbre_matching_score') is not None:
            scores.append(results['timbre_control']['timbre_matching_score'])
            weights.append(0.20)
        
        if not scores:
            return 0.0
        
        # Weighted average
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return float(weighted_sum / total_weight)
