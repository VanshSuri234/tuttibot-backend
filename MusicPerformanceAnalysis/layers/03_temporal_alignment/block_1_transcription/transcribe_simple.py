#!/usr/bin/env python3
"""
Simple Basic Pitch Transcription - Just Works Version

Uses Basic Pitch's built-in MIDI writing functionality.
"""

import argparse
import sys
from pathlib import Path

def transcribe_audio(audio_path, output_midi_path):
    """Transcribe audio to MIDI using Basic Pitch"""
    
    print(f"Transcribing: {audio_path}")
    print(f"Output: {output_midi_path}")
    
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
        
        if generated_midi.exists():
            import shutil
            shutil.move(generated_midi, output_midi_path)
            print(f"SUCCESS: Transcription saved to {output_midi_path}")
            return True
        else:
            print(f"ERROR: Expected output file not found: {generated_midi}")
            return False
            
    except Exception as e:
        print(f"ERROR: Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Simple Basic Pitch Audio Transcription')
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--output', required=True, help='Output MIDI file path')
    args = parser.parse_args()
    
    success = transcribe_audio(args.audio, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
