#!/usr/bin/env python3
"""
Scoring Functions - Convert Raw Metrics to 0-100 Scores
=======================================================

Converts raw grading metrics from Block 2 into normalized 0-100 scores
using research-based thresholds and performance standards.

Based on:
- PQG-A2SA grading rubric
- Music performance assessment literature
- Empirical thresholds from research
"""

import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple


class ScoringFunctions:
    """Convert raw metrics to 0-100 dimension scores"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    # ========================================================================
    # DIMENSION 1: RHYTHM & TEMPO (30% weight)
    # ========================================================================
    
    def score_rhythm_tempo(self, metrics: Dict) -> Dict[str, Any]:
        """
        Score Rhythm & Tempo Mastery (0-100)
        
        Components:
        - Onset timing accuracy (40%)
        - Rhythmic precision (IOI correlation) (30%)
        - Tempo stability (30%)
        
        Args:
            metrics: Raw rhythm_tempo metrics from Block 2
            
        Returns:
            Scored dimension with overall score and interpretation
        """
        self.logger.info("  Scoring Rhythm & Tempo...")
        
        scores = {
            'onset_accuracy_score': 0.0,
            'rhythmic_precision_score': 0.0,
            'tempo_stability_score': 0.0,
            'dimension_score': 0.0,
            'interpretation': 'Unknown',
            'raw_metrics': metrics
        }
        
        # 1. Onset Accuracy Score (40%)
        mean_onset_error = metrics.get('mean_onset_error_ms', float('inf'))
        
        if mean_onset_error <= 20:
            onset_score = 100
        elif mean_onset_error <= 50:
            # Linear interpolation: 20ms=100, 50ms=70
            onset_score = 100 - ((mean_onset_error - 20) / 30) * 30
        elif mean_onset_error <= 100:
            # Linear interpolation: 50ms=70, 100ms=40
            onset_score = 70 - ((mean_onset_error - 50) / 50) * 30
        elif mean_onset_error <= 200:
            # Linear interpolation: 100ms=40, 200ms=0
            onset_score = 40 - ((mean_onset_error - 100) / 100) * 40
        else:
            onset_score = 0
        
        scores['onset_accuracy_score'] = max(0, min(100, onset_score))
        
        # 2. Rhythmic Precision Score (30%) - IOI Correlation
        ioi_correlation = metrics.get('ioi_correlation', 0.0)
        
        if ioi_correlation >= 0.95:
            rhythmic_score = 100
        elif ioi_correlation >= 0.85:
            # Linear: 0.95=100, 0.85=80
            rhythmic_score = 80 + ((ioi_correlation - 0.85) / 0.10) * 20
        elif ioi_correlation >= 0.70:
            # Linear: 0.85=80, 0.70=50
            rhythmic_score = 50 + ((ioi_correlation - 0.70) / 0.15) * 30
        elif ioi_correlation >= 0.50:
            # Linear: 0.70=50, 0.50=20
            rhythmic_score = 20 + ((ioi_correlation - 0.50) / 0.20) * 30
        else:
            # Below 0.50 is very poor
            rhythmic_score = max(0, ioi_correlation * 40)
        
        scores['rhythmic_precision_score'] = max(0, min(100, rhythmic_score))
        
        # 3. Tempo Stability Score (30%) - Coefficient of Variation
        tempo_cv = metrics.get('tempo_cv_percent', float('inf'))
        
        if tempo_cv <= 5:
            tempo_score = 100
        elif tempo_cv <= 10:
            # Linear: 5%=100, 10%=75
            tempo_score = 100 - ((tempo_cv - 5) / 5) * 25
        elif tempo_cv <= 20:
            # Linear: 10%=75, 20%=40
            tempo_score = 75 - ((tempo_cv - 10) / 10) * 35
        elif tempo_cv <= 40:
            # Linear: 20%=40, 40%=0
            tempo_score = 40 - ((tempo_cv - 20) / 20) * 40
        else:
            tempo_score = 0
        
        scores['tempo_stability_score'] = max(0, min(100, tempo_score))
        
        # 4. Overall Dimension Score (weighted average)
        scores['dimension_score'] = (
            scores['onset_accuracy_score'] * 0.40 +
            scores['rhythmic_precision_score'] * 0.30 +
            scores['tempo_stability_score'] * 0.30
        )
        
        # 5. Interpretation
        scores['interpretation'] = self._interpret_score(scores['dimension_score'])
        
        self.logger.info(f"    Onset: {scores['onset_accuracy_score']:.1f}, "
                        f"Rhythmic: {scores['rhythmic_precision_score']:.1f}, "
                        f"Tempo: {scores['tempo_stability_score']:.1f} "
                        f"→ Overall: {scores['dimension_score']:.1f} ({scores['interpretation']})")
        
        return scores
    
    # ========================================================================
    # DIMENSION 2: SOUND QUALITY (20% weight)
    # ========================================================================
    
    def score_sound_quality(self, metrics: Dict) -> Dict[str, Any]:
        """
        Score Sound Quality (0-100)
        
        Components:
        - Pitch accuracy at 50 cents (60%)
        - Pitch accuracy at 25 cents (40%)
        
        Args:
            metrics: Raw sound_quality metrics from Block 2
            
        Returns:
            Scored dimension with overall score and interpretation
        """
        self.logger.info("  Scoring Sound Quality...")
        
        scores = {
            'pitch_accuracy_50c_score': 0.0,
            'pitch_accuracy_25c_score': 0.0,
            'dimension_score': 0.0,
            'interpretation': 'Unknown',
            'raw_metrics': metrics
        }
        
        # 1. Pitch Accuracy at 50 cents (60%)
        pitch_50c = metrics.get('pitch_accuracy_50c_percent', 0.0)
        
        if pitch_50c >= 98:
            pitch_50c_score = 100
        elif pitch_50c >= 95:
            # Linear: 98%=100, 95%=90
            pitch_50c_score = 90 + ((pitch_50c - 95) / 3) * 10
        elif pitch_50c >= 90:
            # Linear: 95%=90, 90%=75
            pitch_50c_score = 75 + ((pitch_50c - 90) / 5) * 15
        elif pitch_50c >= 80:
            # Linear: 90%=75, 80%=50
            pitch_50c_score = 50 + ((pitch_50c - 80) / 10) * 25
        elif pitch_50c >= 60:
            # Linear: 80%=50, 60%=20
            pitch_50c_score = 20 + ((pitch_50c - 60) / 20) * 30
        else:
            # Below 60% is very poor
            pitch_50c_score = pitch_50c / 3
        
        scores['pitch_accuracy_50c_score'] = max(0, min(100, pitch_50c_score))
        
        # 2. Pitch Accuracy at 25 cents (40%) - stricter threshold
        pitch_25c = metrics.get('pitch_accuracy_25c_percent', 0.0)
        
        if pitch_25c >= 95:
            pitch_25c_score = 100
        elif pitch_25c >= 90:
            # Linear: 95%=100, 90%=90
            pitch_25c_score = 90 + ((pitch_25c - 90) / 5) * 10
        elif pitch_25c >= 80:
            # Linear: 90%=90, 80%=70
            pitch_25c_score = 70 + ((pitch_25c - 80) / 10) * 20
        elif pitch_25c >= 60:
            # Linear: 80%=70, 60%=40
            pitch_25c_score = 40 + ((pitch_25c - 60) / 20) * 30
        else:
            # Below 60%
            pitch_25c_score = pitch_25c / 1.5
        
        scores['pitch_accuracy_25c_score'] = max(0, min(100, pitch_25c_score))
        
        # 3. Overall Dimension Score
        scores['dimension_score'] = (
            scores['pitch_accuracy_50c_score'] * 0.60 +
            scores['pitch_accuracy_25c_score'] * 0.40
        )
        
        # 4. Interpretation
        scores['interpretation'] = self._interpret_score(scores['dimension_score'])
        
        self.logger.info(f"    Pitch@50c: {scores['pitch_accuracy_50c_score']:.1f}, "
                        f"Pitch@25c: {scores['pitch_accuracy_25c_score']:.1f} "
                        f"→ Overall: {scores['dimension_score']:.1f} ({scores['interpretation']})")
        
        return scores
    
    # ========================================================================
    # DIMENSION 3: TECHNICAL VIRTUOSITY (20% weight)
    # ========================================================================
    
    def score_technical_virtuosity(self, metrics: Dict) -> Dict[str, Any]:
        """
        Score Technical Virtuosity (0-100)
        
        Components:
        - Note accuracy (50%)
        - Fluency (30%)
        - Difficulty mastery (20%)
        
        Args:
            metrics: Raw technical_virtuosity metrics from Block 2
            
        Returns:
            Scored dimension with overall score and interpretation
        """
        self.logger.info("  Scoring Technical Virtuosity...")
        
        scores = {
            'note_accuracy_score': 0.0,
            'fluency_score': 0.0,
            'difficulty_mastery_score': 0.0,
            'dimension_score': 0.0,
            'interpretation': 'Unknown',
            'raw_metrics': metrics
        }
        
        # 1. Note Accuracy Score (50%)
        note_accuracy = metrics.get('note_accuracy_percent', 0.0)
        
        if note_accuracy >= 98:
            note_score = 100
        elif note_accuracy >= 95:
            note_score = 90 + ((note_accuracy - 95) / 3) * 10
        elif note_accuracy >= 90:
            note_score = 75 + ((note_accuracy - 90) / 5) * 15
        elif note_accuracy >= 80:
            note_score = 50 + ((note_accuracy - 80) / 10) * 25
        else:
            note_score = note_accuracy / 1.6
        
        scores['note_accuracy_score'] = max(0, min(100, note_score))
        
        # 2. Fluency Score (30%) - IOI Coefficient of Variation (lower is better)
        fluency_cv = metrics.get('fluency_ioi_cv_percent', float('inf'))
        
        if fluency_cv <= 10:
            fluency_score = 100
        elif fluency_cv <= 20:
            fluency_score = 90 - ((fluency_cv - 10) / 10) * 15
        elif fluency_cv <= 40:
            fluency_score = 75 - ((fluency_cv - 20) / 20) * 35
        elif fluency_cv <= 60:
            fluency_score = 40 - ((fluency_cv - 40) / 20) * 40
        else:
            fluency_score = 0
        
        scores['fluency_score'] = max(0, min(100, fluency_score))
        
        # 3. Difficulty Mastery Score (20%)
        difficulty_data = metrics.get('difficulty_mastery', {})
        
        if isinstance(difficulty_data, dict):
            difficulty_ratio = difficulty_data.get('difficulty_ratio', 2.0)
            
            # Lower ratio is better (difficult passages handled well)
            if difficulty_ratio <= 1.0:
                difficulty_score = 100
            elif difficulty_ratio <= 1.5:
                difficulty_score = 90 - ((difficulty_ratio - 1.0) / 0.5) * 15
            elif difficulty_ratio <= 2.0:
                difficulty_score = 75 - ((difficulty_ratio - 1.5) / 0.5) * 25
            elif difficulty_ratio <= 3.0:
                difficulty_score = 50 - ((difficulty_ratio - 2.0) / 1.0) * 30
            else:
                difficulty_score = max(0, 20 - (difficulty_ratio - 3.0) * 10)
        else:
            difficulty_score = 50  # Default if no data
        
        scores['difficulty_mastery_score'] = max(0, min(100, difficulty_score))
        
        # 4. Overall Dimension Score
        scores['dimension_score'] = (
            scores['note_accuracy_score'] * 0.50 +
            scores['fluency_score'] * 0.30 +
            scores['difficulty_mastery_score'] * 0.20
        )
        
        # 5. Interpretation
        scores['interpretation'] = self._interpret_score(scores['dimension_score'])
        
        self.logger.info(f"    Note Accuracy: {scores['note_accuracy_score']:.1f}, "
                        f"Fluency: {scores['fluency_score']:.1f}, "
                        f"Difficulty: {scores['difficulty_mastery_score']:.1f} "
                        f"→ Overall: {scores['dimension_score']:.1f} ({scores['interpretation']})")
        
        return scores
    
    # ========================================================================
    # DIMENSION 4: PHRASING & DICTION (15% weight)
    # ========================================================================
    
    def score_phrasing_diction(self, metrics: Dict) -> Dict[str, Any]:
        """
        Score Phrasing & Diction (0-100)
        
        Components:
        - Rubato expressiveness (50%)
        - Agogic expression (50%)
        
        Args:
            metrics: Raw phrasing_diction metrics from Block 2
            
        Returns:
            Scored dimension with overall score and interpretation
        """
        self.logger.info("  Scoring Phrasing & Diction...")
        
        scores = {
            'rubato_expressiveness_score': 0.0,
            'agogic_expression_score': 0.0,
            'dimension_score': 0.0,
            'interpretation': 'Unknown',
            'raw_metrics': metrics
        }
        
        # 1. Rubato Expressiveness Score (50%)
        rubato_std = metrics.get('rubato_variation_std', 0.0)
        
        # Moderate variation is good (0.1-0.3 optimal range)
        if 0.10 <= rubato_std <= 0.30:
            rubato_score = 100
        elif 0.05 <= rubato_std < 0.10:
            # Too little variation
            rubato_score = 70 + ((rubato_std - 0.05) / 0.05) * 30
        elif 0.30 < rubato_std <= 0.50:
            # Slightly excessive
            rubato_score = 100 - ((rubato_std - 0.30) / 0.20) * 25
        elif 0.50 < rubato_std <= 0.80:
            # Excessive variation
            rubato_score = 75 - ((rubato_std - 0.50) / 0.30) * 40
        elif rubato_std < 0.05:
            # Very mechanical
            rubato_score = rubato_std * 1400  # 0.05 → 70
        else:
            # Extremely erratic
            rubato_score = max(0, 35 - (rubato_std - 0.80) * 50)
        
        scores['rubato_expressiveness_score'] = max(0, min(100, rubato_score))
        
        # 2. Agogic Expression Score (50%)
        agogic_mean = metrics.get('agogic_expression_mean_percent', 0.0)
        
        # Good agogic expression: 3-10% tempo change at boundaries
        if 3 <= agogic_mean <= 10:
            agogic_score = 100
        elif 1 <= agogic_mean < 3:
            # Too subtle
            agogic_score = 60 + ((agogic_mean - 1) / 2) * 40
        elif 10 < agogic_mean <= 15:
            # Slightly exaggerated
            agogic_score = 100 - ((agogic_mean - 10) / 5) * 20
        elif 15 < agogic_mean <= 25:
            # Very exaggerated
            agogic_score = 80 - ((agogic_mean - 15) / 10) * 40
        elif agogic_mean < 1:
            # Almost no expression
            agogic_score = agogic_mean * 60
        else:
            # Extreme
            agogic_score = max(0, 40 - (agogic_mean - 25) * 2)
        
        scores['agogic_expression_score'] = max(0, min(100, agogic_score))
        
        # 3. Overall Dimension Score
        scores['dimension_score'] = (
            scores['rubato_expressiveness_score'] * 0.50 +
            scores['agogic_expression_score'] * 0.50
        )
        
        # 4. Interpretation
        scores['interpretation'] = self._interpret_score(scores['dimension_score'])
        
        self.logger.info(f"    Rubato: {scores['rubato_expressiveness_score']:.1f}, "
                        f"Agogic: {scores['agogic_expression_score']:.1f} "
                        f"→ Overall: {scores['dimension_score']:.1f} ({scores['interpretation']})")
        
        return scores
    
    # ========================================================================
    # DIMENSION 5: COMMUNICATIVENESS (15% weight)
    # ========================================================================
    
    def score_communicativeness(self, metrics: Dict) -> Dict[str, Any]:
        """
        Score Communicativeness (0-100)
        
        Components:
        - Structural coherence (60%)
        - Climax placement (40%)
        
        Args:
            metrics: Raw communicativeness metrics from Block 2
            
        Returns:
            Scored dimension with overall score and interpretation
        """
        self.logger.info("  Scoring Communicativeness...")
        
        scores = {
            'structural_coherence_score': 0.0,
            'climax_placement_score': 0.0,
            'dimension_score': 0.0,
            'interpretation': 'Unknown',
            'raw_metrics': metrics
        }
        
        # 1. Structural Coherence Score (60%)
        section_consistency = metrics.get('section_tempo_consistency', [])
        
        if section_consistency and len(section_consistency) > 0:
            # Average CV across sections (lower is more coherent)
            avg_section_cv = np.mean(section_consistency)
            
            if avg_section_cv <= 8:
                coherence_score = 100
            elif avg_section_cv <= 15:
                coherence_score = 90 - ((avg_section_cv - 8) / 7) * 15
            elif avg_section_cv <= 25:
                coherence_score = 75 - ((avg_section_cv - 15) / 10) * 30
            else:
                coherence_score = max(0, 45 - (avg_section_cv - 25))
        else:
            coherence_score = 50  # Default if no data
        
        scores['structural_coherence_score'] = max(0, min(100, coherence_score))
        
        # 2. Climax Placement Score (40%)
        climax_position = metrics.get('climax_position_percent', 0.0)
        
        # Ideal climax: 60-75% through the piece (golden ratio ~ 61.8%)
        if 60 <= climax_position <= 75:
            climax_score = 100
        elif 50 <= climax_position < 60:
            climax_score = 85 + ((climax_position - 50) / 10) * 15
        elif 75 < climax_position <= 85:
            climax_score = 100 - ((climax_position - 75) / 10) * 15
        elif 40 <= climax_position < 50:
            climax_score = 65 + ((climax_position - 40) / 10) * 20
        elif 85 < climax_position <= 95:
            climax_score = 85 - ((climax_position - 85) / 10) * 20
        elif climax_position < 40:
            # Too early
            climax_score = climax_position * 1.625  # 40% → 65
        else:
            # Too late
            climax_score = max(0, 65 - (climax_position - 95) * 3)
        
        scores['climax_placement_score'] = max(0, min(100, climax_score))
        
        # 3. Overall Dimension Score
        scores['dimension_score'] = (
            scores['structural_coherence_score'] * 0.60 +
            scores['climax_placement_score'] * 0.40
        )
        
        # 4. Interpretation
        scores['interpretation'] = self._interpret_score(scores['dimension_score'])
        
        self.logger.info(f"    Coherence: {scores['structural_coherence_score']:.1f}, "
                        f"Climax: {scores['climax_placement_score']:.1f} "
                        f"→ Overall: {scores['dimension_score']:.1f} ({scores['interpretation']})")
        
        return scores
    
    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================
    
    def _interpret_score(self, score: float) -> str:
        """
        Convert numerical score to interpretation label
        
        Args:
            score: Score from 0-100
            
        Returns:
            Interpretation string
        """
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Very Poor"
    
    def score_all_dimensions(self, grading_metrics: Dict) -> Dict[str, Any]:
        """
        Score all 5 grading dimensions
        
        Args:
            grading_metrics: Complete grading metrics from Block 2
            
        Returns:
            Dictionary with all scored dimensions
        """
        self.logger.info("Scoring all dimensions...")
        
        scored_dimensions = {}
        
        # Score each dimension
        if 'rhythm_tempo' in grading_metrics:
            scored_dimensions['rhythm_tempo'] = self.score_rhythm_tempo(
                grading_metrics['rhythm_tempo']
            )
        
        if 'sound_quality' in grading_metrics:
            scored_dimensions['sound_quality'] = self.score_sound_quality(
                grading_metrics['sound_quality']
            )
        
        if 'technical_virtuosity' in grading_metrics:
            scored_dimensions['technical_virtuosity'] = self.score_technical_virtuosity(
                grading_metrics['technical_virtuosity']
            )
        
        if 'phrasing_diction' in grading_metrics:
            scored_dimensions['phrasing_diction'] = self.score_phrasing_diction(
                grading_metrics['phrasing_diction']
            )
        
        if 'communicativeness' in grading_metrics:
            scored_dimensions['communicativeness'] = self.score_communicativeness(
                grading_metrics['communicativeness']
            )
        
        self.logger.info(f"✓ Scored {len(scored_dimensions)} dimensions")
        
        return scored_dimensions


def main():
    """Test scoring functions"""
    import json
    import sys
    
    # Example metrics for testing
    test_metrics = {
        'rhythm_tempo': {
            'mean_onset_error_ms': 35.0,
            'onset_std_ms': 28.0,
            'ioi_correlation': 0.88,
            'tempo_cv_percent': 8.5
        },
        'sound_quality': {
            'pitch_accuracy_50c_percent': 96.5,
            'pitch_accuracy_25c_percent': 87.3
        },
        'technical_virtuosity': {
            'note_accuracy_percent': 94.2,
            'fluency_ioi_cv_percent': 15.0,
            'difficulty_mastery': {
                'difficulty_ratio': 1.8
            }
        },
        'phrasing_diction': {
            'rubato_variation_std': 0.18,
            'agogic_expression_mean_percent': 6.5
        },
        'communicativeness': {
            'section_tempo_consistency': [12.0, 10.5, 11.2, 9.8],
            'climax_position_percent': 67.5
        }
    }
    
    scorer = ScoringFunctions()
    scored = scorer.score_all_dimensions(test_metrics)
    
    print("\n" + "=" * 70)
    print("SCORING RESULTS")
    print("=" * 70)
    
    for dim_name, dim_scores in scored.items():
        print(f"\n{dim_name.upper()}:")
        print(f"  Score: {dim_scores['dimension_score']:.1f}/100")
        print(f"  Interpretation: {dim_scores['interpretation']}")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
