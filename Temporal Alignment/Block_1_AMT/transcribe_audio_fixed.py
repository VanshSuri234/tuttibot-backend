#!/usr/bin/env python3
"""
Block 1: PROPERLY WORKING AMT with Basic Pitch (GPU-Ready)

This version uses the correct Basic Pitch API and properly handles the output format.
Enhanced with GPU detection, automatic fallback, and memory management.
Based on successful CLI testing, this should work end-to-end.
"""

import argparse
import json
import numpy as np
import subprocess
import pandas as pd
from pathlib import Path
import tempfile
import shutil
import os
import sys

# Add parent directory to path for GPU manager import
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

def transcribe_audio_basic_pitch(audio_path: str, output_dir: str = None, gpu_manager=None) -> dict:
    """
    Transcribe audio using Basic Pitch CLI (which we know works)
    Enhanced with GPU support and automatic device selection
    Then parse the output files to get structured data
    """
    print(f"Starting Basic Pitch transcription of {audio_path}")
    
    # Import GPU manager if not provided
    if gpu_manager is None:
        try:
            from gpu_manager import GPUManager
            gpu_manager = GPUManager()
        except ImportError:
            print("Warning: GPU manager not available, using default settings")
            gpu_manager = None
    
    # Log device configuration
    if gpu_manager:
        device_type = "GPU" if gpu_manager.device_config['use_gpu'] else "CPU"
        print(f"AMT Device: {device_type}")
        if gpu_manager.device_config['use_gpu']:
            print(f"GPU ID: {gpu_manager.device_config['device_id']}")
            
            # Monitor GPU memory before transcription
            memory_info = gpu_manager.monitor_gpu_memory()
            if memory_info:
                print(f"GPU Memory: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
    
    # Create temporary directory if no output specified
    if output_dir is None:
        temp_dir = tempfile.mkdtemp()
        output_dir = temp_dir
        cleanup_temp = True
    else:
        cleanup_temp = False
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Prepare Basic Pitch command
        print("Running Basic Pitch CLI...")
        cmd = [
            'basic-pitch', 
            output_dir, 
            audio_path,
            '--save-midi',
            '--save-note-events'
        ]
        
        # Add GPU/device specific options if available
        if gpu_manager and gpu_manager.device_config['use_gpu']:
            # Set environment variables for GPU usage
            env = os.environ.copy()
            env['CUDA_VISIBLE_DEVICES'] = str(gpu_manager.device_config['device_id'])
            # Basic Pitch should automatically use GPU if available
            print(f"Using GPU {gpu_manager.device_config['device_id']} for transcription")
        else:
            env = os.environ.copy()
            # Force CPU mode if needed
            env['CUDA_VISIBLE_DEVICES'] = ''
            print("Using CPU for transcription")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # Increased timeout for GPU operations
            env=env
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Basic Pitch failed: {result.stderr}")
        
        print("   Basic Pitch CLI completed successfully")
        
        # Find the generated files
        audio_stem = Path(audio_path).stem
        csv_file = Path(output_dir) / f"{audio_stem}_basic_pitch.csv"
        midi_file = Path(output_dir) / f"{audio_stem}_basic_pitch.mid"
        
        if not csv_file.exists():
            raise FileNotFoundError(f"Expected CSV file not found: {csv_file}")
        
        # Parse CSV file to get note events
        print("Parsing note events...")
        
        # Read CSV manually to handle malformed rows
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        # Parse header
        header = lines[0].strip().split(',')
        expected_cols = ['start_time_s', 'end_time_s', 'pitch_midi', 'velocity', 'pitch_bend']
        
        notes = []
        for line_num, line in enumerate(lines[1:], 2):
            try:
                # Split and take only the first 5 columns we need
                values = line.strip().split(',')
                if len(values) >= 4:  # At least start, end, pitch, velocity
                    start_time = float(values[0])
                    end_time = float(values[1])
                    pitch_midi = int(float(values[2]))  # Convert to float first to handle decimals
                    velocity = int(float(values[3])) if len(values) > 3 else 127
                    
                    # Skip very short notes or invalid data
                    if end_time > start_time and 0 <= pitch_midi <= 127:
                        note = {
                            'onset_time': start_time,
                            'offset_time': end_time,
                            'duration': end_time - start_time,
                            'pitch_midi': pitch_midi,
                            'pitch_hz': 440.0 * (2.0 ** ((pitch_midi - 69) / 12.0)),
                            'velocity': min(127, max(1, velocity)),  # Clamp to valid MIDI range
                            'confidence': 1.0
                        }
                        notes.append(note)
            except (ValueError, IndexError) as e:
                print(f"   Warning: Skipping malformed line {line_num}: {e}")
                continue
        
        print(f"   Parsed {len(notes)} notes from CSV")
        
        # Calculate statistics
        if notes:
            durations = [n['duration'] for n in notes]
            pitches = [n['pitch_midi'] for n in notes]
            total_duration = max([n['offset_time'] for n in notes])
        else:
            durations = [0]
            pitches = [0]
            total_duration = 0
        
        result_data = {
            'notes': notes,
            'metadata': {
                'total_notes': len(notes),
                'total_duration_s': total_duration,
                'pitch_range': {
                    'min_midi': min(pitches) if pitches else 0,
                    'max_midi': max(pitches) if pitches else 0,
                },
                'duration_stats': {
                    'min_duration': min(durations) if durations else 0,
                    'max_duration': max(durations) if durations else 0,
                    'avg_duration': np.mean(durations) if durations else 0
                },
                'transcription_method': 'basic_pitch_cli',
                'version': '1.0',
                'source_files': {
                    'csv': str(csv_file),
                    'midi': str(midi_file) if midi_file.exists() else None
                }
            }
        }
        
        return result_data
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Basic Pitch transcription timed out")
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")
    finally:
        # Cleanup temporary directory if we created it
        if cleanup_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)

