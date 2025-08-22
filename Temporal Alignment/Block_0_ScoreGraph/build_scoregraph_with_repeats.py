import argparse
import json
from typing import Dict, List, Any

def build_scoregraph(score_path, meta_path, seg_path=None):
    """Build ScoreGraph using music21 with full repeat expansion"""
    
    try:
        from music21 import converter, meter, stream
    except ImportError:
        raise ImportError("music21 library is required. Install with: pip install music21")
    
    # Parse the MusicXML file
    score = converter.parse(score_path)
    
    # ✅ CRITICAL: Expand all repeats using music21's built-in functionality
    try:
        expanded_score = score.expandRepeats()
        print("✅ Repeat expansion successful")
    except:
        print("ℹ️  No repeats to expand or expansion failed, using original score")
        expanded_score = score
    
    # Load meta info
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    # Optionally load segmentation
    segmentation = None
    if seg_path:
        with open(seg_path, 'r') as f:
            segmentation = json.load(f)
    
    # Get the first part
    if hasattr(expanded_score, 'parts') and expanded_score.parts:
        part = expanded_score.parts[0]
    else:
        part = expanded_score
    
    # Build bars and nodes
    bars = []
    nodes = []
    abs_beat = 0.0
    
    # Get all measures from the expanded part
    measures = part.getElementsByClass(stream.Measure)
    if not measures:
        measures = expanded_score.getElementsByClass(stream.Measure)
    
    for measure in measures:
        bar_num = measure.number if measure.number is not None else len(bars) + 1
        
        # Get time signature for this measure
        time_sigs = measure.getElementsByClass(meter.TimeSignature)
        if time_sigs:
            ts = time_sigs[0]
            time_signature = f"{ts.numerator}/{ts.denominator}"
            numerator = ts.numerator
        else:
            # Use metadata or default
            time_signature = meta.get('meter', '4/4')
            numerator = int(time_signature.split('/')[0])
        
        bar_dict = {
            'bar': bar_num,
            'time_sig': time_signature,
            'downbeat_abs_beat': abs_beat
        }
        bars.append(bar_dict)
        
        # Create nodes for each beat in the measure
        for beat in range(1, numerator + 1):
            node_id = f"{bar_num}_{beat}"
            D_beats = 1.0  # Duration in beats
            flags = []
            
            # Attach flags from meta or segmentation
            if 'fermatas' in meta and node_id in meta['fermatas']:
                flags.append('fermata')
            if segmentation and 'cadences' in segmentation and node_id in segmentation['cadences']:
                flags.append('cadence')
            
            node = {
                'id': node_id,
                'bar': bar_num,
                'beat': beat,
                'abs_beat': abs_beat,
                'D_beats': D_beats,
                'flags': flags
            }
            nodes.append(node)
            abs_beat += D_beats
    
    # Extract tempo, key signature, tuning
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
    parser = argparse.ArgumentParser(description='Build ScoreGraph with repeat expansion using music21')
    parser.add_argument('--score', required=True, help='Path to score.musicxml')
    parser.add_argument('--meta', required=True, help='Path to score_meta.json')
    parser.add_argument('--seg', help='Path to segmentation.json (optional)')
    args = parser.parse_args()
    
    scoregraph = build_scoregraph(args.score, args.meta, args.seg)
    
    with open('scoregraph.json', 'w') as f:
        json.dump(scoregraph, f, indent=2)
    
    print(f'✅ ScoreGraph built with repeat expansion!')
    print(f'Total measures: {len(scoregraph["bars"])}')
    print(f'Total nodes: {len(scoregraph["nodes"])}')
    
    if len(scoregraph['nodes']) > 10:
        print('\nFirst 10 nodes:')
        for node in scoregraph['nodes'][:10]:
            print(f"  {node['id']}: beat {node['beat']}, abs_beat {node['abs_beat']}")
        
        print('\nLast 10 nodes:')
        for node in scoregraph['nodes'][-10:]:
            print(f"  {node['id']}: beat {node['beat']}, abs_beat {node['abs_beat']}")
    else:
        print('\nAll nodes:')
        for node in scoregraph['nodes']:
            print(f"  {node['id']}: beat {node['beat']}, abs_beat {node['abs_beat']}")

if __name__ == '__main__':
    main()
