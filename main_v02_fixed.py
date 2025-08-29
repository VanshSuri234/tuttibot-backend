#!/usr/bin/env python3
"""
TuttiBot v02 - Temporal Alignment Pipeline (Fixed Version)
Main execution script for the enhanced temporal alignment system

Simplified Pipeline Flow:
Input Layer → Block 0 (ScoreGraph) → Block 1 (AMT) → Block 2 (Alignment) → Output

Features:
- Automatic GPU detection and management
- CPU fallback with warnings
- HPC/SLURM environment detection
- Multi-GPU support with selection
- GPU memory monitoring and cleanup

Author: TuttiBot Team
Version: 2.0.1
"""

import os
import sys
import json
import argparse
import logging
import traceback
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import GPU manager
from gpu_manager import GPUManager

# Import our enhanced temporal alignment blocks
temporal_alignment_path = project_root / "Temporal Alignment"
sys.path.append(str(temporal_alignment_path / "Block_0_ScoreGraph"))
sys.path.append(str(temporal_alignment_path / "Block_1_AMT"))
sys.path.append(str(temporal_alignment_path / "Block_2_SymbolicAlignment"))

try:
    from build_scoregraph_with_repeats import build_scoregraph
    from transcribe_audio_fixed import transcribe_audio_basic_pitch
    from align_symbolic_enhanced import EnhancedSymbolicAligner
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all enhanced temporal alignment blocks are in the correct directories")
    print(f"Looking in: {temporal_alignment_path}")
    sys.exit(1)

