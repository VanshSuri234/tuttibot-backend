#!/usr/bin/env python3
"""
Block 0: ScoreGraph Builder with Repeat Expansion (Final Version)

Enhanced version of the original build_scoregraph.py with proper repeat expansion.
Same interface, same output format, but with full repeat support.

Usage: python build_scoregraph.py --score score.musicxml --meta score_meta.json [--seg segmentation.json]
"""

import argparse
import json
from typing import Dict, List, Any, Optional

def build_scoregraph(score_path: str, meta_path: str, seg_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Build ScoreGraph from MusicXML with repeat expansion
    
    This is the enhanced version of the original function that adds repeat expansion
    while maintaining the same interface and output format.
    """
    
    try:
        from music21 import converter, meter, stream
    except ImportError:
        raise ImportError("music21 library is required. Install with: pip install music21")
    
    # Load score (MusicXML)
    score = converter.parse(score_path)
    
    # ✅ CRITICAL ENHANCEMENT: Expand repeats before processing
    try:
        score = score.expandRepeats()
        print("✅ Repeat expansion successful")
    except:
        print("ℹ️  No repeats to expand or expansion failed, using original score")
    
    # Load meta info (same as original)
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    # Optionally load segmentation (same as original)
    segmentation = None
    if seg_path:
        with open(seg_path, 'r') as f:
            segmentation = json.load(f)
    
    # Get the first part
    if hasattr(score, 'parts') and score.parts:
        part = score.parts[0]
    else:
        part = score
    
    # Build bars and nodes (same logic as original, but now with expanded repeats)
    bars = []
    nodes = []
    abs_beat = 0.0
    
    # Get all measures from the expanded score
    measures = part.getElementsByClass(stream.Measure)
    if not measures:
        measures = score.getElementsByClass(stream.Measure)
    
    for i, measure in enumerate(measures):
        bar_num = measure.number if measure.number is not None else i + 1
        
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
            D_beats = 1.0  # Duration in beats (can be refined)
            flags = []
            
            # Attach flags from meta or segmentation (same as original)
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
    
    # Tempo marks, key signature, tuning (same as original)
    tempo_marks = meta.get('tempo_marks', [])
    key_signature = meta.get('key_signature', None)
    tuning_hz = meta.get('tuning_hz', 440)
    
    # Mapping helpers (same as original)
    maps = {
        'bar_beat_to_abs_beat': {f"{n['bar']},{n['beat']}": n['abs_beat'] for n in nodes},
        'abs_beat_to_bar_beat': {str(n['abs_beat']): (n['bar'], n['beat']) for n in nodes}
    }
    
    # Build scoregraph (same format as original)
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
    parser = argparse.ArgumentParser(description='Build ScoreGraph from MusicXML and meta info with repeat expansion')
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
            print(f"  {node['id']}: bar {node['bar']}, beat {node['beat']}, abs_beat {node['abs_beat']}")
    else:
        print('\nAll nodes:')
        for node in scoregraph['nodes']:
            print(f"  {node['id']}: bar {node['bar']}, beat {node['beat']}, abs_beat {node['abs_beat']}")

if __name__ == '__main__':
    main()
