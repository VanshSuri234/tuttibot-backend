import argparse
import json
import partitura
from partitura import load_score
from partitura.score import Score

# Helper to expand repeats/voltas and build canonical timeline
def build_scoregraph(score_path, meta_path, seg_path=None):
    # Load score (MusicXML or MIDI)
    score = load_score(score_path)
    # Load meta info
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    # Optionally load segmentation
    segmentation = None
    if seg_path:
        with open(seg_path, 'r') as f:
            segmentation = json.load(f)
    # Expand repeats/voltas
    score.expand_repeats()
    # Build bars and nodes
    bars = []
    nodes = []
    abs_beat = 0.0
    for bar in score.bars:
        bar_dict = {
            'bar': bar.number,
            'time_sig': f"{bar.time_signature_numerator}/{bar.time_signature_denominator}",
            'downbeat_abs_beat': abs_beat
        }
        bars.append(bar_dict)
        for beat in range(1, bar.time_signature_numerator + 1):
            node_id = f"{bar.number}_{beat}"
            D_beats = 1.0  # Duration in beats (can be refined)
            flags = []
            # Attach flags from meta or segmentation
            if 'fermatas' in meta and node_id in meta['fermatas']:
                flags.append('fermata')
            if segmentation and 'cadences' in segmentation and node_id in segmentation['cadences']:
                flags.append('cadence')
            node = {
                'id': node_id,
                'bar': bar.number,
                'beat': beat,
                'abs_beat': abs_beat,
                'D_beats': D_beats,
                'flags': flags
            }
            nodes.append(node)
            abs_beat += D_beats
    # Tempo marks, key signature, tuning
    tempo_marks = meta.get('tempo_marks', [])
    key_signature = meta.get('key_signature', None)
    tuning_hz = meta.get('tuning_hz', 440)
    # Mapping helpers
    maps = {
        'bar_beat_to_abs_beat': {f"{n['bar']},{n['beat']}": n['abs_beat'] for n in nodes},
        'abs_beat_to_bar_beat': {str(n['abs_beat']): (n['bar'], n['beat']) for n in nodes}
    }
    scoregraph = {
        'bars': bars,
        'nodes': nodes,
        'tempo_marks': tempo_marks,
        'key_signature': key_signature,
        'tuning_hz': tuning_hz,
        'maps': maps
    }
    return scoregraph

def main():
    parser = argparse.ArgumentParser(description='Build ScoreGraph from MusicXML/MIDI and meta info')
    parser.add_argument('--score', required=True, help='Path to score.musicxml or score.mid')
    parser.add_argument('--meta', required=True, help='Path to score_meta.json')
    parser.add_argument('--seg', help='Path to segmentation.json (optional)')
    args = parser.parse_args()
    scoregraph = build_scoregraph(args.score, args.meta, args.seg)
    with open('scoregraph.json', 'w') as f:
        json.dump(scoregraph, f, indent=2)
    print('First 10 nodes:')
    for node in scoregraph['nodes'][:10]:
        print(node)

if __name__ == '__main__':
    main()
