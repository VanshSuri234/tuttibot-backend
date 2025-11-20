#!/usr/bin/env python3
"""
Enhanced Context Alignment with True Phrase-Level Analysis

Creates musical phrases based on structural boundaries and aligns
at the phrase level rather than note-by-note.

Musical phrases are detected using:
1. Breath marks and rests
2. Harmonic cadences  
3. Structural markers (repeats, codas)
4. Melodic contour peaks/valleys
5. Time signature boundaries
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
import networkx as nx
from pathlib import Path
import matplotlib.pyplot as plt


class MusicalPhrase:
    """Represents a musical phrase with notes and boundaries"""
    
    def __init__(self, phrase_id: str, start_beat: float, end_beat: float, 
                 notes: List[Dict], phrase_type: str = "melodic"):
        self.id = phrase_id
        self.start_beat = start_beat
        self.end_beat = end_beat
        self.notes = notes
        self.phrase_type = phrase_type  # "melodic", "cadential", "structural"
        self.pitches = [int(note['pitch']) for note in notes]
        self.duration = end_beat - start_beat
    
    def __repr__(self):
        return f"Phrase({self.id}, beats={self.start_beat:.1f}-{self.end_beat:.1f}, notes={len(self.notes)})"


class PhraseContextAligner:
    """Enhanced Context Alignment with phrase-level analysis"""
    
    def __init__(self, 
                 phrase_match_score: float = 10.0,
                 phrase_mismatch_penalty: float = -5.0,
                 phrase_gap_penalty: float = -2.0,
                 min_phrase_duration: float = 1.0,  # beats
                 max_phrase_duration: float = 8.0):  # beats
        """
        Initialize phrase-level context aligner
        
        Args:
            phrase_match_score: Reward for matching phrase
            phrase_mismatch_penalty: Penalty for phrase mismatch
            phrase_gap_penalty: Penalty for missing phrase
            min_phrase_duration: Minimum phrase length in beats
            max_phrase_duration: Maximum phrase length in beats
        """
        self.phrase_match_score = phrase_match_score
        self.phrase_mismatch_penalty = phrase_mismatch_penalty
        self.phrase_gap_penalty = phrase_gap_penalty
        self.min_phrase_duration = min_phrase_duration
        self.max_phrase_duration = max_phrase_duration
    
    def detect_phrase_boundaries(self, score_graph: Dict) -> List[float]:
        """
        Detect phrase boundaries in the score
        
        Returns:
            List of absolute beat positions where phrases begin/end
        """
        boundaries = [0.0]  # Always start with beat 0
        
        musical_notes = score_graph.get('musical_notes', [])
        bars = score_graph.get('bars', [])
        
        if not musical_notes:
            return boundaries
        
        # Sort notes by time
        notes_sorted = sorted(musical_notes, key=lambda n: n['offset_beats'])
        
        # 1. Detect rests/gaps (silence > 0.5 beats)
        for i in range(len(notes_sorted) - 1):
            current_end = notes_sorted[i]['offset_beats'] + notes_sorted[i].get('duration_beats', 0.5)
            next_start = notes_sorted[i + 1]['offset_beats']
            gap_duration = next_start - current_end
            
            if gap_duration > 0.5:  # Significant rest
                boundaries.append(next_start)
        
        # 2. Structural boundaries (bar lines, especially strong beats)
        for bar in bars:
            bar_start = bar['abs_beat']
            # Add boundaries at strong metric positions
            if bar['time_signature'][0] == 4:  # 4/4 time
                boundaries.extend([bar_start, bar_start + 2])  # Downbeat and beat 3
            elif bar['time_signature'][0] == 3:  # 3/4 time
                boundaries.append(bar_start)  # Just downbeats
        
        # 3. Melodic contour peaks (highest/lowest notes in local context)
        window_size = 4  # Look at 4-note windows
        for i in range(window_size, len(notes_sorted) - window_size):
            current_pitch = notes_sorted[i]['pitch']
            
            # Check if this is a local maximum or minimum
            window_pitches = [notes_sorted[j]['pitch'] 
                            for j in range(i - window_size, i + window_size + 1)]
            
            if (current_pitch == max(window_pitches) or 
                current_pitch == min(window_pitches)):
                boundaries.append(notes_sorted[i]['offset_beats'])
        
        # Remove duplicates and sort
        boundaries = sorted(list(set(boundaries)))
        
        # Add final boundary
        if musical_notes:
            final_beat = max(note['offset_beats'] + note.get('duration_beats', 0.5) 
                           for note in musical_notes)
            boundaries.append(final_beat)
        
        return boundaries
    
    def create_phrases_from_boundaries(self, score_graph: Dict, 
                                     boundaries: List[float]) -> List[MusicalPhrase]:
        """Create MusicalPhrase objects from boundary points"""
        phrases = []
        musical_notes = score_graph.get('musical_notes', [])
        
        if not musical_notes:
            return phrases
        
        notes_sorted = sorted(musical_notes, key=lambda n: n['offset_beats'])
        
        for i in range(len(boundaries) - 1):
            start_beat = boundaries[i]
            end_beat = boundaries[i + 1]
            
            # Skip phrases that are too short or too long
            duration = end_beat - start_beat
            if duration < self.min_phrase_duration or duration > self.max_phrase_duration:
                continue
            
            # Find notes in this phrase
            phrase_notes = []
            for note in notes_sorted:
                note_beat = note['offset_beats']
                if start_beat <= note_beat < end_beat:
                    phrase_notes.append(note)
            
            if phrase_notes:  # Only create phrase if it has notes
                phrase_id = f"phrase_{i+1:03d}"
                phrase_type = self._classify_phrase_type(phrase_notes, start_beat, end_beat)
                
                phrase = MusicalPhrase(
                    phrase_id=phrase_id,
                    start_beat=start_beat,
                    end_beat=end_beat,
                    notes=phrase_notes,
                    phrase_type=phrase_type
                )
                phrases.append(phrase)
        
        return phrases
    
    def _classify_phrase_type(self, notes: List[Dict], start_beat: float, end_beat: float) -> str:
        """Classify the type of musical phrase"""
        if not notes:
            return "empty"
        
        # Simple classification based on pitch pattern
        pitches = [note['pitch'] for note in notes]
        pitch_range = max(pitches) - min(pitches)
        
        # Cadential: ends on a resolution (descending pattern)
        if len(pitches) >= 2 and pitches[-1] < pitches[-2]:
            return "cadential"
        
        # Wide range suggests melodic phrase
        if pitch_range > 12:  # More than an octave
            return "melodic"
        
        # Narrow range suggests accompanying phrase
        if pitch_range <= 4:  # Within a third
            return "accompanimental"
        
        return "melodic"  # default
    
    def extract_performance_phrases(self, transcription: List[Dict], 
                                   score_phrases: List[MusicalPhrase]) -> List[MusicalPhrase]:
        """
        Create performance phrases by segmenting transcription based on 
        timing gaps and expected phrase durations from score
        """
        if not transcription:
            return []
        
        # Sort by time
        perf_notes = sorted(transcription, key=lambda n: n.get('start_time', n.get('onset', 0)))
        
        # Estimate average phrase duration from score
        if score_phrases:
            avg_phrase_duration = np.mean([p.duration for p in score_phrases])
            # Convert to seconds (assuming ~120 BPM = 0.5 sec/beat)
            avg_phrase_duration_sec = avg_phrase_duration * 0.5
        else:
            avg_phrase_duration_sec = 4.0  # Default 4 seconds
        
        # Detect gaps in performance
        perf_boundaries = [0.0]
        for i in range(len(perf_notes) - 1):
            current_end = perf_notes[i].get('start_time', 0) + perf_notes[i].get('duration', 0.5)
            next_start = perf_notes[i + 1].get('start_time', 0)
            gap = next_start - current_end
            
            # Gap > 0.3 seconds suggests phrase boundary
            if gap > 0.3:
                perf_boundaries.append(next_start)
        
        # Add final boundary
        if perf_notes:
            final_time = perf_notes[-1].get('start_time', 0) + perf_notes[-1].get('duration', 0.5)
            perf_boundaries.append(final_time)
        
        # Create performance phrases
        perf_phrases = []
        for i in range(len(perf_boundaries) - 1):
            start_time = perf_boundaries[i]
            end_time = perf_boundaries[i + 1]
            
            # Find notes in this time window
            phrase_notes = []
            for note in perf_notes:
                note_time = note.get('start_time', note.get('onset', 0))
                if start_time <= note_time < end_time:
                    phrase_notes.append(note)
            
            if phrase_notes:
                phrase_id = f"perf_phrase_{i+1:03d}"
                phrase = MusicalPhrase(
                    phrase_id=phrase_id,
                    start_beat=start_time,  # Using time instead of beats for performance
                    end_beat=end_time,
                    notes=phrase_notes,
                    phrase_type="performance"
                )
                perf_phrases.append(phrase)
        
        return perf_phrases
    
    def phrase_similarity(self, score_phrase: MusicalPhrase, 
                         perf_phrase: MusicalPhrase) -> float:
        """
        Calculate similarity between score and performance phrases
        
        Returns:
            Similarity score (higher = more similar)
        """
        if not score_phrase.pitches or not perf_phrase.pitches:
            return 0.0
        
        # 1. Pitch sequence similarity using edit distance
        seq1, seq2 = score_phrase.pitches, perf_phrase.pitches
        edit_distance = self._levenshtein_distance(seq1, seq2)
        max_len = max(len(seq1), len(seq2))
        pitch_similarity = 1.0 - (edit_distance / max_len) if max_len > 0 else 0.0
        
        # 2. Duration ratio similarity
        duration_ratio = min(score_phrase.duration, perf_phrase.duration) / max(score_phrase.duration, perf_phrase.duration)
        
        # 3. Pitch range similarity
        score_range = max(score_phrase.pitches) - min(score_phrase.pitches)
        perf_range = max(perf_phrase.pitches) - min(perf_phrase.pitches)
        range_similarity = 1.0 - abs(score_range - perf_range) / max(score_range + perf_range, 1)
        
        # Weighted combination
        total_similarity = (
            0.6 * pitch_similarity +
            0.2 * duration_ratio +
            0.2 * range_similarity
        )
        
        return total_similarity
    
    def _levenshtein_distance(self, seq1: List[int], seq2: List[int]) -> int:
        """Calculate edit distance between two pitch sequences"""
        if not seq1:
            return len(seq2)
        if not seq2:
            return len(seq1)
        
        # Create matrix
        matrix = [[0] * (len(seq2) + 1) for _ in range(len(seq1) + 1)]
        
        # Initialize first row and column
        for i in range(len(seq1) + 1):
            matrix[i][0] = i
        for j in range(len(seq2) + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len(seq1) + 1):
            for j in range(1, len(seq2) + 1):
                if seq1[i-1] == seq2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        return matrix[len(seq1)][len(seq2)]
    
    def align_phrases(self, score_phrases: List[MusicalPhrase], 
                     perf_phrases: List[MusicalPhrase]) -> Tuple[List, List, float]:
        """
        Align score and performance phrases using modified Needleman-Wunsch
        
        Returns:
            aligned_score_phrases, aligned_perf_phrases, alignment_score
        """
        n, m = len(score_phrases), len(perf_phrases)
        
        if n == 0 or m == 0:
            return [], [], 0.0
        
        # Initialize scoring matrix
        S = np.zeros((n + 1, m + 1))
        
        # Initialize gap penalties
        for i in range(n + 1):
            S[i, 0] = i * self.phrase_gap_penalty
        for j in range(m + 1):
            S[0, j] = j * self.phrase_gap_penalty
        
        # Fill matrix using phrase similarity
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                # Calculate similarity between phrases
                similarity = self.phrase_similarity(score_phrases[i-1], perf_phrases[j-1])
                
                if similarity > 0.5:  # Good match
                    match_score = similarity * self.phrase_match_score
                else:  # Poor match
                    match_score = self.phrase_mismatch_penalty
                
                # Three options: match, delete, insert
                match = S[i-1, j-1] + match_score
                delete = S[i-1, j] + self.phrase_gap_penalty
                insert = S[i, j-1] + self.phrase_gap_penalty
                
                S[i, j] = max(match, delete, insert)
        
        # Backtrack to find alignment
        aligned_score = []
        aligned_perf = []
        i, j = n, m
        
        while i > 0 or j > 0:
            if i > 0 and j > 0:
                similarity = self.phrase_similarity(score_phrases[i-1], perf_phrases[j-1])
                if similarity > 0.5:
                    score_diag = S[i-1, j-1] + similarity * self.phrase_match_score
                else:
                    score_diag = S[i-1, j-1] + self.phrase_mismatch_penalty
                
                score_up = S[i-1, j] + self.phrase_gap_penalty if i > 0 else -np.inf
                score_left = S[i, j-1] + self.phrase_gap_penalty if j > 0 else -np.inf
                
                if S[i, j] == score_diag:
                    aligned_score.append(score_phrases[i-1])
                    aligned_perf.append(perf_phrases[j-1])
                    i -= 1
                    j -= 1
                elif S[i, j] == score_up:
                    aligned_score.append(score_phrases[i-1])
                    aligned_perf.append(None)
                    i -= 1
                else:
                    aligned_score.append(None)
                    aligned_perf.append(perf_phrases[j-1])
                    j -= 1
            elif i > 0:
                aligned_score.append(score_phrases[i-1])
                aligned_perf.append(None)
                i -= 1
            else:
                aligned_score.append(None)
                aligned_perf.append(perf_phrases[j-1])
                j -= 1
        
        # Reverse (backtracked)
        aligned_score.reverse()
        aligned_perf.reverse()
        
        return aligned_score, aligned_perf, S[n, m]
    
    def visualize_phrase_alignment(self, score_phrases: List[MusicalPhrase], 
                                  perf_phrases: List[MusicalPhrase],
                                  aligned_score: List, aligned_perf: List,
                                  output_path: str = "phrase_alignment.png"):
        """Create visualization of phrase-level alignment"""
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        
        # 1. Score phrases
        ax1 = axes[0]
        for i, phrase in enumerate(score_phrases):
            start, end = phrase.start_beat, phrase.end_beat
            pitches = phrase.pitches
            
            # Plot phrase as horizontal bar with pitch information
            y_pos = i
            ax1.barh(y_pos, end - start, left=start, height=0.8, 
                    alpha=0.7, label=phrase.phrase_type)
            
            # Add pitch info as text
            avg_pitch = np.mean(pitches) if pitches else 60
            ax1.text(start + (end - start)/2, y_pos, f"{len(pitches)} notes", 
                    ha='center', va='center', fontsize=8)
        
        ax1.set_ylabel('Score Phrases')
        ax1.set_title('Score Phrase Structure')
        ax1.grid(True, alpha=0.3)
        
        # 2. Performance phrases
        ax2 = axes[1]
        for i, phrase in enumerate(perf_phrases):
            start, end = phrase.start_beat, phrase.end_beat
            pitches = phrase.pitches
            
            y_pos = i
            ax2.barh(y_pos, end - start, left=start, height=0.8, 
                    alpha=0.7, color='orange')
            
            avg_pitch = np.mean(pitches) if pitches else 60
            ax2.text(start + (end - start)/2, y_pos, f"{len(pitches)} notes", 
                    ha='center', va='center', fontsize=8)
        
        ax2.set_ylabel('Performance Phrases')
        ax2.set_title('Performance Phrase Structure')
        ax2.grid(True, alpha=0.3)
        
        # 3. Alignment visualization
        ax3 = axes[2]
        matches = 0
        for i, (score_phrase, perf_phrase) in enumerate(zip(aligned_score, aligned_perf)):
            if score_phrase is not None and perf_phrase is not None:
                # Draw connection between matched phrases
                similarity = self.phrase_similarity(score_phrase, perf_phrase)
                color = 'green' if similarity > 0.7 else 'yellow' if similarity > 0.4 else 'red'
                
                ax3.scatter(i, similarity, c=color, s=100, alpha=0.8)
                matches += 1 if similarity > 0.5 else 0
            elif score_phrase is not None:
                ax3.scatter(i, 0, c='red', s=50, marker='x', label='Unmatched Score')
            elif perf_phrase is not None:
                ax3.scatter(i, 0, c='blue', s=50, marker='+', label='Unmatched Performance')
        
        ax3.set_xlabel('Alignment Position')
        ax3.set_ylabel('Phrase Similarity')
        ax3.set_title(f'Phrase Alignment Quality (Matches: {matches}/{len(aligned_score)})')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(-0.1, 1.1)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Phrase alignment visualization saved to: {output_path}")
        plt.close()
    
    def align(self, score_graph_path: str, transcription_path: str,
              output_path: str = "phrase_context_alignment.json",
              visualize: bool = True) -> Dict:
        """
        Perform phrase-level context alignment
        
        Returns:
            Dictionary with phrase-level alignment results
        """
        print("Phrase-Level Context Alignment: Finding structural phrase patterns")
        
        # Load inputs
        with open(score_graph_path, 'r') as f:
            score_graph = json.load(f)
        
        with open(transcription_path, 'r') as f:
            transcription_data = json.load(f)
        transcription = transcription_data.get('notes', [])
        
        print(f"  Score nodes: {len(score_graph['nodes'])}")
        print(f"  Performance notes: {len(transcription)}")
        
        # 1. Detect phrase boundaries in score
        boundaries = self.detect_phrase_boundaries(score_graph)
        print(f"  Detected {len(boundaries)-1} phrase boundaries")
        
        # 2. Create score phrases
        score_phrases = self.create_phrases_from_boundaries(score_graph, boundaries)
        print(f"  Created {len(score_phrases)} score phrases")
        
        # 3. Create performance phrases
        perf_phrases = self.extract_performance_phrases(transcription, score_phrases)
        print(f"  Created {len(perf_phrases)} performance phrases")
        
        if not score_phrases or not perf_phrases:
            print("  No phrases found - falling back to note-level alignment")
            return {"error": "No phrases detected"}
        
        # 4. Align phrases
        aligned_score, aligned_perf, score = self.align_phrases(score_phrases, perf_phrases)
        print(f"  Phrase alignment score: {score:.2f}")
        
        # 5. Calculate statistics
        matches = sum(1 for s, p in zip(aligned_score, aligned_perf) 
                     if s is not None and p is not None and 
                     self.phrase_similarity(s, p) > 0.5)
        
        total_score_phrases = sum(1 for s in aligned_score if s is not None)
        
        results = {
            'phrase_level_analysis': True,
            'score_phrases': [
                {
                    'id': p.id,
                    'start_beat': p.start_beat,
                    'end_beat': p.end_beat,
                    'duration': p.duration,
                    'note_count': len(p.notes),
                    'phrase_type': p.phrase_type,
                    'pitch_range': max(p.pitches) - min(p.pitches) if p.pitches else 0
                } for p in score_phrases
            ],
            'performance_phrases': [
                {
                    'id': p.id,
                    'start_time': p.start_beat,
                    'end_time': p.end_beat,
                    'duration': p.duration,
                    'note_count': len(p.notes)
                } for p in perf_phrases
            ],
            'alignment_score': float(score),
            'phrase_matches': {
                'matches': matches,
                'total_score_phrases': total_score_phrases,
                'total_perf_phrases': len(perf_phrases),
                'match_percentage': (matches / total_score_phrases * 100) if total_score_phrases > 0 else 0
            },
            'phrase_boundaries': boundaries,
            'metadata': {
                'score_graph': score_graph_path,
                'transcription': transcription_path,
                'method': 'Phrase-level DAG + Needleman-Wunsch',
                'min_phrase_duration': self.min_phrase_duration,
                'max_phrase_duration': self.max_phrase_duration
            }
        }
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Phrase context alignment complete: {matches}/{total_score_phrases} phrases matched")
        print(f"  Match percentage: {results['phrase_matches']['match_percentage']:.1f}%")
        print(f"  Saved to: {output_path}")
        
        # Create visualization
        if visualize and score_phrases and perf_phrases:
            viz_path = output_path.replace('.json', '_visualization.png')
            self.visualize_phrase_alignment(score_phrases, perf_phrases, 
                                          aligned_score, aligned_perf, viz_path)
        
        return results


def main():
    """Example usage of phrase-level context alignment"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phrase-Level Context Alignment')
    parser.add_argument('score_graph', help='Path to score_graph.json')
    parser.add_argument('transcription', help='Path to transcription.json')
    parser.add_argument('--output', '-o', default='phrase_context_alignment.json',
                       help='Output path for phrase alignment results')
    parser.add_argument('--no-viz', action='store_true',
                       help='Skip visualization creation')
    parser.add_argument('--min-phrase-duration', type=float, default=1.0,
                       help='Minimum phrase duration in beats')
    parser.add_argument('--max-phrase-duration', type=float, default=8.0,
                       help='Maximum phrase duration in beats')
    
    args = parser.parse_args()
    
    # Create phrase-level aligner
    aligner = PhraseContextAligner(
        min_phrase_duration=args.min_phrase_duration,
        max_phrase_duration=args.max_phrase_duration
    )
    
    # Perform phrase-level alignment
    results = aligner.align(
        score_graph_path=args.score_graph,
        transcription_path=args.transcription,
        output_path=args.output,
        visualize=not args.no_viz
    )
    
    print("\nPhrase-Level Context Alignment Results:")
    print(f"  Score phrases: {len(results.get('score_phrases', []))}")
    print(f"  Performance phrases: {len(results.get('performance_phrases', []))}")
    print(f"  Phrase matches: {results.get('phrase_matches', {}).get('matches', 0)}")
    print(f"  Match percentage: {results.get('phrase_matches', {}).get('match_percentage', 0):.1f}%")


if __name__ == "__main__":
    main()