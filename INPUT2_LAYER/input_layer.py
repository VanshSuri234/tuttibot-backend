#!/usr/bin/env python3
"""
Music Performance Evaluation System - Input Layer (Updated)
===========================================================

This module handles audio and score sheet inputs for music performance evaluation.

Audio Input:
- Accepts WAV files
- Validates format (44.1 kHz / 16-bit, up to 5 channels)
- Attempts resampling if format doesn't match
- Reports conversion success/failure

Score Sheet Input:
- Accepts PDF, MIDI, or MusicXML files
- For MIDI/XML: passes through without processing
- For PDF: converts to MusicXML using multiple methods:
  1. Docker + Audiveris (most reliable)
  2. pdf2image + oemer (fallback)
  3. Handles page extraction and image processing

Dependencies:
- librosa: audio processing and resampling
- soundfile: audio file I/O
- pdf2image: PDF to image conversion
- docker: for Audiveris container (optional but recommended)
- oemer: backup OMR solution
- music21: MusicXML validation
- pathlib: file path handling
"""

import os
import sys
import subprocess
import tempfile
import shutil
import docker
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, Union, List
import warnings

try:
    import librosa
    import soundfile as sf
except ImportError as e:
    print(f"Error: Missing audio processing dependencies: {e}")
    print("Install with: pip install librosa soundfile")
    sys.exit(1)

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    print("Warning: pdf2image not found. PDF processing will be limited.")
    print("Install with: pip install pdf2image")
    PDF2IMAGE_AVAILABLE = False

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    print("Warning: docker not found. Advanced PDF processing will not be available.")
    print("Install with: pip install docker")
    DOCKER_AVAILABLE = False

try:
    import music21
    MUSIC21_AVAILABLE = True
except ImportError:
    print("Warning: music21 not found. MusicXML validation will be limited.")
    print("Install with: pip install music21")
    MUSIC21_AVAILABLE = False

try:
    import oemer
    OEMER_AVAILABLE = True
except ImportError:
    print("Warning: oemer not found. Fallback PDF processing will not be available.")
    print("Install with: pip install oemer")
    OEMER_AVAILABLE = False


class AudioInputProcessor:
    """Handles audio file input, validation, and format conversion."""
    
    TARGET_SAMPLE_RATE = 44100
    TARGET_BIT_DEPTH = 16
    MAX_CHANNELS = 5
    
    def __init__(self):
        self.supported_formats = ['.wav', '.flac', '.mp3', '.aac', '.ogg']
    
    def process_audio(self, audio_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process audio input, validate format, and convert if necessary.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dict containing:
                - success: bool
                - output_path: Path to processed audio (original or converted)
                - original_format: dict with original audio properties
                - converted: bool indicating if conversion was performed
                - message: str with processing details
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            return {
                'success': False,
                'output_path': None,
                'original_format': None,
                'converted': False,
                'message': f"Audio file not found: {audio_path}"
            }
        
        if audio_path.suffix.lower() not in self.supported_formats:
            return {
                'success': False,
                'output_path': None,
                'original_format': None,
                'converted': False,
                'message': f"Unsupported audio format: {audio_path.suffix}"
            }
        
        try:
            # Load audio file and get properties
            audio_data, sample_rate = librosa.load(str(audio_path), sr=None, mono=False)
            
            # Handle mono/stereo loading
            if audio_data.ndim == 1:
                channels = 1
            else:
                channels = audio_data.shape[0] if audio_data.ndim > 1 else 1
            
            # Get bit depth from original file if possible
            try:
                info = sf.info(str(audio_path))
                bit_depth = info.subtype_info.bits if hasattr(info, 'subtype_info') else 16
            except:
                bit_depth = 16  # Default assumption
            
            original_format = {
                'sample_rate': sample_rate,
                'channels': channels,
                'bit_depth': bit_depth,
                'format': audio_path.suffix.lower()
            }
            
            # Check if conversion is needed
            needs_conversion = (
                sample_rate != self.TARGET_SAMPLE_RATE or
                channels > self.MAX_CHANNELS or
                audio_path.suffix.lower() != '.wav'
            )
            
            if not needs_conversion:
                return {
                    'success': True,
                    'output_path': audio_path,
                    'original_format': original_format,
                    'converted': False,
                    'message': "Audio format is already correct (44.1kHz/16-bit WAV, ≤5 channels)"
                }
            
            # Attempt conversion
            return self._convert_audio(audio_path, audio_data, original_format)
            
        except Exception as e:
            return {
                'success': False,
                'output_path': None,
                'original_format': None,
                'converted': False,
                'message': f"Error processing audio: {str(e)}"
            }
    
    def _convert_audio(self, original_path: Path, audio_data, original_format: Dict) -> Dict[str, Any]:
        """Convert audio to target format."""
        try:
            # Resample to target sample rate
            if original_format['sample_rate'] != self.TARGET_SAMPLE_RATE:
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=original_format['sample_rate'], 
                    target_sr=self.TARGET_SAMPLE_RATE
                )
            
            # Handle channel count
            if original_format['channels'] > self.MAX_CHANNELS:
                if audio_data.ndim > 1:
                    # Keep only first MAX_CHANNELS channels
                    audio_data = audio_data[:self.MAX_CHANNELS]
                channels_note = f"Reduced from {original_format['channels']} to {self.MAX_CHANNELS} channels. "
            else:
                channels_note = ""
            
            # Create output path
            output_path = original_path.parent / f"{original_path.stem}_converted.wav"
            
            # Save converted audio
            sf.write(
                str(output_path), 
                audio_data.T if audio_data.ndim > 1 else audio_data,
                self.TARGET_SAMPLE_RATE,
                subtype='PCM_16'
            )
            
            conversion_details = []
            if original_format['sample_rate'] != self.TARGET_SAMPLE_RATE:
                conversion_details.append(f"Resampled from {original_format['sample_rate']}Hz to {self.TARGET_SAMPLE_RATE}Hz")
            if original_format['format'] != '.wav':
                conversion_details.append(f"Converted from {original_format['format']} to WAV")
            if channels_note:
                conversion_details.append(channels_note.strip())
            
            return {
                'success': True,
                'output_path': output_path,
                'original_format': original_format,
                'converted': True,
                'message': f"Audio converted successfully. {' | '.join(conversion_details)}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'output_path': None,
                'original_format': original_format,
                'converted': False,
                'message': f"Audio conversion failed: {str(e)}"
            }


