import argparse
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any

def parse_musicxml_simple(score_path: str) -> Dict[str, Any]:
    """Simple MusicXML parser that extracts basic structure"""
    tree = ET.parse(score_path)
    root = tree.getroot()
    
    # Extract basic information
    parts = []
    measures = []
    
    # Find all parts
    for part in root.findall('.//part'):
        part_id = part.get('id', 'P1')
        part_measures = []
        
        for measure in part.findall('measure'):
            measure_num = int(measure.get('number', '1'))
            
            # Extract time signature
            time_sig = measure.find('.//time')
            if time_sig is not None:
                beats = int(time_sig.find('beats').text) if time_sig.find('beats') is not None else 4
                beat_type = int(time_sig.find('beat-type').text) if time_sig.find('beat-type') is not None else 4
                time_signature = f"{beats}/{beat_type}"
            else:
                time_signature = "4/4"  # Default
            
            part_measures.append({
                'number': measure_num,
                'time_signature': time_signature
            })
        
        parts.append({
            'id': part_id,
            'measures': part_measures
        })
    
    return {'parts': parts}

def build_scoregraph(score_path, meta_path, seg_path=None):
    """Build ScoreGraph from MusicXML and meta info without partitura"""
    
    # Parse the MusicXML file
    score_data = parse_musicxml_simple(score_path)
    
    # Load meta info
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    # Optionally load segmentation
    segmentation = None
    if seg_path:
        with open(seg_path, 'r') as f:
            segmentation = json.load(f)
    
    # Build bars and nodes from the first part (assuming single part for simplicity)
    bars = []
    nodes = []
    abs_beat = 0.0
    
    # Get measures from first part
    if score_data['parts']:
        measures = score_data['parts'][0]['measures']
        
        for measure in measures:
            bar_num = measure['number']
            time_sig = measure['time_signature']
            
            # Parse time signature
            numerator, denominator = map(int, time_sig.split('/'))
            
            bar_dict = {
                'bar': bar_num,
                'time_sig': time_sig,
                'downbeat_abs_beat': abs_beat
            }
            bars.append(bar_dict)
            
            # Create nodes for each beat in the measure
            for beat in range(1, numerator + 1):
                node_id = f"{bar_num}_{beat}"
                D_beats = 1.0  # Duration in beats (can be refined)
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
    
    # ✅ ADD DAG EDGES - Enable Context Alignment navigation
    # Phase 1: Linear edges (each node → next node)
    for i in range(len(nodes) - 1):
        if 'edges' not in nodes[i]:
            nodes[i]['edges'] = []
        nodes[i]['edges'].append(nodes[i + 1]['id'])
    
    # Last node has no outgoing edges
    if nodes:
        nodes[-1]['edges'] = []
    
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
    parser = argparse.ArgumentParser(description='Build ScoreGraph from MusicXML and meta info (simple version)')
    parser.add_argument('--score', required=True, help='Path to score.musicxml')
    parser.add_argument('--meta', required=True, help='Path to score_meta.json')
    parser.add_argument('--seg', help='Path to segmentation.json (optional)')
    args = parser.parse_args()
    
    scoregraph = build_scoregraph(args.score, args.meta, args.seg)
    
    with open('scoregraph.json', 'w') as f:
        json.dump(scoregraph, f, indent=2)
    
    print('ScoreGraph built successfully!')
    print('First 10 nodes:')
    for node in scoregraph['nodes'][:10]:
        print(node)
    
    print(f"\nTotal bars: {len(scoregraph['bars'])}")
    print(f"Total nodes: {len(scoregraph['nodes'])}")

if __name__ == '__main__':
    main()
