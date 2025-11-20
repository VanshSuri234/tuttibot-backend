#!/usr/bin/env python3
"""
Metrics Extractor - Extract Grading Metrics from Block 2
=========================================================

Extracts pre-computed grading metrics from Block 2 alignment results.
Does NOT recompute - just loads and validates.
"""

import logging
from typing import Dict, Any, List, Optional


class MetricsExtractor:
    """Extract and validate grading metrics from Block 2 output"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def extract_grading_metrics(self, alignment_results: Dict) -> Dict[str, Any]:
        """
        Extract pre-computed grading_metrics from Block 2 alignment results
        
        Args:
            alignment_results: Block 2 enhanced_alignment_complete.json content
            
        Returns:
            Dictionary with grading metrics for all 5 dimensions
            
        Raises:
            ValueError: If grading_metrics not found or invalid
        """
        self.logger.info("Extracting grading metrics from Block 2 output...")
        
        # Validate structure
        if not alignment_results:
            raise ValueError("No alignment results provided")
        
        if 'alignment' not in alignment_results:
            raise ValueError("Invalid alignment results: missing 'alignment' key")
        
        alignment = alignment_results['alignment']
        
        if 'grading_metrics' not in alignment:
            raise ValueError("No grading_metrics found in alignment results")
        
        # Extract metrics
        grading_metrics = alignment['grading_metrics']
        
        # Validate dimensions
        expected_dimensions = [
            'rhythm_tempo',
            'sound_quality',
            'technical_virtuosity',
            'phrasing_diction',
            'communicativeness'
        ]
        
        missing_dimensions = []
        for dim in expected_dimensions:
            if dim not in grading_metrics:
                missing_dimensions.append(dim)
                self.logger.warning(f"  ⚠ Missing dimension: {dim}")
        
        if missing_dimensions:
            self.logger.warning(f"Missing {len(missing_dimensions)} dimensions: {missing_dimensions}")
        
        # Log extraction summary
        self.logger.info(f"  ✓ Extracted {len(grading_metrics)} dimensions")
        for dim_name, dim_data in grading_metrics.items():
            metric_count = len(dim_data) if isinstance(dim_data, dict) else 0
            self.logger.info(f"    - {dim_name}: {metric_count} metrics")
        
        return grading_metrics
    
    def validate_metrics(self, grading_metrics: Dict) -> Dict[str, Any]:
        """
        Validate that all expected metrics are present in each dimension
        
        Args:
            grading_metrics: Extracted grading metrics dictionary
            
        Returns:
            Validation report with warnings and errors
        """
        self.logger.info("Validating grading metrics...")
        
        validation_report = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'dimension_status': {}
        }
        
        # Expected metrics for each dimension
        expected_metrics = {
            'rhythm_tempo': [
                'mean_onset_error_ms',
                'onset_std_ms',
                'ioi_correlation',
                'tempo_cv_percent',
                'onset_error_distribution'
            ],
            'sound_quality': [
                'pitch_accuracy_50c_percent',
                'pitch_accuracy_25c_percent',
                'mean_pitch_error_cents',
                'pitch_std_cents',
                'pitch_error_distribution'
            ],
            'technical_virtuosity': [
                'note_accuracy_percent',
                'total_score_notes',
                'matched_notes',
                'unmatched_notes',
                'extra_notes',
                'fluency_ioi_cv_percent',
                'articulation_precision_ms',
                'difficulty_mastery'
            ],
            'phrasing_diction': [
                'rubato_variation_std',
                'rubato_mean_ratio',
                'phrase_boundary_count',
                'agogic_expression_mean_percent'
            ],
            'communicativeness': [
                'section_count',
                'section_tempo_consistency',
                'climax_position_percent',
                'dramatic_trajectory_r2'
            ]
        }
        
        # Validate each dimension
        for dim_name, expected_keys in expected_metrics.items():
            dim_status = {
                'present': dim_name in grading_metrics,
                'missing_metrics': [],
                'has_data': False
            }
            
            if dim_name not in grading_metrics:
                validation_report['errors'].append(f"Dimension '{dim_name}' missing")
                validation_report['is_valid'] = False
                dim_status['present'] = False
            else:
                dim_data = grading_metrics[dim_name]
                
                # Check if dimension has any data
                if dim_data and isinstance(dim_data, dict) and len(dim_data) > 0:
                    dim_status['has_data'] = True
                else:
                    validation_report['warnings'].append(f"Dimension '{dim_name}' is empty")
                
                # Check for expected metrics
                for metric_key in expected_keys:
                    if metric_key not in dim_data:
                        dim_status['missing_metrics'].append(metric_key)
                        validation_report['warnings'].append(
                            f"Metric '{metric_key}' missing in dimension '{dim_name}'"
                        )
            
            validation_report['dimension_status'][dim_name] = dim_status
        
        # Summary
        if validation_report['errors']:
            self.logger.error(f"  ✗ Validation failed with {len(validation_report['errors'])} errors")
            for error in validation_report['errors']:
                self.logger.error(f"    - {error}")
        
        if validation_report['warnings']:
            self.logger.warning(f"  ⚠ {len(validation_report['warnings'])} warnings")
            for warning in validation_report['warnings'][:5]:  # Show first 5
                self.logger.warning(f"    - {warning}")
            if len(validation_report['warnings']) > 5:
                self.logger.warning(f"    ... and {len(validation_report['warnings']) - 5} more")
        
        if not validation_report['errors'] and not validation_report['warnings']:
            self.logger.info("  ✓ All metrics validated successfully")
        
        return validation_report
    
    def extract_note_alignments(self, alignment_results: Dict) -> List[Dict]:
        """
        Extract note-level alignments from Block 2 output
        
        Args:
            alignment_results: Block 2 alignment results
            
        Returns:
            List of note alignment dictionaries
        """
        if not alignment_results or 'alignment' not in alignment_results:
            return []
        
        note_alignments = alignment_results['alignment'].get('note_alignments', [])
        
        self.logger.info(f"  ✓ Extracted {len(note_alignments)} note alignments")
        
        return note_alignments
    
    def get_metadata(self, alignment_results: Dict) -> Dict[str, Any]:
        """
        Extract metadata from Block 2 output
        
        Args:
            alignment_results: Block 2 alignment results
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'block2_metadata': None,
            'input_files': None,
            'dtw_distance': None,
            'confidence': None,
            'score_duration': None,
            'perf_duration': None
        }
        
        if not alignment_results:
            return metadata
        
        # Extract metadata
        if 'metadata' in alignment_results:
            metadata['block2_metadata'] = alignment_results['metadata']
        
        if 'input_files' in alignment_results:
            metadata['input_files'] = alignment_results['input_files']
        
        # Extract alignment quality metrics
        if 'alignment' in alignment_results:
            alignment = alignment_results['alignment']
            metadata['dtw_distance'] = alignment.get('dtw_distance')
            metadata['confidence'] = alignment.get('confidence')
            metadata['score_duration'] = alignment.get('score_duration')
            metadata['perf_duration'] = alignment.get('perf_duration')
        
        return metadata


def main():
    """Test metrics extraction"""
    import json
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("Usage: python metrics_extractor.py <alignment_results.json>")
        sys.exit(1)
    
    # Load alignment results
    alignment_file = Path(sys.argv[1])
    if not alignment_file.exists():
        print(f"Error: File not found: {alignment_file}")
        sys.exit(1)
    
    with open(alignment_file, 'r') as f:
        alignment_results = json.load(f)
    
    # Extract and validate
    extractor = MetricsExtractor()
    
    try:
        grading_metrics = extractor.extract_grading_metrics(alignment_results)
        validation = extractor.validate_metrics(grading_metrics)
        note_alignments = extractor.extract_note_alignments(alignment_results)
        metadata = extractor.get_metadata(alignment_results)
        
        print("\n" + "=" * 70)
        print("EXTRACTION SUMMARY")
        print("=" * 70)
        print(f"Dimensions extracted: {len(grading_metrics)}")
        print(f"Note alignments: {len(note_alignments)}")
        print(f"Validation status: {'PASS' if validation['is_valid'] else 'FAIL'}")
        print(f"Warnings: {len(validation['warnings'])}")
        print(f"Errors: {len(validation['errors'])}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
