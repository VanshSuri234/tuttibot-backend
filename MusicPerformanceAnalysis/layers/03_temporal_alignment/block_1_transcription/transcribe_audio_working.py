#!/usr/bin/env python3
"""
Enhanced Block 1: Working AMT with Basic Improvements

Simplified version that focuses on working functionality.
"""

import argparse
import json
import numpy as np
from pathlib import Path

# Basic Pitch imports
try:
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
except ImportError as e:
    raise ImportError(f"Basic Pitch not available: {e}")

def transcribe_audio_simple(audio_path: str):
    """Simple working transcription with Basic Pitch"""
    print(f"🚀 Starting transcription of {audio_path}")
    
    # Basic Pitch transcription
    print("🎵 Running Basic Pitch transcription...")
    try:
        result = predict(audio_path)
        print(f"   ✅ Basic Pitch completed")
        print(f"   📊 Result type: {type(result)}")
        
        if isinstance(result, tuple):
            print(f"   📊 Tuple length: {len(result)}")
            # Basic Pitch returns (note_events, onsets, contours)
            note_events, onsets, contours = result
            print(f"   📊 Note events shape: {note_events.shape}")
            print(f"   📊 Onsets shape: {onsets.shape}")
            print(f"   📊 Contours shape: {contours.shape}")
            
            # Convert to note list format
            notes = []
            # Find note activations (simplified)
            note_threshold = 0.5
            onset_threshold = 0.5
            
            # Get time resolution
            time_step = 0.01  # 10ms steps typical for Basic Pitch
            
            # Simple note extraction
            for pitch_idx in range(note_events.shape[1]):
                for time_idx in range(note_events.shape[0]):
                    if note_events[time_idx, pitch_idx] > note_threshold:
                        # Found a note
                        start_time = time_idx * time_step
                        
                        # Find end of note
                        end_time_idx = time_idx
                        while (end_time_idx < note_events.shape[0] - 1 and 
                               note_events[end_time_idx + 1, pitch_idx] > note_threshold):
                            end_time_idx += 1
                        
                        end_time = end_time_idx * time_step
                        
                        # Skip very short notes
                        if end_time - start_time > 0.05:  # 50ms minimum
                            pitch_hz = 440 * (2 ** ((pitch_idx - 69) / 12))  # A4 = 440Hz
                            pitch_midi = pitch_idx + 21  # C0 = 21
                            
                            note = {
                                'onset_time': start_time,
                                'offset_time': end_time,
                                'duration': end_time - start_time,
                                'pitch_hz': pitch_hz,
                                'pitch_midi': pitch_midi,
                                'confidence': float(note_events[time_idx, pitch_idx])
                            }
                            notes.append(note)
                        
                        # Skip ahead to avoid duplicate detections
                        time_idx = end_time_idx
            
            print(f"   ✅ Extracted {len(notes)} notes")
            
        else:
            print(f"   ❌ Unexpected result format: {type(result)}")
            notes = []
            
    except Exception as e:
        print(f"   ❌ Transcription failed: {e}")
        raise RuntimeError(f"Basic Pitch transcription failed: {e}")
    
    return notes

def save_transcription(notes, output_path: str):
    """Save transcription to JSON"""
    transcription = {
        'notes': notes,
        'total_notes': len(notes),
        'metadata': {
            'transcription_method': 'enhanced_basic_pitch',
            'version': '1.0'
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(transcription, f, indent=2)
    
    print(f"   ✅ Saved transcription to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced AMT with Basic Pitch')
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--output', help='Output JSON path (default: transcription.json)')
    args = parser.parse_args()
    
    output_path = args.output or 'transcription.json'
    
    try:
        notes = transcribe_audio_simple(args.audio)
        save_transcription(notes, output_path)
        
        print(f"\n✅ Transcription completed successfully!")
        print(f"📊 Found {len(notes)} notes")
        
        if notes:
            print("\nFirst few notes:")
            for i, note in enumerate(notes[:5]):
                print(f"  Note {i+1}: {note['pitch_midi']:.0f} ({note['pitch_hz']:.1f}Hz) "
                      f"from {note['onset_time']:.2f}s to {note['offset_time']:.2f}s "
                      f"(conf: {note['confidence']:.2f})")
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return 1

if __name__ == '__main__':
    main()
