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
import glob
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

def input_layer(score_path, score_type, audio_path, output_dir, logger):
    """
    Input Layer: Convert score to MusicXML and prepare inputs for processing
    Supports PDF, MusicXML, and MIDI inputs
    """
    logger.info("=" * 60)
    logger.info("STARTING INPUT LAYER")
    logger.info("=" * 60)
    
    try:
        input_output_dir = os.path.join(output_dir, 'input_layer')
        
        # Process score based on type
        musicxml_output_path = os.path.join(input_output_dir, "converted_score.musicxml")
        
        if score_type == 'musicxml':
            # Direct copy for MusicXML files
            shutil.copy2(score_path, musicxml_output_path)
            logger.info(f"📄 MusicXML file copied: {score_path} -> {musicxml_output_path}")
            
        elif score_type == 'midi':
            # Convert MIDI to MusicXML using music21
            try:
                import music21
                logger.info(f"🎹 Converting MIDI to MusicXML: {score_path}")
                midi_stream = music21.converter.parse(score_path)
                midi_stream.write('musicxml', fp=musicxml_output_path)
                logger.info(f"✅ MIDI converted to MusicXML: {score_path} -> {musicxml_output_path}")
            except ImportError:
                raise Exception("music21 library required for MIDI conversion. Please install: pip install music21")
            except Exception as e:
                logger.error(f"❌ MIDI conversion failed: {e}")
                raise Exception(f"Cannot process MIDI file: {e}. Please check the MIDI file format.")
                
        elif score_type == 'pdf':
            # PDF conversion using available OMR tools
            logger.info(f"🔄 Converting PDF to MusicXML: {score_path}")
            
            # Try multiple methods in order of preference
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
                    import tempfile
                    input_dir = tempfile.mkdtemp(prefix="audiveris_input_")
                    output_dir = tempfile.mkdtemp(prefix="audiveris_output_")
                    
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
                                output_dir: {'bind': '/output', 'mode': 'rw'}
                            },
                            remove=True,
                            detach=False
                        )
                        logger.info("Audiveris container execution completed")
                        
                        # Find generated MusicXML files
                        import glob
                        mxl_files = glob.glob(os.path.join(output_dir, "*.mxl")) + glob.glob(os.path.join(output_dir, "*.xml"))
                        logger.info(f"Audiveris output directory contents: {os.listdir(output_dir)}")
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
                        shutil.rmtree(output_dir, ignore_errors=True)
                        client.close()
                        
                except docker.errors.ImageNotFound:
                    logger.warning("Audiveris Docker image not found, trying to pull...")
                    try:
                        client.images.pull('toprock/audiveris')
                        logger.info("✅ Audiveris image pulled successfully, retrying conversion...")
                        # Could retry the conversion here, but for simplicity, fall through to next method
                        conversion_error = "Audiveris image was just pulled, please retry the command"
                    except Exception as pull_error:
                        conversion_error = f"Failed to pull Audiveris image: {pull_error}"
                        
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
                                '-o', os.path.dirname(musicxml_output_path),
                                '--use-tf'  # Use TensorFlow instead of ONNX (may be more stable)
                            ], capture_output=True, text=True)
                            
                            if result.returncode == 0:
                                # Find generated MusicXML
                                generated_files = glob.glob(os.path.join(os.path.dirname(musicxml_output_path), "*.musicxml"))
                                if generated_files:
                                    shutil.copy2(generated_files[0], musicxml_output_path)
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
        
        # Verify the conversion was successful
        if not os.path.exists(musicxml_output_path):
            raise Exception(f"Score conversion failed - no MusicXML output generated from {score_path}")
        
        # Copy audio file to output structure
        audio_filename = os.path.basename(audio_path)
        audio_output_path = os.path.join(input_output_dir, audio_filename)
        shutil.copy2(audio_path, audio_output_path)
        
        logger.info(f"✅ Input Layer completed successfully")
        logger.info(f"   Score ({score_type.upper()}): {score_path}")
        logger.info(f"   MusicXML: {musicxml_output_path}")
        logger.info(f"   Audio: {audio_output_path}")
        
        return {
            'musicxml_path': musicxml_output_path,
            'audio_path': audio_output_path,
            'original_score_path': score_path,
            'score_type': score_type
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
        logger.info(f"   Total measures: {scoregraph.get('metadata', {}).get('total_measures', len(scoregraph.get('bars', [])))}")
        logger.info(f"   Total beat nodes: {len(scoregraph.get('nodes', []))}")
        logger.info(f"   Total note nodes: {len(scoregraph.get('musical_notes', []))}")
        logger.info(f"   Total nodes: {len(scoregraph.get('nodes', [])) + len(scoregraph.get('musical_notes', []))}")
        logger.info(f"   ScoreGraph saved: {scoregraph_path}")
        if scoregraph.get('musical_notes'):
            sample_note = scoregraph['musical_notes'][0]
            logger.info(f"   Sample notes: {sample_note.get('pitch_name', 'Unknown')} (MIDI {sample_note.get('pitch', 0)}) at {sample_note.get('offset_seconds', 0):.3f}s")
        
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
        
        # Extract MIDI path from metadata if available
        midi_path = transcription_result.get('midi_path')
        if not midi_path and 'metadata' in transcription_result:
            metadata = transcription_result['metadata']
            if 'source_files' in metadata and 'midi' in metadata['source_files']:
                midi_path = metadata['source_files']['midi']
        
        logger.info(f"   🎹 MIDI path extracted: {midi_path}")
        
        return {
            'transcription_json_path': transcription_json_path,
            'midi_path': midi_path,
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
        
        # Debug the transcription result structure
        logger.info(f"   🎹 Debug - transcription_result keys: {list(transcription_result.keys())}")
        logger.info(f"   🎹 Debug - midi_path from transcription: {transcription_result.get('midi_path')}")
        if 'transcription' in transcription_result:
            transcription_metadata = transcription_result['transcription']
            logger.info(f"   🎹 Debug - transcription metadata keys: {list(transcription_metadata.keys())}")
            if 'metadata' in transcription_metadata:
                meta = transcription_metadata['metadata']
                logger.info(f"   🎹 Debug - metadata has source_files: {meta.get('source_files', {})}")
        
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
        
        # Extract alignment metrics from the nested structure
        alignment_data = alignment_result.get('alignment', {})
        confidence = alignment_data.get('confidence', 'N/A')
        dtw_distance = alignment_data.get('dtw_distance', 'N/A')
        warping_path = alignment_data.get('warping_path', [])
        
        logger.info(f"   Alignment confidence: {confidence}")
        logger.info(f"   DTW distance: {dtw_distance}")
        logger.info(f"   Path length: {len(warping_path)}")
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
                'total_measures': scoregraph.get('metadata', {}).get('total_measures', len(scoregraph.get('bars', []))),
                'total_score_beats': len(scoregraph.get('nodes', [])),
                'detected_notes': len(transcription.get('notes', [])),
                'alignment_confidence': alignment.get('alignment', {}).get('confidence', 0.0),
                'dtw_distance': alignment.get('alignment', {}).get('dtw_distance', float('inf')),
                'alignment_path_length': len(alignment.get('alignment', {}).get('warping_path', []))
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
    print("🎼 TuttiBot v02 - Temporal Alignment Pipeline (GPU-Ready)")
    print("=" * 70)
    print(f"Input Score ({score_type.upper()}): {score_file}")
    print(f"Input Audio: {args.audio}")
    print(f"Output Directory: {output_dir}")
    print(f"Processing Mode: {'GPU' if gpu_manager.device_config['use_gpu'] else 'CPU'}")
    if gpu_manager.device_config['use_gpu']:
        print(f"GPU Device: {gpu_manager.device_config['device_id']}")
    print("=" * 70 + "\n")
    
    try:
        # Execute pipeline
        logger.info("🚀 Starting TuttiBot v02 Pipeline")
        
        # Input Layer - Process score to MusicXML
        input_results = input_layer(score_file, score_type, args.audio, output_dir, logger)
        
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
            block1_results,  # Pass the full Block 1 results, not just transcription
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
