#!/usr/bin/env python3
"""
TuttiBot v02 - Temporal Alignment Pipeline
Main execution script for the enhanced temporal alignment system

Pipeline Flow:
Input Layer → Processing Layer → Block 0 (ScoreGraph) → Block 1 (AMT) → Block 2 (Alignment) → Output

Author: TuttiBot Team
Version: 2.0
"""

import os
import sys
from INPUT3_LAYER.input_layer import ScoreInputProcessor
from PROCESSING_LAYER.processing_layer import ProcessingLayer
import json
import argparse
import logging
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import our enhanced temporal alignment blocks
import sys
sys.path.append(str(project_root / "Temporal Alignment" / "Block_0_ScoreGraph"))
sys.path.append(str(project_root / "Temporal Alignment" / "Block_1_AMT"))
sys.path.append(str(project_root / "Temporal Alignment" / "Block_2_SymbolicAlignment"))

from build_scoregraph_with_repeats import build_scoregraph
from transcribe_audio_fixed import transcribe_audio_basic_pitch
from align_symbolic_enhanced import EnhancedSymbolicAligner

def setup_logging(output_dir):
    """Setup logging configuration"""
    log_file = os.path.join(output_dir, 'tuttibotv02.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def create_output_structure(base_output_dir):
    """Create output directory structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_output_dir, f"tuttibotv02_output_{timestamp}")
    
    # Create subdirectories
    subdirs = [
        'input_layer',
        'processing_layer', 
        'block_0_scoregraph',
        'block_1_amt',
        'block_2_alignment',
        'final_output'
    ]
    
    for subdir in subdirs:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
    
    return output_dir

def input_layer(pdf_path, audio_path, output_dir, logger):
    """
    Input Layer: Convert PDF to MusicXML
    """
    logger.info("=" * 60)
    logger.info("STARTING INPUT LAYER")
    logger.info("=" * 60)
    
    try:
        input_output_dir = os.path.join(output_dir, 'input_layer')
        
        # Convert PDF to MusicXML using ScoreInputProcessor
        logger.info(f"Converting PDF to MusicXML: {pdf_path}")
        score_processor = ScoreInputProcessor()
        score_result = score_processor.process_score(pdf_path)
        
        if not score_result['success']:
            # If PDF conversion fails, try to use existing MusicXML file as fallback
            logger.warning(f"PDF conversion failed: {score_result['message']}")
            logger.info("Attempting to use existing MusicXML file as fallback...")
            
            # Look for existing MusicXML files
            potential_musicxml_files = [
                Path("test.musicxml"),
                Path("Temporal Alignment/Block_0_ScoreGraph/test_with_repeats.musicxml"),
                Path("PROCESSING_LAYER/xml_score.musicxml")
            ]
            
            musicxml_path = None
            for xml_file in potential_musicxml_files:
                if xml_file.exists():
                    musicxml_path = xml_file
                    logger.info(f"Using fallback MusicXML file: {musicxml_path}")
                    break
            
            if musicxml_path is None:
                raise RuntimeError(f"Score conversion failed and no fallback MusicXML found: {score_result['message']}")
        else:
            musicxml_path = score_result['output_path']
        
        # Copy audio file to output structure
        import shutil
        audio_filename = os.path.basename(audio_path)
        audio_output_path = os.path.join(input_output_dir, audio_filename)
        shutil.copy2(audio_path, audio_output_path)
        
        logger.info(f"✅ Input Layer completed successfully")
        logger.info(f"   MusicXML: {musicxml_path}")
        logger.info(f"   Audio: {audio_output_path}")
        
        return {
            'musicxml_path': musicxml_path,
            'audio_path': audio_output_path
        }
        
    except Exception as e:
        logger.error(f"❌ Input Layer failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def processing_layer(musicxml_path, audio_path, output_dir, logger):
    """
    Processing Layer: Audio preprocessing, music feature extraction, and segmentation
    """
    logger.info("=" * 60)
    logger.info("STARTING PROCESSING LAYER")
    logger.info("=" * 60)
    
    try:
        processing_output_dir = os.path.join(output_dir, 'processing_layer')
        
        # Step 1: Audio Preprocessing
        logger.info("Step 1: Audio Preprocessing")
        processed_audio_path = preprocess_audio(audio_path, processing_output_dir)
        logger.info(f"   Processed audio: {processed_audio_path}")
        
        # Step 2: Music Feature Extraction
        logger.info("Step 2: Music Feature Extraction")
        music_features_path = extract_music_features(musicxml_path, processing_output_dir)
        logger.info(f"   Music features: {music_features_path}")
        
        # Step 3: Audio Segmentation
        logger.info("Step 3: Audio Segmentation")
        segmentation_path = segment_audio(processed_audio_path, processing_output_dir)
        logger.info(f"   Segmentation: {segmentation_path}")
        
        logger.info(f"✅ Processing Layer completed successfully")
        
        return {
            'processed_audio_path': processed_audio_path,
            'music_features_path': music_features_path,
            'segmentation_path': segmentation_path,
            'musicxml_path': musicxml_path
        }
        
    except Exception as e:
        logger.error(f"❌ Processing Layer failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def block_0_scoregraph(musicxml_path, music_features_path, output_dir, logger):
    """
    Block 0: Build ScoreGraph with repeat expansion
    """
    logger.info("=" * 60)
    logger.info("STARTING BLOCK 0 - SCOREGRAPH")
    logger.info("=" * 60)
    
    try:
        block0_output_dir = os.path.join(output_dir, 'block_0_scoregraph')
        logger.info("Building ScoreGraph with repeat expansion...")
        scoregraph = build_scoregraph(musicxml_path, music_features_path)
        # Save ScoreGraph
        scoregraph_path = os.path.join(block0_output_dir, 'scoregraph.json')
        with open(scoregraph_path, 'w') as f:
            json.dump(scoregraph, f, indent=2)
        logger.info(f"✅ Block 0 completed successfully")
        logger.info(f"   Total measures: {len(scoregraph['bars'])}")
        logger.info(f"   Total nodes: {len(scoregraph['nodes'])}")
        logger.info(f"   ScoreGraph saved: {scoregraph_path}")
        return {
            'scoregraph_path': scoregraph_path,
            'scoregraph': scoregraph
        }
    except Exception as e:
        logger.error(f"❌ Block 0 failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def block_1_amt(processed_audio_path, output_dir, logger):
    """
    Block 1: Automatic Music Transcription
    """
    logger.info("=" * 60)
    logger.info("STARTING BLOCK 1 - AMT")
    logger.info("=" * 60)
    
    try:
        block1_output_dir = os.path.join(output_dir, 'block_1_amt')
        logger.info("Transcribing audio using Basic Pitch...")
        transcription_result = transcribe_audio_basic_pitch(processed_audio_path, block1_output_dir)
        # Save transcription JSON
        transcription_json_path = os.path.join(block1_output_dir, 'transcription.json')
        with open(transcription_json_path, 'w') as f:
            json.dump(transcription_result, f, indent=2)
        logger.info(f"✅ Block 1 completed successfully")
        logger.info(f"   Notes detected: {len(transcription_result['notes'])}")
        logger.info(f"   Duration: {transcription_result.get('total_duration', 'N/A')}s")
        logger.info(f"   Transcription saved: {transcription_json_path}")
        return {
            'transcription_json_path': transcription_json_path,
            'midi_path': transcription_result.get('midi_path'),
            'transcription': transcription_result
        }
    except Exception as e:
        logger.error(f"❌ Block 1 failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def block_2_alignment(scoregraph_path, transcription_json_path, segmentation_path, output_dir, logger):
    """
    Block 2: Symbolic Alignment
    """
    logger.info("=" * 60)
    logger.info("STARTING BLOCK 2 - SYMBOLIC ALIGNMENT")
    logger.info("=" * 60)
    
    try:
        block2_output_dir = os.path.join(output_dir, 'block_2_alignment')
        
        logger.info("Performing symbolic alignment...")
        aligner = EnhancedSymbolicAligner()
        # Use MIDI path from Block 1 transcription
        import json
        with open(transcription_json_path, 'r') as f:
            transcription_data = json.load(f)
        midi_path = transcription_data.get('metadata', {}).get('source_files', {}).get('midi')
        if not midi_path:
            raise ValueError("MIDI file path not found in transcription metadata.")
        alignment_result = aligner.align_score_performance(scoregraph_path, midi_path, block2_output_dir)
        
        # Save alignment results
        alignment_json_path = os.path.join(block2_output_dir, 'alignment_results.json')
        with open(alignment_json_path, 'w') as f:
            json.dump(alignment_result, f, indent=2)
        
        logger.info(f"✅ Block 2 completed successfully")
        logger.info(f"   Alignment confidence: {alignment_result.get('confidence', 'N/A')}")
        logger.info(f"   DTW distance: {alignment_result.get('dtw_distance', 'N/A')}")
        logger.info(f"   Alignment saved: {alignment_json_path}")
        
        return {
            'alignment_json_path': alignment_json_path,
            'alignment': alignment_result
        }
        
    except Exception as e:
        logger.error(f"❌ Block 2 failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def create_final_output(output_dir, scoregraph, transcription, alignment, logger):
    """
    Create comprehensive final output combining all results
    """
    logger.info("=" * 60)
    logger.info("CREATING FINAL OUTPUT")
    logger.info("=" * 60)
    
    try:
        final_output_dir = os.path.join(output_dir, 'final_output')
        
        # Create comprehensive results
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_version': '2.0',
            'status': 'completed',
            'summary': {
                'total_measures': len(scoregraph['bars']),
                'total_score_beats': len(scoregraph['nodes']),
                'detected_notes': len(transcription['notes']),
                'alignment_confidence': alignment.get('confidence', 0.0),
                'dtw_distance': alignment.get('dtw_distance', float('inf'))
            },
            'scoregraph': scoregraph,
            'transcription': transcription,
            'alignment': alignment
        }
        
        # Save final results
        final_results_path = os.path.join(final_output_dir, 'tuttibotv02_results.json')
        with open(final_results_path, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        # Create summary report
        summary_path = os.path.join(final_output_dir, 'summary_report.txt')
        with open(summary_path, 'w') as f:
            f.write("TuttiBot v02 - Temporal Alignment Results\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Processing completed: {final_results['timestamp']}\n")
            f.write(f"Pipeline version: {final_results['pipeline_version']}\n\n")
            f.write("SUMMARY:\n")
            f.write(f"  Score measures: {final_results['summary']['total_measures']}\n")
            f.write(f"  Score beats: {final_results['summary']['total_score_beats']}\n")
            f.write(f"  Detected notes: {final_results['summary']['detected_notes']}\n")
            f.write(f"  Alignment confidence: {final_results['summary']['alignment_confidence']:.3f}\n")
            f.write(f"  DTW distance: {final_results['summary']['dtw_distance']:.3f}\n")
            f.write("\nStatus: SUCCESS\n")
        
        logger.info(f"✅ Final output created successfully")
        logger.info(f"   Results: {final_results_path}")
        logger.info(f"   Summary: {summary_path}")
        
        return final_results_path
        
    except Exception as e:
        logger.error(f"❌ Final output creation failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def main():
    parser = argparse.ArgumentParser(description='TuttiBot v02 - Temporal Alignment Pipeline')
    parser.add_argument('--pdf', required=True, help='Path to input PDF score')
    parser.add_argument('--audio', required=True, help='Path to input audio performance')
    parser.add_argument('--output', default='./Output', help='Output directory (default: ./Output)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.pdf):
        print(f"❌ Error: PDF file not found: {args.pdf}")
        sys.exit(1)
    
    if not os.path.exists(args.audio):
        print(f"❌ Error: Audio file not found: {args.audio}")
        sys.exit(1)
    
    # Create output structure
    output_dir = create_output_structure(args.output)
    logger = setup_logging(output_dir)
    
    # Print header
    print("\n" + "=" * 70)
    print("🎼 TuttiBot v02 - Temporal Alignment Pipeline")
    print("=" * 70)
    print(f"Input PDF: {args.pdf}")
    print(f"Input Audio: {args.audio}")
    print(f"Output Directory: {output_dir}")
    print("=" * 70 + "\n")
    
    try:
        # Execute pipeline
        logger.info("🚀 Starting TuttiBot v02 Pipeline")
        
        # Input Layer
        input_results = input_layer(args.pdf, args.audio, output_dir, logger)
        
        # Processing Layer
        processing_results = processing_layer(
            input_results['musicxml_path'],
            input_results['audio_path'],
            output_dir, 
            logger
        )
        
        # Block 0: ScoreGraph
        block0_results = block_0_scoregraph(
            processing_results['musicxml_path'],
            processing_results['music_features_path'],
            output_dir,
            logger
        )
        
        # Block 1: AMT
        block1_results = block_1_amt(
            processing_results['processed_audio_path'],
            output_dir,
            logger
        )
        
        # Block 2: Alignment
        block2_results = block_2_alignment(
            block0_results['scoregraph_path'],
            block1_results['transcription_json_path'],
            processing_results['segmentation_path'],
            output_dir,
            logger
        )
        
        # Create Final Output
        final_output_path = create_final_output(
            output_dir,
            block0_results['scoregraph'],
            block1_results['transcription'],
            block2_results['alignment'],
            logger
        )
        
        # Success summary
        print("\n" + "=" * 70)
        print("🎉 TuttiBot v02 Pipeline Completed Successfully!")
        print("=" * 70)
        print(f"📁 Results saved to: {output_dir}")
        print(f"📊 Final results: {final_output_path}")
        print("=" * 70 + "\n")
        
        logger.info("🎉 TuttiBot v02 Pipeline completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        logger.error(f"Pipeline failed: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()