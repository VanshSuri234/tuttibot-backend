#!/usr/bin/env python3
"""
TuttiBot Hybrid Pipeline - Best of Both Worlds
Combines efficient INPUT3_LAYER + PROCESSING_LAYER with advanced Temporal Alignment

Pipeline Flow:
INPUT3_LAYER → PROCESSING_LAYER → Temporal Alignment (Block 0 → Block 1 → Block 2)

Features:
- Fast direct Audiveris CLI (from main.py)
- Efficient audio/music processing (from main.py) 
- Advanced temporal alignment (from main_v02_fixed.py)
- Automatic GPU detection and management
- CPU fallback with warnings
- HPC/SLURM environment detection

Author: TuttiBot Team
Version: 3.0.0 (Hybrid)
"""

import os
import sys
import json
import argparse
import logging
import traceback
import shutil
import glob
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Add layer paths
sys.path.insert(0, str(project_root / "INPUT3_LAYER"))
sys.path.insert(0, str(project_root / "PROCESSING_LAYER"))

# Import GPU manager
from gpu_manager import GPUManager

# Import temporal alignment blocks
temporal_alignment_path = project_root / "Temporal Alignment"
sys.path.append(str(temporal_alignment_path / "Block_0_ScoreGraph"))
sys.path.append(str(temporal_alignment_path / "Block_1_AMT"))
sys.path.append(str(temporal_alignment_path / "Block_2_SymbolicAlignment"))

try:
    from build_scoregraph_with_repeats import build_scoregraph
    from transcribe_audio_fixed import transcribe_audio_basic_pitch
    from align_symbolic_enhanced import EnhancedSymbolicAligner
except ImportError as e:
    print(f"❌ Temporal alignment import error: {e}")
    print("Please ensure all enhanced temporal alignment blocks are in the correct directories")
    print(f"Looking in: {temporal_alignment_path}")
    sys.exit(1)

def setup_logging(output_dir, gpu_manager):
    """Setup logging configuration with GPU status"""
    log_file = os.path.join(output_dir, 'tuttibot_hybrid.log')
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
    output_dir = os.path.join(base_output_dir, f"tuttibot_hybrid_{timestamp}")
    
    # Create subdirectories
    subdirs = [
        '01_input_layer',
        '02_processing_layer', 
        '03_temporal_alignment',
        '04_final_results'
    ]
    
    for subdir in subdirs:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
    
    return output_dir

def run_input3_layer(audio_path: str, score_path: str, output_dir: str, logger):
    """Run INPUT3_LAYER to standardize inputs using direct Audiveris CLI"""
    logger.info("=" * 60)
    logger.info("STEP 1: INPUT3_LAYER (FAST DIRECT AUDIVERIS)")
    logger.info("=" * 60)
    
    try:
        from input_layer import MusicInputLayer
        
        input_layer = MusicInputLayer()
        results = input_layer.process_inputs(audio_path, score_path)
        
        if not results['overall_success']:
            raise Exception(f"Input layer failed:\n"
                          f"  Audio: {results['audio']['message']}\n"
                          f"  Score: {results['score']['message']}")
        
        # Setup output directories
        input_output_dir = os.path.join(output_dir, '01_input_layer')
        
        # Copy results to our output directory
        audio_output = os.path.join(input_output_dir, "standardized_audio.wav")
        score_output = os.path.join(input_output_dir, "standardized_score.xml")
        
        shutil.copy2(results['audio']['output_path'], audio_output)
        shutil.copy2(results['score']['output_path'], score_output)
        
        # Save metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'original_audio': str(Path(audio_path).name),
            'original_score': str(Path(score_path).name),
            'audio_converted': results['audio']['converted'],
            'score_converted': results['score']['converted'],
            'audio_message': results['audio']['message'],
            'score_message': results['score']['message']
        }
        
        metadata_path = os.path.join(input_output_dir, "input_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Audio processed: {results['audio']['message']}")
        logger.info(f"✅ Score processed: {results['score']['message']}")
        logger.info(f"📁 Results saved to: {input_output_dir}")
        
        return {
            'audio_path': audio_output,
            'score_path': score_output,
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"❌ INPUT3_LAYER failed: {e}")
        raise

