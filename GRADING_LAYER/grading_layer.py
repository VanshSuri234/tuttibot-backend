#!/usr/bin/env python3
"""
Grading Layer - Final Performance Grade Generation
==================================================

Takes Inference Core output and computes:
1. Final weighted score (0-100)
2. Letter grade (A+, A, A-, B+, etc.)
3. Comprehensive performance report
4. Strengths and weaknesses analysis
5. Specific recommendations

Author: TuttiBot Team
Version: 1.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class GradingLayer:
    """
    Final grading layer that produces performance assessment
    
    Applies PQG-A2SA framework weights:
    - Rhythm & Tempo: 30%
    - Sound Quality: 20%
    - Technical Virtuosity: 20%
    - Phrasing & Diction: 15%
    - Communicativeness: 15%
    """
    
    # PQG-A2SA dimension weights
    DIMENSION_WEIGHTS = {
        'rhythm_tempo': 0.30,
        'sound_quality': 0.20,
        'technical_virtuosity': 0.20,
        'phrasing_diction': 0.15,
        'communicativeness': 0.15
    }
    
    # Letter grade thresholds
    GRADE_THRESHOLDS = {
        'A+': 97,
        'A': 93,
        'A-': 90,
        'B+': 87,
        'B': 83,
        'B-': 80,
        'C+': 77,
        'C': 73,
        'C-': 70,
        'D+': 67,
        'D': 63,
        'D-': 60,
        'F': 0
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize Grading Layer
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or self._setup_logger()
        self.grading_package = None
        self.final_grade = None
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('GradingLayer')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def load_grading_package(self, grading_package_path: Path) -> Dict[str, Any]:
        """
        Load grading package from Inference Core
        
        Args:
            grading_package_path: Path to grading_package_master.json
            
        Returns:
            Loaded grading package dictionary
        """
        self.logger.info(f"Loading grading package from: {grading_package_path}")
        
        if not grading_package_path.exists():
            raise FileNotFoundError(f"Grading package not found: {grading_package_path}")
        
        with open(grading_package_path, 'r') as f:
            self.grading_package = json.load(f)
        
        # Validate structure
        if 'grading_dimensions' not in self.grading_package:
            raise ValueError("Invalid grading package: missing 'grading_dimensions'")
        
        self.logger.info(f"✓ Loaded grading package with {len(self.grading_package['grading_dimensions'])} dimensions")
        
        return self.grading_package
    
    def compute_final_grade(self, grading_package: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Compute final weighted grade from dimension scores
        
        Args:
            grading_package: Optional grading package (uses loaded if not provided)
            
        Returns:
            Final grade dictionary with score, letter grade, and analysis
        """
        if grading_package:
            self.grading_package = grading_package
        
        if not self.grading_package:
            raise ValueError("No grading package loaded. Call load_grading_package() first.")
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("GRADING LAYER - FINAL GRADE COMPUTATION")
        self.logger.info("=" * 80)
        
        dimensions = self.grading_package['grading_dimensions']
        
        # 1. Compute weighted score
        self.logger.info("\n📊 Computing Weighted Score...")
        
        weighted_score = 0.0
        dimension_contributions = {}
        
        for dim_name, weight in self.DIMENSION_WEIGHTS.items():
            if dim_name in dimensions:
                dim_score = dimensions[dim_name].get('dimension_score', 0.0)
                contribution = dim_score * weight
                weighted_score += contribution
                dimension_contributions[dim_name] = {
                    'score': dim_score,
                    'weight': weight,
                    'contribution': contribution,
                    'interpretation': dimensions[dim_name].get('interpretation', 'Unknown')
                }
                
                self.logger.info(f"  {dim_name:.<30} {dim_score:>5.1f} × {weight:.0%} = {contribution:>5.1f}")
            else:
                self.logger.warning(f"  ⚠ Missing dimension: {dim_name}")
        
        self.logger.info(f"  {'─' * 55}")
        self.logger.info(f"  {'FINAL WEIGHTED SCORE':.<30} {weighted_score:>5.1f}/100")
        
        # 2. Analyze strengths and weaknesses
        self.logger.info("\n🔍 Analyzing Performance...")
        
        strengths = self._identify_strengths(dimension_contributions)
        weaknesses = self._identify_weaknesses(dimension_contributions)
        recommendations = self._generate_recommendations(dimension_contributions)
        
        # 3. Create final grade object
        self.final_grade = {
            'overall_score': round(weighted_score, 2),
            'dimension_contributions': dimension_contributions,
            'analysis': {
                'strengths': strengths,
                'weaknesses': weaknesses,
                'recommendations': recommendations
            },
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'grading_framework': 'PQG-A2SA',
                'grading_layer_version': '1.0',
                'source_inference_core': self.grading_package.get('metadata', {})
            }
        }
        
        # 5. Print summary
        self._print_grade_summary()
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("✅ FINAL GRADE COMPUTED")
        self.logger.info("=" * 80 + "\n")
        
        return self.final_grade
    
    def _score_to_letter_grade(self, score: float) -> str:
        """
        Convert numerical score to letter grade
        
        Args:
            score: Score from 0-100
            
        Returns:
            Letter grade string
        """
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return 'F'
    
    def _interpret_letter_grade(self, letter_grade: str) -> str:
        """
        Provide interpretation of letter grade
        
        Args:
            letter_grade: Letter grade string
            
        Returns:
            Human-readable interpretation
        """
        interpretations = {
            'A+': 'Outstanding - Exceptional mastery of all performance aspects',
            'A': 'Excellent - Strong mastery with minor areas for refinement',
            'A-': 'Very Good - Solid performance with few weaknesses',
            'B+': 'Good - Competent performance with some areas needing improvement',
            'B': 'Above Average - Satisfactory with notable areas for development',
            'B-': 'Adequate - Acceptable but several areas need attention',
            'C+': 'Fair - Basic competency with significant room for improvement',
            'C': 'Passing - Meets minimum standards but many areas need work',
            'C-': 'Below Average - Struggles in multiple performance dimensions',
            'D+': 'Poor - Substantial difficulties across most dimensions',
            'D': 'Very Poor - Significant deficiencies in performance',
            'D-': 'Failing - Major problems in nearly all aspects',
            'F': 'Unacceptable - Does not meet minimum performance standards'
        }
        return interpretations.get(letter_grade, 'Unknown grade level')
    
    def _identify_strengths(self, dimension_contributions: Dict) -> List[Dict[str, Any]]:
        """
        Identify performance strengths (scores ≥ 75)
        
        Args:
            dimension_contributions: Dimension scores and contributions
            
        Returns:
            List of strength dictionaries
        """
        strengths = []
        
        for dim_name, data in dimension_contributions.items():
            score = data['score']
            if score >= 75:
                strength = {
                    'dimension': dim_name.replace('_', ' ').title(),
                    'score': score,
                    'interpretation': data['interpretation'],
                    'comment': self._get_strength_comment(dim_name, score)
                }
                strengths.append(strength)
                self.logger.info(f"  ✓ Strength: {strength['dimension']} ({score:.1f}/100)")
        
        if not strengths:
            self.logger.info("  ⚠ No clear strengths identified (no dimension ≥ 75)")
        
        return sorted(strengths, key=lambda x: x['score'], reverse=True)
    
    def _identify_weaknesses(self, dimension_contributions: Dict) -> List[Dict[str, Any]]:
        """
        Identify performance weaknesses (scores < 60)
        
        Args:
            dimension_contributions: Dimension scores and contributions
            
        Returns:
            List of weakness dictionaries
        """
        weaknesses = []
        
        for dim_name, data in dimension_contributions.items():
            score = data['score']
            if score < 60:
                weakness = {
                    'dimension': dim_name.replace('_', ' ').title(),
                    'score': score,
                    'interpretation': data['interpretation'],
                    'severity': 'Critical' if score < 40 else 'Moderate',
                    'comment': self._get_weakness_comment(dim_name, score)
                }
                weaknesses.append(weakness)
                self.logger.info(f"  ⚠ Weakness: {weakness['dimension']} ({score:.1f}/100) - {weakness['severity']}")
        
        if not weaknesses:
            self.logger.info("  ✓ No critical weaknesses (all dimensions ≥ 60)")
        
        return sorted(weaknesses, key=lambda x: x['score'])
    
    def _generate_recommendations(self, dimension_contributions: Dict) -> List[Dict[str, str]]:
        """
        Generate specific improvement recommendations
        
        Args:
            dimension_contributions: Dimension scores and contributions
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        for dim_name, data in dimension_contributions.items():
            score = data['score']
            
            # Generate recommendations for scores below 75
            if score < 75:
                priority = 'High' if score < 60 else 'Medium'
                recommendation = {
                    'dimension': dim_name.replace('_', ' ').title(),
                    'priority': priority,
                    'suggestion': self._get_recommendation_text(dim_name, score)
                }
                recommendations.append(recommendation)
                self.logger.info(f"  💡 [{priority}] {recommendation['dimension']}: {recommendation['suggestion'][:60]}...")
        
        if not recommendations:
            self.logger.info("  ✓ Excellent performance - continue maintaining high standards")
        
        return sorted(recommendations, key=lambda x: 0 if x['priority'] == 'High' else 1)
    
    def _get_strength_comment(self, dimension: str, score: float) -> str:
        """Get specific comment for strength"""
        comments = {
            'rhythm_tempo': f"Demonstrates excellent timing precision and tempo control (score: {score:.1f}/100). "
                           "Rhythmic patterns are well-executed with consistent timing.",
            'sound_quality': f"Shows strong intonation and pitch accuracy (score: {score:.1f}/100). "
                            "Notes are well in tune with minimal pitch deviation.",
            'technical_virtuosity': f"Exhibits solid technical command (score: {score:.1f}/100). "
                                   "Note accuracy and fluency are well-developed.",
            'phrasing_diction': f"Displays good musical expression and phrasing (score: {score:.1f}/100). "
                               "Effective use of rubato and agogic emphasis.",
            'communicativeness': f"Communicates musical structure effectively (score: {score:.1f}/100). "
                                "Clear sense of musical narrative and climax placement."
        }
        return comments.get(dimension, f"Strong performance in this dimension (score: {score:.1f}/100).")
    
    def _get_weakness_comment(self, dimension: str, score: float) -> str:
        """Get specific comment for weakness"""
        comments = {
            'rhythm_tempo': f"Timing and rhythm need improvement (score: {score:.1f}/100). "
                           "Work on onset precision and maintaining steady tempo.",
            'sound_quality': f"Intonation requires attention (score: {score:.1f}/100). "
                            "Focus on pitch accuracy and reducing out-of-tune notes.",
            'technical_virtuosity': f"Technical execution needs development (score: {score:.1f}/100). "
                                   "Practice note accuracy, fluency, and handling difficult passages.",
            'phrasing_diction': f"Musical expression could be enhanced (score: {score:.1f}/100). "
                               "Develop more nuanced phrasing and dynamic shaping.",
            'communicativeness': f"Musical communication needs strengthening (score: {score:.1f}/100). "
                                "Work on structural coherence and building dramatic arc."
        }
        return comments.get(dimension, f"This dimension needs improvement (score: {score:.1f}/100).")
    
    def _get_recommendation_text(self, dimension: str, score: float) -> str:
        """Get specific recommendation for improvement"""
        recommendations = {
            'rhythm_tempo': "Practice with a metronome to improve timing precision. Focus on onset accuracy and "
                          "maintaining consistent tempo. Record yourself and compare timing against the score.",
            'sound_quality': "Use a tuner during practice to develop better pitch awareness. Practice scales "
                            "and long tones focusing on intonation. Listen critically to pitch accuracy.",
            'technical_virtuosity': "Work on scales and technical exercises. Practice difficult passages slowly, "
                                   "then gradually increase tempo. Focus on clean note transitions and fluency.",
            'phrasing_diction': "Study recordings of professional performances to understand expressive phrasing. "
                               "Practice phrase shaping with varied dynamics and tempo flexibility.",
            'communicativeness': "Analyze the musical structure before practicing. Plan where climaxes should occur. "
                                "Practice sections with attention to their role in the overall narrative."
        }
        return recommendations.get(dimension, 
                                  "Focus on improving this dimension through targeted practice and study.")
    
    def _print_grade_summary(self):
        """Print formatted grade summary"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("PERFORMANCE GRADE SUMMARY")
        self.logger.info("=" * 80)
        self.logger.info(f"\nFinal Score: {self.final_grade['overall_score']:.1f}/100")
        self.logger.info("\n" + "-" * 80)
        
        if self.final_grade['analysis']['strengths']:
            self.logger.info("\nStrengths:")
            for strength in self.final_grade['analysis']['strengths'][:3]:
                self.logger.info(f"  ✓ {strength['dimension']} ({strength['score']:.1f}/100)")
        
        if self.final_grade['analysis']['weaknesses']:
            self.logger.info("\nWeaknesses:")
            for weakness in self.final_grade['analysis']['weaknesses'][:3]:
                self.logger.info(f"  ⚠ {weakness['dimension']} ({weakness['score']:.1f}/100)")
        
        self.logger.info("")
    
    def save_grade_report(self, output_dir: Path):
        """
        Save comprehensive grade report to files
        
        Args:
            output_dir: Directory to save report files
        """
        if not self.final_grade:
            raise ValueError("No grade computed. Call compute_final_grade() first.")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"\n💾 Saving grade report to: {output_dir}")
        
        # 1. Save JSON report
        json_file = output_dir / 'final_grade.json'
        with open(json_file, 'w') as f:
            json.dump(self.final_grade, f, indent=2)
        self.logger.info(f"  ✓ Saved: {json_file.name}")
        
        # 2. Save human-readable report
        txt_file = output_dir / 'performance_report.txt'
        self._save_text_report(txt_file)
        self.logger.info(f"  ✓ Saved: {txt_file.name}")
        
        # 3. Save detailed dimension breakdown
        breakdown_file = output_dir / 'dimension_breakdown.json'
        with open(breakdown_file, 'w') as f:
            json.dump(self.final_grade['dimension_contributions'], f, indent=2)
        self.logger.info(f"  ✓ Saved: {breakdown_file.name}")
        
        self.logger.info("✓ Grade report saved successfully\n")
    
    def _save_text_report(self, filepath: Path):
        """Save human-readable text report"""
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("MUSIC PERFORMANCE GRADE REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            # Header
            f.write(f"Generated: {self.final_grade['metadata']['timestamp']}\n")
            f.write(f"Framework: {self.final_grade['metadata']['grading_framework']}\n\n")
            
            # Final Grade
            f.write("=" * 80 + "\n")
            f.write("FINAL GRADE\n")
            f.write("=" * 80 + "\n")
            f.write(f"Overall Score: {self.final_grade['overall_score']:.1f}/100\n\n")
            
            # Dimension Breakdown
            f.write("=" * 80 + "\n")
            f.write("DIMENSION BREAKDOWN\n")
            f.write("=" * 80 + "\n\n")
            
            for dim_name, data in self.final_grade['dimension_contributions'].items():
                dim_title = dim_name.replace('_', ' ').title()
                f.write(f"{dim_title} (Weight: {data['weight']:.0%})\n")
                f.write(f"  Score: {data['score']:.1f}/100 ({data['interpretation']})\n")
                f.write(f"  Contribution to Final: {data['contribution']:.1f} points\n\n")
            
            # Strengths
            if self.final_grade['analysis']['strengths']:
                f.write("=" * 80 + "\n")
                f.write("STRENGTHS\n")
                f.write("=" * 80 + "\n\n")
                
                for i, strength in enumerate(self.final_grade['analysis']['strengths'], 1):
                    f.write(f"{i}. {strength['dimension']} ({strength['score']:.1f}/100)\n")
                    f.write(f"   {strength['comment']}\n\n")
            
            # Weaknesses
            if self.final_grade['analysis']['weaknesses']:
                f.write("=" * 80 + "\n")
                f.write("AREAS FOR IMPROVEMENT\n")
                f.write("=" * 80 + "\n\n")
                
                for i, weakness in enumerate(self.final_grade['analysis']['weaknesses'], 1):
                    f.write(f"{i}. {weakness['dimension']} ({weakness['score']:.1f}/100) - {weakness['severity']}\n")
                    f.write(f"   {weakness['comment']}\n\n")
            
            # Recommendations
            if self.final_grade['analysis']['recommendations']:
                f.write("=" * 80 + "\n")
                f.write("RECOMMENDATIONS FOR IMPROVEMENT\n")
                f.write("=" * 80 + "\n\n")
                
                for i, rec in enumerate(self.final_grade['analysis']['recommendations'], 1):
                    f.write(f"{i}. [{rec['priority']} Priority] {rec['dimension']}\n")
                    f.write(f"   {rec['suggestion']}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
    
    def process(self, inference_core_output_dir: Path, save_output: bool = True) -> Dict[str, Any]:
        """
        Complete grading process
        
        Args:
            inference_core_output_dir: Directory containing Inference Core output
            save_output: Whether to save output files
            
        Returns:
            Final grade dictionary
        """
        # Load grading package
        grading_package_file = inference_core_output_dir / 'grading_package_master.json'
        self.load_grading_package(grading_package_file)
        
        # Compute final grade
        final_grade = self.compute_final_grade()
        
        # Save outputs
        if save_output:
            output_dir = inference_core_output_dir.parent / '06_grading_layer'
            self.save_grade_report(output_dir)
        
        return final_grade


def main():
    """Test Grading Layer"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Grading Layer - Compute final performance grade')
    parser.add_argument('inference_output_dir', 
                       help='Directory containing Inference Core output (05_inference_core)')
    parser.add_argument('--no-save', action='store_true', help='Do not save output files')
    
    args = parser.parse_args()
    
    # Create and run grading layer
    grading_layer = GradingLayer()
    final_grade = grading_layer.process(
        Path(args.inference_output_dir),
        save_output=not args.no_save
    )
    
    print(f"\n✅ Grading complete!")
    print(f"   Final Score: {final_grade['overall_score']:.1f}/100")
    print(f"   Letter Grade: {final_grade['letter_grade']}")


if __name__ == '__main__':
    main()
