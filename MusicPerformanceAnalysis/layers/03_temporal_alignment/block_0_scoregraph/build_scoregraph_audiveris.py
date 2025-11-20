import argparse
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple

def parse_musicxml_robust(score_path: str) -> Dict[str, Any]:
    """Robust MusicXML parser that handles Audiveris conversion issues"""
    tree = ET.parse(score_path)
    root = tree.getroot()
    
    # Extract basic information
    parts = []
    
    # Find all parts
    for part in root.findall('.//part'):
        part_id = part.get('id', 'P1')
        part_measures = []
        
        # Track state across measures
        current_time_sig = "4/4"
        current_key_sig = "C"
        current_clef = "treble"
        
        for measure in part.findall('measure'):
            measure_num = int(measure.get('number', '1'))
            
            # Extract time signature changes
            time_sig = measure.find('.//time')
            if time_sig is not None:
                beats = int(time_sig.find('beats').text) if time_sig.find('beats') is not None else 4
                beat_type = int(time_sig.find('beat-type').text) if time_sig.find('beat-type') is not None else 4
                current_time_sig = f"{beats}/{beat_type}"
            
            # Extract key signature changes
            key_sig = measure.find('.//key')
            if key_sig is not None:
                fifths = key_sig.find('fifths')
                if fifths is not None:
                    current_key_sig = parse_key_signature(int(fifths.text))
            
            # Check for repeat markings
            repeat_start = measure.find('.//repeat[@direction="forward"]') is not None
            repeat_end = measure.find('.//repeat[@direction="backward"]') is not None
            
            # Check for endings (1st/2nd time)
            ending = measure.find('.//ending')
            ending_info = None
            if ending is not None:
                ending_info = {
                    'type': ending.get('type'),
                    'number': ending.get('number', '1')
                }
            
            # Extract actual musical content (filtering Audiveris artifacts)
            notes = extract_notes_robust(measure)
            
            # Calculate actual measure duration
            actual_duration = calculate_measure_duration(notes, current_time_sig)
            
            part_measures.append({
                'number': measure_num,
                'time_signature': current_time_sig,
                'key_signature': current_key_sig,
                'repeat_start': repeat_start,
                'repeat_end': repeat_end,
                'ending': ending_info,
                'notes': notes,
                'actual_duration': actual_duration,
                'is_pickup': actual_duration < get_full_measure_duration(current_time_sig)
            })
        
        parts.append({
            'id': part_id,
            'measures': part_measures
        })
    
    return {'parts': parts}

def parse_key_signature(fifths: int) -> str:
    """Convert fifths to key signature string"""
    key_map = {
        -7: 'Cb', -6: 'Gb', -5: 'Db', -4: 'Ab', -3: 'Eb', -2: 'Bb', -1: 'F',
        0: 'C', 1: 'G', 2: 'D', 3: 'A', 4: 'E', 5: 'B', 6: 'F#', 7: 'C#'
    }
    return key_map.get(fifths, 'C')

def extract_notes_robust(measure) -> List[Dict]:
    """Extract notes while handling common Audiveris issues"""
    notes = []
    
    for note_elem in measure.findall('.//note'):
        # Skip grace notes (they don't affect timing)
        if note_elem.find('grace') is not None:
            continue
            
        # Skip if it's part of a chord (not the first note)
        if note_elem.find('chord') is not None:
            continue
            
        # Extract duration information
        duration_elem = note_elem.find('duration')
        if duration_elem is None:
            continue
            
        duration = int(duration_elem.text)
        
        # Handle tuplets (triplets, etc.)
        tuplet = note_elem.find('.//tuplet')
        if tuplet is not None:
            actual_notes = int(tuplet.get('actual-notes', '3'))
            normal_notes = int(tuplet.get('normal-notes', '2'))
            duration = duration * (normal_notes / actual_notes)
        
        # Extract note information
        pitch_elem = note_elem.find('pitch')
        is_rest = note_elem.find('rest') is not None
        
        note_info = {
            'duration': duration,
            'is_rest': is_rest,
            'has_tie_start': note_elem.find('.//tie[@type="start"]') is not None,
            'has_tie_stop': note_elem.find('.//tie[@type="stop"]') is not None
        }
        
        if pitch_elem is not None:
            step = pitch_elem.find('step').text if pitch_elem.find('step') is not None else 'C'
            octave = int(pitch_elem.find('octave').text) if pitch_elem.find('octave') is not None else 4
            alter_elem = pitch_elem.find('alter')
            alter = int(alter_elem.text) if alter_elem is not None else 0
            
            note_info.update({
                'pitch': f"{step}{octave}",
                'alter': alter
            })
        
        notes.append(note_info)
    
    return notes

def calculate_measure_duration(notes: List[Dict], time_sig: str) -> float:
    """Calculate actual duration of notes in measure"""
    total_duration = 0
    for note in notes:
        # Don't count tied notes that are continuations
        if not note.get('has_tie_stop', False):
            total_duration += note['duration']
    return total_duration

def get_full_measure_duration(time_sig: str) -> float:
    """Get expected full measure duration based on time signature"""
    numerator, denominator = map(int, time_sig.split('/'))
    # Assuming quarter note = 1 beat, adjust for different denominators
    return numerator * (4 / denominator)

