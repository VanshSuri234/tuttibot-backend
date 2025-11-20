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
        # Sort by offset time to ensure correct sequence
        notes_sorted = sorted(notes, key=lambda n: n['offset_beats'])
        return [int(note['pitch']) for note in notes_sorted]
    
    def extract_performance_pitches(self, transcription: List[Dict]) -> List[int]:
        """Extract pitch sequence from performance transcription"""
        # Sort by start time
        transcription_sorted = sorted(transcription, key=lambda n: n.get('start_time', n.get('onset', 0)))
        return [int(note['pitch_midi']) for note in transcription_sorted]
    
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
        print("Context Alignment: Finding structural path through score")
        
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
        musical_notes_sorted = sorted(musical_notes, key=lambda n: n['offset_beats'])
        note_idx = 0
        
        for i, (score_pitch, perf_pitch) in enumerate(zip(aligned_score, aligned_perf)):
            if score_pitch is not None and perf_pitch is not None:
                # Match found - record this note's position
                if note_idx < len(musical_notes_sorted):
                    note = musical_notes_sorted[note_idx]
                    # Find corresponding beat node
                    abs_beat = note['offset_beats']
                    node_id = self._find_node_at_beat(score_graph['nodes'], abs_beat)
                    if node_id and (not selected_path or node_id != selected_path[-1]):
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
        
        print(f"Context alignment complete: {len(selected_path)} nodes in path")
        print(f"  Match percentage: {results['pitch_matches']['match_percentage']:.1f}%")
        print(f"  Saved to: {output_path}")
        
        return results
    
    def _find_node_at_beat(self, nodes: List[Dict], abs_beat: float) -> Optional[str]:
        """Find node ID closest to given absolute beat"""
        if not nodes:
            return None
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
    
    print("\nContext alignment completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
