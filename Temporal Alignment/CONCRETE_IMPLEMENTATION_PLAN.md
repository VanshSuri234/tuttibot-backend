# TuttiBot: Concrete Implementation Plan for Temporal & Context Alignment

## Executive Summary

Based on the planned architecture (`TuttiBot_Temporal_Context_Alignment_Plan.txt`) and existing code analysis (`IMPLEMENTATION_STATUS_PROMPT.md`), this document provides a **concrete step-by-step implementation plan** that:

1. ✅ Leverages existing working code (Blocks 0, 1, 3, 4)
2. 🔧 Enhances Block 2 with requested features (rubato, beat weighting, band constraints)
3. 🆕 Adds new Context Alignment layer to handle repeats/structure
4. 🎯 Maintains the objective: **Temporal + Context alignment** for complete musical understanding

---

## Architecture Overview: What Changes

### Current Flow (What Exists):
```
MusicXML → Block 0 (ScoreGraph) → [Repeat expansion baked in]
                                    ↓
Audio → Block 1 (AMT) → transcription.json
                                    ↓
                        Block 2 (DTW) → alignment_results.json
```

### New Flow (What We're Building):
```
MusicXML → Block 0 (ScoreGraph + DAG) → score_graph.json [with edges]
              ↓                              ↓
         Audio (.wav)                   Block 4 (Beats) → beats.json [+confidence]
              ↓                              ↓
     Block 1 (AMT) → transcription.json     
              ↓                              ↓
     🆕 Context Alignment (DAG+NW) → context_alignment.json [path through score]
                                             ↓
               🔧 Block 2 Enhanced (DTW) → alignment_meta.json [fine timing]
                        [+ beat weighting + fermata awareness + band constraints]
```

**Key Change**: Split alignment into TWO stages:
1. **Context Alignment** (structural) - Which path through the score?
2. **Temporal Alignment** (timing) - Precise time mapping with expressive features

---

## Phase 1: Update Existing Blocks (1-2 Days)

### 1.1 ✅ Block 0: Add DAG Structure (PRIORITY 1)

**File**: `Block_0_ScoreGraph/build_scoregraph_with_repeats.py`

**Current Status**: ✅ Already expands repeats, detects fermatas/cadences

**Required Enhancement**: Add graph edges for navigation

**Changes**:
```python
def build_scoregraph(score_path, meta_path, seg_path=None):
    """Build ScoreGraph with DAG structure for context alignment"""
    
    # ... existing code for repeat expansion ...
    
    # 🆕 NEW: Add edges to create navigable graph
    for i, node in enumerate(nodes):
        # Linear edge (always present)
        if i < len(nodes) - 1:
            node['edges'] = [nodes[i + 1]['id']]
        else:
            node['edges'] = []  # Last node
        
        # 🆕 Check for structural branches (repeat jumps, endings, etc.)
        # This requires parsing the expanded_score for repeat markers
        if hasattr(measure, 'repeat') and measure.repeat:
            # Add edge back to repeat start
            repeat_target = find_repeat_target(measure, nodes)
            if repeat_target:
                node['edges'].append(repeat_target)
    
    scoregraph = {
        'metadata': {...},
        'bars': bars,
        'nodes': nodes,  # Now includes 'edges' field
        'musical_notes': musical_notes,
        # ... rest unchanged ...
    }
```

**Test**: Verify that nodes have `edges` field pointing to valid next nodes.

**Time Estimate**: 4-6 hours

---

### 1.2 ✅ Block 4: Capture Beat Confidence (PRIORITY 1)

**File**: `Block_4_BeatDownbeat/estimate_beats.py`

**Current Status**: ⚠️ Detects times only, ignores confidence

**Required Enhancement**: Extract confidence scores from BeatNet