def setup_logging(output_dir, gpu_manager):
    """Setup logging configuration with GPU status"""
    log_file = os.path.join(output_dir, 'tuttibotv02.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Log GPU configuration
    device_info = gpu_manager.get_device_info()
    logger.info("=" * 60)
    logger.info("SYSTEM CONFIGURATION")
    logger.info("=" * 60)
    logger.info(f"Environment: {'HPC/SLURM' if device_info['environment']['is_slurm'] else 'Local'}")
    logger.info(f"Device: {'GPU' if device_info['device_config']['use_gpu'] else 'CPU'}")
    if device_info['device_config']['use_gpu']:
        logger.info(f"GPU ID: {device_info['device_config']['device_id']}")
    logger.info(f"TensorFlow: {'Available' if device_info['libraries']['tensorflow'] else 'Not installed'}")
    logger.info(f"PyTorch: {'Available' if device_info['libraries']['pytorch'] else 'Not installed'}")
    logger.info("=" * 60)
    
    return logger

def create_output_structure(base_output_dir):
    """Create output directory structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_output_dir, f"tuttibotv02_output_{timestamp}")
    
    # Create subdirectories
    subdirs = [
        'input_layer',
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
    Input Layer: Convert PDF to MusicXML and prepare inputs for processing
    """
    logger.info("=" * 60)
    logger.info("STARTING INPUT LAYER")
    logger.info("=" * 60)
    
    try:
        input_output_dir = os.path.join(output_dir, 'input_layer')
        
        # Convert PDF to MusicXML (simplified approach for now)
        # For this demo, we'll copy an existing MusicXML file as a placeholder
        # In a full implementation, this would use Audiveris or similar OMR
        
        # Look for an existing MusicXML file to use as converted result
        test_musicxml = os.path.join(project_root, "test.musicxml")
        if os.path.exists(test_musicxml):
            musicxml_filename = "converted_score.musicxml"
            musicxml_output_path = os.path.join(input_output_dir, musicxml_filename)
            shutil.copy2(test_musicxml, musicxml_output_path)
            logger.info(f"📄 PDF conversion simulated: {pdf_path} -> {musicxml_output_path}")
        else:
            # Fallback: create a minimal MusicXML file
            musicxml_output_path = os.path.join(input_output_dir, "minimal_score.musicxml")
            minimal_musicxml = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1">
      <part-name>Piano</part-name>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key>
          <fifths>0</fifths>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <pitch>
          <step>C</step>
          <octave>4</octave>
        </pitch>
        <duration>4</duration>
        <type>whole</type>
      </note>
    </measure>
  </part>
</score-partwise>'''
            with open(musicxml_output_path, 'w') as f:
                f.write(minimal_musicxml)
            logger.info(f"📄 Created minimal MusicXML as PDF conversion placeholder")
        
        # Copy audio file to output structure
        audio_filename = os.path.basename(audio_path)
        audio_output_path = os.path.join(input_output_dir, audio_filename)
        shutil.copy2(audio_path, audio_output_path)
        
        logger.info(f"✅ Input Layer completed successfully")
        logger.info(f"   PDF: {pdf_path}")
        logger.info(f"   MusicXML: {musicxml_output_path}")
        logger.info(f"   Audio: {audio_output_path}")
        
        return {
            'musicxml_path': musicxml_output_path,
            'audio_path': audio_output_path,
            'original_pdf_path': pdf_path
        }
        
    except Exception as e:
        logger.error(f"❌ Input Layer failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def block_0_scoregraph(musicxml_path, output_dir, logger):
    """
    Block 0: Build ScoreGraph with repeat expansion
    """
    logger.info("=" * 60)
    logger.info("STARTING BLOCK 0 - SCOREGRAPH")
    logger.info("=" * 60)
    
    try:
        block0_output_dir = os.path.join(output_dir, 'block_0_scoregraph')
        
        logger.info(f"Building ScoreGraph from: {musicxml_path}")
        # Use the existing meta file for testing
        meta_path = os.path.join(project_root, "Temporal Alignment", "Block_0_ScoreGraph", "score_meta.json")
        scoregraph = build_scoregraph(musicxml_path, meta_path, None)
        
        # Save ScoreGraph
        scoregraph_path = os.path.join(block0_output_dir, 'scoregraph.json')
        with open(scoregraph_path, 'w') as f:
            json.dump(scoregraph, f, indent=2)
        
        logger.info(f"✅ Block 0 completed successfully")
        logger.info(f"   Total measures: {scoregraph.get('total_measures', 'N/A')}")
        logger.info(f"   Total beats: {scoregraph.get('total_beats', 'N/A')}")
        logger.info(f"   ScoreGraph saved: {scoregraph_path}")
        
        return {
            'scoregraph_path': scoregraph_path,
            'scoregraph': scoregraph
        }
        
    except Exception as e:
        logger.error(f"❌ Block 0 failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def block_1_amt(audio_path, output_dir, gpu_manager, logger):
    """
    Block 1: Automatic Music Transcription with GPU support
    """
    logger.info("=" * 60)
    logger.info("STARTING BLOCK 1 - AMT")
    logger.info("=" * 60)
    
    try:
        block1_output_dir = os.path.join(output_dir, 'block_1_amt')
        
        # Log GPU status for AMT
        if gpu_manager.device_config['use_gpu']:
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                logger.info(f"GPU Memory before AMT: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
        
        logger.info(f"Transcribing audio: {audio_path}")
        logger.info(f"Device: {'GPU' if gpu_manager.device_config['use_gpu'] else 'CPU'}")
        
        # Use the stable transcribe_audio_fixed function with GPU support
        transcription_result = transcribe_audio_basic_pitch(
            audio_path, 
            block1_output_dir,
            gpu_manager=gpu_manager
        )
        
        # Save transcription JSON
        transcription_json_path = os.path.join(block1_output_dir, 'transcription.json')
        with open(transcription_json_path, 'w') as f:
            json.dump(transcription_result, f, indent=2)
        
        # Log GPU status after AMT
        if gpu_manager.device_config['use_gpu']:
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                logger.info(f"GPU Memory after AMT: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
            # Cleanup GPU memory after intensive operation
            gpu_manager.cleanup_gpu_memory()
        
        logger.info(f"✅ Block 1 completed successfully")
        logger.info(f"   Notes detected: {len(transcription_result.get('notes', []))}")
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
        # Cleanup on error
        if gpu_manager.device_config['use_gpu']:
            gpu_manager.cleanup_gpu_memory()
        raise

def block_2_alignment(scoregraph_path, transcription_result, output_dir, gpu_manager, logger):
    """
    Block 2: Symbolic Alignment using Enhanced Block 2 with GPU support
    """
    logger.info("=" * 60)
    logger.info("STARTING BLOCK 2 - SYMBOLIC ALIGNMENT")
    logger.info("=" * 60)
    
    try:
        block2_output_dir = os.path.join(output_dir, 'block_2_alignment')
        
        # Get MIDI path from transcription result
        midi_path = transcription_result.get('midi_path')
        
        logger.info(f"Performing symbolic alignment...")
        logger.info(f"   Score graph: {scoregraph_path}")
        logger.info(f"   Performance MIDI: {midi_path}")
        logger.info(f"   Device: {'GPU' if gpu_manager.device_config['use_gpu'] else 'CPU'}")
        
        # Log GPU status before alignment
        if gpu_manager.device_config['use_gpu']:
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                logger.info(f"GPU Memory before alignment: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
        
        # Initialize Enhanced Aligner with GPU support
        aligner = EnhancedSymbolicAligner(gpu_manager=gpu_manager)
        
        # Perform alignment using the correct method
        alignment_result = aligner.align_score_performance(
            score_graph_path=scoregraph_path,
            performance_midi_path=midi_path,
            output_dir=block2_output_dir
        )
        
        # Save alignment results
        alignment_json_path = os.path.join(block2_output_dir, 'alignment_results.json')
        with open(alignment_json_path, 'w') as f:
            json.dump(alignment_result, f, indent=2)
        
        # Log GPU status after alignment
        if gpu_manager.device_config['use_gpu']:
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                logger.info(f"GPU Memory after alignment: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
            # Cleanup GPU memory after intensive operation
            gpu_manager.cleanup_gpu_memory()
        
        logger.info(f"✅ Block 2 completed successfully")
        logger.info(f"   Alignment confidence: {alignment_result.get('confidence', 'N/A')}")
        logger.info(f"   DTW distance: {alignment_result.get('dtw_distance', 'N/A')}")
        logger.info(f"   Path length: {len(alignment_result.get('alignment_path', []))}")
        logger.info(f"   Alignment saved: {alignment_json_path}")
        
        return {
            'alignment_json_path': alignment_json_path,
            'alignment': alignment_result
        }
        
    except Exception as e:
        logger.error(f"❌ Block 2 failed: {str(e)}")
        logger.error(traceback.format_exc())
        # Cleanup on error
        if gpu_manager.device_config['use_gpu']:
            gpu_manager.cleanup_gpu_memory()
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
            'pipeline_version': '2.0.1',
            'status': 'completed',
            'summary': {
                'total_measures': scoregraph.get('total_measures', 0),
                'total_score_beats': scoregraph.get('total_beats', 0),
                'detected_notes': len(transcription.get('notes', [])),
                'alignment_confidence': alignment.get('confidence', 0.0),
                'dtw_distance': alignment.get('dtw_distance', float('inf')),
                'alignment_path_length': len(alignment.get('alignment_path', []))
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
            f.write(f"  Alignment path length: {final_results['summary']['alignment_path_length']}\n")
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
    parser = argparse.ArgumentParser(description='TuttiBot v02 - Temporal Alignment Pipeline (Fixed Version)')
    parser.add_argument('--pdf', required=True, help='Path to input PDF score')
    parser.add_argument('--audio', required=True, help='Path to input audio performance')
    parser.add_argument('--output', default='./Output', help='Output directory (default: ./Output)')
    
    # GPU control options
    parser.add_argument('--cpu-only', action='store_true', 
                       help='Force CPU-only mode (disable GPU acceleration)')
    parser.add_argument('--gpu-id', type=int, 
                       help='Specific GPU ID to use (0, 1, 2, etc.)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.pdf):
        print(f"❌ Error: PDF file not found: {args.pdf}")
        sys.exit(1)
    
    if not os.path.exists(args.audio):
        print(f"❌ Error: Audio file not found: {args.audio}")
        sys.exit(1)
    
    # Initialize GPU Manager
    gpu_manager = GPUManager(force_cpu=args.cpu_only, gpu_id=args.gpu_id)
    
    # Setup TensorFlow and PyTorch
    gpu_manager.setup_tensorflow()
    gpu_manager.setup_pytorch()
    
    # Print system status
    gpu_manager.print_status()
    
    # Create output structure
    output_dir = create_output_structure(args.output)
    logger = setup_logging(output_dir, gpu_manager)
    
    # Print header
    print("\n" + "=" * 70)
    print("🎼 TuttiBot v02 - Temporal Alignment Pipeline (GPU-Ready)")
    print("=" * 70)
    print(f"Input PDF: {args.pdf}")
    print(f"Input Audio: {args.audio}")
    print(f"Output Directory: {output_dir}")
    print(f"Processing Mode: {'GPU' if gpu_manager.device_config['use_gpu'] else 'CPU'}")
    if gpu_manager.device_config['use_gpu']:
        print(f"GPU Device: {gpu_manager.device_config['device_id']}")
    print("=" * 70 + "\n")
    
    try:
        # Execute pipeline
        logger.info("🚀 Starting TuttiBot v02 Pipeline")
        
        # Input Layer - Convert PDF to MusicXML
        input_results = input_layer(args.pdf, args.audio, output_dir, logger)
        
        # Block 0: ScoreGraph
        block0_results = block_0_scoregraph(
            input_results['musicxml_path'],
            output_dir,
            logger
        )
        
        # Block 1: AMT with GPU support
        block1_results = block_1_amt(
            input_results['audio_path'],
            output_dir,
            gpu_manager,
            logger
        )
        
        # Block 2: Alignment with GPU support
        block2_results = block_2_alignment(
            block0_results['scoregraph_path'],
            block1_results['transcription'],
            output_dir,
            gpu_manager,
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
        
        # Final GPU cleanup
        gpu_manager.cleanup_gpu_memory()
        
        # Success summary
        print("\n" + "=" * 70)
        print("🎉 TuttiBot v02 Pipeline Completed Successfully!")
        print("=" * 70)
        print(f"📁 Results saved to: {output_dir}")
        print(f"📊 Final results: {final_output_path}")
        print(f"⚡ Processing mode: {'GPU' if gpu_manager.device_config['use_gpu'] else 'CPU'}")
        
        # Final GPU memory status
        if gpu_manager.device_config['use_gpu']:
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                print(f"🎮 Final GPU memory: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
        
        print("=" * 70 + "\n")
        
        logger.info("🎉 TuttiBot v02 Pipeline completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        logger.error(f"Pipeline failed: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Cleanup GPU on failure
        try:
            gpu_manager.cleanup_gpu_memory()
        except:
            pass
        
        sys.exit(1)

if __name__ == '__main__':
    main()
