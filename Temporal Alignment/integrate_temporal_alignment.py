import argparse
import os
import sys
import json

# Import Block 0 and Block 1 modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'Block_0_ScoreGraph'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'Block_1_AMT'))
from build_scoregraph import build_scoregraph
from transcribe_audio import transcribe_audio

def main():
    parser = argparse.ArgumentParser(description='Integrate Block 0 (ScoreGraph) and Block 1 (AMT)')
    parser.add_argument('--score', required=True, help='Path to score.musicxml or score.mid')
    parser.add_argument('--meta', required=True, help='Path to score_meta.json')
    parser.add_argument('--audio', required=True, help='Path to perf.wav')
    args = parser.parse_args()

    # Block 0: Build ScoreGraph
    print('Running Block 0: ScoreGraph builder...')
    scoregraph = build_scoregraph(args.score, args.meta)
    scoregraph_path = os.path.join(os.path.dirname(__file__), 'Block_0_ScoreGraph', 'scoregraph.json')
    with open(scoregraph_path, 'w') as f:
        json.dump(scoregraph, f, indent=2)
    print('ScoreGraph output saved to:', scoregraph_path)
    print('First 10 nodes:')
    for node in scoregraph['nodes'][:10]:
        print(node)

    # Block 1: AMT Transcription
    print('\nRunning Block 1: AMT transcription...')
    midi_path = os.path.join(os.path.dirname(__file__), 'Block_1_AMT', 'perf.mid')
    notes_path = os.path.join(os.path.dirname(__file__), 'Block_1_AMT', 'perf_notes.json')
    notes_sorted = transcribe_audio(args.audio, midi_path, notes_path)
    print('AMT output saved to:', midi_path, 'and', notes_path)
    print('First 20 note events:')
    for note in notes_sorted[:20]:
        print(note)

if __name__ == '__main__':
    main()