**Changes**:
```python
def estimate_beats(audio_path, beats_path):
    """Estimate beats and downbeats with confidence scores"""
    from beatnet.model import BeatNet
    
    # Initialize BeatNet
    beatnet = BeatNet(
        1,  # model selection
        mode='offline',
        inference_model='DBN',
        plot=[],
        thread=False
    )
    
    # 🆕 Process audio and get full output
    output = beatnet.process(audio_path)
    
    # 🆕 Extract beats with confidence
    beats_json = []
    
    # BeatNet returns: [time, beat_number, confidence]
    if output is not None and len(output) > 0:
        for beat_info in output:
            time_sec = float(beat_info[0])
            beat_num = int(beat_info[1]) if len(beat_info) > 1 else 0
            confidence = float(beat_info[2]) if len(beat_info) > 2 else 1.0
            
            beats_json.append({
                "t": time_sec,
                "downbeat": 1 if beat_num == 1 else 0,
                "confidence": confidence  # 🆕 NEW
            })
    
    # Save with confidence
    with open(beats_path, 'w') as f:
        json.dump(beats_json, f, indent=2)
    
    print(f'✅ Extracted {len(beats_json)} beats/downbeats with confidence scores')
    return beats_json
```

**Test**: Check that `beats.json` includes `confidence` field (0.0-1.0)

**Time Estimate**: 2-3 hours (including BeatNet API research)

---

### 1.3 🔧 Block 2: Enable Band Constraints (PRIORITY 1)

**File**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`

**Current Status**: ⚠️ Basic DTW works, no constraints

**Required Enhancement**: Quick win - enable existing librosa features

**Changes**:
```python
def dtw_alignment(self, X: np.ndarray, Y: np.ndarray, 
                  metric: str = 'cosine') -> Tuple[np.ndarray, float]:
    """
    Perform DTW alignment with Sakoe-Chiba band constraint
    """
    try:
        # 🆕 Enable band constraint for faster, more robust alignment
        D, wp = librosa.sequence.dtw(
            X=X.T, 
            Y=Y.T, 
            metric=metric,
            global_constraints=True,  # 🆕 NEW: Enable Sakoe-Chiba band
            band_rad=0.25              # 🆕 NEW: Allow 25% tempo deviation
        )
        
        distance = D[-1, -1]
        logger.info(f"DTW with band constraint: path length={len(wp)}, distance={distance:.4f}")
        return wp, distance
    except Exception as e:
        logger.warning(f"Band-constrained DTW failed: {e}, falling back")
        return self._dtw_scipy(X, Y, metric)
