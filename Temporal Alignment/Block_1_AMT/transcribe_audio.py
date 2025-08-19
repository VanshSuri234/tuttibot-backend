import argparse
import json
import numpy as np
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
from basic_pitch import save_midi, save_note_events
import soundfile as sf
import os

# Helper to run Basic Pitch AMT and save outputs
def transcribe_audio(audio_path, midi_path, notes_path):
    # Run Basic Pitch prediction
    output_dict = predict(audio_path, model_path=ICASSP_2022_MODEL_PATH)
    # Save MIDI
    save_midi(output_dict, midi_path)
    # Save note events JSON
    notes = output_dict['note_events']
    notes_sorted = sorted(notes, key=lambda x: x['onset_time'])
    with open(notes_path, 'w') as f:
        json.dump({'notes': notes_sorted}, f, indent=2)
    return notes_sorted

def main():
    parser = argparse.ArgumentParser(description='Transcribe audio to MIDI and note events using Basic Pitch')
    parser.add_argument('--audio', required=True, help='Path to perf.wav')
    parser.add_argument('--midi', default='perf.mid', help='Output MIDI file')
    parser.add_argument('--notes', default='perf_notes.json', help='Output note events JSON file')
    args = parser.parse_args()
    notes_sorted = transcribe_audio(args.audio, args.midi, args.notes)
    print('First 20 note events:')
    for note in notes_sorted[:20]:
        print(note)

if __name__ == '__main__':
    main()
