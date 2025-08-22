#!/usr/bin/env python3
"""
Enhanced Block 1: AMT with Timing Improvements

This enhanced version adds practical improvements to Basic Pitch for better temporal alignment:
1. Onset refinement using librosa
2. Confidence scoring
3. Better error handling and validation
4. Multi-resolution onset detection
5. Timing accuracy improvements

Key improvements for temporal alignment without instrument-specific models.
"""

import argparse
import json
import numpy as np
import librosa
import scipy.signal
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Basic Pitch imports
try:
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH
    # Try different import methods for save functions
    try:
        from basic_pitch import save_midi, save_note_events
    except ImportError:
        try:
            from basic_pitch.inference import save_midi, save_note_events
        except ImportError:
            # Fallback: we'll implement our own MIDI saving
            save_midi = None
            save_note_events = None
except ImportError as e:
    raise ImportError(f"Basic Pitch not available: {e}")

import soundfile as sf

def detect_onsets_multi_resolution(audio_path: str, sr: int = 22050) -> Dict[str, np.ndarray]:
    """
    Detect onsets using multiple methods for better timing accuracy.
    
    Returns dict with different onset detection methods for later fusion.
    """
    print("🎵 Loading audio for onset detection...")
    y, _ = librosa.load(audio_path, sr=sr)
    
    # Method 1: Spectral difference (good for general onsets)
    onset_spectral = librosa.onset.onset_detect(
        y=y, sr=sr, 
        units='time',
        hop_length=512,  # ~23ms resolution
        backtrack=True   # Improve timing accuracy
    )
    
    # Method 2: High-frequency content (good for percussive onsets)
    onset_hfc = librosa.onset.onset_detect(
        y=y, sr=sr,
        units='time',
        onset_envelope=librosa.onset.onset_strength(y=y, sr=sr, feature=librosa.feature.spectral_centroid),
        hop_length=512,
        backtrack=True
    )
    
    # Method 3: Complex domain (good for harmonic onsets)
    onset_complex = librosa.onset.onset_detect(
        y=y, sr=sr,
        units='time',
        onset_envelope=librosa.onset.onset_strength(y=y, sr=sr, feature=librosa.stft),
        hop_length=512,
        backtrack=True
    )
    
    return {
        'spectral': onset_spectral,
        'hfc': onset_hfc, 
        'complex': onset_complex,
        'sr': sr,
        'hop_length': 512
    }

def refine_onset_timing(basic_pitch_notes: List[Dict], onset_detections: Dict[str, np.ndarray], 
                       tolerance: float = 0.05) -> List[Dict]:
    """
    Refine Basic Pitch onset timings using librosa onset detection.
    
    Args:
        basic_pitch_notes: Notes from Basic Pitch
        onset_detections: Multi-resolution onset detections
        tolerance: Maximum time difference to consider for refinement (seconds)
    
    Returns:
        Notes with refined onset timings
    """
    print("🔧 Refining onset timings...")
    
    # Combine onset detections (simple union)
    all_onsets = np.concatenate([
        onset_detections['spectral'],
        onset_detections['hfc'],
        onset_detections['complex']
    ])
    all_onsets = np.unique(all_onsets)  # Remove duplicates
    all_onsets.sort()
    
    refined_notes = []
    
    for note in basic_pitch_notes:
        original_onset = note['onset_time']
        
        # Find closest onset detection within tolerance
        time_diffs = np.abs(all_onsets - original_onset)
        closest_idx = np.argmin(time_diffs)
        closest_onset = all_onsets[closest_idx]
        
        if time_diffs[closest_idx] <= tolerance:
            # Use refined timing
            refined_note = note.copy()
            refined_note['onset_time'] = float(closest_onset)
            refined_note['timing_refined'] = True
            refined_note['original_onset'] = original_onset
            refined_note['timing_improvement'] = abs(original_onset - closest_onset)
        else:
            # Keep original timing
            refined_note = note.copy()
            refined_note['timing_refined'] = False
            refined_note['timing_improvement'] = 0.0
        
        refined_notes.append(refined_note)
    
    # Statistics
    refined_count = sum(1 for n in refined_notes if n.get('timing_refined', False))
    avg_improvement = np.mean([n['timing_improvement'] for n in refined_notes if n['timing_improvement'] > 0])
    
    print(f"   ✅ Refined {refined_count}/{len(refined_notes)} notes")
    if refined_count > 0:
        print(f"   📊 Average timing improvement: {avg_improvement*1000:.1f}ms")
    
    return refined_notes