```

**Test**: Verify alignment still works and is faster

**Time Estimate**: 30 minutes

---

## Phase 2: Add Context Alignment Layer (2-3 Days)

### 2.1 🆕 Create Context Aligner (NEW FILE)

**File**: `Temporal Alignment/context_aligner.py` (NEW)

**Purpose**: Use Needleman-Wunsch on DAG to find which path performer took

**Implementation**:
```python
#!/usr/bin/env python3
"""
Context Alignment: DAG + Needleman-Wunsch for structural path finding

Determines which path through the score the performer took,
handling repeats, codas, and structural variations.

Input:  score_graph.json (with edges), transcription.json
Output: context_alignment.json (selected path through score)
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
import networkx as nx
from pathlib import Path

class ContextAligner:
    """Structural alignment using DAG + Needleman-Wunsch"""
    
    def __init__(self, 
                 match_score: float = 2.0,
                 mismatch_penalty: float = -1.0,
                 gap_penalty: float = -0.5):
        """
        Initialize context aligner
        
        Args:
            match_score: Reward for matching pitch
            mismatch_penalty: Penalty for pitch mismatch
            gap_penalty: Penalty for insertion/deletion
        """
        self.match_score = match_score
        self.mismatch_penalty = mismatch_penalty
        self.gap_penalty = gap_penalty
    
    def load_score_graph(self, score_graph_path: str) -> Dict:
        """Load ScoreGraph with DAG structure"""
        with open(score_graph_path, 'r') as f:
            return json.load(f)
    
    def load_transcription(self, transcription_path: str) -> List[Dict]:
        """Load AMT transcription"""
        with open(transcription_path, 'r') as f:
            data = json.load(f)
        return data.get('notes', [])
    
    def build_dag(self, score_graph: Dict) -> nx.DiGraph:
        """
        Build NetworkX DiGraph from ScoreGraph
        
        Returns:
            DAG where nodes are beat positions and edges represent
            possible transitions (including repeat jumps)
        """
        G = nx.DiGraph()
        
        # Add nodes
        for node in score_graph['nodes']:
            G.add_node(
                node['id'],
                abs_beat=node['abs_beat'],
                bar=node['bar'],
                beat=node['beat'],
                flags=node.get('flags', [])
            )
        
        # Add edges (from node['edges'] field)
        for node in score_graph['nodes']:
            node_id = node['id']
            for next_id in node.get('edges', []):
                G.add_edge(node_id, next_id)
        
        return G
    
    def extract_pitch_sequence(self, score_graph: Dict) -> List[int]:
        """Extract pitch sequence from score's musical_notes"""
        notes = score_graph.get('musical_notes', [])
        return [int(note['pitch']) for note in notes]
    
    def extract_performance_pitches(self, transcription: List[Dict]) -> List[int]:
        """Extract pitch sequence from performance transcription"""
        return [int(note['pitch_midi']) for note in transcription]
    
    def needleman_wunsch(self, 
                        seq1: List[int], 
                        seq2: List[int]) -> Tuple[List, List, float]:
        """
        Needleman-Wunsch global sequence alignment
        
        Args:
            seq1: Score pitch sequence
            seq2: Performance pitch sequence
            
        Returns:
            aligned_seq1, aligned_seq2, alignment_score
        """
        n, m = len(seq1), len(seq2)
        
        # Initialize scoring matrix
        S = np.zeros((n + 1, m + 1))
        
        # Initialize gap penalties
        for i in range(n + 1):
            S[i, 0] = i * self.gap_penalty
        for j in range(m + 1):
            S[0, j] = j * self.gap_penalty
        
        # Fill matrix
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                # Match/mismatch
                if seq1[i-1] == seq2[j-1]:
                    match = S[i-1, j-1] + self.match_score
                else:
                    match = S[i-1, j-1] + self.mismatch_penalty
                
                # Gap in seq2 (deletion)
                delete = S[i-1, j] + self.gap_penalty
                
                # Gap in seq1 (insertion)
                insert = S[i, j-1] + self.gap_penalty
                
                S[i, j] = max(match, delete, insert)
        
        # Backtrack to find alignment
        aligned_seq1 = []
        aligned_seq2 = []
        i, j = n, m
        
        while i > 0 or j > 0:
            if i > 0 and j > 0:
                # Check which move was best
                if seq1[i-1] == seq2[j-1]:
                    score_diag = S[i-1, j-1] + self.match_score
                else:
                    score_diag = S[i-1, j-1] + self.mismatch_penalty
                
                score_up = S[i-1, j] + self.gap_penalty if i > 0 else -np.inf
                score_left = S[i, j-1] + self.gap_penalty if j > 0 else -np.inf
                
                if S[i, j] == score_diag:
                    aligned_seq1.append(seq1[i-1])
                    aligned_seq2.append(seq2[j-1])
                    i -= 1
                    j -= 1
                elif S[i, j] == score_up:
                    aligned_seq1.append(seq1[i-1])
                    aligned_seq2.append(None)  # Gap in performance
                    i -= 1
                else:
                    aligned_seq1.append(None)  # Gap in score
                    aligned_seq2.append(seq2[j-1])
                    j -= 1
            elif i > 0:
                aligned_seq1.append(seq1[i-1])
                aligned_seq2.append(None)
                i -= 1
            else:
                aligned_seq1.append(None)
                aligned_seq2.append(seq2[j-1])
                j -= 1
        
        # Reverse (we backtracked)
        aligned_seq1.reverse()
        aligned_seq2.reverse()
        
        return aligned_seq1, aligned_seq2, S[n, m]
    
    def align(self, score_graph_path: str, transcription_path: str,
              output_path: str = "context_alignment.json") -> Dict:
        """
        Perform context alignment
        
        Returns:
            Dictionary with:
            - selected_path: List of node IDs showing path through score
            - alignment_score: Quality metric
            - pitch_matches: Match statistics
        """
        print("🎯 Context Alignment: Finding structural path through score")
        
        # Load inputs
        score_graph = self.load_score_graph(score_graph_path)
        transcription = self.load_transcription(transcription_path)
        
        print(f"  Score nodes: {len(score_graph['nodes'])}")
        print(f"  Performance notes: {len(transcription)}")
        
        # Build DAG
        dag = self.build_dag(score_graph)
        print(f"  DAG: {dag.number_of_nodes()} nodes, {dag.number_of_edges()} edges")
        
        # Extract pitch sequences
        score_pitches = self.extract_pitch_sequence(score_graph)
        perf_pitches = self.extract_performance_pitches(transcription)
        
        print(f"  Score pitches: {len(score_pitches)}")
        print(f"  Performance pitches: {len(perf_pitches)}")
        
        # Perform Needleman-Wunsch alignment
        aligned_score, aligned_perf, score = self.needleman_wunsch(
            score_pitches, 
            perf_pitches
        )
        
        print(f"  Alignment score: {score:.2f}")
        
        # Map aligned pitches back to node IDs
        # This creates the "path" through the score DAG
        selected_path = []
        musical_notes = score_graph.get('musical_notes', [])
        note_idx = 0
        
        for i, (score_pitch, perf_pitch) in enumerate(zip(aligned_score, aligned_perf)):
            if score_pitch is not None and perf_pitch is not None:
                # Match found - record this note's position
                if note_idx < len(musical_notes):
                    note = musical_notes[note_idx]
                    # Find corresponding beat node
                    abs_beat = note['offset_beats']
                    node_id = self._find_node_at_beat(score_graph['nodes'], abs_beat)
                    if node_id:
                        selected_path.append(node_id)
                note_idx += 1
            elif score_pitch is not None:
                # Gap in performance (skip)
                note_idx += 1
        
        # Calculate match statistics
        matches = sum(1 for s, p in zip(aligned_score, aligned_perf) 
                     if s is not None and p is not None and s == p)
        total_aligned = sum(1 for s in aligned_score if s is not None)
        
        results = {
            'selected_path': selected_path,
            'alignment_score': float(score),
            'pitch_matches': {
                'matches': matches,
                'total_score_notes': total_aligned,
                'total_perf_notes': len(perf_pitches),
                'match_percentage': (matches / total_aligned * 100) if total_aligned > 0 else 0
            },
            'metadata': {
                'score_graph': score_graph_path,
                'transcription': transcription_path,
                'method': 'DAG + Needleman-Wunsch'
            }
        }
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Context alignment complete: {len(selected_path)} nodes in path")
        print(f"   Match percentage: {results['pitch_matches']['match_percentage']:.1f}%")
        print(f"   Saved to: {output_path}")
        
        return results
    
    def _find_node_at_beat(self, nodes: List[Dict], abs_beat: float) -> Optional[str]:
        """Find node ID closest to given absolute beat"""
        closest_node = min(nodes, key=lambda n: abs(n['abs_beat'] - abs_beat))
        return closest_node['id']


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Context Alignment: Find structural path through score')
    parser.add_argument('score_graph', help='Path to score_graph.json')
    parser.add_argument('transcription', help='Path to transcription.json')
    parser.add_argument('--output', '-o', default='context_alignment.json',
                       help='Output path for context alignment')
    parser.add_argument('--match-score', type=float, default=2.0,
                       help='Reward for pitch match')
    parser.add_argument('--mismatch-penalty', type=float, default=-1.0,
                       help='Penalty for pitch mismatch')
    parser.add_argument('--gap-penalty', type=float, default=-0.5,
                       help='Penalty for gap (insertion/deletion)')
    
    args = parser.parse_args()
    
    # Create aligner
    aligner = ContextAligner(
        match_score=args.match_score,
        mismatch_penalty=args.mismatch_penalty,
        gap_penalty=args.gap_penalty
    )
    
    # Perform alignment
    results = aligner.align(
        args.score_graph,
        args.transcription,
        args.output
    )
    
    print("\n✅ Context alignment completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())
```

**Test**: Run on a simple score with one repeat, verify correct path selection

**Time Estimate**: 8-12 hours

---

### 2.2 🔧 Block 2: Add Beat Weighting (PRIORITY 2)

**File**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`

**Enhancement**: Use beat confidence to weight DTW cost

**Changes**:
```python
class EnhancedSymbolicAligner:
    # ... existing code ...
    
    def enhanced_alignment(self, score_midi, perf_midi, 
                          beats_json=None,      # 🆕 NEW parameter
                          score_graph=None):    # 🆕 NEW parameter
        """
        Perform enhanced alignment with beat weighting
        """
        try:
            # Get duration
            score_duration = score_midi.get_end_time()
            perf_duration = perf_midi.get_end_time()
            max_duration = max(score_duration, perf_duration)
            
            logger.info(f"Aligning: score={score_duration:.2f}s, perf={perf_duration:.2f}s")
            
            # Extract chromagram features
            score_chroma = self.midi_to_chroma(score_midi, max_duration)
            perf_chroma = self.midi_to_chroma(perf_midi, max_duration)
            
            # 🆕 NEW: Apply beat-weighted cost if beats available
            if beats_json:
                logger.info("🎵 Applying beat-weighted cost matrix")
                C = self._compute_beat_weighted_cost(
                    score_chroma, 
                    perf_chroma, 
                    beats_json
                )
                # Use precomputed cost matrix
                wp, distance = self.dtw_alignment_with_cost(C)
            else:
                # Standard DTW
                wp, distance = self.dtw_alignment(score_chroma, perf_chroma)
            
            # ... rest of method unchanged ...
    
    def _compute_beat_weighted_cost(self, X: np.ndarray, Y: np.ndarray,
                                     beats_json: List[Dict]) -> np.ndarray:
        """
        Compute cost matrix weighted by beat confidence
        
        Args:
            X: Score chroma [12, N]
            Y: Performance chroma [12, M]
            beats_json: Beat detection results with confidence
            
        Returns:
            C: Weighted cost matrix [N, M]
        """
        from scipy.spatial.distance import cdist
        
        # Base cost (cosine distance)
        C = cdist(X.T, Y.T, metric='cosine')
        
        # Map beat times to frame indices
        beat_times = [b['t'] for b in beats_json]
        beat_frames = librosa.time_to_frames(
            beat_times,
            sr=self.sr,
            hop_length=self.hop_length
        )
        beat_confidences = np.array([b.get('confidence', 1.0) for b in beats_json])
        
        # Create confidence mask for Y (performance) axis
        # High confidence → lower cost → preferred alignment
        conf_mask = np.ones(Y.shape[1])
        
        for frame, conf in zip(beat_frames, beat_confidences):
            if 0 <= frame < len(conf_mask):
                # Apply confidence in a window around beat
                window_start = max(0, frame - 2)
                window_end = min(len(conf_mask), frame + 3)
                
                # Reduce cost near high-confidence beats
                weight = 1.0 / (1.0 + conf)  # Higher conf → lower weight → lower cost
                conf_mask[window_start:window_end] *= weight
        
        # Apply mask to cost matrix (broadcast over score axis)
        C = C * conf_mask[np.newaxis, :]
        
        logger.info(f"  Beat-weighted cost: {len(beat_frames)} beats used")
        return C
    
    def dtw_alignment_with_cost(self, C: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Perform DTW with precomputed cost matrix
        """
        try:
            D, wp = librosa.sequence.dtw(
                C=C,
                global_constraints=True,
                band_rad=0.25,
                backtrack=True
            )
            distance = D[-1, -1]
            logger.info(f"DTW with cost matrix: path length={len(wp)}, distance={distance:.4f}")
            return wp, distance
        except Exception as e:
            logger.error(f"DTW with cost matrix failed: {e}")
            raise
```

**Test**: Compare alignment with/without beat weighting

**Time Estimate**: 6-8 hours

---

### 2.3 🔧 Block 2: Add Fermata-Aware Weights (PRIORITY 2)

**File**: `Block_2_SymbolicAlignment/align_symbolic_enhanced.py`

**Enhancement**: Reduce step penalties near fermatas/cadences

**Changes**:
```python
class EnhancedSymbolicAligner:
    # ... existing code ...
    
    def enhanced_alignment(self, score_midi, perf_midi, 
                          beats_json=None,
                          score_graph=None):      # 🆕 Use this parameter
        """Enhanced alignment with fermata awareness"""
        
        # ... feature extraction ...
        
        # 🆕 Compute adaptive step weights if score_graph available
        weights_mul = None
        if score_graph:
            logger.info("🎼 Computing fermata-aware step weights")
            weights_mul = self._compute_adaptive_weights(
                n_frames=score_chroma.shape[1],
                nodes=score_graph['nodes']
            )
        
        # Apply in DTW
        if beats_json:
            C = self._compute_beat_weighted_cost(score_chroma, perf_chroma, beats_json)
            wp, distance = self.dtw_alignment_with_weights(C, weights_mul)
        else:
            wp, distance = self.dtw_alignment_with_weights_direct(
                score_chroma, perf_chroma, weights_mul
            )
        
        # ... rest of method ...
    
    def _compute_adaptive_weights(self, n_frames: int, 
                                   nodes: List[Dict]) -> np.ndarray:
        """
        Compute adaptive DTW step weights based on fermatas/cadences
        
        Returns:
            weights_mul: Array of shape [3] for [diagonal, horizontal, vertical] steps
                        Lower values = more flexibility
        """
        # Default: equal weights (standard DTW)
        weights = np.array([1.0, 1.0, 1.0])
        
        # TODO: This is a simplified version
        # Full implementation needs frame-to-beat mapping
        
        # Count fermatas and cadences in score
        fermata_count = sum(1 for n in nodes if 'fermata' in n.get('flags', []))
        cadence_count = sum(1 for n in nodes if 'cadence' in n.get('flags', []))
        
        if fermata_count > 0 or cadence_count > 0:
            # Reduce horizontal/vertical weights globally if expressive markings present
            # This allows more temporal flexibility throughout
            flexibility_factor = 0.7  # 30% reduction in penalty
            weights[1] *= flexibility_factor  # Horizontal (performance stretches/compresses)
            weights[2] *= flexibility_factor  # Vertical (score pauses)
            
            logger.info(f"  Adaptive weights: {fermata_count} fermatas, {cadence_count} cadences")
            logger.info(f"  Step weights: {weights}")
        
        return weights
    
    def dtw_alignment_with_weights(self, C: np.ndarray, 
                                    weights_mul: Optional[np.ndarray]) -> Tuple[np.ndarray, float]:
        """DTW with cost matrix and step weights"""
        try:
            if weights_mul is not None:
                D, wp = librosa.sequence.dtw(
                    C=C,
                    weights_mul=weights_mul,  # 🆕 Adaptive weights
                    global_constraints=True,
                    band_rad=0.25,
                    backtrack=True
                )
            else:
                D, wp = librosa.sequence.dtw(
                    C=C,
                    global_constraints=True,
                    band_rad=0.25,
                    backtrack=True
                )
            
            distance = D[-1, -1]
            return wp, distance
        except Exception as e:
            logger.error(f"DTW with weights failed: {e}")
            raise
```

**Test**: Verify alignment is more flexible near fermatas

**Time Estimate**: 6-8 hours

---

## Phase 3: Integration & Pipeline (1-2 Days)

### 3.1 Update Main Integration Script

**File**: `main_hybrid_v02.py` or `Temporal Alignment/integrate_temporal_alignment.py`

**Changes**: Add context alignment step

```python
def run_temporal_alignment_pipeline(score_path, audio_path, output_dir):
    """
    Complete pipeline with context + temporal alignment
    """
    
    # Block 0: Build ScoreGraph with DAG
    print("=" * 60)
    print("BLOCK 0: ScoreGraph with DAG")
    print("=" * 60)
    scoregraph = build_scoregraph(score_path, meta_path, seg_path)
    scoregraph_path = os.path.join(output_dir, 'scoregraph.json')
    with open(scoregraph_path, 'w') as f:
        json.dump(scoregraph, f, indent=2)
    
    # Block 4: Beat detection with confidence
    print("=" * 60)
    print("BLOCK 4: Beat Detection")
    print("=" * 60)
    beats_path = os.path.join(output_dir, 'beats.json')
    beats_json = estimate_beats(audio_path, beats_path)
    
    # Block 1: AMT Transcription
    print("=" * 60)
    print("BLOCK 1: AMT Transcription")
    print("=" * 60)
    transcription_path = os.path.join(output_dir, 'transcription.json')
    transcribe_audio_basic_pitch(audio_path, output_dir, transcription_path)
    
    # 🆕 NEW: Context Alignment
    print("=" * 60)
    print("CONTEXT ALIGNMENT: Find Structural Path")
    print("=" * 60)
    from context_aligner import ContextAligner
    
    context_aligner = ContextAligner()
    context_results = context_aligner.align(
        scoregraph_path,
        transcription_path,
        output_path=os.path.join(output_dir, 'context_alignment.json')
    )
    
    # Block 2: Temporal Alignment (Enhanced)
    print("=" * 60)
    print("BLOCK 2: Temporal Alignment (Enhanced)")
    print("=" * 60)
    
    aligner = EnhancedSymbolicAligner(gpu_manager=gpu_manager)
    
    # 🆕 Pass beats and score_graph to alignment
    results = aligner.align_score_performance(
        scoregraph_path,
        os.path.join(output_dir, 'basic_pitch.mid'),
        beats_json_path=beats_path,        # 🆕 NEW
        score_graph_json=scoregraph_path,  # 🆕 NEW
        context_path=os.path.join(output_dir, 'context_alignment.json'),  # 🆕 NEW
        output_dir=os.path.join(output_dir, 'block_2_enhanced')
    )
    
    print("=" * 60)
    print("PIPELINE COMPLETE!")
    print("=" * 60)
    
    return results
```

**Time Estimate**: 4-6 hours

---

## Phase 4: Testing & Validation (1-2 Days)

### 4.1 Create Test Suite

**File**: `Temporal Alignment/test_pipeline.py` (NEW)

```python
#!/usr/bin/env python3
"""
Test suite for temporal + context alignment pipeline
"""

import pytest
import json
from pathlib import Path

def test_scoregraph_has_edges():
    """Verify Block 0 outputs include edges"""
    with open('test_output/scoregraph.json') as f:
        sg = json.load(f)
    
    # Check first node has edges
    assert 'edges' in sg['nodes'][0]
    assert len(sg['nodes'][0]['edges']) > 0

def test_beats_have_confidence():
    """Verify Block 4 outputs include confidence"""
    with open('test_output/beats.json') as f:
        beats = json.load(f)
    
    # Check first beat has confidence
    assert 'confidence' in beats[0]
    assert 0.0 <= beats[0]['confidence'] <= 1.0

def test_context_alignment_output():
    """Verify context alignment produces valid path"""
    with open('test_output/context_alignment.json') as f:
        ctx = json.load(f)
    
    assert 'selected_path' in ctx
    assert len(ctx['selected_path']) > 0
    assert 'alignment_score' in ctx

def test_temporal_alignment_uses_beats():
    """Verify Block 2 uses beat information"""
    with open('test_output/block_2_enhanced/alignment_meta.json') as f:
        meta = json.load(f)
    
    assert meta.get('beat_conf_used', False) == True
    assert 'band_rad' in meta

# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**Time Estimate**: 6-8 hours

---

## Implementation Timeline

| Phase | Task | Time | Priority |
|-------|------|------|----------|
| **Phase 1** | Block 0: Add DAG edges | 4-6h | HIGH |
| | Block 4: Capture beat confidence | 2-3h | HIGH |
| | Block 2: Enable band constraints | 0.5h | HIGH |
| | **Phase 1 Total** | **7-10h** | **~1-2 days** |
| **Phase 2** | Context Aligner implementation | 8-12h | MEDIUM |
| | Block 2: Beat weighting | 6-8h | MEDIUM |
| | Block 2: Fermata-aware weights | 6-8h | MEDIUM |
| | **Phase 2 Total** | **20-28h** | **~3-4 days** |
| **Phase 3** | Integration & pipeline | 4-6h | MEDIUM |
| | **Phase 3 Total** | **4-6h** | **~1 day** |
| **Phase 4** | Testing & validation | 6-8h | LOW |
| | **Phase 4 Total** | **6-8h** | **~1 day** |
| **TOTAL** | | **37-52h** | **~5-8 days** |

---

## Dependencies to Install

```bash
# Existing (should already be installed)
pip install music21 librosa scipy numpy matplotlib pretty_midi basic-pitch

# New for this implementation
pip install networkx  # For DAG representation
pip install beatnet   # For beat detection with confidence

# Optional (for testing)
pip install pytest
```

---

## Expected Outputs

### File Structure After Implementation:
```
Temporal Alignment/
├── Block_0_ScoreGraph/
│   └── build_scoregraph_with_repeats.py  [MODIFIED: +edges]
├── Block_1_AMT/
│   └── transcribe_audio_fixed.py  [UNCHANGED]
├── Block_2_SymbolicAlignment/
│   └── align_symbolic_enhanced.py  [MODIFIED: +beat weighting, +fermata awareness]
├── Block_4_BeatDownbeat/
│   └── estimate_beats.py  [MODIFIED: +confidence]
├── context_aligner.py  [NEW]
├── test_pipeline.py  [NEW]
└── Output/
    ├── scoregraph.json  [with 'edges' field]
    ├── beats.json  [with 'confidence' field]
    ├── transcription.json
    ├── context_alignment.json  [NEW]
    └── alignment_meta.json  [with rubato/beat metadata]
```

---

## Success Criteria

✅ **Context Alignment**:
- Correctly identifies path through score with repeats
- Match percentage > 70% for well-performed pieces

✅ **Temporal Alignment**:
- DTW with band constraint runs faster than unconstrained
- Beat-weighted alignment shows improved accuracy at downbeats
- Fermata-aware weights show increased flexibility near marked regions

✅ **Integration**:
- Pipeline runs end-to-end without errors
- All JSON outputs validated and well-formed
- Results visualizations show clear improvements

---

## Next Steps After Completion

1. **Evaluation Layer**: Use aligned results for pitch/rhythm grading
2. **Visualization**: Create interactive plots of alignment paths
3. **Online Following**: Adapt for real-time performance tracking
4. **Advanced Features**:
   - Adaptive band width (per-frame, not global)
   - Transposition-invariant alignment
   - Multi-voice handling

---

## Questions & Decisions Needed

1. **DAG Edge Representation**: Should we store all possible edges (including repeat targets) or compute them dynamically?
   - **Recommendation**: Store explicitly for clarity

2. **Beat Confidence Threshold**: What confidence level should we trust?
   - **Recommendation**: Start with 0.5, tune based on testing

3. **Context vs Temporal Order**: Should context alignment run before or concurrently with temporal?
   - **Recommendation**: Sequential (Context → Temporal) for clarity

4. **Error Handling**: How to handle cases where context alignment fails?
   - **Recommendation**: Fallback to linear path (existing behavior)

---

## Final Notes

This plan:
- ✅ Aligns with your original plan in `TuttiBot_Temporal_Context_Alignment_Plan.txt`
- ✅ Leverages existing working code (minimal changes to Blocks 0, 1, 4)
- ✅ Adds clear separation: Context (structure) + Temporal (timing)
- ✅ Maintains backward compatibility (new features are optional)
- ✅ Provides concrete code examples for every change
- ✅ Includes realistic time estimates
- ✅ Defines clear success criteria

**Ready to proceed?** Start with Phase 1 (highest priority, quickest wins) and test each component before moving to Phase 2.
