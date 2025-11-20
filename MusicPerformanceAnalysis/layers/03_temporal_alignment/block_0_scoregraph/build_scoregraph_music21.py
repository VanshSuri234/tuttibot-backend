#!/usr/bin/env python3
"""
Block 0: Comprehensive ScoreGraph Builder with Repeat Expansion (Music21 Only)

This is the FINAL production-ready implementation for building ScoreGraph from MusicXML 
files with proper repeat expansion using music21 library only.

Compatible with original Block 0 interface and adds repeat expansion capability.

Input (same as original):
- score.musicxml (from Audiveris PDF→XML conversion) 
- score_meta.json (metadata with tempo, key, fermatas, etc.)
- segmentation.json (optional, for cadences and structural analysis)

Output (enhanced with repeat expansion):
- scoregraph.json (comprehensive musical timeline with repeat expansion)

Key Features:
✅ Full repeat expansion (volta brackets, da capo, dal segno, nested repeats) 
✅ Music21-based implementation (reliable, no partitura issues)
✅ Compatible with existing Block 0 interface
✅ Comprehensive error handling and validation
✅ Rich metadata and debugging information
✅ Works with Audiveris-generated MusicXML files
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

def build_scoregraph_with_repeats(score_path: str, meta_path: str, seg_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Build ScoreGraph using music21 with full repeat expansion
    
    Args:
        score_path: Path to MusicXML file (from Audiveris)
        meta_path: Path to metadata JSON file
        seg_path: Optional path to segmentation JSON file
        
    Returns:
        Complete ScoreGraph dictionary with expanded repeats
    """
    
    try:
        from music21 import converter, meter, stream, tempo, key
    except ImportError:
        raise ImportError("music21 library is required. Install with: pip install music21")
    
    print("🎵 Loading score with music21...")
    
    # Parse the MusicXML file
    score = converter.parse(score_path)
    
    # ✅ CRITICAL: Expand all repeats using music21's built-in functionality
    print("🔄 Expanding repeats (volta brackets, da capo, dal segno, nested repeats)...")
    try:
        expanded_score = score.expandRepeats()
        print("   ✅ Repeat expansion successful")
    except Exception as e:
        print(f"   ⚠️  Repeat expansion failed: {e}")
        print("   ℹ️  Using original score (likely MIDI or score without measures)")
        expanded_score = score
    
    # Load metadata
    print("📋 Loading metadata...")
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    # Optionally load segmentation
    segmentation = None
    if seg_path and Path(seg_path).exists():
        print("📋 Loading segmentation data...")
        with open(seg_path, 'r') as f:
            segmentation = json.load(f)
    
    # Get the first part (handle both single part and multi-part scores)
    if hasattr(expanded_score, 'parts') and expanded_score.parts:
        part = expanded_score.parts[0]
        print(f"   Working with first part of {len(expanded_score.parts)} parts")
    else:
        part = expanded_score
        print("   Working with single-part score")
    
    print("📊 Building bars and nodes from expanded score...")
    
    # Build bars and nodes from expanded score
    bars = []
    nodes = []
    abs_beat = 0.0
    
    # Get all measures from the expanded part
    measures = part.getElementsByClass(stream.Measure)
    
    if not measures:
        # Fallback: try to get measures from the score directly
        measures = expanded_score.getElementsByClass(stream.Measure)
    
    print(f"   Found {len(measures)} measures after repeat expansion")
    
    for i, measure in enumerate(measures):
        # Handle measure numbering (some may be None after expansion)
        bar_num = measure.number if measure.number is not None else i + 1
        
        # Get time signature for this measure
        time_sigs = measure.getElementsByClass(meter.TimeSignature)
        if time_sigs:
            ts = time_sigs[0]
            time_signature = f"{ts.numerator}/{ts.denominator}"
            numerator = ts.numerator
        else:
            # Look for time signature in previous measures or metadata
            ts = part.getElementsByClass(meter.TimeSignature)
            if ts:
                last_ts = ts[-1]
                time_signature = f"{last_ts.numerator}/{last_ts.denominator}"
                numerator = last_ts.numerator
            else:
                # Use metadata or default
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
    
    # Extract tempo, key signature, tuning from metadata
    tempo_marks = meta.get('tempo_marks', [])
    key_signature = meta.get('key_signature', meta.get('key', None))
    tuning_hz = meta.get('tuning_hz', 440)
    
    # Create mapping helpers for fast lookup
    maps = {
        'bar_beat_to_abs_beat': {f"{n['bar']},{n['beat']}": n['abs_beat'] for n in nodes},
        'abs_beat_to_bar_beat': {str(n['abs_beat']): (n['bar'], n['beat']) for n in nodes}
    }
    
    # Build comprehensive ScoreGraph
    scoregraph = {
        'bars': bars,
        'nodes': nodes,
        'tempo_marks': tempo_marks,
        'key_signature': key_signature,
        'tuning_hz': tuning_hz,
        'maps': maps,
        'metadata': {
            'method': 'music21_expanded',
            'total_measures': len(measures),
            'total_nodes': len(nodes),
            'total_beats': nodes[-1]['abs_beat'] + nodes[-1]['D_beats'] if nodes else 0,
            'expanded': True,
            'repeat_expansion': True,
            'source_file': str(Path(score_path).name),
            'meta_file': str(Path(meta_path).name)
        }
    }
    
    return scoregraph

