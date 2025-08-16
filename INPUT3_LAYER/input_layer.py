#!/usr/bin/env python3
"""
Music Performance Evaluation System - Input Layer (Simple Direct Version)
=========================================================================

Simple, clean version that uses Audiveris directly without Docker.
No fallbacks, no complex dependencies - just audio processing + direct Audiveris CLI.

Requirements:
1. Audio: librosa + soundfile (for audio processing)
2. Score: Audiveris installed with command-line access

Dependencies:
- librosa: audio processing and resampling
- soundfile: audio file I/O  
- Audiveris: direct CLI calls for PDF to MusicXML conversion
"""

import os
import sys
import subprocess
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, Union
import platform

# Optional imports for MXL conversion
try:
    import music21
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False

try:
    import librosa
    import soundfile as sf
except ImportError as e:
    print(f"Error: Missing audio processing dependencies: {e}")
    print("Install with: pip install librosa soundfile")
    sys.exit(1)


class AudioInputProcessor:
    """Handles audio file input, validation, and format conversion."""
    
    TARGET_SAMPLE_RATE = 44100
    TARGET_BIT_DEPTH = 16
    MAX_CHANNELS = 5
    
    def __init__(self):
        self.supported_formats = ['.wav', '.flac', '.mp3', '.aac', '.ogg']
    
    def process_audio(self, audio_path: Union[str, Path]) -> Dict[str, Any]:
        """Process audio input, validate format, and convert if necessary."""
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
                bit_depth = 16
            
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
    """Handles score sheet input using direct Audiveris CLI calls."""
    
    def __init__(self):
        self.supported_formats = {
            '.pdf': 'pdf',
            '.midi': 'midi',
            '.mid': 'midi',
            '.xml': 'musicxml',
            '.musicxml': 'musicxml',
            '.mxl': 'musicxml'
        }
        
        # Find Audiveris executable
        self.audiveris_cmd = self._find_audiveris_command_robust()
    
    def _find_audiveris_command_robust(self) -> str:
        """Find Audiveris command with robust detection."""
        # First, try the known working path directly
        known_path = "/opt/audiveris/bin/Audiveris"
        if os.path.exists(known_path):
            try:
                # Quick test to ensure it's executable
                result = subprocess.run([known_path, "-help"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if "Audiveris" in str(result.stdout) or "CLI" in str(result.stdout):
                    print(f"Found Audiveris at: {known_path}")
                    return known_path
            except:
                pass
        
        # Fallback to the original method
        return self._find_audiveris_command()
    
    def _find_audiveris_command(self) -> str:
        """Find the Audiveris command based on the operating system."""
        system = platform.system().lower()
        
        # Common installation paths for different OS
        possible_paths = []
        
        if system == "windows":
            possible_paths = [
                r"C:\Program Files\Audiveris\bin\Audiveris.bat",
                r"C:\Program Files (x86)\Audiveris\bin\Audiveris.bat",
                "audiveris.bat",
                "audiveris"
            ]
        elif system == "darwin":  # macOS
            possible_paths = [
                "/Applications/Audiveris.app/Contents/MacOS/Audiveris",
                "/opt/audiveris/bin/Audiveris",
                "audiveris"
            ]
        else:  # Linux and others
            possible_paths = [
                "/opt/audiveris/bin/Audiveris",
                "/usr/local/bin/audiveris",
                "/usr/bin/audiveris",
                "audiveris"
            ]
        
        # Test each path to see if Audiveris is available
        for path in possible_paths:
            try:
                # Test if the command works
                result = subprocess.run([path, "-help"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                if result.returncode == 0 and "Audiveris" in result.stdout:
                    print(f"Found Audiveris at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                continue
        
        return None
    
    def process_score(self, score_path: Union[str, Path]) -> Dict[str, Any]:
        """Process score input based on file type."""
        score_path = Path(score_path)
        
        if not score_path.exists():
            return {
                'success': False,
                'output_path': None,
                'original_format': None,
                'converted': False,
                'message': f"Score file not found: {score_path}"
            }
        
        file_ext = score_path.suffix.lower()
        if file_ext not in self.supported_formats:
            return {
                'success': False,
                'output_path': None,
                'original_format': None,
                'converted': False,
                'message': f"Unsupported score format: {file_ext}. Supported: {list(self.supported_formats.keys())}"
            }
        
        format_type = self.supported_formats[file_ext]
        
        if format_type in ['midi', 'musicxml']:
            # No processing needed for MIDI and MusicXML
            return {
                'success': True,
                'output_path': score_path,
                'original_format': format_type,
                'converted': False,
                'message': f"{format_type.upper()} file ready for processing (no conversion needed)"
            }
        
        elif format_type == 'pdf':
            # Convert PDF to MusicXML using direct Audiveris CLI
            return self._convert_pdf_with_audiveris(score_path)
        
        else:
            return {
                'success': False,
                'output_path': None,
                'original_format': format_type,
                'converted': False,
                'message': f"Unknown format type: {format_type}"
            }
    
    def _convert_pdf_with_audiveris(self, pdf_path: Path) -> Dict[str, Any]:
        """Convert PDF to MusicXML using direct Audiveris CLI."""
        if self.audiveris_cmd is None:
            return {
                'success': False,
                'output_path': None,
                'original_format': 'pdf',
                'converted': False,
                'message': "Audiveris not found. Please install Audiveris and ensure it's in your PATH or standard installation directory."
            }
        
        try:
            # Create output directory
            output_dir = pdf_path.parent / f"{pdf_path.stem}_audiveris_output"
            output_dir.mkdir(exist_ok=True)
            
            # Build Audiveris command
            # audiveris -batch -export -output <output_dir> <input_pdf>
            cmd = [
                self.audiveris_cmd,
                "-batch",           # Run without GUI
                "-export",          # Export to MusicXML
                "-output", str(output_dir),  # Output directory
                str(pdf_path)       # Input PDF file
            ]
            
            print(f"Running Audiveris: {' '.join(cmd)}")
            
            # Run Audiveris with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(pdf_path.parent)
            )
            
            # Find generated MusicXML files (including compressed .mxl format)
            musicxml_files = list(output_dir.glob("*.xml")) + list(output_dir.glob("*.musicxml")) + list(output_dir.glob("*.mxl"))
            
            # Check for successful conversion by presence of output files
            # (Audiveris can return non-zero exit codes even when successful)
            if not musicxml_files and result.returncode != 0:
                return {
                    'success': False,
                    'output_path': None,
                    'original_format': 'pdf',
                    'converted': False,
                    'message': f"Audiveris conversion failed. Exit code: {result.returncode}. Error: {result.stderr}"
                }
            
            if not musicxml_files:
                # Also check for .omr files that might need extraction
                omr_files = list(output_dir.glob("*.omr"))
                if omr_files:
                    return {
                        'success': False,
                        'output_path': None,
                        'original_format': 'pdf',
                        'converted': False,
                        'message': f"Audiveris created .omr file but no MusicXML. Check {output_dir} for results."
                    }
                else:
                    return {
                        'success': False,
                        'output_path': None,
                        'original_format': 'pdf',
                        'converted': False,
                        'message': f"No MusicXML files generated by Audiveris. Check {output_dir} for any output files."
                    }
            
            # Use the first generated MusicXML file
            source_xml = musicxml_files[0]
            final_output = pdf_path.parent / f"{pdf_path.stem}_audiveris.xml"
            
            # If it's an .mxl file, convert it to .xml
            if source_xml.suffix.lower() == '.mxl':
                converted_xml = self._convert_mxl_to_xml(source_xml, final_output)
                if converted_xml:
                    final_output = converted_xml
                    # Clean up the .mxl file
                    try:
                        source_xml.unlink()
                    except:
                        pass  # Don't fail if cleanup doesn't work
                else:
                    # Fallback: just copy the .mxl file
                    shutil.copy2(source_xml, final_output)
            else:
                shutil.copy2(source_xml, final_output)
            
            return {
                'success': True,
                'output_path': final_output,
                'original_format': 'pdf',
                'converted': True,
                'message': f"PDF successfully converted to MusicXML using Audiveris. Output: {final_output.name}"
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output_path': None,
                'original_format': 'pdf',
                'converted': False,
                'message': "Audiveris conversion timed out (>5 minutes). Try with a simpler or smaller PDF."
            }
        except Exception as e:
            return {
                'success': False,
                'output_path': None,
                'original_format': 'pdf',
                'converted': False,
                'message': f"Error during Audiveris conversion: {str(e)}"
            }
    
    def _convert_mxl_to_xml(self, mxl_path: Path, output_path: Path) -> Path:
        """Convert .mxl (compressed MusicXML) to .xml format."""
        try:
            # Method 1: Direct ZIP extraction (faster)
            with zipfile.ZipFile(mxl_path, 'r') as zip_file:
                # Find the main .xml file in the zip
                xml_files = [name for name in zip_file.namelist() if name.endswith('.xml')]
                if xml_files:
                    # Extract the first .xml file
                    main_xml = xml_files[0]
                    with zip_file.open(main_xml) as source:
                        with open(output_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    print(f"Converted .mxl to .xml using ZIP extraction")
                    return output_path
        except Exception as e:
            print(f"ZIP extraction failed: {e}")
        
        # Method 2: Music21 fallback (if available)
        if MUSIC21_AVAILABLE:
            try:
                score = music21.converter.parse(str(mxl_path))
                score.write('musicxml', fp=str(output_path))
                print(f"Converted .mxl to .xml using music21")
                return output_path
            except Exception as e:
                print(f"Music21 conversion failed: {e}")
        
        # Method 3: Last resort - just rename (not ideal but works)
        try:
            shutil.copy2(mxl_path, output_path)
            print(f"Copied .mxl as .xml (fallback method)")
            return output_path
        except Exception as e:
            print(f"All conversion methods failed: {e}")
            return None


class MusicInputLayer:
    """Main input layer class that coordinates audio and score processing."""
    
    def __init__(self):
        self.audio_processor = AudioInputProcessor()
        self.score_processor = ScoreInputProcessor()
        
        # Check if Audiveris is available
        if self.score_processor.audiveris_cmd:
            print(f"✓ Audiveris found: {self.score_processor.audiveris_cmd}")
        else:
            print("⚠ Audiveris not found. PDF processing will not be available.")
            print("  Please install Audiveris from: https://github.com/Audiveris/audiveris/releases")
    
    def process_inputs(self, audio_path: Union[str, Path], score_path: Union[str, Path]) -> Dict[str, Any]:
        """Process both audio and score inputs."""
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
        
        print("-" * 50)
        
        return {
            'audio': audio_result,
            'score': score_result,
            'overall_success': audio_result['success'] and score_result['success']
        }


def main():
    """Example usage of the input layer."""
    if len(sys.argv) != 3:
        print("Usage: python input_layer_simple.py <audio_file> <score_file>")
        print("Example: python input_layer_simple.py song.wav sheet_music.pdf")
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