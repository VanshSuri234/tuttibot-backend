#!/usr/bin/env python3
"""
Enhanced Basic Pitch Transcription with Transposition and Octave Correction

Adds support for:
1. Transposing instruments (Bb, Eb, F, etc.)
2. Octave correction for bass instruments
3. Automatic instrument detection from filename
"""

import argparse
import sys
import re
from pathlib import Path
import pretty_midi
import numpy as np


# Instrument transpositions (in semitones)
TRANSPOSITIONS = {
    'clarinet': 2,      # Bb clarinet: sounds whole tone lower, written 2 semitones higher
    'saxophone': 2,     # Bb saxophone (default)
    'saxphone': 2,      # Handle misspelling in dataset
    'sax': 2,
    'tenor_sax': 2,     # Bb tenor sax
    'soprano_sax': 2,   # Bb soprano sax
    'alto_sax': -3,     # Eb alto sax: sounds major 6th lower, written 3 semitones lower (in concert pitch)
    'baritone_sax': -3, # Eb baritone sax
    'trumpet': 2,       # Bb trumpet
    'cornet': 2,        # Bb cornet
    'horn': -7,         # F horn: sounds perfect 5th lower
    'french_horn': -7,
    'english_horn': -7, # F english horn
}

# Bass instruments that often get transcribed an octave too high
BASS_INSTRUMENTS = [
    'bassoon',
    'contrabassoon',
    'cello',
    'bass',
    'double_bass',
    'contrabass',
    'tuba',
    'bass_clarinet',
    'baritone_sax',
]


def detect_instrument_from_filename(audio_path):
    """
    Detect instrument type from filename
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        str: Instrument name or None
    """
    filename = Path(audio_path).stem.lower()
    
    # Check for each known instrument
    for instrument in list(TRANSPOSITIONS.keys()) + BASS_INSTRUMENTS:
        if instrument.replace('_', '') in filename.replace('_', '').replace('-', ''):
            return instrument
    
    return None


def correct_octave_for_bass_instrument(midi_data, instrument_name):
    """
    Correct octave for bass instruments that are transcribed too high
    
    Args:
        midi_data: PrettyMIDI object
        instrument_name: Name of instrument
        
    Returns:
        bool: True if correction was applied
    """
    if instrument_name not in BASS_INSTRUMENTS:
        return False
    
    # Analyze average pitch
    all_notes = []
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            all_notes.append(note.pitch)
    
    if not all_notes:
        return False
    
    avg_pitch = np.mean(all_notes)
    
    # Bass instruments should typically be well below middle C (MIDI 60)
    # Bassoon range: Bb1 (MIDI 34) to Eb5 (MIDI 75), typical playing range C2-C4 (MIDI 36-60)
    # DISABLED: Octave correction disabled - causing overcorrection
    # If needed, threshold should be instrument-specific and more conservative
    octave_shift = 0
    
    # if avg_pitch > 72:  # Above C5 - definitely too high for bass instrument
    #     octave_shift = -24  # Down 2 octaves
    #     print(f"  Detected very high pitch for {instrument_name} (avg={avg_pitch:.1f})")
    #     print(f"  Applying -2 octave correction")
    # elif avg_pitch > 54:  # Above F#3 - likely too high for bass instruments
    #     octave_shift = -12  # Down 1 octave
    #     print(f"  Detected high pitch for {instrument_name} (avg={avg_pitch:.1f})")
    #     print(f"  Applying -1 octave correction")
    
    if octave_shift != 0:
        for instrument in midi_data.instruments:
            for note in instrument.notes:
                note.pitch = max(0, min(127, note.pitch + octave_shift))
        return True
    
    return False


def apply_transposition(midi_data, semitones):
    """
    Transpose all notes in MIDI by specified semitones
    
    Args:
        midi_data: PrettyMIDI object
        semitones: Number of semitones to transpose (positive = up, negative = down)
    """
    if semitones == 0:
        return
    
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            # Transpose and clamp to valid MIDI range (0-127)
            note.pitch = max(0, min(127, note.pitch + semitones))


def transcribe_audio(audio_path, output_midi_path):
    """
    Transcribe audio to MIDI using Basic Pitch with transposition correction
    
    Args:
        audio_path: Path to audio file
        output_midi_path: Path for output MIDI file
        
    Returns:
        bool: True if successful
    """
    
    print(f"Transcribing: {audio_path}")
    print(f"Output: {output_midi_path}")
    
    # Detect instrument
    instrument_name = detect_instrument_from_filename(audio_path)
    if instrument_name:
        print(f"  Detected instrument: {instrument_name}")
    
    try:
        from basic_pitch.inference import predict_and_save
        from basic_pitch import ICASSP_2022_MODEL_PATH
        
        # Use Basic Pitch's built-in MIDI writing
        predict_and_save(
            audio_path_list=[str(audio_path)],
            output_directory=str(Path(output_midi_path).parent),
            save_midi=True,
            sonify_midi=False,
            save_model_outputs=False,
            save_notes=False,
            model_or_model_path=ICASSP_2022_MODEL_PATH
        )
        
        # Basic Pitch saves with the audio filename, rename to our desired name
        audio_name = Path(audio_path).stem
        generated_midi = Path(output_midi_path).parent / f"{audio_name}_basic_pitch.mid"
        
        if not generated_midi.exists():
            print(f"ERROR: Expected output file not found: {generated_midi}")
            return False
        
        # Load MIDI for post-processing
        midi_data = pretty_midi.PrettyMIDI(str(generated_midi))
        
        # Track what corrections we apply
        corrections_applied = []
        
        # Step 1: Correct octave for bass instruments
        if instrument_name and instrument_name in BASS_INSTRUMENTS:
            if correct_octave_for_bass_instrument(midi_data, instrument_name):
                corrections_applied.append("octave correction")
        
        # Step 2: Apply transposition for transposing instruments
        if instrument_name and instrument_name in TRANSPOSITIONS:
            semitones = TRANSPOSITIONS[instrument_name]
            print(f"  Applying transposition: {semitones:+d} semitones")
            apply_transposition(midi_data, semitones)
            corrections_applied.append(f"transposition {semitones:+d}ST")
        
        # Save corrected MIDI
        midi_data.write(str(output_midi_path))
        
        # Clean up original
        if generated_midi.exists() and generated_midi != Path(output_midi_path):
            generated_midi.unlink()
        
        if corrections_applied:
            print(f"  Applied corrections: {', '.join(corrections_applied)}")
        
        print(f"SUCCESS: Transcription saved to {output_midi_path}")
        
        # Print MIDI statistics
        all_pitches = []
        total_notes = 0
        for instrument in midi_data.instruments:
            total_notes += len(instrument.notes)
            for note in instrument.notes:
                all_pitches.append(note.pitch)
        
        if all_pitches:
            print(f"  Total notes: {total_notes}")
            print(f"  Pitch range: {min(all_pitches)} - {max(all_pitches)} (avg: {np.mean(all_pitches):.1f})")
        
        return True
            
    except Exception as e:
        print(f"ERROR: Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Basic Pitch Audio Transcription with Transposition Support'
    )
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--output', required=True, help='Output MIDI file path')
    parser.add_argument('--instrument', help='Force instrument type (optional)')
    args = parser.parse_args()
    
    success = transcribe_audio(args.audio, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
