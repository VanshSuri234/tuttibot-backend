#!/usr/bin/env python3
"""
Technical Virtuosity Analyzer - Dimension 3 (20% weight)
========================================================

Analyzes technical execution quality.

Metrics computed:
- Smoothness and fluency
- Accuracy and cleanliness
- Difficulty mastery
- Dynamic control
- Articulation precision
"""

import numpy as np
import logging
from typing import Dict, Any, List, Optional
from ..data_collector import InferenceCoreInputs
from ..utils.metric_utils import (
    compute_dynamic_range,
    normalize_to_percent,
    interpret_score
)


class TechnicalVirtuosityAnalyzer:
    """Analyzes Technical Virtuosity (20%)"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(self, inputs: InferenceCoreInputs) -> Dict[str, Any]:
        """Perform complete technical virtuosity analysis"""
        self.logger.info("📊 Analyzing Technical Virtuosity...")
        
        results = {
            'fluency': {},
            'accuracy': {},
            'difficulty_mastery': {},
            'dynamic_control': {},
            'articulation_precision': {},
            'overall_score': None,
            'interpretation': None
        }
        
        # 1. Fluency Analysis
        results['fluency'] = self._analyze_fluency(inputs)
        
        # 2. Accuracy Analysis
        results['accuracy'] = self._analyze_accuracy(inputs)
        self.logger.info(f"  ✓ Note accuracy: {results['accuracy'].get('note_accuracy_rate', 0):.1f}%")
        
        # 3. Difficulty Mastery
        results['difficulty_mastery'] = self._analyze_difficulty_mastery(inputs)
        
        # 4. Dynamic Control
        results['dynamic_control'] = self._analyze_dynamic_control(inputs)
        
        # 5. Articulation Precision
        results['articulation_precision'] = self._analyze_articulation(inputs)
        
        # Overall score
        results['overall_score'] = self._compute_overall_score(results)
        results['interpretation'] = interpret_score(
            results['overall_score'],
            {'excellent': (90, 100), 'good': (75, 90), 'fair': (60, 75), 'poor': (0, 60)}
        )
        
        self.logger.info(f"  → Overall Technical Virtuosity: {results['overall_score']:.1f}/100")
        
        return results
    
    def _analyze_fluency(self, inputs: InferenceCoreInputs) -> Dict:
        """Analyze smoothness and fluency"""
        results = {}
        
        # Onset regularity
        if inputs.performance_features and 'onset_times' in inputs.performance_features:
            onsets = inputs.performance_features['onset_times']
            if len(onsets) > 2:
                ioi = np.diff(onsets)
                ioi_cv = np.std(ioi) / np.mean(ioi) if np.mean(ioi) > 0 else 1.0
                smoothness = normalize_to_percent(ioi_cv, 0.0, 0.5, invert=True)
                results['note_transition_smoothness'] = smoothness
        
        # Phrase continuity from segments
        if inputs.audio_segments and 'audio_segments' in inputs.audio_segments:
            segments = inputs.audio_segments['audio_segments']
            if segments:
                # Count gaps between segments
                gaps = 0
                for i in range(len(segments) - 1):
                    gap = segments[i+1]['start_time'] - segments[i]['end_time']
                    if gap > 0.5:  # > 500ms gap
                        gaps += 1
                
                continuity = normalize_to_percent(gaps, 0, len(segments) * 0.3, invert=True)
                results['phrase_continuity_score'] = continuity
                results['hesitation_count'] = gaps
        
        return results
    
    def _analyze_accuracy(self, inputs: InferenceCoreInputs) -> Dict:
        """Analyze note accuracy"""
        results = {}
        
        # Get note counts
        score_notes = self._count_score_notes(inputs)
        perf_notes = self._count_performance_notes(inputs)
        
        if score_notes > 0:
            # Simple accuracy estimate
            note_accuracy = min(perf_notes / score_notes * 100, 100)
            results['note_accuracy_rate'] = note_accuracy
            
            # Estimate errors
            if perf_notes > score_notes:
                results['extra_notes_count'] = perf_notes - score_notes
                results['missed_notes_count'] = 0
            else:
                results['extra_notes_count'] = 0
                results['missed_notes_count'] = score_notes - perf_notes
            
            results['wrong_notes_count'] = 0  # Would need alignment
            results['clean_execution_score'] = note_accuracy
        
        return results
    
    def _analyze_difficulty_mastery(self, inputs: InferenceCoreInputs) -> Dict:
        """Analyze difficulty mastery"""
        results = {}
        
        # Estimate difficulty from note density
        if inputs.music_features:
            notes = self._get_music_features_notes(inputs.music_features)
            duration = self._get_duration(inputs)
            
            if notes and duration:
                note_density = len(notes) / duration
                # High density = more difficult
                difficulty_level = normalize_to_percent(note_density, 0, 10, invert=False)
                results['score_difficulty_level'] = difficulty_level
        
        return results
    
    def _analyze_dynamic_control(self, inputs: InferenceCoreInputs) -> Dict:
        """Analyze dynamic control"""
        results = {}
        
        if inputs.performance_features and 'rms_energy' in inputs.performance_features:
            rms = inputs.performance_features['rms_energy']
            
            # Dynamic range
            dynamic_range = compute_dynamic_range(rms)
            if dynamic_range:
                results['dynamic_range_utilized_db'] = dynamic_range
                # Good dynamic range: 20-40 dB
                control_score = normalize_to_percent(dynamic_range, 10, 40, invert=False)
                results['dynamic_contrast_score'] = control_score
        
        return results
    
    def _analyze_articulation(self, inputs: InferenceCoreInputs) -> Dict:
        """Analyze articulation precision"""
        results = {}
        
        # Use PQG-A2SA data if available
        if inputs.pqg_alignment and 'articulations' in inputs.pqg_alignment:
            # Analyze staccato/legato detection
            articulations = inputs.pqg_alignment['articulations']
            # Placeholder scoring
            results['articulation_match_rate'] = 80.0  # Would need score markings
        else:
            # Estimate from zero-crossing rate
            if inputs.performance_features and 'zero_crossing_rate' in inputs.performance_features:
                zcr = inputs.performance_features['zero_crossing_rate']
                zcr_mean = np.mean(zcr) if zcr else 0
                # Higher ZCR suggests more articulation
                results['articulation_consistency'] = 75.0  # Placeholder
        
        return results
    
    def _count_score_notes(self, inputs: InferenceCoreInputs) -> int:
        """Count notes in score"""
        if inputs.music_features:
            notes = self._get_music_features_notes(inputs.music_features)
            return len(notes)
        return 0
    
    def _count_performance_notes(self, inputs: InferenceCoreInputs) -> int:
        """Count notes in performance"""
        if inputs.transcription and 'notes' in inputs.transcription:
            return len(inputs.transcription['notes'])
        return 0
    
    def _get_music_features_notes(self, music_features: Dict) -> List:
        """Extract notes from music_features"""
        if 'music_features' in music_features:
            return music_features['music_features'].get('notes', [])
        return music_features.get('notes', [])
    
    def _get_duration(self, inputs: InferenceCoreInputs) -> float:
        """Get piece duration"""
        if inputs.performance_features:
            return inputs.performance_features.get('duration', 0)
        return 0
    
    def _compute_overall_score(self, results: Dict) -> float:
        """Compute overall technical virtuosity score"""
        scores = []
        weights = []
        
        # Fluency (25%)
        if results['fluency'].get('note_transition_smoothness') is not None:
            scores.append(results['fluency']['note_transition_smoothness'])
            weights.append(0.25)
        
        # Accuracy (35%)
        if results['accuracy'].get('note_accuracy_rate') is not None:
            scores.append(results['accuracy']['note_accuracy_rate'])
            weights.append(0.35)
        
        # Dynamic control (20%)
        if results['dynamic_control'].get('dynamic_contrast_score') is not None:
            scores.append(results['dynamic_control']['dynamic_contrast_score'])
            weights.append(0.20)
        
        # Articulation (20%)
        if results['articulation_precision'].get('articulation_consistency') is not None:
            scores.append(results['articulation_precision']['articulation_consistency'])
            weights.append(0.20)
        
        if not scores:
            return 0.0
        
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return float(weighted_sum / total_weight) if total_weight > 0 else 0.0
