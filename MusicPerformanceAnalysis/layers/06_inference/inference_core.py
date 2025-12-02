#!/usr/bin/env python3
"""
Inference Core - Main Orchestrator
===================================

Coordinates data collection, analysis, and formatting for Grading Layer.

Author: TuttiBot Team
Version: 1.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .data_collector import DataCollector, InferenceCoreInputs
from .utils import MetricsExtractor, ScoringFunctions


class InferenceCore:
    """
    Main Inference Core orchestrator
    
    Bridges upstream layers and Grading Layer by:
    1. Collecting all upstream data
    2. Analyzing each grading dimension
    3. Formatting output for Grading Layer
    4. Validating completeness
    """
    
    def __init__(self, output_base_dir: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize Inference Core
        
        Args:
            output_base_dir: Base directory containing all layer outputs
            logger: Optional logger instance
        """
        self.output_base_dir = Path(output_base_dir)
        self.logger = logger or self._setup_logger()
        
        # Initialize data collector
        self.data_collector = DataCollector(output_base_dir, self.logger)
        
        # Initialize metrics extractor and scoring functions
        self.metrics_extractor = MetricsExtractor(self.logger)
        self.scoring_functions = ScoringFunctions(self.logger)
        
        # Storage for inputs and results
        self.inputs: Optional[InferenceCoreInputs] = None
        self.grading_package: Optional[Dict[str, Any]] = None
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('InferenceCore')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def process(self, save_output: bool = True) -> Dict[str, Any]:
        """
        Complete processing pipeline
        
        Args:
            save_output: Whether to save output files
            
        Returns:
            Complete grading package dictionary
        """
        start_time = datetime.now()
        
        # self.logger.info("\n" + "=" * 80)
        self.logger.info("INFERENCE CORE - PROCESSING PIPELINE")
        # self.logger.info("=" * 80)
        
        try:
            # Step 1: Collect all upstream data
            self.logger.info("\n STEP 1: Data Collection")
            self.inputs = self.data_collector.collect_all_data()
            
            # Step 2: Extract grading metrics from Block 2
            self.logger.info("\n STEP 2: Extracting Grading Metrics from Block 2")
            
            raw_grading_metrics = self.metrics_extractor.extract_grading_metrics(
                self.inputs.alignment_results
            )
            
            # Validate metrics
            validation = self.metrics_extractor.validate_metrics(raw_grading_metrics)
            
            # Step 3: Score all dimensions (convert raw metrics to 0-100 scores)
            self.logger.info("\n STEP 3: Scoring Dimensions")
            
            scored_dimensions = self.scoring_functions.score_all_dimensions(raw_grading_metrics)
            
            # Step 4: Create grading package
            self.logger.info("\n STEP 4: Creating Grading Package")
            
            # Add metadata and validation from extraction
            extraction_metadata = self.metrics_extractor.get_metadata(self.inputs.alignment_results)
            
            self.grading_package = {
                'metadata': self._create_metadata(extraction_metadata),
                'data_availability': {
                    'processing_layer': self.inputs.has_processing,
                    'extraction_layer': self.inputs.has_extraction,
                    'temporal_alignment': self.inputs.has_temporal_alignment,
                    'beat_detection': self.inputs.has_beat_detection,
                    'pqg_a2sa': self.inputs.has_pqg_a2sa
                },
                'extraction_validation': validation,
                'grading_dimensions': {}
            }
            
            # Add each scored dimension with PQG-A2SA weights
            dimension_weights = {
                'rhythm_tempo': 0.30,
                'sound_quality': 0.20,
                'technical_virtuosity': 0.20,
                'phrasing_diction': 0.15,
                'communicativeness': 0.15
            }
            
            for dim_name, weight in dimension_weights.items():
                if dim_name in scored_dimensions:
                    self.grading_package['grading_dimensions'][dim_name] = {
                        'weight': weight,
                        'dimension_score': scored_dimensions[dim_name]['dimension_score'],
                        'interpretation': scored_dimensions[dim_name]['interpretation'],
                        'component_scores': {
                            k: v for k, v in scored_dimensions[dim_name].items()
                            if k not in ['dimension_score', 'interpretation', 'raw_metrics']
                        },
                        'raw_metrics': scored_dimensions[dim_name].get('raw_metrics', {})
                    }
            
            # Add overall validation
            self.grading_package['validation'] = self._validate_package()
            
            # Step 5: Save outputs
            if save_output:
                self.logger.info("\n STEP 5: Saving Outputs")
                output_dir = self.output_base_dir / '05_inference_core'
                self._save_outputs(output_dir)
            
            # Summary
            elapsed_time = (datetime.now() - start_time).total_seconds()
            # self.logger.info("\n" + "=" * 80)
            self.logger.info(" INFERENCE CORE PROCESSING COMPLETE")
            self.logger.info(f"   Processing time: {elapsed_time:.2f} seconds")
            # self.logger.info("=" * 80 + "\n")
            
            return self.grading_package
            
        except Exception as e:
            self.logger.error(f"\n INFERENCE CORE ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _create_metadata(self, extraction_metadata: Dict = None) -> Dict[str, Any]:
        """Create metadata for grading package"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'inference_core_version': '2.0',
            'output_base_dir': str(self.output_base_dir),
            'audio_path': str(self.inputs.audio_path) if self.inputs.audio_path else None,
            'score_path': str(self.inputs.score_path) if self.inputs.score_path else None
        }
        
        # Add Block 2 metadata if available
        if extraction_metadata:
            metadata['block2_source'] = extraction_metadata
        
        return metadata
    
    def _validate_package(self) -> Dict[str, Any]:
        """Validate grading package completeness"""
        validation = {
            'is_complete': True,
            'missing_dimensions': [],
            'warnings': [],
            'errors': []
        }
        
        # Check each dimension has data
        for dim_name, dim_data in self.grading_package['grading_dimensions'].items():
            if not dim_data or dim_data.get('dimension_score') is None:
                validation['missing_dimensions'].append(dim_name)
                validation['warnings'].append(f"Dimension '{dim_name}' has incomplete score")
        
        # Check critical data sources
        if not self.inputs.has_temporal_alignment:
            validation['errors'].append("Temporal alignment data missing (critical)")
            validation['is_complete'] = False
        
        if not self.inputs.alignment_results:
            validation['errors'].append("Block 2 alignment results missing (critical)")
            validation['is_complete'] = False
        
        if not self.inputs.has_extraction:
            validation['warnings'].append("Extraction layer data missing (some metrics unavailable)")
        
        if not self.inputs.has_processing:
            validation['warnings'].append("Processing layer data missing (some metrics unavailable)")
        
        return validation
    
    def _save_outputs(self, output_dir: Path):
        """Save all output files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Save master grading package
        master_file = output_dir / 'grading_package_master.json'
        with open(master_file, 'w') as f:
            json.dump(self.grading_package, f, indent=2)
        self.logger.info(f"   ✓ Saved master package: {master_file.name}")
        
        # 2. Save individual dimension files
        dimensions_dir = output_dir / 'dimensions'
        dimensions_dir.mkdir(exist_ok=True)
        
        for dim_name, dim_info in self.grading_package['grading_dimensions'].items():
            dim_file = dimensions_dir / f'{dim_name}.json'
            dim_output = {
                'dimension': dim_name,
                'weight': dim_info['weight'],
                'dimension_score': dim_info['dimension_score'],
                'interpretation': dim_info['interpretation'],
                'component_scores': dim_info.get('component_scores', {}),
                'raw_metrics': dim_info.get('raw_metrics', {}),
                'timestamp': self.grading_package['metadata']['timestamp']
            }
            with open(dim_file, 'w') as f:
                json.dump(dim_output, f, indent=2)
            self.logger.info(f"  Saved dimension: {dim_file.name}")
        
        # 3. Save validation report
        validation_file = output_dir / 'validation_report.json'
        with open(validation_file, 'w') as f:
            json.dump(self.grading_package['validation'], f, indent=2)
        self.logger.info(f"  Saved validation: {validation_file.name}")
        
        # 4. Save human-readable summary
        summary_file = output_dir / 'inference_summary.txt'
        self._save_summary(summary_file)
        self.logger.info(f"  Saved summary: {summary_file.name}")
    
    def _save_summary(self, summary_file: Path):
        """Save human-readable summary"""
        with open(summary_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("INFERENCE CORE - PROCESSING SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Timestamp: {self.grading_package['metadata']['timestamp']}\n")
            f.write(f"Output Directory: {self.output_base_dir}\n\n")
            
            f.write("DATA AVAILABILITY:\n")
            f.write("-" * 80 + "\n")
            for source, available in self.grading_package['data_availability'].items():
                status = " Available" if available else " Missing"
                f.write(f"  {source:.<50} {status}\n")
            f.write("\n")
            
            f.write("GRADING DIMENSIONS:\n")
            f.write("-" * 80 + "\n")
            for dim_name, dim_info in self.grading_package['grading_dimensions'].items():
                score = dim_info.get('dimension_score', 0)
                interpretation = dim_info.get('interpretation', 'unknown')
                weight = dim_info['weight'] * 100
                
                f.write(f"\n  {dim_name.upper().replace('_', ' ')} ({weight:.0f}% weight):\n")
                f.write(f"    Score: {score:.1f}/100 ({interpretation})\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("VALIDATION:\n")
            f.write("=" * 80 + "\n")
            
            val = self.grading_package['validation']
            f.write(f"Complete: {'YES' if val['is_complete'] else 'NO'}\n")
            
            if val['warnings']:
                f.write("\nWarnings:\n")
                for warning in val['warnings']:
                    f.write(f"  ⚠ {warning}\n")
            
            if val['errors']:
                f.write("\nErrors:\n")
                for error in val['errors']:
                    f.write(f"  ✗ {error}\n")
            
            f.write("\n" + "=" * 80 + "\n")


def main():
    """Test Inference Core"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Inference Core - Process upstream layer outputs')
    parser.add_argument('output_dir', help='Base output directory containing all layer outputs')
    parser.add_argument('--no-save', action='store_true', help='Do not save output files')
    
    args = parser.parse_args()
    
    # Create and run inference core
    inference_core = InferenceCore(Path(args.output_dir))
    grading_package = inference_core.process(save_output=not args.no_save)
    
    print("\n Inference Core processing complete!")
    print(f"   Grading package created with {len(grading_package['grading_dimensions'])} dimensions")


if __name__ == '__main__':
    main()