class ScoreInputProcessor:
    """Handles score sheet input in PDF, MIDI, or MusicXML formats."""
    
    def __init__(self):
        self.supported_formats = {
            '.pdf': 'pdf',
            '.midi': 'midi',
            '.mid': 'midi',
            '.xml': 'musicxml',
            '.musicxml': 'musicxml',
            '.mxl': 'musicxml'
        }
        
        # Check available PDF processing methods
        self.available_methods = self._check_available_methods()
    
    def _check_available_methods(self) -> List[str]:
        """Check which PDF processing methods are available."""
        methods = []
        
        if DOCKER_AVAILABLE:
            try:
                client = docker.from_env()
                # Check if Audiveris Docker image is available
                try:
                    client.images.get('toprock/audiveris')
                    methods.append('docker_audiveris')
                except docker.errors.ImageNotFound:
                    # Try to pull the image
                    try:
                        client.images.pull('toprock/audiveris')
                        methods.append('docker_audiveris')
                    except:
                        pass
                client.close()
            except:
                pass
        
        if PDF2IMAGE_AVAILABLE and OEMER_AVAILABLE:
            methods.append('pdf2image_oemer')
        
        return methods
    
    def process_score(self, score_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process score input based on file type.
        
        Args:
            score_path: Path to the score file
            
        Returns:
            Dict containing:
                - success: bool
                - output_path: Path to processed score
                - original_format: str (pdf/midi/musicxml)
                - converted: bool indicating if conversion was performed
                - message: str with processing details
                - method_used: str indicating which conversion method was used
        """
        score_path = Path(score_path)
        
        if not score_path.exists():
            return {
                'success': False,
                'output_path': None,
                'original_format': None,
                'converted': False,
                'message': f"Score file not found: {score_path}",
                'method_used': None
            }
        
        file_ext = score_path.suffix.lower()
        if file_ext not in self.supported_formats:
            return {
                'success': False,
                'output_path': None,
                'original_format': None,
                'converted': False,
                'message': f"Unsupported score format: {file_ext}. Supported: {list(self.supported_formats.keys())}",
                'method_used': None
            }
        
        format_type = self.supported_formats[file_ext]
        
        if format_type in ['midi', 'musicxml']:
            # Validate MusicXML files if music21 is available
            if format_type == 'musicxml' and MUSIC21_AVAILABLE:
                validation_result = self._validate_musicxml(score_path)
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'output_path': None,
                        'original_format': format_type,
                        'converted': False,
                        'message': f"Invalid MusicXML file: {validation_result['error']}",
                        'method_used': None
                    }
            
            return {
                'success': True,
                'output_path': score_path,
                'original_format': format_type,
                'converted': False,
                'message': f"{format_type.upper()} file ready for processing (no conversion needed)",
                'method_used': None
            }
        
        elif format_type == 'pdf':
            # Try multiple PDF conversion methods
            return self._convert_pdf_to_musicxml(score_path)
        
        else:
            return {
                'success': False,
                'output_path': None,
                'original_format': format_type,
                'converted': False,
                'message': f"Unknown format type: {format_type}",
                'method_used': None
            }
    
    def _validate_musicxml(self, xml_path: Path) -> Dict[str, Any]:
        """Validate MusicXML file using music21."""
        try:
            score = music21.converter.parse(str(xml_path))
            if score is None:
                return {'valid': False, 'error': 'Failed to parse MusicXML'}
            return {'valid': True, 'error': None}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _convert_pdf_to_musicxml(self, pdf_path: Path) -> Dict[str, Any]:
        """Convert PDF to MusicXML using available methods."""
        if not self.available_methods:
            return {
                'success': False,
                'output_path': None,
                'original_format': 'pdf',
                'converted': False,
                'message': "No PDF conversion methods available. Install docker + pull toprock/audiveris, or install pdf2image + oemer",
                'method_used': None
            }
        
        # Try methods in order of preference
        for method in self.available_methods:
            print(f"Attempting PDF conversion using {method}...")
            
            if method == 'docker_audiveris':
                result = self._convert_with_docker_audiveris(pdf_path)
            elif method == 'pdf2image_oemer':
                result = self._convert_with_pdf2image_oemer(pdf_path)
            else:
                continue
            
            if result['success']:
                result['method_used'] = method
                return result
            else:
                print(f"Method {method} failed: {result['message']}")
        
        # All methods failed
        return {
            'success': False,
            'output_path': None,
            'original_format': 'pdf',
            'converted': False,
            'message': f"All PDF conversion methods failed. Tried: {', '.join(self.available_methods)}",
            'method_used': None
        }
    
    def _convert_with_docker_audiveris(self, pdf_path: Path) -> Dict[str, Any]:
        """Convert PDF using Docker + Audiveris."""
        try:
            client = docker.from_env()
            
            # Create temporary directories
            input_dir = tempfile.mkdtemp(prefix="audiveris_input_")
            output_dir = tempfile.mkdtemp(prefix="audiveris_output_")
            
            try:
                # Copy PDF to input directory
                input_pdf = Path(input_dir) / pdf_path.name
                shutil.copy2(pdf_path, input_pdf)
                
                # Run Audiveris container
                container = client.containers.run(
                    'toprock/audiveris',
                    volumes={
                        input_dir: {'bind': '/input', 'mode': 'ro'},
                        output_dir: {'bind': '/output', 'mode': 'rw'}
                    },
                    remove=True,
                    detach=False
                )
                
                # Find generated MusicXML files
                output_path = Path(output_dir)
                mxl_files = list(output_path.glob("*.mxl")) + list(output_path.glob("*.xml"))
                
                if not mxl_files:
                    return {
                        'success': False,
                        'output_path': None,
                        'original_format': 'pdf',
                        'converted': False,
                        'message': "Audiveris did not generate any MusicXML files"
                    }
                
                # Move the first MusicXML file to the original location
                result_file = mxl_files[0]
                final_output = pdf_path.parent / f"{pdf_path.stem}_audiveris.{result_file.suffix[1:]}"
                shutil.move(result_file, final_output)
                
                return {
                    'success': True,
                    'output_path': final_output,
                    'original_format': 'pdf',
                    'converted': True,
                    'message': f"PDF successfully converted to MusicXML using Docker + Audiveris. Output: {final_output.name}"
                }
                
            finally:
                # Cleanup
                shutil.rmtree(input_dir, ignore_errors=True)
                shutil.rmtree(output_dir, ignore_errors=True)
                client.close()
                
        except Exception as e:
            return {
                'success': False,
                'output_path': None,
                'original_format': 'pdf',
                'converted': False,
                'message': f"Docker + Audiveris conversion failed: {str(e)}"
            }
    
    def _convert_with_pdf2image_oemer(self, pdf_path: Path) -> Dict[str, Any]:
        """Convert PDF using pdf2image + oemer."""
        try:
            # Create output directory
            output_dir = pdf_path.parent / f"{pdf_path.stem}_pdf2image_output"
            output_dir.mkdir(exist_ok=True)
            
            # Convert PDF to images
            print("Converting PDF pages to images...")
            images = convert_from_path(pdf_path, dpi=300)
            
            if not images:
                return {
                    'success': False,
                    'output_path': None,
                    'original_format': 'pdf',
                    'converted': False,
                    'message': "Failed to convert PDF to images"
                }
            
            # Process each page with oemer
            musicxml_files = []
            for i, image in enumerate(images):
                page_image_path = output_dir / f"page_{i+1:03d}.png"
                image.save(page_image_path, 'PNG')
                
                print(f"Processing page {i+1}/{len(images)} with oemer...")
                
                # Run oemer on this image
                try:
                    original_cwd = os.getcwd()
                    os.chdir(str(output_dir))
                    
                    cmd = [sys.executable, '-m', 'oemer', str(page_image_path), '-o', '.']
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        # Find generated XML
                        xml_files = list(output_dir.glob(f"page_{i+1:03d}*.xml"))
                        if xml_files:
                            musicxml_files.extend(xml_files)
                    
                except subprocess.TimeoutExpired:
                    print(f"Timeout processing page {i+1}")
                except Exception as e:
                    print(f"Error processing page {i+1}: {e}")
                finally:
                    os.chdir(original_cwd)
            
            if not musicxml_files:
                return {
                    'success': False,
                    'output_path': None,
                    'original_format': 'pdf',
                    'converted': False,
                    'message': "No MusicXML files generated from PDF pages"
                }
            
            # If multiple pages, combine or return the first one
            if len(musicxml_files) == 1:
                final_output = musicxml_files[0]
            else:
                # For multiple pages, return the first one and note the others
                final_output = musicxml_files[0]
            
            # Move to final location
            final_path = pdf_path.parent / f"{pdf_path.stem}_oemer.xml"
            shutil.move(final_output, final_path)
            
            return {
                'success': True,
                'output_path': final_path,
                'original_format': 'pdf',
                'converted': True,
                'message': f"PDF successfully converted to MusicXML using pdf2image + oemer. Processed {len(images)} pages. Output: {final_path.name}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'output_path': None,
                'original_format': 'pdf',
                'converted': False,
                'message': f"pdf2image + oemer conversion failed: {str(e)}"
            }


class MusicInputLayer:
    """Main input layer class that coordinates audio and score processing."""
    
    def __init__(self):
        self.audio_processor = AudioInputProcessor()
        self.score_processor = ScoreInputProcessor()
        
        # Print available PDF conversion methods
        if hasattr(self.score_processor, 'available_methods'):
            methods = self.score_processor.available_methods
            if methods:
                print(f"Available PDF conversion methods: {', '.join(methods)}")
            else:
                print("Warning: No PDF conversion methods available")
    
    def process_inputs(self, audio_path: Union[str, Path], score_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process both audio and score inputs.
        
        Args:
            audio_path: Path to audio file
            score_path: Path to score file
            
        Returns:
            Dict containing results for both audio and score processing
        """
        print("Processing music inputs...")
        print("-" * 50)
        
        # Process audio
        print("1. Processing audio input...")
        audio_result = self.audio_processor.process_audio(audio_path)
        print(f"   Status: {'✓' if audio_result['success'] else '✗'}")
        print(f"   Message: {audio_result['message']}")
        
        if audio_result['success'] and audio_result['original_format']:
            fmt = audio_result['original_format']
            print(f"   Original format: {fmt['sample_rate']}Hz, {fmt['channels']} ch, {fmt['bit_depth']}-bit, {fmt['format']}")
        
        print()
        
        # Process score
        print("2. Processing score input...")
        score_result = self.score_processor.process_score(score_path)
        print(f"   Status: {'✓' if score_result['success'] else '✗'}")
        print(f"   Message: {score_result['message']}")
        
        if score_result['success']:
            print(f"   Format: {score_result['original_format'].upper()}")
            if score_result.get('method_used'):
                print(f"   Method: {score_result['method_used']}")
        
        print("-" * 50)
        
        return {
            'audio': audio_result,
            'score': score_result,
            'overall_success': audio_result['success'] and score_result['success']
        }


def main():
    """Example usage of the input layer."""
    if len(sys.argv) != 3:
        print("Usage: python input_layer.py <audio_file> <score_file>")
        print("Example: python input_layer.py song.wav sheet_music.pdf")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    score_file = sys.argv[2]
    
    # Initialize input layer
    input_layer = MusicInputLayer()
    
    # Process inputs
    results = input_layer.process_inputs(audio_file, score_file)
    
    # Print summary
    print("\nProcessing Summary:")
    print(f"Overall Success: {'✓' if results['overall_success'] else '✗'}")
    
    if results['overall_success']:
        print("\nReady for next processing layer!")
        print(f"Audio file: {results['audio']['output_path']}")
        print(f"Score file: {results['score']['output_path']}")
    else:
        print("\nPlease fix the issues above before proceeding.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())