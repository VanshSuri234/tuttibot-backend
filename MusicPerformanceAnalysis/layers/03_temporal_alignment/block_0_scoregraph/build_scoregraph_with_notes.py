#!/usr/bin/env python3
"""
Block 0: ScoreGraph Builder WITH NOTE EXTRACTION

This version extracts actual note data from MusicXML for alignment purposes.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

def build_scoregraph_with_notes(score_path: str, meta_path: str, seg_path: Optional[str] = None, part_index: int = 0) -> Dict[str, Any]:
    """
    Build ScoreGraph using music21 with NOTE extraction
    
    Args:
        score_path: Path to MusicXML file
        meta_path: Path to metadata JSON file
        seg_path: Optional path to segmentation JSON file
        part_index: Which part to extract from multi-part score (default: 0)
        
    Returns:
        Complete ScoreGraph dictionary with beat nodes AND musical notes
    """
    
    try:
        from music21 import converter, meter, stream, tempo, key, note, chord
    except ImportError:
        raise ImportError("music21 library is required. Install with: pip install music21")
    
    print("Loading score with music21...")
    
    # Parse the MusicXML file
    score = converter.parse(score_path)
    
    # Load metadata
    print("Loading metadata...")
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    # Optionally load segmentation
    segmentation = None
    if seg_path and Path(seg_path).exists():
        print("Loading segmentation data...")
        with open(seg_path, 'r') as f:
            segmentation = json.load(f)
    
    # Get the specified part (handle both single part and multi-part scores)
    if hasattr(score, 'parts') and score.parts:
        if part_index >= len(score.parts):
            print(f"WARNING: Requested part {part_index} but score only has {len(score.parts)} parts. Using part 0.")
            part_index = 0
        part = score.parts[part_index]
        print(f"Working with part {part_index} of {len(score.parts)} parts (Part name: {part.partName})")
    else:
        part = score
        print("Working with single-part score")
    
    print("Building bars and nodes...")
    
    # Build bars and nodes from score
    bars = []
    nodes = []
    abs_beat = 0.0
    
    # Get all measures
    measures = part.getElementsByClass(stream.Measure)
    
    if not measures:
        measures = score.getElementsByClass(stream.Measure)
    
    print(f"Found {len(measures)} measures")
    
    for i, measure in enumerate(measures):
        bar_num = measure.number if measure.number is not None else i + 1
        
        # Get time signature for this measure
        time_sigs = measure.getElementsByClass(meter.TimeSignature)
        if time_sigs:
            ts = time_sigs[0]
            time_signature = f"{ts.numerator}/{ts.denominator}"
            numerator = ts.numerator
        else:
            ts = part.getElementsByClass(meter.TimeSignature)
            if ts:
                last_ts = ts[-1]
                time_signature = f"{last_ts.numerator}/{last_ts.denominator}"
                numerator = last_ts.numerator
            else:
                time_signature = meta.get('meter', meta.get('time_signature', '4/4'))
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
            D_beats = 1.0
            flags = []
            
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
    
    # ===== CRITICAL: Extract actual musical notes =====
    print("Extracting musical notes from score...")
    musical_notes = []
    
    # Get default tempo from metadata or use 120 BPM
    default_bpm = 120
    if meta.get('tempo_marks') and len(meta['tempo_marks']) > 0:
        default_bpm = meta['tempo_marks'][0].get('bpm', 120)
    
    # Calculate seconds per beat
    seconds_per_beat = 60.0 / default_bpm
    
    # Flatten the part to get all notes in order
    notes_and_chords = part.flatten().notesAndRests
    
    for element in notes_and_chords:
        if isinstance(element, note.Rest):
            continue  # Skip rests
            
        # Get offset in quarter notes
        offset_quarters = element.offset
        duration_quarters = element.quarterLength
        
        # Convert to seconds (assuming constant tempo)
        offset_seconds = offset_quarters * seconds_per_beat
        duration_seconds = duration_quarters * seconds_per_beat
        
        if isinstance(element, note.Note):
            # Single note
            musical_notes.append({
                'pitch': element.pitch.midi,
                'offset_seconds': offset_seconds,
                'duration_seconds': duration_seconds,
                'velocity': 80,  # Default velocity
                'offset_quarters': offset_quarters,
                'duration_quarters': duration_quarters
            })
        elif isinstance(element, chord.Chord):
            # Chord - add each note
            for pitch in element.pitches:
                musical_notes.append({
                    'pitch': pitch.midi,
                    'offset_seconds': offset_seconds,
                    'duration_seconds': duration_seconds,
                    'velocity': 80,
                    'offset_quarters': offset_quarters,
                    'duration_quarters': duration_quarters
                })
    
    print(f"Extracted {len(musical_notes)} musical notes")
    
    # Normalize note timings to start from 0 (for DTW alignment)
    if musical_notes:
        min_offset = min(n['offset_seconds'] for n in musical_notes)
        print(f"Normalizing note timings (shifting by -{min_offset:.2f}s)")
        for note in musical_notes:
            note['offset_seconds'] -= min_offset
    
    # Extract tempo, key signature, tuning from metadata
    tempo_marks = meta.get('tempo_marks', [])
    key_signature = meta.get('key_signature', meta.get('key', None))
    tuning_hz = meta.get('tuning_hz', 440)
    
    # Create mapping helpers for fast lookup
    maps = {
        'bar_beat_to_abs_beat': {f"{n['bar']},{n['beat']}": n['abs_beat'] for n in nodes},
        'abs_beat_to_bar_beat': {str(n['abs_beat']): (n['bar'], n['beat']) for n in nodes}
    }
    
    # Build comprehensive ScoreGraph WITH NOTES
    scoregraph = {
        'bars': bars,
        'nodes': nodes,
        'musical_notes': musical_notes,  # ← CRITICAL: Added note data
        'tempo_marks': tempo_marks,
        'key_signature': key_signature,
        'tuning_hz': tuning_hz,
        'maps': maps,
        'metadata': {
            'method': 'music21_with_notes',
            'total_measures': len(measures),
            'total_nodes': len(nodes),
            'total_notes': len(musical_notes),
            'total_beats': nodes[-1]['abs_beat'] + nodes[-1]['D_beats'] if nodes else 0,
            'source_file': str(Path(score_path).name),
            'meta_file': str(Path(meta_path).name)
        }
    }
    
    return scoregraph

def main():
    parser = argparse.ArgumentParser(
        description='Build ScoreGraph with note extraction using music21'
    )
    
    parser.add_argument('--score', required=True, 
                        help='Path to score.musicxml')
    parser.add_argument('--meta', required=True, 
                        help='Path to score_meta.json (metadata file)')
    parser.add_argument('--seg', 
                        help='Path to segmentation.json (optional structural analysis)')
    parser.add_argument('--part', type=int, default=0,
                        help='Which part to extract from multi-part score (default: 0)')
    parser.add_argument('--output', default='scoregraph.json',
                        help='Output file name (default: scoregraph.json)')
    
    args = parser.parse_args()
    
    try:
        # Validate input files
        if not Path(args.score).exists():
            print(f"Score file not found: {args.score}")
            sys.exit(1)
        if not Path(args.meta).exists():
            print(f"Metadata file not found: {args.meta}")
            sys.exit(1)
        
        print(f"Building ScoreGraph with note extraction...")
        print(f"Score: {args.score}")
        print(f"Meta: {args.meta}")
        if args.seg:
            print(f"Segmentation: {args.seg}")
        print(f"Part: {args.part}")
        
        # Build ScoreGraph
        scoregraph = build_scoregraph_with_notes(args.score, args.meta, args.seg, args.part)
        
        # Save to file
        with open(args.output, 'w') as f:
            json.dump(scoregraph, f, indent=2)
        
        # Print summary
        metadata = scoregraph['metadata']
        print(f"\nScoreGraph built successfully")
        print(f"Output: {args.output}")
        print(f"Method: {metadata['method']}")
        print(f"Total measures: {metadata['total_measures']}")
        print(f"Total nodes: {metadata['total_nodes']}")
        print(f"Total musical notes: {metadata['total_notes']}")
        print(f"Total beats: {metadata['total_beats']}")
        
        # Show sample notes
        notes = scoregraph.get('musical_notes', [])
        if notes:
            print(f"\nFirst 5 notes:")
            for note in notes[:5]:
                print(f"  Pitch {note['pitch']}: start={note['offset_seconds']:.2f}s, duration={note['duration_seconds']:.2f}s")
            if len(notes) > 5:
                print(f"\nLast 5 notes:")
                for note in notes[-5:]:
                    print(f"  Pitch {note['pitch']}: start={note['offset_seconds']:.2f}s, duration={note['duration_seconds']:.2f}s")
        
    except Exception as e:
        print(f"Error building ScoreGraph: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