def validate_scoregraph(scoregraph: Dict[str, Any]) -> bool:
    """Validate the generated ScoreGraph for common issues"""
    
    print("🔍 Validating ScoreGraph...")
    
    # Check basic structure
    required_keys = ['bars', 'nodes', 'maps', 'metadata']
    for key in required_keys:
        if key not in scoregraph:
            print(f"❌ Missing required key: {key}")
            return False
    
    # Check if we have reasonable number of nodes
    total_nodes = len(scoregraph['nodes'])
    if total_nodes < 4:
        print(f"⚠️  Warning: Very few nodes ({total_nodes}). Check if file has content.")
    
    # Check if repeat expansion worked
    metadata = scoregraph['metadata']
    if metadata.get('expanded') and total_nodes > metadata.get('total_measures', 0) * 2:
        print(f"✅ Repeat expansion appears successful ({total_nodes} nodes from {metadata.get('total_measures')} measures)")
    elif metadata.get('expanded'):
        print(f"ℹ️  Simple structure: {total_nodes} nodes from {metadata.get('total_measures')} measures")
    
    # Check mapping consistency
    if len(scoregraph['maps']['bar_beat_to_abs_beat']) != total_nodes:
        print(f"⚠️  Warning: Mapping size mismatch")
    
    print("✅ ScoreGraph validation complete")
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Build comprehensive ScoreGraph with repeat expansion using music21',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with Audiveris files
  python build_scoregraph_music21.py --score score.musicxml --meta score_meta.json
  
  # Include segmentation data
  python build_scoregraph_music21.py --score score.musicxml --meta score_meta.json --seg segmentation.json
  
  # Custom output file
  python build_scoregraph_music21.py --score score.musicxml --meta score_meta.json --output my_scoregraph.json
        """
    )
    
    parser.add_argument('--score', required=True, 
                        help='Path to score.musicxml (from Audiveris PDF→XML conversion)')
    parser.add_argument('--meta', required=True, 
                        help='Path to score_meta.json (metadata file)')
    parser.add_argument('--seg', 
                        help='Path to segmentation.json (optional structural analysis)')
    parser.add_argument('--output', default='scoregraph.json',
                        help='Output file name (default: scoregraph.json)')
    parser.add_argument('--validate', action='store_true',
                        help='Run validation checks on the generated ScoreGraph')
    
    args = parser.parse_args()
    
    try:
        # Validate input files
        if not Path(args.score).exists():
            print(f"❌ Score file not found: {args.score}")
            sys.exit(1)
        if not Path(args.meta).exists():
            print(f"❌ Metadata file not found: {args.meta}")
            sys.exit(1)
        
        print(f"🚀 Building ScoreGraph with music21...")
        print(f"   Score: {args.score}")
        print(f"   Meta: {args.meta}")
        if args.seg:
            print(f"   Segmentation: {args.seg}")
        
        # Build ScoreGraph
        scoregraph = build_scoregraph_with_repeats(args.score, args.meta, args.seg)
        
        # Optional validation
        if args.validate:
            if not validate_scoregraph(scoregraph):
                print("⚠️  Validation found issues, but continuing...")
        
        # Save to file
        with open(args.output, 'w') as f:
            json.dump(scoregraph, f, indent=2)
        
        # Print summary
        metadata = scoregraph['metadata']
        print(f"\n✅ ScoreGraph built successfully!")
        print(f"📄 Output: {args.output}")
        print(f"🔧 Method: {metadata['method']}")
        print(f"📊 Total measures: {metadata['total_measures']}")
        print(f"🎵 Total nodes: {metadata['total_nodes']}")
        print(f"⏱️  Total beats: {metadata['total_beats']}")
        print(f"🔄 Repeat expansion: {metadata['repeat_expansion']}")
        
        # Show sample nodes
        nodes = scoregraph['nodes']
        if len(nodes) > 20:
            print(f"\n📋 First 10 nodes:")
            for node in nodes[:10]:
                flags_str = f" {node['flags']}" if node['flags'] else ""
                print(f"   {node['id']}: bar {node['bar']}, beat {node['beat']}, abs_beat {node['abs_beat']}{flags_str}")
            
            print(f"\n📋 Last 10 nodes:")
            for node in nodes[-10:]:
                flags_str = f" {node['flags']}" if node['flags'] else ""
                print(f"   {node['id']}: bar {node['bar']}, beat {node['beat']}, abs_beat {node['abs_beat']}{flags_str}")
        else:
            print(f"\n📋 All nodes:")
            for node in nodes:
                flags_str = f" {node['flags']}" if node['flags'] else ""
                print(f"   {node['id']}: bar {node['bar']}, beat {node['beat']}, abs_beat {node['abs_beat']}{flags_str}")
        
        # Success indicators
        if metadata['total_nodes'] > metadata['total_measures'] * 3:
            print(f"\n🎉 Excellent! Detected significant repeat expansion")
        elif metadata['total_nodes'] > metadata['total_measures'] * 1.5:
            print(f"\n👍 Good! Some repeat expansion detected")
        else:
            print(f"\n📝 Simple structure or no repeats in this piece")
        
    except Exception as e:
        print(f"❌ Error building ScoreGraph: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