def expand_repeats(measures: List[Dict]) -> List[Dict]:
    """Expand repeated sections and handle endings"""
    expanded = []
    i = 0
    
    while i < len(measures):
        measure = measures[i]
        
        # Handle repeat sections
        if measure.get('repeat_start'):
            repeat_start_idx = i
            # Find the end of the repeat
            repeat_end_idx = i
            for j in range(i + 1, len(measures)):
                if measures[j].get('repeat_end'):
                    repeat_end_idx = j
                    break
            
            # Add the repeated section
            repeated_section = measures[repeat_start_idx:repeat_end_idx + 1]
            
            # Handle endings
            first_time_measures = []
            second_time_measures = []
            regular_measures = []
            
            for m in repeated_section:
                ending = m.get('ending')
                if ending:
                    if ending['number'] == '1':
                        first_time_measures.append(m)
                    elif ending['number'] == '2':
                        second_time_measures.append(m)
                else:
                    regular_measures.append(m)
            
            # First time through
            expanded.extend(regular_measures)
            expanded.extend(first_time_measures)
            
            # Second time through
            expanded.extend(regular_measures)
            expanded.extend(second_time_measures)
            
            i = repeat_end_idx + 1
        else:
            expanded.append(measure)
            i += 1
    
    # Renumber measures
    for idx, measure in enumerate(expanded):
        measure['expanded_number'] = idx + 1
    
    return expanded

def build_scoregraph_robust(score_path, meta_path, seg_path=None):
    """Build ScoreGraph with robust handling of Audiveris issues"""
    
    # Parse the MusicXML file
    score_data = parse_musicxml_robust(score_path)
    
    # Load meta info
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    # Optionally load segmentation
    segmentation = None
    if seg_path:
        with open(seg_path, 'r') as f:
            segmentation = json.load(f)
    
    # Build bars and nodes from the first part
    bars = []
    nodes = []
    abs_beat = 0.0
    
    if score_data['parts']:
        measures = score_data['parts'][0]['measures']
        
        # Expand repeats first
        expanded_measures = expand_repeats(measures)
        
        for measure in expanded_measures:
            bar_num = measure.get('expanded_number', measure['number'])
            time_sig = measure['time_signature']
            
            # Parse time signature
            numerator, denominator = map(int, time_sig.split('/'))
            
            # Handle pickup measures (anacrusis)
            if measure.get('is_pickup', False):
                # Adjust beats for pickup measure
                pickup_duration = measure['actual_duration']
                full_measure_duration = get_full_measure_duration(time_sig)
                pickup_beats = numerator * (pickup_duration / full_measure_duration)
                beat_count = int(pickup_beats) if pickup_beats > 0 else 1
            else:
                beat_count = numerator
            
            bar_dict = {
                'bar': bar_num,
                'time_sig': time_sig,
                'downbeat_abs_beat': abs_beat,
                'is_pickup': measure.get('is_pickup', False),
                'key_signature': measure['key_signature']
            }
            bars.append(bar_dict)
            
            # Create nodes for each beat in the measure
            for beat in range(1, beat_count + 1):
                node_id = f"{bar_num}_{beat}"
                D_beats = 1.0  # Duration in beats
                flags = []
                
                # Attach flags from meta or segmentation
                if 'fermatas' in meta and node_id in meta['fermatas']:
                    flags.append('fermata')
                if segmentation and 'cadences' in segmentation and node_id in segmentation['cadences']:
                    flags.append('cadence')
                
                # Add structural flags
                if measure.get('repeat_start'):
                    flags.append('repeat_start')
                if measure.get('repeat_end'):
                    flags.append('repeat_end')
                if measure.get('ending'):
                    flags.append(f"ending_{measure['ending']['number']}")
                
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
        'maps': maps,
        'metadata': {
            'total_expanded_measures': len([m for m in nodes]),
            'has_repeats': any('repeat' in str(n.get('flags', [])) for n in nodes),
            'has_endings': any('ending' in str(n.get('flags', [])) for n in nodes),
            'pickup_measures': len([b for b in bars if b.get('is_pickup', False)])
        }
    }
    
    return scoregraph

def main():
    parser = argparse.ArgumentParser(description='Build ScoreGraph with robust Audiveris handling')
    parser.add_argument('--score', required=True, help='Path to score.musicxml')
    parser.add_argument('--meta', required=True, help='Path to score_meta.json')
    parser.add_argument('--seg', help='Path to segmentation.json (optional)')
    args = parser.parse_args()
    
    scoregraph = build_scoregraph_robust(args.score, args.meta, args.seg)
    
    with open('scoregraph_robust.json', 'w') as f:
        json.dump(scoregraph, f, indent=2)
    
    print('Robust ScoreGraph built successfully!')
    print('Metadata:', scoregraph['metadata'])
    print(f"Total bars: {len(scoregraph['bars'])}")
    print(f"Total nodes: {len(scoregraph['nodes'])}")
    
    # Show examples of structural elements
    structural_nodes = [n for n in scoregraph['nodes'] if n.get('flags')]
    if structural_nodes:
        print(f"\nStructural elements found: {len(structural_nodes)}")
        for node in structural_nodes[:5]:
            print(f"  {node['id']}: {node['flags']}")

if __name__ == '__main__':
    main()
