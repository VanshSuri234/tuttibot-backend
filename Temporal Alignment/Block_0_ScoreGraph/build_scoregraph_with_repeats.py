import argparse
import json
from typing import Dict, List, Any

def extract_musical_notes(part, tempo=120.0):
    """Extract musical notes with precise timing from music21 part"""
    notes = []
    
    try:
        from music21 import note, chord, duration, tempo as music21_tempo
    except ImportError:
        return notes
    
    # Get tempo marking if available
    tempo_markings = part.flat.getElementsByClass(music21_tempo.TempoIndication)
    if tempo_markings:
        tempo = tempo_markings[0].number
    
    def beats_to_seconds(beats, tempo_bpm):
        """Convert beats to seconds using tempo"""
        return (beats * 60.0) / tempo_bpm
    
    # Extract notes and chords
    for element in part.flat.notesAndRests:
        if isinstance(element, note.Note):
            # Single note
            offset_beats = float(element.offset)
            duration_beats = float(element.duration.quarterLength)
            
            note_data = {
                'type': 'note',
                'pitch': element.pitch.midi,
                'pitch_name': str(element.pitch),
                'offset_beats': offset_beats,
                'offset_seconds': beats_to_seconds(offset_beats, tempo),
                'duration_beats': duration_beats,
                'duration_seconds': beats_to_seconds(duration_beats, tempo),
                'velocity': 64  # Default velocity
            }
            notes.append(note_data)
            
        elif isinstance(element, chord.Chord):
            # Chord - create one entry per note
            offset_beats = float(element.offset)
            duration_beats = float(element.duration.quarterLength)
            
            for pitch in element.pitches:
                note_data = {
                    'type': 'chord_note',
                    'pitch': pitch.midi,
                    'pitch_name': str(pitch),
                    'offset_beats': offset_beats,
                    'offset_seconds': beats_to_seconds(offset_beats, tempo),
                    'duration_beats': duration_beats,
                    'duration_seconds': beats_to_seconds(duration_beats, tempo),
                    'velocity': 64,  # Default velocity
                    'chord_size': len(element.pitches)
                }
                notes.append(note_data)
    
    return notes

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
    
    # Extract musical notes with timing information
    musical_notes = extract_musical_notes(part)
    
    # Mapping helpers
    maps = {
        'bar_beat_to_abs_beat': {f"{n['bar']},{n['beat']}": n['abs_beat'] for n in nodes},
        'abs_beat_to_bar_beat': {str(n['abs_beat']): (n['bar'], n['beat']) for n in nodes}
    }
    
    scoregraph = {
        'metadata': {
            'total_measures': len(bars),
            'total_notes': len(musical_notes),
            'key_signature': key_signature,
            'tuning_hz': tuning_hz
        },
        'bars': bars,
        'nodes': nodes,
        'musical_notes': musical_notes,
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
    
    print(f'✅ ScoreGraph built with {len(scoregraph["bars"])} bars, {len(scoregraph["nodes"])} beats, {len(scoregraph.get("musical_notes", []))} notes')
    print(f'Total measures: {len(scoregraph["bars"])}')
    print(f'Total beat nodes: {len(scoregraph["nodes"])}')
    print(f'Total note nodes: {len(scoregraph.get("musical_notes", []))}')
    print(f'Total nodes: {len(scoregraph["nodes"]) + len(scoregraph.get("musical_notes", []))}')
    
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
