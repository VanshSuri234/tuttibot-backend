#!/usr/bin/env python3
"""
Enhanced Inference Core with PQG-A2SA Integration
==================================================

This is an enhanced version of inference_core.py that implements the two-pass approach:
1. First pass: Uses Block 2 DTW-based grading metrics
2. Second pass: If PQG-A2SA results available, recomputes metrics and overrides

This provides backward compatibility (works without PQG-A2SA) while enabling
enhanced accuracy when PQG-A2SA is available.

Author: TuttiBot Team
Date: November 2025
Version: 2.0 (with PQG-A2SA integration)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .data_collector import DataCollector, InferenceCoreInputs
from .utils import MetricsExtractor, ScoringFunctions
from .pqg_metrics_recomputer import PQGMetricsRecomputer


class InferenceCoreWithPQG:
    """
    Enhanced Inference Core with PQG-A2SA integration
    
    This extends the original InferenceCore to support two-pass metric computation:
    - Pass 1: Extract DTW-based metrics from Block 2 (always available)
    - Pass 2: Recompute with PQG-A2SA if available (optional enhancement)
    
    The enhanced metrics from PQG-A2SA override DTW metrics for:
    - rhythm_tempo (IOI correlation, onset errors)
    - sound_quality (pitch accuracy)
    - technical_virtuosity (note accuracy, articulation precision)
    """
    
    def __init__(self, output_base_dir: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize Enhanced Inference Core
        
        Args:
            output_base_dir: Base directory containing all layer outputs
            logger: Optional logger instance
        """
        self.output_base_dir = Path(output_base_dir)
        self.logger = logger or self._setup_logger()
        
        # Initialize components
        self.data_collector = DataCollector(output_base_dir, self.logger)
        self.metrics_extractor = MetricsExtractor(self.logger)
        self.scoring_functions = ScoringFunctions(self.logger)
        self.pqg_recomputer = PQGMetricsRecomputer(self.logger)
        
        # Storage
        self.inputs: Optional[InferenceCoreInputs] = None
        self.grading_package: Optional[Dict[str, Any]] = None
        self.pqg_enhanced: bool = False
        self.metric_sources: Dict[str, str] = {}
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('InferenceCoreWithPQG')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def process(self, save_output: bool = True, use_pqg_if_available: bool = True) -> Dict[str, Any]:
        """
        Complete processing pipeline with optional PQG-A2SA enhancement
        
        Args:
            save_output: Whether to save output files
            use_pqg_if_available: Whether to use PQG-A2SA metrics if available
            
        Returns:
            Complete grading package dictionary
        """
        start_time = datetime.now()
        import sys
        
        print("\n" + "=" * 80)
        print("ENHANCED INFERENCE CORE - PROCESSING PIPELINE (with PQG-A2SA)")
        print("=" * 80)
        sys.stdout.flush()
        
        try:
            # ===== STEP 1: Data Collection =====
            print("\n🔍 STEP 1: Data Collection")
            sys.stdout.flush()
            self.inputs = self.data_collector.collect_all_data()
            
            # ===== STEP 2: Extract DTW Metrics (Pass 1) =====
            print("\n📊 STEP 2: Extracting DTW-Based Metrics from Block 2 (Pass 1)")
            sys.stdout.flush()
            
            dtw_grading_metrics = self.metrics_extractor.extract_grading_metrics(
                self.inputs.alignment_results
            )
            
            print(f"  ✓ Extracted {len(dtw_grading_metrics)} dimensions from DTW")
            sys.stdout.flush()
            
            # Validate DTW metrics
            validation = self.metrics_extractor.validate_metrics(dtw_grading_metrics)
            
            # ===== STEP 3: PQG-A2SA Enhancement (Pass 2) =====
            final_metrics = dtw_grading_metrics
            
            if use_pqg_if_available and self.inputs.has_pqg_a2sa:
                print("\n🎯 STEP 3: PQG-A2SA Enhancement (Pass 2)")
                print("  PQG-A2SA results detected - recomputing metrics...")
                sys.stdout.flush()
                
                # Load PQG-A2SA results
                pqg_dir = self.output_base_dir / '05_pqg_a2sa'
                pqg_results_path = pqg_dir / 'pqg_a2sa_results.json'
                
                pqg_results = self.pqg_recomputer.load_pqg_results(pqg_results_path)
                
                if pqg_results:
                    # Get score note count from DTW metrics for accurate note accuracy
                    score_note_count = None
                    if 'technical_virtuosity' in dtw_grading_metrics:
                        score_note_count = dtw_grading_metrics['technical_virtuosity'].get('total_score_notes')
                    
                    # Get DTW note alignments for score matching
                    # Handle both flat and nested structure
                    dtw_note_alignments = []
                    if 'note_alignments' in self.inputs.alignment_results:
                        dtw_note_alignments = self.inputs.alignment_results['note_alignments']
                    elif 'alignment' in self.inputs.alignment_results:
                        if 'note_alignments' in self.inputs.alignment_results['alignment']:
                            dtw_note_alignments = self.inputs.alignment_results['alignment']['note_alignments']
                    
                    print(f"  Found {len(dtw_note_alignments)} DTW note alignments")
                    sys.stdout.flush()
                    
                    if not dtw_note_alignments:
                        print("  ⚠ No DTW note alignments available - cannot merge with PQG")
                        sys.stdout.flush()
                        self.metric_sources = {dim: 'DTW (Block 2)' for dim in dtw_grading_metrics}
                    else:
                        # Recompute metrics using PQG-A2SA merged with DTW alignments
                        pqg_metrics = self.pqg_recomputer.recompute_all_metrics(
                            pqg_results,
                            dtw_note_alignments,
                            score_note_count=score_note_count
                        )
                        
                        if pqg_metrics:
                            # Merge metrics (PQG overrides DTW)
                            final_metrics, self.metric_sources = self.pqg_recomputer.merge_metrics(
                                dtw_grading_metrics,
                                pqg_metrics
                            )
                            self.pqg_enhanced = True
                            
                            print("  ✓ Metrics enhanced with PQG-A2SA")
                            sys.stdout.flush()
                        else:
                            print("  ⚠ PQG-A2SA recomputation failed - using DTW metrics")
                            sys.stdout.flush()
                            self.metric_sources = {dim: 'DTW (Block 2)' for dim in dtw_grading_metrics}
                else:
                    print("  ⚠ Could not load PQG-A2SA results - using DTW metrics")
                    sys.stdout.flush()
                    self.metric_sources = {dim: 'DTW (Block 2)' for dim in dtw_grading_metrics}
            else:
                if use_pqg_if_available:
                    print("\n📊 STEP 3: PQG-A2SA not available - using DTW metrics")
                else:
                    print("\n📊 STEP 3: PQG-A2SA disabled - using DTW metrics")
                sys.stdout.flush()
                self.metric_sources = {dim: 'DTW (Block 2)' for dim in dtw_grading_metrics}
            
            # ===== STEP 4: Score Dimensions =====
            print("\n🎯 STEP 4: Scoring Dimensions")
            sys.stdout.flush()
            
            scored_dimensions = self.scoring_functions.score_all_dimensions(final_metrics)
            
            # ===== STEP 5: Create Grading Package =====
            print("\n📦 STEP 5: Creating Grading Package")
            sys.stdout.flush()
            
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
                'pqg_enhancement': {
                    'enabled': use_pqg_if_available,
                    'used': self.pqg_enhanced,
                    'metric_sources': self.metric_sources
                },
                'extraction_validation': validation,
                'grading_dimensions': {}
            }
            
            # Add dimension weights
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
                        'source': self.metric_sources.get(dim_name, 'Unknown'),
                        'component_scores': {
                            k: v for k, v in scored_dimensions[dim_name].items()
                            if k not in ['dimension_score', 'interpretation', 'raw_metrics']
                        },
                        'raw_metrics': scored_dimensions[dim_name].get('raw_metrics', {})
                    }
            
            # Validation
            self.grading_package['validation'] = self._validate_package()
            
            # ===== STEP 6: Save Outputs =====
            if save_output:
                print("\n💾 STEP 6: Saving Outputs")
                sys.stdout.flush()
                output_dir = self.output_base_dir / '05_inference_core'
                self._save_outputs(output_dir)
            
            # Summary
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print("\n" + "=" * 80)
            print("✅ ENHANCED INFERENCE CORE PROCESSING COMPLETE")
            if self.pqg_enhanced:
                print("   🎯 PQG-A2SA enhancement: ACTIVE")
                print(f"   📊 Enhanced dimensions: {sum(1 for s in self.metric_sources.values() if 'PQG' in s)}")
            else:
                print("   📊 Using DTW-based metrics only")
            print(f"   ⏱️  Processing time: {elapsed_time:.2f} seconds")
            print("=" * 80 + "\n")
            sys.stdout.flush()
            
            return self.grading_package
            
        except Exception as e:
            print(f"\n❌ ENHANCED INFERENCE CORE ERROR: {e}")
            sys.stdout.flush()
            import traceback
            traceback.print_exc()
            raise
    
    def _create_metadata(self, extraction_metadata: Dict = None) -> Dict[str, Any]:
        """Create metadata for grading package"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'inference_core_version': '2.0-with-PQG',
            'output_base_dir': str(self.output_base_dir),
            'audio_path': str(self.inputs.audio_path) if self.inputs.audio_path else None,
            'score_path': str(self.inputs.score_path) if self.inputs.score_path else None,
            'pqg_enhanced': self.pqg_enhanced
        }
        
        if extraction_metadata:
            metadata['block2_source'] = extraction_metadata
        
        return metadata
    
    def _validate_package(self) -> Dict[str, Any]:
        """Validate grading package completeness"""
        validation = {
            'is_complete': True,
            'missing_dimensions': [],
            'warnings': [],
            'errors': [],
            'pqg_enhanced': self.pqg_enhanced
        }
        
        # Check each dimension
        for dim_name, dim_data in self.grading_package['grading_dimensions'].items():
            if not dim_data or dim_data.get('dimension_score') is None:
                validation['missing_dimensions'].append(dim_name)
                validation['warnings'].append(f"Dimension '{dim_name}' has incomplete score")
        
        # Check critical data
        if not self.inputs.has_temporal_alignment:
            validation['errors'].append("Temporal alignment data missing (critical)")
            validation['is_complete'] = False
        
        return validation
    
    def _save_outputs(self, output_dir: Path):
        """Save grading package and related outputs"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save grading package
        package_file = output_dir / 'grading_package_enhanced.json'
        with open(package_file, 'w') as f:
            json.dump(self.grading_package, f, indent=2)
        
        #self.logger.info(f"  ✓ Saved enhanced grading package: {package_file.name}")
        print(f"  ✓ Saved enhanced grading package: {package_file.name}")
        import sys
        sys.stdout.flush()
        
        # Save metric source map
        if self.metric_sources:
            source_map_file = output_dir / 'metric_sources.json'
            with open(source_map_file, 'w') as f:
                json.dump({
                    'pqg_enhanced': self.pqg_enhanced,
                    'sources': self.metric_sources,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            #self.logger.info(f"  ✓ Saved metric source map: {source_map_file.name}")
            print(f"  ✓ Saved metric source map: {source_map_file.name}")
            sys.stdout.flush()


def main():
    """Test/demo function"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced Inference Core with PQG-A2SA integration"
    )
    parser.add_argument("output_dir", help="Output directory containing layer results")
    parser.add_argument("--no-pqg", action="store_true", help="Disable PQG-A2SA enhancement")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run enhanced inference core
    inference = InferenceCoreWithPQG(Path(args.output_dir))
    
    try:
        grading_package = inference.process(
            save_output=True,
            use_pqg_if_available=not args.no_pqg
        )
        
        print("\n" + "=" * 70)
        print("SUCCESS - Grading package created")
        print("=" * 70)
        
        if grading_package.get('pqg_enhancement', {}).get('used'):
            print("\n✓ PQG-A2SA enhancement ACTIVE")
            print("\nMetric sources:")
            for dim, source in inference.metric_sources.items():
                print(f"  - {dim}: {source}")
        else:
            print("\n  Using DTW-based metrics only")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