def add_confidence_scores(notes: List[Dict], audio_path: str) -> List[Dict]:
    """
    Add confidence scores based on audio characteristics around each note.
    
    This helps downstream alignment algorithms weight notes appropriately.
    """
    print("📊 Computing confidence scores...")
    
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Compute spectral features for confidence estimation
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
    
    # Time axis for features
    times = librosa.frames_to_time(np.arange(len(spectral_centroids)), sr=sr)
    
    for note in notes:
        onset_time = note['onset_time']
        
        # Find closest frame
        frame_idx = np.argmin(np.abs(times - onset_time))
        
        # Simple confidence based on spectral characteristics
        # Higher confidence for notes with clear spectral features
        centroid_conf = min(1.0, spectral_centroids[frame_idx] / 4000.0)  # Normalize
        rolloff_conf = min(1.0, spectral_rolloff[frame_idx] / 8000.0)     # Normalize  
        zcr_conf = 1.0 - min(1.0, zero_crossing_rate[frame_idx] * 10)    # Lower ZCR = higher confidence
        
        # Combined confidence score
        confidence = (centroid_conf + rolloff_conf + zcr_conf) / 3.0
        note['confidence'] = float(np.clip(confidence, 0.1, 1.0))  # Ensure reasonable range
    
    return notes

def validate_transcription(notes: List[Dict], audio_path: str, expected_tuning: float = 440.0) -> Dict[str, Any]:
    """
    Validate transcription quality and provide diagnostics.
    
    Returns validation report for debugging and quality assessment.
    """
    print("🔍 Validating transcription...")
    
    if not notes:
        return {'valid': False, 'error': 'No notes transcribed'}
    
    # Basic statistics
    note_count = len(notes)
    duration = max(note['offset_time'] for note in notes) - min(note['onset_time'] for note in notes)
    avg_velocity = np.mean([note.get('velocity', 80) for note in notes])
    
    # Pitch distribution
    pitches = [note['pitch'] for note in notes]
    pitch_range = max(pitches) - min(pitches)
    
    # Timing statistics
    onset_times = [note['onset_time'] for note in notes]
    inter_onset_intervals = np.diff(sorted(onset_times))
    avg_ioi = np.mean(inter_onset_intervals) if len(inter_onset_intervals) > 0 else 0
    
    # Confidence statistics (if available)
    confidences = [note.get('confidence', 1.0) for note in notes]
    avg_confidence = np.mean(confidences)
    
    # Simple tuning check (basic frequency analysis)
    y, sr = librosa.load(audio_path, sr=22050)
    pitches_hz = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))[0]
    detected_fundamental = np.nanmedian(pitches_hz) if len(pitches_hz) > 0 else expected_tuning
    
    tuning_deviation = abs(detected_fundamental - expected_tuning) if detected_fundamental else 0
    tuning_cents = 1200 * np.log2(detected_fundamental / expected_tuning) if detected_fundamental else 0
    
    validation_report = {
        'valid': True,
        'note_count': note_count,
        'duration_sec': round(duration, 2),
        'avg_velocity': round(avg_velocity, 1),
        'pitch_range_semitones': pitch_range,
        'avg_inter_onset_interval': round(avg_ioi, 3),
        'avg_confidence': round(avg_confidence, 3),
        'detected_tuning_hz': round(detected_fundamental, 1) if detected_fundamental else None,
        'tuning_deviation_cents': round(tuning_cents, 1),
        'tuning_ok': abs(tuning_cents) < 50,  # Within 50 cents
        'timing_refined_count': sum(1 for n in notes if n.get('timing_refined', False)),
        'quality_score': min(1.0, avg_confidence * (1.0 - abs(tuning_cents)/100.0))
    }
    
    return validation_report

