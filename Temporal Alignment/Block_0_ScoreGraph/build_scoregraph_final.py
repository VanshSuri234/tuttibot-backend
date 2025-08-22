#!/usr/bin/env python3
"""
Block 0: Comprehensive ScoreGraph Builder with Repeat Expansion

This is the production-ready implementation for building ScoreGraph from MusicXML 
files with proper repeat expansion, optimized for Audiveris-generated files.

Input:
- score.musicxml (from Audiveris PDF→XML conversion)
- score_meta.json (metadata with tempo, key, fermatas, etc.)
- segmentation.json (optional, for cadences and structural analysis)

Output:
- scoregraph.json (comprehensive musical timeline with repeat expansion)

Key Features:
✅ Full repeat expansion (volta brackets, da capo, dal segno, nested repeats)
✅ Audiveris optimization (handles grace notes, artifacts)
✅ Multiple library support (music21, partitura) with fallbacks
✅ Comprehensive error handling and validation
✅ Rich metadata and debugging information
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class ScoreGraphBuilder:
    """Comprehensive ScoreGraph builder with multiple method support"""
    
    def __init__(self):
        self.available_methods = self._check_available_libraries()
        
    def _check_available_libraries(self) -> List[str]:
        """Check which music libraries are available"""
        methods = []
        
        try:
            import music21.converter
            methods.append('music21')
        except ImportError:
            pass
            
        try:
            # Import only the specific modules we need to avoid soundfont download
            import partitura.io
            import partitura.score
            methods.append('partitura')
        except ImportError:
            pass
            
        if not methods:
            print("⚠️  Warning: No music libraries found. Install with:")
            print("   pip install music21  # or")
            print("   pip install partitura")
            
        return methods
    
    def build_scoregraph_music21(self, score_path: str, meta_path: str, seg_path: Optional[str] = None) -> Dict[str, Any]:
        """Build ScoreGraph using music21 with full repeat expansion"""
        
        try:
            from music21 import converter, meter, stream, tempo, key
        except ImportError:
            raise ImportError("music21 library is required. Install with: pip install music21")
        
        print("🎵 Loading score with music21...")
        
        # Parse the MusicXML file
        score = converter.parse(score_path)
        
        # ✅ CRITICAL: Expand all repeats using music21's built-in functionality
        print("🔄 Expanding repeats (volta, da capo, dal segno)...")
        expanded_score = score.expandRepeats()
        
        # Load metadata
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        
        # Optionally load segmentation
        segmentation = None
        if seg_path and Path(seg_path).exists():
            with open(seg_path, 'r') as f:
                segmentation = json.load(f)
        
        # Get the first part (handle both single part and multi-part scores)
        if hasattr(expanded_score, 'parts') and expanded_score.parts:
            part = expanded_score.parts[0]
        else:
            part = expanded_score
        
        print("📊 Building bars and nodes...")
        
        # Build bars and nodes from expanded score
        bars = []
        nodes = []
        abs_beat = 0.0
        
        # Get all measures from the expanded part
        measures = part.getElementsByClass(stream.Measure)
        
        if not measures:
            # Fallback: try to get measures from the score directly
            measures = expanded_score.getElementsByClass(stream.Measure)
        
        print(f"   Found {len(measures)} measures after expansion")
        
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
        
        return self._finalize_scoregraph(bars, nodes, meta, 'music21', len(measures))
    
    def build_scoregraph_partitura(self, score_path: str, meta_path: str, seg_path: Optional[str] = None) -> Dict[str, Any]:
        """Build ScoreGraph using partitura with full repeat expansion and Audiveris optimization"""
        
        try:
            # Import only specific modules to avoid soundfont download
            from partitura.io import load_musicxml
            import partitura.score as pt_score
        except ImportError:
            raise ImportError("partitura library is required. Install with: pip install partitura")
        
        print("🎵 Loading score with partitura...")
        
        # Load with optimal Audiveris settings
        score = load_musicxml(
            score_path, 
            ignore_invisible_objects=True,  # ✅ Filters grace notes and artifacts
            force_note_ids=True  # ✅ Ensures note tracking
        )
        
        # Get first part
        part = score.parts[0] if hasattr(score, 'parts') and score.parts else score
        
        # ✅ CRITICAL: Expand ALL repeats (volta, da capo, dal segno, nested)
        print("🔄 Expanding repeats with maximal unfolding...")
        expanded_part = pt_score.unfold_part_maximal(part, update_ids=True)
        
        # Load metadata
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        
        # Optionally load segmentation
        segmentation = None
        if seg_path and Path(seg_path).exists():
            with open(seg_path, 'r') as f:
                segmentation = json.load(f)
        
        print("📊 Building bars and nodes...")
        
        # Build bars and nodes from expanded part
        bars = []
        nodes = []
        abs_beat = 0.0
        
        # Get all measures from the expanded part
        measures = list(expanded_part.iter_all(pt_score.Measure))
        
        print(f"   Found {len(measures)} measures after expansion")
        
        for measure in measures:
            bar_num = measure.number if measure.number is not None else len(bars) + 1
            
            # Get time signature for this measure
            time_sigs = list(measure.iter_all(pt_score.TimeSignature))
            if time_sigs:
                ts = time_sigs[0]
                time_signature = f"{ts.numerator}/{ts.denominator}"
                numerator = ts.numerator
            else:
                # Look for time signature in part
                part_ts = list(expanded_part.iter_all(pt_score.TimeSignature))
                if part_ts:
                    last_ts = part_ts[-1]
                    time_signature = f"{last_ts.numerator}/{last_ts.denominator}"
                    numerator = last_ts.numerator
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
        
        return self._finalize_scoregraph(bars, nodes, meta, 'partitura', len(measures))
    
    def _finalize_scoregraph(self, bars: List[Dict], nodes: List[Dict], meta: Dict, method: str, total_measures: int) -> Dict[str, Any]:
        """Finalize ScoreGraph with metadata and mapping helpers"""
        
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
                'method': method,
                'total_measures': total_measures,
                'total_nodes': len(nodes),
                'total_beats': nodes[-1]['abs_beat'] + nodes[-1]['D_beats'] if nodes else 0,
                'expanded': True,
                'repeat_expansion': True,
                'audiveris_optimized': method == 'partitura'
            }
        }
        
        return scoregraph
    
    def build_scoregraph(self, score_path: str, meta_path: str, seg_path: Optional[str] = None, method: Optional[str] = None) -> Dict[str, Any]:
        """Main entry point - builds ScoreGraph with best available method"""
        
        # Validate input files
        if not Path(score_path).exists():
            raise FileNotFoundError(f"Score file not found: {score_path}")
        if not Path(meta_path).exists():
            raise FileNotFoundError(f"Metadata file not found: {meta_path}")
        
        # Determine method to use
        if method and method not in self.available_methods:
            raise ValueError(f"Method '{method}' not available. Available: {self.available_methods}")
        
        if not method:
            # Auto-select best method
            if 'partitura' in self.available_methods:
                method = 'partitura'  # Preferred for Audiveris files
            elif 'music21' in self.available_methods:
                method = 'music21'
            else:
                raise RuntimeError("No music libraries available. Install music21 or partitura.")
        
        print(f"🚀 Building ScoreGraph using {method}...")
        
        # Build ScoreGraph with selected method
        if method == 'partitura':
            return self.build_scoregraph_partitura(score_path, meta_path, seg_path)
        elif method == 'music21':
            return self.build_scoregraph_music21(score_path, meta_path, seg_path)
        else:
            raise ValueError(f"Unknown method: {method}")

def main():
    parser = argparse.ArgumentParser(
        description='Build comprehensive ScoreGraph with repeat expansion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-select best method
  python build_scoregraph_final.py --score score.musicxml --meta score_meta.json
  
  # Use specific method
  python build_scoregraph_final.py --score score.musicxml --meta score_meta.json --method partitura
  
  # Include segmentation
  python build_scoregraph_final.py --score score.musicxml --meta score_meta.json --seg segmentation.json
        """
    )
    
    parser.add_argument('--score', required=True, 
                        help='Path to score.musicxml (from Audiveris)')
    parser.add_argument('--meta', required=True, 
                        help='Path to score_meta.json')
    parser.add_argument('--seg', 
                        help='Path to segmentation.json (optional)')
    parser.add_argument('--method', choices=['music21', 'partitura'], 
                        help='Method to use for repeat expansion (auto-select if not specified)')
    parser.add_argument('--output', default='scoregraph.json',
                        help='Output file name (default: scoregraph.json)')
    
    args = parser.parse_args()
    
    try:
        # Initialize builder
        builder = ScoreGraphBuilder()
        
        if not builder.available_methods:
            print("❌ No music libraries available!")
            print("Install with: pip install music21 partitura")
            sys.exit(1)
        
        # Build ScoreGraph
        scoregraph = builder.build_scoregraph(
            args.score, 
            args.meta, 
            args.seg, 
            args.method
        )
        
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
        
        if len(scoregraph['nodes']) > 20:
            print(f"\n📋 First 10 nodes:")
            for node in scoregraph['nodes'][:10]:
                print(f"   {node['id']}: bar {node['bar']}, beat {node['beat']}, abs_beat {node['abs_beat']}")
            
            print(f"\n📋 Last 10 nodes:")
            for node in scoregraph['nodes'][-10:]:
                print(f"   {node['id']}: bar {node['bar']}, beat {node['beat']}, abs_beat {node['abs_beat']}")
        else:
            print(f"\n📋 All nodes:")
            for node in scoregraph['nodes']:
                print(f"   {node['id']}: bar {node['bar']}, beat {node['beat']}, abs_beat {node['abs_beat']}")
        
        # Validation check
        if metadata['total_nodes'] < 10:
            print("\n⚠️  Warning: Very few nodes generated. Check if repeats were properly expanded.")
        
    except Exception as e:
        print(f"❌ Error building ScoreGraph: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
