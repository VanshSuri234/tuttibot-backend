#!/usr/bin/env python3
"""
TuttiBot Hybrid Pipeline v02 - Alternative PDF Conversion Method
Combines the flow of main_hybrid.py with PDF conversion method from main_v02_fixed.py

Pipeline Flow:
INPUT_LAYER (Docker+Audiveris/oemer fallback) → PROCESSING_LAYER → Temporal Alignment

Features:
- Docker + Audiveris PDF conversion (with oemer fallback)
- Efficient audio/music processing (from main.py) 
- Advanced temporal alignment (from main_v02_fixed.py)
- Automatic GPU detection and management
- Multiple PDF conversion fallbacks for reliability

Author: TuttiBot Team
Version: 3.0.1 (Hybrid v02)
"""

import os
import sys
import json
import argparse
import logging
import traceback
import shutil
import glob
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Add layer paths
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
    log_file = os.path.join(output_dir, 'tuttibot_hybrid_v02.log')
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
    output_dir = os.path.join(base_output_dir, f"tuttibot_hybrid_v02_{timestamp}")
    
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

def run_input_layer_v02(audio_path: str, score_path: str, score_type: str, output_dir: str, logger):
    """
    Input Layer using Docker + Audiveris (with oemer fallback) method from main_v02_fixed.py
    """
    logger.info("=" * 60)
    logger.info("STEP 1: INPUT_LAYER (DOCKER + AUDIVERIS / OEMER FALLBACK)")
    logger.info("=" * 60)
    
    try:
        input_output_dir = os.path.join(output_dir, '01_input_layer')
        
        # Process audio (copy as-is, assuming it's already in good format)
        audio_filename = os.path.basename(audio_path)
        audio_output_path = os.path.join(input_output_dir, audio_filename)
        shutil.copy2(audio_path, audio_output_path)
        logger.info(f"✅ Audio copied: {audio_output_path}")
        
        # Process score based on type
        if score_type == 'pdf':
            # PDF conversion using Docker + Audiveris method (same as main_v02_fixed.py)
            musicxml_output_path = os.path.join(input_output_dir, 'converted_score.xml')
            
            pdf_converted = False
            conversion_error = None
            
            # Method 1: Docker + Audiveris (most reliable)
            try:
                import docker
                client = docker.from_env()
                
                # Check if Audiveris image is available
                try:
                    client.images.get('toprock/audiveris')
                    logger.info("📦 Using Docker + Audiveris for PDF conversion")
                    
                    # Create temporary directories
                    input_dir = tempfile.mkdtemp(prefix="audiveris_input_")
                    temp_output_dir = tempfile.mkdtemp(prefix="audiveris_output_")
                    
                    try:
                        # Copy PDF to input directory
                        input_pdf = os.path.join(input_dir, os.path.basename(score_path))
                        shutil.copy2(score_path, input_pdf)
                        
                        # Run Audiveris container
                        logger.info(f"Running Audiveris on {os.path.basename(score_path)}")
                        container = client.containers.run(
                            'toprock/audiveris',
                            command=f"-batch -export /input/{os.path.basename(score_path)}",
                            volumes={
                                input_dir: {'bind': '/input', 'mode': 'ro'},
                                temp_output_dir: {'bind': '/output', 'mode': 'rw'}
                            },
                            remove=True,
                            detach=False
                        )
                        logger.info("Audiveris container execution completed")
                        
                        # Find generated MusicXML files
                        mxl_files = glob.glob(os.path.join(temp_output_dir, "*.mxl")) + glob.glob(os.path.join(temp_output_dir, "*.xml"))
                        logger.info(f"Audiveris output directory contents: {os.listdir(temp_output_dir)}")
                        logger.info(f"Found MusicXML files: {mxl_files}")
                        
                        if mxl_files:
                            # Copy the first MusicXML file to target location
                            shutil.copy2(mxl_files[0], musicxml_output_path)
                            pdf_converted = True
                            logger.info(f"✅ PDF converted using Docker + Audiveris: {score_path} -> {musicxml_output_path}")
                        else:
                            conversion_error = "Audiveris did not generate any MusicXML files"
                            
                    finally:
                        # Cleanup temporary directories
                        shutil.rmtree(input_dir, ignore_errors=True)
                        shutil.rmtree(temp_output_dir, ignore_errors=True)
                        client.close()
                        
                except Exception as e:
                    logger.warning(f"Docker + Audiveris failed: {e}")
                    conversion_error = f"Docker + Audiveris failed: {e}"
                        
            except ImportError:
                conversion_error = "Docker not available (install: pip install docker)"
            except Exception as docker_error:
                conversion_error = f"Docker + Audiveris failed: {docker_error}"
            
            # Method 2: oemer (fallback)
            if not pdf_converted:
                try:
                    logger.info("📦 Trying oemer for PDF conversion...")
                    
                    # Convert PDF to image first
                    try:
                        from pdf2image import convert_from_path
                        images = convert_from_path(score_path, dpi=300)
                        
                        if images:
                            # Save first page as image
                            temp_image = os.path.join(os.path.dirname(musicxml_output_path), "temp_page.png")
                            images[0].save(temp_image, 'PNG')
                            
                            # Run oemer on the image
                            import subprocess
                            result = subprocess.run([
                                'oemer', temp_image, 
                                '-o', os.path.dirname(musicxml_output_path)
                            ], capture_output=True, text=True)
                            
                            if result.returncode == 0:
                                # Find generated MusicXML files (both .xml and .musicxml)
                                xml_files = glob.glob(os.path.join(os.path.dirname(musicxml_output_path), "*.musicxml"))
                                xml_files.extend(glob.glob(os.path.join(os.path.dirname(musicxml_output_path), "*.xml")))
                                
                                if xml_files:
                                    shutil.copy2(xml_files[0], musicxml_output_path)
                                    pdf_converted = True
                                    logger.info(f"✅ PDF converted using oemer: {score_path} -> {musicxml_output_path}")
                                else:
                                    conversion_error = "oemer did not generate MusicXML file"
                            else:
                                conversion_error = f"oemer failed: {result.stderr}"
                            
                            # Cleanup temp image
                            if os.path.exists(temp_image):
                                os.remove(temp_image)
                        else:
                            conversion_error = "Failed to convert PDF to images"
                            
                    except ImportError:
                        conversion_error = "pdf2image not available (install: pip install pdf2image)"
                        
                except Exception as oemer_error:
                    conversion_error = f"oemer conversion failed: {oemer_error}"
            
            # If all methods failed
            if not pdf_converted:
                logger.error(f"❌ PDF conversion failed: {conversion_error}")
                raise Exception(
                    f"PDF conversion failed. Error: {conversion_error}\n\n"
                    f"To enable PDF conversion:\n"
                    f"1. Install Docker + Audiveris: docker pull toprock/audiveris\n"
                    f"2. Or install oemer: pip install pdf2image oemer\n"
                    f"3. Or convert PDF to MusicXML manually using MuseScore\n"
                    f"Current PDF file: {score_path}"
                )
            
            score_output_path = musicxml_output_path
            
        elif score_type in ['musicxml', 'xml']:
            # MusicXML files - copy directly
            score_output_path = os.path.join(input_output_dir, 'score.xml')
            shutil.copy2(score_path, score_output_path)
            logger.info(f"✅ MusicXML copied: {score_output_path}")
            
        elif score_type == 'midi':
            # MIDI files - copy directly (will be processed by music21)
            score_output_path = os.path.join(input_output_dir, 'score.mid')
            shutil.copy2(score_path, score_output_path)
            logger.info(f"✅ MIDI copied: {score_output_path}")
            
        else:
            raise Exception(f"Unsupported score type: {score_type}")
        
        # Verify the files exist
        if not os.path.exists(audio_output_path):
            raise Exception(f"Audio processing failed - no output generated from {audio_path}")
        if not os.path.exists(score_output_path):
            raise Exception(f"Score conversion failed - no output generated from {score_path}")
        
        # Save metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'original_audio': str(Path(audio_path).name),
            'original_score': str(Path(score_path).name),
            'score_type': score_type,
            'audio_converted': False,  # We just copy audio
            'score_converted': (score_type == 'pdf'),
            'conversion_method': 'Docker+Audiveris' if pdf_converted and score_type == 'pdf' else 'oemer' if score_type == 'pdf' else 'copy',
            'audio_message': f"Audio copied from {audio_path}",
            'score_message': f"Score processed from {score_path}"
        }
        
        metadata_path = os.path.join(input_output_dir, "input_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Input Layer completed successfully")
        logger.info(f"   Audio: {audio_output_path}")
        logger.info(f"   Score: {score_output_path}")
        logger.info(f"   Method: {metadata['conversion_method']}")
        
        return {
            'audio_path': audio_output_path,
            'score_path': score_output_path,
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"❌ INPUT_LAYER failed: {e}")
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
        
        # Extract MIDI path from metadata if available
        midi_path = transcription_result.get('midi_path')
        if not midi_path and 'metadata' in transcription_result:
            metadata = transcription_result['metadata']
            if 'source_files' in metadata and 'midi' in metadata['source_files']:
                midi_path = metadata['source_files']['midi']
        
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
                'pipeline_version': 'TuttiBot Hybrid v02 v3.0.1',
                'layers_used': ['INPUT_LAYER_V02', 'PROCESSING_LAYER', 'TEMPORAL_ALIGNMENT']
            },
            'input_summary': {
                'original_audio': input_results['metadata']['original_audio'],
                'original_score': input_results['metadata']['original_score'],
                'score_type': input_results['metadata']['score_type'],
                'audio_converted': input_results['metadata']['audio_converted'],
                'score_converted': input_results['metadata']['score_converted'],
                'conversion_method': input_results['metadata']['conversion_method']
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
        final_results_path = os.path.join(final_output_dir, 'hybrid_v02_pipeline_results.json')
        with open(final_results_path, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        # Create summary report
        summary_path = os.path.join(final_output_dir, 'summary_report.txt')
        with open(summary_path, 'w') as f:
            f.write("TuttiBot Hybrid v02 Pipeline - Final Results\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Processing completed: {final_results['pipeline_info']['timestamp']}\n")
            f.write(f"Pipeline version: {final_results['pipeline_info']['pipeline_version']}\n\n")
            
            f.write("INPUT PROCESSING:\n")
            f.write(f"  Audio file: {final_results['input_summary']['original_audio']}\n")
            f.write(f"  Score file: {final_results['input_summary']['original_score']}\n")
            f.write(f"  Score type: {final_results['input_summary']['score_type']}\n")
            f.write(f"  Conversion method: {final_results['input_summary']['conversion_method']}\n\n")
            
            f.write("PROCESSING SUMMARY:\n")
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
        logger.info(f"   Conversion method: {final_results['input_summary']['conversion_method']}")
        logger.info(f"   Results: {final_results_path}")
        logger.info(f"   Summary: {summary_path}")
        
        return final_results, final_results_path
        
    except Exception as e:
        logger.error(f"❌ Final results creation failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='TuttiBot Hybrid v02 Pipeline - Alternative PDF Conversion Method')
    
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
    print("🎼 TuttiBot Hybrid v02 Pipeline - Alternative PDF Conversion")
    print("INPUT_LAYER (Docker+Audiveris/oemer) → PROCESSING_LAYER → Temporal Alignment")
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
        
        # Execute hybrid v02 pipeline
        logger.info("🚀 Starting TuttiBot Hybrid v02 Pipeline")
        
        # Step 1: INPUT_LAYER_V02 (Docker + Audiveris / oemer fallback)
        input_results = run_input_layer_v02(args.audio, score_file, score_type, output_dir, logger)
        
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
        print("🎉 TuttiBot Hybrid v02 Pipeline Completed Successfully!")
        print("=" * 70)
        print(f"📁 Results saved to: {output_dir}")
        print(f"📊 Final results: {final_results_path}")
        print(f"⏱️  Total processing time: {total_time:.1f} seconds")
        print(f"⚡ Processing mode: {'GPU' if gpu_manager.device_config['use_gpu'] else 'CPU'}")
        print(f"🔄 PDF conversion method: {final_results['input_summary']['conversion_method']}")
        print(f"🎯 Alignment confidence: {final_results['alignment_summary']['confidence']:.3f}")
        print(f"📈 Quality: {final_results['quality_metrics']['alignment_quality']}")
        
        # Final GPU memory status
        if gpu_manager.device_config['use_gpu']:
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                print(f"🎮 Final GPU memory: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
        
        print("=" * 70 + "\n")
        
        logger.info("🎉 TuttiBot Hybrid v02 Pipeline completed successfully!")
        logger.info(f"Total processing time: {total_time:.1f} seconds")
        logger.info(f"PDF conversion method used: {final_results['input_summary']['conversion_method']}")
        
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
