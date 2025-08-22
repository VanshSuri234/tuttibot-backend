#!/usr/bin/env python3
"""
Block 1: Simple Working AMT

This is a minimal working version that successfully transcribes audio to MIDI/JSON
using Basic Pitch without complex enhancements.
"""

import argparse
import json
import numpy as np
from pathlib import Path

# Basic Pitch imports
try:
    from basic_pitch.inference import predict_and_save, predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
except ImportError as e:
    raise ImportError(f"Basic Pitch not available: {e}")

def transcribe_audio_basic(audio_path: str, output_dir: str = "."):
    """
    Simple transcription using Basic Pitch's built-in functionality
    """
    print(f"🚀 Starting transcription of {audio_path}")
    
    # Use Basic Pitch's predict_and_save for simplicity
    try:
        print("🎵 Running Basic Pitch transcription...")
        
        # This saves MIDI and other outputs directly
        predict_and_save(
            audio_path_list=[audio_path],
            output_directory=output_dir,
            save_midi=True,
            sonify_midi=False,
            save_model_outputs=True,
            save_notes=True
        )
        
        print(f"   ✅ Basic Pitch transcription completed")
        print(f"   📁 Output saved to: {output_dir}")
        
        # Also get raw prediction for analysis
        model_output, midi_data, note_events = predict(audio_path)
        
        print(f"   📊 Found {len(note_events)} note events")
        
        # Convert note events to our JSON format
        notes = []
        for note in note_events:
            notes.append({
                'onset_time': float(note['start_time_s']),
                'offset_time': float(note['end_time_s']),
                'duration': float(note['end_time_s'] - note['start_time_s']),
                'pitch_hz': float(note['pitch_hz']),
                'pitch_midi': int(note['pitch_midi']),
                'confidence': float(note['confidence']),
                'amplitude': float(note['amplitude'])
            })
        
        return notes
        
    except Exception as e:
        print(f"   ❌ Transcription failed: {e}")
        raise RuntimeError(f"Basic Pitch transcription failed: {e}")

def save_transcription_json(notes, output_path: str):
    """Save transcription to JSON format"""
    
    # Calculate statistics
    total_duration = max([n['offset_time'] for n in notes]) if notes else 0
    pitch_range = {
        'min_midi': min([n['pitch_midi'] for n in notes]) if notes else 0,
        'max_midi': max([n['pitch_midi'] for n in notes]) if notes else 0,
    }
    
    transcription = {
        'notes': notes,
        'metadata': {
            'total_notes': len(notes),
            'total_duration_s': total_duration,
            'pitch_range': pitch_range,
            'transcription_method': 'basic_pitch',
            'version': '1.0'
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(transcription, f, indent=2)
    
    print(f"   ✅ Saved JSON transcription to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Simple Working AMT with Basic Pitch')
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--output', help='Output directory (default: current)')
    args = parser.parse_args()
    
    output_dir = args.output or "."
    audio_path = Path(args.audio)
    
    try:
        # Run transcription
        notes = transcribe_audio_basic(str(audio_path), output_dir)
        
        # Save JSON version
        json_path = Path(output_dir) / f"{audio_path.stem}_transcription.json"
        save_transcription_json(notes, str(json_path))
        
        print(f"\n✅ Transcription completed successfully!")
        print(f"📊 Found {len(notes)} notes")
        print(f"📁 MIDI output: {output_dir}/{audio_path.stem}.mid")
        print(f"📁 JSON output: {json_path}")
        
        if notes:
            print(f"\n📈 Statistics:")
            durations = [n['duration'] for n in notes]
            pitches = [n['pitch_midi'] for n in notes]
            print(f"   Duration: {min(durations):.2f}s - {max(durations):.2f}s")
            print(f"   Pitch range: {min(pitches)} - {max(pitches)} MIDI")
            print(f"   Avg confidence: {np.mean([n['confidence'] for n in notes]):.2f}")
            
            print(f"\nFirst few notes:")
            for i, note in enumerate(notes[:5]):
                print(f"  Note {i+1}: MIDI {note['pitch_midi']} ({note['pitch_hz']:.1f}Hz) "
                      f"from {note['onset_time']:.2f}s to {note['offset_time']:.2f}s "
                      f"(conf: {note['confidence']:.2f})")
        
        return 0
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
