#!/usr/bin/env python3
"""
Simple AMT Fallback using librosa for note detection when Basic Pitch fails
"""

import librosa
import numpy as np
import json
from pathlib import Path

def simple_amt_fallback(audio_path: str, output_dir: str = ".") -> dict:
    """
    Simple AMT using librosa onset detection and pitch estimation
    This is a basic fallback when Basic Pitch fails
    """
    print(f"🎵 Using simple AMT fallback for {audio_path}")
    
    # Load audio
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Onset detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    print(f"   🎯 Detected {len(onset_frames)} onsets")
    
    # Pitch estimation using harmonic-percussive separation
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    
    # Get pitches using a simple method
    pitches, magnitudes = librosa.piptrack(y=y_harmonic, sr=sr, threshold=0.1)
    
    # Create simple note events
    notes = []
    hop_length = 512
    frame_rate = sr / hop_length
    
    for i, onset_time in enumerate(onset_frames):
        # Estimate offset time (next onset or end of audio)
        if i + 1 < len(onset_frames):
            offset_time = onset_frames[i + 1]
        else:
            offset_time = len(y) / sr
            
        duration = offset_time - onset_time
        
        # Find the most prominent pitch around this onset
        onset_frame = int(onset_time * frame_rate)
        
        # Look for pitch in a small window around the onset
        window_start = max(0, onset_frame - 5)
        window_end = min(pitches.shape[1], onset_frame + 5)
        
        pitch_window = pitches[:, window_start:window_end]
        mag_window = magnitudes[:, window_start:window_end]
        
        # Find the bin with maximum magnitude
        max_mag_idx = np.unravel_index(np.argmax(mag_window), mag_window.shape)
        
        if mag_window[max_mag_idx] > 0:
            pitch_hz = pitch_window[max_mag_idx]
            if pitch_hz > 0:
                pitch_midi = librosa.hz_to_midi(pitch_hz)
            else:
                pitch_midi = 60  # Default to C4
                pitch_hz = librosa.midi_to_hz(pitch_midi)
        else:
            # Fallback estimation based on position
            pitch_midi = 60 + (i % 12)  # Simple pattern
            pitch_hz = librosa.midi_to_hz(pitch_midi)
        
        notes.append({
            'onset_time': float(onset_time),
            'offset_time': float(offset_time), 
            'duration': float(duration),
            'pitch_hz': float(pitch_hz),
            'pitch_midi': int(pitch_midi),
            'confidence': 0.5,  # Fixed confidence for simple method
            'amplitude': float(mag_window[max_mag_idx] if mag_window[max_mag_idx] > 0 else 0.5)
        })
    
    print(f"   ✅ Generated {len(notes)} note events")
    
    # Save JSON output
    transcription = {
        'notes': notes,
        'metadata': {
            'total_notes': len(notes),
            'total_duration_s': float(len(y) / sr),
            'pitch_range': {
                'min_midi': int(min([n['pitch_midi'] for n in notes])) if notes else 60,
                'max_midi': int(max([n['pitch_midi'] for n in notes])) if notes else 60,
            },
            'transcription_method': 'simple_librosa_fallback',
            'version': '1.0'
        }
    }
    
    # Save to file
    output_path = Path(output_dir) / 'transcription.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(transcription, f, indent=2)
    
    print(f"   📁 Saved transcription to {output_path}")
    
    return transcription

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python simple_amt_fallback.py <audio_path> [output_dir]")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    result = simple_amt_fallback(audio_path, output_dir)
    print(f"Transcription complete: {result['metadata']['total_notes']} notes")