def transcribe_audio_enhanced(audio_path: str, midi_path: str = 'perf.mid', 
                            notes_path: str = 'perf_notes.json',
                            expected_tuning: float = 440.0) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    Enhanced transcription with timing refinement and validation.
    
    Returns:
        (refined_notes, validation_report)
    """
    print(f"🚀 Starting enhanced transcription of {audio_path}")
    
    # Step 1: Basic Pitch transcription
    print("🎵 Running Basic Pitch transcription...")
    try:
        # Try different API signatures
        try:
            result = predict(audio_path)
        except Exception:
            # Try with model path if needed
            result = predict(audio_path, ICASSP_2022_MODEL_PATH)
        
        # Handle different return types
        if isinstance(result, dict):
            basic_notes = result['note_events']
        elif isinstance(result, tuple):
            # Basic Pitch may return (note_events, onsets, frames)
            basic_notes = result[0]  # note_events is typically first
        else:
            basic_notes = result
            
        print(f"   ✅ Basic Pitch found {len(basic_notes)} notes")
    except Exception as e:
        raise RuntimeError(f"Basic Pitch transcription failed: {e}")
    
    # Step 2: Multi-resolution onset detection
    try:
        onset_detections = detect_onsets_multi_resolution(audio_path)
        total_onsets = sum(len(onsets) for onsets in onset_detections.values() if isinstance(onsets, np.ndarray))
        print(f"   ✅ Detected {total_onsets} onset candidates across methods")
    except Exception as e:
        print(f"   ⚠️  Onset detection failed: {e}, using Basic Pitch timing only")
        onset_detections = {'spectral': np.array([]), 'hfc': np.array([]), 'complex': np.array([])}
    
    # Step 3: Refine timing using onset detection
    try:
        refined_notes = refine_onset_timing(basic_notes, onset_detections)
    except Exception as e:
        print(f"   ⚠️  Timing refinement failed: {e}, using Basic Pitch timing")
        refined_notes = basic_notes
    
    # Step 4: Add confidence scores
    try:
        refined_notes = add_confidence_scores(refined_notes, audio_path)
    except Exception as e:
        print(f"   ⚠️  Confidence scoring failed: {e}, using default confidence")
        for note in refined_notes:
            note['confidence'] = 1.0
    
    # Step 5: Sort by onset time
    refined_notes = sorted(refined_notes, key=lambda x: x['onset_time'])
    
    # Step 6: Save outputs
    try:
        # Save MIDI (using Basic Pitch's method if available, otherwise skip)
        if save_midi is not None:
            save_midi(result, midi_path)
            print(f"   ✅ Saved MIDI: {midi_path}")
        else:
            print(f"   ⚠️  MIDI save not available, saving JSON only")
        
        # Save enhanced JSON with refinements
        output_json = {
            'notes': refined_notes,
            'metadata': {
                'transcription_method': 'basic_pitch_enhanced',
                'timing_refined': True,
                'confidence_scored': True,
                'onset_detection_methods': ['spectral', 'hfc', 'complex']
            }
        }
        
        with open(notes_path, 'w') as f:
            json.dump(output_json, f, indent=2)
        
        print(f"   ✅ Saved notes: {notes_path}")
    except Exception as e:
        print(f"   ⚠️  Save failed: {e}")
    
    # Step 7: Validation
    try:
        validation_report = validate_transcription(refined_notes, audio_path, expected_tuning)
    except Exception as e:
        print(f"   ⚠️  Validation failed: {e}")
        validation_report = {'valid': False, 'error': str(e)}
    
    return refined_notes, validation_report

def main():
    parser = argparse.ArgumentParser(
        description='Enhanced audio transcription with timing refinement for temporal alignment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python transcribe_audio_enhanced.py --audio perf.wav
  
  # With custom tuning
  python transcribe_audio_enhanced.py --audio perf.wav --tuning 442
  
  # Custom output files
  python transcribe_audio_enhanced.py --audio perf.wav --midi output.mid --notes output_notes.json
        """
    )
    
    parser.add_argument('--audio', required=True, help='Path to perf.wav')
    parser.add_argument('--midi', default='perf.mid', help='Output MIDI file')
    parser.add_argument('--notes', default='perf_notes.json', help='Output note events JSON file')
    parser.add_argument('--tuning', type=float, default=440.0, help='Expected tuning frequency (Hz)')
    parser.add_argument('--tolerance', type=float, default=0.05, help='Onset refinement tolerance (seconds)')
    
    args = parser.parse_args()
    
    # Validate input
    if not Path(args.audio).exists():
        print(f"❌ Error: Audio file not found: {args.audio}")
        return 1
    
    try:
        # Run enhanced transcription
        notes, validation = transcribe_audio_enhanced(
            args.audio, args.midi, args.notes, args.tuning
        )
        
        # Print results
        print(f"\n✅ Enhanced transcription complete!")
        print(f"📊 Results:")
        print(f"   Notes: {len(notes)}")
        print(f"   Duration: {validation.get('duration_sec', 'unknown')}s")
        print(f"   Quality score: {validation.get('quality_score', 0.0):.2f}")
        print(f"   Timing refined: {validation.get('timing_refined_count', 0)} notes")
        print(f"   Tuning: {validation.get('detected_tuning_hz', 'unknown')} Hz")
        
        if validation.get('tuning_ok', True):
            print(f"   ✅ Tuning within acceptable range")
        else:
            print(f"   ⚠️  Tuning deviation: {validation.get('tuning_deviation_cents', 0):.1f} cents")
        
        # Show first few notes
        print(f"\n📋 First 10 transcribed notes:")
        for i, note in enumerate(notes[:10]):
            timing_status = "📍" if note.get('timing_refined', False) else "⏰"
            confidence = note.get('confidence', 1.0)
            print(f"   {timing_status} Note {i+1}: pitch={note['pitch']}, "
                  f"onset={note['onset_time']:.3f}s, confidence={confidence:.2f}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
