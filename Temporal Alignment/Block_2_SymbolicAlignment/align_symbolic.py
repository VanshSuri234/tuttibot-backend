import argparse
import json
import random
import matplotlib.pyplot as plt
from parangonar import DualDTWNoteMatcher
import partitura
from partitura import load_score, load_match
from partitura.musicanalysis import midi_to_note_array

# Helper to run symbolic alignment and save outputs
def align_symbolic(score_path, scoregraph_path, perf_midi_path, match_path, time_map_path):
    # Load score
    score = load_score(score_path)
    # Load scoregraph
    with open(scoregraph_path, 'r') as f:
        scoregraph = json.load(f)
    # Load performance MIDI
    perf_note_array = midi_to_note_array(perf_midi_path)
    # Run Parangonar alignment
    matcher = DualDTWNoteMatcher()
    match = matcher.match(score.note_array(), perf_note_array)
    # Save alignment.match
    partitura.io.exportmatch(match, match_path)
    # Build dense time map
    hop_sec = 0.01
    path = []
    for m in match:
        score_abs_beat = m['score_abs_beat'] if 'score_abs_beat' in m else m['score_note']['abs_beat']
        perf_time_sec = m['perf_onset_sec'] if 'perf_onset_sec' in m else m['perf_note']['onset_sec']
        path.append([score_abs_beat, perf_time_sec])
    time_map = {
        'method': 'Parangonar.DualDTWNoteMatcher',
        'hop_sec': hop_sec,
        'path': path
    }
    with open(time_map_path, 'w') as f:
        json.dump(time_map, f, indent=2)
    # Plot 30 random matched notes
    if len(path) >= 30:
        sample = random.sample(path, 30)
    else:
        sample = path
    plt.scatter([x[0] for x in sample], [x[1] for x in sample])
    plt.xlabel('Score abs_beat')
    plt.ylabel('Performance time (sec)')
    plt.title('Random Matched Notes')
    plt.savefig('alignment_sample.png')
    plt.close()
    print('Plotted 30 random matched notes to alignment_sample.png')


def main():
    parser = argparse.ArgumentParser(description='Align score and performance MIDI using Parangonar')
    parser.add_argument('--score', required=True, help='Path to score.musicxml or score.mid')
    parser.add_argument('--scoregraph', required=True, help='Path to scoregraph.json')
    parser.add_argument('--perf', required=True, help='Path to perf.mid')
    parser.add_argument('--match', default='alignment.match', help='Output MATCH file')
    parser.add_argument('--timemap', default='time_map.json', help='Output time map JSON file')
    args = parser.parse_args()
    align_symbolic(args.score, args.scoregraph, args.perf, args.match, args.timemap)
    print('Alignment and time map generated.')

if __name__ == '__main__':
    main()