def run_processing_layer(audio_path: str, score_path: str, output_dir: str, logger):
    """Run PROCESSING_LAYER for audio cleaning and music analysis"""
    logger.info("=" * 60)
    logger.info("STEP 2: PROCESSING_LAYER (EFFICIENT AUDIO/MUSIC PROCESSING)")
    logger.info("=" * 60)
    
    try:
        from processing_layer import ProcessingLayer
        
        # Initialize with our output directory
        processing_output_dir = os.path.join(output_dir, '02_processing_layer')
        processor = ProcessingLayer(shared_output_dir=processing_output_dir)
        
        # Process audio and score
        result = processor.process(audio_path, score_path)
        
        if not result:
            raise Exception("Processing failed: No result returned")
        
        # Save processing metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'processed_audio_path': result.processed_audio_path,
            'audio_segments_count': len(result.audio_segments),
            'music_features_count': len(result.music_features.notes) if hasattr(result.music_features, 'notes') else 0,
            'processing_metadata': result.processing_metadata
        }
        
        metadata_path = os.path.join(processing_output_dir, "processing_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"✅ Audio cleaned and segmented: {len(result.audio_segments)} segments")
        logger.info(f"✅ Music features extracted: {metadata['music_features_count']} features")
        logger.info(f"📁 Results saved to: {processing_output_dir}")
        
        return {
            'processed_audio_path': result.processed_audio_path,
            'audio_segments': result.audio_segments,
            'music_features': result.music_features,
            'processing_result': result,
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"❌ PROCESSING_LAYER failed: {e}")
        raise

def run_temporal_alignment(score_path: str, audio_path: str, output_dir: str, gpu_manager, logger):
    """Run temporal alignment blocks (Block 0 → Block 1 → Block 2)"""
    logger.info("=" * 60)
    logger.info("STEP 3: TEMPORAL ALIGNMENT (ADVANCED GPU-ACCELERATED)")
    logger.info("=" * 60)
    
    try:
        alignment_output_dir = os.path.join(output_dir, '03_temporal_alignment')
        
        # Create subdirectories for each block
        block0_dir = os.path.join(alignment_output_dir, 'block_0_scoregraph')
        block1_dir = os.path.join(alignment_output_dir, 'block_1_amt') 
        block2_dir = os.path.join(alignment_output_dir, 'block_2_alignment')
        
        for dir_path in [block0_dir, block1_dir, block2_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        logger.info("🔄 Block 0: Building ScoreGraph...")
        
        # Block 0: ScoreGraph
        logger.info(f"Building ScoreGraph from: {score_path}")
        meta_path = os.path.join(project_root, "Temporal Alignment", "Block_0_ScoreGraph", "score_meta.json")
        scoregraph = build_scoregraph(score_path, meta_path, None)
        
        scoregraph_path = os.path.join(block0_dir, 'scoregraph.json')
        with open(scoregraph_path, 'w') as f:
            json.dump(scoregraph, f, indent=2)
        
        logger.info(f"✅ Block 0 completed: {len(scoregraph.get('nodes', []))} nodes")
        
        # Block 1: AMT with GPU support
        logger.info("🔄 Block 1: Automatic Music Transcription...")
        
        if gpu_manager.device_config['use_gpu']:
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                logger.info(f"GPU Memory before AMT: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
        
        transcription_result = transcribe_audio_basic_pitch(
            audio_path,
            block1_dir,
            gpu_manager=gpu_manager
        )
        
        transcription_json_path = os.path.join(block1_dir, 'transcription.json')
        with open(transcription_json_path, 'w') as f:
            json.dump(transcription_result, f, indent=2)
        
        if gpu_manager.device_config['use_gpu']:
            gpu_manager.cleanup_gpu_memory()
            
        logger.info(f"✅ Block 1 completed: {len(transcription_result.get('notes', []))} notes detected")
        
        # Block 2: Symbolic Alignment
        logger.info("🔄 Block 2: Symbolic Alignment...")
        
        midi_path = transcription_result.get('midi_path')
        logger.info(f"Using MIDI: {midi_path}")
        
        if gpu_manager.device_config['use_gpu']:
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                logger.info(f"GPU Memory before alignment: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
        
        aligner = EnhancedSymbolicAligner(gpu_manager=gpu_manager)
        alignment_result = aligner.align_score_performance(
            score_graph_path=scoregraph_path,
            performance_midi_path=midi_path,
            output_dir=block2_dir
        )
        
        alignment_json_path = os.path.join(block2_dir, 'alignment_results.json')
        with open(alignment_json_path, 'w') as f:
            json.dump(alignment_result, f, indent=2)
        
        if gpu_manager.device_config['use_gpu']:
            gpu_manager.cleanup_gpu_memory()
        
        # Extract metrics
        alignment_data = alignment_result.get('alignment', {})
        confidence = alignment_data.get('confidence', 0.0)
        dtw_distance = alignment_data.get('dtw_distance', float('inf'))
        
        logger.info(f"✅ Block 2 completed: confidence={confidence:.3f}, dtw_distance={dtw_distance:.3f}")
        logger.info(f"📁 Temporal alignment results saved to: {alignment_output_dir}")
        
        return {
            'scoregraph': scoregraph,
            'transcription': transcription_result,
            'alignment': alignment_result,
            'scoregraph_path': scoregraph_path,
            'transcription_path': transcription_json_path,
            'alignment_path': alignment_json_path
        }
        
    except Exception as e:
        logger.error(f"❌ TEMPORAL_ALIGNMENT failed: {e}")
        if gpu_manager.device_config['use_gpu']:
            gpu_manager.cleanup_gpu_memory()
        raise

def create_final_results(input_results, processing_results, alignment_results, output_dir, logger):
    """Create comprehensive final results"""
    logger.info("=" * 60)
    logger.info("STEP 4: CREATING FINAL RESULTS")
    logger.info("=" * 60)
    
    try:
        final_output_dir = os.path.join(output_dir, '04_final_results')
        
        # Extract key metrics
        alignment_data = alignment_results['alignment'].get('alignment', {})
        confidence = alignment_data.get('confidence', 0.0)
        dtw_distance = alignment_data.get('dtw_distance', float('inf'))
        
        # Create comprehensive results
        final_results = {
            'pipeline_info': {
                'timestamp': datetime.now().isoformat(),
                'pipeline_version': 'TuttiBot Hybrid v3.0.0',
                'layers_used': ['INPUT3_LAYER', 'PROCESSING_LAYER', 'TEMPORAL_ALIGNMENT']
            },
            'input_summary': {
                'original_audio': input_results['metadata']['original_audio'],
                'original_score': input_results['metadata']['original_score'],
                'audio_converted': input_results['metadata']['audio_converted'],
                'score_converted': input_results['metadata']['score_converted']
            },
            'processing_summary': {
                'audio_segments': processing_results['metadata']['audio_segments_count'],
                'music_features': processing_results['metadata']['music_features_count'],
                'processed_audio_path': processing_results['processed_audio_path']
            },
            'alignment_summary': {
                'confidence': confidence,
                'dtw_distance': dtw_distance,
                'detected_notes': len(alignment_results['transcription'].get('notes', [])),
                'scoregraph_nodes': len(alignment_results['scoregraph'].get('nodes', [])),
                'alignment_path_length': len(alignment_data.get('warping_path', []))
            },
            'quality_metrics': {
                'overall_success': confidence > 0.5,
                'high_confidence': confidence > 0.8,
                'alignment_quality': 'Excellent' if confidence > 0.9 else 'Good' if confidence > 0.7 else 'Fair' if confidence > 0.5 else 'Poor'
            },
            'file_paths': {
                'scoregraph': alignment_results['scoregraph_path'],
                'transcription': alignment_results['transcription_path'],
                'alignment': alignment_results['alignment_path'],
                'processed_audio': processing_results['processed_audio_path']
            }
        }
        
        # Save final results
        final_results_path = os.path.join(final_output_dir, 'hybrid_pipeline_results.json')
        with open(final_results_path, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        # Create summary report
        summary_path = os.path.join(final_output_dir, 'summary_report.txt')
        with open(summary_path, 'w') as f:
            f.write("TuttiBot Hybrid Pipeline - Final Results\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Processing completed: {final_results['pipeline_info']['timestamp']}\n")
            f.write(f"Pipeline version: {final_results['pipeline_info']['pipeline_version']}\n\n")
            
            f.write("PROCESSING SUMMARY:\n")
            f.write(f"  Audio file: {final_results['input_summary']['original_audio']}\n")
            f.write(f"  Score file: {final_results['input_summary']['original_score']}\n")
            f.write(f"  Audio segments: {final_results['processing_summary']['audio_segments']}\n")
            f.write(f"  Music features: {final_results['processing_summary']['music_features']}\n")
            f.write(f"  Detected notes: {final_results['alignment_summary']['detected_notes']}\n\n")
            
            f.write("ALIGNMENT RESULTS:\n")
            f.write(f"  Confidence: {final_results['alignment_summary']['confidence']:.3f}\n")
            f.write(f"  DTW Distance: {final_results['alignment_summary']['dtw_distance']:.3f}\n")
            f.write(f"  Quality: {final_results['quality_metrics']['alignment_quality']}\n")
            f.write(f"  Success: {'YES' if final_results['quality_metrics']['overall_success'] else 'NO'}\n\n")
            
            f.write("STATUS: SUCCESS\n")
        
        # Copy key files for easy access
        key_files = [
            (input_results['audio_path'], "final_audio.wav"),
            (input_results['score_path'], "final_score.xml"),
            (alignment_results['alignment_path'], "final_alignment.json"),
            (alignment_results['transcription_path'], "final_transcription.json")
        ]
        
        for src, dst in key_files:
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(final_output_dir, dst))
        
        logger.info(f"✅ Final results created successfully")
        logger.info(f"   Confidence: {confidence:.3f}")
        logger.info(f"   Quality: {final_results['quality_metrics']['alignment_quality']}")
        logger.info(f"   Results: {final_results_path}")
        logger.info(f"   Summary: {summary_path}")
        
        return final_results, final_results_path
        
    except Exception as e:
        logger.error(f"❌ Final results creation failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='TuttiBot Hybrid Pipeline - INPUT3_LAYER → PROCESSING_LAYER → Temporal Alignment')
    
    # Score input - make mutually exclusive
    score_group = parser.add_mutually_exclusive_group(required=True)
    score_group.add_argument('--pdf', help='Path to input PDF score')
    score_group.add_argument('--musicxml', help='Path to input MusicXML score')
    score_group.add_argument('--midi', help='Path to input MIDI score')
    
    parser.add_argument('--audio', required=True, help='Path to input audio performance')
    parser.add_argument('--output', default='./Output', help='Output directory (default: ./Output)')
    
    # GPU control options
    parser.add_argument('--cpu-only', action='store_true', 
                       help='Force CPU-only mode (disable GPU acceleration)')
    parser.add_argument('--gpu-id', type=int, 
                       help='Specific GPU ID to use (0, 1, 2, etc.)')
    
    args = parser.parse_args()
    
    # Determine score file and type
    score_file = None
    score_type = None
    
    if args.pdf:
        score_file = args.pdf
        score_type = 'pdf'
    elif args.musicxml:
        score_file = args.musicxml
        score_type = 'musicxml'
    elif args.midi:
        score_file = args.midi
        score_type = 'midi'
    
    # Validate inputs
    if not os.path.exists(score_file):
        print(f"❌ Error: Score file not found: {score_file}")
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
    print("🎼 TuttiBot Hybrid Pipeline - Best of Both Worlds")
    print("INPUT3_LAYER → PROCESSING_LAYER → Temporal Alignment")
    print("=" * 70)
    print(f"Input Score ({score_type.upper()}): {score_file}")
    print(f"Input Audio: {args.audio}")
    print(f"Output Directory: {output_dir}")
    print(f"Processing Mode: {'GPU' if gpu_manager.device_config['use_gpu'] else 'CPU'}")
    if gpu_manager.device_config['use_gpu']:
        print(f"GPU Device: {gpu_manager.device_config['device_id']}")
    print("=" * 70 + "\n")
    
    try:
        start_time = datetime.now()
        
        # Execute hybrid pipeline
        logger.info("🚀 Starting TuttiBot Hybrid Pipeline")
        
        # Step 1: INPUT3_LAYER (Fast direct Audiveris)
        input_results = run_input3_layer(args.audio, score_file, output_dir, logger)
        
        # Step 2: PROCESSING_LAYER (Efficient audio/music processing)
        processing_results = run_processing_layer(
            input_results['audio_path'],
            input_results['score_path'],
            output_dir,
            logger
        )
        
        # Step 3: TEMPORAL_ALIGNMENT (Advanced GPU-accelerated)
        alignment_results = run_temporal_alignment(
            input_results['score_path'],
            input_results['audio_path'],
            output_dir,
            gpu_manager,
            logger
        )
        
        # Step 4: Create Final Results
        final_results, final_results_path = create_final_results(
            input_results,
            processing_results,
            alignment_results,
            output_dir,
            logger
        )
        
        # Calculate total time
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Final GPU cleanup
        gpu_manager.cleanup_gpu_memory()
        
        # Success summary
        print("\n" + "=" * 70)
        print("🎉 TuttiBot Hybrid Pipeline Completed Successfully!")
        print("=" * 70)
        print(f"📁 Results saved to: {output_dir}")
        print(f"📊 Final results: {final_results_path}")
        print(f"⏱️  Total processing time: {total_time:.1f} seconds")
        print(f"⚡ Processing mode: {'GPU' if gpu_manager.device_config['use_gpu'] else 'CPU'}")
        print(f"🎯 Alignment confidence: {final_results['alignment_summary']['confidence']:.3f}")
        print(f"📈 Quality: {final_results['quality_metrics']['alignment_quality']}")
        
        # Final GPU memory status
        if gpu_manager.device_config['use_gpu']:
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                print(f"🎮 Final GPU memory: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
        
        print("=" * 70 + "\n")
        
        logger.info("🎉 TuttiBot Hybrid Pipeline completed successfully!")
        logger.info(f"Total processing time: {total_time:.1f} seconds")
        
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
