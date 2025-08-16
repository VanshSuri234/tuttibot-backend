#!/usr/bin/env python3
"""
Music Performance Evaluation System - Input Layer
==================================================

This module handles audio and score sheet inputs for music performance evaluation.

Audio Input:
- Accepts WAV files
- Validates format (44.1 kHz / 16-bit, up to 5 channels)
- Attempts resampling if format doesn't match
- Reports conversion success/failure

Score Sheet Input:
- Accepts PDF, MIDI, or MusicXML files
- For MIDI/XML: passes through without processing
- For PDF: converts to MusicXML using oemer (Optical Music Recognition)

Dependencies:
- librosa: audio processing and resampling
- soundfile: audio file I/O
- oemer: PDF to MusicXML conversion
- pathlib: file path handling
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, Union
import warnings

try:
    import librosa
    import soundfile as sf
except ImportError as e:
    print(f"Error: Missing audio processing dependencies: {e}")
    print("Install with: pip install librosa soundfile")
    sys.exit(1)

try:
    import oemer
except ImportError:
    print("Warning: oemer not found. PDF processing will not be available.")
    print("Install with: pip install oemer")
    oemer = None


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
        """
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
            # Convert PDF to MusicXML using oemer
            return self._convert_pdf_to_musicxml(score_path)
        
        else:
            return {
                'success': False,
                'output_path': None,
                'original_format': format_type,
                'converted': False,
                'message': f"Unknown format type: {format_type}"
            }
    
    def _convert_pdf_to_musicxml(self, pdf_path: Path) -> Dict[str, Any]:
        """Convert PDF to MusicXML using oemer."""
        if oemer is None:
            return {
                'success': False,
                'output_path': None,
                'original_format': 'pdf',
                'converted': False,
                'message': "oemer not installed. Cannot convert PDF to MusicXML. Install with: pip install oemer"
            }
        
        try:
            # Create output directory
            output_dir = pdf_path.parent / f"{pdf_path.stem}_omr_output"
            output_dir.mkdir(exist_ok=True)
            
            # Run oemer conversion
            # oemer outputs to current directory by default, so we need to handle this
            original_cwd = os.getcwd()
            try:
                os.chdir(str(output_dir))
                
                # Use oemer command line interface
                cmd = [sys.executable, '-m', 'oemer', str(pdf_path), '-o', '.']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    return {
                        'success': False,
                        'output_path': None,
                        'original_format': 'pdf',
                        'converted': False,
                        'message': f"oemer conversion failed: {result.stderr}"
                    }
                
                # Find the generated MusicXML file
                musicxml_files = list(output_dir.glob("*.xml"))
                if not musicxml_files:
                    return {
                        'success': False,
                        'output_path': None,
                        'original_format': 'pdf',
                        'converted': False,
                        'message': "No MusicXML file generated by oemer"
                    }
                
                # Use the first generated XML file
                output_path = musicxml_files[0]
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'original_format': 'pdf',
                    'converted': True,
                    'message': f"PDF successfully converted to MusicXML using oemer. Output: {output_path.name}"
                }
                
            finally:
                os.chdir(original_cwd)
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output_path': None,
                'original_format': 'pdf',
                'converted': False,
                'message': "oemer conversion timed out (>5 minutes). Try with --without-deskew flag if image has no skew."
            }
        except Exception as e:
            return {
                'success': False,
                'output_path': None,
                'original_format': 'pdf',
                'converted': False,
                'message': f"Error during PDF conversion: {str(e)}"
            }


class MusicInputLayer:
    """Main input layer class that coordinates audio and score processing."""
    
    def __init__(self):
        self.audio_processor = AudioInputProcessor()
        self.score_processor = ScoreInputProcessor()
    
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