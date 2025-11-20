#!/usr/bin/env python3
"""
Data Collector - Upstream Layer Output Collection
==================================================

Locates and loads all outputs from upstream layers:
- INPUT3_LAYER
- PROCESSING_LAYER
- EXTRACTION_LAYER
- TEMPORAL_ALIGNMENT (Blocks 0, 1, 2, 4)
- PQG-A2SA (optional)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class InferenceCoreInputs:
    """Complete collection of upstream layer outputs"""
    
    # Raw file paths
    input3_dir: Optional[Path] = None
    processing_dir: Optional[Path] = None
    extraction_dir: Optional[Path] = None
    temporal_alignment_dir: Optional[Path] = None
    pqg_a2sa_dir: Optional[Path] = None
    
    # Loaded data - PROCESSING_LAYER
    music_features: Optional[Dict] = None
    audio_segments: Optional[Dict] = None
    
    # Loaded data - EXTRACTION_LAYER
    performance_features: Optional[Dict] = None
    score_features: Optional[Dict] = None
    
    # Loaded data - TEMPORAL_ALIGNMENT
    scoregraph: Optional[Dict] = None
    transcription: Optional[Dict] = None
    alignment_results: Optional[Dict] = None
    time_map: Optional[List] = None
    beats: Optional[Dict] = None
    
    # Loaded data - PQG-A2SA (optional)
    pqg_alignment: Optional[Dict] = None
    
    # Metadata
    audio_path: Optional[Path] = None
    score_path: Optional[Path] = None
    output_base_dir: Optional[Path] = None
    
    # Data availability flags
    has_processing: bool = False
    has_extraction: bool = False
    has_temporal_alignment: bool = False
    has_pqg_a2sa: bool = False
    has_beat_detection: bool = False


class DataCollector:
    """Collects and loads all upstream layer outputs"""
    
    def __init__(self, output_base_dir: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize DataCollector
        
        Args:
            output_base_dir: Base output directory containing all layer outputs
            logger: Optional logger instance
        """
        self.output_base_dir = Path(output_base_dir)
        self.logger = logger or self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('DataCollector')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def collect_all_data(self) -> InferenceCoreInputs:
        """
        Collect all available upstream layer outputs
        
        Returns:
            InferenceCoreInputs with all loaded data
        """
        self.logger.info("=" * 70)
        self.logger.info("INFERENCE CORE - DATA COLLECTION")
        self.logger.info("=" * 70)
        self.logger.info(f"Base directory: {self.output_base_dir}")
        
        inputs = InferenceCoreInputs(output_base_dir=self.output_base_dir)
        
        # Locate layer directories
        self._locate_layer_directories(inputs)
        
        # Load data from each layer
        self._load_processing_layer_data(inputs)
        self._load_extraction_layer_data(inputs)
        self._load_temporal_alignment_data(inputs)
        self._load_pqg_a2sa_data(inputs)
        
        # Validate critical data
        self._validate_critical_data(inputs)
        
        # Print summary
        self._print_collection_summary(inputs)
        
        return inputs
    
    def _locate_layer_directories(self, inputs: InferenceCoreInputs):
        """Locate output directories for each layer"""
        self.logger.info("\n🔍 Locating layer output directories...")
        
        # Common directory patterns
        patterns = {
            'input3': ['01_input_layer', 'input_layer', 'INPUT3_LAYER'],
            'processing': ['02_processing_layer', 'processing_layer', 'PROCESSING_LAYER'],
            'extraction': ['03_extraction_layer', 'extraction_layer', 'EXTRACTION_LAYER', 'extracted'],
            'temporal': ['03_temporal_alignment', 'temporal_alignment', 'Temporal_Alignment'],
            'pqg_a2sa': ['05_pqg_a2sa', '04_pqg_a2sa', 'pqg_a2sa', 'PQG-A2SA']
        }
        
        for layer_name, possible_names in patterns.items():
            found = False
            for name in possible_names:
                candidate = self.output_base_dir / name
                if candidate.exists():
                    if layer_name == 'input3':
                        inputs.input3_dir = candidate
                    elif layer_name == 'processing':
                        inputs.processing_dir = candidate
                    elif layer_name == 'extraction':
                        inputs.extraction_dir = candidate
                    elif layer_name == 'temporal':
                        inputs.temporal_alignment_dir = candidate
                    elif layer_name == 'pqg_a2sa':
                        inputs.pqg_a2sa_dir = candidate
                    
                    self.logger.info(f"  ✓ Found {layer_name}: {candidate.name}")
                    found = True
                    break
            
            if not found and layer_name != 'pqg_a2sa':  # PQG-A2SA is optional
                self.logger.warning(f"  ⚠ {layer_name} directory not found")
    
    def _load_processing_layer_data(self, inputs: InferenceCoreInputs):
        """Load PROCESSING_LAYER outputs"""
        if not inputs.processing_dir:
            self.logger.warning("⚠ PROCESSING_LAYER directory not found - skipping")
            return
        
        self.logger.info("\n📂 Loading PROCESSING_LAYER data...")
        
        try:
            # Look for music features
            music_features_candidates = [
                inputs.processing_dir / 'processed' / 'music_features.json',
                inputs.processing_dir / 'music_features.json'
            ]
            
            for candidate in music_features_candidates:
                if candidate.exists():
                    with open(candidate, 'r') as f:
                        inputs.music_features = json.load(f)
                    self.logger.info(f"  ✓ Loaded music_features.json")
                    break
            
            # Look for audio segments
            segment_candidates = [
                inputs.processing_dir / 'processed' / 'audio_segments.json',
                inputs.processing_dir / 'audio_segments.json'
            ]
            
            for candidate in segment_candidates:
                if candidate.exists():
                    with open(candidate, 'r') as f:
                        inputs.audio_segments = json.load(f)
                    self.logger.info(f"  ✓ Loaded audio_segments.json")
                    break
            
            inputs.has_processing = (inputs.music_features is not None)
            
        except Exception as e:
            self.logger.error(f"  ✗ Error loading PROCESSING_LAYER data: {e}")
    
    def _load_extraction_layer_data(self, inputs: InferenceCoreInputs):
        """Load EXTRACTION_LAYER outputs"""
        if not inputs.extraction_dir:
            self.logger.warning("⚠ EXTRACTION_LAYER directory not found - skipping")
            return
        
        self.logger.info("\n📂 Loading EXTRACTION_LAYER data...")
        
        try:
            # Performance features
            perf_features_file = inputs.extraction_dir / 'performance_features.json'
            if perf_features_file.exists():
                with open(perf_features_file, 'r') as f:
                    inputs.performance_features = json.load(f)
                self.logger.info(f"  ✓ Loaded performance_features.json")
            
            # Score features
            score_features_file = inputs.extraction_dir / 'score_features.json'
            if score_features_file.exists():
                with open(score_features_file, 'r') as f:
                    inputs.score_features = json.load(f)
                self.logger.info(f"  ✓ Loaded score_features.json")
            
            inputs.has_extraction = (
                inputs.performance_features is not None and 
                inputs.score_features is not None
            )
            
        except Exception as e:
            self.logger.error(f"  ✗ Error loading EXTRACTION_LAYER data: {e}")
    
    def _load_temporal_alignment_data(self, inputs: InferenceCoreInputs):
        """Load TEMPORAL_ALIGNMENT outputs (Blocks 0, 1, 2, 4)"""
        self.logger.info("\n📂 Loading TEMPORAL_ALIGNMENT data...")
        
        try:
            # Block 0: ScoreGraph
            block0_candidates = []
            if inputs.temporal_alignment_dir:
                block0_candidates.extend([
                    inputs.temporal_alignment_dir / 'block_0_scoregraph' / 'scoregraph.json',
                    inputs.temporal_alignment_dir / 'scoregraph.json'
                ])
            # Fallback: search base directory
            block0_candidates.extend([
                self.output_base_dir / 'block0_scoregraph' / 'scoregraph.json',
                self.output_base_dir / 'scoregraph.json'
            ])
            
            for candidate in block0_candidates:
                if candidate.exists():
                    with open(candidate, 'r') as f:
                        inputs.scoregraph = json.load(f)
                    self.logger.info(f"  ✓ Block 0: Loaded scoregraph.json")
                    break
            
            # Block 1: Transcription
            block1_candidates = []
            if inputs.temporal_alignment_dir:
                block1_candidates.extend([
                    inputs.temporal_alignment_dir / 'block_1_amt' / 'transcription.json',
                    inputs.temporal_alignment_dir / 'transcription.json'
                ])
            # Fallback
            block1_candidates.extend([
                self.output_base_dir / 'block1_amt' / 'transcription.json',
                self.output_base_dir / 'transcription.json'
            ])
            
            for candidate in block1_candidates:
                if candidate.exists():
                    with open(candidate, 'r') as f:
                        inputs.transcription = json.load(f)
                    self.logger.info(f"  ✓ Block 1: Loaded transcription.json")
                    break
            
            # Block 2: Alignment Results
            block2_candidates = []
            if inputs.temporal_alignment_dir:
                block2_candidates.extend([
                    inputs.temporal_alignment_dir / 'alignment_output' / 'enhanced_alignment_complete.json',
                    inputs.temporal_alignment_dir / 'alignment_output' / 'alignment_results.json',
                    inputs.temporal_alignment_dir / 'block_2_alignment' / 'enhanced_alignment_complete.json',
                    inputs.temporal_alignment_dir / 'block_2_alignment' / 'alignment_results.json',
                    inputs.temporal_alignment_dir / 'alignment_results.json'
                ])
            # Fallback: Additional patterns for different naming conventions
            block2_candidates.extend([
                self.output_base_dir / 'block2_alignment_grading' / 'enhanced_alignment_complete.json',
                self.output_base_dir / 'block2_alignment' / 'enhanced_alignment_complete.json',
                self.output_base_dir / 'enhanced_alignment_complete.json'
            ])
            
            for candidate in block2_candidates:
                if candidate.exists():
                    with open(candidate, 'r') as f:
                        inputs.alignment_results = json.load(f)
                    self.logger.info(f"  ✓ Block 2: Loaded alignment_results.json")
                    break
            
            # Time map (often inside alignment results or separate)
            if inputs.alignment_results:
                if 'time_map' in inputs.alignment_results:
                    inputs.time_map = inputs.alignment_results['time_map']
                    self.logger.info(f"  ✓ Block 2: Extracted time_map from alignment_results")
                elif 'alignment_pairs' in inputs.alignment_results:
                    inputs.time_map = inputs.alignment_results['alignment_pairs']
                    self.logger.info(f"  ✓ Block 2: Extracted time_map from alignment_pairs")
            
            # Block 4: Beat Detection (optional)
            block4_candidates = []
            if inputs.temporal_alignment_dir:
                block4_candidates.extend([
                    inputs.temporal_alignment_dir / 'block_4_beats' / 'beats.json',
                    inputs.temporal_alignment_dir / 'beats.json'
                ])
            # Fallback
            block4_candidates.extend([
                self.output_base_dir / 'block4_beats' / 'beats.json',
                self.output_base_dir / 'beats.json'
            ])
            
            for candidate in block4_candidates:
                if candidate.exists():
                    with open(candidate, 'r') as f:
                        inputs.beats = json.load(f)
                    self.logger.info(f"  ✓ Block 4: Loaded beats.json")
                    inputs.has_beat_detection = True
                    break
            
            inputs.has_temporal_alignment = (
                inputs.scoregraph is not None and
                inputs.transcription is not None and
                inputs.alignment_results is not None
            )
            
        except Exception as e:
            self.logger.error(f"  ✗ Error loading TEMPORAL_ALIGNMENT data: {e}")
    
    def _load_pqg_a2sa_data(self, inputs: InferenceCoreInputs):
        """Load PQG-A2SA outputs (optional, for ensemble)"""
        if not inputs.pqg_a2sa_dir:
            self.logger.info("\n📂 PQG-A2SA data not available (optional for single instruments)")
            return
        
        self.logger.info("\n📂 Loading PQG-A2SA data...")
        
        try:
            # Look for PQG-A2SA alignment results
            pqg_candidates = [
                inputs.pqg_a2sa_dir / 'pqg_a2sa_results.json',
                inputs.pqg_a2sa_dir / 'pqg_alignment.json',
                inputs.pqg_a2sa_dir / 'note_level_alignment.json',
                inputs.pqg_a2sa_dir / 'results.json'
            ]
            
            for candidate in pqg_candidates:
                if candidate.exists():
                    with open(candidate, 'r') as f:
                        inputs.pqg_alignment = json.load(f)
                    self.logger.info(f"  ✓ Loaded PQG-A2SA alignment data")
                    inputs.has_pqg_a2sa = True
                    break
            
        except Exception as e:
            self.logger.error(f"  ✗ Error loading PQG-A2SA data: {e}")
    
    def _validate_critical_data(self, inputs: InferenceCoreInputs):
        """Validate that critical data is present"""
        self.logger.info("\n🔍 Validating critical data...")
        
        critical_data = {
            'ScoreGraph (Block 0)': inputs.scoregraph,
            'Transcription (Block 1)': inputs.transcription,
            'Alignment (Block 2)': inputs.alignment_results,
            'Music Features (Processing)': inputs.music_features,
            'Performance Features (Extraction)': inputs.performance_features,
            'Score Features (Extraction)': inputs.score_features
        }
        
        missing = []
        for name, data in critical_data.items():
            if data is None:
                missing.append(name)
                self.logger.warning(f"  ⚠ Missing: {name}")
            else:
                self.logger.info(f"  ✓ Present: {name}")
        
        if missing:
            self.logger.warning(f"\n⚠ Missing {len(missing)} critical data sources")
            self.logger.warning("  Some grading dimensions may be incomplete")
        else:
            self.logger.info("\n✓ All critical data sources present")
    
    def _print_collection_summary(self, inputs: InferenceCoreInputs):
        """Print summary of collected data"""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("DATA COLLECTION SUMMARY")
        self.logger.info("=" * 70)
        
        self.logger.info(f"PROCESSING_LAYER:      {'✓ Available' if inputs.has_processing else '✗ Missing'}")
        self.logger.info(f"EXTRACTION_LAYER:      {'✓ Available' if inputs.has_extraction else '✗ Missing'}")
        self.logger.info(f"TEMPORAL_ALIGNMENT:    {'✓ Available' if inputs.has_temporal_alignment else '✗ Missing'}")
        self.logger.info(f"Beat Detection (Opt):  {'✓ Available' if inputs.has_beat_detection else '○ Not available'}")
        self.logger.info(f"PQG-A2SA (Opt):        {'✓ Available' if inputs.has_pqg_a2sa else '○ Not available'}")
        
        self.logger.info("=" * 70 + "\n")


def main():
    """Test data collection"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_collector.py <output_directory>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    
    collector = DataCollector(output_dir)
    inputs = collector.collect_all_data()
    
    print("\n✅ Data collection complete!")
    print(f"   Processing: {inputs.has_processing}")
    print(f"   Extraction: {inputs.has_extraction}")
    print(f"   Temporal Alignment: {inputs.has_temporal_alignment}")
    print(f"   PQG-A2SA: {inputs.has_pqg_a2sa}")


if __name__ == '__main__':
    main()
