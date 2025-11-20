#!/usr/bin/env python3
"""
Enhanced Pipeline with PQG-A2SA Integration
============================================

This is an enhanced version of the main pipeline that uses the two-pass approach
for grading metrics:
1. Block 2 DTW provides baseline metrics (always available)
2. PQG-A2SA provides enhanced metrics (if available, overrides DTW)

This file does NOT modify the original pipeline.py - it's a new variant that
users can choose to use when they want PQG-A2SA enhancement.

Usage:
    python pipeline_with_pqg.py --audio audio.wav --score score.xml --output results/

Author: TuttiBot Team
Date: November 2025
Version: 2.0
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Import the original pipeline from same directory
from pipeline import MusicPerformancePipeline


class EnhancedPipelineWithPQG(MusicPerformancePipeline):
    """
    Enhanced pipeline that uses PQG-A2SA for improved grading metrics
    
    This inherits from the original MusicPerformancePipeline and only overrides
    the run_inference() method to use the enhanced inference core.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with same arguments as original pipeline"""
        super().__init__(*args, **kwargs)
        
        # Flag to track if we're using PQG enhancement
        self.use_pqg_enhancement = True
        
        logging.info("Enhanced Pipeline with PQG-A2SA Integration initialized")
    
    def run_inference(self):
        """
        Override to use Enhanced Inference Core with PQG-A2SA integration
        
        This is the ONLY method that differs from the original pipeline.
        Everything else remains the same.
        """
        logger = logging.getLogger(__name__)
        logger.info("\n[Layer 6: Enhanced Inference Core with PQG-A2SA]")
        
        try:
            # Import the enhanced inference core (using importlib for numeric module name)
            import importlib
            LAYERS_DIR = Path(__file__).parent / "layers"
            if str(LAYERS_DIR) not in sys.path:
                sys.path.insert(0, str(LAYERS_DIR))
            
            inference_module = importlib.import_module('06_inference')
            InferenceCoreWithPQG = inference_module.InferenceCoreWithPQG
            
            # Create enhanced inference core
            inference = InferenceCoreWithPQG(
                output_base_dir=self.output_dir,
                logger=logger
            )
            
            # Process with PQG-A2SA enhancement if available
            grading_package = inference.process(
                save_output=True,
                use_pqg_if_available=self.use_pqg_enhancement
            )
            
            # Track status
            self.status['inference'] = True
            self.results['grading_package'] = str(
                self.output_dir / '05_inference_core' / 'grading_package_enhanced.json'
            )
            self.results['pqg_enhanced'] = inference.pqg_enhanced
            
            if inference.pqg_enhanced:
                logger.info("✓ Inference complete (PQG-A2SA enhanced)")
            else:
                logger.info("✓ Inference complete (DTW-based)")
            
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import enhanced inference core: {e}")
            logger.warning("Falling back to original inference core...")
            # Fall back to original implementation
            return super().run_inference()
            
        except Exception as e:
            logger.error(f"Enhanced inference failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_pipeline(self):
        """
        Run complete pipeline with PQG-A2SA enhancement
        
        This calls the parent's run_pipeline() but adds PQG enhancement info
        to the summary.
        """
        logger = logging.getLogger(__name__)
        logger.info("\n" + "="*70)
        logger.info("  ENHANCED MUSIC PERFORMANCE ANALYSIS PIPELINE")
        logger.info("  (with PQG-A2SA Integration)")
        logger.info("="*70)
        logger.info(f"  Audio: {self.audio_path.name}")
        logger.info(f"  Score: {self.score_path.name}")
        logger.info(f"  Output: {self.output_dir.name}")
        logger.info(f"  PQG Enhancement: {'Enabled' if self.use_pqg_enhancement else 'Disabled'}")
        logger.info("="*70)
        
        # Run the parent's pipeline
        success = super().run_pipeline()
        
        return success
    
    def _save_summary(self, start_time):
        """
        Override to add PQG enhancement info to summary
        """
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            'pipeline_version': '2.0-with-PQG',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'status': self.status,
            'results': self.results,
            'inputs': {
                'audio': str(self.audio_path),
                'score': str(self.score_path),
                'part': self.score_part
            },
            'output_directory': str(self.output_dir),
            'pqg_enhancement': {
                'enabled': self.use_pqg_enhancement,
                'used': self.results.get('pqg_enhanced', False)
            }
        }
        
        summary_file = self.output_dir / "pipeline_summary_enhanced.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Enhanced pipeline summary: {summary_file}")
        logger.info(f"Duration: {duration:.1f} seconds")
        
        if summary['pqg_enhancement']['used']:
            logger.info("✓ PQG-A2SA enhancement was applied")
        else:
            logger.info("  PQG-A2SA enhancement not used (using DTW metrics)")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced Music Performance Analysis Pipeline with PQG-A2SA Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with PQG-A2SA enhancement (default)
  python pipeline_with_pqg.py --audio performance.wav --score score.xml --output results/

  # Disable PQG-A2SA enhancement (use DTW only)
  python pipeline_with_pqg.py --audio performance.wav --score score.xml --output results/ --no-pqg

  # Specify score part
  python pipeline_with_pqg.py --audio violin.wav --score chorale.xml --output results/ --part 0

Notes:
  - PQG-A2SA enhancement is automatic if Layer 5 produces results
  - Falls back to DTW metrics if PQG-A2SA is unavailable
  - Backward compatible with original pipeline
        """
    )
    
    parser.add_argument("--audio", required=True, help="Path to audio file (.wav, .mp3, .flac)")
    parser.add_argument("--score", required=True, help="Path to score file (.xml, .mxl, .mid)")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--part", type=int, default=None, 
                       help="Score part index (0-based, auto-detected if not specified)")
    parser.add_argument("--config", help="Path to config.yaml (optional)")
    parser.add_argument("--no-pqg", action="store_true",
                       help="Disable PQG-A2SA enhancement (use DTW metrics only)")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create enhanced pipeline
    pipeline = EnhancedPipelineWithPQG(
        audio_path=args.audio,
        score_path=args.score,
        output_dir=args.output,
        config_path=args.config,
        score_part=args.part
    )
    
    # Set PQG enhancement flag
    pipeline.use_pqg_enhancement = not args.no_pqg
    
    # Run pipeline
    try:
        success = pipeline.run_pipeline()
        
        if success:
            print("\n" + "="*70)
            print("✅ PIPELINE COMPLETED SUCCESSFULLY")
            print("="*70)
            print(f"\nResults saved to: {args.output}")
            
            if pipeline.results.get('pqg_enhanced'):
                print("\n🎯 PQG-A2SA enhancement: ACTIVE")
                print("   Grading metrics use PQG-A2SA's precise onset/offset detection")
            else:
                print("\n📊 Using DTW-based metrics")
            
            sys.exit(0)
        else:
            print("\n❌ PIPELINE FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ PIPELINE ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