def save_transcription(transcription_data: dict, output_path: str):
    """Save transcription data to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(transcription_data, f, indent=2)
    print(f"   Saved transcription to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Working AMT with Basic Pitch CLI')
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--output-dir', help='Output directory for Basic Pitch files')
    parser.add_argument('--json-output', help='JSON output file (default: transcription.json)')
    args = parser.parse_args()
    
    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return 1
    
    output_dir = args.output_dir or "output"
    json_output = args.json_output or "transcription.json"
    
    try:
        # Run transcription
        transcription_data = transcribe_audio_basic_pitch(str(audio_path), output_dir)
        
        # Save JSON version
        save_transcription(transcription_data, json_output)
        
        # Print results
        notes = transcription_data['notes']
        metadata = transcription_data['metadata']
        
        print(f"\nTranscription completed successfully!")
        print(f"Found {len(notes)} notes")
        print(f"Total duration: {metadata['total_duration_s']:.2f}s")
        print(f"Pitch range: {metadata['pitch_range']['min_midi']} - {metadata['pitch_range']['max_midi']} MIDI")
        print(f"MIDI file: {metadata['source_files']['midi']}")
        print(f"JSON file: {json_output}")
        
        if notes:
            print(f"\nFirst few notes:")
            for i, note in enumerate(notes[:5]):
                print(f"  Note {i+1}: MIDI {note['pitch_midi']} ({note['pitch_hz']:.1f}Hz) "
                      f"from {note['onset_time']:.2f}s to {note['offset_time']:.2f}s "
                      f"(vel: {note['velocity']})")
            
            print(f"\nStatistics:")
            print(f"   Avg duration: {metadata['duration_stats']['avg_duration']:.3f}s")
            print(f"   Min duration: {metadata['duration_stats']['min_duration']:.3f}s")
            print(f"   Max duration: {metadata['duration_stats']['max_duration']:.3f}s")
        
        return 0
        
    except Exception as e:
        print(f"Error: Transcription failed: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
