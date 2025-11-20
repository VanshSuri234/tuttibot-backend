#!/usr/bin/env python3
"""
Communicativeness Analyzer - Dimension 5 (15% weight)
=====================================================

Analyzes expressive impact and interpretive coherence.

Metrics computed:
- Emotional engagement
- Structural coherence
- Interpretive consistency
- Musical narrative
- Overall impact
"""

import numpy as np
import logging
from typing import Dict, Any, Optional
from ..data_collector import InferenceCoreInputs
from ..utils.metric_utils import normalize_to_percent, interpret_score


class CommunicativenessAnalyzer:
    """Analyzes Communicativeness (15%)"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze(self, inputs: InferenceCoreInputs) -> Dict[str, Any]:
        """Perform complete communicativeness analysis"""
        self.logger.info("📊 Analyzing Communicativeness...")
        
        results = {
            'emotional_engagement': {},
            'structural_coherence': {},
            'interpretive_consistency': {},
            'musical_narrative': {},
            'overall_impact': {},
            'overall_score': None,
            'interpretation': None
        }
        
        # 1. Emotional Engagement
        results['emotional_engagement'] = self._analyze_emotional_engagement(inputs)
        
        # 2. Structural Coherence
        results['structural_coherence'] = self._analyze_structural_coherence(inputs)
        self.logger.info(f"  ✓ Structural coherence analyzed")
        
        # 3. Interpretive Consistency
        results['interpretive_consistency'] = self._analyze_interpretive_consistency(inputs)
        
        # 4. Musical Narrative
        results['musical_narrative'] = self._analyze_musical_narrative(inputs)
        
        # 5. Overall Impact
        results['overall_impact'] = self._synthesize_overall_impact(results)
        
        # Overall score
        results['overall_score'] = self._compute_overall_score(results)
        results['interpretation'] = interpret_score(
            results['overall_score'],
            {'exceptional': (90, 100), 'strong': (75, 90), 'adequate': (60, 75), 'weak': (0, 60)}
        )
        
        self.logger.info(f"  → Overall Communicativeness: {results['overall_score']:.1f}/100")
        
        return results
    
    def _analyze_emotional_engagement(self, inputs: InferenceCoreInputs) -> Dict:
        """Analyze emotional expression breadth"""
        results = {}
        
        if inputs.performance_features:
            # Dynamic expression range
            rms = inputs.performance_features.get('rms_energy', [])
            if rms:
                rms_array = np.array(rms)
                rms_range = np.max(rms_array) - np.min(rms_array[rms_array > 0])
                results['dynamic_expression_range'] = normalize_to_percent(rms_range, 0, 1, invert=False)
            
            # Timbral variation (MFCC diversity)
            mfcc = inputs.performance_features.get('mfcc_features', [])
            if mfcc and len(mfcc) > 0:
                mfcc_array = np.array(mfcc)
                if len(mfcc_array.shape) == 2:
                    mfcc_var = np.mean(np.var(mfcc_array, axis=0))
                    results['timbral_variation'] = normalize_to_percent(mfcc_var, 0, 10, invert=False)
            
            # Emotional commitment score (composite)
            if 'dynamic_expression_range' in results or 'timbral_variation' in results:
                scores = [v for v in results.values() if isinstance(v, (int, float))]
                results['emotional_commitment_score'] = np.mean(scores) if scores else 70.0
        
        return results
    
    def _analyze_structural_coherence(self, inputs: InferenceCoreInputs) -> Dict:
        """Analyze structural awareness"""
        results = {}
        
        # Use alignment quality as proxy for structural understanding
        if inputs.alignment_results and 'metrics' in inputs.alignment_results:
            metrics = inputs.alignment_results['metrics']
            
            # Good alignment suggests structural awareness
            if 'mean_similarity' in metrics:
                similarity = metrics['mean_similarity']
                results['formal_awareness_score'] = normalize_to_percent(similarity, 0.5, 1.0, invert=False)
        
        # Section differentiation from segmentation
        if inputs.audio_segments and 'audio_segments' in inputs.audio_segments:
            segments = inputs.audio_segments['audio_segments']
            if len(segments) > 2:
                # Energy variance between segments suggests differentiation
                energies = [s.get('rms_energy', s.get('total_energy', 0)) for s in segments]
                if energies:
                    energy_cv = np.std(energies) / (np.mean(energies) + 1e-10)
                    results['section_differentiation'] = normalize_to_percent(energy_cv, 0, 0.5, invert=False)
        
        return results
    
    def _analyze_interpretive_consistency(self, inputs: InferenceCoreInputs) -> Dict:
        """Analyze consistency of interpretive approach"""
        results = {}
        
        # Tempo philosophy coherence
        if inputs.performance_features and 'tempo_bpm' in inputs.performance_features:
            tempo = inputs.performance_features['tempo_bpm']
            if isinstance(tempo, list) and len(tempo) > 1:
                tempo_array = np.array(tempo)
                # Smooth tempo curve = coherent approach
                tempo_smoothness = 1.0 / (1.0 + np.std(np.diff(tempo_array)))
                results['tempo_philosophy_coherence'] = normalize_to_percent(tempo_smoothness, 0, 1, invert=False)
        
        # Dynamic strategy coherence
        if inputs.performance_features and 'rms_energy' in inputs.performance_features:
            rms = np.array(inputs.performance_features['rms_energy'])
            if len(rms) > 1:
                # Smooth dynamic curve = coherent strategy
                rms_smoothness = 1.0 / (1.0 + np.std(np.diff(rms)))
                results['dynamic_strategy_coherence'] = normalize_to_percent(rms_smoothness, 0, 1, invert=False)
        
        # Overall interpretive identity
        if results:
            scores = [v for v in results.values() if isinstance(v, (int, float))]
            results['interpretive_identity'] = np.mean(scores) if scores else 75.0
        
        return results
    
    def _analyze_musical_narrative(self, inputs: InferenceCoreInputs) -> Dict:
        """Analyze narrative arc and storytelling"""
        results = {}
        
        # Dramatic trajectory (energy/intensity curve)
        if inputs.performance_features and 'rms_energy' in inputs.performance_features:
            rms = np.array(inputs.performance_features['rms_energy'])
            if len(rms) > 10:
                # Fit polynomial to see if there's an arc
                x = np.linspace(0, 1, len(rms))
                p = np.polyfit(x, rms, 2)
                
                # Parabolic curve suggests intentional arc
                curve_strength = abs(p[0])
                results['dramatic_trajectory'] = normalize_to_percent(curve_strength, 0, 0.5, invert=False)
        
        # Climax building (where is peak energy?)
        if inputs.performance_features and 'rms_energy' in inputs.performance_features:
            rms = np.array(inputs.performance_features['rms_energy'])
            if len(rms) > 0:
                peak_position = np.argmax(rms) / len(rms)
                # Climax around 2/3 to 3/4 is typical
                climax_placement = 100 - abs(peak_position - 0.7) * 200
                results['climax_building'] = max(0, climax_placement)
        
        # Communicative clarity (composite)
        if results:
            scores = [v for v in results.values() if isinstance(v, (int, float))]
            results['communicative_clarity'] = np.mean(scores) if scores else 70.0
        
        return results
    
    def _synthesize_overall_impact(self, results: Dict) -> Dict:
        """Synthesize overall performance impact"""
        impact = {}
        
        # Performance conviction (from emotional engagement)
        emotional_score = results['emotional_engagement'].get('emotional_commitment_score', 70)
        impact['performance_conviction'] = emotional_score
        
        # Artistic maturity (from structural coherence)
        structural_score = results['structural_coherence'].get('formal_awareness_score', 70)
        impact['artistic_maturity'] = structural_score
        
        # Audience engagement potential (from narrative)
        narrative_score = results['musical_narrative'].get('communicative_clarity', 70)
        impact['audience_engagement_potential'] = narrative_score
        
        # Interpretive originality (from consistency)
        consistency_score = results['interpretive_consistency'].get('interpretive_identity', 75)
        impact['interpretive_originality'] = consistency_score
        
        return impact
    
    def _compute_overall_score(self, results: Dict) -> float:
        """Compute overall communicativeness score"""
        scores = []
        weights = []
        
        # Emotional engagement (30%)
        if results['emotional_engagement'].get('emotional_commitment_score') is not None:
            scores.append(results['emotional_engagement']['emotional_commitment_score'])
            weights.append(0.30)
        
        # Structural coherence (25%)
        if results['structural_coherence'].get('formal_awareness_score') is not None:
            scores.append(results['structural_coherence']['formal_awareness_score'])
            weights.append(0.25)
        
        # Interpretive consistency (20%)
        if results['interpretive_consistency'].get('interpretive_identity') is not None:
            scores.append(results['interpretive_consistency']['interpretive_identity'])
            weights.append(0.20)
        
        # Musical narrative (25%)
        if results['musical_narrative'].get('communicative_clarity') is not None:
            scores.append(results['musical_narrative']['communicative_clarity'])
            weights.append(0.25)
        
        if not scores:
            return 70.0  # Default moderate-good score
        
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return float(weighted_sum / total_weight) if total_weight > 0 else 70.0
